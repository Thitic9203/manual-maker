# Confluence page conventions — preserve structure, swap values

This is the shape-and-tone contract for every page this skill writes. The overriding rule: **the
page's existing structure and format are kept exactly; only placeholder values change.**

## 1. Structure is inherited, not invented

- Read the target page in `html` first. Its headings, tables (columns + order), panels
  (`data-type="panel-*"`), expands, status lozenges, and macros are the template — **reproduce them
  unchanged**.
- Replace **only** the placeholder *values*: mock cell text (FEAT01, Module A, สมมติ), and
  `<span data-type="placeholder">…</span>` nodes. A placeholder node is replaced with the real value,
  or removed if genuinely not applicable — it is **never left in the published page**.
- Do not add columns, sections, panels, or macros the template did not have. Do not drop ones it had.
- Preserve the ⚠️ intent of the page while removing the "MOCK" warning panel itself once real content
  is in (the warning was scaffold-only).

## 2. Subsystem dimension — one convention across the whole space

- Every data table carries a **`Subsystem`** column; values are exactly **OLS / ELMS / CBMS / EvMS**
  (the locked forms — never "Open Learning", "อีแอลเอ็มเอส", etc.).
- Tag each page with Confluence **labels** for the subsystems it covers: `ols`, `elms`, `cbms`, `evms`.
- One row per (item × subsystem) where a value differs by subsystem; a single row tagged with multiple
  subsystems only when the value is genuinely shared.

## 3. Terminology — one locked term per concept

- The **`Wording Guideline` page in the space is the term source.** Use its exact word everywhere; never
  a synonym. If a concept has no locked term yet → **ask** the user which word, then add it to the
  Wording Guideline page (do not silently coin one).
- Locked terms are passed to `verify-confluence.py --terms` so a split/inconsistent term fails the review.

## 4. Tone & language

- **Formal, professional, human** — never machine-translated stiffness.
- **No first/second-person pronouns** (ผม / ฉัน / เรา / คุณ / ท่าน) — use the imperative or the role term.
- **No sentence-final particles** (ครับ / ค่ะ / นะ).
- Meeting notes / Minutes / Sprint Review may attribute statements to a named participant (from the
  real record) — that is not a pronoun and is allowed; the particle rule still holds.

## 5. Numbering & tables

- Continuous decimal outline for sections (`1`, `1.1`, `1.1.1`) — no gaps or duplicates.
- Index/parent pages that list child instances (PRD, BRD, Meeting notes) keep the index table in sync
  with the child pages that actually exist — every listed row links to a real page, every child page is
  listed.

## 6. Diagrams

- Diagram slots are filled per `diagrams.md`: **Confluence-rendered Mermaid from the real source**,
  proven to render at review layer 5. Never a screenshot of an invented diagram, never a raw code block
  left unrendered, never a `placeholder` node shipped.

## 7. Storage format specifics

- Write with `contentFormat: html` (round-trip safe: panels, macros, tables, local IDs preserved).
- Thai text needs no special font handling in Confluence (unlike docx), but **do not split a locked
  term across a `<br>` or element boundary** — `verify-confluence.py` flags a locked term broken by
  whitespace/markup (the Confluence analogue of คำพราก).
- Never embed a credential, token, or real minor's identifier in page content.

## Final page checklist (per page, before it counts as done)

- [ ] โครง/คอลัมน์/panel/macro ตรงกับ template เดิม ครบ ไม่ขาดไม่เกิน
- [ ] ไม่มี placeholder/mock token เหลือ (FEAT01, Module A, สมมติ, mock, TBD, `data-type="placeholder"`)
- [ ] ทุกค่าสาวกลับไปถึงแหล่งใน `source-map.md` ได้
- [ ] คอลัมน์ `Subsystem` + label ครบตาม scope
- [ ] locked term ตรง Wording Guideline ทั้งหน้า ไม่มีคำพ้องปน
- [ ] โทน: ไม่มีสรรพนาม 1/2, ไม่มีคำลงท้าย
- [ ] diagram (ถ้ามี) render เป็นภาพจริงบนหน้า publish
- [ ] index/parent ↔ child pages ตรงกัน ลิงก์ไม่หลุด
