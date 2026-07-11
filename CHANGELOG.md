# Changelog

All notable changes to manual-maker are recorded here. Versions follow semver (major.minor.patch).

## [0.2.0] - 2026-07-11
### Added
- `scripts/bump-version.sh` — one command bumps the version across `plugin.json`, `marketplace.json` (both fields), the README badge + version line, and stamps a CHANGELOG entry.
- SessionStart hook (`hooks/check-version.sh`) — on every new session it compares the installed version to `main` on GitHub and, when a newer version exists, tells the user how to update. Notify-only, offline-safe, never mutates the install.
- Version badges at the top of the README.

## [0.1.0]
### Added
- Initial release: intake → (screenshots) → doc-coauthoring draft → team template → export (Confluence / PDF / docx / web).
