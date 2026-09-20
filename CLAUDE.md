# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`manual-maker` is a **Claude Code plugin (skill)**, not an application. It has no build system, no tests, no CI, and no runtime code — it is Markdown (the skill) plus two JSON manifests (plugin + marketplace). The deliverable is the *behavior* Claude exhibits when the skill fires, defined entirely in `skills/manual-maker/`.

**Purpose:** produce **end-user manuals / handbooks for web systems** — step-by-step guides a non-technical reader follows to operate a system (access & login → each feature, with annotated screenshots), exported to Confluence / PDF / Word / web. Everything in this repo exists to make those manuals **accurate, consistent, and professionally written**; judge changes by whether they improve that outcome.

<!-- rule:token-context-budget v1 · the same rule in every repo (Thai and English versions) · change one, change all -->
## Token and context budget (iron rule)

**Correctness and completeness come before saving tokens.** Never skip reading the spec, running tests, verifying, or collecting evidence to cut tokens. If the right path costs more, take it and find a cheaper way to walk it. A context window near full makes the model forget early instructions and make more mistakes, so the 70% ceiling protects quality as much as cost.

**Read only what the work needs, with the context-management skill that fits. Invoke skills on need, never in advance.**
- Output that may be large (logs, test runs, JSON, API responses, web pages, data files) goes through the `context-mode` skill (`ctx_execute`, `ctx_batch_execute`, or `ctx_fetch_and_index` then `ctx_search`), so only the derived answer enters context. Without that skill, filter before reading (`rtk`, `grep`, `jq`, `tail`).
- For code, locate before reading (Grep/Glob, or the `smart-explore` skill at symbol level), then Read only the needed range with offset/limit. Do not open a long file whole when a range will do.
- Broad exploration across many files or sources goes to a subagent, which returns conclusions with `path:line`. A lookup whose location is already known is cheaper done directly.
- Prefer page text or the accessibility tree over screenshots. Do not re-read a file you just wrote. Point to a path instead of pasting long file contents into chat.
- A skill already loaded this session needs no second invocation. Independent tool calls go out together in one round.

**Measure context at the end of every major step; never guess the number.**
- Add `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` from the latest assistant message in the session transcript `~/.claude/projects/*/<session-id>.jsonl` (the id is in `$CLAUDE_SESSION_ID` or `$CLAUDE_CODE_SESSION_ID`) and divide by the model's context window, or ask the user to run `/context`. If it cannot be measured or the window size is unknown, ask the user.
- At 60%, write a checkpoint file: what is done, the evidence, the next step, and what to read next.
- At 70%, stop pulling raw data into context, hand the remaining reading to subagents, and tell the user, proposing `/compact <what to keep>` or a fresh session that resumes from the checkpoint.

**CLAUDE.md loads in every session.** Add only rules needed every time, and keep them short. Move details, long procedures, and incident history into skills or documents read on demand, each with a line saying when to read it. Official guidance puts CLAUDE.md under 200 lines, and `@import`ed files still load at session start.

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

## Preflight — the skill installs its own tooling (v0.15.0+)

รายละเอียดทั้งหมดอยู่ใน [`docs/PREFLIGHT.md`](docs/PREFLIGHT.md) — การติดตั้ง tooling ของสกิล อ่านไฟล์นั้นก่อนแตะเรื่องนี้ทุกครั้ง

## The delivery gate — รีวิว 5 ชั้น (v0.16.0+)

รายละเอียดทั้งหมดอยู่ใน [`docs/DELIVERY_GATE.md`](docs/DELIVERY_GATE.md) — รีวิว 5 ชั้นก่อนส่งมอบ อ่านไฟล์นั้นก่อนแตะเรื่องนี้ทุกครั้ง

## The feedback 5-layer guards (v0.25.0+) — the team's five defects can't recur

รายละเอียดทั้งหมดอยู่ใน [`docs/FEEDBACK_GUARDS.md`](docs/FEEDBACK_GUARDS.md) — feedback 5-layer guards อ่านไฟล์นั้นก่อนแตะเรื่องนี้ทุกครั้ง

## Parallel Steps 4–6 + per-section review (v0.17.0+)

รายละเอียดทั้งหมดอยู่ใน [`docs/PARALLEL_STEPS.md`](docs/PARALLEL_STEPS.md) — การรัน Step 4–6 ขนาน + per-section review อ่านไฟล์นั้นก่อนแตะเรื่องนี้ทุกครั้ง

## Document quality standards (load-bearing — the manual is judged on these)

These live in `template.md` and are enforced in the `SKILL.md` draft + review steps. They are the point of the repo, not decoration — do not weaken them:

