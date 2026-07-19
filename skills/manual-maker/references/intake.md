# Intake Questions

Ask these **one at a time**, in order. Where an answer has a **bold default**, offer it. Where it says *(ต้องถาม — no default)*, **never assume** — keep asking until the user gives an explicit, clear answer.

**How to ask:** พูดกับผู้ใช้เป็น **ภาษาไทยที่เป็นทางการ สุภาพ มืออาชีพ** (ตามค่าเริ่มต้น) — สะกดถูกต้อง เลือกใช้คำให้เหมาะสม ถามทีละข้อ ไม่รวบหลายคำถามในครั้งเดียว หลีกเลี่ยงคำลงท้าย (ครับ/ค่ะ) และสรรพนามที่ไม่จำเป็น ให้ข้อความกระชับ ชัดเจน เป็นธรรมชาติ

## Golden rules for this skill

- **ห้ามมโน / ห้ามคิดเอง.** If any answer is missing, vague, or you are unsure — STOP and ask again until you get explicit confirmation. Never guess system steps, scope, wording, fonts, or numbering.
- **ห้ามทำเกินขอบเขต.** Document only what was asked. No extra modules, no opinions, no "while I'm here" additions, no deciding on the user's behalf.
- **ยืนยันก่อนเริ่มเสมอ.** After intake, summarize everything and get an explicit "go" before any screenshot or drafting (see the Confirmation Gate at the end).

## Sequencing — ถามทีละข้อเฉพาะข้อที่ต้องถาม; ข้อที่มี default รวบเป็นชุดเดียว

ลดจำนวนรอบถามโดยไม่ลดทอน gate ใด:

- **ถามทีละข้อ** — ข้อ *(ต้องถาม — no default)*: **1, 2, 3, 4, 5, 6, 9, 13, 15, 17**. ห้ามรวบ ห้ามข้าม ห้ามเดา.
- **รวบเป็นชุดเดียว** — ข้อที่มี bold default ชัดเจน: **7, 8, 10, 11, 12, 14, 16, 18, 19, 20**. แสดง default ทุกข้อในตารางเดียว แล้วถามครั้งเดียว: **"ค่าเริ่มต้นเหล่านี้ใช้ได้ไหม หรือต้องการแก้ข้อใด"** — ผู้ใช้แก้เฉพาะข้อที่ต้องการ ที่เหลือถือว่ารับ default.
- Confirmation Gate ท้ายสุดยังทำครบเหมือนเดิม — การรวบชุด default ไม่ได้ข้ามการยืนยัน.

## 0. Load saved profile first — do not re-ask what this user already answered

Before Section A, follow `profile.md`: look in `~/.manual-maker/profiles/` for this user's saved
answers for this system. If found, show them and ask what changed — then **skip every intake
question the user confirms is unchanged.** Only ask for missing or changed fields. If nothing is
saved, run the full intake below. (Credentials are **never** saved — always ask them fresh.)

## A. System & access  — *live access is verified every run*

> With a saved profile, **URL(s) and VPN state are pre-filled and confirmed** (shown as the
> default; the user confirms they still hold — not asked from scratch). **Credentials are never
> stored and are always asked fresh, in-session.**

1. **System name** — which system, and what is it in one line? *(ต้องถาม)*
2. **URL(s)** to document. *(ต้องถาม — with a saved profile, show the saved URL as the default and confirm it still holds; never silently reuse — live access is verified every run)*
3. **Login** — email/username + password needed to reach the screens. *(ต้องถาม)*
   > 🔐 Credentials are used **only in this session** to open the system for screenshots. The **headless
   > Playwright** capture reads them from the **environment** (`process.env.EMAIL`/`process.env.PW`) or a
   > pre-saved `storageState` — Claude never types a password into a live form by hand. They are **never**
   > written into the manual, the repo, logs, a committed script, or any file, **never echoed** (show
   > `password provided (not shown)`), and any `.env` stays behind `.gitignore`. See `screenshots.md`.
4. **VPN** — does access need a VPN, and is it connected yet? *(ต้องถาม — confirm before trying the URL)*

## B. Source material — so the content is accurate, not guessed  (*ห้ามมโน*)

