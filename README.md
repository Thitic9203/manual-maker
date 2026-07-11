# manual-maker

A Claude Code plugin (skill) that turns a working web system into a finished **user handbook** — the kind an end user reads and follows step by step.

It's a thin **team wrapper** around Anthropic's first-party skills. It does not copy their content — it composes them:

- Runs a **structured intake** so every manual starts from complete, consistent, system-specific inputs.
- Optionally **auto-captures screenshots** of the live UI (Playwright / Chrome MCP).
- **Delegates the writing** to the official `doc-coauthoring` skill.
- Applies the **team handbook template** (structure + tone).
- **Exports / publishes** to Confluence, PDF, docx, or a web page.

## Install

```
/plugin marketplace add Thitic9203/manual-maker
/plugin install manual-maker@manual-maker-dev
```

Then restart Claude Code.

## Use

Ask for a manual, e.g.:

- "ทำคู่มือการใช้งานระบบ Admin Dashboard ให้ผู้ใช้"
- "create a user manual for the booking system"

The skill will interview you (system name, login, users, scope, output format…), optionally screenshot the UI, draft with `doc-coauthoring`, and publish to your chosen format.

## Requirements

All first-party / already available in Claude Code — nothing paid:

- `doc-coauthoring`, `docx`, `pdf`, `web-artifacts-builder` skills
- Playwright or Chrome MCP (for screenshots)
- Atlassian MCP (for Confluence publishing)

## Structure

```
manual-maker/
├── .claude-plugin/
│   ├── plugin.json          # plugin manifest
│   └── marketplace.json     # marketplace manifest (repo is its own marketplace)
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
