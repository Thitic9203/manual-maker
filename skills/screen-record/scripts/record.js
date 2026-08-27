#!/usr/bin/env node
/* screen-record — headless, spec-grade screen recording of a web flow.
 *
 *   NODE_PATH="$HOME/.manual-maker/runtime/node_modules" node record.js play.json
 *
 * What it produces, per run: <out>/<name>.mp4, <out>/<name>.capture.json and one PNG per `expect`
 * checkpoint. The MP4 is the deliverable; the PNGs back up any wording/label that the video
 * cannot render legibly (quality gate layer 5).
 *
 * Three properties are structural here, not optional flags — each one exists because a clip
 * that lacks it looks like proof without being proof:
 *
 *  1. LOGIN IS NOT IN THE CLIP. Authentication runs in a NON-recorded context; its
 *     storageState (incl. httpOnly cookies) is handed to a SECOND context that records. The
 *     clip therefore contains only the flow — and no credential is ever on screen.
 *  2. THE RUN FAILS CLOSED. A step whose `waitFor`/`expect` never appears aborts the run with
 *     a non-zero exit. A short clip that stopped before reaching its target must never be
 *     mistaken for a successful recording; the correct outcome is "blocked, with the reason".
 *  3. IT LOOKS LIKE A PERSON RECORDING THEIR OWN SCREEN. Exactly ONE thing is drawn into the
 *     page — a mouse pointer, because a real screen recording has one and a screencast does
 *     not. It is not an animation played over the top: it tracks the REAL pointer through
 *     the page's own mousemove/mousedown events, so it can only ever show where the browser
 *     actually clicked. Nothing else is injected: no banner, no URL strip, no watermark, no
 *     step counter. Anything diagnostic goes to the run log, which no viewer ever sees.
 *
 * Credentials come from the environment only (`SR_USER` / `SR_PASS`, or the names given in
 * `login.userEnv` / `login.passEnv`). They are never read from the play file, never printed.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (e) {
  console.error('FATAL playwright not resolvable. Run preflight.sh --install, then re-run with:');
  console.error('  NODE_PATH="$HOME/.manual-maker/runtime/node_modules" node record.js <play.json>');
  process.exit(2);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Two ways to fail, and the difference matters:
//   die()  — before recording starts (bad play file, failed login). Nothing to salvage, exit now.
//   fail() — once the recording is live. Throws instead of exiting, so main() can still finalize
//            and encode what was captured before the abort. Diagnosing "why did it never reach
//            the menu" needs the frames leading up to it; process.exit() would throw them away.
const die = (msg) => { console.error('FATAL ' + msg); process.exit(1); };
const fail = (msg) => { throw new Error(msg); };

// ----------------------------------------------------------------- play file
const playPath = process.argv[2];
if (!playPath) die('usage: node record.js <play.json>');
if (!fs.existsSync(playPath)) die(`play file not found: ${playPath}`);

let play;
try { play = JSON.parse(fs.readFileSync(playPath, 'utf8')); }
catch (e) { die(`play file is not valid JSON: ${e.message}`); }

const NAME = play.name || die('play.name is required (it becomes the file name)');
const BASE = (play.baseUrl || '').replace(/\/$/, '');
// `~` is what a person writes, and the spec's own example uses it. path.resolve does not expand it,
// so an unexpanded one silently produces a directory literally named "~" next to the home directory
// — the run reports success and the files are somewhere nobody looks.
const OUT = path.resolve((play.out || 'recordings').replace(/^~(?=$|[/\\])/, process.env.HOME || ''));
const VIEW = Object.assign({ width: 1920, height: 1080 }, play.viewport || {});
const DSF = play.deviceScaleFactor == null ? 2 : play.deviceScaleFactor;
const CRF = play.crf == null ? 18 : play.crf;
const PRESET = play.preset || 'slow';
// The capture pipeline. See the "capture" section below for why none of this goes through
// Playwright's own `recordVideo` any more.
//   OUT_FPS   — the frame rate of the delivered file.
//   JPEG_Q    — screencast frame quality; the ONLY lossy step before the final encode.
//   MIN_UNIQUE_FPS — fail-closed floor on the rate actually achieved.
//   MAX_SCRATCH_MB — every frame is kept, so the scratch directory has to be bounded somewhere.
//
// There is deliberately NO capture-fps setting, and that is the second bug this rewrite had to
// remove rather than a simplification. A first cut thinned the stream with `keep the frame only
// if t - lastKept >= 1/30`. On a page delivering ~31 fps (median gap 22 ms) that dropped every
// second frame — 22 ms is below the 31 ms minimum, so the keeper waits for the one after —
// yielding 15.4 fps, measurably WORSE judder than the defect being fixed. Any decimator aliases
// like that when the source rate is near the target; a phase accumulator does the same. The only
// rule that cannot alias is to keep every frame the browser sends and let the encoder do the rate
// conversion, so that is the rule. Bound the disk, never the frame rate.
const OUT_FPS = play.fps == null ? 25 : play.fps;
const JPEG_Q = play.jpegQuality == null ? 92 : play.jpegQuality;
const MIN_UNIQUE_FPS = play.minUniqueFps == null ? OUT_FPS * 0.8 : play.minUniqueFps;
const MAX_SCRATCH_MB = play.maxScratchMb == null ? 6144 : play.maxScratchMb;
const SETTLE = play.settle == null ? 900 : play.settle;      // pause after each step
const STEP_TIMEOUT = play.stepTimeout == null ? 30000 : play.stepTimeout;
const CURSOR = play.cursor !== false;                        // the drawn pointer (see header note 3)
const GLIDE_STEPS = play.glideSteps == null ? 28 : play.glideSteps;   // higher = slower, smoother travel
const TYPE_DELAY = play.typeDelay == null ? 55 : play.typeDelay;      // ms per character, 0 = instant
const NARRATION = play.narration || null;   // { lang, gender, voice?, rate? } — see narrate.py

// When a step carries `say`, the line and the moment it started are recorded here. Timing has to be
// measured during the run — a narration track built from guessed offsets drifts out of sync with
// the very thing it is describing.
const narration = [];
let recStart = null;

// Pass one (`narrate.py --prepare play.json`) speaks each line and writes how long it takes.
// Without it the flow moves on while the narrator is still mid-sentence — measured on the first
// narrated run: three lines each ran 5-6 s into the following step. Optional: a run with no
// durations file still records, it just is not paced to the voice.
// The durations file also records HOW the measuring pass spoke — tone, pitch, volume. That travels
// onto the timeline so the muxing pass speaks the same way; measuring at one tone and speaking at
// another gives every line a length the recording was not paced to.
let SAYMETA = {};
const SAYDUR = (() => {
  const guess = play.sayDurations || playPath.replace(/\.json$/, '') + '.saydur.json';
  try {
    if (fs.existsSync(guess)) {
      const d = JSON.parse(fs.readFileSync(guess, 'utf8'));
      console.log(`NARRATION TIMING: ${guess} (${Object.keys(d.steps || {}).length} lines)`
        + (d.tone ? ` tone ${d.tone}` : ''));
      SAYMETA = d;
      return d.steps || {};
    }
  } catch (e) { console.log('NARRATION TIMING: unreadable, recording unpaced —', e.message); }
  if (play.narration) {
    console.log('NARRATION TIMING: none — run `narrate.py --prepare` first so steps are paced to the voice');
  }
  return {};
})();
const steps = Array.isArray(play.steps) ? play.steps : die('play.steps must be an array');
if (!steps.length) die('play.steps is empty — there is no flow to record');

fs.mkdirSync(OUT, { recursive: true });

// Absolute URL from a play-file path: "/courses" → BASE + "/courses"; full URLs pass through.
const abs = (u) => (/^https?:\/\//i.test(u) ? u : BASE + '/' + String(u).replace(/^\//, ''));

// A locator from a play-file target: "text=..." / "//xpath" / any CSS selector.
const loc = (page, sel) => (String(sel).startsWith('//') ? page.locator(`xpath=${sel}`) : page.locator(sel));

// A step may live inside an iframe. OLS puts its whole sign-in form in one, served from another
// host (`/sign-in/embed`), so every selector aimed at the login fields searched the top document
// and found nothing — the run failed closed with "never reached", which was true and unhelpful.
//
// `"frame": "sign-in/embed"` matches a substring of the frame's URL and resolves the step there.
// Waiting is deliberate: an embedded form is fetched after the host page settles, so the frame
// often does not exist yet at the moment the step begins.
async function ctxOf(page, s) {
  if (!s || !s.frame) return page;
  const deadline = Date.now() + (s.frameTimeout || 20000);
  while (Date.now() < deadline) {
    const f = page.frames().find((fr) => fr.url().includes(s.frame));
    if (f) return f;
    await sleep(300);
  }
  // fail(), not die(): every caller runs inside the live step loop, so throwing lets main() finalize
  // and encode the frames captured up to the abort — which are exactly the frames needed to see why
  // the frame never appeared. process.exit() here would throw away the captured frames instead.
  fail(`step "${s.label || s.do}" wants the frame matching "${s.frame}", and no frame on the page `
    + `has that in its URL. Frames present: ${page.frames().map((f) => f.url()).join(', ') || 'none'}`);
}

// ---------------------------------------------------------------- mouse pointer
// Playwright's video has no pointer, so a viewer sees controls activate with nothing touching
// them — the one thing that gives away that a clip was not recorded by a person.
//
// This draws a pointer, but it does NOT animate one: it listens to the page's own mousemove /
// mousedown / mouseup and follows the REAL pointer. So the arrow can only ever be where the
// browser actually is, and the click flash can only fire on a real click. A drawn-on animation
// could show a click that never happened; this cannot.
//
// Runs through addInitScript, so it survives every navigation. Hidden until the first move, so a
// page that is never clicked shows no stray arrow.
function installCursor() {
  const draw = () => {
    if (document.getElementById('__sr_cursor')) return;
    const host = document.body || document.documentElement;
    if (!host) return;

    const style = document.createElement('style');
    style.textContent = `
      #__sr_cursor{position:fixed;left:0;top:0;width:24px;height:24px;z-index:2147483647;
        pointer-events:none;opacity:0;transition:opacity .12s linear;
        will-change:transform;transform:translate(-2px,-2px)}
      #__sr_cursor.__on{opacity:1}
      #__sr_cursor.__press{transform:translate(-2px,-2px) scale(.82)}
      #__sr_ring{position:fixed;left:0;top:0;width:34px;height:34px;margin:-17px 0 0 -17px;
        border-radius:50%;border:2px solid rgba(0,0,0,.45);z-index:2147483646;pointer-events:none;
        opacity:0}
      @keyframes __sr_pop{from{transform:scale(.35);opacity:.75}to{transform:scale(1.5);opacity:0}}
      #__sr_ring.__go{animation:__sr_pop .42s ease-out forwards}
    `;
    (document.head || host).appendChild(style);

    const cur = document.createElement('div');
    cur.id = '__sr_cursor';
    // Standard arrow: black fill, white outline so it stays visible on any background.
    cur.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
      + '<path d="M5 2.5 L5 18.2 L9.1 14.4 L11.7 20.6 L14.6 19.4 L12 13.3 L17.6 13.1 Z" '
      + 'fill="#111" stroke="#fff" stroke-width="1.3" stroke-linejoin="round"/></svg>';
    const ring = document.createElement('div');
    ring.id = '__sr_ring';
    host.appendChild(cur);
    host.appendChild(ring);

    let x = -100, y = -100;
    const place = () => { cur.style.transform = `translate(${x - 2}px, ${y - 2}px)`; };
    addEventListener('mousemove', (e) => {
      x = e.clientX; y = e.clientY;
      cur.classList.add('__on');
      cur.style.transform = `translate(${x - 2}px, ${y - 2}px)`
        + (cur.classList.contains('__press') ? ' scale(.82)' : '');
    }, true);
    addEventListener('mousedown', () => {
      cur.classList.add('__press'); place();
      cur.style.transform = `translate(${x - 2}px, ${y - 2}px) scale(.82)`;
      ring.style.left = x + 'px'; ring.style.top = y + 'px';
      ring.classList.remove('__go'); void ring.offsetWidth; ring.classList.add('__go');
    }, true);
    addEventListener('mouseup', () => {
      cur.classList.remove('__press');
      cur.style.transform = `translate(${x - 2}px, ${y - 2}px)`;
    }, true);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', draw);
  else draw();
  setTimeout(draw, 800);   // SPA shells that replace <body> after first paint
}

// Where the pointer is, kept on this side so it can be restored after a navigation.
let mouseAt = { x: Math.round(1920 / 2), y: Math.round(1080 / 3) };

// The live capture handle, so checkpoint() can hold the picture while a still is taken.
let capture = null;

// Travel to an element the way a hand does: a visible glide, then a beat before acting. The real
// pointer moves, so genuine :hover states fire on the way in — which is also what a viewer expects.
async function glideTo(page, locator) {
  if (!CURSOR) return;
  let box = null;
  try { box = await locator.boundingBox({ timeout: 5000 }); } catch (_) {}
  if (!box) return;                      // off-screen or detached — the action itself will report it
  const x = Math.round(box.x + box.width / 2);
  const y = Math.round(box.y + box.height / 2);
  await page.mouse.move(x, y, { steps: GLIDE_STEPS });
  mouseAt = { x, y };
  await sleep(260);                      // the pause a person makes before clicking
}

// A fresh document starts with no pointer until something moves it. Nudge it back so the arrow
// reappears where the viewer last saw it instead of blinking out for a whole page.
async function restoreCursor(page) {
  if (!CURSOR) return;
  await page.mouse.move(mouseAt.x, mouseAt.y).catch(() => {});
}

// ---------------------------------------------------------------------- login
async function login(context, cfg) {
  const userEnv = cfg.userEnv || 'SR_USER';
  const passEnv = cfg.passEnv || 'SR_PASS';
  const user = process.env[userEnv];
  const pass = process.env[passEnv];
  if (!user || !pass) {
    die(`login needs ${userEnv} and ${passEnv} in the environment `
      + '(credentials are never read from the play file). Seed them for this run only.');
  }
  const page = await context.newPage();
  await page.goto(abs(cfg.url || '/'), { waitUntil: 'domcontentloaded', timeout: 60000 });
  await sleep(2000);

  // Consent / commemorative / cookie overlays intercept the login control. Each is best-effort:
  // an overlay that is not shown this run must not fail the run.
  for (const sel of cfg.dismiss || []) {
    try { await loc(page, sel).first().click({ timeout: 5000 }); await sleep(700); } catch (_) {}
  }
  if (cfg.escapeOverlays !== false) { await page.keyboard.press('Escape').catch(() => {}); await sleep(400); }

  if (cfg.openSelector) {
    try { await loc(page, cfg.openSelector).first().click({ timeout: 20000 }); await sleep(1200); }
    catch (e) { die(`login.openSelector not clickable: ${cfg.openSelector}`); }
  }

  await loc(page, cfg.userSelector || '#email').first().fill(user, { timeout: 20000 })
    .catch(() => die(`login.userSelector not fillable: ${cfg.userSelector || '#email'}`));
  await loc(page, cfg.passSelector || '#password').first().fill(pass, { timeout: 20000 })
    .catch(() => die(`login.passSelector not fillable: ${cfg.passSelector || '#password'}`));
  await sleep(400);
  await loc(page, cfg.submitSelector || "//button[@type='submit']").first().click({ timeout: 20000 })
    .catch(() => die(`login.submitSelector not clickable: ${cfg.submitSelector}`));
  await sleep(2500);

  // Post-login signal. Without one we cannot tell "logged in" from "login page re-rendered",
  // so a missing/failed readySelector is fatal — recording an unauthenticated flow silently
  // is exactly the kind of false evidence this tool exists to prevent.
  if (cfg.readySelector) {
    await page.waitForSelector(cfg.readySelector, { timeout: cfg.readyTimeout || 45000 })
      .catch(() => die(`login did not reach readySelector: ${cfg.readySelector} `
        + '(wrong credentials, MFA, or a changed selector — check before re-running)'));
  } else if (cfg.readyUrl) {
    await page.waitForURL((u) => u.href.includes(cfg.readyUrl), { timeout: cfg.readyTimeout || 45000 })
      .catch(() => die(`login did not reach readyUrl: ${cfg.readyUrl}`));
  } else {
    die('login needs readySelector or readyUrl — without one the run cannot prove it logged in');
  }

  // Session warm-up: some apps only populate their session/localStorage after the app shell has
  // loaded once. Visiting it here means the recorded context starts already hydrated.
  if (cfg.warmUrl) {
    await page.goto(abs(cfg.warmUrl), { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
    if (cfg.readySelector) await page.waitForSelector(cfg.readySelector, { timeout: 20000 }).catch(() => {});
    await sleep(2000);
  }
  await page.close();
  console.log('LOGIN: ok');
}

// ------------------------------------------------------------------- one step
async function runStep(page, s, i) {
  const tag = `step ${i + 1}${s.label ? ' — ' + s.label : ''}`;
  const stepStart = Date.now();
  if (s.say && recStart != null) {
    narration.push({ step: i + 1, atMs: stepStart - recStart, text: String(s.say) });
  }
  const to = s.timeout || STEP_TIMEOUT;
  const act = s.do || 'goto';
  // Selectors resolve inside `s.frame` when the step names one; otherwise in the top document.
  const ctx = await ctxOf(page, s);

  switch (act) {
    case 'goto':
      await page.goto(abs(s.url), { waitUntil: 'domcontentloaded', timeout: 60000 });
      await restoreCursor(page);          // a fresh document has no pointer until something moves it
      break;
    case 'click': {
      const el = loc(ctx, s.selector).first();
      await glideTo(page, el);
      await el.click({ timeout: to });
      break;
    }
    case 'fill': {
      // A person clicks the field, then types into it. Setting .value in one frame next to a
      // moving pointer is the tell that gives an automated clip away, so type it out.
      const el = loc(ctx, s.selector).first();
      // `"value": { "env": "SR_PASS" }` types what the environment holds, never what the file holds.
      //
      // Normally the login runs off-camera precisely so no credential is ever on screen. That does
      // not work for the one clip whose SUBJECT is logging in: a manual page called "เข้าสู่ระบบ"
      // has to show the fields being filled. This is the opt-in for that clip and nothing else —
      // the play file still carries no secret, and a password field still renders as dots. Anything
      // typed into a plain text field WILL be readable in the deliverable, so only put an account
      // there that is meant to be seen.
      let value;
      if (s.value && typeof s.value === 'object' && s.value.env) {
        value = process.env[s.value.env];
        if (!value) die(`step "${s.label || s.do}" wants ${s.value.env} from the environment, and it is not set`);
      } else {
        value = String(s.value == null ? '' : s.value);
      }
      await glideTo(page, el);
      await el.click({ timeout: to });
      await el.fill('', { timeout: to });                 // clear whatever was there
      const delay = s.typeDelay == null ? TYPE_DELAY : s.typeDelay;
      if (delay > 0) await el.pressSequentially(value, { delay, timeout: to });
      else await el.fill(value, { timeout: to });
      break;
    }
    case 'select': {
      const el = loc(ctx, s.selector).first();
      await glideTo(page, el);
      await el.selectOption(String(s.value), { timeout: to });
      break;
    }
    case 'hover': {
      const el = loc(ctx, s.selector).first();
      await glideTo(page, el);
      await el.hover({ timeout: to });
      break;
    }
    case 'press':
      await page.keyboard.press(s.key || 'Enter');
      break;
    case 'scroll':
      // Human-paced, so the reader can follow — an instant jump reads as a cut.
      await page.evaluate(async (to_) => {
        const target = to_ == null ? document.body.scrollHeight : to_;
        const start = window.scrollY;
        const stepPx = target > start ? 250 : -250;
        for (let y = start; stepPx > 0 ? y < target : y > target; y += stepPx) {
          window.scrollTo(0, y);
          await new Promise((r) => setTimeout(r, 350));
        }
        window.scrollTo(0, target);
      }, s.to == null ? null : s.to);
      break;
    case 'scrollTo': {
      const el = loc(ctx, s.selector).first();
      await el.scrollIntoViewIfNeeded({ timeout: to });
      await sleep(400);
      await glideTo(page, el);            // land the pointer on what was just brought into view
      break;
    }
    case 'wait':
      await sleep(s.ms || 1000);
      break;
    case 'waitFor':
      await loc(ctx, s.selector).first().waitFor({ state: 'visible', timeout: to });
      break;
    default:
      fail(`${tag}: unknown action "${act}"`);
  }

  // Gate layer 3 in code: the step must land where it claimed it would. Fail closed.
  if (s.waitFor) {
    // The thing you act on and the thing that proves it worked are not always in the same document.
    // Clicking the host page's login button must produce a field inside the embedded form; clicking
    // submit INSIDE that form must produce the logged-in host page. `waitForFrame` names where to
    // look — `null` means the top document even when the action itself happened in a frame.
    const wctx = ('waitForFrame' in s)
      ? await ctxOf(page, { frame: s.waitForFrame, label: s.label, frameTimeout: s.frameTimeout })
      : ctx;
    await loc(wctx, s.waitFor).first().waitFor({ state: 'visible', timeout: to })
      .catch(() => fail(`${tag}: never reached "${s.waitFor}" — the flow did not arrive at its target. `
        + 'Do not ship this clip; fix the selector/flow or report the case as blocked.'));
  }
  await sleep(s.settle == null ? SETTLE : s.settle);

  // Let the narrator finish before the next action starts. The line began when the step began, so
  // what is left is its measured length minus the time the step already took, plus a short beat.
  const spoken = SAYDUR[String(i + 1)];
  if (s.say && spoken) {
    const elapsed = (Date.now() - stepStart) / 1000;
    const left = spoken + 0.35 - elapsed;
    if (left > 0) {
      console.log(`        …holding ${left.toFixed(1)}s for the narration to finish`);
      await sleep(Math.round(left * 1000));
    }
  }
}

// Gate layer 4/5: the state that decides the expected result is shown, and a still is captured.
// The pointer belongs in the video — in a still it is just something parked on top of the words
// someone needs to read — so it is hidden for the shutter and restored straight after.
async function checkpoint(page, s, i, shots) {
  if (!s.expect) return;
  const tag = `step ${i + 1}${s.label ? ' — ' + s.label : ''}`;
  // The proof lives where the step ARRIVED, not where it acted — the same split `waitFor` already
  // handles. Clicking submit inside an embedded sign-in frame lands on the host page and destroys
  // that frame, so resolving `expect` against `s.frame` aborts a step that in fact succeeded, with
  // a message blaming a missing frame. Order: an explicit `expectFrame`, else `waitForFrame`
  // (including an explicit `null`, meaning the top document), else the frame the action ran in.
  const scope = 'expectFrame' in s ? s.expectFrame
    : ('waitForFrame' in s ? s.waitForFrame : s.frame);
  const ctx = await ctxOf(page, { frame: scope, label: s.label, frameTimeout: s.frameTimeout });
  await loc(ctx, s.expect).first().waitFor({ state: 'visible', timeout: s.timeout || STEP_TIMEOUT })
    .catch(() => fail(`${tag}: expected result "${s.expect}" never became visible — the clip would not prove it.`));
  await sleep(600);
  const n = String(shots.length + 1).padStart(2, '0');
  const file = path.join(OUT, `${NAME}-ER_${n}.png`);
  const setCursor = (vis) => page.evaluate((v) => {
    const c = document.getElementById('__sr_cursor');
    if (c) c.style.visibility = v ? '' : 'hidden';
  }, vis).catch(() => {});
  // Hiding the pointer for the shutter used to blink it out of the VIDEO too — a ~750 ms
  // disappearance of the one element that makes the clip read as a person's screen, once per
  // checkpoint. The still still needs the pointer gone, so the fix is to hold the picture across
  // the whole window instead: capture pauses, the last frame stays on screen, and the blink never
  // reaches the file. Safe because a checkpoint is by definition a settled screen — `expect` has
  // already gone visible and 600 ms has passed, so there is nothing moving to freeze.
  if (capture) capture.pause();
  try {
    if (CURSOR) { await setCursor(false); await sleep(150); }
    await page.screenshot({ path: file, fullPage: !!s.fullPage });
    if (CURSOR) { await setCursor(true); await sleep(80); }
  } finally {
    if (capture) capture.resume();
  }
  shots.push(file);
  console.log(`SHOT: ${file} ${fs.statSync(file).size} bytes`);
}

// -------------------------------------------------------------------- capture
/* WHY THIS EXISTS — the flicker that shipped, and the two mechanisms behind it.
 *
 * Until v0.35.0 the clip came from Playwright's own `recordVideo`. Two defects are baked into
 * that path and NEITHER is reachable from its API. Both were measured — on the delivered
 * ELMS-2.4.1 clip and on a synthetic page — not inferred:
 *
 *  1. BITRATE CAP → the picture pumps. playwright-core spawns ffmpeg with a hardcoded
 *       -c:v vp8 -qmin 0 -qmax 50 -crf 8 -deadline realtime -speed 8 -b:v 1M -threads 1
 *     — 1 Mbps for 1920x1080. Whenever the page moves, rate control slams the quantiser and the
 *     WHOLE frame goes soft for a frame or two, then snaps back. Measured on the delivered clip:
 *     mean edge energy 1733 static vs 1529 moving (-11.8%), worst single frame -37%. A
 *     sharp/soft/sharp alternation is exactly what a viewer calls "กระพริบ".
 *
 *  2. FIXED-RATE PADDING → the motion judders. Its writeFrame does
 *       frameNumber = floor((t - t0) * 25);  push lastFrame (frameNumber - last.frameNumber)x
 *     so every gap in delivery is filled by REPEATING the previous frame, quantised onto a 40 ms
 *     grid. 46% of the delivered clip's frames were duplicates of their predecessor.
 *
 * The tempting reading is "this machine cannot capture 1080p fast enough". It is wrong, and it
 * was tested rather than assumed: driving Page.screencastFrame directly, same machine, same
 * 1920x1080 viewport, deviceScaleFactor 2, on a HEAVIER page — 59.8 fps, median inter-frame gap
 * 17 ms. The browser was never the bottleneck; the single-threaded realtime VP8 encoder
 * downstream of it was. Lowering deviceScaleFactor would therefore have fixed nothing (dsf 1
 * measured 58.9 fps — inside the noise) while making every still blurrier.
 *
 * So this owns the capture: frames arrive over CDP as JPEG, are written to a scratch directory
 * WITH THEIR REAL TIMESTAMPS, and are encoded once, after the run, with no realtime deadline and
 * no bitrate ceiling. That deletes an entire lossy generation as well as both defects above:
 * JPEG → x264, instead of JPEG → VP8@1Mbps → x264.
 *
 * Three properties are load-bearing. Do not "simplify" any of them away:
 *   - ACK FIRST, WRITE AFTER. Chrome sends nothing further until a frame is acked. Acking before
 *     touching the disk is what holds the browser at full rate however slow the disk is — the
 *     exact coupling Playwright has, and the reason its capture starves.
 *   - KEEP EVERY FRAME'S REAL TIME. The encode places each frame at the moment it happened rather
 *     than on a 40 ms grid, so nothing is shown early or late.
 *   - NOTHING IS THINNED. Every delivered frame is kept; no frame is invented, duplicated, moved
 *     or dropped. See the MAX_SCRATCH_MB note above for why a rate filter is not an option.
 */
