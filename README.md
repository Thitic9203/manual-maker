# manual-maker

A Claude Code plugin (skill) that turns a working web system into a finished **user handbook** — the kind an end user reads and follows step by step.

It is a thin **team wrapper** around Anthropic's first-party skills. It does not copy their content — it composes them.

---

## Background — why this repo exists

The team needed a repeatable way to produce **end-user manuals** for the web systems it builds and tests (QA context: dashboards, booking flows, admin panels).

Anthropic already ships an excellent first-party skill, **`doc-coauthoring`**, that writes long-form documents well. But on its own it starts from a blank page every time and knows nothing about *our* systems or *our* handbook conventions.

Rather than fork `doc-coauthoring` and drift from upstream, this repo adds a thin layer **on top** of it:

1. A **system-specific intake** — the skill asks the right questions first (system, login, users, modules, output) so every manual starts complete and consistent.
2. A **team handbook template** — one structure and tone for every manual.
3. **Composition, not copying** — the skill delegates the actual writing to `doc-coauthoring` via the Skill tool, and delegates export to `docx` / `pdf` / `web-artifacts-builder`. No third-party content lives in this repo, so it stays free to be public and keeps benefiting from upstream updates.

## Design decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Architecture | **Wrapper-delegate** (not fork) | Keeps upstream updates, low maintenance, no third-party content in repo |
| Repo visibility | **Public** | No secrets, no Anthropic content — team installs without auth |
| Output formats | Confluence / PDF / docx / web (chosen at runtime) | Fits different audiences; default Confluence (team's channel) |
| Screenshots | Optional, via Playwright / Chrome MCP | Auto-capture real UI per step |
| Publishing | Confluence via Atlassian MCP | Push straight to the team space |
| Distribution | Repo is its own marketplace | Team installs directly from GitHub |
| Marketplace name | `manual-maker-dev` (≠ plugin name) | Mirrors the team's proven-working plugins (`helix-dev`, `retest-bug-dev`, `full-test-dev`) |

## What it does

- Runs a **structured intake** for system-specific inputs.
- Optionally **auto-captures screenshots** of the live UI.
- **Delegates writing** to the official `doc-coauthoring` skill.
- Applies the **team handbook template** (structure + tone).
- **Exports / publishes** to Confluence, PDF, docx, or a web page.

## Install

Two ways — pick by need.

### Option A — personal skill (one machine, no `/plugin` needed)

Skills don't require the plugin system. Copy the skill into your personal skills directory:

```bash
cp -r skills/manual-maker ~/.claude/skills/manual-maker
```

Restart Claude Code. Note: a personal copy does **not** auto-sync with this repo — re-copy after updates.

### Option B — plugin marketplace (team distribution)

`/plugin` only works in the **real `claude` terminal** (not the desktop/web app). In a terminal:

```
claude
```

then inside Claude Code:

```
/plugin marketplace add Thitic9203/manual-maker
/plugin install manual-maker@manual-maker-dev
```

Restart Claude Code.

## Use

Ask for a manual, e.g.:

- "ทำคู่มือการใช้งานระบบ Admin Dashboard ให้ผู้ใช้"
- "create a user manual for the booking system"

The skill interviews you (system, login, users, scope, output…), optionally screenshots the UI, drafts with `doc-coauthoring`, applies the template, and publishes to your chosen format.

## How it works (runtime flow)

```
Intake  →  (Screenshots)  →  Draft            →  Template        →  Export
one-at-a-   Playwright /       delegate to         apply team         Confluence /
time Qs      Chrome MCP        doc-coauthoring     structure+tone     PDF / docx / web
```

## Requirements

All first-party / already available in Claude Code — nothing paid:

- Skills: `doc-coauthoring`, `docx`, `pdf`, `web-artifacts-builder`
- MCP: Playwright or Chrome (screenshots), Atlassian (Confluence publish)

## Structure

```
manual-maker/
├── .claude-plugin/
│   ├── plugin.json          # plugin manifest
│   └── marketplace.json     # marketplace manifest (name: manual-maker-dev)
└── skills/
    └── manual-maker/
        ├── SKILL.md         # workflow: intake → screenshots → draft → template → export
        └── references/
            ├── intake.md    # the system-specific question set
            └── template.md  # team handbook structure + conventions
```

## Safety

- No secrets in output or repo — login steps describe the *procedure*, never real credentials.
- Screenshots navigate only user-provided URLs.
- Confluence / web publishing asks for confirmation before posting.

## License

MIT
