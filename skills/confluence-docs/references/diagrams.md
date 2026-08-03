# Diagrams — ใส่ให้ครบ ถูกต้อง render จริง ไม่พัง (ห้ามมโน)

doc-types ที่มีไดอะแกรม: **Enterprise Architecture (EA)**, **Use Case & Sequence Diagram**,
**Data Dictionary & ER Diagram**, และส่วน Architecture/Sequence ใน **Technical Document**.

**ข้อจำกัดที่วัดแล้ว:** Atlassian MCP **อัปโหลดไฟล์แนบ/รูปไม่ได้** — จึงฝัง PNG/รูปไม่ได้. วิธีเดียวที่ใส่
ไดอะแกรมจริงได้โดยไม่อัปโหลดไฟล์ คือ **diagram-as-code ที่ Confluence render เองบนเซิร์ฟเวอร์** (Mermaid /
PlantUML / draw.io). ช่องไดอะแกรมใน scaffold เขียนว่า "draw.io / Mermaid" ไว้แล้ว.

## หลักการ

1. **เนื้อไดอะแกรมต้องมีที่มา (ห้ามมโน).** โครงไดอะแกรม generate **จากแหล่งจริงเท่านั้น**:
   - **ER** ← DB schema จริง (migration / Prisma / SQL DDL) — entity/column/FK มาจาก schema เดียวกับ Data Dictionary
   - **Sequence** ← flow/spec จริง หรือ code path
   - **EA / landscape** ← architecture doc / C4 / diagram source จริง
   ไม่มีแหล่ง → **ช่องไดอะแกรมเป็น blocker** ไม่วาดเดา (ตรวจไม่ได้ = ไม่ผ่าน).

2. **ฝังเป็น Mermaid macro (ตัวเลือกหลัก).** สร้าง diagram-as-code (Mermaid syntax) จากแหล่ง แล้วฝังผ่าน
   **Mermaid macro ของ space** (เขียนใน `contentFormat: html` เป็น macro/extension node). Mermaid ดีสุดเพราะ
   generate จาก schema/flow เป็นข้อความได้ตรงและ diff ได้.

3. **พื้นขาวล้วน ห้ามมีสีอื่นแซม (บังคับทุกไดอะแกรม).** ธีม default ของ Mermaid ใส่สีเอง — actor/node เป็น
   ลาเวนเดอร์, `note` เป็น**เหลือง**, activation bar เป็นสีจาง. **ไม่เอา** — ไดอะแกรมในเอกสารต้องเป็น
   **เส้นดำ/เทาเข้มบนพื้นขาวล้วน** เท่านั้น สม่ำเสมอทุกหน้า. ทำได้โดย**ขึ้นต้นทุกไดอะแกรมด้วย init directive**
   ที่ pin พาเลตต์ขาวล้วน (บรรทัดแรกของ Mermaid source เสมอ ห้ามละ):

   ```
   %%{init: {'theme':'base','themeVariables':{
     'background':'#ffffff','primaryColor':'#ffffff','primaryBorderColor':'#333333',
     'primaryTextColor':'#000000','lineColor':'#333333','secondaryColor':'#ffffff',
     'tertiaryColor':'#ffffff','mainBkg':'#ffffff','clusterBkg':'#ffffff','clusterBorder':'#333333',
     'noteBkgColor':'#ffffff','noteTextColor':'#000000','noteBorderColor':'#333333',
     'actorBkg':'#ffffff','actorBorder':'#333333','actorTextColor':'#000000',
     'activationBkgColor':'#ffffff','activationBorderColor':'#333333',
     'signalColor':'#333333','signalTextColor':'#000000','labelBoxBkgColor':'#ffffff',
     'labelBoxBorderColor':'#333333','labelTextColor':'#000000','sequenceNumberColor':'#000000',
     'attributeBackgroundColorOdd':'#ffffff','attributeBackgroundColorEven':'#ffffff'
   }}}%%
   ```

   ครอบทั้ง sequence · ER · flow/EA. **ห้ามใส่ `style`/`classDef`/`fill:` ที่ให้สีพื้นอื่น** และห้ามพึ่ง
   ธีมสำเร็จ (`forest`/`neutral`/`dark`) — ทุกตัวมีสีแซม. ต้องการเน้น → ใช้ **เส้นหนา/กรอบเข้ม** ไม่ใช่สีพื้น.

4. **ต้องพิสูจน์ว่า render จริง (ชั้น 5).** หลัง publish — screenshot หน้า Confluence จริง แล้วดูว่า macro
   **แสดงเป็นภาพไดอะแกรม ไม่ใช่โค้ดดิบ ไม่ใช่กล่อง error** และ **พื้นขาวล้วน ไม่มีบล็อกเหลือง/ลาเวนเดอร์/สีอื่น
   แซม**. render ไม่ได้ หรือ มีสีอื่นโผล่ = **ไม่ผ่าน** (แก้ init directive แล้ว publish ใหม่).

## แนวป้องกัน 5 ชั้น — ไดอะแกรมพื้นขาวล้วน (ห้ามผิดเรื่องนี้)

สีแซม (เหลือง `note` / ลาเวนเดอร์ actor·activation) เกิดจาก**ธีม default ของ Mermaid เอง** ไม่ใช่สิ่งที่ตั้งใจใส่ —
เป็นบั๊กที่หลุดง่ายเพราะไม่มีใครเช็ก. กันด้วย 5 ชั้น แต่ละชั้นมี**เจ้าของ + หลักฐาน** ชัด และ **ตรวจไม่ได้ = ไม่ผ่าน**:

