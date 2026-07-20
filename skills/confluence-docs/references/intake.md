# Intake Questions — confluence-docs

Ask these **one at a time**, in order. Where an answer has a **bold default**, offer it. Where it says
*(ต้องถาม — no default)*, **never assume** — keep asking until the user gives an explicit, clear answer.

**How to ask:** พูดกับผู้ใช้เป็น **ภาษาไทยที่เป็นทางการ สุภาพ มืออาชีพ** — สะกดถูกต้อง ถามทีละข้อ ไม่รวบหลายคำถามในครั้งเดียว
หลีกเลี่ยงคำลงท้าย (ครับ/ค่ะ) และสรรพนามที่ไม่จำเป็น กระชับ ชัดเจน.

## Golden rules for this skill

- **ห้ามมโน / ห้ามคิดเอง / ห้ามโกหก.** Missing, vague, or unsure → STOP and ask again. Never guess a
  feature name, number, term, owner, status, schema column, or diagram.
- **ห้ามทำเกินขอบเขต.** Only the one doc-type (and children) confirmed this run.
- **ยืนยันก่อนเริ่มเสมอ.** After intake, summarize everything and get an explicit "go" before reading
  sources or writing anything (Confirmation Gate at the end).

## Sequencing — ถามทีละข้อเฉพาะข้อที่ต้องถาม; ข้อที่มี default รวบเป็นชุดเดียว

- **ถามทีละข้อ** — ข้อ *(ต้องถาม — no default)*: **1, 4, 5**. ห้ามรวบ ห้ามข้าม ห้ามเดา.
- **รวบเป็นชุดเดียว** — ข้อที่มี bold default: **2, 3, 6, 7, 8**. แสดง default ทุกข้อในตารางเดียว แล้วถามครั้งเดียว
  ว่า **"ค่าเริ่มต้นเหล่านี้ใช้ได้ไหม หรือต้องการแก้ข้อใด"**.
- **9 (สิทธิ์เขียน)** และ **10 (Confirmation Gate)** ไม่ใช่คำถาม — เป็น preflight อัตโนมัติ และ gate ท้ายสุด.

## A. What to work on this run

1. **Doc-type ไหน** ในรอบนี้ — ระบุ 1 doc-type จากชุด scaffold (PRD / High Level Business Requirements /
   Technical Document / Enterprise Architecture / Master Data / Jira Board & Ticket Template /
   Troubleshooting article / Knowledge Sharing / Meeting notes / QA Documents / AI & Data Documentation /
   Integration Documents / Sprint Review / DevOps Documents / Deliverable Checklist / User Manual /
   Risk & Issue Logs / Wording Guideline / Open Questions / Pre-grooming …). แสดงรายการให้เลือก.
   *(ต้องถาม — no default)*

2. **หน้าปลายทาง** — page id / URL ของหน้า mock ที่จะ update. **Default: auto-resolve จากชื่อ doc-type
   ใต้ tree Mica (space `PLUT`, cloudId `dfc2cd04-b24b-48cf-81a1-4a3e0ed7569f`, root `3693641732`)** —
   แสดง id ที่ resolve ได้ให้ผู้ใช้ยืนยัน ไม่เขียนโดยไม่ยืนยัน. ถ้าผู้ใช้ระบุ space/หน้าอื่น ใช้ตามนั้น.

3. **subsystem scope** — รอบนี้ครอบ subsystem ใด. **Default: ทั้ง 4 (OLS / ELMS / CBMS / EvMS)** —
   กำหนดว่าแถวไหนในตารางมี และ label ใดที่ติดหน้า.

## B. Source material — ทุกค่าต้องมีที่มา (*ห้ามมโน*)