- **Tone & language.** Formal, professional, **human** written language — never machine-translated stiffness. **No first/second-person pronouns** (ผม / ฉัน / คุณ / ท่าน) — use the imperative or the locked role term. **No sentence-final particles** (ครับ / ค่ะ / นะ).
- **Terminology consistency.** One **locked term** per concept, used identically throughout (e.g. always "ผู้เรียน", never "นักเรียน" / "นร."). Confirm the term list with the user; if a new term appears mid-draft, ask which word to use.
- **Numbering.** Continuous decimal outline (`1`, `1.1`, `1.1.1`) — no gaps or duplicates; the table of contents matches the body.
- **Font & size.** Taken from the user's reference document or explicitly confirmed — **never assumed**; uniform across the whole manual.
- **Image clarity + annotation.** Every screenshot sharp and legible; when requested, a **box (กรอบ) + numbered marker (เลขลำดับ)** on the click target, in a consistent style throughout.
- **Output format.** Word (`.docx`) / PDF / Confluence / web — the skill **always asks which** when the user hasn't said, phrased for non-technical users.


**A name scrub that cannot fail is not a safeguard.** Screenshot name-masking happens in the DOM immediately before the shutter, and the capture **aborts** if any known name survives a re-read of `document.body.innerText`. This is not belt-and-braces: on the ELMS run the scrub ran, silently missed one account chip, and the real teacher's name reached a delivered `.docx`. The two pixel-masking alternatives were both measured and both worse — a fixed top-right box misses the chip because a `fullPage` capture renders the sticky header wherever the page was scrolled, and a "find the pale header band" heuristic matches white table rows and paints over content (nine places on one image). Names must also be **collected from the page** (the chip's own text, plus `ครู <name>` matches), because a hardcoded list cannot know the account a future run uses — that is exactly how the last leak survived three passes that each reported themselves clean. Student identifiers (`รหัสนักเรียน`, `เลขที่นักเรียน`) are masked too; an ID identifies a minor as surely as a name.

## Second skill — `confluence-docs` (v0.22.0+, this repo hosts two skills now)

รายละเอียดทั้งหมดอยู่ใน [`docs/SKILL_CONFLUENCE_DOCS.md`](docs/SKILL_CONFLUENCE_DOCS.md) — สกิล confluence-docs อ่านไฟล์นั้นก่อนแตะเรื่องนี้ทุกครั้ง

## Third skill — `screen-record`, and the one invariant that must never be undone (v0.35.0+)

รายละเอียดทั้งหมดอยู่ใน [`docs/SKILL_SCREEN_RECORD.md`](docs/SKILL_SCREEN_RECORD.md) — สกิล screen-record อ่านไฟล์นั้นก่อนแตะเรื่องนี้ทุกครั้ง

## Release workflow & gotchas

รายละเอียดทั้งหมดอยู่ใน [`docs/RELEASE.md`](docs/RELEASE.md) — ขั้นตอน release และ gotchas อ่านไฟล์นั้นก่อนแตะเรื่องนี้ทุกครั้ง

## Two install/distribution paths

- **Personal skill** — `cp -r skills/manual-maker ~/.claude/skills/manual-maker`. A snapshot: it does **not** auto-sync, so re-copy after every change. Skills work without the plugin system. Don't keep this alongside the installed plugin — two skills named `manual-maker` collide; pick one source.
- **Plugin, interactive** — inside a Claude Code TUI session: `/plugin marketplace add Thitic9203/manual-maker` then `/plugin install manual-maker@manual-maker-dev`. `/plugin` is a session-only slash command (not the shell, not desktop/web app).
- **Plugin, headless CLI** (no interactive `/plugin` needed) — from any shell: `claude plugin marketplace add Thitic9203/manual-maker`, `claude plugin install manual-maker@manual-maker-dev`, verify with `claude plugin list`. This is the way to install/verify outside a TUI (desktop/web app, scripts, agents). `claude plugin validate <path>` checks a manifest without installing.

Either way, changes require a restart / new session to load.

## Conventions

- **Bilingual TH/EN.** The audience is a Thai QA team; the skill defaults to Thai output, and docs/intake/template mix Thai and English intentionally. Keep new user-facing strings bilingual and preserve Thai defaults.
- **Safety is part of the spec, not a nicety.** Never record real credentials/tokens — login steps describe the *procedure* only. Screenshots navigate only user-provided URLs. Confluence/web publishing confirms the target before the first post. These rules live in SKILL.md, template.md, and README and must stay consistent across all three.
- **Free tooling only.** Everything the skill depends on is first-party/already installed — no paid services. Don't introduce a dependency that bills.
