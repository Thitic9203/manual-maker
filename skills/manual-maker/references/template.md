# Team Handbook Template

Standard structure, quality rules, and final-review checklist for every user manual. `doc-coauthoring` drafts into this shape; the manual is not delivered until it passes the checklist at the bottom.

## Structure (sections, in order)

> 🔴 **If the user supplied a base template (ต้นแบบ), that template's structure wins** — reuse its
> cover, header, footer (page numbers), TOC, styles, and its **role-based chapters**
> (บทนำ / ครูผู้สอน / ผู้เรียน / ผู้ดูแลระบบ) **exactly**. Never hand-build a look-alike.
> See `docx-build.md`. The generic outline below applies only when there is no template.

1. **หน้าปก / Cover** — system name, version, date, target audience, "who this guide is for".
2. **ภาพรวมระบบ / Overview** — what the system does, main benefits, key terms.
3. **เริ่มต้นใช้งาน / Getting Started** — prerequisites, VPN (if any), how to reach the URL, how to log in (procedure only), first-time setup.
4. **แนะนำหน้าจอ / UI Orientation** — a labelled screenshot of the main screen; name the key areas.
5. **การใช้งานตามฟีเจอร์ / Feature Walkthroughs** — one subsection per module: what it's for → numbered steps → annotated screenshot per step → expected result.
6. **งานที่ทำบ่อย / Common Tasks (How-to)** — task-based recipes, each a short numbered flow.
7. **แก้ปัญหาเบื้องต้น / Troubleshooting & FAQ**.
8. **อภิธานศัพท์ / Glossary** — the locked terms, defined once.
9. **ติดต่อ / Support**.

## Quality rules — the four axes (be exact)

### 1. Font & size
- Take the exact font and sizes from the **reference document** the user provided. If none, **ask** — never assume a font.
- Keep them **uniform**: one font family; one size per role (H1/H2/H3/body/caption). Record the chosen values here at the start of each project and apply them everywhere.
- **Thai default (unless the template says otherwise): `TH SarabunPSK` — body 16 pt, headings 18 pt bold.**
- ⚠️ Thai is a **complex script**: in `.docx`, set **all four** `w:rFonts` slots (`w:ascii`, `w:hAnsi`, `w:eastAsia`, **`w:cs`**). Miss `w:cs` and Word silently renders Thai in a fallback font.

### 2. Numbering
- Continuous decimal outline (`1`, `1.1`, `1.1.1`) with **no gaps and no duplicates**.
- Step lists restart at 1 within each task; section numbers never restart.
- The table of contents must match the body numbering exactly.

### 3. Image clarity + annotation — **see `screenshots.md` (binding)**
- **Real live-system screens only** — never a placeholder box, a mock-up, or a redrawn table standing in for a screen.
- **Full screen (เต็มจอ)** — never crop the content. Remove **only** the Claude screen-control glow border (and mind the orange agency logo, which naive orange-detection will eat).
- **No mouse cursor** in the image.
- **Red numbered circles** on the click targets, **numbers matching the step numbers 1:1**, ≤ 5 per image, same style throughout.
- Steps name the system's **real** menu/button/tab wording — no placeholder text left behind.
- **Mask people's names** (students are minors). Every screenshot sharp and legible; caption what to look at.

### 4. Terminology consistency
- Use the **locked term** for each concept **everywhere** — e.g. if "ผู้เรียน" is chosen, never use "นักเรียน" / "นร." / "ผู้ใช้" interchangeably.
- Keep the term list in the Glossary. If a new term appears mid-draft and isn't on the list → **ask the user** which word to use before writing it.

## Language & tone (the manual's writing)

The manual is written in **formal, professional, polished written Thai** (or the chosen language) — clear and natural to read, **not** a stiff machine translation.

