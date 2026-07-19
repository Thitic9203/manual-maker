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
5. **Delivery gate — ผ่านรีวิว 5 ชั้นก่อนเท่านั้น.** Never say "เสร็จแล้ว" / "ส่งงานได้" / hand the
   file over until **all five review layers pass** per `references/review.md`. **ตรวจไม่ได้ = ไม่ผ่าน**
   — there is no "น่าจะผ่าน". One FAIL → fix, then **re-review all five layers**, because fixing one
   breaks another (adding a figure shifts the step numbers). Review the **exported file**, never the
   draft in conversation.
6. **ต้นแบบคือของจริง.** If the user supplies a base/reference document, reproduce its **cover, header, footer (page numbers), TOC, styles, and role-based chapters exactly** — never a hand-built look-alike. See `references/docx-build.md`.
7. **ภาพต้องเป็นหน้าจอระบบจริง.** Every figure is a **real, full-screen** screenshot of the live system, with **red numbered circles whose numbers match the step numbers**. No placeholders, no mock-ups, no redrawn tables standing in for a screen. Circles are **derived from the final step list** and recorded in `annotations.json` as they are drawn; `scripts/verify-annotations.py` proves the 1:1 claim against the pixels at Step 8. See `references/screenshots.md`.
8. **งานขนานห้ามลดคุณภาพ และ subagent ห้ามตัดสินใจแทนผู้ใช้.** Steps 4–6 fan out across 2–3
   `manual-section-writer` agents plus **one** `manual-section-reviewer` that reviews each หัวข้อย่อย
   as it lands — see `references/parallel.md`. A subagent **cannot talk to the user**, so anything
   unclear comes back as `BLOCKED`/`ASK` and **this thread asks the user in chat** before any fix is
   chosen. Per-section review is a **pre-check, never a replacement** for the Step 8 five-layer gate.
9. **Login is headless & env-seeded; credentials are session-only.** Screenshots use a **headless Playwright** browser that authenticates by reading the credential **from the environment** (`process.env.EMAIL`/`process.env.PW`) or a pre-saved `storageState` — Claude **never types a password into a live form by hand**. The secret is used only in-session, **never** written to the manual, repo, logs, a committed script, or the profile, and **never echoed** (show `password provided (not shown)`). If login can't be automated (SSO/MFA/captcha), the **user logs in** and Claude captures read-only. See `references/screenshots.md`.

## When to Use

When the user wants a manual/handbook/user guide for a web system or app (e.g. "ทำคู่มือการใช้งานระบบ X ให้ผู้ใช้"). Not for API reference or code docs.

## Workflow

Track with TodoWrite: `Intake → Confirm → Ingest sources → [Screenshots → Draft → Template+Quality ขนานต่อหัวข้อย่อย + รีวิวทีละหัวข้อ] → Build file → รีวิว 5 ชั้น → ส่งมอบ/publish`.

**Build before review, publish after it.** The review must run on the **exported file**, so the file
is built at Step 7, reviewed at Step 8, and only **published/handed over at Step 9** — Confluence
posting and delivery are outward-facing and must never happen ahead of a 5/5 verdict.

**Steps 4–6 run in parallel, one หัวข้อย่อย per writer.** Everything before and after them stays in
this thread. Read `references/parallel.md` before dispatching.

**Running this skill's scripts — always resolve the path first.** `scripts/preflight.sh`,
`scripts/verify-doc.py`, and `scripts/verify-annotations.py` live **next to this file**, never in the
user's project. The run's cwd *is*
the user's project, so a bare `scripts/preflight.sh` resolves there, is not found, and the script
looks like it does not exist — do **not** conclude it is missing and hand-improvise the step. Neither
shortcut works either: `CLAUDE_PLUGIN_ROOT` is **unset** in Bash tool calls (hooks get it, tool calls
do not), and the plugin cache path is version-stamped, so it cannot be hardcoded. Resolve it in the
**same** Bash call as the script — shell state does not survive between calls:

```bash
MM=$(ls -d ~/.claude/plugins/cache/*/manual-maker/*/skills/manual-maker 2>/dev/null | sort -V | tail -1); [ -n "$MM" ] || MM=~/.claude/skills/manual-maker
"$MM/scripts/preflight.sh" --check
```

`sort -V | tail -1` picks the newest installed version; the fallback covers the personal-skill
install (`cp -r skills/manual-maker ~/.claude/skills/`). If `$MM` comes back empty **and** the
fallback path has no `scripts/`, say so and stop — never substitute a hand-rolled preflight.

### Step 1 — Intake (always first, one question at a time)

