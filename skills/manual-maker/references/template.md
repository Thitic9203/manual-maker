# Team Handbook Template

Standard structure, quality rules, and final-review checklist for every user manual. `doc-coauthoring` drafts into this shape; the manual is not delivered until it passes the checklist at the bottom.

## Structure (sections, in order)

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

### 2. Numbering
- Continuous decimal outline (`1`, `1.1`, `1.1.1`) with **no gaps and no duplicates**.
- Step lists restart at 1 within each task; section numbers never restart.
- The table of contents must match the body numbering exactly.

### 3. Image clarity + annotation
- Every screenshot **sharp and legible** at the delivered size — no blur, no half-cut UI.
- If annotation was requested: a **box (กรอบ)** around the click target **and** a **numbered marker (เลขลำดับ)** matching the step number. Consistent colour and marker style across the whole manual.
- One meaningful screenshot per action step; caption what to look at.

### 4. Terminology consistency
- Use the **locked term** for each concept **everywhere** — e.g. if "ผู้เรียน" is chosen, never use "นักเรียน" / "นร." / "ผู้ใช้" interchangeably.
- Keep the term list in the Glossary. If a new term appears mid-draft and isn't on the list → **ask the user** which word to use before writing it.

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
- [ ] **Font & size สม่ำเสมอ** — matches the agreed values on every page.
- [ ] **ภาพครบ + ชัด + annotate ถูก** — every step has a sharp screenshot; boxes/numbers correct and consistent.
- [ ] **ไม่มี placeholder ค้าง** — no "TODO", no "[…]", no missing caption.
- [ ] **สะกด/ภาษา** — spelling and grammar checked; tone consistent.
- [ ] **ไม่มี credential/ข้อมูลลับ** หลุดในเอกสาร.
- [ ] **Output ถูกช่อง** — correct format; if Confluence/web, target confirmed before posting.

Report the checklist result to the user before export.
