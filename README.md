# manual-maker

![version](https://img.shields.io/badge/version-0.2.0-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2)

A Claude Code plugin (skill) that turns a working web system into a finished **user handbook** — the kind an end user reads and follows step by step.

It is a thin **team wrapper** around Anthropic's first-party skills. It does not copy their content — it composes them.

**Version 0.2.0 · MIT · Claude Code plugin**

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

Skills don't require the plugin system. In the mac Terminal, copy the skill into your personal skills directory:

```bash
cp -r skills/manual-maker ~/.claude/skills/manual-maker
```

Restart Claude Code. Note: a personal copy does **not** auto-sync with this repo — re-copy after updates.

### Option B — plugin marketplace (team distribution)

> ⚠️ **อย่าวางทั้ง 3 บรรทัดทีเดียว!**
> `claude` เป็นคำสั่ง **shell** (เปิดโปรแกรม) — ส่วน `/plugin` ต้องพิมพ์ **ข้างใน Claude Code** หลังมันเปิดแล้ว
> ทำ **ทีละขั้น** ตามนี้:

**Step 1 — ที่ mac Terminal (zsh):**

```bash
claude
```

กด Enter → รอ Claude Code เปิด
👉 หน้าจอเปลี่ยนเป็น UI มีช่องพิมพ์ = เข้ามา "ข้างใน" แล้ว

**Step 2 — พิมพ์ข้างใน Claude Code:**

```
/plugin marketplace add Thitic9203/manual-maker
```

กด Enter → รอเสร็จ

**Step 3 — พิมพ์ข้างใน Claude Code:**

```
/plugin install manual-maker@manual-maker-dev
```

กด Enter → รอเสร็จ

**Step 4 — ออกแล้วเปิด `claude` ใหม่ (restart) → เสร็จ**

💡 `/plugin` เปิดจากโฟลเดอร์ไหนก็ได้ — มันโหลดจาก GitHub เอง

### Verify it's installed

Start a new session and confirm `manual-maker` appears in your available skills — or just ask *"ทำคู่มือระบบ …"* and the intake should begin.

### Update

Every new session, the plugin checks GitHub for a newer version and — if there is one — tells you the exact command to run. You never have to remember to check. To apply an update:

- **Plugin:** พิมพ์ข้างใน Claude Code → `/plugin marketplace update manual-maker-dev` → restart.
- **Personal skill:** re-copy → `cp -r skills/manual-maker ~/.claude/skills/manual-maker`.

> The check is **notify-only** — it never changes your install by itself, needs no setup, and stays silent when you are up to date or offline.

### Uninstall

- **Plugin:** พิมพ์ข้างใน Claude Code → `/plugin uninstall manual-maker@manual-maker-dev`.
- **Personal skill:** `rm -rf ~/.claude/skills/manual-maker`.

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

## Customize for your team

The whole point of the wrapper is that you tune it — **no code, just two Markdown files**:

- `skills/manual-maker/references/intake.md` — the questions the skill asks. Add fields specific to your systems (environment, tenant, role matrix), change defaults, drop what you don't need.
- `skills/manual-maker/references/template.md` — the handbook structure, section order, tone, and step/screenshot conventions.

After editing, **release with one command** — never hand-edit version strings:

```bash
scripts/bump-version.sh minor   # or: patch | major | an explicit 0.3.0
```

It bumps every version location at once (`plugin.json`, `marketplace.json` ×2, the README badge + version line) and stamps a `CHANGELOG.md` entry. Then:

1. Edit the new `CHANGELOG.md` stub to describe the change.
2. Commit and push.
3. Team members get a new-version notice on their next session; they run `/plugin marketplace update manual-maker-dev` (or re-copy the personal skill).

## Requirements

All first-party / already available in Claude Code — nothing paid:

- Skills: `doc-coauthoring`, `docx`, `pdf`, `web-artifacts-builder`
- MCP: Playwright or Chrome (screenshots), Atlassian (Confluence publish)
- The new-version check uses `curl` (ships with macOS) to read the public GitHub repo — free, no auth, no account.

## Structure

```
manual-maker/
├── .claude-plugin/
│   ├── plugin.json          # plugin manifest (version, hooks pointer)
│   └── marketplace.json     # marketplace manifest (name: manual-maker-dev)
├── hooks/
│   ├── hooks.json           # registers the SessionStart hook
│   └── check-version.sh     # notify-only new-version check (fail-silent)
├── scripts/
│   └── bump-version.sh      # bump the version everywhere in one command
├── CHANGELOG.md             # per-version history
└── skills/
    └── manual-maker/
        ├── SKILL.md         # workflow: intake → screenshots → draft → template → export
        └── references/
            ├── intake.md    # the system-specific question set
            └── template.md  # team handbook structure + conventions
```

## Troubleshooting

| อาการ | สาเหตุ | วิธีแก้ |
|-------|--------|---------|
| `/plugin isn't available in this environment` | อยู่ในแอป desktop/web ไม่ใช่ CLI — `/plugin` มีเฉพาะใน terminal | รัน `claude` ใน Terminal จริง **หรือ** ใช้ Option A (personal skill) |
| วางคำสั่งทีเดียวแล้ว error | `claude` เป็น shell, `/plugin` อยู่ข้างใน — วางรวมกันไม่ได้ | ทำทีละ step ตาม Option B |
| Skill ไม่ trigger | เปิด session ก่อนติดตั้ง | Restart Claude Code / เปิด session ใหม่ |
| แก้ skill แล้วไม่เปลี่ยน | personal skill เป็น snapshot ไม่ใช่ลิงก์สด | re-copy โฟลเดอร์ หรือใช้ plugin route |
| Confluence publish fail | Atlassian MCP ไม่ต่อ / space key ผิด | ต่อ Atlassian MCP + เช็ค space key จาก intake |
| Screenshot ไม่ติด | Playwright/Chrome MCP ไม่ต่อ / URL ต้อง login | ต่อ MCP + เช็ค login steps ใน intake |

## Safety

- No secrets in output or repo — login steps describe the *procedure*, never real credentials.
- Screenshots navigate only user-provided URLs.
- Confluence / web publishing asks for confirmation before posting.

## License

MIT
