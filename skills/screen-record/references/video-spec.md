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

### 2. It looks like a person recording their own screen

A viewer should not be able to tell a script drove it. Two things make the difference, and both
are on by default:

**A mouse pointer.** Playwright's video has none, so without one a viewer watches controls
activate with nothing touching them. The recorder draws an arrow — but it does **not** animate
one. The drawn arrow listens to the page's own `mousemove` / `mousedown` / `mouseup` and follows
the **real** pointer, so it can only ever be where the browser actually is, and the click flash
can only fire on a real click. A painted-on animation could show a click that never happened;
this cannot. Before every click, hover, select or `scrollTo`, the real pointer **glides** to the
target over ~28 steps and pauses ~260 ms — so genuine `:hover` states fire on the way in, the way
they do for a person.

**Typing that is typed.** `fill` clicks the field, clears it, then enters the value one character
at a time (`typeDelay`, default 55 ms). A value that appears in a single frame next to a moving
pointer is the tell that gives an automated clip away.

Everything else stays out of the frame:

- The pointer is the **only** thing drawn into the page. No banner, no URL strip, no watermark,
  no step counter. Anything diagnostic goes to the run log, which no viewer ever sees.
- Headless Chromium adds no *"controlled by automated test software"* bar to page content, and
  Playwright records page content only — the browser's own chrome is never in the video.
- Scrolling is paced at ~250 px per 350 ms, so the page moves the way someone reading it would
  move it rather than jumping between states.
- **Stills hide the pointer.** In a video the arrow is the point; in a screenshot it is something
  parked on top of words a reader needs. It is hidden for the shutter and restored right after.

`"cursor": false` turns the pointer off (and with it the glide) for a clip that should look like
pure navigation. `"typeDelay": 0` fills instantly. Both are the exception, not the default.

### 3. The run fails closed

A step that declares `waitFor` and never sees it **aborts the run with a non-zero exit**. A clip
that stopped before reaching its target is not a shorter success — it is a failed recording, and
the honest outcome is "blocked, with the reason". The video is still finalized so the failure can be
diagnosed, but the command exits non-zero and says what was never reached.

## Narration (optional)

Asked for at intake — none, Thai, or English — and produced in two passes, because the voice has to
be measured *before* the recording so the flow can be paced to it.

| Setting | Value | Why |
|---|---|---|
| Voice (th) | **`th-TH-NiwatNeural`** (male) · **`th-TH-PremwadeeNeural`** (female) | Neural. macOS `say` is not an alternative: its only Thai voice is female and audibly synthetic |
| Voice (en) | **`en-US-GuyNeural`** (male) · **`en-US-AriaNeural`** (female) | Neural |
| Gender | **asked at intake** | Never chosen for the user; `male` only when they said so or a saved profile confirms it |
| Rate | **`+4%`** | A touch above default reads as engaged rather than sleepy |
| Pause inside a clause | **0.22 s** | |
| Pause at a sentence end | **0.40 s** | A listener needs longer to close a sentence than a clause |
| Phrase ceiling | **62 chars (th) / 95 (en)** | Thai has no inter-word spaces, so a long line hits the ear as one breathless run |
| Loudness | **`loudnorm I=-16 TP=-1.5 LRA=11`** | Every line at the same level — the difference between narration and a voice memo |
| Audio codec | **AAC 160 kbps** | Video stream is copied, never re-encoded |

**Phrasing is where narration stops sounding synthetic.** Lines are split at real boundaries — the
author's punctuation first, then Thai/English connectives that actually *start* a clause. Words that
usually *end* one are deliberately not break points: cutting before `แล้ว` splits `เรียบร้อยแล้ว`
in half, and a listener hears that as a stumble. Same for `ให้`, which lives inside `ทำให้` far more
often than it opens a clause.

**The two passes:**

```bash
narrate.py --prepare play-TC_01.json      # speak each line, measure it, write play-TC_01.saydur.json
                                          # (--lang / --gender / --voice override the play file)
node record.js play-TC_01.json            # record — each narrated step is held open until its line ends
narrate.py out/TC_01.mp4                  # speak it onto the clip at the measured offsets
```

Pass one is what keeps the voice off the next action: without it, measured on a real run, three of
four lines ran 5–6 s into the following step. Synthesized phrases are cached by voice+rate+text, so
the second pass re-uses pass one's takes instead of paying for them twice — and cannot end up with
two slightly different readings of the same sentence.

**Two things the muxer will not do.** It never re-encodes the video (`-c:v copy`), and it never
trims it: `-shortest` was removed after it cut a 19.1 s clip down to 17.3 s to match a shorter
narration track. The picture is the deliverable; the audio fits around it.

Play-file shape:

```json
{
  "narration": { "lang": "th", "gender": "female" },
  "steps": [
    { "do": "click", "selector": "text=สร้างคอร์ส", "waitFor": "text=สร้างคอร์สใหม่",
      "say": "คลิกปุ่มสร้างคอร์ส ระบบจะเปิดหน้าฟอร์มสำหรับกรอกรายละเอียด" }
  ]
}
```

Every `say` line comes from the **same source as the steps**. A narrated sentence that is not in
the source is an invented claim about the product, spoken aloud, in a deliverable.

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
| `cursor` | `true` | Draw the mouse pointer and glide it to each target before acting |
| `glideSteps` | `28` | Pointer travel resolution — higher is slower and smoother |
| `typeDelay` | `55` ms | Per character for `fill`. `0` = set the value instantly |
| `narration` | — | `{ "lang": "th" \| "en", "gender": "male" \| "female", "voice"?: "..." }` — see Narration above |
| `sayDurations` | auto | Path to the `--prepare` output; defaults to `<play>.saydur.json` |
| `tail` | `1500` ms | Hold on the last frame so it lands in the video |
| `login` | — | Omit for a public flow |
| `storageState` | — | Path to a saved session — used instead of logging in (the SSO/MFA route) |
| `saveStorageState` | — | Path to write the session to after logging in, to reuse next run |
| `headless` | `true` | `false` only when debugging a selector by eye |

### Step actions

| `do` | Fields | Notes |
|---|---|---|
| `goto` | `url` | Relative resolves against `baseUrl` |
| `click` | `selector` | The pointer glides to the element first |
| `fill` | `selector`, `value` | Clicks the field, clears it, types it out. Per-step `typeDelay` overrides the default. Never put a credential here |
| `select` | `selector`, `value` | `<select>` option |
| `hover` | `selector` | The pointer glides there — real `:hover` fires |
| `press` | `key` | e.g. `Enter`, `Escape` |
| `scroll` | `to` (px, optional) | Paced ~250 px / 350 ms — an instant jump reads as a cut |
| `scrollTo` | `selector` | Bring an element into view, then land the pointer on it (this is how layer 3 "scroll to menu XX" is satisfied) |
| `waitFor` | `selector` | Explicit wait as its own step |
| `wait` | `ms` | Last resort — prefer waiting for something real |

Every step also accepts:

- **`label`** — printed in the run log; use the step's wording from the source so the log can be
  read against it.
- **`waitFor`** — what must be visible *after* the action. **Fail-closed** (see above). Put one on
  every step that navigates or changes state.
- **`expect`** — the state that proves an expected result. Asserted, then captured as
  `<name>-ER_NN.png`. This is quality-gate layers 4 and 5.
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
