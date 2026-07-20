---
name: confluence-docs
description: Use when replacing the mock/placeholder content of a Confluence documentation space with the real system's data, or creating/updating Confluence pages under a doc-type scaffold. Runs a structured intake, sources every value from an authoritative source (Jira filter / repo / OpenAPI / DB schema / spec / meeting notes) — never invents, delegates prose drafting to the doc-coauthoring skill, preserves each page's existing structure/format while swapping mock → real, embeds diagrams as Confluence-rendered code (Mermaid), and publishes via Atlassian MCP after a 5-layer review. Triggers on "อัปเดต confluence", "เติมข้อมูลจริงลง confluence", "แทน mock ใน confluence", "update confluence page", "populate the doc space", "confluence-docs".
---

# Confluence Docs

## Overview

Confluence Docs turns a **mock/placeholder Confluence doc-space** into a real one — it walks a
doc-type page tree whose structure and format are already correct but whose values are placeholders
(FEAT01, Module A, สมมติ) and **replaces every placeholder with the real system's data**, page by page,
creating extra child pages when a doc-type has many real instances.

It is a thin team wrapper that **composes** first-party skills — it does not re-implement or copy them:

- **Prose drafting** → `doc-coauthoring`
- **Publishing / reading** → Atlassian MCP (Confluence: `getConfluencePage`, `updateConfluencePage`, `createConfluencePage`)
- **Diagram render check** → Playwright / Chrome MCP (screenshot the published page)

This skill lives beside `manual-maker` in the same plugin and shares its non-negotiable ethos:
**ห้ามมโน · ยืนยันก่อนเริ่ม · ทุกค่ามีที่มา · อยู่ในขอบเขต · รีวิวก่อนส่ง.**

## The concrete target (default) — parameterizable

- **System:** NDLP, four subsystems — **OLS** (Open Learning System), **ELMS** (Extended LMS),
  **CBMS** (Credit Bank Management System), **EvMS** (Evaluation Management System).
- **Space:** `PLUT` — "SkillLane Pluton" · **cloudId** `dfc2cd04-b24b-48cf-81a1-4a3e0ed7569f`.
- **Scaffold root:** page **`3693641732`** — "Mica Phase 2 (Draft)"; ~25 doc-type child pages, each `(Mock)`.
- The doc-type set and the "ข้อมูลหลักที่ต้องกรอก" column of the scaffold's index page are the backbone
  of `references/source-map.md`. Target page/space are **inputs** — the skill works on any space when
  the user names a different one; PLUT/Mica is only the default.

## Non-negotiable working rules — read first

1. **ห้ามมโน / ห้ามคิดเอง / ห้ามตัดสินใจแทนผู้ใช้ / ห้ามโกหก.** If any value cannot be traced to an
   authoritative source, **STOP and ask** — never invent a feature name, a number, a term, an owner,
   a status, a schema column, or a diagram. Never report a check as passed when it was not run.
2. **ห้ามทำเกินขอบเขต.** Do only the one doc-type (and its children) confirmed for this run. No extra
   pages, no "while I'm here" edits to other doc-types, no opinions.
3. **ยืนยันก่อนเริ่มเสมอ.** After intake, summarize everything in a table and get an explicit "go"
   **before** reading sources or writing anything (Step 2 gate).
4. **ทุกค่ามีที่มา (source-map).** Every value that replaces a placeholder is traced to the doc-type's
   authoritative source in `references/source-map.md`. **No source for a doc-type → the run stops for
   that doc-type**; a placeholder is never filled with a guess.
5. **โครง/ฟอแมตคงเดิม.** The page's existing structure — table columns, headings, panels, macros — is
   **preserved exactly**. Only placeholder *values* change. Never rebuild a look-alike layout.
6. **Delivery gate — ผ่านรีวิว 5 ชั้นก่อนเท่านั้น** per `references/review.md`. **ตรวจไม่ได้ = ไม่ผ่าน.**
   One FAIL → fix, then **re-review all five layers**. Layers 1–4 are proven on the prepared body
   **before** any write; layer 5 (render) is proven on the **published page**. Publishing is
   outward-facing — it never precedes the layer 1–4 pass.
7. **Write is capability-gated.** Confluence writing needs the Atlassian connector to expose
   `updateConfluencePage`/`createConfluencePage` **and** hold `write:page:confluence` scope. Preflight
   checks this (Step 0); if missing, **STOP and tell the user how to enable it** — do not fake a write,
   do not silently downgrade to "here's the text, paste it yourself" unless the user chose that.

## When to Use

When the user wants a Confluence documentation space populated with real data in place of mock/
placeholder content, or specific doc-type pages created/updated from authoritative sources. **Not** for
end-user handbooks with annotated UI screenshots — that is `manual-maker`.