function startCapture(cdp, page) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sr-frames-'));
  const frames = [];                     // { file, t } — t is the browser's own timestamp, seconds
  // Windows where capture was paused for a still, in CAPTURE-CLOCK seconds. They have to be
  // declared, not just counted: a hold deliberately repeats one frame, and on a page with a
  // background animation that is indistinguishable from the stall verify-video.py exists to
  // catch. The verifier excludes exactly these spans and fails if they cover most of the clip.
  const holds = [];
  let kept = 0, seen = 0, writeErrors = 0, bytes = 0, paused = false, overBudget = false;
  let pendingHold = null;

  cdp.on('Page.screencastFrame', (ev) => {
    // Ack first, unconditionally — see the note above. Nothing below may block this.
    cdp.send('Page.screencastFrameAck', { sessionId: ev.sessionId }).catch(() => {});
    seen++;
    if (paused || overBudget) return;    // a still is being taken; the video holds the last frame
    const t = (ev.metadata && ev.metadata.timestamp) || 0;
    const buf = Buffer.from(ev.data, 'base64');
    if (bytes + buf.length > MAX_SCRATCH_MB * 1024 * 1024) {
      // Stop growing rather than fill the disk — and remember it, so the run cannot report a
      // truncated capture as a complete one.
      overBudget = true;
      return;
    }
    const file = path.join(dir, `f${String(kept + 1).padStart(6, '0')}.jpg`);
    try { fs.writeFileSync(file, buf); }
    catch (e) { writeErrors++; return; }
    kept++; bytes += buf.length;
    frames.push({ file, t });
    if (pendingHold) { pendingHold.to = t; holds.push(pendingHold); pendingHold = null; }
  });

  const opts = {
    format: 'jpeg', quality: JPEG_Q, everyNthFrame: 1,
    maxWidth: VIEW.width, maxHeight: VIEW.height,
  };
  const start = () => cdp.send('Page.startScreencast', opts).catch(() => {});
  // A cross-document navigation can tear the screencast down. Re-arming on every main-frame
  // navigation is cheap and idempotent; missing one would silently lose a whole page of the flow.
  page.on('framenavigated', (f) => { if (f === page.mainFrame()) start(); });

  return {
    dir, frames, holds,
    started: start(),
    // The span runs from the last frame that made it in to the first one after the shutter — the
    // stretch the encoder will fill by repeating that last frame.
    pause() {
      paused = true;
      pendingHold = { from: frames.length ? frames[frames.length - 1].t : 0 };
    },
    resume() { paused = false; },
    async stop() { await cdp.send('Page.stopScreencast').catch(() => {}); },
    stats() {
      const t0 = frames.length ? frames[0].t : 0;
      const span = frames.length > 1 ? frames[frames.length - 1].t - t0 : 0;
      const gaps = frames.slice(1).map((f, i) => f.t - frames[i].t).sort((a, b) => a - b);
      const at = (p) => (gaps.length ? gaps[Math.min(gaps.length - 1, Math.floor(gaps.length * p))] : 0);
      return {
        framesKept: frames.length, framesSeen: seen, writeErrors,
        scratchMb: +(bytes / 1048576).toFixed(1), overBudget,
        spanSeconds: +span.toFixed(3),
        uniqueFps: span > 0 ? +(frames.length / span).toFixed(2) : 0,
        medianGapMs: +(at(0.5) * 1000).toFixed(1),
        p95GapMs: +(at(0.95) * 1000).toFixed(1),
        maxGapMs: +(at(1) * 1000).toFixed(1),
        holds: holds.length,
        // Seconds from the first captured frame, i.e. straight onto the video's own timeline.
        holdSpans: holds
          .filter((h) => h.to != null && h.to > h.from)
          .map((h) => ({ from: +(h.from - t0).toFixed(3), to: +(h.to - t0).toFixed(3) })),
      };
    },
    cleanup() { try { fs.rmSync(dir, { recursive: true, force: true }); } catch (_) {} },
  };
}

