# Screenshots — capture & annotation contract

Every figure in a manual is a **real screenshot of the live system**. These rules are not style
preferences — each one was paid for with rework on a real deliverable. **ห้ามผิดซ้ำ.**

## The six hard rules

### 1. Real screens only (ห้ามมโน)
- A figure is a **real screenshot of the live system**. Never a placeholder box, never a redrawn
  table / mock-up standing in for a screen, never a screen from a different role or system.
- If a screen shows **no data**, find the *real* cause (wrong class / year / term / week / role /
  account) — do **not** fabricate data and do **not** substitute another screen.
- Do **not** create records in the system to make a screen look full unless the user **explicitly**
  authorises it for that run.

### 2. Full screen — never crop the content (เต็มจอ)
- Capture the **whole application screen**. Do not crop to a region, do not "tidy" the edges.
- **The primary path (headless Playwright) produces a clean full-page PNG with no glow border and no
  cursor — nothing to remove.** The cleanup below applies **only to the fallback path** (screen /
  clipboard capture), which paints on the *"Claude is controlling the screen"* glow.
- Fallback only: the **only** thing that may be removed is the capture artefact — the orange/red glow
  border. Content stays; the glow goes.
- ⚠️ Fallback only: auto-detecting "orange" also matches the **agency logo** (OBEC's is orange/gold)
  and any highlighted cell. A naive orange-crop eats the logo. Either protect the logo's bounding box,
  or **neutralise the warm tint in the outer band** instead of cropping — safer, and loses nothing.

### 3. No mouse cursor
- **Headless Playwright never paints a cursor** — the primary path has nothing to clean.
- Fallback only (screen / clipboard capture): paint the cursor out, including its soft **peach
  drop-shadow**. Remove it by **colour test** (warm pixels → background), not with a blunt rectangle —
  a rectangle clips the text next to it (it ate a `09:00-10:00` label once).

### 4. Red numbered circles = the step numbers
- Draw a **filled red circle with a white number** on each click target.
- The numbers **must map 1:1 to the numbered steps** of that section's step table. Circle ① is step 1.
- If a step's target is not visible on that screenshot, either **capture that screen too**, or
  **rewrite the steps** so they describe only the actions visible in the figure. Never leave a
  mismatch between circle numbers and step numbers.
- **≤ 5 callouts per image.** Same colour, radius, and number font throughout the whole manual.

### 5. Steps use the system's real words
- Every step names the real **menu / button / tab / field** exactly as the system spells it.
- No template placeholder text (`[ระบุการดำเนินการขั้นตอนที่ 1 …]`) may survive into the delivery.

### 6. Privacy
- **Mask or blur real people's names** — especially **students (minors)** and teachers.
- Never show credentials, tokens, or a filled-in password field.

## Where the images live (deterministic naming — do this from image #1)

All figures for a run go in **one** folder: **`manual-assets/<slug>/`** — `<slug>` is the same
system slug `profile.md` uses. Name every file **`<section>-<step>.png`** (e.g. `05-2-01.png` =
section 5.2, step 1). Figure ↔ step ↔ filename map 1:1, so a 40-image manual never gets scrambled
and the red circle numbers line up with the step numbers by construction.

`/tmp` is **scratch only** (clipboard bridge + PIL work). The **final annotated PNG** is always
saved into `manual-assets/<slug>/` under its deterministic name — that copy is what gets embedded.

## Prerequisites — installed for the user, never asked of them

`scripts/preflight.sh` handles this: `--check` during intake (report only), `--install` after the
user's "go". It installs Playwright, the matching Chromium build, and Pillow into
**`~/.manual-maker/runtime/`** — a skill-owned sandbox, so the user's projects and global npm space
stay untouched. Idempotent; a satisfied machine is a no-op.

**Run every capture script with that sandbox on `NODE_PATH`:**

```bash
NODE_PATH="$HOME/.manual-maker/runtime/node_modules" node capture.js
```

Two traps this closes, both observed on a real machine:
- `npm i -g playwright` is **not** enough — Node does not resolve global packages from an arbitrary
  cwd, so `require('playwright')` throws even though the package is installed.
- A populated `~/Library/Caches/ms-playwright/` is **not** proof Chromium is usable — those builds
  belong to specific Playwright versions. Preflight asks Playwright for its own
  `chromium.executablePath()` and tests that path instead.

## Pipeline that actually works (macOS)

**Primary path = headless Playwright — non-intrusive.** It runs in its own **headless browser**
(`chromium.launch({ headless: true })`), so it **never takes over the user's real screen**: no window
steals focus, no *"Claude is controlling the screen"* glow, no mouse cursor, and the user keeps
working while every screen is captured in one unattended pass. This is the same approach as the
ols-qa `/testing-ticket-workflow` capture bot (`capture_one.js`).

1. **Log in headlessly, once — env-seeded (never a typed password).** A small `login()` helper drives
   Playwright to the login page (dismiss any cookie / commemorative modal first), then fills the
   credential **from environment variables** the user seeded — `process.env.EMAIL` / `process.env.PW`
   (or system-specific names). Submit, wait for the post-login signal (avatar / redirected URL). Save
   the session and **reuse it** for every capture:
   ```js
   const { chromium } = require('playwright');
   const browser = await chromium.launch({ headless: true });
   const authCtx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
   // login() fills #email / #password from process.env — Claude never types the password itself
   await login(authCtx, process.env.EMAIL, process.env.PW);
   const state = await authCtx.storageState();   // capture the logged-in session once
   await authCtx.close();
   const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, storageState: state });
   const page = await ctx.newPage();
   ```
   Credentials come **only** from the environment (or a pre-saved `storageState.json`) — never pasted
   into chat, never hardcoded, never committed. Put any `.env` behind `.gitignore`. If the project
   already has a Playwright config / fixture / saved `storageState`, **reuse it** once the user
   confirms that env is valid — do not re-implement login.
2. **Reach each screen read-only, then get the pixels — direct-to-disk.** Navigate to each target URL
   (never click create / edit / delete on a live system while capturing) and write the full-page PNG
   straight to disk:
   ```js
   await page.goto(url, { waitUntil: 'domcontentloaded' });
   await page.screenshot({ path: 'manual-assets/<slug>/<section>-<step>.png', fullPage: true });
   ```
   No per-image manual copy, no screen takeover — capture every screen in one pass. This removes the
   single biggest cost of a large manual.
   - **Fallback — clipboard bridge (Chrome MCP / screen capture), for screens Playwright can't reach**
     (SSO / MFA / captcha, or auth that can't be automated). Here the **user logs in on their own
     screen** and Claude captures read-only; the browser MCP's screenshot `save_to_disk` returns an
     image id but **no filesystem path**, so bridge one screen at a time — the user copies the screen
     (macOS `Ctrl+Cmd+Shift+4`), then:
     ```bash
     osascript -e 'set d to (the clipboard as «class PNGf»)' \
               -e 'set f to (POSIX file "/tmp/shot.png")' \
               -e 'set fh to open for access f with write permission' \
               -e 'set eof fh to 0' -e 'write d to fh' -e 'close access fh'
     ```
     Use this **only** when the headless path can't reach the screen — it is slow at scale and is the
     path that needs the glow-border / cursor cleanup in rules 2–3.
3. **Annotate with Pillow.** `PIL` lives on **`/usr/bin/python3`** — the Homebrew `python3` on the
   PATH often has no PIL. The user's Desktop can be **TCC-protected** (reads fail with
   `Operation not permitted`): do the image work in `/tmp`, then **save the finished PNG into
   `manual-assets/<slug>/`** under its `<section>-<step>.png` name.
4. **Embed** into the document — see `docx-build.md`.

## Login — headless, env-seeded (credential discipline)

Login for capture is **headless and env-seeded**, the ols-qa way:

- **Claude never types a password into a live form by hand** (no computer-use / manual keystrokes on
  a login screen). Authentication is done by the **Playwright `login()` helper reading the credential
  from the environment** (`process.env.EMAIL` / `process.env.PW`) or a pre-saved `storageState.json`.
  The user seeds that env / session once; the raw secret is supplied by the environment, not entered
  by Claude.
- **Session-only.** The credential is used only to reach the screens for this run. It **never** reaches
  the manual, the repo, a log, a committed script, or the profile (`profile.md` never stores secrets).
  Any `.env` stays behind `.gitignore`.
- **Never echoed.** Do not print the password back; in summaries show `password provided (not shown)`.
- **Fallback (SSO / MFA / captcha):** if login can't be automated, the **user logs in on their own
  screen** and Claude captures read-only via the clipboard bridge above.
