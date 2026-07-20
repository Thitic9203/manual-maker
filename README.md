# manual-maker

![version](https://img.shields.io/badge/version-0.22.0-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2)

**A Claude Code plugin that documents the web systems your team builds.** It ships **two skills** that turn a running system into finished documentation — a step-by-step user handbook, or a fully populated Confluence space.

It is a thin **team wrapper** around Anthropic's first-party skills: it composes them (via the Skill tool) instead of copying their content, so the repo stays public and keeps benefiting from upstream updates.

> 🔄 **Auto-update (v0.6.0+):** install once, then just **open a new session** — the plugin fetches and installs the latest version in the background. Nothing to click. Disable with `MANUAL_MAKER_NO_AUTOUPDATE=1`. See [Update](#update).

---

## The two skills

| Skill | Purpose | Reads | Produces | Command |
|-------|---------|-------|----------|---------|
| **`manual-maker`** | End-user handbook a non-technical reader follows step by step | Live UI + your source (Confluence/spec) | `.docx` / PDF / Confluence page / web, with annotated screenshots | `/manual-maker` |
| **`confluence-docs`** (v0.22.0+) | Replace the mock/placeholder content of a Confluence doc-space with the system's **real** data | Live Confluence page + authoritative source (Jira/repo/schema/spec) | Updated & new Confluence pages | `/confluence-docs` |

Both skills share one ethos: **ห้ามมโน (never invent) · confirm before starting · every value sourced · stay in scope · review before delivery.** They install together; use whichever the task needs.

## Table of contents

- [Install](#install) · [Verify](#verify-its-installed) · [Update](#update) · [Uninstall](#uninstall)
- [Skill 1 — `manual-maker`](#skill-1--manual-maker)
- [Skill 2 — `confluence-docs`](#skill-2--confluence-docs)
- [Bare commands & shims](#bare-commands--shims)
- [Requirements](#requirements) · [Repository structure](#repository-structure) · [Troubleshooting](#troubleshooting) · [Safety](#safety) · [Design decisions](#design-decisions)

---

## Install

Installing the plugin gives you **both skills**. Pick one route.

### Option A — personal skill (one machine, no `/plugin` needed)

Skills work without the plugin system. In the mac Terminal, copy the skill you want into your personal skills directory:

```bash
cp -r skills/manual-maker    ~/.claude/skills/manual-maker
cp -r skills/confluence-docs ~/.claude/skills/confluence-docs
```

Restart Claude Code. A personal copy is a snapshot — it does **not** auto-sync, so re-copy after each update.

### Option B — plugin marketplace (team distribution, auto-updates)

> ⚠️ **Do not paste all three lines at once.** `claude` is a **shell** command (it launches the app); `/plugin` must be typed **inside** Claude Code after it opens. Do it step by step.

**Step 1 — in the mac Terminal (zsh):**

```bash
claude
```

Press Enter and wait for Claude Code to open — when the screen becomes a UI with an input box, you are "inside".

**Step 2 — inside Claude Code:**

```
/plugin marketplace add Thitic9203/manual-maker
```

**Step 3 — inside Claude Code:**

```
/plugin install manual-maker@manual-maker-dev
```

**Step 4 — quit and reopen `claude` (restart). Done.**

💡 `/plugin` works from any folder — it loads straight from GitHub.

> ℹ️ The marketplace is named `manual-maker-dev` (≠ the plugin name `manual-maker`), so the install target is `manual-maker@manual-maker-dev`. This mirrors the team's other plugins (`helix-dev`, `retest-bug-dev`).

### Verify it's installed

Start a new session and confirm `manual-maker` and `confluence-docs` appear in your available skills — or just ask *"ทำคู่มือระบบ …"* / *"อัปเดต confluence …"* and the intake should begin.

```bash
claude plugin list | grep -A3 'manual-maker@'   # prints version + enabled status
```

### Update

**Since v0.6.0 the plugin updates itself — you do nothing.** On every **new session** the SessionStart hook compares the installed version with the latest on `main`; if `main` is ahead it runs `claude plugin update` **in the background** (no startup lag) and says so in chat. The new version takes effect **next session** (or after `/reload-plugins` once the download finishes).

> In short: push to `main` with a version bump → installed users get the latest version after one or two new sessions, automatically.

**Details & conditions:**

- Updates fire only when the **`version` string changes** — which `scripts/bump-version.sh` does on every release.
- Uses the official `claude plugin update` command (never touches the cache directly), guards against overlapping updates with a lock, and stays silent when offline, up to date, or `claude` is not on PATH.
- Applies to updates **from v0.6.0 onward** — an older install must reach v0.6.0 once (its old hook only notifies), then it is fully automatic.
- GitHub's raw CDN caches ~5 minutes, so a hook may not see a brand-new release immediately. Wait ~5 minutes and open a new session.

**Turn auto-update off** — the hook falls back to notify-only:

```bash
export MANUAL_MAKER_NO_AUTOUPDATE=1
```

> ⚠️ This auto-update **opts you in on your behalf** (Claude Code normally leaves third-party auto-update off by design). Running new code from GitHub every release is a recorded trade-off — see `RISK_REGISTER.md` (MM-001). Uncomfortable with it? Use the opt-out above and update manually.

<details>
<summary>Native auto-update (the "more correct" route) &amp; manual update</summary>

Prefer Claude Code's built-in auto-update over the self-updating hook? Turn the hook off (env var above), then enable one of:

- **Per user, once:** `/plugin` → **Marketplaces** tab → `manual-maker-dev` → **Enable auto-update**.
- **Whole team:** add `"autoUpdate": true` to `extraKnownMarketplaces` in the shared `settings.json`:
  ```jsonc
  {
    "extraKnownMarketplaces": {
      "manual-maker-dev": {
        "source": { "source": "github", "repo": "Thitic9203/manual-maker" },
        "autoUpdate": true
      }
    },
    "enabledPlugins": { "manual-maker@manual-maker-dev": true }
  }
  ```

Third-party native auto-update is **off by default** (only Anthropic's official marketplaces default on).

**Manual update:**
- In Claude Code (TUI): `/plugin marketplace update manual-maker-dev` → `/reload-plugins` or new session.
- Outside the TUI (desktop/web/shell):
  ```bash
  claude plugin marketplace update manual-maker-dev
  claude plugin update manual-maker@manual-maker-dev
  ```
  then restart.
- Personal skill (Option A): re-copy the folder(s) — Option A has no auto-update.

</details>

### Uninstall

- **Plugin:** inside Claude Code → `/plugin uninstall manual-maker@manual-maker-dev`.
- **Personal skill:** `rm -rf ~/.claude/skills/manual-maker ~/.claude/skills/confluence-docs`.
- **Shim commands:** `rm ~/.claude/commands/manual-maker.md ~/.claude/commands/confluence-docs.md` — these live outside the plugin system, so `/plugin uninstall` leaves them. See [Bare commands & shims](#bare-commands--shims).

---

## Skill 1 — `manual-maker`

**Purpose:** produce an **end-user handbook** — the kind a non-technical reader follows step by step to operate a web system: access & login, then each feature, with annotated screenshots — exported to `.docx`, PDF, Confluence, or a web page.

### Use it

Ask in natural language, or run the command:

```
/manual-maker ทำคู่มือระบบ Admin Dashboard
/manual-maker:manual-maker create a manual for the booking system
```

| Entry point | Example | Notes |
|-------------|---------|-------|
| **Natural language** | `ทำคู่มือการใช้งานระบบ <ระบบ> ให้ผู้ใช้` | The skill triggers itself — no `/` needed |
| **Short command** | `/manual-maker ทำคู่มือระบบ <ระบบ>` | Installed automatically (v0.14.0+) |
| **Full command** | `/manual-maker:manual-maker …` | Always works |

All three enter the same workflow. The command lays the run out as a checklist and **auto-advances through every step** — intake → confirm → sources → screenshots → draft → template → review → export — so you never nudge it between steps. It still **stops at the gates that keep a manual honest:** it asks intake questions one at a time, waits for your confirmation before screenshots or drafting, and confirms the target before any Confluence/web publish.

**How it runs:**

```
Intake  →  Confirm  →  Sources  →  ┌──────────── ขนานต่อหัวข้อย่อย ────────────┐  →  Build  →  รีวิว 5 ชั้น  →  Export
one-at-a-   gate       ต้นแบบ /     │ writer ×2–3: ถ่ายภาพ → วงแดง → เขียนสเตป │     .docx     บนไฟล์จริง      Confluence /
time Qs     ยืนยัน      Confluence   │ reviewer ×1: รีวิวทันทีทีละหัวข้อย่อย      │     ประกอบ    5/5 เท่านั้น      PDF / docx / web
                                    └──────────────────────────────────────────┘
```

The skill interviews you one question at a time — system URL, login, VPN, **the source that describes the real steps** (Confluence page / spec / example doc), audience, scope, screenshot **annotation** (boxes + step numbers), **font & size**, numbering, and the **locked terminology**. It then **summarizes everything and waits for your explicit confirmation** before doing anything, optionally screenshots the UI, drafts with `doc-coauthoring`, runs a **detailed final review**, and publishes in your chosen format.

> The skill never assumes: if anything is unclear it asks first, it stays within your scope, and credentials are used only in-session — never written into the manual or repo.

**Remembers your answers (v0.8.0+):** on the next manual for a system you have documented before, the skill loads your previous answers (source, target users, annotation, font, numbering, locked terms, output format) and **asks only what is missing or changed** — stored per user in `~/.manual-maker/profiles/`. **Passwords / accounts / VPN are never saved — asked fresh every time.**

### Parallel work + per-section review (v0.17.0)

The slowest part of a manual — **capturing screenshots and writing steps** — is independent per subsection, so it runs in parallel.

**The unit of work is the subsection, not the phase.** One writer owns one subsection **end to end** (capture → annotate → write steps); it is never split into "a screenshotter" and "a writer", because the rule **red-circle number = step number, 1:1** is an invariant inside a subsection and splitting it breaks that rule.

| Work | Owner |
|------|-------|
| Capture + annotate + draft steps | `manual-section-writer` **×2–3**, one subsection each |
| Review each subsection as it lands | `manual-section-reviewer` **×1** (read-only) |
| Login · sources · assembly · 5-layer review · publish | main thread |

**No collisions:** each writer may write only its own subsection's files (`manual-assets/<slug>/<section>-*.png`, `manual-drafts/<slug>/<section>.md`); section numbers are assigned before dispatch; the `.docx` is assembled only in the main thread; login happens **once** and writers get a read-only session (no concurrent logins — that risks account lockout).

**Unclear → always ask first.** A subagent cannot talk to the user, so a writer that cannot source a step returns `BLOCKED`, and the reviewer splits findings into **fix-able** (the confirmed table already dictates the answer) and **must-ask** (everything else, and anything it is unsure about). Every question surfaces in chat — **nothing is guessed** — and a subsection with an open question is not done and is not assembled.

**Review is not reduced:** per-section review covers section-level only; defects created during file conversion (font fallback, คำพราก, dropped images, stale TOC, cross-chapter numbering, cover/header/footer) are provable only on the exported file, so the **5-layer delivery gate still runs in full**.

<details>
<summary>Automatic progress reports</summary>

While work is in subagents' hands you cannot see it, so the skill reports a table **whenever a subsection changes status, and at least every ~10 minutes**:

```
~40% เสร็จ

| ขั้น | สถานะ |
|---|---|
| Intake / ยืนยัน / อ่านแหล่ง | ✅ เสร็จ |
| จับภาพ | 🟡 17 ไฟล์ — เล่มครูครบ, เล่มผู้เรียนเหลือ 3 หัวข้อ |
| ปิดชื่อ + วงแดงมีเลข | ⬜ ยังไม่เริ่ม |
| ร่างเนื้อหา | ⬜ |
| ประกอบ .docx 2 เล่ม | ⬜ |
| ตรวจ + ส่งมอบ | ⬜ |
```

Claude Code has **no timer hook**, so the reminder rides tool calls and is throttled by wall clock — *at most ~10 minutes apart while work is running*, not exactly every 10 minutes. It is active only during a real run, silent otherwise.

| Variable | Effect |
|----------|--------|
| `MANUAL_MAKER_NO_PROGRESS=1` | Turn the reminder off (the skill still reports on status changes) |
| `MANUAL_MAKER_PROGRESS_INTERVAL=<seconds>` | Change the interval (default `600`, minimum `60`) |

</details>

### Customize for your team

Tune the skill with **no code — just two Markdown files:**

- `skills/manual-maker/references/intake.md` — the questions the skill asks. Add system-specific fields (environment, tenant, role matrix), change defaults, drop what you do not need.
- `skills/manual-maker/references/template.md` — the handbook structure, section order, tone, and step/screenshot conventions.

---

## Skill 2 — `confluence-docs`

**Purpose:** take a Confluence documentation space whose page structure is correct but whose values are **mock placeholders** (FEAT01, Module A, สมมติ) and **fill it with the real system's data**, one doc-type per run, creating or updating child pages. Built for the NDLP space `PLUT` (four subsystems: OLS / ELMS / CBMS / EvMS), but the target space and page are inputs — point it anywhere.

### Use it

```
/confluence-docs อัปเดต Technical Document
/manual-maker:confluence-docs populate the PRD page
```

| Entry point | Example | Notes |
|-------------|---------|-------|
| **Natural language** | `เติมข้อมูลจริงลง confluence แทน mock` | The skill triggers itself |
| **Short command** | `/confluence-docs อัปเดต <doc-type>` | Installed automatically |
| **Full command** | `/manual-maker:confluence-docs …` | Always works |

**How it runs (one doc-type per run):**

```
Preflight สิทธิ์เขียน → Intake → ยืนยัน (gate 1) → อ่านหน้าเดิม + ดึงแหล่ง → เติม mock→จริง →
ไดอะแกรม → รีวิวด่าน 1–4 → reconfirm ก่อนเขียน (gate 2) → publish → รีวิวด่าน 5 (render หน้าจริง)
```

- **Source-map per doc-type** — each doc-type maps to a **mandatory** authoritative source (PRD ← Jira filter, API Doc ← OpenAPI/repo, Data Dictionary ← DB schema, Meeting notes ← real minutes…). **No source → the run stops.** A placeholder is never guessed.
- **Structure-preserving** — reads and writes with `contentFormat: html`, changing only the *values*; every column, panel, and macro stays. A `Subsystem` column plus labels (`ols` / `elms` / `cbms` / `evms`) are the one convention across the space.
- **Two mandatory gates** — confirm the intake before any work, then **reconfirm before the first write** (showing the diff, the child pages to create, and the review result — then waits for "go").
- **Write is capability-gated** — the connector must expose `updateConfluencePage` / `createConfluencePage` and hold `write:page:confluence`. A preflight checks this; a read-only connector **stops with instructions** instead of faking a write.
- **Diagrams** — Atlassian MCP cannot upload images, so diagrams go in as **Confluence-rendered Mermaid** generated from the real source (ER from the schema, sequence from the flow) and are proven to render at review layer 5. Diagrams are never invented.
- **5-card review** (`references/review.md`) — (1) matches confirmation · (2) every value sourced + no mock left · (3) structure preserved · (4) text/numbers/terms · (5) renders on the live page. **ตรวจไม่ได้ = ไม่ผ่าน · needs 5/5 · one FAIL re-reviews all five.** `scripts/verify-confluence.py` is the mechanical gate (no mock leftover, locked terms not split, structure preserved, no credential leak) — exit 1 blocks the write. **Passing the script is not passing the review.**

> ℹ️ **Status:** v0.22.0 ships the full skill and a tested mechanical verifier. A real **end-to-end run against Confluence** (write, publish, diagram render) must happen in a session where the connector has `write:page:confluence` — it is not yet proven under a read-only grant.

### Customize

- `skills/confluence-docs/references/source-map.md` — each doc-type's required source.
- `skills/confluence-docs/references/template.md` — storage-format conventions (preserve structure, Subsystem column, tone).
- `skills/confluence-docs/references/intake.md` — the doc-type / source / subsystem questions.

---

## Bare commands & shims

Both short commands — `/manual-maker` and `/confluence-docs` — are installed **automatically** (v0.14.0+). At session start the plugin copies each `shim/*.md` into `~/.claude/commands/`, where user-level commands are **not namespaced**, so the short form resolves.

Why a shim is needed: Claude Code namespaces *every* plugin command as `/plugin-name:command-name` by design, and **no** frontmatter key, alias, or manifest field lets a plugin expose a bare name — only a file in `~/.claude/commands/` can.

**First session works too (v0.14.1+).** Claude Code reads the command list at session *start*, so a just-written shim isn't in that session's table and a bare command returns `Unknown command` — but Claude Code still delivers your text to the skill, and the hook instructs it to honour the intent anyway. From the next session the command resolves normally and the message stops.

**Good to know:**

- A shim is a **pure pointer** to the plugin skill — it holds no workflow logic, so it can't drift; the hook refreshes it when the source changes.
- It **never overwrites your file** — a pre-existing `~/.claude/commands/manual-maker.md` without the `managed-by: manual-maker-plugin` marker is left untouched.
- Shims live **outside** the plugin, so `/plugin uninstall` does not remove them: `rm ~/.claude/commands/manual-maker.md ~/.claude/commands/confluence-docs.md`.
- **Don't want the short commands?** Set `MANUAL_MAKER_NO_SHIM=1` and delete the files — the full `/manual-maker:…` forms still work, as does natural language.

<details>
<summary>Install a shim manually (auto turned off, or before a new session)</summary>

```bash
mkdir -p ~/.claude/commands
/usr/bin/curl -fsSL https://raw.githubusercontent.com/Thitic9203/manual-maker/main/shim/manual-maker.md \
  -o ~/.claude/commands/manual-maker.md
/usr/bin/curl -fsSL https://raw.githubusercontent.com/Thitic9203/manual-maker/main/shim/confluence-docs.md \
  -o ~/.claude/commands/confluence-docs.md
```

Use `/usr/bin/curl` (macOS's own) by full path on purpose — a MacPorts/Homebrew curl earlier on PATH often fails TLS to `raw.githubusercontent.com` with `unable to establish a secure connection`. On Linux, plain `curl` is fine.

</details>

---

## Requirements

All first-party / already available in Claude Code — nothing paid:

- **Skills:** `doc-coauthoring` (drafting), `docx` / `pdf` / `web-artifacts-builder` (export).
- **MCP:** Playwright or Chrome (screenshots + diagram-render checks), Atlassian (Confluence read/write). `confluence-docs` writing needs the Atlassian connector to hold `write:page:confluence`.
- The new-version check uses `curl` (ships with macOS) to read the public GitHub repo — free, no auth, no account.

## Repository structure

```
manual-maker/
├── .claude-plugin/
│   ├── plugin.json          # plugin manifest (name, version, description)
│   └── marketplace.json     # marketplace manifest (name: manual-maker-dev)
├── commands/
│   └── manual-maker.md      # /manual-maker:manual-maker — drives the manual pipeline to the end
├── shim/
│   ├── manual-maker.md      # auto-copied to ~/.claude/commands/ so bare /manual-maker works
│   └── confluence-docs.md   # same, for bare /confluence-docs (the hook installs both)
├── agents/
│   ├── manual-section-writer.md    # owns one subsection: capture → annotate → draft (2–3 run at once)
│   └── manual-section-reviewer.md  # reviews each subsection as it lands; read-only; asks, never decides
├── hooks/
│   ├── hooks.json           # registers the SessionStart + PostToolUse hooks
│   ├── check-version.sh     # installs both shims + background self-update (fail-silent)
│   └── progress-tick.sh     # ~10-min progress-table reminder during a manual run (fail-silent, opt-out)
├── scripts/
│   └── bump-version.sh      # bump the version everywhere in one command
├── CHANGELOG.md             # per-version history
├── RISK_REGISTER.md         # decisions with trade-offs, recorded so they aren't re-litigated
└── skills/
    ├── manual-maker/                 # Skill 1 — end-user handbooks
    │   ├── SKILL.md         # intake → confirm → sources → [parallel] → build → review → publish
    │   ├── scripts/
    │   │   ├── preflight.sh          # checks + installs capture tooling into ~/.manual-maker/runtime
    │   │   ├── verify-doc.py         # mechanical .docx checks; exit 1 blocks delivery
    │   │   └── verify-annotations.py # red-circle numbers vs the real pixels; exit 1 blocks delivery
    │   └── references/
    │       ├── intake.md · profile.md · parallel.md · screenshots.md · docx-build.md · review.md · template.md
    └── confluence-docs/              # Skill 2 — populate a Confluence space (mock → real)
        ├── SKILL.md         # preflight → intake → confirm → sources → draft → diagrams → review 1–4 → reconfirm → publish → review 5
        ├── scripts/
        │   └── verify-confluence.py  # no-mock-leftover, structure vs --original, term split, credential; exit 1 blocks the write
        └── references/
            ├── intake.md      # the doc-type / source / subsystem question set
            ├── source-map.md  # each doc-type → its mandatory authoritative source (blocks if none)
            ├── template.md    # storage-format conventions: preserve structure, Subsystem column, tone
            ├── diagrams.md    # Confluence-rendered Mermaid from the real source (no image upload)
            └── review.md      # the 5-card review gate (mechanical + human, before/after publish)
```

## Release (maintainers)

Never hand-edit version strings — one command bumps them all:

```bash
scripts/bump-version.sh minor   # or: patch | major | an explicit 0.3.0
```

It updates `plugin.json`, `marketplace.json` (×2), and the README badge + version line, and stamps a `CHANGELOG.md` entry. Then: (1) edit the CHANGELOG stub, (2) commit and push, (3) v0.6.0+ users get it automatically next session; personal-skill users re-copy.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `/plugin isn't available in this environment` | You're in the desktop/web app, not the CLI — `/plugin` is terminal-only | Run `claude` in a real Terminal, **or** use Option A (personal skill) |
| Pasting all commands at once errors | `claude` is a shell command; `/plugin` runs inside it | Do it step by step (Option B) |
| Skill does not trigger | Session started before install | Restart Claude Code / open a new session |
| Bare `/manual-maker` or `/confluence-docs` says `Unknown command` | Shim written this session isn't in the command table yet | Use it anyway (the hook honours intent), or `/reload-plugins`; the full `/manual-maker:…` form always works |
| Skill edits have no effect | Personal skill is a snapshot, not a live link | Re-copy the folder, or use the plugin route |
| `confluence-docs` stops at preflight | Atlassian connector is read-only (no `write:page:confluence`) | Grant write scope to the connector (via `/mcp` or claude.ai settings) and re-run |
| Confluence publish fails | Atlassian MCP not connected / wrong space key | Connect Atlassian MCP + check the space key from intake |
| Images missing on a Confluence page (manual-maker) | Atlassian MCP publishes the page body, not image files | Use **.docx/PDF** (default) or attach images / reference hosted URLs |
| Diagram shows raw code on the page (confluence-docs) | The space has no renderable Mermaid/diagram macro | Install a Mermaid app, or attach the image manually (see `references/diagrams.md`) |
| Screenshots not captured | Playwright/Chrome MCP not connected / URL needs login | Connect the MCP + check login steps in intake |
| Work is not running in parallel | Old session (agents load at start) **or** the run had a single subsection | Open a new session; check `manual-section-writer` / `manual-section-reviewer` are listed |
| Frequent questions during a run | The reviewer hit something the confirmation table didn't specify — **intentional; it asks, never guesses** | Answer once; give complete **source + locked-term list** at intake to reduce next time |

## Safety

- **No secrets in output or repo** — login steps describe the *procedure*, never real credentials; `confluence-docs` never writes a credential or a minor's identifier into a page.
- **Login once** in the main thread, shared read-only to writers — subagents never see the raw password and never log in themselves.
- Screenshots navigate only user-provided URLs.
- **Publishing is outward-facing** — both skills confirm the target before posting, and `confluence-docs` never writes ahead of its review passing.
- **Subagents cannot decide for you** — anything unclear returns to chat as a question first.

## Design decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Architecture | **Wrapper-delegate** (not fork) | Keeps upstream updates, low maintenance, no third-party content in the repo |
| Repo visibility | **Public** | No secrets, no Anthropic content — the team installs without auth |
| One plugin, two skills | `manual-maker` + `confluence-docs` | Related documentation jobs; skills auto-load from `skills/*/SKILL.md`, so no manifest change to add one |
| Pre-delivery review | **Multi-layer gate, ตรวจไม่ได้ = ไม่ผ่าน** | Proven on the real artifact (exported file / published page); one FAIL re-reviews every layer |
| Tooling setup | **Zero prep (v0.15.0+)** — the skill checks & installs into `~/.manual-maker/runtime/` | The user need not know a run wants Playwright/Chromium/Pillow; nothing global is touched |
| Distribution | Repo is its own marketplace (`source: "./"`) | The team installs directly from GitHub |
| Marketplace name | `manual-maker-dev` (≠ plugin name) | Mirrors the team's proven-working plugins |

## License

MIT
