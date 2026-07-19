# Team Handbook Template

Standard structure, quality rules, and final-review checklist for every user manual. `doc-coauthoring` drafts into this shape; the manual is not delivered until it passes the checklist at the bottom.

## Structure (sections, in order)

> 🔴 **If the user supplied a base template (ต้นแบบ), that template's structure wins** — reuse its
> cover, header, footer (page numbers), TOC, styles, and its **role-based chapters**
> (บทนำ / ครูผู้สอน / ผู้เรียน / ผู้ดูแลระบบ) **exactly**. Never hand-build a look-alike.
> See `docx-build.md`. The generic outline below applies only when there is no template.
> **If the run also splits by role/module (intake Q9), read "Document split" just below —
> the split decides packaging (how many volumes); the template still decides the look.**

1. **หน้าปก / Cover** — system name, version, date, target audience, "who this guide is for".
2. **ภาพรวมระบบ / Overview** — what the system does, main benefits, key terms.
3. **เริ่มต้นใช้งาน / Getting Started** — prerequisites, VPN (if any), how to reach the URL, how to log in (procedure only), first-time setup.
4. **แนะนำหน้าจอ / UI Orientation** — a labelled screenshot of the main screen; name the key areas.
5. **การใช้งานตามฟีเจอร์ / Feature Walkthroughs** — one subsection per module: what it's for → numbered steps → annotated screenshot per step → expected result.
6. **งานที่ทำบ่อย / Common Tasks (How-to)** — task-based recipes, each a short numbered flow.
7. **แก้ปัญหาเบื้องต้น / Troubleshooting & FAQ** — **include only if a source was given at intake Q20** (doc / Confluence / known-issues list). No source → **omit the section**; never invent problems or fixes (ห้ามมโน).
8. **อภิธานศัพท์ / Glossary** — the locked terms, defined once (sourced from intake Q15).
9. **ติดต่อ / Support** — **include only if contact info was given at intake Q19**. No contact → **omit the section**; do not fabricate a channel.

## Document split — one volume, or several (from intake Q9)

The confirmed split choice (intake Q9) decides how many deliverables this run produces:

- **(ค) เล่มเดียวรวม / single combined volume** — the default shape above: one document, roles
  handled as chapters inside it.
- **(ก) แบ่งตามบทบาท / by role** — **one separate volume per confirmed role** (e.g. a
  ผู้ดูแลระบบ volume and a ผู้เรียน volume). Each volume is a complete document with its **own**
  cover, TOC, and numbering **restarting at 1**; each covers only that role's features.
- **(ข) แบ่งตามระบบ/โมดูล / by system or module** — one separate volume per confirmed
  system/module, same per-volume rules as (ก).

**Base template vs by-role/-module split — resolution rule (both can be in play at once):**
the base template (🔴 above) governs the **look** — cover, header/footer, TOC, styles, fonts.
The Q9 choice governs the **packaging** — how many volumes and what each contains. They do not
conflict: apply the template's styling to **each** volume, but a by-role/-module split
**overrides** the template's single-document *role-based chapter list* — instead of all roles as
chapters in one file, emit one styled volume per confirmed role/module. If the base template and
the Q9 split imply different groupings, the **confirmed Q9 choice wins for packaging**; never
silently merge volumes back into one, and never split a confirmed single volume.

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
- **Full screen (เต็มจอ)** — never crop the content. The primary **headless Playwright** capture has no glow border and no cursor; only the screen/clipboard **fallback** needs the glow removed (mind the orange agency logo, which naive orange-detection will eat).
- **No mouse cursor** in the image (headless has none; paint it out only on the fallback path).
- **Red numbered circles** on the click targets, **numbers matching the step numbers 1:1**, ≤ 5 per image, same style throughout.
- Steps name the system's **real** menu/button/tab wording — no placeholder text left behind.
- **Mask people's names** (students are minors). Every screenshot sharp and legible; caption what to look at.
- **File location:** every source PNG lives in `manual-assets/<slug>/`, named `<section>-<step>.png` (see `screenshots.md`) — figure ↔ step ↔ filename stay 1:1, so the red circle numbers align with the step numbers by construction.

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
   ![create button](manual-assets/<slug>/05-2-01.png)   ← กรอบ + เลข 1 ที่ปุ่ม
