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
- **Two deliberate exceptions to "reproduce unchanged"** (both scaffold-only, like the MOCK panel):
  **(a)** table **column headers are always rewritten to English + bold** — see §5; the column *count
  and order* are still preserved, only the header word changes. **(b)** a standalone page-level
  **`SUBSYSTEM: <X>` badge / lozenge / heading is removed** — see §2.

## 2. Subsystem dimension — one convention across the whole space

- Every data table carries a **`Subsystem`** column; values are exactly **OLS / ELMS / CBMS / EvMS**
  (the locked forms — never "Open Learning", "อีแอลเอ็มเอส", etc.).
- Tag each page with Confluence **labels** for the subsystems it covers: `ols`, `elms`, `cbms`, `evms`.
- One row per (item × subsystem) where a value differs by subsystem; a single row tagged with multiple
  subsystems only when the value is genuinely shared.
- **No page-level `SUBSYSTEM: <X>` badge.** The subsystem is already carried by the **page title**
  (`[EvMS] Master Data`), the Confluence **labels**, and the in-table **`Subsystem` column**. A
  standalone "SUBSYSTEM: EVMS" lozenge/heading at the top of the page is redundant — **do not add it,
  and remove it if the scaffold carries one.** `verify-confluence.py` FAILs on a `SUBSYSTEM: <value>`
  badge; the bare `Subsystem` column header is fine (it has no `: value`).

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
- **Column headers are ALWAYS English and bold — in every table, every time.** Put the header row in
  `<th>` cells and wrap each label in `<strong>` (e.g. `<th><strong>Feature</strong></th>`). If a
  scaffold header is Thai (`ฟีเจอร์`, `เนื้อหา`, `สถานะ`…), **translate it to its English equivalent** —
  the column count and order stay exactly as the template had them; only the header word changes. Use the
  established English term (`Feature`, `Contents`, `Status`, `Entity`, `Column`, `Type`, `Description`,
  `Subsystem`…); if the right English word for a header is genuinely unclear, **ask the user — never
  invent one** (ห้ามมโน). Body/data cells keep their normal language (Thai values stay Thai); this rule is
  headers only. `verify-confluence.py` FAILs a header that still contains Thai or is not bold.

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

- [ ] โครง/คอลัมน์/panel/macro ตรงกับ template เดิม ครบ ไม่ขาดไม่เกิน (จำนวน+ลำดับคอลัมน์คงเดิม)
- [ ] **หัวคอลัมน์ทุกตารางเป็นอังกฤษ + ตัวหนา** (`<th><strong>…</strong></th>`) — หัวไทยแปลเป็นอังกฤษหมด
- [ ] **ไม่มีป้าย `SUBSYSTEM: <X>` ระดับหน้า** (ชื่อหน้า + label + คอลัมน์ Subsystem บอกอยู่แล้ว)
- [ ] ไม่มี placeholder/mock token เหลือ (FEAT01, Module A, สมมติ, mock, TBD, `data-type="placeholder"`)
- [ ] ทุกค่าสาวกลับไปถึงแหล่งใน `source-map.md` ได้
- [ ] คอลัมน์ `Subsystem` + label ครบตาม scope
- [ ] locked term ตรง Wording Guideline ทั้งหน้า ไม่มีคำพ้องปน
- [ ] โทน: ไม่มีสรรพนาม 1/2, ไม่มีคำลงท้าย
- [ ] diagram (ถ้ามี) render เป็นภาพจริงบนหน้า publish
- [ ] index/parent ↔ child pages ตรงกัน ลิงก์ไม่หลุด
