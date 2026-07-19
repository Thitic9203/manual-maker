# Changelog

All notable changes to manual-maker are recorded here. Versions follow semver (major.minor.patch).

## [0.18.0] - 2026-07-19

The finished manual now lands somewhere the user can actually find it.

### Changed
- **The delivered file is written to `~/Downloads/` itself — never a subfolder** (`SKILL.md` Step 7).
  Previous runs invented a per-run `output/` directory nested beside the user's source material, so
  the deliverable ended up two folders deep next to the inputs it was built from. The rule is now
  explicit: no `output/` folder, no per-run directory, no nesting beside the sources. A by-role or
  by-module split puts **every** volume in that same place, told apart by filename
  (`คู่มือการใช้งาน <ระบบ> - <บทบาท>.docx`), not by folder.
- **Working files are kept out of `~/Downloads`.** Screenshots stay in `manual-assets/<slug>/` and
  per-section drafts in `manual-drafts/<slug>/`; only the finished document is copied out. An
  existing file of the same name is **never** silently overwritten — ask first.
- **Step 9 reports the deliverable as that exact path**, one line per volume.
- **Intake no longer asks where to save** (`references/intake.md`, near Q18) — the location is a
  constant, not a question. It is stated to the user alongside the output format instead.

## [0.17.0] - 2026-07-19

A manual is now written by a small team instead of one thread, and reviewed หัวข้อย่อย by หัวข้อย่อย
instead of all at once at the end.

### Added
- **Parallel Steps 4–6** (`references/parallel.md`). Capture → annotate → draft is partitioned **by
  หัวข้อย่อย** and dispatched to **2–3 `manual-section-writer` agents** at a time. Partitioning is by
  section and **not** by phase on purpose: "เลขในวงแดง = เลขขั้นตอน 1:1" is an invariant *inside* a
  หัวข้อย่อย, so a "one agent screenshots, another writes" split would force two agents to renegotiate
  step numbers across a boundary.
- **`manual-section-reviewer`** — **one** reviewer (never more; several would judge terminology and
  tone inconsistently) reviews each หัวข้อย่อย the moment its writer hands it over, so defects surface
  while they are still cheap to fix. It is **read-only**: it reports, the owning writer fixes.
- **`ASK` before deciding.** Reviewer findings are split into `FIX` — the confirmed table or the
  locked-term list already dictates the one correct answer (a synonym for a locked term, a ครับ/ค่ะ
  particle, a leftover placeholder, วง present when `annotations: none` was ordered) — and `ASK`,
  which is **everything else and everything the reviewer is unsure of**. Subagents cannot talk to the
  user, so every `ASK` and every writer `BLOCKED` **comes to the user in chat** before a fix is
  chosen. A หัวข้อย่อย with an open question is **not done** and never reaches the file.
- **Progress table roughly every 10 minutes** (`hooks/progress-tick.sh`, `PostToolUse`). During the
  long stretch the work is invisible to the user, so the run reports `~N% เสร็จ` plus a
  `ขั้น | สถานะ` table with measurable numbers.

### Changed
- `SKILL.md` Steps 4–6 now describe the fan-out and its prerequisites: the Step 2 gate, a **numbered
  outline assigned before dispatch**, ingested sources, locked terms, and a saved `storageState`.
  Login happens **once in the main thread** — three concurrent logins risk locking the account and
  spread the credential further than needed — and writers reuse the session read-only.
- `doc-coauthoring` is still invoked **once, in the main thread**, for the document-level voice and
  structure contract that every writer drafts against. Per-writer invocation would yield three
  different styles — the exact defect the manual is judged on.

### Unchanged (deliberately)
- **The 5-layer delivery gate.** Per-section review covers layers 1–4 *at section level* only; font
  fallback, คำพราก, TOC, cross-chapter numbering and all of layer 5 are created by the conversion and
  provable only on the exported file. Step 8 still runs in full, on the built file, and "every
  section passed its review" is **not** evidence for any layer.

