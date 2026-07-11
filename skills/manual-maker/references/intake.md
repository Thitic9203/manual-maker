# Intake Questions

Ask these **one at a time**, in order. Where an answer has a **bold default**, offer it. Where it says *(ต้องถาม — no default)*, **never assume** — keep asking until the user gives an explicit, clear answer.

**How to ask:** พูดกับผู้ใช้เป็น **ภาษาไทยที่เป็นทางการ สุภาพ มืออาชีพ** (ตามค่าเริ่มต้น) — สะกดถูกต้อง เลือกใช้คำให้เหมาะสม ถามทีละข้อ ไม่รวบหลายคำถามในครั้งเดียว หลีกเลี่ยงคำลงท้าย (ครับ/ค่ะ) และสรรพนามที่ไม่จำเป็น ให้ข้อความกระชับ ชัดเจน เป็นธรรมชาติ

## Golden rules for this skill

- **ห้ามมโน / ห้ามคิดเอง.** If any answer is missing, vague, or you are unsure — STOP and ask again until you get explicit confirmation. Never guess system steps, scope, wording, fonts, or numbering.
- **ห้ามทำเกินขอบเขต.** Document only what was asked. No extra modules, no opinions, no "while I'm here" additions, no deciding on the user's behalf.
- **ยืนยันก่อนเริ่มเสมอ.** After intake, summarize everything and get an explicit "go" before any screenshot or drafting (see the Confirmation Gate at the end).

## A. System & access  — *ask fresh every time; do not reuse old answers*

1. **System name** — which system, and what is it in one line? *(ต้องถาม)*
2. **URL(s)** to document. *(ต้องถาม — ask every time, even if a URL was used before)*
3. **Login** — email/username + password needed to reach the screens. *(ต้องถาม)*
   > 🔐 Credentials are used **only in this session** to open the system for screenshots. They are **never** written into the manual, the repo, logs, or any file. Ask the user to paste them at that moment.
4. **VPN** — does access need a VPN, and is it connected yet? *(ต้องถาม — confirm before trying the URL)*

## B. Source material — so the content is accurate, not guessed  (*ห้ามมโน*)

5. **Authoritative source of how the system works** — is there a **Confluence page, spec, flow diagram, existing manual, or example document** that clearly describes the steps? Ask for the links/files. Every step in the manual must come from these sources **plus** the live system — **never** from assumption. If none exists and a step is unclear → ask the user. *(ต้องถาม — get links/files or an explicit "none")*
6. **Reference / example document to match** (layout, font, section structure)? If yes, ask the user to share the file now; the skill reads it to copy the format and terminology. **Default: none.**

## C. Audience & scope

7. **Target users** — role + tech level. **Default: non-technical end users.**
8. **Scope** — which modules/features to cover. **Default: all main user-facing features.**
9. **Depth** — overview, or exhaustive step-by-step? **Default: step-by-step for core tasks.**

## D. Screenshots

10. **Capture** — auto-capture from the live system (Playwright/Chrome), user-provided images, or none? **Default: auto-capture.**
11. **Annotation** — draw **กรอบ (boxes) / เลขลำดับขั้นตอน (numbered markers)** on the click target in each screenshot? If yes, confirm the style (box colour, marker position). *(ต้องถาม — recommended: red box + numbered marker per action, but confirm)*

## E. Formatting & terminology  — *be exact; this is where quality is won or lost*

12. **Font & size** — follow the reference document, or specify (heading vs body sizes)? *(ต้องถาม — take from the reference doc or ask; never assume a font)*
13. **Numbering** — scheme for sections and steps (e.g. `1`, `1.1`, `1.1.1`). **Default: follow the reference doc; otherwise a decimal outline, continuous with no gaps.**
14. **Terminology to lock** — the key terms and the **exact word** to use everywhere (e.g. always "ผู้เรียน", never "นักเรียน"/"นร."). Build the term list and read it back for confirmation. If unsure about any word → ask before writing. *(ต้องถาม — confirm the locked term list)*
15. **Language** — which language for the manual? **Default: Thai.**
    > **โทนของเอกสารถูกกำหนดไว้แล้ว (ไม่ต้องถาม แต่แจ้งให้ผู้ใช้ทราบ):** ภาษาเขียนที่เป็นทางการ สุภาพ มืออาชีพ อ่านลื่น เป็นธรรมชาติ (ไม่ใช่สำนวนแปลด้วยเครื่อง) — **ไม่ใช้สรรพนามบุรุษที่ 1/2** (ผม ฉัน ดิฉัน เรา คุณ ท่าน) และ **ไม่ใช้คำลงท้าย** (ครับ ค่ะ นะ). ดูรายละเอียดใน `template.md`.

## F. Output

16. **Output format — ต้องถามเสมอ ถ้าผู้ใช้ยังไม่ระบุ:** ต้องการไฟล์รูปแบบใด — **ไฟล์ Word (.docx) / PDF / Confluence / หน้าเว็บ**? ถ้าเลือก Confluence ให้ระบุ space + หน้าแม่ที่จะเผยแพร่. **Default: Confluence** (แต่หากผู้ใช้ไม่ได้บอก ให้ถามให้ชัดว่าต้องการ Word, PDF หรือรูปแบบอื่น ก่อนดำเนินการ)
17. **Version label** — **Default: today's date + v1.0.**

## Confirmation Gate — before any screenshot or drafting

Print a summary table of **every** answer:

| Field | Value |
|-------|-------|
| System / URL | … |
| Login provided? / VPN | … (never print the actual password) |
| Step sources (Confluence/spec/…) | … |
| Reference doc | … |
| Audience / Scope / Depth | … |
| Screenshots + annotation | … |
| Font & size / Numbering | … |
| Locked terms | … |
| Output format / Version | … |

Then ask, verbatim: **"ยืนยันข้อมูลทั้งหมดถูกต้อง และเริ่มดำเนินการได้หรือไม่"**

Do **not** proceed until the user replies with an explicit confirmation. If anything is "ไม่แน่ใจ", resolve it first.
