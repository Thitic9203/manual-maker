---
description: Drive the full manual-maker pipeline end to end from one command — intake → confirm → sources → screenshots → draft → template → review → export — auto-advancing through every step, pausing only at the mandatory human gates.
argument-hint: ทำคู่มือ <ชื่อระบบ>  |  create a manual for <system>
---

# /manual-maker — build a user handbook from start to finish

The user invoked this command to produce a finished **user handbook** in one shot. Their request:

> $ARGUMENTS

## Your job

Own this from intake to exported deliverable. **Load the `manual-maker` skill using the Skill
tool** — invoke it by name, do not depend on a filesystem path. Once loaded, the skill pulls in
its own references (`references/intake.md`, `references/template.md`); follow its workflow verbatim.

Run **every** step of that skill's workflow, in order, and **auto-continue between steps** — do
not stop to ask "shall I move to the next step?". The user has already said "เดินงานให้จนจบ" (drive
it to the end), so momentum between steps is the default.

**First action:** create the full TodoWrite list so the user sees the whole run up front —
`Intake → Confirm → Ingest sources → [Screenshots → Draft → Template+Quality ขนานต่อหัวข้อย่อย + รีวิวทีละหัวข้อ] → Build file → รีวิว 5 ชั้น → Export/publish`
— then start Step 1 immediately.

If `$ARGUMENTS` already names the system (e.g. "ทำคู่มือระบบ CBMS"), seed that as the subject and
skip re-asking for it; otherwise the first intake question establishes it.

## Drive to completion — but never at the cost of correctness

Keep moving on your own through every step **except** the three mandatory human gates below. They
exist because a manual must be **sourced, not invented** — this is the skill's first non-negotiable
rule (ห้ามมโน / ห้ามคิดเอง). Pause only here:

1. **Intake answers** — the system-specific facts (system name, login, target users, modules,
   reference sources, terminology, output format) live only in the user's head. Ask the
   `intake.md` questions **one at a time** — the auto-advance rule above governs moving between
   *steps*, never batching intake questions; ask them one by one even while driving to the end.
   Never assume a default for access, credentials, sources, fonts, or terminology.
   **If this user already documented this system, load their saved profile first**
   (`~/.manual-maker/profiles/`, per the skill's `profile.md`) and ask only what is missing or
   changed — do not re-ask answered questions. Credentials are never stored; always ask fresh.
2. **Confirmation gate** — before any screenshot or drafting, print the intake summary table and
   get an explicit "ยืนยัน / go". Do nothing else until then.
3. **Publish confirmation** — before posting to Confluence or a public web page (outward-facing),
   confirm the exact target (space + parent, or destination).
4. **คำถามจากรีวิวรายหัวข้อ** — Steps 4–6 run 2–3 `manual-section-writer` agents in parallel with one
   `manual-section-reviewer` behind them (`references/parallel.md`). A subagent **cannot talk to the
   user**, so every `BLOCKED` from a writer and every `ASK` from the reviewer — i.e. anything needing
   judgement, and anything the reviewer was unsure about — **comes to the user in chat before a fix is
   chosen**. Never decide on their behalf to keep momentum. A หัวข้อย่อย with an open question is not
   done.

Between those gates, proceed **autonomously**: ingest the given sources, fan the หัวข้อย่อย out to the
writers (capture + annotate + draft per section), review each one the moment it lands, apply
`template.md` and its four quality axes (font & size, numbering, image clarity + annotation,
terminology), assemble the file, run the 5-layer review on it, and export to the chosen format — all
without waiting for a nudge.

If a single fact for a step cannot be sourced from the live system or the user's references →
**stop and ask for just that fact**, then resume. Never paper over a gap with a guess.

## Done when

The manual is exported in the requested format (Confluence / PDF / docx / web), has passed the
Final Review Checklist, and the deliverable — file path or published URL — is reported back to the
user.