### Notes
- Claude Code has **no time-based hook**, and `SubagentStop` supports only `decision`/`reason` — not
  `hookSpecificOutput.additionalContext` — so it cannot inject a message. The 10-minute update
  therefore rides `PostToolUse` (matcher `Task|Bash`) with a wall-clock throttle: **no tool call, no
  tick**. Reporting on every section status change remains the primary mechanism; the hook is a
  silence net. It is inert unless `~/.manual-maker/state/run.active` exists (created at the Step 2
  gate, deleted at Step 9), fail-silent, self-clears a marker older than 12h, and opts out with
  `MANUAL_MAKER_NO_PROGRESS=1` (interval via `MANUAL_MAKER_PROGRESS_INTERVAL`).
- Trade-offs recorded in `RISK_REGISTER.md` **MM-004**.

## [0.16.0] - 2026-07-19

A manual can no longer be handed over until it has been proven correct.

### Added
- **รีวิว 5 ชั้น + delivery gate** (`references/review.md`). Before this, review was a flat 19-item
  checklist that Claude self-assessed and then reported "before export" — nothing stopped a manual
  from being delivered with the checklist waved through. Now five layers must each pass **with
  evidence**, judged against the Step 2 confirmation table:
  1. **ตรงตามที่ยืนยัน** — scope, การแบ่งเล่ม (Q9), ภาษา, ฟอนต์, format, and the annotation mode.
  2. **ทุกอย่างมีที่มา** — every step traces to the live system + the user's source; a chapter with no
     source is cut, never invented.
  3. **ภาพ** — real, full-screen, red-circle numbers matching step numbers 1:1, names masked.
  4. **ตัวหนังสือและตัวเลข** — numbering + TOC, spelling, **คำพราก**, locked terms, tone.
  5. **รูปเล่ม** — cover, header, footer `PAGE` field, TOC field, fonts per the user's format.

  Gate rules: **ตรวจไม่ได้ = ไม่ผ่าน** (no "น่าจะผ่าน"); one FAIL means fix and **re-review all five**,
  since fixing one layer breaks another; review the **exported file**, never the draft in
  conversation; no delivery with caveats attached.

- **`scripts/verify-doc.py`** — mechanical verifier for a built `.docx`, so judgement is spent on what
  a regex cannot settle. Checks placeholders, `w:cs`, `w:lang w:bidi`, locked terms split mid-word,
  invisible characters, image embedding + relationship resolution, cover/header/footer/`PAGE`/TOC,
  heading-number continuity, and credential leaks. Exit 1 blocks delivery. Verified in both
  directions against fixtures: it fails a deliberately broken document (4 defects, including a
  numbering gap `[1, 2, 4]`) and passes a well-formed one.

### Changed
- **Workflow reordered: build → review → publish.** The review has to run on the exported file, so
  Step 7 now *builds* the file, Step 8 is the 5-layer gate, and Step 9 publishes — only on 5/5.
  Previously review sat before export, which meant the conversion-time defects it most needed to
  catch (font fallback, dropped images, stale TOC, คำพราก) had not happened yet. Confluence
  publishing is outward-facing and now cannot precede a passing verdict.
- **Intake Q12 makes "ไม่มีวง" a first-class choice**, not just a deviation from the red-circle
  default. Both modes are correct; what fails review is a mismatch with what the user confirmed. The
  answer feeds `--annotations required|none`.
- `template.md`'s checklist is now explicitly the item-level detail of the five layers — same content,
  different view — rather than a second, competing review.

### Fixed
- **คำพราก is prevented at build time, not just caught at review.** Its two causes are now documented
  and required in `docx-build.md`: a space or break inserted inside a Thai word, and a Thai run with
  no `w:lang w:bidi`, which leaves Word without a dictionary so it breaks mid-word. Every Thai run
  must carry both `w:cs` and the language tag.
- The คำพราก check is scoped to the **locked terms** rather than any Thai space. Probing a fixture
  showed a naive "Thai space Thai" rule flags legitimate phrase spacing — Thai separates phrases with
  spaces — which would have made the check almost all false positives.

