# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`manual-maker` is a **Claude Code plugin (skill)**, not an application. It has no build system, no tests, no CI, and no runtime code — it is Markdown (the skill) plus two JSON manifests (plugin + marketplace). The deliverable is the *behavior* Claude exhibits when the skill fires, defined entirely in `skills/manual-maker/`.

**Purpose:** produce **end-user manuals / handbooks for web systems** — step-by-step guides a non-technical reader follows to operate a system (access & login → each feature, with annotated screenshots), exported to Confluence / PDF / Word / web. Everything in this repo exists to make those manuals **accurate, consistent, and professionally written**; judge changes by whether they improve that outcome.

## Core architecture: wrapper-delegate (read before changing anything)

This is the one concept that requires reading multiple files to grasp, and it constrains every change:

**The skill does not write documents itself.** It is a thin team wrapper that *composes* Anthropic's first-party skills instead of reimplementing or forking them. At runtime it delegates:

- **Drafting** → the `doc-coauthoring` skill (via the Skill tool)
- **Export** → `docx` / `pdf` / `web-artifacts-builder` skills
- **Screenshots** → Playwright or Chrome MCP
- **Publishing** → Atlassian MCP (`createConfluencePage` / `updateConfluencePage`)

The invariant that follows: **no third-party (Anthropic) skill content is ever copied into this repo.** That is deliberate — it keeps the repo publishable/public, low-maintenance, and automatically benefiting from upstream skill updates. When adding capability, prefer delegating to an existing first-party skill over writing new prose/logic here. Do not paste another skill's content in.

## Where behavior lives — edit these, not code

The skill's entire behavior is three Markdown files:

- `skills/manual-maker/SKILL.md` — the workflow orchestration: `Intake → Confirm → Ingest sources → (Screenshots) → Draft → Template + quality → Final review → Export`, and which tool/skill owns each step. The `description:` frontmatter is what makes the skill auto-trigger (English + Thai trigger phrases) — edit it to change *when* the skill fires.
- `skills/manual-maker/references/intake.md` — the question set the skill asks, one at a time, each with a bold default. Editing this changes *what inputs* every manual collects. This is the primary tuning surface for a new team/system.
- `skills/manual-maker/references/template.md` — the handbook's section order, conventions, and step/screenshot format. Editing this changes the *shape and tone* of every manual produced.

There is no code path to trace; changing the skill means changing these files.

## How the skill makes a manual — the operating contract

Every manual run follows these **non-negotiable rules** (defined in `SKILL.md` + `intake.md`; keep all three behavior files consistent whenever you touch one):

1. **Never assume, never invent (ห้ามมโน).** If any input is missing, vague, or unclear — stop and ask. Never guess a system step, a term, a font, a number, or the scope.
2. **Confirm before starting.** After intake, summarize every answer in a table and wait for the user's **explicit "go"** before any screenshot or drafting. No silent starts.
3. **Every step is sourced, not guessed.** Content comes from the live system **plus** a user-supplied authoritative source (Confluence page / spec / flow / example doc). If a step can't be sourced → ask.
4. **Stay in scope (ห้ามทำเกินขอบเขต).** Document only what was asked; don't add modules, inject opinions, or decide on the user's behalf.
5. **Credentials are in-session only.** Login details reach the screens for screenshots and are **never** written into the manual, repo, logs, or printed back; ask for them fresh each run.
6. **Detailed final review before delivery.** Run the checklist in `template.md` line by line; deliver only when nothing is missing, wrong, or inconsistent.

Runtime flow: `Intake (one question at a time) → Confirmation gate → Ingest sources → Screenshots (optional, annotated) → Draft (doc-coauthoring) → Apply template + quality → Final review → Export/publish`.

## Document quality standards (load-bearing — the manual is judged on these)

These live in `template.md` and are enforced in the `SKILL.md` draft + review steps. They are the point of the repo, not decoration — do not weaken them:

