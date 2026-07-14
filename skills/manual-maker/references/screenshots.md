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
- The **only** thing that may be removed is the capture artefact: the orange/red
  *"Claude is controlling the screen"* glow border. Content stays; the glow goes.
- ⚠️ Auto-detecting "orange" also matches the **agency logo** (OBEC's is orange/gold) and any
  highlighted cell. A naive orange-crop eats the logo. Either protect the logo's bounding box, or
  **neutralise the warm tint in the outer band** instead of cropping — safer, and loses nothing.

### 3. No mouse cursor
- Paint the cursor out, including its soft **peach drop-shadow**.
- Remove it by **colour test** (warm pixels → background), not with a blunt rectangle — a rectangle
  clips the text next to it (it ate a `09:00-10:00` label once).

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

## Pipeline that actually works (macOS)

1. **Reach the screen** — drive the browser **read-only** (Chrome MCP). Never click create / edit /
   delete on a live system while capturing.
2. **Get the pixels.** The browser MCP's screenshot `save_to_disk` returns an image id but **no
   filesystem path** — you cannot embed from it. Bridge through the clipboard:
   - the user copies the screen (macOS `Ctrl+Cmd+Shift+4`), then
   ```bash
   osascript -e 'set d to (the clipboard as «class PNGf»)' \
             -e 'set f to (POSIX file "/tmp/shot.png")' \
             -e 'set fh to open for access f with write permission' \
             -e 'set eof fh to 0' -e 'write d to fh' -e 'close access fh'
   ```
3. **Annotate with Pillow.** `PIL` lives on **`/usr/bin/python3`** — the Homebrew `python3` on the
   PATH often has no PIL. The user's Desktop can be **TCC-protected** (reads fail with
   `Operation not permitted`): copy the PNG into `/tmp` and do all image work there.
4. **Embed** into the document — see `docx-build.md`.

## Login — never type a password

Claude must **never** enter a password: not by hand, and not through an automation script that fills
a login form. The **user logs in**; Claude captures afterwards, read-only. Credentials never reach
the manual, the repo, a log, or a script committed anywhere.
