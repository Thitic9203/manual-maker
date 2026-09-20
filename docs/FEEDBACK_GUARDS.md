# The feedback 5-layer guards (v0.25.0+) — the team's five defects can't recur

`references/feedback-guards.md` exists because a real feedback round (Google Doc "Feedback update
Skill") named **five** docx defects, and the team's standing rule is that none may recur — "ยังไม่ครบ
5 ชั้นทุกข้อ = งานยังไม่เสร็จ". Each defect is guarded by the **same 5-layer shape** the repo already
uses for วงห้ามทับตัวอักษร and white-only diagrams: authoring rule → writer self-check → retained
evidence → **mechanical gate (`verify-doc.py`, exit 1)** → human review row, re-review-all-on-fail.

The five, and their mechanical layer (all in `scripts/verify-doc.py`, all proven on **synthetic
fixtures**, not real deliverables — say so):

- **Figure captions (item 1a)** — check **11**, gated by `--captions required`: FAIL when inline images
  (`<wp:inline`) outnumber figure-caption paragraphs (text starts `รูปที่/ภาพที่/แผนภาพที่/Figure`, or a
  `SEQ Figure` field).
- **Table captions (item 1b)** — check **14**, same flag: every *content* table needs `ตารางที่ N`. The
  **step-layout table is excluded** by its header signature (`ภาพประกอบ` together with `ขั้นตอน`/`ลำดับ`),
  so the check never fires on a step table — the one measured false-positive trap here.
- **Thai Distribute (item 3)** — check **12**, gated by `--thai-distribute required`: a *floor* — FAIL only
  when ≥3 long Thai paragraphs exist and `w:val="thaiDistribute"` is absent from **document AND styles**.
  A compliant build always carries it, so it never fires on correct output; it cannot prove every
  paragraph has it (that stays authoring + human).
- **Auto-numbered headings (item 2)** — check **13**, unconditional: FAILs on **double-numbering** — a
  heading with numbering **and** a hand-typed outline number. Numbering is read from the paragraph
  `<w:numPr>` **or the Heading style** (styles.xml), because `docx-build.md` §3.2 recommends binding numPr
  on the style; without the style read, the likeliest real double-number (style auto-number + typed "1.1")
  slips through. Absence of numbering only SKIPs — a base template may dictate its own scheme (ต้นแบบชนะ).
- **Step image in its row (item 4)** — check **15**, unconditional: FAILs only in the total-miss case — a
  doc that has step tables and inline images but **zero images inside any `<w:tc>`** (images dumped outside
  the rows). It cannot know an image is in the *correct* step's row (standalone UI-orientation figures are
  legitimate), so "รูปอยู่แถวที่ถูก" stays writer (owns the whole หัวข้อย่อย) + human, exactly like
  "วงชี้ปุ่มที่ถูกไหม".

**What stays human — do not oversell the scripts.** Checks 11/14 prove captions are *present*, never that
the caption text/number is *right*; 15 proves images are *in cells*, never in the *right* cell; `--terms`
(check 4) catches a locked term split mid-word (คำพราก), never a wrong-synonym choice. Those, plus glossary
correctness, are `review.md` layer-3/4 human rows, and **ตรวจไม่ได้ = ไม่ผ่าน** applies in full. The
locked-term list itself is `references/glossary-ndlp.md` — the NDLP team's **live sheet** is source of
truth (pull it each run; the dated snapshot is offline-only), and a suspected misspelling in it is
**flagged for the user, never auto-fixed** (`template.md` §Terminology) — the same ห้ามมโน stance, and how
the `เรียนรู้` vs `เรียนรู` spelling was resolved (user-confirmed, 2026-08-05).