Read `references/intake.md`. **First load any saved profile** for this user + system per
`references/profile.md` (stored at `~/.manual-maker/profiles/`): if one exists, show it and ask
only what is **missing or changed** — never re-ask what the user already confirmed. Then ask the
remaining questions per `intake.md` **Sequencing**: the *(ต้องถาม)* questions (no default) **one at
a time**, and the default-bearing questions as **one confirm-batch** (show the defaults, ask once
what to change). Do not skip. Do not assume defaults for access, credentials, sources, fonts, or
terminology. **Credentials are never stored — always ask them fresh in-session.**

**Then run preflight — the user is not expected to know what a capture run needs.** Once the
screenshot question is answered **yes**, run this skill's **`preflight.sh --check`** (read-only,
installs nothing) via the resolver above:

```bash
MM=$(ls -d ~/.claude/plugins/cache/*/manual-maker/*/skills/manual-maker 2>/dev/null | sort -V | tail -1); [ -n "$MM" ] || MM=~/.claude/skills/manual-maker
"$MM/scripts/preflight.sh" --check
```

Put its result table into the Step 2 summary as the *เครื่องมือที่ต้องใช้* row, download sizes
included. **If screenshots = no, skip preflight entirely** — a text-only manual needs no browser.
Never ask the user to install anything by hand.

### Step 2 — Confirmation Gate (mandatory — do not skip)

Print the summary table from the end of `intake.md` and ask **"ยืนยันข้อมูลทั้งหมดถูกต้อง เริ่มทำได้เลยไหมครับ?"**. **Do nothing else** — no screenshots, no drafting — until the user explicitly confirms. If anything is "ไม่แน่ใจ", resolve it first.

**On confirmation, save the profile** per `references/profile.md` — the confirmed answers **minus every credential/secret** — so the next run for this system does not re-ask.

**On confirmation, also open the progress marker** so the user gets periodic updates during the long
part of the run:

```bash
mkdir -p ~/.manual-maker/state && date +%s > ~/.manual-maker/state/run.active
```

While that file exists, `hooks/progress-tick.sh` reminds this thread every ~10 minutes to print the
progress table (format in `references/parallel.md`). **Delete it at Step 9 when the manual is
delivered** — `rm -f ~/.manual-maker/state/run.active ~/.manual-maker/state/last-tick`.

**On confirmation, also install the missing tools** — run `preflight.sh --install` before Step 3,
same resolver:

```bash
MM=$(ls -d ~/.claude/plugins/cache/*/manual-maker/*/skills/manual-maker 2>/dev/null | sort -V | tail -1); [ -n "$MM" ] || MM=~/.claude/skills/manual-maker
"$MM/scripts/preflight.sh" --install
```

