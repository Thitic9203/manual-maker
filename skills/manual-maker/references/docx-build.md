# Building the Word file (.docx)

## 1. The customer's base template is the deliverable — copy it exactly (ต้นแบบ)

When the user supplies a **base/ต้นแบบ `.docx`**, the manual **is** that template. Reuse, verbatim:

- the **cover** (background image + delivery/contract text),
- the **header** (agency logo + organisation line),
- the **footer** (the `PAGE` field — page numbers),
- the **table of contents** (a real `TOC` field, **grouped by role**),
- the **styles** (`Heading1`/`Heading2`/`Caption`…) and the **section structure**.

Do **not** rebuild any of these from scratch. A hand-made look-alike will be rejected — the user
asked for the template, "เลียนแบบมาเลย".

**docx-js cannot open an existing file.** To keep the shell, edit the OOXML directly:

```bash
unzip -q template.docx -d unpacked/
# edit unpacked/word/document.xml  (insert your section)
(cd unpacked && zip -Xrq ../out.docx .)
```

**Adding an image:** drop the PNG into `word/media/`, add a `<Relationship … Type=".../image"
Target="media/imageN.png"/>` to `word/_rels/document.xml.rels`, and reference it from a
`<w:drawing><wp:inline>` block. Easiest and safest: **copy an existing image block from the
template** and swap `r:embed` plus the **two** extents (`<wp:extent>` and `<a:ext>`) — recompute
`cy` from the new image's aspect ratio (`cy = cx × height / width`) or the picture will stretch.

Use `docx-js` only for documents **created from nothing**.

## 2. Chapters by role (แยกตามบทบาท)

Structure the manual by **user role**, matching the template:
**บทนำ → ครูผู้สอน → ผู้เรียน → ผู้ดูแลระบบ**. Each role is a chapter (`บทที่ N`); each task is a
numbered sub-section (`4.3 วิธี…`). The TOC groups by these chapters.

## 3. Font

**TH SarabunPSK** — body **16 pt** (`w:sz 32`), headings **18 pt bold** (`w:sz 36`) — unless the
template dictates otherwise; then follow the template.

> Thai is a **complex script**. Set **all four** `w:rFonts` slots — `w:ascii`, `w:hAnsi`,
> `w:eastAsia`, and above all **`w:cs`**. Miss `w:cs` and Word silently renders the Thai text in a
> fallback font.

### Line spacing — a wrapped Thai paragraph must not collide with the next one

`w:cs` fixes the glyphs; it does **not** fix the line box. Thai stacks vowel and tone marks above
and below the baseline, so a paragraph squeezed below the document's own default line height
overlaps the paragraph beneath it **as soon as it wraps**. Observed on a real delivery: a one-line
bullet rendered perfectly while the two-line bullet under it printed straight through its neighbour.
The defect is invisible until the text is long enough to wrap, so short test content never reveals it.

Two hazards, both flagged by `scripts/verify-doc.py` check 10:

- **`w:lineRule="exact"`** on a paragraph carrying real Thai text — a fixed line box clips the marks
  outright. (Template *spacer* paragraphs legitimately use `w:line="1" w:lineRule="exact"`; the check
  ignores them by requiring ≥ 40 Thai characters, so do not "fix" those.)
- **A paragraph-level `w:line` tighter than `docDefaults`** — something deliberately squeezed this
  paragraph below the rhythm the template chose.

When authoring a paragraph, either inherit the template's spacing untouched or set an explicit
`<w:spacing w:line="300" w:lineRule="auto"/>` with a little `w:after`. Never invent a value below the
document default. Judge inheritance, not the tag alone: most template paragraphs carry **no**
`<w:spacing>` at all and inherit a perfectly safe value from `docDefaults` — a checker that reads the
paragraph tag in isolation flags the pristine template (measured: 23 false positives on untouched
TOC entries).

### คำพราก — prevent it here, at build time

A Thai word split across two lines ("นัก" ends one line, "เรียน" starts the next) is **not** something
to fix in review — it is caused at build time, by exactly two things:

1. **A space or break inserted inside a word.** Thai puts spaces *between phrases*, never inside a
   word, so any space mid-word survives into the render as a break point. Never insert one for
   "spacing"; never let a `<w:br/>` land mid-sentence.
2. **A Thai run with no language tag.** Word breaks Thai lines using a Thai dictionary — but only
   when the run says it is Thai. Without it Word has no word boundaries and breaks anywhere.

So every Thai run carries **both** the `w:cs` font slot and the language tag:

```xml
<w:rPr>
  <w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK"
            w:eastAsia="TH SarabunPSK" w:cs="TH SarabunPSK"/>
  <w:sz w:val="32"/><w:szCs w:val="32"/>
  <w:lang w:bidi="th-TH"/>          <!-- ← ให้ Word ตัดคำไทยตามพจนานุกรม -->
</w:rPr>
```

