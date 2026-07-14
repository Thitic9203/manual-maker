# Changelog

All notable changes to manual-maker are recorded here. Versions follow semver (major.minor.patch).

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