## [0.15.0] - 2026-07-19
### Added
- **Auto-preflight — the skill now sets up its own tooling.** New `skills/manual-maker/scripts/preflight.sh`
  checks and installs what a screenshot run needs (Playwright, the matching Chromium build, Pillow).
  Users no longer have to know — or be told — that anything must be installed.
  - `--check` runs during intake (read-only) and its result table becomes the *เครื่องมือที่ต้องใช้* row
    of the Step 2 confirmation summary, download sizes included.
  - `--install` runs right after the user's existing "go" — **no second confirmation gate**.
  - Skipped entirely when screenshots = no, so a text-only manual downloads nothing.
  - Installs into the skill-owned sandbox `~/.manual-maker/runtime/`; the user's projects and global
    npm space are never modified. Idempotent — a satisfied machine is a no-op.

### Fixed
- **Capture no longer fails on a machine that looks ready.** Two real failure modes found by probing
  a live install, now both closed by preflight:
  - A global `npm i -g playwright` does not make `require('playwright')` resolve from an arbitrary
    cwd, so capture scripts threw despite the package being installed. Capture now runs with
    `NODE_PATH="$HOME/.manual-maker/runtime/node_modules"`.
  - A populated `~/Library/Caches/ms-playwright/` is not proof Chromium is usable — cached builds are
    version-specific. Preflight now tests Playwright's own `chromium.executablePath()`.

## [0.14.1] - 2026-07-19
### Fixed
- **Closed the one-session gap — `/manual-maker` now works from the very first session that has the plugin.** 0.14.0 auto-installed the shim, but Claude Code reads command files when a session *starts*, so the file the hook had just written was not in that session's command table: a user who installed the plugin, restarted, and typed `/manual-maker` still got `Unknown command` once. Measured directly — deleting the shim and running a session showed the hook creating the file yet the command still failing in that same run, then resolving in the next. Claude Code delivers the user's typed text to the skill alongside that error, so on a first install the hook now includes a directive telling Claude to treat a failed `/manual-maker` as an invocation and run the `manual-maker:manual-maker` skill with the remaining text as args, rather than telling the user the command is unavailable. The directive is emitted **only** on the session where the shim was freshly created — from the next session the command resolves natively and the hook is silent again. Covered by an 11-assertion scenario test (fresh install emits the directive; second session, stale refresh, foreign file, and opt-out all stay silent).

## [0.14.0] - 2026-07-19

Bare `/manual-maker` now works for everyone, with nothing to install by hand.

### Added
- **The SessionStart hook installs the bare-name shim automatically.** `hooks/check-version.sh` copies `shim/manual-maker.md` to `~/.claude/commands/manual-maker.md` on session start, so `/manual-maker` resolves without the user running a `curl`. It becomes usable on the next session (Claude Code reads command files at startup); the hook says so once, then stays silent. Rails: never overwrites a file lacking the `managed-by: manual-maker-plugin` marker (a hand-written `/manual-maker` is left alone), no-op when the content already matches, silent refresh when the shipped copy changes, atomic temp-file + `mv`, fail-silent on any error or missing `$HOME`. Opt out with `MANUAL_MAKER_NO_SHIM=1`. Recorded as `RISK_REGISTER.md` MM-003; the manual `curl` is kept in the README as a collapsed fallback.

### Fixed
- **Corrected the 0.13.0 explanation of *why* bare fails.** 0.13.0 blamed a name collision between `commands/manual-maker.md` and `skills/manual-maker/`, reasoning from a doc line that says the plugin prefix is "optional unless there are name collisions". That doc line does not match Claude Code 2.1.210. Measured with a throwaway probe plugin run headless: a plugin command with **no collision anywhere** still failed bare, a frontmatter `aliases:` key was ignored, and only the `/plugin:command` forms resolved. So the prefix is unconditional and no rename, alias, or manifest field can change it — the conclusion in 0.13.0 was right, the reason was not. `CLAUDE.md` now records the measurement so the three tempting non-fixes are not retried.

