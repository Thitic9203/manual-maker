# Risk Register — manual-maker

Decisions that trade something away, recorded so future sessions don't silently re-litigate or "fix" them. Each entry: what was chosen, why, the trade-off accepted, and how to reverse it.

## MM-001 — Self-updating SessionStart hook (overrides notify-only)

- **Date:** 2026-07-14
- **Decision by:** repo owner (explicit choice, this session)
- **Status:** Accepted, shipped in v0.6.0

**What changed.** `hooks/check-version.sh` no longer only *notifies* about a new version — when it detects that `main` on GitHub is ahead of the installed version, it launches `claude plugin update manual-maker@manual-maker-dev` in the background and the new version applies on the next session / `/reload-plugins`. This makes updates zero-touch on the plugin path: open a new session and the install updates itself.

**Why.** The owner wanted existing installs to get new versions with no per-user action. Claude Code's native plugin auto-update is **off by default for third-party marketplaces** and can only be enabled client-side (per-user toggle or `autoUpdate:true` in shared/managed settings) — the author cannot enable it from the repo. Given that, a self-updating hook is the only way to get true zero-touch on the plugin path without every user opting in first.

**Trade-offs accepted.**
1. **Bypasses a security opt-in.** Claude Code makes third-party auto-update opt-in on purpose (a plugin auto-running newly-pushed code from GitHub is a supply-chain surface). This hook opts the user in on their behalf. Mitigated by: the user already installed + trusted the plugin and its hook; an explicit opt-out (`MANUAL_MAKER_NO_AUTOUPDATE=1`); transparent per-session notice of what it did.
2. **Reimplements a native feature.** Duplicates what native auto-update already does properly (background, post-startup, with reload prompt). Risk of drift if Claude Code's plugin internals change. Mitigated by using the **supported `claude plugin update` CLI**, never a raw mutation of the plugin cache / `installed_plugins.json`.
3. **Mutates the install without a per-session prompt.** Every release lands automatically. Mitigated by opt-out + notice + single-flight lock.
4. **Contradicts the earlier documented invariant** ("keep the hook notify-only; don't turn it into an auto-updater"). That invariant is now explicitly superseded by this entry.

**Safety rails in the implementation (keep these).** Fail-silent when offline / up-to-date / no curl; opt-out env var; notify-only degrade when `claude` is not on PATH; non-blocking (detached `nohup &`) so session start is never delayed; atomic `mkdir` lock (stale after 10 min) to prevent overlapping updates.

**How to reverse.** Set `MANUAL_MAKER_NO_AUTOUPDATE=1` (per user), or revert `hooks/check-version.sh` to the notify-only version (git history before v0.6.0) and point users at the native per-marketplace toggle documented in the README "Update" section.

## MM-002 — Saved intake profile persists to disk (credentials never included)

- **Date:** 2026-07-14
- **Decision by:** repo owner (explicit choice, this session)
- **Status:** Accepted, shipped in v0.8.0

**What changed.** After the Confirmation Gate, manual-maker writes a user's confirmed intake (system, URLs, sources, audience/scope, screenshot annotation, font, numbering, locked terminology, output destination) to a **per-user local** file at `~/.manual-maker/profiles/<slug>.json`, and reuses it on the next run for the same system so the user isn't re-asked. Spec: `skills/manual-maker/references/profile.md`.

**Why.** Documenting the same system twice meant retyping the whole intake. Remembering the stable answers removes that friction while the Confirmation Gate still re-verifies everything each run.

**Trade-offs accepted.**
1. **Writes intake data to disk outside the repo.** Profiles hold internal system details (module names, Confluence links, terminology). Mitigated by: per-user local storage only (not committed, not team-shared — the owner's explicit choice); it is the user's own machine; data is only ever written *after* the user confirms it.
2. **Credentials must never leak into the file.** Passwords, usernames, tokens, cookies, VPN secrets, and secrets embedded in a URL (basic-auth, `?token=`) are on an explicit NEVER-store list and stripped before writing; only `vpn_required` (boolean) is kept. Credentials are still asked fresh, in-session, every run.
3. **A stored profile could go stale** if the live system changes. Mitigated by: the profile is only a set of *preferences* (never step content, which is re-ingested live), and the mandatory Confirmation Gate re-shows every value for confirmation each run — sourced-not-invented is preserved.

**Safety rails (keep these).** Save only *after* the gate, never before; NEVER-store credential list incl. URL-embedded secrets; overwrite the loaded file (no duplicate profiles); on multiple matches, ask which.

**How to reverse.** Delete `skills/manual-maker/references/profile.md` and the profile load/save steps in `SKILL.md` / `intake.md` / `commands/manual-maker.md`; users can delete `~/.manual-maker/profiles/` to purge stored data.
