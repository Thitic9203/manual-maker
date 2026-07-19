# manual-maker

![version](https://img.shields.io/badge/version-0.15.0-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2)

A Claude Code plugin (skill) that turns a working web system into a finished **user handbook** — the kind an end user reads and follows step by step.

It is a thin **team wrapper** around Anthropic's first-party skills. It does not copy their content — it composes them.

**Version 0.15.0 · MIT · Claude Code plugin**

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

| วิธี | พิมพ์ |
|------|-------|
| **คำสั่งสั้น** (v0.14.0+ ติดตั้งให้อัตโนมัติ) | `/manual-maker ทำคู่มือระบบ <ชื่อระบบ>` |
| **คำสั่งเต็ม** (ใช้ได้เสมอ ไม่ต้องพึ่งอะไร) | `/manual-maker:manual-maker ทำคู่มือระบบ <ชื่อระบบ>` |
| **ภาษาธรรมชาติ** (สกิล trigger เอง ไม่ต้องมี `/`) | `ทำคู่มือการใช้งานระบบ <ชื่อระบบ> ให้ผู้ใช้` |

ทั้งสามทางเข้า workflow เดียวกัน — command แค่เป็นทางเรียกที่ชัดเจนและย้ำให้เดินจนจบ.

> ℹ️ **ทำไมมีสองรูปแบบ:** Claude Code บังคับ namespace ทุก plugin command เป็น `/plugin:command` เสมอ
> (กันชนกันข้าม plugin) — ปลั๊กอิน**เปิด**ชื่อสั้นเองไม่ได้ ตั้งแต่ **v0.14.0** ปลั๊กอินจึงติดตั้ง
> [shim ระดับ user](#คำสั่งสั้น-manual-maker--ติดตั้งอัตโนมัติ) ให้อัตโนมัติตอนเปิด session
> **ผู้ใช้ไม่ต้องทำอะไร และพิมพ์ `/manual-maker` ได้ตั้งแต่ session แรกที่มีปลั๊กอิน** (v0.14.1+).

**3. ตอบ intake ทีละข้อ** (ระบบ, URL, login, source ที่บอกขั้นตอนจริง, ผู้ใช้, ขอบเขต, ภาพ+การใส่กรอบ/เลข, ฟอนต์, คำศัพท์ที่ล็อก, รูปแบบผลลัพธ์) → **ยืนยันที่ตารางสรุป** → สกิลลงมือ: screenshot → ร่างด้วย `doc-coauthoring` → รีวิวละเอียด → export (Word/PDF/Confluence/เว็บ) ให้จนจบ.

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
| เครื่องมือที่ต้องติดตั้ง | **ไม่ต้องเตรียมอะไรเลย (v0.15.0+)** — สกิลเช็คและติดตั้งให้เอง | ผู้ใช้ไม่รู้ล่วงหน้าว่าต้องมี Playwright/Chromium/Pillow → สกิลเช็คตอน intake แล้วติดตั้งหลังกด "go" ลงกล่องแยก `~/.manual-maker/runtime/` ไม่แตะโปรเจกต์หรือ npm global. ไม่ทำ screenshot = ไม่โหลดอะไรเลย |
| Publishing | Confluence via Atlassian MCP | Push straight to the team space |
| Distribution | Repo is its own marketplace | Team installs directly from GitHub |
| Marketplace name | `manual-maker-dev` (≠ plugin name) | Mirrors the team's proven-working plugins (`helix-dev`, `retest-bug-dev`, `full-test-dev`) |

## What it does

- Runs a **structured intake** for system-specific inputs.
- Optionally **auto-captures screenshots** of the live UI.
- **Delegates writing** to the official `doc-coauthoring` skill.
- Applies the **team handbook template** (structure + tone).
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
Intake  →  (Screenshots)  →  Draft            →  Template        →  Export
one-at-a-   Playwright /       delegate to         apply team         Confluence /
time Qs      Chrome MCP        doc-coauthoring     structure+tone     PDF / docx / web
```

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
├── hooks/
│   ├── hooks.json           # registers the SessionStart hook
│   └── check-version.sh     # notify-only new-version check (fail-silent)
├── scripts/
│   └── bump-version.sh      # bump the version everywhere in one command
├── CHANGELOG.md             # per-version history
└── skills/
    └── manual-maker/
        ├── SKILL.md         # workflow: intake → screenshots → draft → template → export
        └── references/
            ├── intake.md    # the system-specific question set
            ├── profile.md   # remembers a user's answers (~/.manual-maker/profiles) so it doesn't re-ask
            └── template.md  # team handbook structure + conventions
```

## Troubleshooting

| อาการ | สาเหตุ | วิธีแก้ |
|-------|--------|---------|
| `/plugin isn't available in this environment` | อยู่ในแอป desktop/web ไม่ใช่ CLI — `/plugin` มีเฉพาะใน terminal | รัน `claude` ใน Terminal จริง **หรือ** ใช้ Option A (personal skill) |
| วางคำสั่งทีเดียวแล้ว error | `claude` เป็น shell, `/plugin` อยู่ข้างใน — วางรวมกันไม่ได้ | ทำทีละ step ตาม Option B |
| Skill ไม่ trigger | เปิด session ก่อนติดตั้ง | Restart Claude Code / เปิด session ใหม่ |
| แก้ skill แล้วไม่เปลี่ยน | personal skill เป็น snapshot ไม่ใช่ลิงก์สด | re-copy โฟลเดอร์ หรือใช้ plugin route |
| Confluence publish fail | Atlassian MCP ไม่ต่อ / space key ผิด | ต่อ Atlassian MCP + เช็ค space key จาก intake |
| ภาพไม่ขึ้นใน Confluence | Atlassian MCP เผยแพร่ตัวหน้า ไม่อัปโหลดไฟล์ภาพ | ใช้ **.docx/PDF** (default) หรือแนบภาพเอง / อ้าง URL ภาพที่ host ไว้แล้ว |
| Screenshot ไม่ติด | Playwright/Chrome MCP ไม่ต่อ / URL ต้อง login | ต่อ MCP + เช็ค login steps ใน intake; ใช้ Playwright ยิงลงดิสก์ตรง (fallback = คัดลอกจอ) |

## Safety

- No secrets in output or repo — login steps describe the *procedure*, never real credentials.
- Screenshots navigate only user-provided URLs.
- Confluence / web publishing asks for confirmation before posting.

## License

MIT