## [0.13.1] - 2026-07-19
### Fixed
- **Shim install command now uses `/usr/bin/curl` (full path).** The 0.13.0 snippet used bare `curl`, which resolves to a MacPorts/Homebrew build on many of the team's machines and fails the TLS handshake to `raw.githubusercontent.com` (`unable to establish a secure connection`) — so the shim install died on the exact machines that needed it. macOS's system curl fetches it fine; the README notes plain `curl` is correct on Linux.

## [0.13.0] - 2026-07-19

Fixes the `/manual-maker` → `Unknown command` dead end. No change to the manual-making workflow itself.

### Fixed
- **Corrected the documented invocation to `/manual-maker:manual-maker`.** The README previously showed bare `/manual-maker` and described the namespaced form as a collision-only fallback. That is wrong: Claude Code namespaces **every** plugin command and plugin skill as `/plugin-name:command-name` by design, so bare `/manual-maker` always returns `Unknown command`. Users following the README hit a dead end on their first command.

### Added
- **`shim/manual-maker.md` — opt-in, one-`curl` install for the short form.** User-level commands (`~/.claude/commands/`) are not namespaced, so copying this file there makes bare `/manual-maker` work on that machine, for every project. The shim is a pure pointer that invokes the `manual-maker:manual-maker` skill and holds no workflow logic, so it cannot drift from `SKILL.md`. Documented in the README with its trade-offs: it lives outside the plugin, so it does not auto-update and is not removed by `/plugin uninstall`, and it is per-machine.
- **`CLAUDE.md` gotcha** recording that the prefix is mandatory and unfixable from the repo — including the three tempting non-fixes (rename the command, add an alias field, delete `skills/manual-maker/`) and why `shim/` must never move under `commands/`.

### Note
- No frontmatter key, manifest field, or marketplace setting can expose the bare form — verified against the official Claude Code docs. Typing the natural-language trigger (`ทำคู่มือระบบ X`) still needs no slash command at all.

## [0.12.0] - 2026-07-19

Headless, non-intrusive screenshot capture — aligned with the ols-qa `/testing-ticket-workflow` bot. Same scope, all gates preserved.

### Changed
- **Screenshots now capture with headless Playwright by default (`chromium.launch({ headless: true })`).** `references/screenshots.md` — the capture runs in its own headless browser, so it never takes over the user's real screen: no focus-stealing window, no "Claude is controlling the screen" glow, no mouse cursor, and the user keeps working while every screen is captured in one unattended pass.
- **Headless, env-seeded login.** A `login()` helper authenticates by reading the credential from the **environment** (`process.env.EMAIL` / `process.env.PW`) or a pre-saved `storageState` and reuses that session for every capture — Claude never types a password into a live form by hand. Credentials stay session-only: never pasted into chat, hardcoded, committed, logged, or echoed (`.env` behind `.gitignore`; summaries show `password provided (not shown)`).
- **Rewrote rule #8** in `SKILL.md` from "Claude never types a password / user logs in" to the headless env-seeded credential discipline; updated Step 4 accordingly.
- **Glow-border and cursor cleanup are now fallback-only.** The headless path produces a clean full-page PNG with neither, so rules 2–3 in `screenshots.md` and the clarity checklist in `template.md` apply only to the screen/clipboard fallback (SSO/MFA/captcha), where the user logs in on their own screen.
- **Intake wording** (`references/intake.md` Q3/Q11/Q12) updated to describe headless env-seeded capture.

## [0.11.0] - 2026-07-19

Five usability fixes for the actual manual-making run — no new scope, all gates preserved.

### Changed
- **Screenshots: direct-to-disk is now the primary capture path.** `references/screenshots.md`
  puts **Playwright `page.screenshot({ path, fullPage: true })`** first — a full-page PNG written
  straight to disk with no per-image manual copy — and demotes the clipboard bridge
  (`Ctrl+Cmd+Shift+4` → `osascript`) to a fallback for when Playwright can't reach the screen.
  This removes the single biggest cost of a large manual (dozens of manual copies). `SKILL.md`
  Step 4 points at the same rule.
