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
6. **ต้นแบบคือของจริง.** If the user supplies a base/reference document, reproduce its **cover, header, footer (page numbers), TOC, styles, and role-based chapters exactly** — never a hand-built look-alike. See `references/docx-build.md`.
7. **ภาพต้องเป็นหน้าจอระบบจริง.** Every figure is a **real, full-screen** screenshot of the live system, with **red numbered circles whose numbers match the step numbers**. No placeholders, no mock-ups, no redrawn tables standing in for a screen. See `references/screenshots.md`.
8. **Login is headless & env-seeded; credentials are session-only.** Screenshots use a **headless Playwright** browser that authenticates by reading the credential **from the environment** (`process.env.EMAIL`/`process.env.PW`) or a pre-saved `storageState` — Claude **never types a password into a live form by hand**. The secret is used only in-session, **never** written to the manual, repo, logs, a committed script, or the profile, and **never echoed** (show `password provided (not shown)`). If login can't be automated (SSO/MFA/captcha), the **user logs in** and Claude captures read-only. See `references/screenshots.md`.

## When to Use

When the user wants a manual/handbook/user guide for a web system or app (e.g. "ทำคู่มือการใช้งานระบบ X ให้ผู้ใช้"). Not for API reference or code docs.

## Workflow

Track with TodoWrite: `Intake → Confirm → Ingest sources → Screenshots → Draft → Template+Quality → Final review → Export`.

### Step 1 — Intake (always first, one question at a time)

Read `references/intake.md`. **First load any saved profile** for this user + system per
`references/profile.md` (stored at `~/.manual-maker/profiles/`): if one exists, show it and ask
only what is **missing or changed** — never re-ask what the user already confirmed. Then ask the
remaining questions per `intake.md` **Sequencing**: the *(ต้องถาม)* questions (no default) **one at
a time**, and the default-bearing questions as **one confirm-batch** (show the defaults, ask once
what to change). Do not skip. Do not assume defaults for access, credentials, sources, fonts, or
terminology. **Credentials are never stored — always ask them fresh in-session.**

**Then run preflight — the user is not expected to know what a capture run needs.** Once the
screenshot question is answered **yes**, run this skill's **`scripts/preflight.sh --check`**
(read-only, installs nothing) and put its result table into the Step 2 summary as the
*เครื่องมือที่ต้องใช้* row, download sizes included. **If screenshots = no, skip preflight
entirely** — a text-only manual needs no browser. Never ask the user to install anything by hand.

### Step 2 — Confirmation Gate (mandatory — do not skip)

Print the summary table from the end of `intake.md` and ask **"ยืนยันข้อมูลทั้งหมดถูกต้อง เริ่มทำได้เลยไหมครับ?"**. **Do nothing else** — no screenshots, no drafting — until the user explicitly confirms. If anything is "ไม่แน่ใจ", resolve it first.

**On confirmation, save the profile** per `references/profile.md` — the confirmed answers **minus every credential/secret** — so the next run for this system does not re-ask.