`scripts/verify-doc.py` fails the build when either is missing (checks 3 and 4), so a manual that
would แตกคำ cannot reach the user — but the fix belongs here, not there.

## 3.1 Thai Distribute — จัดแนวข้อความไทยทุกย่อหน้าเนื้อหา

การตัดคำของเอกสารใช้ **Thai Distribute** (feedback ข้อ 3): ทุกย่อหน้า **เนื้อหาภาษาไทยที่เขียนขึ้นเอง**
ตั้ง justification เป็น `thaiDistribute` — Word จะกระจายข้อความให้เต็มบรรทัด ตัดคำตามขอบเขตคำไทย และขอบ
ซ้าย-ขวาเสมอกัน. ทำงานคู่กับ `w:cs` + `w:lang w:bidi` (§3) ที่กันคำพราก.

```xml
<w:pPr>
  <w:jc w:val="thaiDistribute"/>
  <w:spacing w:line="300" w:lineRule="auto" w:after="120"/>   <!-- อย่าบีบต่ำกว่าค่าเริ่มต้น (§3) -->
</w:pPr>
```

ใส่กับย่อหน้าเนื้อหา (คำอธิบาย, ผลลัพธ์, bullet). **หัวข้อ/caption/เซลล์ตารางสั้น ๆ ไม่ต้องบังคับ** — ถ้ามี
ต้นแบบกำหนด jc ของ style ไว้แล้ว ให้เคารพต้นแบบ. `verify-doc.py --thai-distribute required` (ข้อ 12) จับ
เอกสารไทยยาวที่ไม่ได้ตั้ง thaiDistribute เลย.

## 3.2 หัวข้อเลขอัตโนมัติ — auto-numbered headings (multilevel list)

เลขหัวข้อ (`1`, `1.1`, `1.1.1`) มาจาก **ระบบเลขของ Word ผูกกับ Heading styles** ไม่ใช่พิมพ์เลขลงในข้อความ
หัวข้อ (feedback ข้อ 2): แทรก/สลับหัวข้อแล้วเลขไล่ใหม่เอง และ TOC ดึงเลขไปให้อัตโนมัติ.

1. **นิยาม multilevel list ใน `word/numbering.xml`** — abstractNum ที่แต่ละระดับ `w:numFmt="decimal"`
   และ `w:lvlText` เป็น `%1`, `%1.%2`, `%1.%2.%3` แล้วผูกเป็น `w:num w:numId="1"`:
   ```xml
   <w:abstractNum w:abstractNumId="10">
     <w:lvl w:ilvl="0"><w:numFmt w:val="decimal"/><w:lvlText w:val="%1"/></w:lvl>
     <w:lvl w:ilvl="1"><w:numFmt w:val="decimal"/><w:lvlText w:val="%1.%2"/></w:lvl>
     <w:lvl w:ilvl="2"><w:numFmt w:val="decimal"/><w:lvlText w:val="%1.%2.%3"/></w:lvl>
   </w:abstractNum>
   <w:num w:numId="1"><w:abstractNumId w:val="10"/></w:num>
   ```
2. **ผูกเข้ากับ Heading styles ใน `word/styles.xml`** — ให้ทุกหัวข้อได้เลขโดยไม่ต้องแตะราย paragraph:
   ```xml
   <w:style w:type="paragraph" w:styleId="Heading1"> … 
     <w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr>
   </w:style>
   ```
   (Heading2 → `w:ilvl="1"`, Heading3 → `w:ilvl="2"`.)
3. **ข้อความหัวข้อมีแต่ชื่อ ห้ามมีเลข** — เขียน `<w:t>ครูผู้สอน</w:t>` ไม่ใช่ `<w:t>2.1 ครูผู้สอน</w:t>`.
   เลขซ้อน (numPr + เลขพิมพ์มือ) = `verify-doc.py` ข้อ 13 FAIL.

**ถ้ามีต้นแบบ (ต้นฉบับ) กำหนดสไตล์เลขของตัวเองไว้ → ใช้ของต้นแบบ** (ต้นแบบชนะ) — สคริปต์ SKIP ให้เมื่อ
ไม่พบ numPr โดยไม่ FAIL. TOC เป็น field จริงอยู่แล้ว จะแสดงเลขที่ Word สร้างให้เอง.

## 3.3 คำบรรยายรูป/ตาราง — figure & table captions (SEQ field)