- **Deterministic image naming/folder convention.** All figures for a run live in one folder,
  **`manual-assets/<slug>/`**, named **`<section>-<step>.png`** (e.g. `05-2-01.png`) — figure ↔
  step ↔ filename map 1:1, so red circle numbers align with step numbers by construction and a
  40-image manual never gets scrambled. `/tmp` is scratch only. Documented in `screenshots.md`
  and `template.md` (quality axis 3 + example).
- **Default output format changed `Confluence` → `Word (.docx)`.** The Atlassian MCP publishes a
  Confluence page's **body/structure only — it does not upload screenshot files**, so it was a
  broken default for image-heavy manuals (the usual case). `.docx` embeds screenshots reliably.
  Confluence remains an option, with an explicit caveat (attach images manually or reference a
  pre-hosted URL). Consistent across `intake.md` Q17, `SKILL.md` export table, `profile.md`, and
  the README (design-decisions table + Troubleshooting).
- **Intake sequencing: default-bearing questions asked as one batch.** `intake.md` now asks the
  *(ต้องถาม)* questions one at a time (1, 2, 3, 4, 5, 6, 9, 13, 15, 17) but collapses the
  default-bearing ones (7, 8, 10, 11, 12, 14, 16, 18, 19, 20) into a **single confirm-batch** —
  fewer round-trips for a first-time run, no gate weakened. `SKILL.md` Step 1 updated to match.

### Added
- **Intake Q19/Q20 — Support & Troubleshooting/FAQ sources.** The template's Troubleshooting/FAQ
  and Support sections are now **sourced or skipped, never invented**: Q20 asks for a known-issues
  source and Q19 for a support channel; with no source the section is **omitted** (enforces
  ห้ามมโน). Wired through the Confirmation Gate summary row, `template.md` sections 7/9, a new
  final-review checklist line, and the saved profile (`support` / `faq_source`, non-secret).

## [0.10.1] - 2026-07-19
### Changed
- Release-only version bump so auto-update installs pick up the `references/template.md`
  document-split consistency fix that landed on `main` after the 0.10.0 tag (auto-update fires
  only when the `version` string changes). No new behavior beyond 0.10.0.

## [0.10.0] - 2026-07-19
### Added
- **Intake Q9 — document split (การแบ่งเล่มเอกสาร).** The intake now always asks, as explicit
  options, how the manual should be divided: **(ก) by user role** (one volume per role, e.g.
  admin / learner / instructor), **(ข) by system or module**, or **(ค) a single combined
  volume**. No default — if (ก)/(ข) is chosen the skill asks for the role/system list and
  confirms the volume names before starting. The choice appears in the pre-start Confirmation
  Gate summary table and is saved in the per-system profile (`split` field), and the draft step
  produces exactly one deliverable per confirmed volume.

### Changed
- Intake questions Depth through Version renumbered (old Q9–Q17 → new Q10–Q18) to make room
  for the new Q9; `SKILL.md` terminology cross-reference updated (Q14 → Q15).
- `references/template.md` — new "Document split" section reflecting multi-volume output, with a
  resolution rule for base-template styling vs by-role/-module packaging, and a matching
  final-review checklist line.

## [0.9.0] - 2026-07-14
### Added
- **`references/screenshots.md`** — binding capture & annotation contract, written from a real
  government deliverable run. Real live-system screens only (no placeholder boxes, no mock-ups, no
  redrawn tables); **full screen — never crop the content**, remove only the Claude screen-control
  glow border (and protect the orange agency logo an "orange" detector would otherwise eat); **no
  mouse cursor** (remove its peach shadow by colour test, not a rectangle — a rectangle clips
  adjacent text); **red numbered circles that map 1:1 to the step numbers**, ≤ 5 per image; steps
  written with the system's real menu/button wording; people's names masked (students are minors).
  Also documents the working pipeline: the browser MCP's `save_to_disk` returns **no file path**, so
  bridge through the clipboard (`osascript` → PNG) → **Pillow on `/usr/bin/python3`** (the Homebrew
  `python3` has no PIL; the Desktop can be TCC-blocked → work in `/tmp`) → embed.
