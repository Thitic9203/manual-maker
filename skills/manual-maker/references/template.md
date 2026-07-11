# Team Handbook Template

Standard structure and conventions for every user manual. doc-coauthoring drafts into this shape.

## Structure (sections, in order)

1. **หน้าปก / Cover** — system name, version, date, target audience, "who this guide is for".
2. **ภาพรวมระบบ / Overview** — what the system does, main benefits, key terms (1 short paragraph + a bullet list).
3. **เริ่มต้นใช้งาน / Getting Started** — prerequisites, how to access the URL, how to log in (procedure only), first-time setup.
4. **แนะนำหน้าจอ / UI Orientation** — a labelled screenshot of the main screen; name the key areas (nav, header, main panel).
5. **การใช้งานตามฟีเจอร์ / Feature Walkthroughs** — one subsection per module. Each: what it's for → numbered steps → screenshot per step → expected result.
6. **งานที่ทำบ่อย / Common Tasks (How-to)** — task-based recipes ("how to create X", "how to export Y"), each a short numbered flow.
7. **แก้ปัญหาเบื้องต้น / Troubleshooting & FAQ** — common errors, what they mean, how to fix; frequent questions.
8. **อภิธานศัพท์ / Glossary** — one term per concept, defined once.
9. **ติดต่อ / Support** — where to get help.

## Conventions

- **Numbered steps** for every procedure — one action per step, imperative voice.
- **Screenshot after each action step** where available; caption what to look at.
- **One term per concept** — pick a name and use it everywhere (don't mix "ตะกร้า"/"cart"/"basket").
- **Plain, polite language** matched to the audience; avoid internal jargon and dev terms.
- **Callouts** for warnings/tips: `> ⚠️ ข้อควรระวัง:` and `> 💡 เคล็ดลับ:`.
- **No real credentials, tokens, or personal data** anywhere in the manual.
- **Consistent numbering** across sections; keep the table of contents in sync.

## Example step format

```
### 5.2 สร้างรายการใหม่

1. คลิกปุ่ม **"+ สร้างใหม่"** มุมขวาบน
   ![create button](assets/05-create-01.png)
2. กรอกชื่อรายการในช่อง **ชื่อ**
3. คลิก **บันทึก**
   → ระบบแสดงข้อความ "บันทึกสำเร็จ" และรายการปรากฏในตาราง
```
