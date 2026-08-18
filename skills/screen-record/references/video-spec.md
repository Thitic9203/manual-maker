# Video spec — the settings that make a recording match the reference clips

Every number here was taken from the recorder that produced the team's System / Integration / Unit
test recordings. They are **a set**, not a menu: change one and the output stops being comparable
with everything already delivered. Change them only when the user asks, and say what changed.

## The encode

| Setting | Value | Why this value |
|---|---|---|
| Viewport | **1920 × 1080** | Layer 1 of the quality gate. Below this, UI text stops being legible once the video is compressed. |
| `deviceScaleFactor` | **2** | Renders at 2× so glyphs are sharp. Playwright records at the requested `size` regardless, so this costs nothing in the video and makes the stills crisp. |
| Record size | **1920 × 1080** | Match the viewport. A recorded size smaller than the viewport downscales — the one thing layer 1 forbids. |
| Codec | **H.264 (`libx264`)** | Plays everywhere: browsers, Jira, Drive, QuickTime, Confluence preview. |
| Quality | **CRF 20** | Visually near-lossless on UI content. CRF 23+ starts smearing small Thai glyphs; CRF < 18 inflates the file for no visible gain. |
| Preset | **slow** | Better compression at the same CRF — a smaller file at identical quality. Encoding takes longer; the recording does not. |
| Pixel format | **`yuv420p`** | Some players refuse `yuv444p`/`yuvj420p` outright. |
| Container flag | **`+faststart`** | Moves `moov` ahead of `mdat` so the file streams/previews without downloading in full. |

```bash
ffmpeg -y -i in.webm -c:v libx264 -crf 20 -preset slow \
       -pix_fmt yuv420p -movflags +faststart out.mp4
```

Playwright records **WebM**; the MP4 is the deliverable. Keep the `.webm` until the MP4 has passed
`verify-video.py` — it is the only way to re-encode without re-running the whole flow.

## Three structural properties (not flags — the recorder is built around them)

### 1. The login is never in the clip

Authentication runs in a **non-recorded** browser context. Its `storageState` — including httpOnly
session cookies and localStorage — is handed to a **second** context that has `recordVideo` on. The
clip therefore starts at the first real step.

This is a safety property, not a tidiness one: **no credential is ever on screen**, so a recording
can be attached to a ticket or shipped with a manual without a redaction pass.

```js
const authCtx = await browser.newContext({ viewport });
await login(authCtx, cfg);                    // reads SR_USER / SR_PASS from the environment
const state = await authCtx.storageState();
await authCtx.close();
const recCtx = await browser.newContext({ viewport, deviceScaleFactor: 2, storageState: state,
                                          recordVideo: { dir: out, size: viewport } });
```

If the app only hydrates its session after the shell has loaded once, set `login.warmUrl` — the
non-recorded context visits it, so the recorded one starts already logged in instead of opening on
a "could not load" state.

### 2. The URL is visible in every frame

Playwright records **page content**, not browser chrome — so a recorded clip has no address bar and
cannot show where it is. The recorder injects a 26 px strip that renders the **live**
`location.href`, updated on an interval.

It is **read from the page, never typed**: it reports where the browser actually is. That is what
makes it evidence rather than an edit. (It is written with `textContent`, never `innerHTML` — a URL
fragment can carry markup, and this strip renders a URL nobody controls.)

**Stills hide it.** The strip is display-hidden immediately before every screenshot and restored
after, so a figure destined for a manual carries no overlay.

Turn it off with `"urlBar": false` when the clip is for a manual and the strip would be noise.

### 3. The run fails closed

A step that declares `waitFor` and never sees it **aborts the run with a non-zero exit**. A clip
that stopped before reaching its target is not a shorter success — it is a failed recording, and
the honest outcome is "blocked, with the reason". The video is still finalized so the failure can be
diagnosed, but the command exits non-zero and says what was never reached.

## The play file

One JSON file per clip. It holds **no credentials** — those come from the environment.