- **`references/docx-build.md`** — how to build the Word file. When the user supplies a base template
  (ต้นแบบ), **the template is the deliverable**: reuse its cover, header, footer (`PAGE` field), TOC,
  styles, and role-based chapters **exactly** — docx-js cannot open an existing file, so edit the
  OOXML (`unzip → word/document.xml → zip`) and copy an existing image block when embedding a picture
  (swap `r:embed` + **both** extents, recomputing `cy` from the aspect ratio). Font **TH SarabunPSK**,
  body 16 pt / headings 18 pt bold, with **all four `w:rFonts` slots** set — Thai is a complex script
  and a missing **`w:cs`** silently falls back to another font. Plus the `~$….docx` Word-lock
  handling ("close without saving → reopen → Update fields? → Yes").

### Changed
- **SKILL.md** — three new non-negotiable rules: the base template is reproduced exactly, every figure
  is a real full-screen system screenshot with step-matched red circles, and **Claude never types a
  password** (the user logs in; Claude captures read-only). Steps 3/4/8 now point at the two new
  references.
- **`references/template.md`** — the base template overrides the generic outline (role-based chapters:
  บทนำ / ครูผู้สอน / ผู้เรียน / ผู้ดูแลระบบ); Thai font default recorded (TH SarabunPSK 16/18 + `w:cs`);
  the image axis rewritten to the screenshot contract; six new final-review checks (template fidelity,
  real screenshot, clean image, circles-match-steps, names masked, image really embedded) plus the
  Word "Update fields" handover step.
- **`references/intake.md`** — the base-template question is now binding (build **on** it, never hand-
  build a look-alike); annotation defaults to red numbered circles matching the step numbers on
  full-screen shots; the font question carries the Thai default and the `w:cs` warning.

## [0.8.0] - 2026-07-14
### Added
- **Remembered intake — stop re-asking what a user already answered.** After the Confirmation Gate, manual-maker now saves that user's confirmed intake for the system to a **per-user local** profile at `~/.manual-maker/profiles/<slug>.json`. On the next run for the same system it loads the profile, shows it back, and asks **only what is missing or changed** — the stable answers (sources, audience/scope, screenshot annotation, font & size, numbering, locked terminology, output format/destination) are not re-asked. New reference: `skills/manual-maker/references/profile.md`.

### Security
- **Credentials are never persisted.** Passwords, usernames, tokens, cookies, and VPN secrets are excluded from the profile and are always asked **fresh, in-session**, exactly as before. Only `vpn_required` (a boolean) is stored.

### Changed
- Intake reconciled with the profile: **URL(s) and VPN state are pre-filled from the profile and re-confirmed each run** (shown as the default, user confirms they still hold) rather than asked from scratch — live access is still verified every time. The **Confirmation Gate is unchanged and still mandatory**; a profile only ever stores user-confirmed data (saved *after* the gate, never before). Updated `SKILL.md`, `references/intake.md`, and the `/manual-maker` command to match.

## [0.7.0] - 2026-07-14
### Added
- **`/manual-maker` slash command** — a one-shot entry point that drives the whole handbook pipeline to completion. The user runs `/manual-maker ทำคู่มือ <ระบบ>` and the command loads the `manual-maker` skill, lays out the full `Intake → Confirm → Ingest → Screenshots → Draft → Template+Quality → Final review → Export` TodoWrite, and **auto-advances between steps** instead of pausing after each one.
- The command preserves the skill's three mandatory human gates — one-at-a-time **intake**, the **confirmation gate** before screenshots/drafting, and **publish confirmation** before any outward-facing Confluence/web post — because a manual must stay sourced, not invented (ห้ามมโน). Momentum is automated; the correctness gates are not.

### Notes
- Additive only: the skill's auto-trigger on "ทำคู่มือ / write a manual" is unchanged. The command just adds an explicit `/`-invocable path and stronger drive-to-completion framing. No existing behavior removed.

