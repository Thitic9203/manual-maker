---
name: manual-maker
description: Use when creating a user handbook or manual for a web system/app that end users read and follow. Runs a structured intake to gather system-specific details (system name, login, target users, modules, output format), optionally auto-captures UI screenshots with Playwright/Chrome, delegates the actual writing to the doc-coauthoring skill, applies the team's handbook template, and exports to Confluence, PDF, docx, or a web page. Triggers on "write a manual", "create a handbook", "user guide for <system>", "ทำคู่มือการใช้งาน", "คู่มือผู้ใช้".
---

# Manual Maker

## Overview

Manual Maker turns a working web system into a finished **user handbook** — the kind an end user reads and follows step by step.

It is a thin team wrapper that **composes** Anthropic's first-party skills (it does not re-implement or copy them):

- **Drafting** → `doc-coauthoring`
- **Export** → `docx` / `pdf` / `web-artifacts-builder`
- **Screenshots** → Playwright / Chrome MCP
- **Publishing** → Atlassian MCP (Confluence)

## Non-negotiable working rules — read first

1. **ห้ามมโน / ห้ามคิดเอง / ห้ามตัดสินใจแทนผู้ใช้.** If any input is missing, vague, or you are unsure, **STOP and ask**. Proceed only after an explicit, clear confirmation. Never invent a system step, a term, a font, or a number.
2. **ห้ามทำเกินขอบเขต.** Do only what was asked. No extra sections, no assumptions dressed up as facts.
3. **ยืนยันก่อนเริ่มเสมอ.** Summarize the request and all collected data, and get an explicit "go" **before** any screenshot or drafting.
4. **Every step must be sourced** — from the live system and the user's reference/Confluence/spec — not from guesswork. If you cannot source a step, ask.
5. **Review in detail before delivery** — complete, correct, consistent, nothing missed.

## When to Use

When the user wants a manual/handbook/user guide for a web system or app (e.g. "ทำคู่มือการใช้งานระบบ X ให้ผู้ใช้"). Not for API reference or code docs.

## Workflow

Track with TodoWrite: `Intake → Confirm → Ingest sources → Screenshots → Draft → Template+Quality → Final review → Export`.

### Step 1 — Intake (always first, one question at a time)

Read `references/intake.md`. **First load any saved profile** for this user + system per
`references/profile.md` (stored at `~/.manual-maker/profiles/`): if one exists, show it and ask
only what is **missing or changed** — never re-ask what the user already confirmed. Then ask the
remaining questions **one at a time**. Do not skip. Do not assume defaults for access, credentials,
sources, fonts, or terminology. **Credentials are never stored — always ask them fresh in-session.**

### Step 2 — Confirmation Gate (mandatory — do not skip)

Print the summary table from the end of `intake.md` and ask **"ยืนยันข้อมูลทั้งหมดถูกต้อง เริ่มทำได้เลยไหมครับ?"**. **Do nothing else** — no screenshots, no drafting — until the user explicitly confirms. If anything is "ไม่แน่ใจ", resolve it first.

**On confirmation, save the profile** per `references/profile.md` — the confirmed answers **minus every credential/secret** — so the next run for this system does not re-ask.

### Step 3 — Ingest sources (grounds the content)

- If the user gave a **reference/example document** → read it (docx/pdf) to copy the layout, font, section structure, and terminology.
- If the user gave **Confluence pages / spec / flow** → read them (Atlassian MCP `getConfluencePage`, or fetch) to learn the **real** steps.
- Lock the **terminology list** (from intake Q14) and read it back for confirmation.

Never write a step you cannot source. If a detail is unclear → ask.

### Step 4 — Screenshots (optional)

Use Playwright / Chrome MCP. Navigate **only** user-provided URLs; use credentials **only** in-session (never stored/printed). If annotation was requested → draw **boxes + numbered markers** on the click target, matching the step numbers. Save to `assets/`, named by section+step (e.g. `03-login-01.png`). Keep every image **sharp and legible**.

### Step 5 — Draft (delegate to doc-coauthoring)

Invoke the **`doc-coauthoring`** skill via the Skill tool. Pass: the confirmed intake, the reference-doc format, the ingested sources, `references/template.md`, the locked terms, and the screenshot list.

Draft **section by section**, grounded only in verified sources, in the chosen language (default Thai). Follow the **Language & tone** rules in `references/template.md`: formal, professional written language, **no first/second-person pronouns** (ผม/ฉัน/คุณ/ท่าน), **no sentence-final particles** (ครับ/ค่ะ/นะ), natural and human — not machine-translated. Use the **locked term everywhere** — one word per concept. If a needed fact is missing → stop and ask; do not fill the gap with assumption.

### Step 6 — Apply template + quality rules

Match `references/template.md` and enforce its four quality axes: **font & size**, **numbering consistency**, **image clarity + annotation**, **terminology consistency**.

### Step 7 — Final review before delivery (mandatory, detailed)

Run the **Final Review Checklist** in `references/template.md` line by line. Fix everything. Deliver only when nothing is missing, wrong, or inconsistent.

### Step 8 — Export / publish

| Format | How |
|--------|-----|
| Confluence | Atlassian MCP `createConfluencePage` / `updateConfluencePage` under the space+parent from intake. **Confirm target before posting.** |
| PDF | `pdf` skill |
| docx | `docx` skill |
| Web page | `web-artifacts-builder` skill |

## Composition Note

Composes first-party skills via the Skill tool — no third-party content is copied into this repo, so it stays public-safe and benefits from upstream updates.

## Safety

- **Credentials** are used only in-session to reach the screens — never written into the manual, repo, logs, or any file, and never printed back.
- Screenshots navigate only user-provided URLs; never arbitrary or emailed links.
- Confluence/web publishing is outward-facing — confirm the target before posting.
- All tooling is first-party / already installed — no paid services.