```json
{
  "name": "TC_01",
  "baseUrl": "https://staging.example.com",
  "out": "~/Downloads/recordings",
  "login": {
    "url": "/login",
    "dismiss": ["button[aria-label=Close]", "text=ยอมรับ"],
    "openSelector": "//button[normalize-space(.)='เข้าสู่ระบบ']",
    "userSelector": "#email",
    "passSelector": "#password",
    "submitSelector": "//button[@type='submit']",
    "readySelector": ".avatar",
    "warmUrl": "/",
    "userEnv": "SR_USER",
    "passEnv": "SR_PASS"
  },
  "steps": [
    { "do": "goto",  "url": "/courses", "waitFor": "text=รายการคอร์ส", "label": "เปิดหน้ารายการคอร์ส" },
    { "do": "click", "selector": "text=สร้างคอร์ส", "waitFor": "text=สร้างคอร์สใหม่", "label": "กดสร้างคอร์ส" },
    { "do": "fill",  "selector": "#title", "value": "คอร์สตัวอย่าง", "label": "กรอกชื่อคอร์ส" },
    { "do": "click", "selector": "text=บันทึก", "expect": "text=บันทึกสำเร็จ", "label": "บันทึก" },
    { "do": "scroll", "label": "เลื่อนดูทั้งหน้า" }
  ]
}
```

### Top-level keys

| Key | Default | Meaning |
|---|---|---|
| `name` | *required* | File stem — produces `<name>.mp4`, `<name>.webm`, `<name>-ER_NN.png` |
| `baseUrl` | `""` | Prefix for relative step URLs |
| `out` | `recordings` | Output directory (created if missing) |
| `viewport` | `1920×1080` | See the table above before changing |
| `deviceScaleFactor` | `2` | |
| `crf` / `preset` | `20` / `slow` | |
| `settle` | `900` ms | Pause after each step, so the viewer can follow |
| `stepTimeout` | `30000` ms | Per-step ceiling |
| `urlBar` | `true` | The live-URL strip |
| `tail` | `1500` ms | Hold on the last frame so it lands in the video |
| `login` | — | Omit for a public flow |
| `storageState` | — | Path to a saved session — used instead of logging in (the SSO/MFA route) |
| `saveStorageState` | — | Path to write the session to after logging in, to reuse next run |
| `headless` | `true` | `false` only when debugging a selector by eye |

### Step actions

| `do` | Fields | Notes |
|---|---|---|
| `goto` | `url` | Relative resolves against `baseUrl` |
| `click` | `selector` | |
| `fill` | `selector`, `value` | Never put a credential here |
| `select` | `selector`, `value` | `<select>` option |
| `hover` | `selector` | |
| `press` | `key` | e.g. `Enter`, `Escape` |
| `scroll` | `to` (px, optional) | Paced ~250 px / 350 ms — an instant jump reads as a cut |
| `scrollTo` | `selector` | Bring an element into view (this is how layer 3 "scroll to menu XX" is satisfied) |
| `waitFor` | `selector` | Explicit wait as its own step |
| `wait` | `ms` | Last resort — prefer waiting for something real |

Every step also accepts:

- **`label`** — printed in the run log; use the step's wording from the source so the log can be
  read against it.
- **`waitFor`** — what must be visible *after* the action. **Fail-closed** (see above). Put one on
  every step that navigates or changes state.
- **`expect`** — the state that proves an expected result. Asserted, then captured as
  `<name>-ER_NN.png` with the URL strip hidden. This is quality-gate layers 4 and 5.
- **`settle`**, **`timeout`**, **`fullPage`** (for `expect` stills).

Selectors accept **CSS**, **`text=…`**, or an **XPath starting with `//`**.

## Running it

```bash
SR_USER='...' SR_PASS='...' \
NODE_PATH="$HOME/.manual-maker/runtime/node_modules" \
node "$SR/scripts/record.js" play.json
```

Seed the credentials **inline on the command** (as above) so they stay out of the shell profile,
out of any file, and out of the play file. Never echo them back; in summaries write
`password provided (not shown)`.

Then measure the result — a recording is not done until it has been verified:

```bash
"$SR/scripts/verify-video.py" ~/Downloads/recordings/TC_01.mp4
```