## Workflow

Track with TodoWrite: `Preflight → Intake → Confirm → Read target + Ingest sources → Draft (fill mock→real) → Diagrams → รีวิว 1–4 → Reconfirm ก่อนเขียน → Publish → รีวิว 5 (render) → done`.

**Two gates, both mandatory:** Step 2 (before any source-reading/drafting) and Step 7 (before the first
write). Never write without both.

**One doc-type per run** (parent page + its children). Iterative across runs.

### Running this skill's scripts — resolve the path first

`scripts/verify-confluence.py` lives **next to this file**, never in the user's project. The run's cwd
*is* the user's project, so a bare `scripts/verify-confluence.py` resolves there and looks missing — do
not conclude it is absent and hand-improvise. `CLAUDE_PLUGIN_ROOT` is **unset** in Bash tool calls and
the plugin cache path is version-stamped, so neither can be hardcoded. Inline this resolver in the
**same** Bash call as the script (shell state does not persist between tool calls):

```bash
CD=$(ls -d ~/.claude/plugins/cache/*/manual-maker/*/skills/confluence-docs 2>/dev/null | sort -V | tail -1); [ -n "$CD" ] || CD=~/.claude/skills/confluence-docs
/usr/bin/python3 "$CD/scripts/verify-confluence.py" <body.html> --terms "…"
```

### Step 0 — Preflight (write capability)

Before intake concludes, confirm the write path exists:

- The Atlassian MCP exposes `updateConfluencePage` **and** `createConfluencePage` (search the tool
  list). If they are absent, the connected connector is read-only.
- The connector holds `write:page:confluence` scope — check `getAccessibleAtlassianResources`; its
  `scopes` array must contain `write:page:confluence` (a read-only grant lists only `read:page…`).

If either is missing, **STOP** and report, verbatim intent:

> Atlassian connector ปัจจุบันเป็น read-only (ไม่มี `updateConfluencePage` หรือไม่มี scope
> `write:page:confluence`) — เขียน Confluence ไม่ได้. กรุณาเปิดสิทธิ์เขียนให้ connector (ผ่าน
> `/mcp` หรือ claude.ai connector settings แล้ว re-auth) แล้วรันใหม่.

Record the preflight result — it becomes the *สิทธิ์เขียน* row of the Step 2 table. Never proceed to a
write on an unverified capability.

### Step 1 — Intake (one question at a time)

Follow `references/intake.md` exactly — ask one at a time, honour bold defaults, never assume the
`(ต้องถาม)` ones (doc-type, target page, authoritative source, diagram source). The doc-type chosen
here selects its row in `references/source-map.md`, which dictates the required authoritative source.
The write-capability preflight (Step 0) and the Confirmation Gate are not questions — they run
automatically and as the final gate.

### Step 2 — Confirmation Gate (mandatory)

Print the summary table from `references/intake.md` (doc-type · target page + space/cloudId · subsystem
scope · authoritative source(s) · diagram source · update-vs-create · locked terms · language/tone ·
สิทธิ์เขียน). Ask verbatim: **"ยืนยันข้อมูลทั้งหมดถูกต้อง และเริ่มดำเนินการได้หรือไม่"** — proceed only on an
explicit "go". Do not read sources or write anything before this.

### Step 3 — Read target + ingest sources

- **Read the target page(s) in `html`** (`getConfluencePage`, `contentFormat: html`) — this is the
  ground truth for structure/format. Round-trip is safe in html (panels, macros, tables, local IDs
  preserved). Also read the scaffold index and any child pages in scope.
- **Read the locked-term source** — the space's `Wording Guideline` page — and use its term list
  throughout. A new concept with no locked term → **ask** the user which word, then add it there.
- **Ingest the authoritative source** named at intake, per `source-map.md`:
  - Jira filter → `searchJiraIssuesUsingJql` / the filter's JQL (e.g. NDLP subsystem filters 21689–21692).
  - Repo / OpenAPI / DB schema / spec / meeting notes → read the file/URL the user gave.
  - **If the source is missing or does not cover a required value → STOP and ask.** Do not fill it.

### Step 4 — Draft (fill mock → real)

- Call **`doc-coauthoring` once** (main thread) for the document-level voice/structure contract, then
  draft this doc-type's content against it. Do not copy doc-coauthoring's content into this repo.
- **Preserve the page's storage structure**; replace only placeholder values. Keep every table column,
  heading, panel, and macro. Placeholder nodes (`<span data-type="placeholder">…</span>`) are replaced
  by real content or, if genuinely not applicable, removed — never left as a placeholder.
