# Plan: ปรับฟอแมตหน้า Confluence ใต้ "Mica Phase 2 (Draft)" — ตารางเป็น full-width ทุกหน้า

**Session:** 2026-07-22 · space `PLUT` · cloudId `dfc2cd04-b24b-48cf-81a1-4a3e0ed7569f` · root page `3693641732` (+ 85 descendants = **86 หน้า**)

## โจทย์จาก user

> ขยายความกว้างให้เป็น Max เสมอ และเนื้อหายังต้องแสดงอย่างเหมาะสมกับหน้าจอด้วย

ตีความที่ยืนยันแล้ว: ทุก `<table>` ในทุกหน้าใต้ root → `data-layout="full-width"` + ลบ `data-width="NNN"` (ค่า px คงที่ที่ตรึงตารางแคบ) — คง `data-colwidth` รายคอลัมน์ไว้ (เป็นสัดส่วน ยืดตามจอ) — ห้ามแตะเนื้อหา/โครงอื่นใดทั้งสิ้น
ข้อจำกัดที่วัดแล้ว: Atlassian MCP **ไม่มี tool ตั้ง page appearance** (`content-appearance-published`) — ทำได้เฉพาะระดับ table ผ่าน body HTML

## Transform contract (สคริปต์อยู่ใน scratchpad ของ session)

Scratchpad: `/private/tmp/claude-502/-Users-thitichaya-GitHub-manual-maker/cecb8a00-ed9e-467e-bf7f-2efbbdbefa3f/scratchpad/`

- `widen.py IN.html > OUT.html` — แก้เฉพาะ opening tag ของ `<table>`: ลบ `data-width`, set `data-layout="full-width"` · พิมพ์ stats ลง stderr
- `verify.py ORIG NEW` — exit 0 เมื่อ: bytes นอก table tag เหมือนเดิมทุก byte + ทุก table เป็น full-width + ไม่เหลือ `data-width`
- **End-to-end proof ต่อหน้า:** update แล้ว re-fetch จาก server → `verify.py raw_ID.html chk_ID.html` — การที่ update call สำเร็จ **ไม่ใช่หลักฐาน**; หลักฐานเดียวคือ verify ผ่านบน body ที่ fetch กลับมาจริง
- Batch lists: `batch_ols.txt` (18) · `batch_evms.txt` (21) · `batch_elms.txt` (21) · `batch_misc.txt` (26) · ผลรายหน้า append ที่ `results/{ols,evms,elms,misc}.txt` รูปแบบ `ID|already-ok/updated/FAIL|tables=N|proof=...`

## สถานะ ณ ตอน commit นี้

1. **รอบแรก (เมื่อคืน) ตายกลางทาง** — ชน session limit; agents รายงานว่าอัปเดตไปแล้วบางหน้า (เช่น 3711959136 v4, 3712090204 v4, 3711795429 v2) **แต่ยังไม่ผ่านการพิสูจน์** → ห้ามเชื่อ ต้อง sweep ใหม่หมด
2. **รอบสอง (ตอนนี้) — verify+fix sweep กำลังรัน:** 3 agents background กำลังไล่ทีละหน้า fetch→widen→(ถ้าเปลี่ยน)update→re-fetch proof: batch **OLS**, **EvMS**, **ELMS**
3. **batch_misc (26 หน้า: root + CBMS 7 + Technical 9 + top-level อื่นๆ) ยังไม่ได้ dispatch** ← งานถัดไปทันที

## สิ่งที่ต้องทำต่อ (เรียงลำดับ)

- [ ] Dispatch agent สำหรับ `batch_misc.txt` (กติกาเดียวกับ 3 ตัวแรก: ห้าม subagent, sequential, ต้องมี re-fetch proof)
- [ ] รอ 4 agents จบ → รวม `results/*.txt` เช็คครบ 86 หน้า (id ใน results ต้อง match ทุก id ใน batch files — หน้าที่หายไป = agent ตายก่อนถึง → ทำเองต่อ)
- [ ] หน้าที่ `FAIL` → แก้เองในเธรดหลักทีละหน้า (fetch→widen→verify→update→re-fetch proof)
- [ ] รีวิว layer 5 (render จริง): เปิดหน้า live ตัวอย่างอย่างน้อย 1 หน้า/subsystem (OLS·CBMS·EvMS·ELMS·Technical) ผ่าน browser — ตารางกว้างเต็ม + เนื้อหาไม่ล้นจอ ตามโจทย์ "แสดงเหมาะสมกับหน้าจอ"
- [ ] สรุปตารางผลรวมรายหน้า (86 แถว) ให้ user + อัปเดตไฟล์นี้ปิดงาน

## บทเรียน / กติกาที่ต้องคงไว้

- **general-purpose agents ชอบ fan-out ซ้อน** — รอบแรกทุกตัวแตก subagent เอง คุมไม่ได้และเผา token จนชน limit → prompt ต้องสั่งห้าม Agent/Task tool ตรงๆ (รอบสองสั่งแล้ว)
- เคยเจอ update response คืน **หน้าอื่น** (PII Documentation 3693674596) ทั้งที่ยิงไปอีก page id → ทุก update ต้องเช็ค id/title ใน response + นับเป็น FAIL ถ้า mismatch
- Server อาจ normalize markup ตอน round-trip (entity encoding ฯลฯ) — verify fail ให้ดู diff ก่อนสรุปว่า corrupt; ถ้าเป็น normalization ล้วน = `ok-normalized`
- หน้าใหญ่สุด ~140KB (EvMS/ELMS "ต่อ N") — ระวัง truncate ตอนถ่าย body