- **ไม่ใช้สรรพนามบุรุษที่ 1/2** — never "ผม / ฉัน / ดิฉัน / เรา / คุณ / ท่าน". Refer to the reader by the locked role term ("ผู้ใช้งาน" / "ผู้เรียน") only when necessary, or write in the **imperative** ("เลือกเมนู…", "กดปุ่มบันทึก").
- **ไม่ใช้คำลงท้าย** — never "ครับ / ค่ะ / นะ / จ้ะ".
- **Professional yet human** — vary sentence structure, use natural connectors; avoid robotic repetition and literal translationese.
- **One locked term per concept**, consistent throughout.
- Consistent, correct spelling; formal vocabulary suited to the audience.

Example — ✅ "เลือกเมนู **หลักสูตรของฉัน** จากแถบด้านซ้าย เพื่อเปิดรายการหลักสูตรทั้งหมด"  ❌ "คุณสามารถเลือกเมนูหลักสูตรของฉันได้เลยนะครับ"

## Conventions

- **Numbered steps**, one action per step, imperative voice.
- **Callouts:** `> ⚠️ ข้อควรระวัง:` and `> 💡 เคล็ดลับ:`.
- **No real credentials, tokens, or personal data** anywhere in the manual.
- Plain, polite language matched to the audience; no internal jargon or dev terms.

## Example step format

```
### 5.2 สร้างรายการใหม่

1. คลิกปุ่ม **"+ สร้างใหม่"** มุมขวาบน
   ![create button](assets/05-create-01.png)   ← กรอบ + เลข 1 ที่ปุ่ม
2. กรอกชื่อในช่อง **ชื่อ**
3. คลิก **บันทึก**
   → ระบบแสดง "บันทึกสำเร็จ" และรายการปรากฏในตาราง
```

## Final Review Checklist — run before delivery (ห้ามตกหล่น)

Go through **every** line; fix all before handing over. Do not deliver a manual that fails any item.

- [ ] **เนื้อหาตรงแหล่งข้อมูล** — every step matches the live system + the user's source (Confluence/spec/reference). No invented steps.
- [ ] **ครบตาม scope** — all requested modules/features covered; nothing extra added.
- [ ] **เลขข้อถูกต้อง** — numbering continuous, no gaps/duplicates; TOC matches body.
- [ ] **คำศัพท์สอดคล้อง** — one locked term per concept throughout; no synonyms slipped in.
- [ ] **โทน/ภาษาถูกต้อง** — formal written language; no 1st/2nd-person pronouns (ผม/คุณ/ท่าน), no particles (ครับ/ค่ะ); reads naturally, not machine-translated; spelling correct.
- [ ] **Font & size สม่ำเสมอ** — matches the agreed values on every page.
- [ ] **ตรงต้นแบบ** — if a base template was given: cover, header, footer (page numbers), TOC, styles, and role-based chapters are the template's own, not rebuilt.
- [ ] **ภาพเป็นระบบจริง** — every figure is a **real, full-screen** live-system screenshot. No placeholder box, no mock-up, no redrawn table.
- [ ] **ภาพสะอาด** — Claude's screen-control glow border removed, **no mouse cursor**, agency logo intact, content never cropped.
- [ ] **วงแดงตรงสเตป** — red numbered circles map **1:1** to the step numbers (≤ 5 per image), consistent style.
- [ ] **ชื่อคนถูกปิด** — students'/teachers' real names masked or blurred.
- [ ] **ไม่มี placeholder ค้าง** — no "TODO", no "[…]", no `SCREENSHOT PLACEHOLDER`, no `[ระบุ…]`, no missing caption.
- [ ] **รูปฝังจริง** — `word/media/` has the image, the relationship resolves, the `<w:drawing>` block is complete.
- [ ] **สะกด/ภาษา** — spelling and grammar checked; tone consistent.
- [ ] **ไม่มี credential/ข้อมูลลับ** หลุดในเอกสาร.
- [ ] **Output ถูกช่อง** — correct format; if Confluence/web, target confirmed before posting.
- [ ] **ส่งมอบ Word ถูกวิธี** — if a `~$….docx` lock exists (Word has it open), tell the user to **close Word without saving**, reopen, and answer **"Update fields? → Yes"** so the TOC, page numbers, and figure numbers refresh.

Report the checklist result to the user before export.
