---
description: Drive the full manual-maker pipeline end to end from one command — intake → confirm → sources → screenshots → draft → template → review → export — auto-advancing through every step, pausing only at the mandatory human gates.
argument-hint: ทำคู่มือ <ชื่อระบบ>  |  create a manual for <system>
---

# /manual-maker — build a user handbook from start to finish

The user invoked this command to produce a finished **user handbook** in one shot. Their request:

> $ARGUMENTS

## Your job

Own this from intake to exported deliverable. **Load and follow the `manual-maker` skill** at
`${CLAUDE_PLUGIN_ROOT}/skills/manual-maker/SKILL.md` together with its references
(`${CLAUDE_PLUGIN_ROOT}/skills/manual-maker/references/intake.md` and `template.md`).

Run **every** step of that skill's workflow, in order, and **auto-continue between steps** — do
not stop to ask "shall I move to the next step?". The user has already said "เดินงานให้จนจบ" (drive
it to the end), so momentum between steps is the default.

**First action:** create the full TodoWrite list so the user sees the whole run up front —
`Intake → Confirm → Ingest sources → Screenshots → Draft → Template+Quality → Final review → Export`
— then start Step 1 immediately.

If `$ARGUMENTS` already names the system (e.g. "ทำคู่มือระบบ CBMS"), seed that as the subject and
skip re-asking for it; otherwise the first intake question establishes it.

## Drive to completion — but never at the cost of correctness

Keep moving on your own through every step **except** the three mandatory human gates below. They
exist because a manual must be **sourced, not invented** — this is the skill's first non-negotiable
rule (ห้ามมโน / ห้ามคิดเอง). Pause only here:

1. **Intake answers** — the system-specific facts (system name, login, target users, modules,
   reference sources, terminology, output format) live only in the user's head. Ask the
   `intake.md` questions **one at a time**. Never assume a default for access, credentials,
   sources, fonts, or terminology.
2. **Confirmation gate** — before any screenshot or drafting, print the intake summary table and
   get an explicit "ยืนยัน / go". Do nothing else until then.
3. **Publish confirmation** — before posting to Confluence or a public web page (outward-facing),
   confirm the exact target (space + parent, or destination).

Between those gates, proceed **autonomously**: ingest the given sources, capture the requested
screenshots, draft section-by-section via the `doc-coauthoring` skill, apply `template.md` and its
four quality axes (font & size, numbering, image clarity + annotation, terminology), run the Final
Review Checklist, and export to the chosen format — all without waiting for a nudge.

If a single fact for a step cannot be sourced from the live system or the user's references →
**stop and ask for just that fact**, then resume. Never paper over a gap with a guess.

## Done when

The manual is exported in the requested format (Confluence / PDF / docx / web), has passed the
Final Review Checklist, and the deliverable — file path or published URL — is reported back to the
user.
