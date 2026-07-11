# Changelog

All notable changes to manual-maker are recorded here. Versions follow semver (major.minor.patch).

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
