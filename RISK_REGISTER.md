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

## MM-003 — SessionStart hook writes a shim into the user's `~/.claude/commands/`

- **Date:** 2026-07-19
- **Decision by:** repo owner (explicit choice, this session: "แก้มาแบบที่คนอื่น เมื่อเรียกใช้งาน พิมพ์ /manual-maker ต้องใช้ได้ปกติห้าม error")
- **Status:** Accepted, shipped in v0.14.0

**What changed.** `hooks/check-version.sh` now also copies `shim/manual-maker.md` into `~/.claude/commands/manual-maker.md` on session start, so bare `/manual-maker` resolves for every user without them running anything.

**Why.** Claude Code reaches plugin commands and plugin skills **only** as `/plugin-name:command-name`; bare `/manual-maker` returns `Unknown command`. This was verified empirically against Claude Code 2.1.210, not assumed: a throwaway probe plugin (`mmprobe`) was installed with (a) a command with no name collision anywhere, (b) a command carrying a frontmatter `aliases:` key, and (c) a command whose name equalled both the plugin and a sibling skill. Run headless, **every bare form returned `Unknown command`** while the `/mmprobe:…` forms resolved. The command matcher in the bundle is `e.name===t || userFacingName()===t || aliases?.includes(t)`, and plugin-sourced commands are only ever registered under qualified names — so no manifest field, frontmatter key, or file rename can expose the short form. User-level commands in `~/.claude/commands/` are *not* namespaced, which makes the shim the only mechanism that exists. A documented one-liner was tried first (v0.13.0) and rejected as insufficient: users who don't run it still hit the error.

**Trade-offs accepted.**
1. **The plugin writes outside its own install root**, into the user's personal config directory, without a per-session prompt. Mitigated by: a single small file at a predictable path; a `managed-by: manual-maker-plugin` marker in the file; an opt-out (`MANUAL_MAKER_NO_SHIM=1`); a one-time notice explaining what was created and how to remove it.
2. **Not removed by `/plugin uninstall`.** The hook cannot run once the plugin is gone, so the file is left behind and its `/manual-maker` will then report that the plugin is missing. Users remove it with `rm ~/.claude/commands/manual-maker.md`; documented in the README uninstall section.
3. **A second source of truth for the entry point.** Mitigated by keeping the shim a pure pointer (it only invokes the `manual-maker:manual-maker` skill and holds no workflow prose), and by the hook refreshing it whenever the shipped copy changes — so it cannot drift from `SKILL.md`.

**Safety rails in the implementation (keep these).** Never clobber a file that lacks the marker (a hand-written `/manual-maker` command is left untouched); no-op when the content already matches; atomic temp-file + `mv`; fail-silent on any error, missing `$HOME`, or missing source file; announce only the first install, stay silent on refresh. Covered by the 11-case scenario test in the v0.14.0 work (fresh install, current no-op, stale refresh, foreign file untouched, opt-out, missing `$HOME`).

**How to reverse.** Set `MANUAL_MAKER_NO_SHIM=1` and `rm ~/.claude/commands/manual-maker.md` (per user), or delete the `install_shim` block from `hooks/check-version.sh` and revert the README to the manual-`curl` instructions from v0.13.1.

## MM-004 — Steps 4–6 fan out to parallel subagents, with a per-section reviewer

- **Date:** 2026-07-19
- **Decision by:** repo owner (explicit choice, this session: "แยก agent 2-3 ตัว … เพื่อให้ทำคู่มือได้รวดเร็วขึ้น" + "มี sub-agent อีกตัวเป็นผู้รีวิว … เมื่อทำเสร็จทีละหัวข้อย่อย")
- **Status:** Accepted, shipped in v0.17.0