2. กรอกชื่อในช่อง **ชื่อ**
3. คลิก **บันทึก**
   → ระบบแสดง "บันทึกสำเร็จ" และรายการปรากฏในตาราง
```

## Final Review Checklist — run before delivery (ห้ามตกหล่น)

> 🔴 **This checklist is the item-level detail of the 5-layer review in `review.md` — same content,
> different view.** `review.md` owns the **ลำดับการตัดสินและ delivery gate** (ห้ามบอกว่าเสร็จจนกว่าจะผ่านครบ
> 5 ชั้น; ตรวจไม่ได้ = ไม่ผ่าน; FAIL ข้อเดียว = รีวิวใหม่ทั้ง 5 ชั้น). Run this list **against the built
> file**, as part of those layers — not as a separate self-assessment.

Go through **every** line; fix all before handing over. Do not deliver a manual that fails any item.

- [ ] **เนื้อหาตรงแหล่งข้อมูล** — every step matches the live system + the user's source (Confluence/spec/reference). No invented steps.
- [ ] **ไม่มีบทที่แต่งเอง** — Troubleshooting/FAQ (Q20) และ Support (Q19) มาจากแหล่ง/ข้อมูลที่ผู้ใช้ให้เท่านั้น; ไม่มีแหล่ง = **ข้ามบท** ไม่ใช่มโนขึ้นมา.
- [ ] **ครบตาม scope** — all requested modules/features covered; nothing extra added.
- [ ] **แบ่งเล่มถูกตามที่ยืนยัน** — the number of volumes and the split dimension match the confirmed intake Q9 choice; each by-role/-module volume has its own cover, TOC, and numbering restarting at 1, and covers only its role/module.
- [ ] **เลขข้อถูกต้อง** — numbering continuous, no gaps/duplicates; TOC matches body.
- [ ] **คำศัพท์สอดคล้อง** — one locked term per concept throughout; no synonyms slipped in.
- [ ] **โทน/ภาษาถูกต้อง** — formal written language; no 1st/2nd-person pronouns (ผม/คุณ/ท่าน), no particles (ครับ/ค่ะ); reads naturally, not machine-translated; spelling correct.
- [ ] **Font & size สม่ำเสมอ** — matches the agreed values on every page.
- [ ] **ตรงต้นแบบ** — if a base template was given: cover, header, footer (page numbers), TOC, styles, and role-based chapters are the template's own, not rebuilt.
- [ ] **ภาพเป็นระบบจริง** — every figure is a **real, full-screen** live-system screenshot. No placeholder box, no mock-up, no redrawn table.
- [ ] **ภาพสะอาด** — no glow border, **no mouse cursor**, agency logo intact, content never cropped (headless capture is clean by default; fallback captures must have the glow/cursor removed).
- [ ] **วงแดงตรงสเตป** — red numbered circles map **1:1** to the step numbers (≤ 5 per image), consistent style.
- [ ] **ชื่อคนถูกปิด** — students'/teachers' real names masked or blurred.
- [ ] **ไม่มี placeholder ค้าง** — no "TODO", no "[…]", no `SCREENSHOT PLACEHOLDER`, no `[ระบุ…]`, no missing caption.
- [ ] **รูปฝังจริง** — `word/media/` has the image, the relationship resolves, the `<w:drawing>` block is complete.
- [ ] **สะกด/ภาษา** — spelling and grammar checked; tone consistent.
- [ ] **ไม่มี credential/ข้อมูลลับ** หลุดในเอกสาร.
- [ ] **Output ถูกช่อง** — correct format; if Confluence/web, target confirmed before posting.
- [ ] **ส่งมอบ Word ถูกวิธี** — if a `~$….docx` lock exists (Word has it open), tell the user to **close Word without saving**, reopen, and answer **"Update fields? → Yes"** so the TOC, page numbers, and figure numbers refresh.

Report the result to the user as the **5-layer verdict table** in `review.md` — every round, including
the failing ones. **ผ่าน 5/5 เท่านั้นจึงส่งมอบ/publish ได้.**