**On confirmation, also install the missing tools** — run `scripts/preflight.sh --install` before
Step 3. It installs only what the check found missing, into the skill-owned sandbox
`~/.manual-maker/runtime/` (never the user's projects, never global npm), and is a no-op once
satisfied. The user's single "go" covers this — do **not** open a second gate for it. If it exits
`blocked`, show the reason and stop: capture cannot proceed, and inventing screens is forbidden.

### Step 3 — Ingest sources (grounds the content)

- If the user gave a **base/reference document (ต้นแบบ)** → read it (docx/pdf) and **build on it**, reusing its cover, header, footer, TOC, styles, role-based chapters, font, and terminology. Do not approximate it by hand — see `references/docx-build.md`.
- If the user gave **Confluence pages / spec / flow** → read them (Atlassian MCP `getConfluencePage`, or fetch) to learn the **real** steps.
- Lock the **terminology list** (from intake Q15) and read it back for confirmation.

Never write a step you cannot source. If a detail is unclear → ask.

### Step 4 — Screenshots

**Read `references/screenshots.md` and follow it exactly.** In short: real live-system screens only,
**full screen** (never crop the content), **red numbered circles that map 1:1 to the step numbers**
(≤ 5 per image), steps written with the system's real menu/button wording, and people's names masked.
Preflight (Step 1/2) already installed the tooling. Run every capture script with the sandbox on
`NODE_PATH` — a global `npm i -g playwright` does **not** make `require('playwright')` resolve from
an arbitrary directory, which is exactly how a run fails without this:
```bash
NODE_PATH="$HOME/.manual-maker/runtime/node_modules" node capture.js
```

**Primary path = headless Playwright — non-intrusive:** a `headless: true` browser logs in once by
reading the credential **from the environment** (`process.env.EMAIL`/`process.env.PW`, or a saved
`storageState`), reuses that session, and captures each screen **direct-to-disk** (`fullPage`, saved
as `manual-assets/<slug>/<section>-<step>.png`). It never takes over the user's real screen, so there
is **no glow border and no cursor to clean up** — the glow/cursor cleanup and the clipboard bridge are
the **fallback only**, for screens headless can't reach (SSO/MFA/captcha), where the **user logs in**
and Claude captures read-only. Drive the browser **read-only** — never click create/edit/delete on a
live system while capturing.

### Step 5 — Draft (delegate to doc-coauthoring)

Invoke the **`doc-coauthoring`** skill via the Skill tool. Pass: the confirmed intake, the reference-doc format, the ingested sources, `references/template.md`, the locked terms, and the screenshot list.

Honor the confirmed **document split (intake Q9)**: one deliverable per confirmed volume (per role, per system/module, or a single combined volume) — never merge or split differently from what the user confirmed.

Draft **section by section**, grounded only in verified sources, in the chosen language (default Thai). Follow the **Language & tone** rules in `references/template.md`: formal, professional written language, **no first/second-person pronouns** (ผม/ฉัน/คุณ/ท่าน), **no sentence-final particles** (ครับ/ค่ะ/นะ), natural and human — not machine-translated. Use the **locked term everywhere** — one word per concept. If a needed fact is missing → stop and ask; do not fill the gap with assumption.

### Step 6 — Apply template + quality rules

Match `references/template.md` and enforce its four quality axes: **font & size**, **numbering consistency**, **image clarity + annotation**, **terminology consistency**.

### Step 7 — Final review before delivery (mandatory, detailed)

Run the **Final Review Checklist** in `references/template.md` line by line. Fix everything. Deliver only when nothing is missing, wrong, or inconsistent.

### Step 8 — Export / publish

| Format | How |
|--------|-----|
| Confluence | Atlassian MCP `createConfluencePage` / `updateConfluencePage` under the space+parent from intake. **Confirm target before posting.** ⚠️ The MCP publishes the **page body/structure only — it does not upload screenshot files.** Embed images via a pre-hosted URL, or attach them to the page manually; for **image-heavy** manuals (the usual case) prefer **docx/PDF**. |
| PDF | `pdf` skill |
| docx | `docx` skill — **and `references/docx-build.md`**: if there is a base template, edit its OOXML (`unzip → word/document.xml → zip`); docx-js cannot open an existing file. Font **TH SarabunPSK**, body 16 pt / headings 18 pt bold, with the **`w:cs`** slot set. |
| Web page | `web-artifacts-builder` skill |

## Composition Note

Composes first-party skills via the Skill tool — no third-party content is copied into this repo, so it stays public-safe and benefits from upstream updates.

## Safety

- **Credentials** are used only in-session to reach the screens — never written into the manual, repo, logs, or any file, and never printed back.
- Screenshots navigate only user-provided URLs; never arbitrary or emailed links.
- Confluence/web publishing is outward-facing — confirm the target before posting.
- All tooling is first-party / already installed — no paid services.