It installs only what the check found missing, into the skill-owned sandbox
`~/.manual-maker/runtime/` (never the user's projects, never global npm), and is a no-op once
satisfied. The user's single "go" covers this — do **not** open a second gate for it. If it exits
`blocked`, show the reason and stop: capture cannot proceed, and inventing screens is forbidden.

### Step 3 — Ingest sources (grounds the content)

- If the user gave a **base/reference document (ต้นแบบ)** → read it (docx/pdf) and **build on it**, reusing its cover, header, footer, TOC, styles, role-based chapters, font, and terminology. Do not approximate it by hand — see `references/docx-build.md`.
- If the user gave **Confluence pages / spec / flow** → read them (Atlassian MCP `getConfluencePage`, or fetch) to learn the **real** steps.
- Lock the **terminology list** (from intake Q15) and read it back for confirmation.

Never write a step you cannot source. If a detail is unclear → ask.

### Steps 4–6 — กระจายงานต่อหัวข้อย่อย + รีวิวทีละหัวข้อ (อ่าน `references/parallel.md` ก่อนสั่งงาน)

Steps 4, 5 and 6 are **one unit of work per หัวข้อย่อย** — capture → annotate → draft — and that unit
goes to **one** `manual-section-writer`, because "เลขในวงแดง = เลขขั้นตอน 1:1" is an invariant *inside*
a หัวข้อย่อย: split capture from drafting and it breaks immediately.

**Before dispatching, all of this must already be settled in this thread:** the user's Step 2
confirmation · the outline with **every หัวข้อย่อย number pre-assigned** (writers never number
themselves) · the ingested sources (Step 3) summarised per หัวข้อ · the locked term list · a saved
`storageState` from **one** headless login. Missing any of these, do not fan out.

Then dispatch **2–3 writers in a single message** (separate messages run them serially and buy
nothing), and after each หัวข้อย่อย comes back, hand it straight to the **single**
`manual-section-reviewer` — do not wait for the other writers. The reviewer returns `FIX`
(the confirmed table already dictates the one correct answer → the writer just fixes it) and `ASK`
(**anything needing judgement, and anything the reviewer is unsure of** → **ถามผู้ใช้ในแชทก่อนเสมอ**,
never decide for them). A หัวข้อย่อย with an open `ASK` is **not done** and does not go into the file.

`references/parallel.md` holds the ownership table, the brief template, and the loop in full.

### Step 4 — Screenshots (per หัวข้อย่อย, by its writer)

**Log in once here, in this thread** — headless and env-seeded per `screenshots.md` — and save the
`storageState` for the writers to reuse read-only. Writers never log in themselves: three concurrent
logins risk locking the account and spread the credential further than needed.

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

### Step 5 — Draft (doc-coauthoring once, then per-หัวข้อย่อย by the writers)

Invoke the **`doc-coauthoring`** skill via the Skill tool **once, here** — not inside each writer.
Pass: the confirmed intake, the reference-doc format, the ingested sources, `references/template.md`,
the locked terms, and the screenshot list. What comes back is the **document-level contract**
(structure, voice, sentence shape) that every writer then drafts its own หัวข้อย่อย against. Calling
it three times in parallel would produce three different styles — the exact defect the manual is
judged on.

Honor the confirmed **document split (intake Q9)**: one deliverable per confirmed volume (per role, per system/module, or a single combined volume) — never merge or split differently from what the user confirmed.

Draft **section by section**, grounded only in verified sources, in the chosen language (default Thai). Follow the **Language & tone** rules in `references/template.md`: formal, professional written language, **no first/second-person pronouns** (ผม/ฉัน/คุณ/ท่าน), **no sentence-final particles** (ครับ/ค่ะ/นะ), natural and human — not machine-translated. Use the **locked term everywhere** — one word per concept. If a needed fact is missing → stop and ask; do not fill the gap with assumption.

### Step 6 — Apply template + quality rules

Match `references/template.md` and enforce its four quality axes: **font & size**, **numbering consistency**, **image clarity + annotation**, **terminology consistency**.

Each writer applies these to its own หัวข้อย่อย and the reviewer checks them there. The axes that
only exist across the whole document — TOC, cross-chapter numbering, uniform font in the built file —
are settled in this thread at Step 7 and proven at Step 8.

**Assemble only from หัวข้อย่อย that passed review with no open `ASK`.** Collect the per-section
drafts from `manual-drafts/<slug>/` in outline order; do not let a writer edit the assembled document.

### Step 7 — Build the deliverable file (do **not** publish yet)

Produce the actual file in the confirmed format — `docx` skill (+ `references/docx-build.md`), `pdf`,
or the web/Confluence body. **Building is not delivering:** nothing is posted to Confluence, sent, or
described as finished until Step 8 returns 5/5. See the format table in Step 9.

**Where the finished file goes — `~/Downloads/` itself, never a subfolder.** Write every delivered
document straight to `~/Downloads/<ชื่อไฟล์>`. Do **not** create an `output/` folder, do **not** nest it
beside the user's source material, and do **not** invent a per-run directory — the user opens
`~/Downloads` and the manual is simply there. A by-role/-module split puts each volume in that same
place, distinguished by filename (`คู่มือการใช้งาน <ระบบ> - <บทบาท>.docx`), not by folder.

Working files are a separate matter and must **not** land in `~/Downloads`: screenshots stay in
`manual-assets/<slug>/` and per-section drafts in `manual-drafts/<slug>/`. Only the finished
deliverable is copied out. If a file of the same name already exists there, ask before overwriting —
never silently replace a document the user may still need.

### Step 8 — รีวิว 5 ชั้น + delivery gate (mandatory — the hard stop before delivery)

**Read `references/review.md` and follow it exactly.** Review the **built file from Step 7**, not the
draft in conversation — most defects (font fallback, dropped images, stale TOC, คำพราก) are born in
the conversion, so reviewing the draft proves nothing.

The five layers, each decided against the **Step 2 confirmation table** and each needing evidence:

| ชั้น | มุมมอง | ตัดสินว่า |
|---|---|---|
| 1 | ตรงตามที่ยืนยัน | scope, การแบ่งเล่ม (Q9), ภาษา, ฟอนต์, format, **โหมดวงแดง — มี/ไม่มี ตามที่สั่ง** |
| 2 | ทุกอย่างมีที่มา | ทุกขั้นตอนสาวถึงระบบจริง+แหล่งของผู้ใช้; บทที่ไม่มีแหล่ง = ตัดทิ้ง ไม่ใช่แต่งเพิ่ม |
| 3 | ภาพ | ของจริง, เต็มจอ, **เลขในวงตรงขั้นตอน 1:1 — พิสูจน์ด้วย `verify-annotations.py`**, ไม่มีเคอร์เซอร์/ขอบเรือง, ปิดชื่อคน |
| 4 | ตัวหนังสือและตัวเลข | เลขข้อ+TOC ตรง, ไม่มีคำผิด, **ไม่มีคำพราก**, คำศัพท์ล็อกเดียว, โทนถูก |
| 5 | รูปเล่ม | ปก + header + footer (`PAGE` field) + TOC field + ฟอนต์ ตามฟอร์แมตที่ผู้ใช้กำหนด |

Run the mechanical half first — it settles what a regex and the pixels can settle, so judgement goes
to the rest. **Both scripts, same resolver, same Bash call** (shell state does not survive between
calls, and the run's cwd is the user's project — a bare relative path finds neither script):

```bash
MM=$(ls -d ~/.claude/plugins/cache/*/manual-maker/*/skills/manual-maker 2>/dev/null | sort -V | tail -1); [ -n "$MM" ] || MM=~/.claude/skills/manual-maker
/usr/bin/python3 "$MM/scripts/verify-doc.py" <ไฟล์.docx> --terms "<คำล็อก,คั่นด้วยจุลภาค>" --annotations required|none
/usr/bin/python3 "$MM/scripts/verify-annotations.py" manual-assets/<slug>/ --assets manual-assets/<slug>/ --docx <ไฟล์.docx>
```

`verify-annotations.py` is the **evidence for layer 3's "เลขในวงตรงขั้นตอน 1:1"**, which used to be
prose a human was expected to eyeball — and it got through: a delivered manual had ② on step 3's
control, ④ on an alternative path that was not a numbered step, and ⑤ on two different figures. It
reads `annotations.json` (written during annotation, see `references/screenshots.md`) and checks it
against the **actual pixels**, so a manifest that lies about what was drawn fails — and it compares
each circle's `label` against the control its own `step_text` names in quotes, which is what catches
the ②-on-step-3's-button case. **Skip it only when the confirmed โหมดภาพ is `none`** — then what must
be proved is that there are no circles at all, which is layer 1.

**Exit 1 on either = ห้ามส่ง.** But **passing the scripts is not passing the review.** What still
needs a human on layer 3 is narrower than before but not empty: **whether the control the step names
is the right one to click at all** (a step that says `คลิกปุ่ม “ยกเลิก”` where it should say
`“บันทึก”`, with the circle honestly on ยกเลิก, passes every check — everything is consistent, the
*step* is wrong), whether the circle covers the right pixels on screen, and the ~1-in-5 steps that
name no quoted control and are therefore skipped. Content matching the real system and layout
matching the ต้นแบบ stay human-judged too.

Print the 5-layer verdict table (format in `review.md`) to the user **every time**, including the
failing rounds. Deliver only on **5/5**. If a layer cannot be verified, it is **ไม่ผ่าน** — say so and
ask; never assume it through.

### Step 9 — ส่งมอบ / publish (only after 5/5)

**Entry condition: Step 8 returned 5/5.** Publishing is outward-facing and hard to walk back — a
Confluence page posted from a manual that fails review has already reached its readers.

**Close the progress marker once the deliverable is handed over** —
`rm -f ~/.manual-maker/state/run.active ~/.manual-maker/state/last-tick` — so the 10-minute progress
reminder stops.

| Format | How |
|--------|-----|
| Confluence | Atlassian MCP `createConfluencePage` / `updateConfluencePage` under the space+parent from intake. **Confirm target before posting.** ⚠️ The MCP publishes the **page body/structure only — it does not upload screenshot files.** Embed images via a pre-hosted URL, or attach them to the page manually; for **image-heavy** manuals (the usual case) prefer **docx/PDF**. |
| PDF | `pdf` skill |
| docx | `docx` skill — **and `references/docx-build.md`**: if there is a base template, edit its OOXML (`unzip → word/document.xml → zip`); docx-js cannot open an existing file. Font **TH SarabunPSK**, body 16 pt / headings 18 pt bold, with the **`w:cs`** slot set. |
| Web page | `web-artifacts-builder` skill |

For every file-based format, the finished document sits in **`~/Downloads/`** itself (Step 7) — report
the deliverable back as that exact path, one line per volume, so the user can open it without hunting
through folders.

## Composition Note

Composes first-party skills via the Skill tool — no third-party content is copied into this repo, so it stays public-safe and benefits from upstream updates.

## Safety

- **Credentials** are used only in-session to reach the screens — never written into the manual, repo, logs, or any file, and never printed back.
- Screenshots navigate only user-provided URLs; never arbitrary or emailed links.
- Confluence/web publishing is outward-facing — confirm the target before posting.
- All tooling is first-party / already installed — no paid services.