5. **Authoritative source of how the system works** — is there a **Confluence page, spec, flow diagram, existing manual, or example document** that clearly describes the steps? Ask for the links/files. Every step in the manual must come from these sources **plus** the live system — **never** from assumption. If none exists and a step is unclear → ask the user. *(ต้องถาม — get links/files or an explicit "none")*
6. **Base template / ต้นแบบ to match** (cover, header/footer, TOC, layout, font, chapter structure)? Ask the user to share the file now. **If one exists it is binding: the manual is built ON that template — its cover, header, footer (page numbers), TOC, styles, and role-based chapters are reused exactly, never rebuilt by hand** (see `docx-build.md`). **Default: none.**

## C. Audience & scope

7. **Target users** — role + tech level. **Default: non-technical end users.**
8. **Scope** — which modules/features to cover. **Default: all main user-facing features.**
9. **Document split / การแบ่งเล่มเอกสาร** — ต้องการแยกคู่มือเป็นกี่เล่ม และแบ่งตามอะไร? **เสนอเป็นตัวเลือกให้ผู้ใช้เลือกเสมอ:**
   - **(ก) แบ่งตามบทบาทผู้ใช้งาน** — คู่มือแยกเล่มต่อ role เช่น เล่มผู้ดูแลระบบ / เล่มผู้เรียน / เล่มผู้สอน
   - **(ข) แบ่งตามระบบหรือโมดูล** — คู่มือแยกเล่มต่อระบบ/โมดูล เช่น เล่มระบบประเมิน / เล่มระบบรายงาน
   - **(ค) เล่มเดียวรวมทุกอย่าง** — คู่มือเล่มเดียว แบ่งเป็นบทภายในเล่ม
   *(ต้องถาม — no default; ถ้าเลือก ก หรือ ข ให้ถามต่อว่ามี role/ระบบ อะไรบ้าง และยืนยันรายชื่อเล่มก่อนเริ่ม)*
10. **Depth** — overview, or exhaustive step-by-step? **Default: step-by-step for core tasks.**

## D. Screenshots

11. **Capture** — auto-capture from the live system (**headless Playwright**, non-intrusive — runs in its own headless browser, does not take over the screen), user-provided images, or none? **Default: auto-capture.**
12. **Annotation — ถามให้ชัดว่าเอาแบบไหน (ทั้งสองแบบถูกได้ ผิดคือทำไม่ตรงกับที่สั่ง):**
    **(ก) มีวงแดง — Default:** วงกลมแดงมีเลขบนเป้าที่คลิก เลขตรงกับเลขขั้นตอน **1:1**, ≤ 5 วง/รูป, สไตล์เดียวกันทั้งเล่ม ·
    **(ข) ไม่มีวง:** ภาพหน้าจอเปล่า เต็มจอเหมือนกัน **ห้ามใส่วงมาเผื่อ**.
    คำตอบนี้ถูกบันทึกลงตารางยืนยัน และกลายเป็นค่า `--annotations required|none` ที่ใช้ตรวจในรีวิวชั้นที่ 1 และ 3
    (`review.md`) — ถ้าไม่ตรงกับที่ยืนยันไว้ ถือว่า **ไม่ผ่าน**. ถ้าผู้ใช้อยากได้สไตล์อื่น (กรอบ/ลูกศร/ไฮไลต์) ให้ยืนยันสไตล์ก่อนเริ่ม. Screenshots are **full-screen, uncropped**; the headless capture has **no glow border and no cursor** to remove (that cleanup applies only to the screen/clipboard fallback) — see `screenshots.md`.

## E. Formatting & terminology  — *be exact; this is where quality is won or lost*

13. **Font & size** — follow the base template, or specify (heading vs body sizes)? *(ต้องถาม — take from the template or ask; never assume a font)* **Thai default when there is no template: `TH SarabunPSK`, body 16 pt, headings 18 pt bold.** In `.docx`, Thai needs the **`w:cs`** font slot set — see `docx-build.md`.
14. **Numbering** — scheme for sections and steps (e.g. `1`, `1.1`, `1.1.1`). **Default: follow the reference doc; otherwise a decimal outline, continuous with no gaps.**
15. **Terminology to lock** — the key terms and the **exact word** to use everywhere (e.g. always "ผู้เรียน", never "นักเรียน"/"นร."). Build the term list and read it back for confirmation. If unsure about any word → ask before writing. *(ต้องถาม — confirm the locked term list)*
16. **Language** — which language for the manual? **Default: Thai.**
    > **โทนของเอกสารถูกกำหนดไว้แล้ว (ไม่ต้องถาม แต่แจ้งให้ผู้ใช้ทราบ):** ภาษาเขียนที่เป็นทางการ สุภาพ มืออาชีพ อ่านลื่น เป็นธรรมชาติ (ไม่ใช่สำนวนแปลด้วยเครื่อง) — **ไม่ใช้สรรพนามบุรุษที่ 1/2** (ผม ฉัน ดิฉัน เรา คุณ ท่าน) และ **ไม่ใช้คำลงท้าย** (ครับ ค่ะ นะ). ดูรายละเอียดใน `template.md`.