ทุกรูปมี `รูปที่ N: …` และทุกตารางเนื้อหามี `ตารางที่ N: …` (feedback ข้อ 1) เพื่อให้เรียงลำดับและอ้างอิงได้.
เลขในคำบรรยายเป็น **field `SEQ`** ใน style `Caption` (ไม่ใช่เลขพิมพ์มือ) — แทรกรูปแล้วเลขไล่ใหม่เอง:

```xml
<w:p>
  <w:pPr><w:pStyle w:val="Caption"/><w:jc w:val="center"/></w:pPr>
  <w:r><w:rPr><w:rFonts w:cs="TH SarabunPSK"/><w:lang w:bidi="th-TH"/></w:rPr>
      <w:t xml:space="preserve">รูปที่ </w:t></w:r>
  <w:r><w:fldChar w:fldCharType="begin"/></w:r>
  <w:r><w:instrText xml:space="preserve"> SEQ Figure \* ARABIC </w:instrText></w:r>
  <w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r>
  <w:r><w:fldChar w:fldCharType="end"/></w:r>
  <w:r><w:rPr><w:rFonts w:cs="TH SarabunPSK"/><w:lang w:bidi="th-TH"/></w:rPr>
      <w:t xml:space="preserve">: หน้าจอหลักของระบบ</w:t></w:r>
</w:p>
```

- ตารางเนื้อหาใช้ `SEQ Table` แทน `SEQ Figure`. **ตารางที่เป็น layout ของขั้นตอนไม่นับเป็นตารางเนื้อหา**
  จึงไม่ใส่ `ตารางที่ …`.
- Caption อยู่ **ใต้รูป/ตารางในเซลล์เดียวกัน** (รูปในแถวขั้นตอน → caption ในแถวนั้น).
- อยากได้ **สารบัญรูป (List of Figures)** ใส่ TOC field `\c "Figure"` (และ `\c "Table"` สำหรับตาราง).
- SEQ เป็น field → ผู้ใช้ต้องตอบ **"Update fields? → Yes"** ตอนเปิด (มีบอกใน §5 อยู่แล้ว).
- `verify-doc.py --captions required` (ข้อ 11) FAIL ถ้ารูป inline มากกว่าจำนวน caption รูป.

## 3.4 ตารางขั้นตอน — step table with the image in the step's row

ขั้นตอนจัดเป็น **ตาราง** แถวละขั้นตอน และ **ภาพของขั้นตอนนั้นอยู่ในแถวเดียวกัน** (feedback ข้อ 4) —
คอลัมน์ `ลำดับ | ขั้นตอน | ภาพประกอบ`. รูปฝังแบบ inline ในเซลล์ `ภาพประกอบ` พร้อม caption `รูปที่ N` ใต้รูป
ในเซลล์เดิม. เลขในวงแดง = เลขในคอลัมน์ `ลำดับ` 1:1.

- **รูปเดียวครอบหลายขั้นตอน → วางในแถวของขั้นตอน _แรก_** ในกลุ่มนั้น (เว้นเซลล์ภาพของขั้นถัด ๆ ไป หรือใส่
  "ดูรูปที่ N") และวาดวงแดงทุกวงที่เกี่ยวข้องบนรูปเดียวนั้น (≤ 5 วง/รูป). เช่น หน้าจอที่แสดงคอนโทรลของ
  ขั้นตอน 2–4 → รูปไปอยู่แถวขั้นตอน 2 พร้อมวง ②③④.
- คัดลอกโครง `<w:tbl>` + `<w:tblPr>` (เส้น/ความกว้าง) จากต้นแบบถ้ามี; ฝังรูปด้วยบล็อก `<w:drawing><wp:inline>`
  ตาม §1 (recompute `cy` จากอัตราส่วนรูป). ห้ามรวบรูปไปกองท้ายหัวข้อ.

## 4. Verify before delivering

- The image really is embedded: `word/media/imageN.png` exists, a relationship points at it, and the
  `<w:drawing>` block is complete.
- No template placeholder text survives (`SCREENSHOT PLACEHOLDER`, `[ระบุ…]`).
- Font, sizes, numbering, and the TOC match the template.
- **Captions** — every inline image has a `รูปที่ N` caption (§3.3); run `verify-doc.py --captions required`.
- **Thai Distribute** — authored Thai body paragraphs set `w:jc w:val="thaiDistribute"` (§3.1); run `verify-doc.py --thai-distribute required`.
- **Headings** — auto-numbered via the multilevel list (§3.2), no hand-typed or double numbers.

## 5. Word has the file open

A `~$<name>.docx` lock file means **Word is holding the document**. Writing to disk still succeeds,
but Word keeps the *old* copy in memory and will overwrite yours if the user saves. Tell the user:

1. **Close Word — do not Save.**
2. Reopen the file.
3. Answer **"Update fields?" → Yes** so the TOC, page numbers, and figure numbers refresh.