- **Tone & language.** Formal, professional, **human** written language — never machine-translated stiffness. **No first/second-person pronouns** (ผม / ฉัน / คุณ / ท่าน) — use the imperative or the locked role term. **No sentence-final particles** (ครับ / ค่ะ / นะ).
- **Terminology consistency.** One **locked term** per concept, used identically throughout (e.g. always "ผู้เรียน", never "นักเรียน" / "นร."). Confirm the term list with the user; if a new term appears mid-draft, ask which word to use.
- **Numbering.** Continuous decimal outline (`1`, `1.1`, `1.1.1`) — no gaps or duplicates; the table of contents matches the body.
- **Font & size.** Taken from the user's reference document or explicitly confirmed — **never assumed**; uniform across the whole manual.
- **Image clarity + annotation.** Every screenshot sharp and legible; when requested, a **box (กรอบ) + numbered marker (เลขลำดับ)** on the click target, in a consistent style throughout.
- **Output format.** Word (`.docx`) / PDF / Confluence / web — the skill **always asks which** when the user hasn't said, phrased for non-technical users.

## Release workflow & gotchas

There are no build/lint/test commands. The only "commands" are install and version bookkeeping.

**Never hand-edit version strings — run `scripts/bump-version.sh`.** The version lives in FOUR places that must stay in sync: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (both `metadata.version` AND `plugins[0].version`), and the README (shields badge + the `**Version …**` line). A mismatch ships a broken marketplace entry. The script updates all of them at once and stamps a `CHANGELOG.md` entry. Release: `scripts/bump-version.sh minor` (or `patch`/`major`/explicit `0.3.0`) → edit the CHANGELOG stub → commit → push. Users with auto-update on get it automatically next session; everyone else runs `/plugin marketplace update manual-maker-dev`. If you must edit versions by hand, edit *all four* spots.