// ------------------------------------------------------------------- encoding
// One encode, from the captured JPEGs straight to H.264. The concat demuxer carries each frame's
// MEASURED duration, so `-fps_mode cfr` lays them onto the output grid at the times they actually
// happened. CRF 18 + preset slow is visually lossless on UI content; yuv420p and +faststart keep
// it playable in browsers, Jira, Drive and QuickTime alike. Changing these changes what "same as
// the reference recordings" means — see references/video-spec.md.
//
// The range conversion is not decoration. Screencast frames are JPEG, which is FULL-range, so a
// plain `-pix_fmt yuv420p` still comes out tagged `yuvj420p` — measured, and it fails
// verify-video.py's layer-1 pix_fmt check as well as rendering with crushed blacks in players
// that ignore the tag. `scale=in_range=full:out_range=limited` CONVERTS the levels (rather than
// relabelling them, which would shift every tone) and `-color_range tv` records what was done.
const ENCODER_ARGS = (list, mp4) => ['-y', '-f', 'concat', '-safe', '0', '-i', list,
  '-fps_mode', 'cfr', '-r', String(OUT_FPS),
  '-vf', 'scale=in_range=full:out_range=limited',
  '-c:v', 'libx264', '-crf', String(CRF), '-preset', PRESET,
  '-pix_fmt', 'yuv420p', '-color_range', 'tv',
  '-movflags', '+faststart', mp4];

