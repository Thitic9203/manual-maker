# manual-maker

![version](https://img.shields.io/badge/version-0.21.0-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2)

A Claude Code plugin (skill) that turns a working web system into a finished **user handbook** — the kind an end user reads and follows step by step.

It is a thin **team wrapper** around Anthropic's first-party skills. It does not copy their content — it composes them.

**Version 0.21.0 · MIT · Claude Code plugin**

> 🔄 **อัปเดตอัตโนมัติ (v0.6.0+):** ติดตั้งครั้งเดียว จากนั้นแค่ **เปิด session ใหม่** ปลั๊กอินก็ดึงเวอร์ชันล่าสุดมาติดตั้งเองเบื้องหลัง — **ผู้ใช้ไม่ต้องกดอัปเดตหรือทำอะไรเพิ่ม.** ปิดได้ด้วย `MANUAL_MAKER_NO_AUTOUPDATE=1`. รายละเอียด → [Update](#update--อัปเดตอัตโนมัติ-auto-update).

---

## Quickstart — เรียกใช้สกิลยังไง

**1. ติดตั้ง (ครั้งเดียว)** — พิมพ์ใน Claude Code:

```
/plugin marketplace add Thitic9203/manual-maker
/plugin install manual-maker@manual-maker-dev
```

แล้ว **restart Claude Code** (หรือ `/reload-plugins`) — ครั้งเดียว จากนั้นอัปเดตเองอัตโนมัติ.

**2. เรียกใช้ — เลือกทางใดก็ได้:**

| Method | Type this | Notes |
|--------|-----------|-------|
| **Short command** | `/manual-maker ทำคู่มือระบบ <ชื่อระบบ>` | v0.14.0+ ติดตั้งให้อัตโนมัติ |
| **Full command** | `/manual-maker:manual-maker ทำคู่มือระบบ <ชื่อระบบ>` | ใช้ได้เสมอ ไม่ต้องพึ่งอะไร |
| **Natural language** | `ทำคู่มือการใช้งานระบบ <ชื่อระบบ> ให้ผู้ใช้` | สกิล trigger เอง ไม่ต้องมี `/` |

ทั้งสามทางเข้า workflow เดียวกัน — command แค่เป็นทางเรียกที่ชัดเจนและย้ำให้เดินจนจบ.

> ℹ️ **ทำไมมีสองรูปแบบ:** Claude Code บังคับ namespace ทุก plugin command เป็น `/plugin:command` เสมอ
> (กันชนกันข้าม plugin) — ปลั๊กอิน**เปิด**ชื่อสั้นเองไม่ได้ ตั้งแต่ **v0.14.0** ปลั๊กอินจึงติดตั้ง
> [shim ระดับ user](#คำสั่งสั้น-manual-maker--ติดตั้งอัตโนมัติ) ให้อัตโนมัติตอนเปิด session
> **ผู้ใช้ไม่ต้องทำอะไร และพิมพ์ `/manual-maker` ได้ตั้งแต่ session แรกที่มีปลั๊กอิน** (v0.14.1+).

**3. ตอบ intake ทีละข้อ** (ระบบ, URL, login, source ที่บอกขั้นตอนจริง, ผู้ใช้, ขอบเขต, ภาพ+การใส่กรอบ/เลข, ฟอนต์, คำศัพท์ที่ล็อก, รูปแบบผลลัพธ์) → **ยืนยันที่ตารางสรุป** → สกิลลงมือเอง: แตกงานเป็นหัวข้อย่อยให้ผู้เขียน 2–3 ตัวทำพร้อมกัน (screenshot + ร่างตามแนวของ `doc-coauthoring`) มีผู้รีวิวตรวจทีละหัวข้อย่อย → ประกอบไฟล์ → **รีวิว 5 ชั้นบนไฟล์จริง** → export (Word/PDF/Confluence/เว็บ) ให้จนจบ.

> ระหว่างทางจะมี **ตารางความคืบหน้า** ขึ้นเป็นระยะ และถ้าผู้รีวิวเจอเรื่องที่ต้องใช้ดุลพินิจ **จะถามในแชทก่อนเสมอ ไม่ตัดสินใจแทน** → [รายละเอียด](#งานขนาน--รีวิวรายหัวข้อย่อย-v0170).

> รอบถัดไปของ **ระบบเดิม** สกิลจำคำตอบเดิมให้ ถามแค่ส่วนที่เปลี่ยน (v0.8.0+). **รหัสผ่าน/บัญชีถามสดทุกครั้ง ไม่เก็บลงไฟล์.**

---

## Background — why this repo exists

The team needed a repeatable way to produce **end-user manuals** for the web systems it builds and tests (QA context: dashboards, booking flows, admin panels).

Anthropic already ships an excellent first-party skill, **`doc-coauthoring`**, that writes long-form documents well. But on its own it starts from a blank page every time and knows nothing about *our* systems or *our* handbook conventions.

Rather than fork `doc-coauthoring` and drift from upstream, this repo adds a thin layer **on top** of it:

1. A **system-specific intake** — the skill asks the right questions first (system, login, users, modules, output) so every manual starts complete and consistent.
2. A **team handbook template** — one structure and tone for every manual.
3. **Composition, not copying** — the skill delegates the actual writing to `doc-coauthoring` via the Skill tool, and delegates export to `docx` / `pdf` / `web-artifacts-builder`. No third-party content lives in this repo, so it stays free to be public and keeps benefiting from upstream updates.

## Design decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Architecture | **Wrapper-delegate** (not fork) | Keeps upstream updates, low maintenance, no third-party content in repo |
| Repo visibility | **Public** | No secrets, no Anthropic content — team installs without auth |
| Output formats | docx / PDF / Confluence / web (chosen at runtime) | Fits different audiences; **default docx** — screenshots embed reliably. Confluence via MCP publishes the page body only (no image upload), so it suits text-first pages |
| Screenshots | Optional, via Playwright / Chrome MCP | Auto-capture real UI per step |
| Tooling setup | **ไม่ต้องเตรียมอะไรเลย (v0.15.0+)** — สกิลเช็คและติดตั้งให้เอง | ผู้ใช้ไม่รู้ล่วงหน้าว่าต้องมี Playwright/Chromium/Pillow → สกิลเช็คตอน intake แล้วติดตั้งหลังกด "go" ลงกล่องแยก `~/.manual-maker/runtime/` ไม่แตะโปรเจกต์หรือ npm global. ไม่ทำ screenshot = ไม่โหลดอะไรเลย |
| Speed / parallelism | **ขนานต่อหัวข้อย่อย (v0.17.0+)** — writer 2–3 ตัว + reviewer 1 ตัว | 1 หัวข้อย่อย = 1 คนทำครบ ถ่ายภาพ+วงแดง+เขียนสเตป (กฎเลขวง=เลขขั้นตอน 1:1 อยู่ในหัวข้อ แยกคนแล้วพัง) แต่ละคนเขียนได้เฉพาะไฟล์ของหัวข้อตัวเอง จึงไม่ชนกัน · reviewer รีวิวทันทีทีละหัวข้อย่อย **เจอเรื่องต้องใช้ดุลพินิจ = ถามผู้ใช้ก่อนเสมอ** |
| Pre-delivery review | **รีวิว 5 ชั้น + gate (v0.16.0+)** — ไม่ผ่านครบ 5 ชั้น = ไม่ส่ง | ตรวจจากไฟล์ที่ export แล้ว: ตรงตามที่ยืนยัน · ทุกอย่างมีที่มา · ภาพ · เลข/คำ (รวม**คำพราก**) · รูปเล่ม. **ตรวจไม่ได้ = ไม่ผ่าน**, FAIL ข้อเดียว = รีวิวใหม่ทั้ง 5 ชั้น |
| Publishing | Confluence via Atlassian MCP | Push straight to the team space (หลังผ่าน 5/5 เท่านั้น) |
| Distribution | Repo is its own marketplace | Team installs directly from GitHub |
| Marketplace name | `manual-maker-dev` (≠ plugin name) | Mirrors the team's proven-working plugins (`helix-dev`, `retest-bug-dev`, `full-test-dev`) |

## What it does

- Runs a **structured intake** for system-specific inputs.
- Optionally **auto-captures screenshots** of the live UI.
- **Delegates writing** to the official `doc-coauthoring` skill.
- **ทำงานขนานต่อหัวข้อย่อย (v0.17.0+)** — writer 2–3 ตัวทำคนละหัวข้อย่อย + reviewer 1 ตัวรีวิวทันทีทีละหัวข้อย่อย (ดู [งานขนาน](#งานขนาน--รีวิวรายหัวข้อย่อย-v0170)).
- Applies the **team handbook template** (structure + tone).
- **ตรวจ 5 ชั้นก่อนส่ง** — ไม่ผ่านครบ 5 ชั้นบนไฟล์จริง = ไม่ส่ง.
- **Exports / publishes** to Confluence, PDF, docx, or a web page.
- **Updates itself** — ตั้งแต่ v0.6.0 พอเปิด **session ใหม่** ปลั๊กอินดึงเวอร์ชันล่าสุดมาติดตั้งเอง **ผู้ใช้ไม่ต้องทำอะไรเพิ่ม** (ดู [Update](#update--อัปเดตอัตโนมัติ-auto-update)).

## Install

Two ways — pick by need.

### Option A — personal skill (one machine, no `/plugin` needed)

Skills don't require the plugin system. In the mac Terminal, copy the skill into your personal skills directory:

```bash
cp -r skills/manual-maker ~/.claude/skills/manual-maker
```

Restart Claude Code. Note: a personal copy does **not** auto-sync with this repo — re-copy after updates.

### Option B — plugin marketplace (team distribution)

> ⚠️ **อย่าวางทั้ง 3 บรรทัดทีเดียว!**
> `claude` เป็นคำสั่ง **shell** (เปิดโปรแกรม) — ส่วน `/plugin` ต้องพิมพ์ **ข้างใน Claude Code** หลังมันเปิดแล้ว
> ทำ **ทีละขั้น** ตามนี้:

**Step 1 — ที่ mac Terminal (zsh):**

```bash
claude
```

กด Enter → รอ Claude Code เปิด
👉 หน้าจอเปลี่ยนเป็น UI มีช่องพิมพ์ = เข้ามา "ข้างใน" แล้ว

**Step 2 — พิมพ์ข้างใน Claude Code:**

```
/plugin marketplace add Thitic9203/manual-maker
```

กด Enter → รอเสร็จ

**Step 3 — พิมพ์ข้างใน Claude Code:**

```
/plugin install manual-maker@manual-maker-dev
```

กด Enter → รอเสร็จ

**Step 4 — ออกแล้วเปิด `claude` ใหม่ (restart) → เสร็จ**

💡 `/plugin` เปิดจากโฟลเดอร์ไหนก็ได้ — มันโหลดจาก GitHub เอง

### Verify it's installed

Start a new session and confirm `manual-maker` appears in your available skills — or just ask *"ทำคู่มือระบบ …"* and the intake should begin.

### Update — อัปเดตอัตโนมัติ (auto-update)

**ตั้งแต่ v0.6.0 ปลั๊กอินอัปเดตตัวเอง — ไม่ต้องทำอะไรเลย.** ทุกครั้งที่เปิด **session ใหม่** SessionStart hook เทียบเวอร์ชันที่ติดตั้ง กับล่าสุดบน `main`; ถ้ามีใหม่กว่า มันสั่ง `claude plugin update` **เบื้องหลัง** (ไม่หน่วงตอนเปิด session) แล้วบอกในแชทว่ากำลังอัปเดต. เวอร์ชันใหม่ **มีผลตอนเปิด session ถัดไป** (หรือพิมพ์ `/reload-plugins` หลังดาวน์โหลดเสร็จ).

> พูดง่ายๆ: push ขึ้น `main` (bump version) → คนที่ติดตั้งไว้แค่เปิด session ใหม่ 1–2 รอบก็ได้เวอร์ชันล่าสุดเอง.

**เงื่อนไข / รายละเอียด:**

- อัปเดตก็ต่อเมื่อ **เลข `version` เปลี่ยน** — ซึ่ง `scripts/bump-version.sh` bump ให้ทุก release อยู่แล้ว.
- ใช้คำสั่งทางการ `claude plugin update` (ไม่ได้ไปยุ่ง cache ตรงๆ) + มี lock กันอัปเดตซ้อน + เงียบเมื่อออฟไลน์/เวอร์ชันตรงกัน/ไม่มี `claude` ใน PATH.
- **มีผลกับ update ตั้งแต่ v0.6.0 เป็นต้นไป** — ของที่ติดตั้งไว้เวอร์ชันก่อนหน้าต้องอัปเดตขึ้น v0.6.0 ก่อน 1 ครั้ง (ตัว hook เก่ายังเป็นแบบแจ้งเตือน) จากนั้นเป็นอัตโนมัติทั้งหมด.

#### ปิด auto-update (ถ้าไม่อยากให้อัปเดตเอง)

ตั้ง env var — hook จะกลับไปเป็น **แจ้งเตือนอย่างเดียว**:

```bash
export MANUAL_MAKER_NO_AUTOUPDATE=1
```

> ⚠️ auto-update นี้เป็นการ **opt-in แทนผู้ใช้** (โดยปกติ Claude Code ตั้งใจให้ผู้ใช้เปิดเอง เพื่อความปลอดภัย). ปลั๊กอินที่รันโค้ดใหม่จาก GitHub เองอัตโนมัติทุก release คือ trade-off ที่รับรู้ไว้แล้ว — ดู `RISK_REGISTER.md` (MM-001). ถ้าไม่สบายใจ ใช้ opt-out ด้านบน แล้วอัปเดตเองแบบ manual.

#### ทางเลือกที่ "ถูกวิธี" กว่า — native auto-update ของ Claude Code

ถ้าอยากเลี่ยง hook ที่อัปเดตตัวเอง ใช้ auto-update ในตัวของ Claude Code แทนได้ (ปิด hook ด้วย env ด้านบน แล้วเปิดอันนี้):

- **ต่อคน ครั้งเดียว:** `/plugin` → แท็บ **Marketplaces** → `manual-maker-dev` → **Enable auto-update**.
- **ทั้งทีมทีเดียว:** ใส่ `"autoUpdate": true` ใน `extraKnownMarketplaces` ของ `settings.json` ที่ทีมใช้ร่วม:
  ```jsonc
  {
    "extraKnownMarketplaces": {
      "manual-maker-dev": {
        "source": { "source": "github", "repo": "Thitic9203/manual-maker" },
        "autoUpdate": true
      }
    },
    "enabledPlugins": { "manual-maker@manual-maker-dev": true }
  }
  ```

(marketplace บุคคลที่สาม native auto-update **ปิดเป็นค่าเริ่มต้น** — เฉพาะของทางการ Anthropic ที่เปิดให้ default.)

#### อัปเดตเองแบบ manual

- **ใน Claude Code (TUI):** `/plugin marketplace update manual-maker-dev` → `/reload-plugins` หรือเปิด session ใหม่.
- **นอก TUI (desktop/web app / shell):**
  ```bash
  claude plugin marketplace update manual-maker-dev
  claude plugin update manual-maker@manual-maker-dev
  ```
  แล้ว restart.
- **Personal skill (Option A):** re-copy → `cp -r skills/manual-maker ~/.claude/skills/manual-maker` (Option A ไม่มี auto-update — ต้อง re-copy เองทุกครั้ง).

> 💡 GitHub raw CDN cache ~5 นาที — เพิ่ง release เสร็จ hook อาจยังไม่เห็นเวอร์ชันใหม่ทันที รอ ~5 นาทีแล้วเปิด session ใหม่.

### Uninstall

- **Plugin:** พิมพ์ข้างใน Claude Code → `/plugin uninstall manual-maker@manual-maker-dev`.
- **Personal skill:** `rm -rf ~/.claude/skills/manual-maker`.
- **Shim คำสั่งสั้น:** `rm ~/.claude/commands/manual-maker.md` — ไฟล์นี้อยู่นอกระบบปลั๊กอิน
  `/plugin uninstall` จึง**ไม่ลบให้** ถ้าไม่ลบ `/manual-maker` จะยังอยู่แต่ฟ้องว่าหาปลั๊กอินไม่เจอ.

## Use

Ask for a manual, e.g.:

- "ทำคู่มือการใช้งานระบบ Admin Dashboard ให้ผู้ใช้"
- "create a user manual for the booking system"

### `/manual-maker` — one-shot, drives to the end

Prefer a single explicit entry point? Run the command with the system in one line:

```
/manual-maker ทำคู่มือระบบ Admin Dashboard
/manual-maker:manual-maker create a manual for the booking system
```

> **Both forms work; they are not the same mechanism.** `/manual-maker:manual-maker` is the plugin
> command itself and always works. Bare `/manual-maker` works via the user-level shim the plugin
> installs for you (v0.14.0+) — Claude Code namespaces *every* plugin command as
> `/plugin-name:command-name` by design, and **no** frontmatter key, alias, or manifest field lets a
> plugin expose the short form; only a file in `~/.claude/commands/` can. Details and opt-out:
> [คำสั่งสั้น](#คำสั่งสั้น-manual-maker--ติดตั้งอัตโนมัติ).

The command lays out the full run as a checklist and **auto-advances through every step** — intake → confirm → sources → screenshots → draft → template → review → export — so you don't have to nudge it between steps. It still **pauses at the three gates that keep a manual honest**: it asks the intake questions one at a time, waits for your confirmation before screenshots/drafting, and confirms the target before any Confluence/web publish. Momentum is automated; the correctness gates are not. (The natural-language triggers above still work exactly the same — the command is just an explicit `/` path.)

#### คำสั่งสั้น `/manual-maker` — ติดตั้งอัตโนมัติ

**ตั้งแต่ v0.14.0 ไม่ต้องทำอะไรเอง.** ตอนเปิด session ปลั๊กอินจะก๊อป `shim/manual-maker.md` ไปไว้ที่
`~/.claude/commands/manual-maker.md` ให้ — คำสั่งระดับ **user** ไม่ถูก namespace จึงเรียก
`/manual-maker` สั้นๆ ได้ทุก project ในเครื่องนั้น.

**session แรกก็ใช้ได้ (v0.14.1+).** Claude Code อ่านรายชื่อคำสั่งตอน *เริ่ม* session ไฟล์ที่เพิ่งถูกวาง
จึงยังไม่อยู่ในตารางคำสั่งของ session นั้น และ `/manual-maker` จะได้ `Unknown command` — แต่ Claude Code
**ยังส่งข้อความที่ผู้ใช้พิมพ์ต่อให้สกิลเห็น** hook จึงสั่งไว้ว่าถ้าเจอกรณีนี้ให้เรียกสกิลให้เลย ผู้ใช้จึงได้ผลลัพธ์ปกติ
ไม่ต้องพิมพ์ซ้ำ ตั้งแต่ session ถัดไปคำสั่ง resolve เองตามปกติและข้อความนี้จะหายไป.

**ข้อควรรู้:**

- shim เป็น **ตัวชี้ไปหาปลั๊กอิน** ไม่ถือ logic เอง — workflow ทั้งหมดอยู่ในปลั๊กอิน จึง drift ไม่ได้
  และ hook จะรีเฟรชให้เองเมื่อไฟล์ต้นทางเปลี่ยน.
- **ไม่ทับไฟล์ของคุณ** — ถ้ามี `~/.claude/commands/manual-maker.md` ของตัวเองอยู่แล้ว (ไม่มีบรรทัด
  `managed-by: manual-maker-plugin`) hook จะไม่แตะเลย.
- shim อยู่ **นอก** ระบบปลั๊กอิน → **ไม่ถูกลบ** ตอน `/plugin uninstall` ลบเองด้วย
  `rm ~/.claude/commands/manual-maker.md`.
- **ไม่อยากได้คำสั่งลัดนี้:** ตั้ง `MANUAL_MAKER_NO_SHIM=1` แล้วลบไฟล์ทิ้ง — `/manual-maker:manual-maker`
  ยังใช้ได้ตามปกติ.
- ถ้าไม่อยากพึ่ง `/` เลย: **พิมพ์ภาษาธรรมชาติ** (`ทำคู่มือระบบ X`) สกิล trigger เองอยู่แล้ว.

<details>
<summary>ติดตั้ง shim เองแบบ manual (กรณีปิด auto ไว้ หรืออยากลงก่อนเปิด session ใหม่)</summary>

```bash
mkdir -p ~/.claude/commands
/usr/bin/curl -fsSL https://raw.githubusercontent.com/Thitic9203/manual-maker/main/shim/manual-maker.md \
  -o ~/.claude/commands/manual-maker.md
```

ใช้ `/usr/bin/curl` (curl ของ macOS) แบบเต็ม path ตั้งใจ — ถ้าเครื่องมี MacPorts/Homebrew curl อยู่ใน
PATH ก่อน มันมักต่อ TLS กับ `raw.githubusercontent.com` ไม่ผ่านแล้วขึ้น `unable to establish a secure
connection`. บน Linux ใช้ `curl` เฉยๆ ได้ตามปกติ.

</details>

The skill interviews you one question at a time — system URL, login, VPN, **the source that describes the real steps** (Confluence page / spec / example doc), audience, scope, screenshot **annotation** (boxes + step numbers), **font & size**, numbering, and the **locked terminology** to use throughout. It then **summarizes everything and waits for your explicit confirmation** before doing anything, optionally screenshots the UI, drafts with `doc-coauthoring`, runs a **detailed final review**, and publishes to your chosen format.

> The skill never assumes: if anything is unclear it asks first, it stays within the scope you set, and credentials are used only in-session — never written into the manual or repo.

**จำคำตอบเดิมให้ ไม่ถามซ้ำ (v0.8.0+):** เคยทำคู่มือระบบไหนไปแล้ว รอบถัดไปสกิลจะโหลดคำตอบเดิมของคุณ (source, ผู้ใช้เป้าหมาย, การใส่กรอบ/เลขในภาพ, ฟอนต์/ขนาด, การนับเลข, คำศัพท์ที่ล็อก, รูปแบบผลลัพธ์) มาโชว์ แล้ว **ถามแค่ส่วนที่ขาดหรือเปลี่ยน** — เก็บแบบ per-user ที่ `~/.manual-maker/profiles/` ในเครื่องคุณเอง. **รหัสผ่าน/บัญชี/VPN ไม่ถูกบันทึกลงไฟล์เด็ดขาด — ถามสดทุกครั้ง.** ระบบยังยืนยัน URL/VPN และผ่าน Confirmation Gate ทุกครั้งเหมือนเดิม.

## How it works (runtime flow)

```
Intake  →  Confirm  →  Sources  →  ┌──────────── ขนานต่อหัวข้อย่อย ────────────┐  →  Build  →  รีวิว 5 ชั้น  →  Export
one-at-a-   gate       ต้นแบบ /     │ writer ×2–3: ถ่ายภาพ → วงแดง → เขียนสเตป │     .docx     บนไฟล์จริง      Confluence /
time Qs     ยืนยัน      Confluence   │ reviewer ×1: รีวิวทันทีทีละหัวข้อย่อย      │     ประกอบ    5/5 เท่านั้น      PDF / docx / web
                                    └──────────────────────────────────────────┘
```

## งานขนาน + รีวิวรายหัวข้อย่อย (v0.17.0)

ช่วงที่กินเวลาที่สุดของการทำคู่มือคือ **ถ่ายภาพ + เขียนขั้นตอน** ซึ่งแต่ละหัวข้อย่อยไม่ได้ขึ้นต่อกัน
ตั้งแต่ v0.17.0 ช่วงนี้จึงถูกกระจายให้ทำพร้อมกัน

**หน่วยของงานคือหัวข้อย่อย ไม่ใช่เฟส** — ผู้เขียนหนึ่งคนทำหัวข้อย่อยหนึ่งหัวข้อ **ครบวงจร**
(ถ่ายภาพ → วงแดง → เขียนขั้นตอน) ไม่แยกเป็น "คนถ่ายรูป" กับ "คนเขียน" เพราะกฎ
**เลขในวงแดง = เลขขั้นตอน 1:1** เป็นข้อผูกภายในหัวข้อย่อย แยกคนเมื่อไรกฎนี้พังทันที

| Work | Owner |
|------|-------|
| Capture + annotate + draft steps | `manual-section-writer` **2–3 ตัว** คนละหัวข้อย่อย |
| Review each subsection as it lands | `manual-section-reviewer` **1 ตัว** (อ่านอย่างเดียว) |
| Login · sources · assembly · 5-layer review · publish | thread หลัก |

**ไม่ชนกัน** — ผู้เขียนแต่ละคนเขียนได้เฉพาะไฟล์ของหัวข้อตัวเอง
(`manual-assets/<slug>/<section>-*.png` และ `manual-drafts/<slug>/<section>.md`) เลขหัวข้อถูกแจกก่อนเริ่ม
ไฟล์ `.docx` ประกอบใน thread หลักที่เดียว และล็อกอิน **ครั้งเดียว** แล้วแชร์เซสชันแบบอ่านอย่างเดียว
(ไม่ให้ล็อกอินพร้อมกันหลายตัว — เสี่ยงบัญชีโดนล็อก และรหัสผ่านไม่กระจายเกินจำเป็น)

**เจอเรื่องไม่ชัด = ถามก่อนเสมอ** — subagent คุยกับผู้ใช้ไม่ได้ ผู้เขียนที่หาแหล่งอ้างอิงไม่เจอจะหยุดแล้วส่งคำถามกลับ
ส่วนผู้รีวิวแยกสิ่งที่เจอเป็นสองกอง: **แก้เองได้** (ตารางยืนยันหรือรายการคำล็อกระบุคำตอบเดียวไว้แล้ว เช่นใช้คำนอกรายการ
มีคำลงท้าย ครับ/ค่ะ placeholder ค้าง) กับ **ต้องถาม** (ทุกอย่างที่เหลือ **และทุกกรณีที่ไม่แน่ใจ**)
คำถามทั้งหมดเด้งขึ้นแชทให้ตอบ — **ไม่มีการเดาแทน** และหัวข้อย่อยที่ยังมีคำถามค้าง **ไม่นับว่าเสร็จ** ไม่ถูกเอาไปประกอบไฟล์

**ไม่ได้ลดการตรวจ** — รีวิวรายหัวข้อย่อยครอบได้แค่ระดับหัวข้อ ส่วนข้อผิดที่เกิดตอนแปลงเป็นไฟล์
(ฟอนต์เพี้ยน คำพราก รูปหลุด TOC ไม่ตรง เลขข้ามบท ปก/header/footer) ยังต้องพิสูจน์บนไฟล์จริง
**รีวิว 5 ชั้นก่อนส่งมอบจึงยังทำครบเหมือนเดิมทุกข้อ**

### รายงานความคืบหน้าอัตโนมัติ

ระหว่างช่วงที่งานอยู่ในมือ subagent ผู้ใช้จะมองไม่เห็นว่าเกิดอะไรขึ้น สกิลจึงรายงานเป็นตาราง
**ทุกครั้งที่หัวข้อย่อยเปลี่ยนสถานะ และอย่างน้อยทุก ~10 นาที**:

```
~40% เสร็จ

| ขั้น | สถานะ |
|---|---|
| Intake / ยืนยัน / อ่านแหล่ง | ✅ เสร็จ |
| จับภาพ | 🟡 17 ไฟล์ — เล่มครูครบ, เล่มผู้เรียนเหลือ 3 หัวข้อ |
| ปิดชื่อ + วงแดงมีเลข | ⬜ ยังไม่เริ่ม |
| ร่างเนื้อหา | ⬜ |
| ประกอบ .docx 2 เล่ม | ⬜ |
| ตรวจ + ส่งมอบ | ⬜ |
```

> ℹ️ Claude Code **ไม่มี hook แบบตั้งเวลา** ตัวเตือนจึงเกาะจังหวะ tool call แล้วคุมด้วยนาฬิกา
> ผลคือ *อย่างช้าไม่เกิน ~10 นาทีระหว่างที่งานยังเดินอยู่* ไม่ใช่ตรงเป๊ะทุก 10 นาที
> ตัวเตือนทำงานเฉพาะระหว่างมีรอบทำคู่มือจริงเท่านั้น นอกนั้นเงียบสนิท

ปรับได้ด้วย environment variable:

| Variable | Effect |
|----------|--------|
| `MANUAL_MAKER_NO_PROGRESS=1` | ปิดตัวเตือนความคืบหน้า (สกิลยังรายงานตอนหัวข้อย่อยเปลี่ยนสถานะตามปกติ) |
| `MANUAL_MAKER_PROGRESS_INTERVAL=<seconds>` | เปลี่ยนช่วงเวลา (ค่าเริ่มต้น `600` = 10 นาที, ต่ำสุด 60) |

## Customize for your team

The whole point of the wrapper is that you tune it — **no code, just two Markdown files**:

- `skills/manual-maker/references/intake.md` — the questions the skill asks. Add fields specific to your systems (environment, tenant, role matrix), change defaults, drop what you don't need.
- `skills/manual-maker/references/template.md` — the handbook structure, section order, tone, and step/screenshot conventions.

After editing, **release with one command** — never hand-edit version strings:

```bash
scripts/bump-version.sh minor   # or: patch | major | an explicit 0.3.0
```

It bumps every version location at once (`plugin.json`, `marketplace.json` ×2, the README badge + version line) and stamps a `CHANGELOG.md` entry. Then:

1. Edit the new `CHANGELOG.md` stub to describe the change.
2. Commit and push.
3. Team members on **v0.6.0+** get the new version installed automatically on their next session — the SessionStart hook self-updates in the background (see [Update](#update--อัปเดตอัตโนมัติ-auto-update)). Nothing to do. Personal-skill (Option A) users re-copy.

## Requirements

All first-party / already available in Claude Code — nothing paid:

- Skills: `doc-coauthoring`, `docx`, `pdf`, `web-artifacts-builder`
- MCP: Playwright or Chrome (screenshots), Atlassian (Confluence publish)
- The new-version check uses `curl` (ships with macOS) to read the public GitHub repo — free, no auth, no account.

## Structure

```
manual-maker/
├── .claude-plugin/
│   ├── plugin.json          # plugin manifest (name, version, description)
│   └── marketplace.json     # marketplace manifest (name: manual-maker-dev)
├── commands/
│   └── manual-maker.md      # /manual-maker:manual-maker — drives the pipeline to the end
├── shim/
│   └── manual-maker.md      # auto-copied to ~/.claude/commands/ so bare /manual-maker works
├── agents/
│   ├── manual-section-writer.md    # owns one หัวข้อย่อย: capture → annotate → draft (2–3 run at once)
│   └── manual-section-reviewer.md  # reviews each หัวข้อย่อย as it lands; read-only; asks, never decides
├── hooks/
│   ├── hooks.json           # registers the SessionStart + PostToolUse hooks
│   ├── check-version.sh     # shim install + background self-update (fail-silent)
│   └── progress-tick.sh     # ~10-min progress-table reminder during a run (fail-silent, opt-out)
├── scripts/
│   └── bump-version.sh      # bump the version everywhere in one command
├── CHANGELOG.md             # per-version history
├── RISK_REGISTER.md         # decisions with trade-offs, recorded so they aren't re-litigated
└── skills/
    └── manual-maker/
        ├── SKILL.md         # workflow: intake → confirm → sources → [parallel] → build → review → publish
        ├── scripts/
        │   ├── preflight.sh    # checks + installs capture tooling into ~/.manual-maker/runtime
        │   ├── verify-doc.py   # mechanical .docx checks; exit 1 blocks delivery
        │   └── verify-annotations.py  # red-circle numbers vs the real pixels; exit 1 blocks delivery
        └── references/
            ├── intake.md      # the system-specific question set
            ├── profile.md     # remembers a user's answers (~/.manual-maker/profiles) so it doesn't re-ask
            ├── parallel.md    # how Steps 4–6 fan out + the per-section review loop
            ├── screenshots.md # capture & annotation contract
            ├── docx-build.md  # building on a base template via OOXML
            ├── review.md      # the 5-layer delivery gate
            └── template.md    # team handbook structure + conventions
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `/plugin isn't available in this environment` | อยู่ในแอป desktop/web ไม่ใช่ CLI — `/plugin` มีเฉพาะใน terminal | รัน `claude` ใน Terminal จริง **หรือ** ใช้ Option A (personal skill) |
| Pasting all commands at once errors | `claude` เป็น shell, `/plugin` อยู่ข้างใน — วางรวมกันไม่ได้ | ทำทีละ step ตาม Option B |
| Skill does not trigger | เปิด session ก่อนติดตั้ง | Restart Claude Code / เปิด session ใหม่ |
| Skill edits have no effect | personal skill เป็น snapshot ไม่ใช่ลิงก์สด | re-copy โฟลเดอร์ หรือใช้ plugin route |
| Confluence publish fail | Atlassian MCP ไม่ต่อ / space key ผิด | ต่อ Atlassian MCP + เช็ค space key จาก intake |
| Images missing on the Confluence page | Atlassian MCP เผยแพร่ตัวหน้า ไม่อัปโหลดไฟล์ภาพ | ใช้ **.docx/PDF** (default) หรือแนบภาพเอง / อ้าง URL ภาพที่ host ไว้แล้ว |
| Screenshots not captured | Playwright/Chrome MCP ไม่ต่อ / URL ต้อง login | ต่อ MCP + เช็ค login steps ใน intake; ใช้ Playwright ยิงลงดิสก์ตรง (fallback = คัดลอกจอ) |
| Work is not running in parallel | ยังเป็น session เก่า (agent โหลดตอนเปิด session) **หรือ** รอบนั้นมีหัวข้อย่อยเดียว (ไม่แตกโดยตั้งใจ) | เปิด session ใหม่; เช็คว่า `manual-section-writer` / `manual-section-reviewer` อยู่ในลิสต์ agent |
| No progress table appears | ตัวเตือนเกาะจังหวะ tool call — ช่วงที่ไม่มี tool call เลยจะไม่ยิง **หรือ** ถูกปิดด้วย `MANUAL_MAKER_NO_PROGRESS=1` | ปกติ ไม่ใช่ error; สกิลยังรายงานตอนหัวข้อย่อยเปลี่ยนสถานะ. สั่ง "ขอสรุปความคืบหน้า" ได้ตลอด |
| Frequent questions during a run | ผู้รีวิวเจอเรื่องที่ตารางยืนยันไม่ได้ระบุ — **ตั้งใจให้ถาม ไม่ให้เดา** | ตอบให้ชัดครั้งเดียว; ลดคำถามรอบหน้าได้ด้วยการให้ **source + รายการคำล็อก** ครบตั้งแต่ intake |

## Safety

- No secrets in output or repo — login steps describe the *procedure*, never real credentials.
- **ล็อกอินครั้งเดียวใน thread หลัก** แล้วแชร์เป็นเซสชันอ่านอย่างเดียวให้ผู้เขียน — subagent ไม่เห็นรหัสผ่านดิบ และไม่ล็อกอินเอง.
- Screenshots navigate only user-provided URLs.
- Confluence / web publishing asks for confirmation before posting.
- **Subagent ไม่มีสิทธิ์ตัดสินใจแทนผู้ใช้** — ทุกจุดที่ไม่ชัดจะถูกส่งกลับมาถามในแชทก่อนเสมอ.

## License

MIT