**Updates are self-driven by the SessionStart hook (Path B) — a deliberate override of the old notify-only design.** The repo owner chose true zero-touch updates on the plugin path over the "correct" native route, accepting the trade-offs (see `RISK_REGISTER.md`, MM-001). Context on the native alternative, still valid and documented in the README "Update" section: Claude Code *can* auto-update third-party plugins natively, but it is **off by default** for third-party marketplaces (only Anthropic's official ones default on) and the author **cannot enable it from the repo** — it is a client-side opt-in, by security design. The native paths (per-user `/plugin` → Marketplaces → **Enable auto-update**, or team-wide `"autoUpdate": true` in `extraKnownMarketplaces`) remain the cleaner options and are offered as such. Either way, auto-update only fires when the `version` string changes — which `bump-version.sh` guarantees.

**The SessionStart hook self-updates.** `hooks/hooks.json` registers `hooks/check-version.sh`, which on every session start compares the installed `plugin.json` version to `main` on GitHub (via `curl`, 3s cap) and, if GitHub is ahead, launches `claude plugin update` **in the background** (detached, non-blocking) and tells the user via `additionalContext`; the new version applies on the next session / `/reload-plugins`. Safety rails baked in and must be preserved: fail-silent when offline/up-to-date/curl-less; **opt-out** via `MANUAL_MAKER_NO_AUTOUPDATE=1` (degrades to notify-only); notify-only degrade if `claude` is not on PATH; an atomic `mkdir` lock (stale after 10 min) prevents overlapping updates; it uses the **supported `claude plugin update` CLI, never a raw git-pull into the plugin cache**. This intentionally bypasses Claude Code's per-marketplace auto-update opt-in — do not "restore" it to notify-only without the owner's say-so; the override is recorded, not accidental. The GitHub owner/repo URL is hardcoded in the script; update it if the repo moves. **Do NOT list `hooks/hooks.json` in `plugin.json`'s `hooks` key** — Claude Code auto-loads the standard `hooks/hooks.json`, so referencing it there causes a fatal "Duplicate hooks file detected" error and the hook silently fails to load (this bit us in 0.3.0–0.4.0, fixed in 0.4.1). `manifest.hooks` is only for *additional* hook files outside the standard path.

**A disabled plugin silently freezes the self-update — check enabled status before version.** The hook only runs while the plugin is enabled, so `"manual-maker@manual-maker-dev": false` under `enabledPlugins` in `~/.claude/settings.json` breaks the loop: the hook never fires → `claude plugin update` never runs → the install stays pinned at whatever version it was disabled at, with no warning and no notification. Seen in the wild: an install sat on 0.11.0 well after 0.12.0 shipped. The tell is that the `manual-maker` skill is missing from the session's skill list entirely. Diagnose with `claude plugin list | grep -A3 'manual-maker@'`, which prints version *and* status together. Recovering takes both steps — `claude plugin enable manual-maker@manual-maker-dev` then `claude plugin update manual-maker@manual-maker-dev` — because enabling alone leaves the stale version in place until some later session's hook run catches it. Restart / `/reload-plugins` to load.

**Bare `/manual-maker` can never work from the plugin — the prefix is mandatory, and a `shim/` copy is the only workaround.** Claude Code namespaces *every* plugin command and plugin skill as `/plugin-name:command-name`, by design, so plugins can't collide; the invocation is `/manual-maker:manual-maker` (plugin `manual-maker` + `commands/manual-maker.md`). Bare `/manual-maker` returns `Unknown command`. There is **no** frontmatter key (`name`, `aliases`), manifest field, or marketplace setting an author can set to expose the short form — verified against the official docs, which are explicit that plugin skills are always namespaced. Do not "fix" this by renaming the command, adding an alias field, or dropping `skills/manual-maker/` in the hope the bare name frees up; none of those change the rule, and the last one deletes the actual product. The supported escape hatch is `shim/manual-maker.md` — a **user-level** command (`~/.claude/commands/` is not namespaced) that users opt into with one `curl`. Keep the shim a pure pointer that just invokes the `manual-maker:manual-maker` skill: it lives outside the plugin, so it does **not** auto-update and is **not** removed on `/plugin uninstall`, and any workflow prose copied into it would silently drift from `SKILL.md`. `shim/` is inert to the plugin loader (only `commands/`, `skills/`, `agents/`, `hooks/hooks.json` are auto-loaded), so it must never move under `commands/` — that would register a second, duplicate `/manual-maker:manual-maker`.

**Marketplace name ≠ plugin name, on purpose.** The plugin is `manual-maker`; the marketplace is `manual-maker-dev`. So the install command is `/plugin install manual-maker@manual-maker-dev` and updates target `manual-maker-dev`. This intentional mismatch mirrors the team's other proven-working plugins (`helix-dev`, `retest-bug-dev`, `full-test-dev`). Don't "fix" it to match.

**The repo is its own marketplace** — `source: "./"` in `marketplace.json`. Installs come straight from GitHub (`Thitic9203/manual-maker`); there is no separate registry.

**Validate before every push.** Run `claude plugin validate <repo-path>` before pushing a manifest change. The validator (Claude Code ≥ 2.1.104) **rejects root-level `id` and `description` keys in `marketplace.json`** — keep the root to `name` / `owner` / `metadata` / `plugins` only, and nest description/version under `metadata`. The team's older manifests (`helix-dev` etc.) still carry root `id`/`description` and were grandfathered in, so don't copy them verbatim — a fresh `marketplace add` runs validation and will fail on those keys.

## Two install/distribution paths

- **Personal skill** — `cp -r skills/manual-maker ~/.claude/skills/manual-maker`. A snapshot: it does **not** auto-sync, so re-copy after every change. Skills work without the plugin system. Don't keep this alongside the installed plugin — two skills named `manual-maker` collide; pick one source.
- **Plugin, interactive** — inside a Claude Code TUI session: `/plugin marketplace add Thitic9203/manual-maker` then `/plugin install manual-maker@manual-maker-dev`. `/plugin` is a session-only slash command (not the shell, not desktop/web app).
- **Plugin, headless CLI** (no interactive `/plugin` needed) — from any shell: `claude plugin marketplace add Thitic9203/manual-maker`, `claude plugin install manual-maker@manual-maker-dev`, verify with `claude plugin list`. This is the way to install/verify outside a TUI (desktop/web app, scripts, agents). `claude plugin validate <path>` checks a manifest without installing.

Either way, changes require a restart / new session to load.

## Conventions

- **Bilingual TH/EN.** The audience is a Thai QA team; the skill defaults to Thai output, and docs/intake/template mix Thai and English intentionally. Keep new user-facing strings bilingual and preserve Thai defaults.
- **Safety is part of the spec, not a nicety.** Never record real credentials/tokens — login steps describe the *procedure* only. Screenshots navigate only user-provided URLs. Confluence/web publishing confirms the target before the first post. These rules live in SKILL.md, template.md, and README and must stay consistent across all three.
- **Free tooling only.** Everything the skill depends on is first-party/already installed — no paid services. Don't introduce a dependency that bills.
