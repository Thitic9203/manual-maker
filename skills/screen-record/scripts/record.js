#!/usr/bin/env node
/* screen-record — headless, spec-grade screen recording of a web flow.
 *
 *   NODE_PATH="$HOME/.manual-maker/runtime/node_modules" node record.js play.json
 *
 * What it produces, per run: <out>/<name>.mp4 (+ .webm source) and one PNG per `expect`
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
 *  3. NOTHING OF OURS IS ON SCREEN. The clip must be indistinguishable from a person using the
 *     system and recording their own screen. This script draws NOTHING into the page — no
 *     overlay, no banner, no watermark, no debug strip. Playwright is already invisible to the
 *     page (no cursor, no "controlled by automated software" bar in page content). If you are
 *     ever tempted to inject a helper element "just for this run", don't: it lands in every
 *     frame and has to be edited out afterwards.
 *
 * Credentials come from the environment only (`SR_USER` / `SR_PASS`, or the names given in
 * `login.userEnv` / `login.passEnv`). They are never read from the play file, never printed.
 */
'use strict';

const fs = require('fs');
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
const OUT = path.resolve(play.out || 'recordings');
const VIEW = Object.assign({ width: 1920, height: 1080 }, play.viewport || {});
const DSF = play.deviceScaleFactor == null ? 2 : play.deviceScaleFactor;
const CRF = play.crf == null ? 20 : play.crf;
const PRESET = play.preset || 'slow';
const SETTLE = play.settle == null ? 900 : play.settle;      // pause after each step
const STEP_TIMEOUT = play.stepTimeout == null ? 30000 : play.stepTimeout;
const steps = Array.isArray(play.steps) ? play.steps : die('play.steps must be an array');
if (!steps.length) die('play.steps is empty — there is no flow to record');

fs.mkdirSync(OUT, { recursive: true });

// Absolute URL from a play-file path: "/courses" → BASE + "/courses"; full URLs pass through.
const abs = (u) => (/^https?:\/\//i.test(u) ? u : BASE + '/' + String(u).replace(/^\//, ''));

// A locator from a play-file target: "text=..." / "//xpath" / any CSS selector.
const loc = (page, sel) => (String(sel).startsWith('//') ? page.locator(`xpath=${sel}`) : page.locator(sel));

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
  const to = s.timeout || STEP_TIMEOUT;
  const act = s.do || 'goto';

  switch (act) {
    case 'goto':
      await page.goto(abs(s.url), { waitUntil: 'domcontentloaded', timeout: 60000 });
      break;
    case 'click':
      await loc(page, s.selector).first().click({ timeout: to });
      break;
    case 'fill':
      await loc(page, s.selector).first().fill(String(s.value == null ? '' : s.value), { timeout: to });
      break;
    case 'select':
      await loc(page, s.selector).first().selectOption(String(s.value), { timeout: to });
      break;
    case 'hover':
      await loc(page, s.selector).first().hover({ timeout: to });
      break;
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
    case 'scrollTo':
      await loc(page, s.selector).first().scrollIntoViewIfNeeded({ timeout: to });
      break;
    case 'wait':
      await sleep(s.ms || 1000);
      break;
    case 'waitFor':
      await loc(page, s.selector).first().waitFor({ state: 'visible', timeout: to });
      break;
    default:
      fail(`${tag}: unknown action "${act}"`);
  }

  // Gate layer 3 in code: the step must land where it claimed it would. Fail closed.
  if (s.waitFor) {
    await loc(page, s.waitFor).first().waitFor({ state: 'visible', timeout: to })
      .catch(() => fail(`${tag}: never reached "${s.waitFor}" — the flow did not arrive at its target. `
        + 'Do not ship this clip; fix the selector/flow or report the case as blocked.'));
  }
  await sleep(s.settle == null ? SETTLE : s.settle);
}

// Gate layer 4/5: the state that decides the expected result is shown, and a still is captured
// of the page exactly as it is — nothing is drawn on it before or after the shutter.
async function checkpoint(page, s, i, shots) {
  if (!s.expect) return;
  const tag = `step ${i + 1}${s.label ? ' — ' + s.label : ''}`;
  await loc(page, s.expect).first().waitFor({ state: 'visible', timeout: s.timeout || STEP_TIMEOUT })
    .catch(() => fail(`${tag}: expected result "${s.expect}" never became visible — the clip would not prove it.`));
  await sleep(600);
  const n = String(shots.length + 1).padStart(2, '0');
  const file = path.join(OUT, `${NAME}-ER_${n}.png`);
  await page.screenshot({ path: file, fullPage: !!s.fullPage });
  shots.push(file);
  console.log(`SHOT: ${file} ${fs.statSync(file).size} bytes`);
}

// ------------------------------------------------------------------- encoding
function encode(webm, mp4) {
  // CRF 20 + preset slow = visually near-lossless at a size that still uploads; yuv420p and
  // +faststart keep it playable in browsers, Jira, Drive and QuickTime alike. Changing these
  // changes what "same as the reference recordings" means — see references/video-spec.md.
  execFileSync('ffmpeg', ['-y', '-i', webm,
    '-c:v', 'libx264', '-crf', String(CRF), '-preset', PRESET,
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4], { stdio: 'ignore' });
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

    const ctx = await browser.newContext({
      viewport: VIEW,
      deviceScaleFactor: DSF,
      ...(state ? { storageState: state } : {}),
      recordVideo: { dir: OUT, size: { width: VIEW.width, height: VIEW.height } },
    });
    const page = await ctx.newPage();

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

    const video = page.video();
    await page.close();                                    // finalizes the recording
    await ctx.close();
    const src = await video.path();
    const webm = path.join(OUT, `${NAME}.webm`);
    fs.renameSync(src, webm);
    const mp4 = path.join(OUT, `${NAME}.mp4`);
    try {
      encode(webm, mp4);
      console.log(`MP4: ${mp4} ${fs.statSync(mp4).size} bytes`);
    } catch (e) {
      die(`ffmpeg failed — the .webm is at ${webm}. Install ffmpeg (preflight.sh --install) and re-encode.`);
    }
    console.log(`WEBM: ${webm} ${fs.statSync(webm).size} bytes`);
    console.log(`SHOTS: ${shots.length}`);
    if (failed) die(`run aborted mid-flow: ${failed.message}`);
    console.log('RESULT: recorded');
  } finally {
    await browser.close();
  }
})().catch((e) => { console.error('FATAL', e && e.message ? e.message : e); process.exit(1); });
