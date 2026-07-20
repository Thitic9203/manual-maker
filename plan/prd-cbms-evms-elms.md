# แผนการอัปเดต PRD บน Confluence — CBMS · EvMS · ELMS

**สถานะ:** อนุมัติแผนแล้ว · ยังไม่เริ่มเขียน Confluence
**วันที่:** 2026-07-20
**Space เป้าหมาย:** `PLUT` (SkillLane Pluton) · cloudId `dfc2cd04-b24b-48cf-81a1-4a3e0ed7569f`

---

## Context

Space `PLUT` มี PRD ครบแล้วเฉพาะระบบ **OLS** — หน้าดัชนี
[[OLS] PRD — Product Requirement Documents](https://skilllane.atlassian.net/wiki/spaces/PLUT/pages/3709763630)
พร้อมหน้าย่อยราย Epic 15 หน้า อีก 3 ระบบ (CBMS, EvMS, ELMS) ยังไม่มี PRD

งานนี้คือขยาย PRD ให้ครบทั้ง 3 ระบบ โดย **ฟอแมตและการจัดวางระดับเดียวกับ OLS**
และ **ขอบเขต Epic ยึดจากบอร์ด** https://mica-phase2-dashboard.pages.dev/ → tab **Epic Breakdown**
(บอร์ดกรองเฉพาะ ticket ที่มีทั้ง Epic และ Sprint) — ไม่เพิ่ม Epic นอกบอร์ด

ผลลัพธ์ที่ต้องการ: PRD ที่ทีมใช้อ้างอิงได้จริง ทุกค่ามีที่มาจาก Jira ไม่มีการเดา

---

## 1. ขอบเขต — ระบบและ Epic (จาก Epic Breakdown, 20/Jul/2026 11:02 PM)

รวม **18 Epic** ใน 3 ระบบ (OLS 16 Epic = นอกขอบเขต ทำเสร็จแล้ว)
ตัวเลข Tickets คือจำนวน ticket ทั้งหมดบนบอร์ด (รวม Story/Bug/Task) — **จำนวน Use Case จะไม่ตรงกับตัวเลขนี้** (ดู §7)

### 1.1 CBMS — Credit Bank Management System (6 Epic)

| # | Epic Key | ชื่อ Epic | Tickets บนบอร์ด |
|---|---|---|---|
| 1 | MICA2-648 | School Credit Bank Activation | 11 |
| 2 | MICA2-649 | Credit Bank Curriculum Management | 9 |
| 3 | MICA2-650 | Credit Bank Course Management | 27 |
| 4 | MICA2-651 | Credit Transfer (Learner) | 11 |
| 5 | MICA2-652 | Credit Transfer (Staff) | 6 |
| 6 | MICA2-653 | My Credit | 8 |
| | | **รวม** | **72** |

### 1.2 EvMS — Evaluation Management System (7 Epic)

| # | Epic Key | ชื่อ Epic | Tickets บนบอร์ด |
|---|---|---|---|
| 1 | MICA2-630 | Exam Bank / Question Bank | 78 |
| 2 | MICA2-631 | Exam Timetable | 41 |
| 3 | MICA2-632 | Exam Grading | 34 |
| 4 | MICA2-633 | Exam Report and Evaluation | 35 |
| 5 | MICA2-636 | Exam Room | 20 |
| 6 | MICA2-634 | Exam Room Management | 0 (Epic Without Tickets) |
| 7 | MICA2-635 | Create Exam (All) | 0 (Epic Without Tickets) |
| | | **รวม** | **208** |

### 1.3 ELMS — Extended Learning Management System (5 Epic)

| # | Epic Key | ชื่อ Epic | Tickets บนบอร์ด |
|---|---|---|---|
| 1 | MICA2-625 | AI Integration | 4 |
| 2 | MICA2-626 | Google Docs | 55 |
| 3 | MICA2-627 | Google Meet / VDO Conference | 58 |
| 4 | MICA2-628 | Google Drive | 28 |
| 5 | MICA2-629 | Google Connect | 4 |
| | | **รวม** | **149** |

> Epic ทั้ง 18 อยู่ใน Jira board เดียวกัน = **MICA2 Board** (ELMS, CBMS, EvMS)
> "Tickets Without Epic (8)" บนบอร์ดเป็นของ OLS ทั้งหมด → นอกขอบเขต

---

## 2. โครงสร้างหน้า (ยึดตาม OLS)

```
PLUT space
├── [CBMS] PRD — Product Requirement Documents      ← หน้าดัชนี (สร้างใหม่)
│   └── … 6 หน้าย่อย
├── [EvMS] PRD — Product Requirement Documents      ← หน้าดัชนี (สร้างใหม่)
│   └── … 7 หน้าย่อย
└── [ELMS] PRD — Product Requirement Documents      ← หน้าดัชนี (สร้างใหม่)
    └── … 5 หน้าย่อย
```

รวม **3 หน้าดัชนี + 18 หน้าย่อย = 21 หน้า**

### 2.1 หน้าดัชนี — โครงตามหน้า `3709763630`

- **ขอบเขต:** ย่อหน้าเปิด ระบุว่า 1 หน้าย่อย = 1 Epic, อ้างอิงจาก Jira board MICA2
- **หลักการจัดทำ** (คงกติกาเดิมของ OLS ทั้งหมด):
  - 1 Story ใน Jira = 1 Use Case · Story ที่เป็นส่วนปรับปรุงเพิ่มเติมนับเป็น Use Case แยก
  - Bug ไม่นับเป็น Use Case
  - ค่าที่ Jira ไม่ได้ระบุ → กำกับ **"รอข้อมูล"** ไม่ประมาณค่าแทน
  - ส่วนภาพรวม / กลุ่มผู้ใช้ / ขอบเขต เป็นการสังเคราะห์จาก Story และรอ BA ยืนยัน
- **ดัชนีหน้าย่อย:** ตาราง **6 คอลัมน์ เรียงตามนี้เท่านั้น**

  | Subsystem | Epic | ชื่อ Epic | หน้า PRD | จำนวน Use Case | การตรวจแหล่งข้อมูล |
  |---|---|---|---|---|---|

  - `หน้า PRD` = ลิงก์ไปหน้าย่อย ข้อความลิงก์ = ชื่อหน้าเต็ม
  - `การตรวจแหล่งข้อมูล` = **status macro สีเขียว** ข้อความแบบเดียวกับ OLS
    (`ตรวจแล้ว ไม่พบจุดแก้` / `ตรวจแล้ว แก้ N จุด` / `ตรวจรายใบขณะจัดทำ`) — ห้ามคิดข้อความใหม่
- **บรรทัดสรุปท้ายตาราง:** `รวม N Epic · M Use Case` (รูปแบบเดียวกับ OLS)
- **ท้ายหน้า — `## ข้อจำกัดที่ยังพิสูจน์ไม่ได้`:** ใส่ `panel-warning` / `panel-note` เฉพาะเมื่อ**มีข้อจำกัดจริง**
  (เช่น ดึง Story ไม่ครบ, ยังไม่ได้ตรวจการแสดงผล) — ไม่มีข้อจำกัด = ไม่ต้องมีหัวข้อนี้ ห้ามใส่ panel เปล่า

### 2.2 หน้าย่อยราย Epic — โครงตามหน้า `3711270942` ([OLS-1] Authentication)

ชื่อหน้า: `[<SYS>] PRD - [<EPIC-KEY>] <Epic Name>`

1. **Page Properties / ข้อมูลเอกสาร** — ตาราง 4 แถว: Epic Jira Link (smartlink) · Theme · Status (status macro) · Last Updated (date macro)
2. **1. ภาพรวมและวัตถุประสงค์** — พร้อม panel เตือน *"ร่างจาก Jira Story — รอ BA ยืนยัน"*
   - 1.1 ภาพรวม (Overview)
   - 1.2 ปัญหาหรือความท้าทาย (Problem Statement)
   - 1.3 วัตถุประสงค์ (Objectives)
3. **2. กลุ่มผู้ใช้งานเป้าหมาย (Target Personas)** — ตาราง: ผู้ใช้ · ช่องทางเข้าใช้งาน · บทบาทในระบบ · **Subsystem**
4. **3. ขอบเขตการทำงาน** — 3.1 In-Scope · 3.2 Out-of-Scope
5. **4. ความต้องการทางฟังก์ชัน**
   - 4.2 ตารางสรุป Use Case: `UC | ชื่อ | Actor | Jira | Subsystem`
   - ตารางรายละเอียด 1 ตาราง/UC หัวข้อ `Use Case No. UC-n | <ชื่ออังกฤษ>` แถว:
     ชื่อการใช้งาน (Use Case) · ผู้ใช้งาน (Actor) · รายละเอียดการทำงาน (Description) ·
     Business Rules / เงื่อนไข · Edge Case · Error Messages & Handling ·
     Jira Ticket Link · SRS Functional Requirement ID · Business Flow

**คอลัมน์ `Subsystem`** ใส่ค่า `CBMS` / `EvMS` / `ELMS` ตามระบบ + ติด **label** หน้า: `cbms` / `evms` / `elms`
(คงคอนเวนชันข้าม space เดิม)

### 2.3 ตรึงฟอแมต — ใช้ของ OLS ตรงตัว ห้ามแต่งเอง

**ฟอแมตทั้งหมดของหน้า PRD และตาราง UC ตรึงตามหน้า OLS ห้ามดัดแปลง**
ต้นแบบที่ยึด: หน้าดัชนี `3709763630` · หน้าย่อย `3711270942`

**วิธีทำให้ตรงจริง (ไม่ใช่ทำจากความจำ):**

1. ก่อนสร้างหน้าแรกของทุกระบบ → **ดึงหน้าต้นแบบทั้งสองด้วย `contentFormat: html`** เก็บเป็น skeleton
2. สร้างหน้าใหม่โดย **คัดโครงจาก skeleton แล้วเปลี่ยนเฉพาะ "ค่า"** — ไม่รื้อโครง
3. ทุกครั้งที่ไม่แน่ใจว่าฟอแมตไหนถูก → **เปิดหน้าต้นแบบดู ห้ามเดา**

**ห้าม (ต่อให้คิดว่าดีกว่า):**

- ห้ามเพิ่ม / ลบ / สลับลำดับ หัวข้อ · หัวข้อย่อย · แถวในตาราง UC · คอลัมน์ในทุกตาราง
- ห้ามเปลี่ยนคำหัวข้อ แม้แต่คำเดียว — ใช้คำไทย/อังกฤษ วงเล็บ และตัวหนา แบบเดียวกับ OLS เป๊ะ
- ห้ามเปลี่ยนรูปแบบเลข UC (`UC-1`, `UC-2`, …) และหัวตารางรายละเอียด
  (`Use Case No. UC-n  |  <ชื่ออังกฤษ>`)
- ห้ามเพิ่ม panel / emoji / สีสัน / ตารางสรุป / บทนำ / บทส่งท้าย ที่ OLS ไม่มี
- ห้าม "ปรับปรุงภาษาให้สวยขึ้น" — โทนและสำนวนตาม OLS
- **เลข `4.2` ที่ไม่มี `4.1`** เป็นของต้นแบบ → คงไว้ ห้าม renumber ให้ "ถูกต้อง"

**ห้ามมโน info — เข้มกว่าฟอแมต:**

- ทุกค่าในหน้าต้องชี้กลับไปที่ Story ใน Jira ได้ (summary / description / AC / Exceptional Case / Reference UI)
- ไม่มีที่มา → **"รอข้อมูล"** เท่านั้น · ห้ามเติม Business Rule, Edge Case, Error Message,
  Actor, Persona, In/Out-of-Scope, Objective ที่ Jira ไม่ได้เขียนไว้
- ห้ามอนุมานจากระบบอื่น (เช่น ยก pattern ของ OLS มาใส่ CBMS) — คนละระบบ คนละ Story
- ห้ามรวบหลาย Story เป็น UC เดียว และห้ามแตก Story เดียวเป็นหลาย UC
- ส่วนที่ 1–3 เป็นการสังเคราะห์ → ต้องติด panel *"ร่างจาก Jira Story — รอ BA ยืนยัน"* ทุกหน้า
- ข้อจำกัดที่พิสูจน์ไม่ได้ (ดึง Story ไม่ครบ ฯลฯ) → **เขียนไว้ใน panel ตรงๆ** ห้ามกลบ

---

## 3. ขั้นตอนทำงาน

### Step 0 — Preflight (บล็อก)

- ยืนยันสิทธิ์ `write:page:confluence` และมี tool `createConfluencePage` / `updateConfluencePage` จริง
- ถ้าไม่มี → **หยุด** แจ้ง user พร้อมวิธีเปิดสิทธิ์ ไม่ปลอมการเขียน

### Step 1 — ดึง Story จาก Jira (ต่อ Epic)

- JQL: `parent = <EPIC-KEY> AND issuetype = Story AND (sprint in (openSprints(), futureSprints()) OR status = Done)`
- **ตัด Story ที่อยู่ใน Backlog ออก** — Backlog = ไม่อยู่ใน Sprint active/future และยังไม่ Done
  (งานที่ไม่ทำ ไม่ต้องมี Use Case) · เกณฑ์นี้ตรงกับเกณฑ์ที่บอร์ด Epic Breakdown ใช้
- field ที่ดึง: summary, description, Acceptance Criteria, Exceptional Case, Reference UI, status
- **ตัด Bug ออก** · Task / Sub-task ไม่นับเป็น UC
- Story ที่ไม่มี description / AC → UC ยังอยู่ แต่ช่องที่ไม่มีข้อมูลใส่ **"รอข้อมูล"**
- **Epic ที่ไม่มี Story เลย** (MICA2-634, MICA2-635) → สร้างหน้าตามโครงเดิม ใส่ "รอข้อมูล" ทุกช่อง
  ส่วนที่ 4 ระบุว่ายังไม่มี Story ใน Jira — ไม่ข้าม เพื่อให้ index ครบตามบอร์ด

### Step 2 — ร่างเนื้อหา

- ส่วน 1–3 = สังเคราะห์จาก Story ของ Epic นั้น (ติด panel รอ BA ยืนยัน)
- ส่วน 4 = map 1 Story → 1 UC ตรงตัว ไม่รวบ ไม่แตก
- ภาษาเดียวกับ OLS: ไทยทางการ ไม่มีสรรพนามบุรุษที่ 1/2 ไม่มีคำลงท้าย

### Step 3 — สร้างหน้า

- **ดึงหน้าต้นแบบ OLS (`3709763630`, `3711270942`) เป็น `html` ก่อนเสมอ** ใช้เป็น skeleton (ดู §2.3)
- `contentFormat: html` (round-trip safe — panel / macro / table / local ID ไม่หาย)
- สร้างหน้าดัชนีก่อน → สร้างหน้าย่อย → กลับมาเติมตารางดัชนีพร้อมลิงก์จริง + บรรทัด `รวม N Epic · M Use Case`
- ลำดับ: **CBMS (6) → EvMS (7) → ELMS (5)** ทำทีละระบบ ให้ผ่านรีวิวก่อนขึ้นระบบถัดไป

### Step 4 — รีวิว 5 ชั้น ก่อน publish รอบสุดท้าย

| ชั้น | ตรวจอะไร |
|---|---|
| 1 | ตรงตามขอบเขตที่ยืนยัน — 18 Epic ตรงตาราง §1 ไม่ขาดไม่เกิน · ไม่มี Story จาก Backlog หลุดเข้ามา |
| 2 | **ทุกค่ามีที่มาจาก Jira** — ไล่ทีละช่อง ชี้ได้ว่ามาจาก Story ใบไหน ฟิลด์ไหน · ไม่มีค่าที่เดา · ไม่มี placeholder เหลือ |
| 3 | **โครง / ฟอแมตตรงกับ OLS เป๊ะ** — เทียบ §2.3 checklist ด้านล่าง |
| 4 | ศัพท์ / ตัวเลข / คำพราก — locked term ไม่ถูกตัดด้วย whitespace หรือ tag |
| 5 | Render บนหน้าที่ publish จริง — macro / ตาราง / smartlink แสดงผลถูก |

**ตรวจไม่ได้ = ไม่ผ่าน** · FAIL 1 ชั้น → แก้แล้วรีวิวใหม่ทั้ง 5 ชั้น

#### Checklist ชั้น 2 — ห้ามมโน (ต่อหน้า)

- [ ] ทุกแถวในตาราง UC ชี้ Story ได้ 1 ใบ — ไม่มี UC ที่ไม่มี Jira link
- [ ] ทุกช่องที่ Jira ไม่มีข้อมูล = `"รอข้อมูล"` ไม่ใช่ข้อความที่แต่งขึ้น
- [ ] Business Rules / Edge Case / Error Message ทุกข้อ หาต้นทางในใบ Story เจอ
- [ ] Persona / In-Scope / Out-of-Scope สังเคราะห์จาก Story ของ Epic นี้เท่านั้น ไม่ยืมจาก OLS
- [ ] จำนวน UC = จำนวน Story ที่ผ่านเกณฑ์ ไม่รวบ ไม่แตก

#### Checklist ชั้น 3 — ฟอแมตตรงต้นแบบ (ต่อหน้า)

- [ ] ชื่อหน้า `[<SYS>] PRD - [<EPIC-KEY>] <Epic Name>`
- [ ] Page Properties 4 แถว ชื่อแถวและลำดับตรงต้นแบบ
- [ ] หัวข้อครบและเรียงตรง: 1 / 1.1 / 1.2 / 1.3 / 2 / 3 / 3.1 / 3.2 / 4 / 4.2 (คง `4.2` ที่ไม่มี `4.1`)
- [ ] คำหัวข้อตรงตัวอักษร รวมวงเล็บอังกฤษและตัวหนา
- [ ] ตาราง 4.2 มี 5 คอลัมน์: `UC | ชื่อ | Actor | Jira | Subsystem`
- [ ] ตารางรายละเอียด UC มี 9 แถว ชื่อแถวและลำดับตรงต้นแบบ
- [ ] หัวตาราง `Use Case No. UC-n  |  <ชื่ออังกฤษ>`
- [ ] ไม่มีหัวข้อ / panel / ตาราง / emoji ที่ต้นแบบไม่มี
- [ ] หน้าดัชนี: ตาราง 6 คอลัมน์ + บรรทัด `รวม N Epic · M Use Case` + label ระบบ

---

## 4. กติกาที่ห้ามผ่อน

- **ห้ามมโน** — ไม่มีข้อมูลใน Jira → `"รอข้อมูล"` เท่านั้น ห้ามเดา Business Rule / Error Message / Actor
- **ห้ามแต่งฟอแมตเอง** — ยึดต้นแบบ OLS ตาม §2.3 ทุกกรณี ไม่แน่ใจ = เปิดหน้าต้นแบบดู
- **ห้ามเกินขอบเขต** — เฉพาะ 18 Epic ใน §1 ห้ามเพิ่ม Epic / โมดูลเอง
- **ยืนยันก่อนเขียนจริง** — สรุปหน้าที่จะสร้างทั้งหมดให้ user เห็น แล้วรอ "go" ก่อน publish หน้าแรก
- **ไม่มี credential / ข้อมูลระบุตัวบุคคล** ในหน้า PRD

---

## 5. Verification

| ตรวจอะไร | วิธี |
|---|---|
| Epic ครบ 18 | นับตาราง §1 เทียบ Epic Breakdown ทีละ card |
| Epic Key ถูก | ทุก key เปิด `https://skilllane.atlassian.net/browse/<KEY>` ได้จริง (ตอน Step 1) |
| ฟอแมตตรง OLS | เทียบหัวข้อหน้าใหม่ vs หน้า `3711270942` ทีละบรรทัด |
| ไม่มีค่าที่เดา | ทุกช่องที่ไม่มีที่มาต้องเป็น "รอข้อมูล" ตรวจด้วยการไล่หา placeholder ที่เหลือ |
| Render ถูก | เปิดหน้าที่ publish แล้วดู macro / smartlink / ตาราง แสดงผลจริง |

---

## 6. Reference

| ของ | ที่อยู่ |
|---|---|
| ต้นแบบหน้าดัชนี | https://skilllane.atlassian.net/wiki/spaces/PLUT/pages/3709763630 |
| ต้นแบบหน้าย่อย | https://skilllane.atlassian.net/wiki/spaces/PLUT/pages/3711270942 |
| แหล่งขอบเขต Epic | https://mica-phase2-dashboard.pages.dev/ → tab Epic Breakdown |
| Jira board | MICA2 Board (ELMS, CBMS, EvMS) |

---

## 7. ข้อตัดสินใจที่ยืนยันแล้ว

| ประเด็น | สรุป |
|---|---|
| ขอบเขต Story | Story ใต้ Epic ที่ **อยู่ใน Sprint active/future หรือ Done** — **ตัด Backlog ออกทั้งหมด** เพราะเป็นงานที่ไม่ทำ |
| Epic ที่ไม่มี ticket | **สร้างหน้า** ใส่ "รอข้อมูล" — EvMS ครบ 7 หน้าตามบอร์ด |
| จำนวน UC vs ตัวเลข §1 | ยัง**น้อยกว่า** §1 — เกณฑ์ Sprint ตรงกันแล้ว แต่ §1 รวม Bug/Task ซึ่งไม่นับเป็น UC |