4. **แหล่งข้อมูล authoritative ของ doc-type นี้** — โชว์แหล่งที่ `source-map.md` คาดไว้สำหรับ doc-type ที่เลือก
   (เช่น PRD/Pre-grooming ← Jira filter, API Doc ← OpenAPI/repo, Master Data / Data Dictionary ← DB schema,
   Meeting notes ← โน้ตจริง). ขอ link/ไฟล์/JQL ให้ครบ. ทุกค่าที่แทน placeholder ต้องสาวกลับไปถึงแหล่งนี้ได้.
   *(ต้องถาม — ขอ link/ไฟล์ หรือคำว่า "ไม่มี"; ถ้าไม่มี = หยุด doc-type นี้ ไม่เติมด้วยการเดา)*
   > NDLP Jira filters: OLS `21689` · ELMS `21690` · CBMS `21691` · EvMS `21692`.

5. **แหล่งไดอะแกรม** — เฉพาะ doc-type ที่มี diagram (EA / Sequence / ER / Data Dictionary). ไดอะแกรมจริง
   มาจากไหน (repo path ของ schema / DB / spec / flow)? *(ต้องถามถ้า doc-type มี diagram — ไม่มีแหล่ง = เว้นช่อง
   นั้นเป็น blocker ไม่วาดไดอะแกรมมโน; ดู `diagrams.md`)* ถ้า doc-type ไม่มี diagram ให้ข้ามข้อนี้.

## C. Write behaviour & style — bold defaults

6. **update ทับ / สร้างหน้าลูกเพิ่ม** — **Default: update in-place หน้า mock; สำหรับ doc-type ที่มีหลาย
   instance (PRD features, Meeting notes, BRD per module) update หน้า index ในที่เดิม แล้วสร้างหน้าลูก 1 หน้า
   ต่อ 1 instance จริง.** ถ้าจะสร้างหน้าลูก ให้ยืนยันรายการ instance ก่อน.

7. **locked terms** — **Default: ใช้ term list จากหน้า `Wording Guideline` ใน space.** ถ้ามี concept ใหม่ที่
   ยังไม่มี term ล็อก → ถามผู้ใช้ว่าจะใช้คำใด แล้วเพิ่มในหน้า Wording Guideline.

8. **ภาษา/โทน** — **Default: ไทย, ทางการ, มืออาชีพ, ไม่ใช้สรรพนามบุรุษ 1/2, ไม่มีคำลงท้าย (ครับ/ค่ะ/นะ)**
   ตาม `template.md`. (Meeting notes / Minutes ใช้สำนวนบันทึกที่ระบุผู้พูดได้ แต่ยังเลี่ยงคำลงท้าย.)

## D. Automatic — not questions

9. **preflight สิทธิ์เขียน** — เช็คอัตโนมัติว่ามี `updateConfluencePage`/`createConfluencePage` + scope
   `write:page:confluence` (ดู Step 0 ใน `SKILL.md`). ไม่มี = หยุด บอกวิธีเปิดสิทธิ์. ผลลง row *สิทธิ์เขียน*
   ของตารางยืนยัน.

## Confirmation Gate — before reading sources or writing anything

Print a summary table of **every** answer:

| Field | Value |
|-------|-------|
| Doc-type | … |
| หน้าปลายทาง (space / cloudId / page id + title) | … |
| subsystem scope + labels | … |
| แหล่งข้อมูล authoritative (link/ไฟล์/JQL) | … |
| แหล่งไดอะแกรม (หรือ "ไม่มี diagram") | … |
| update in-place / สร้างหน้าลูก + รายการ instance | … |
| locked terms (จาก Wording Guideline) | … |
| ภาษา/โทน | … |
| สิทธิ์เขียน (ผล preflight Step 0) | พร้อม / ไม่พร้อม + วิธีเปิด |

Then ask, verbatim: **"ยืนยันข้อมูลทั้งหมดถูกต้อง และเริ่มดำเนินการได้หรือไม่"**

Do **not** proceed until the user replies with an explicit confirmation. If anything is "ไม่แน่ใจ",
resolve it first. Nothing is read from a source and nothing is written before this gate passes.