## F. Output

17. **Output format — ต้องถามเสมอ ถ้าผู้ใช้ยังไม่ระบุ:** ต้องการไฟล์รูปแบบใด — **ไฟล์ Word (.docx) / PDF / Confluence / หน้าเว็บ**? ถ้าเลือก Confluence ให้ระบุ space + หน้าแม่ที่จะเผยแพร่. **Default: Word (.docx)** — เป็นเส้นทางที่ฝัง screenshot ได้จริง (พิสูจน์แล้ว). ⚠️ **Confluence เผยแพร่ผ่าน Atlassian MCP ได้เฉพาะตัวหน้า/โครงสร้าง — MCP ไม่อัปโหลดไฟล์ภาพให้**; คู่มือที่มีภาพเยอะ (กรณีปกติ) ใช้ .docx/PDF, ถ้าจะใช้ Confluence จริงต้องแนบภาพเองหรืออ้าง URL ภาพที่ host ไว้แล้ว. หากผู้ใช้ยังไม่ระบุรูปแบบ ให้ถามให้ชัดก่อนดำเนินการ.
> 📁 **ที่เก็บไฟล์ไม่ต้องถาม — ไฟล์ที่ส่งมอบจะอยู่ใน `~/Downloads/` เสมอ ไม่สร้างโฟลเดอร์ย่อย** แจ้งให้ผู้ใช้ทราบพร้อมรูปแบบไฟล์ได้เลย (ดู Step 7 ใน `SKILL.md`)

18. **Version label** — **Default: today's date + v1.0.**

## G. Support & Troubleshooting content — *source it, or the section is skipped (ห้ามมโน)*

The template has a **Troubleshooting/FAQ** and a **Support** section. Their content is **not** invented — if no source is given, the section is **omitted**, not filled with guesses.

19. **Support / ติดต่อ** — ช่องทางช่วยเหลือที่จะลงในบท Support (อีเมล เบอร์ ทีม ลิงก์ระบบแจ้งปัญหา). **Default: none — ถ้าไม่ให้ ข้ามบท Support ไม่แต่งเอง.**
20. **Troubleshooting / FAQ source** — มีแหล่งบอกปัญหาที่พบบ่อย + วิธีแก้เบื้องต้น (เอกสาร / Confluence / รายการ known issues) หรือไม่? เนื้อหาบทนี้มาจากแหล่งนี้เท่านั้น. **Default: none — ถ้าไม่มีแหล่ง ข้ามบท Troubleshooting/FAQ ห้ามมโนปัญหา/วิธีแก้ขึ้นเอง.**

## Confirmation Gate — before any screenshot or drafting

Print a summary table of **every** answer:

| Field | Value |
|-------|-------|
| System / URL | … |
| Login provided? / VPN | … (never print the actual password) |
| Step sources (Confluence/spec/…) | … |
| Reference doc | … |
| Audience / Scope / Depth | … |
| การแบ่งเล่ม (role / ระบบ / เล่มเดียว) + รายชื่อเล่ม | … |
| Screenshots + annotation | … |
| เครื่องมือที่ต้องใช้ | ผลจาก `scripts/preflight.sh --check` — ตัวไหนพร้อม/ตัวไหนจะติดตั้งให้ + ขนาดที่ต้องโหลด (เว้นว่างถ้าไม่ทำ screenshot) |
| Font & size / Numbering | … |
| Locked terms | … |
| Support / FAQ source (or "ข้าม") | … |
| Output format / Version | … |

Then ask, verbatim: **"ยืนยันข้อมูลทั้งหมดถูกต้อง และเริ่มดำเนินการได้หรือไม่"**

Do **not** proceed until the user replies with an explicit confirmation. If anything is "ไม่แน่ใจ", resolve it first.

**After confirmation → save the profile.** Once the user confirms, write the confirmed answers
(**minus every credential/secret**) to `~/.manual-maker/profiles/<slug>.json` per `profile.md`, so
the next run for this system does not re-ask. Then tell the user it was saved.