1. **ชั้น 1 — ป้องกันที่ต้นทาง (ตอนสร้าง source).** ทุก Mermaid source **ขึ้นต้นด้วย white-init directive**
   (บล็อกในข้อ 3) เสมอ — pin ทุก fill เป็น `#ffffff`, เส้น/ตัวอักษรเป็นเทาเข้ม/ดำ. **ห้าม** `style`/`classDef`/
   `fill:` ที่ให้สีพื้น และห้ามธีมสำเร็จ (`forest`/`neutral`/`dark`/`default`).

2. **ชั้น 2 — self-check ก่อนเขียน (drafting agent).** ก่อนประกอบ body ให้ grep ทุก source ที่จะฝัง: (ก) มี
   directive `theme:base` + `#ffffff` ครบ, (ข) **ทุก hex เป็นสีเทา/ขาว** — คือ `#rrggbb` ที่ R==G==B (ขาว/ดำ/เทา
   ล้วนผ่านหมด, เหลือง/ลาเวนเดอร์ตกทันทีเพราะ R≠G≠B). เจอสีอื่น/ไม่มี directive → แก้ก่อน อย่าเพิ่ง publish
   (fail-closed: ตรวจไม่ได้ = ไม่ผ่าน).

3. **ชั้น 3 — สคริปต์บังคับ (`verify-confluence.py` → `check_diagrams`, exit 1 บล็อกการเขียน).** สแกน Mermaid
   source ทุกบล็อก (CDATA / `<ac:plain-text-body>` / `<pre>`) แล้วบังคับกติกาชั้น 2 ด้วยเครื่อง — ขาด directive,
   ใช้ธีมสี, หรือมี hex ที่ไม่ใช่เทา/ขาว → **FAIL, ห้ามเขียน**. นี่คือชั้นที่บังคับได้จริง (มี fixture RED/GREEN
   พิสูจน์). **ข้อจำกัดที่พูดตรงๆ:** พิสูจน์ได้แค่ "source สะอาด" — พิสูจน์ pixel ที่ render จริงไม่ได้ (macro
   อาจ ignore directive) และเห็นเฉพาะ Mermaid ที่เก็บใน CDATA/plain-text-body/pre; เก็บแบบอื่น → ตกไปชั้น 4/5.

4. **ชั้น 4 — พิสูจน์บนหน้าที่ publish จริง (ชั้น 5 ของ `review.md`).** screenshot หน้า Confluence จริง แล้วดูด้วยตา
   ว่า **พื้นขาวล้วน ไม่มีบล็อกเหลือง/ลาเวนเดอร์/สีอื่นแซม** และ render เป็นภาพไม่ใช่โค้ดดิบ. มีสีโผล่ = **ไม่ผ่าน**
   → แก้ init แล้ว publish ใหม่. (นี่คือ backstop ของกรณีที่ชั้น 3 มองไม่เห็น/macro re-tint.)

5. **ชั้น 5 — แถวรีวิวคน + แก้แล้วรีวิวใหม่ทั้งหมด.** reviewer เขียนยืนยันเป็นคำว่าไดอะแกรมพื้นขาวล้วน (แนบ
   screenshot เป็นหลักฐาน ห้าม "น่าจะขาว"). **หนึ่ง FAIL = แก้ init → re-publish → re-review ครบทั้ง 5 ชั้น**
   เพราะแก้ไดอะแกรมหนึ่งอาจกระทบเลขข้อ/โครงหน้า.

ชั้น 1–3 พิสูจน์ก่อน**เขียน**; ชั้น 4–5 พิสูจน์หลัง**publish** เท่านั้น. ชั้น 3 ผ่าน ≠ จบ — ต้องครบทั้ง 5.

## ถ้า space ไม่มี macro ที่ render ได้ → หยุด บอกผู้ใช้ (ห้ามปล่อยพัง)

ตรวจ runtime ว่ามี diagram macro ที่ใช้ได้ไหม (ลองอ่านหน้าที่มี macro อยู่แล้ว หรือ publish หน้า sandbox แล้ว
อ่านกลับ/screenshot). ถ้าไม่มีตัวไหน render:

> Space นี้ยังไม่มี Mermaid/diagram macro ที่ render ได้ — ใส่ไดอะแกรมให้ render จริงไม่ได้จากที่นี่.
> ตัวเลือก: (ก) ติดตั้ง Mermaid app ใน Confluence แล้วรันใหม่ · (ข) ส่งไดอะแกรมเป็นไฟล์ภาพให้แนบเอง
> (skill เตรียม Mermaid source ให้พร้อมก๊อป). — เลือกทางไหน?

**ห้าม**: ปล่อยโค้ดดิบไว้เฉยๆ, ทิ้ง `placeholder` node, หรือแต่งไดอะแกรมที่ไม่ตรง schema. ตัวเลข/ความสัมพันธ์
ทุกเส้นต้องตรงแหล่ง.

## Fallback ที่ผู้ใช้เลือกได้ (ไม่ใช่ default)

ถ้าผู้ใช้เลือก "เตรียม source ให้แนบเอง" — ใส่ Mermaid/DDL source ใน **code block** บนหน้า พร้อมโน้ตว่า
"ไดอะแกรมรอแนบ (render จาก source นี้)" และทำเครื่องหมายเป็นงานค้างที่ชัดเจน (ไม่ใช่ mock, ไม่ใช่ของเสร็จ) —
รายงานตรงๆ ว่าชั้น 5 ยังไม่ผ่านสำหรับช่องไดอะแกรมนั้นจนกว่าจะแนบ.
