# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`manual-maker` is a **Claude Code plugin (skill)**, not an application. It has no build system, no tests, no CI, and no runtime code — it is Markdown (the skill) plus two JSON manifests (plugin + marketplace). The deliverable is the *behavior* Claude exhibits when the skill fires, defined entirely in `skills/manual-maker/`.

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

- `skills/manual-maker/SKILL.md` — the workflow orchestration: `Intake → (Screenshots) → Draft → Template → Export`, and which tool/skill owns each step. The `description:` frontmatter is what makes the skill auto-trigger (English + Thai trigger phrases) — edit it to change *when* the skill fires.
- `skills/manual-maker/references/intake.md` — the question set the skill asks, one at a time, each with a bold default. Editing this changes *what inputs* every manual collects. This is the primary tuning surface for a new team/system.
- `skills/manual-maker/references/template.md` — the handbook's section order, conventions, and step/screenshot format. Editing this changes the *shape and tone* of every manual produced.

There is no code path to trace; changing the skill means changing these files.

## Release workflow & gotchas

There are no build/lint/test commands. The only "commands" are install and version bookkeeping.

**Never hand-edit version strings — run `scripts/bump-version.sh`.** The version lives in FOUR places that must stay in sync: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (both `metadata.version` AND `plugins[0].version`), and the README (shields badge + the `**Version …**` line). A mismatch ships a broken marketplace entry. The script updates all of them at once and stamps a `CHANGELOG.md` entry. Release: `scripts/bump-version.sh minor` (or `patch`/`major`/explicit `0.3.0`) → edit the CHANGELOG stub → commit → push → team runs `/plugin marketplace update manual-maker-dev`. If you must edit versions by hand, edit *all four* spots.

**New-version notice is a SessionStart hook, notify-only.** `hooks/hooks.json` registers `hooks/check-version.sh`, which on every session start compares the installed `plugin.json` version to `main` on GitHub (via `curl`, 3s cap) and, if GitHub is ahead, emits `additionalContext` telling Claude to inform the user how to update. It is deliberately **notify-only**: it never runs git/pull, never mutates the install (that would fight Claude Code's plugin cache), and fail-silents when offline / up-to-date / curl-less. Keep it that way — don't turn it into an auto-updater. The GitHub owner/repo URL is hardcoded in the script; update it if the repo moves.

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
