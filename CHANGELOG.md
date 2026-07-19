# Changelog

All notable changes to manual-maker are recorded here. Versions follow semver (major.minor.patch).

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