**What changed.** Screenshots + drafting + template application (Steps 4–6) are no longer done serially in the main thread. The work is partitioned **by หัวข้อย่อย** and dispatched to **2–3 `manual-section-writer` agents** running concurrently, with **one** `manual-section-reviewer` reviewing each หัวข้อย่อย the moment its writer hands it over. Contract: `skills/manual-maker/references/parallel.md`; agent prompts: `agents/*.md`. A `PostToolUse` hook (`hooks/progress-tick.sh`) reminds the main thread to print a progress table roughly every 10 minutes while a run is open.

**Why.** A manual with dozens of screens is dominated by per-section capture + drafting, and those sections are genuinely independent. Reviewing only at the end also meant defects surfaced when they were most expensive — after numbering, figures, and the built file all depended on them.

**Why partition by หัวข้อย่อย and not by phase.** The obvious alternative (one agent captures every screen, another writes every step) was rejected: **"เลขในวงแดง = เลขขั้นตอน 1:1" is an invariant _inside_ a หัวข้อย่อย.** Split capture from drafting and the two halves must renegotiate step numbers across an agent boundary — exactly the defect class the review layers exist to catch.

**Trade-offs accepted.**
1. **More tokens per run.** Three writers plus a reviewer cost more than one thread doing the same work. Accepted deliberately for wall-clock; capped at 3 writers, and no fan-out at all for a single หัวข้อย่อย.
2. **Subagents cannot talk to the user.** A writer that cannot source a step, or a reviewer unsure how to fix something, would otherwise be pushed toward guessing — the one thing this skill forbids. Mitigated structurally: writers return `BLOCKED`, reviewers split findings into `FIX` (the confirmed table already dictates the single correct answer) vs `ASK` (everything else, **including anything the reviewer is unsure of**), and **only the main thread asks the user**. A หัวข้อย่อย with an open `ASK` is not "done" and never reaches the file.
3. **Concurrent writes could corrupt a run.** Mitigated by ownership, not by convention: each writer may write only `manual-assets/<slug>/<section>-*.png` and `manual-drafts/<slug>/<section>.md`; section numbers are assigned by the main thread before dispatch; the `.docx` is assembled only in the main thread; the reviewer is read-only.
4. **Three concurrent logins would risk account lockout and spread the credential.** Mitigated by logging in **once** in the main thread and passing a read-only `storageState`; writers are forbidden to log in and return `BLOCKED` on session expiry.
5. **Per-section review could be mistaken for the delivery gate.** It reviews only layers 1–4 *at section level*; font fallback, คำพราก, TOC, cross-chapter numbering and all of layer 5 are born in the conversion and provable only on the exported file. Mitigated by saying so in `review.md`, `parallel.md`, and the reviewer's own prompt, and by leaving Step 8 completely unchanged.
6. **The 10-minute progress update is a floor, not a timer.** Claude Code has **no time-based hook**; `SubagentStop` supports only `decision`/`reason` and cannot inject a message. So the reminder rides `PostToolUse` (matcher `Task|Bash`) and throttles on wall clock — no tool call, no tick. Accepted as the only real mechanism; the skill still reports on every section status change independently of the hook.

**Safety rails (keep these).** Do not fan out before the Step 2 gate, the numbered outline, the ingested sources, the locked terms, and the saved `storageState` all exist. Dispatch writers in one message (separate messages serialise them). One reviewer only — several would judge terminology and tone differently, which is the defect they exist to find. The reviewer never edits (that would collide with a live writer); fixes go back to the owning writer. Re-review the **whole** หัวข้อย่อย after a fix, not just the changed line. `progress-tick.sh` stays fail-silent, inert without `~/.manual-maker/state/run.active`, opt-out via `MANUAL_MAKER_NO_PROGRESS=1`, and self-clears a marker older than 12h.

**How to reverse.** Delete `agents/`, `skills/manual-maker/references/parallel.md`, and the `PostToolUse` block in `hooks/hooks.json`; revert the Steps 4–6 bodies in `SKILL.md` to the v0.16.0 serial text. Nothing else depends on it — the 5-layer gate, the intake, and the build path are untouched.