- **Subsystem dimension:** every table carries a **`Subsystem`** column (values OLS / ELMS / CBMS /
  EvMS); tag the page with Confluence **labels** `ols` / `elms` / `cbms` / `evms` for the subsystems it
  covers. One consistent convention across the whole space.
- **Tone (see `references/template.md`):** formal, professional, human — no first/second-person
  pronouns, no sentence-final particles, one locked term per concept. Meeting-note / minutes doc-types
  may use natural attributed phrasing but still avoid ครับ/ค่ะ.
- **Create vs update:** update the mock page in-place for single-instance doc-types; for many-instance
  doc-types (PRD features, Meeting notes, BRD per module) update the index/parent in-place and
  **create** one child page per real instance under it (`createConfluencePage`, parent = the doc-type
  page). Confirm the instance list at intake before creating.

### Step 5 — Diagrams (only doc-types that need one)

Follow `references/diagrams.md`. Never invent a diagram: generate **diagram-as-code from the real
source** (ER from the DB schema, sequence from the flow/spec), embed it as a **Confluence-rendered
Mermaid macro**, and prove it renders at layer 5. If the space has no diagram macro that renders →
**ตรวจไม่ได้ = ไม่ผ่าน**: stop and tell the user to install one / attach the image manually. No source
for the diagram → the slot is a blocker, not a guess.

### Step 6 — รีวิว layers 1–4 (before any write)

Run `references/review.md` layers 1–4 on the **prepared storage body**:

```bash
CD=$(ls -d ~/.claude/plugins/cache/*/manual-maker/*/skills/confluence-docs 2>/dev/null | sort -V | tail -1); [ -n "$CD" ] || CD=~/.claude/skills/confluence-docs
/usr/bin/python3 "$CD/scripts/verify-confluence.py" <prepared-body.html> \
    --original <original-body.html> \
    --terms "<locked terms, comma-sep>"
```

The script proves the mechanical half (no mock/placeholder token survives, structure preserved,
locked terms not split, no credential leak, subsystem column present). **Exit 1 = ห้ามเขียน.** The
human half of layers 1–4 (values actually correct per the real system, tone) is judged by you against
the Step 2 table. A clean script run is necessary, never sufficient.

### Step 7 — Pre-write reconfirm gate (mandatory) → Publish

Writing to a shared team space is outward-facing and hard to walk back, so there is a **second explicit
gate here** — separate from the Step 2 intake gate. Only reach it after layers 1–4 are ✅.

**Reconfirm gate — before the first `update`/`create` call, show and ask:**

| จะเขียนอะไร | รายละเอียด |
|---|---|
| หน้าที่จะ update | space + page id + title (ตรงกับที่ยืนยัน Step 1) |
| สรุปการเปลี่ยน | ค่าไหน mock→จริง (สรุป/diff ย่อ), subsystem label ที่จะติด |
| หน้าลูกที่จะ **สร้างใหม่** | รายชื่อ instance ทั้งหมด (ถ้ามี) |
| ผลรีวิว 1–4 | ✅ ครบ (แนบตารางผล) |

Then ask verbatim: **"ยืนยันเขียนลง Confluence ตามนี้หรือไม่"** — **wait for an explicit "go".** Do not
call any write tool before this reply. If the user changes anything → fix, re-run layers 1–4, re-ask.

After the go:
- Update in-place → `updateConfluencePage` (`contentFormat: html`, the prepared body).
- New instance pages → `createConfluencePage` under the doc-type parent.

Publish the parent's index/table update **after** its child instances exist, so links resolve.

### Step 8 — รีวิว layer 5 (render, on the published page) + full verdict

Read the published page back (`getConfluencePage`, html) and **screenshot the live Confluence page**
(Playwright/Chrome MCP) to prove layer 5: tables render unbroken, the Mermaid macro renders as a
diagram (not raw code), TOC/links resolve, the Subsystem column shows, no คำพราก in Thai runs. Then
print the **5-layer verdict table** (format in `review.md`) every time. Deliver only on **5/5**. A
layer-5 failure means the live page is wrong — fix and **re-review all five layers**; on a production
space prefer publishing a **draft version** first when the connector supports it.

## Composition Note

Composes first-party skills (`doc-coauthoring`) via the Skill tool — no third-party skill content is
copied into this repo, so it stays public-safe and benefits from upstream updates.

## Safety

- **Credentials / tokens** are never written into a page, the repo, logs, or printed back.
- Reads and writes only the space/pages the user named; never other spaces.
- Confluence writing is outward-facing to a shared team space — **confirm the target before the first
  write**, and never write ahead of the layer 1–4 pass.
- All tooling is first-party / already connected — no paid services.