function encode(cap, mp4) {
  const fr = cap.frames;
  if (fr.length < 2) die('capture produced no frames — nothing to encode. The screencast never '
    + 'started; check that the browser stayed open and that CDP is reachable.');
  const list = path.join(cap.dir, 'list.txt');
  const out = [];
  for (let i = 0; i < fr.length; i++) {
    const d = i + 1 < fr.length ? fr[i + 1].t - fr[i].t : 1 / OUT_FPS;
    out.push(`file '${fr[i].file}'`);
    out.push(`duration ${Math.max(0.001, d).toFixed(6)}`);
  }
  out.push(`file '${fr[fr.length - 1].file}'`);   // concat needs the final entry repeated
  fs.writeFileSync(list, out.join('\n') + '\n');
  execFileSync('ffmpeg', ENCODER_ARGS(list, mp4), { stdio: 'ignore' });
}

// ----------------------------------------------------------------------- main
(async () => {
  const browser = await chromium.launch({ headless: play.headless === false ? false : true });
  let failed = null;
  try {
    let state;
    if (play.storageState && fs.existsSync(play.storageState)) {
      state = play.storageState;                       // reuse a session the user already saved
      console.log('LOGIN: reused storageState', play.storageState);
    } else if (play.login) {
      const authCtx = await browser.newContext({ viewport: VIEW });
      await login(authCtx, play.login);
      state = await authCtx.storageState();
      await authCtx.close();
      if (play.saveStorageState) {
        fs.writeFileSync(play.saveStorageState, JSON.stringify(state));
        console.log('LOGIN: saved storageState', play.saveStorageState);
      }
    } else {
      console.log('LOGIN: none (public flow)');
    }

    // No `recordVideo` — the clip is captured by startCapture() instead. See the capture section
    // for the two measured defects that choice removes.
    const ctx = await browser.newContext({
      viewport: VIEW,
      deviceScaleFactor: DSF,
      ...(state ? { storageState: state } : {}),
    });
    const page = await ctx.newPage();
    const cdp = await ctx.newCDPSession(page);
    capture = startCapture(cdp, page);
    await capture.started;
    recStart = Date.now();          // the video starts here, so narration offsets are measured from here
    if (CURSOR) {
      mouseAt = { x: Math.round(VIEW.width / 2), y: Math.round(VIEW.height / 3) };
      await page.addInitScript(installCursor);
    }

    const shots = [];
    try {
      for (let i = 0; i < steps.length; i++) {
        const s = steps[i];
        console.log(`STEP ${i + 1}/${steps.length}: ${s.do || 'goto'}${s.label ? ' — ' + s.label : ''}`);
        await runStep(page, s, i);
        await checkpoint(page, s, i, shots);
      }
      await sleep(play.tail == null ? 1500 : play.tail);   // let the last frame land in the video
    } catch (e) {
      failed = e;                                          // still finalize the video for diagnosis
    }

    await capture.stop();
    await page.close();
    await ctx.close();

    const mp4 = path.join(OUT, `${NAME}.mp4`);
    const stats = capture.stats();
    try {
      encode(capture, mp4);
      console.log(`MP4: ${mp4} ${fs.statSync(mp4).size} bytes`);
    } catch (e) {
      capture.cleanup();
      die('ffmpeg failed to encode the captured frames. Install ffmpeg (preflight.sh --install) '
        + `and re-run. Underlying error: ${e && e.message ? e.message : e}`);
    }

    // The capture manifest — retained evidence, the same role `annotations.json` plays for the
    // manual. It records what the pipeline ACTUALLY did (rate, gaps, encoder arguments), so
    // verify-video.py can check the delivered file against it instead of taking the run's word.
    // A missing manifest is itself a failure at the gate: ตรวจไม่ได้ = ไม่ผ่าน.
    const capFile = path.join(OUT, `${NAME}.capture.json`);
    fs.writeFileSync(capFile, JSON.stringify({
      name: NAME, video: path.basename(mp4),
      viewport: VIEW, deviceScaleFactor: DSF,
      outFps: OUT_FPS, jpegQuality: JPEG_Q, maxScratchMb: MAX_SCRATCH_MB,
      crf: CRF, preset: PRESET,
      pipeline: 'cdp-screencast->x264',   // never 'playwright-recordVideo' — see the capture note
      encoderArgs: ENCODER_ARGS('<list>', path.basename(mp4)).join(' '),
      minUniqueFps: MIN_UNIQUE_FPS,
      ...stats,
    }, null, 2));
    console.log(`CAPTURE: ${capFile} — ${stats.framesKept} frames, ${stats.uniqueFps} unique fps, `
      + `median gap ${stats.medianGapMs} ms, p95 ${stats.p95GapMs} ms, ${stats.holds} still-holds`);
    console.log(`SHOTS: ${shots.length}`);

    // Fail closed on a starved capture. A clip encoded from fewer real frames than it claims to
    // show is the judder defect coming back by another route, and it must never be mistaken for a
    // good recording. The file is left on disk so the failure can be diagnosed, not re-run blind.
    if (stats.overBudget) {
      capture.cleanup();
      die(`capture hit the ${MAX_SCRATCH_MB} MB scratch budget and stopped early — the clip at `
        + `${mp4} is cut short and must not be shipped. Record a shorter flow, or raise `
        + '`maxScratchMb` in the play file if the disk genuinely has the room.');
    }
    if (stats.uniqueFps < MIN_UNIQUE_FPS) {
      capture.cleanup();
      die(`capture starved: ${stats.uniqueFps} unique fps against a ${MIN_UNIQUE_FPS} floor `
        + `(p95 gap ${stats.p95GapMs} ms, max ${stats.maxGapMs} ms). The clip at ${mp4} would `
        + 'judder. Do not ship it. Close other heavy work and re-run, or lower `fps` in the play '
        + 'file to a rate the machine can actually hold — never raise `minUniqueFps` to go green.');
    }
    if (narration.length) {
      const nfile = path.join(OUT, `${NAME}.narration.json`);
      // Carry the WHOLE narration config, not a subset. Dropping `gender` here is what made every
      // clip requested as female come back in the male voice: narrate.py reads this file, found no
      // gender, and fell back to its default. The measuring pass had used the right voice, so the
      // timing looked correct and only the voice was wrong — the hardest kind of bug to notice.
      fs.writeFileSync(nfile, JSON.stringify({
        name: NAME,
        video: path.basename(mp4),
        lang: (NARRATION && NARRATION.lang) || SAYMETA.lang || null,
        gender: (NARRATION && NARRATION.gender) || SAYMETA.gender || null,
        voice: (NARRATION && NARRATION.voice) || SAYMETA.voice || null,
        rate: (NARRATION && NARRATION.rate) || SAYMETA.rate || null,
        // Tone/pitch/volume come from whatever the measuring pass ACTUALLY used, falling back to
        // the play file. Preferring the measurement is deliberate: the durations the recording was
        // paced to were produced at that tone, so speaking at any other one re-lengthens every line.
        tone: SAYMETA.tone || (NARRATION && NARRATION.tone) || null,
        pitch: SAYMETA.pitch || null,
        volume: SAYMETA.volume || null,
        lines: narration,
      }, null, 2));
      console.log(`NARRATION: ${nfile} ${narration.length} lines`
        + ` — run narrate.py to speak it onto the video`);
    } else if (NARRATION) {
      console.log('NARRATION: requested but no step carried a `say` line — nothing to speak');
    }
    if (failed) die(`run aborted mid-flow: ${failed.message}`);
    console.log('RESULT: recorded');
  } finally {
    await browser.close();
    if (capture) capture.cleanup();      // the scratch frames are large; never leave them behind
  }
})().catch((e) => { console.error('FATAL', e && e.message ? e.message : e); process.exit(1); });