## [0.6.0] - 2026-07-14
### Changed
- **Zero-touch self-update.** `hooks/check-version.sh` no longer only notifies — on SessionStart, when `main` is ahead of the installed version, it now runs `claude plugin update` **in the background** and the new version applies on the next session / `/reload-plugins`. Existing installs (v0.6.0+) upgrade themselves with no user action. Safety rails: non-blocking (detached), single-flight `mkdir` lock, uses the supported CLI (not a raw cache mutation), fail-silent when offline / up-to-date / no `claude` on PATH, and an **opt-out** via `MANUAL_MAKER_NO_AUTOUPDATE=1` (degrades to notify-only). Takes effect for updates from v0.6.0 onward; pre-0.6.0 installs update once to reach it.
- **Deliberate override of the prior notify-only policy**, chosen by the repo owner for true zero-touch on the plugin path. Trade-offs (bypasses Claude Code's per-marketplace auto-update opt-in; reimplements a native feature) are recorded in the new `RISK_REGISTER.md` (MM-001).
- **README "Update" section rewritten** to document the self-update behavior, the opt-out, and the cleaner native alternatives (per-user `/plugin` toggle, or team-wide `"autoUpdate": true` in `extraKnownMarketplaces`). CLAUDE.md updated to match.

### Added
- `RISK_REGISTER.md` — records trade-off decisions (MM-001: self-updating hook).

## [0.5.0] - 2026-07-11
### Changed
- **Document tone policy** — the generated manual is now written in formal, professional, human written language: **no first/second-person pronouns** (ผม/คุณ/ท่าน), **no sentence-final particles** (ครับ/ค่ะ/นะ), natural rather than machine-translated. Encoded in `template.md` (new Language & tone section + a review-checklist item) and enforced in the `SKILL.md` draft step.
- **Output-format question made explicit** — intake now always asks for the file format (**Word (.docx) / PDF / Confluence / web**) when the user hasn't stated one, phrased for non-technical users.
- Reviewed every intake question for correct spelling and wording; questions are asked one at a time in formal Thai, and the confirmation prompt dropped its trailing particle.

## [0.4.1] - 2026-07-11
### Fixed
- SessionStart version-notify hook now loads. `plugin.json` referenced `"hooks": "./hooks/hooks.json"`, but Claude Code auto-loads the standard `hooks/hooks.json`, so the explicit reference triggered a "Duplicate hooks file detected" error and the hook failed to load entirely (broken since it was added in 0.3.0). Removed the redundant `manifest.hooks` key — the hook still loads via auto-discovery.

## [0.4.0] - 2026-07-11
### Changed
- Intake (`intake.md`) rewritten: now asks for the **authoritative step source** (Confluence page / spec / flow / example doc) so every step is sourced, not guessed. Also adds URL/login/VPN asked fresh each run, screenshot **annotation** (boxes + step numbers), **font & size**, a numbering scheme, and a **locked terminology** list.
- `SKILL.md`: added a mandatory **confirmation gate** (summarize all inputs → wait for explicit "go" before any screenshot or drafting), a **never-assume / no-scope-creep** rule, a source-ingestion step, and a **detailed final-review checklist** step before delivery.
- `template.md`: added the four quality axes — font & size, numbering consistency, image clarity + annotation, terminology consistency — and a final delivery checklist.
- Credentials are used in-session only — never written into the manual, repo, or logs, and never printed back.

## [0.3.0] - 2026-07-11
### Changed
- No functional changes — a version bump used to exercise the SessionStart update notice end-to-end (installed 0.2.0 sees 0.3.0 on GitHub and notifies). Confirms the release path (bump script → push → notify) works.

## [0.2.0] - 2026-07-11
### Added
- `scripts/bump-version.sh` — one command bumps the version across `plugin.json`, `marketplace.json` (both fields), the README badge + version line, and stamps a CHANGELOG entry.
- SessionStart hook (`hooks/check-version.sh`) — on every new session it compares the installed version to `main` on GitHub and, when a newer version exists, tells the user how to update. Notify-only, offline-safe, never mutates the install.
- Version badges at the top of the README.

## [0.1.0]
### Added
- Initial release: intake → (screenshots) → doc-coauthoring draft → team template → export (Confluence / PDF / docx / web).
