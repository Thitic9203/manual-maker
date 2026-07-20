# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`manual-maker` is a **Claude Code plugin (skill)**, not an application. It has no build system, no tests, no CI, and no runtime code — it is Markdown (the skill) plus two JSON manifests (plugin + marketplace). The deliverable is the *behavior* Claude exhibits when the skill fires, defined entirely in `skills/manual-maker/`.

**Purpose:** produce **end-user manuals / handbooks for web systems** — step-by-step guides a non-technical reader follows to operate a system (access & login → each feature, with annotated screenshots), exported to Confluence / PDF / Word / web. Everything in this repo exists to make those manuals **accurate, consistent, and professionally written**; judge changes by whether they improve that outcome.

## Core architecture: wrapper-delegate (read before changing anything)

This is the one concept that requires reading multiple files to grasp, and it constrains every change:

**The skill does not write documents itself.** It is a thin team wrapper that *composes* Anthropic's first-party skills instead of reimplementing or forking them. At runtime it delegates:

- **Drafting** → the `doc-coauthoring` skill (via the Skill tool)
- **Export** → `docx` / `pdf` / `web-artifacts-builder` skills
- **Screenshots** → Playwright or Chrome MCP
- **Publishing** → Atlassian MCP (`createConfluencePage` / `updateConfluencePage`)

The invariant that follows: **no third-party (Anthropic) skill content is ever copied into this repo.** That is deliberate — it keeps the repo publishable/public, low-maintenance, and automatically benefiting from upstream skill updates. When adding capability, prefer delegating to an existing first-party skill over writing new prose/logic here. Do not paste another skill's content in.

## Where behavior lives — edit these, not code

The skill's entire behavior is three Markdown files:

- `skills/manual-maker/SKILL.md` — the workflow orchestration: `Intake → Confirm → Ingest sources → (Screenshots) → Draft → Template + quality → Final review → Export`, and which tool/skill owns each step. The `description:` frontmatter is what makes the skill auto-trigger (English + Thai trigger phrases) — edit it to change *when* the skill fires.
- `skills/manual-maker/references/intake.md` — the question set the skill asks, one at a time, each with a bold default. Editing this changes *what inputs* every manual collects. This is the primary tuning surface for a new team/system.
- `skills/manual-maker/references/template.md` — the handbook's section order, conventions, and step/screenshot format. Editing this changes the *shape and tone* of every manual produced.

There is no code path to trace; changing the skill means changing these files.

## How the skill makes a manual — the operating contract

Every manual run follows these **non-negotiable rules** (defined in `SKILL.md` + `intake.md`; keep all three behavior files consistent whenever you touch one):

1. **Never assume, never invent (ห้ามมโน).** If any input is missing, vague, or unclear — stop and ask. Never guess a system step, a term, a font, a number, or the scope.
2. **Confirm before starting.** After intake, summarize every answer in a table and wait for the user's **explicit "go"** before any screenshot or drafting. No silent starts.
3. **Every step is sourced, not guessed.** Content comes from the live system **plus** a user-supplied authoritative source (Confluence page / spec / flow / example doc). If a step can't be sourced → ask.
4. **Stay in scope (ห้ามทำเกินขอบเขต).** Document only what was asked; don't add modules, inject opinions, or decide on the user's behalf.
5. **Credentials are in-session only.** Login details reach the screens for screenshots and are **never** written into the manual, repo, logs, or printed back; ask for them fresh each run.
6. **Detailed final review before delivery.** Run the checklist in `template.md` line by line; deliver only when nothing is missing, wrong, or inconsistent.

Runtime flow: `Intake (one question at a time) → Confirmation gate → Ingest sources → Screenshots (optional, annotated) → Draft (doc-coauthoring) → Apply template + quality → Final review → Export/publish`.

## Preflight — the skill installs its own tooling (v0.15.0+)

`skills/manual-maker/scripts/preflight.sh` exists because **the user does not know a capture run needs anything.** It runs `--check` during intake (read-only; its table becomes the *เครื่องมือที่ต้องใช้* row of the Step 2 summary, with download sizes) and `--install` immediately after the user's existing "go" — deliberately **no second gate**, since the confirmation gate already covers it. Skipped entirely when screenshots = no, so a text-only manual downloads nothing.

Everything lands in the skill-owned sandbox **`~/.manual-maker/runtime/`** (sibling of `profiles/`), never the user's projects and never global npm. The script is idempotent — re-running on a satisfied machine is a no-op — and continues past failures rather than `set -e` aborting, so one broken tool still yields a full report.

**Both scripts must be invoked through the path resolver in `SKILL.md` (*Running this skill's scripts*) — a bare `scripts/preflight.sh` silently resolves into the user's project.** This is the one failure that actually bit a live run (ELMS, 2026-07-19): the skill's paths were written repo-relative, the run's cwd was the user's project, `scripts/preflight.sh` wasn't there, and the step got hand-improvised — while a correct, executable `preflight.sh` sat in the install the whole time. Note the trap for anyone re-auditing this: `ls scripts/` at the repo root shows only `bump-version.sh`, because the skill's scripts live at **`skills/manual-maker/scripts/`**; the file being "missing" is a path artifact, not a gap. Neither obvious shortcut works, and both were measured, not assumed: **`CLAUDE_PLUGIN_ROOT` is unset inside Bash tool calls** (only `hooks/hooks.json` gets it substituted), and the plugin cache path is **version-stamped** (`~/.claude/plugins/cache/manual-maker-dev/manual-maker/<version>/…`), so it cannot be hardcoded either — hence `ls -d … | sort -V | tail -1` with a `~/.claude/skills/manual-maker` fallback for the personal-skill install. The resolver must be inlined into the **same** Bash call as the script, since shell state does not persist between tool calls.

Two traps it closes, both **measured on a real machine, not assumed** — don't "simplify" them away:

- **`npm i -g playwright` does not work.** Node won't resolve global packages from an arbitrary cwd, so `require('playwright')` throws even when the package is installed. Hence the sandbox + `NODE_PATH="$HOME/.manual-maker/runtime/node_modules" node capture.js`. Every capture invocation must carry that `NODE_PATH`.
- **A populated `~/Library/Caches/ms-playwright/` is not proof Chromium works.** Those builds are Playwright-version-specific; the probe machine had five cached builds *and* an unusable `require`. The check asks Playwright for its own `chromium.executablePath()` and tests that path.

Pillow is pinned to **`/usr/bin/python3`** (Homebrew's `python3` usually lacks PIL) — same constraint as the annotation step in `screenshots.md`. Report rows are pipe-delimited, not column-padded: `printf` pads by byte count and Thai + emoji make byte width ≠ display width.

## The delivery gate — รีวิว 5 ชั้น (v0.16.0+)

`references/review.md` is the hard stop before a manual reaches the user, and it replaced a flat self-assessed checklist that nothing enforced. Five layers, each needing **evidence**, each judged against the Step 2 confirmation table: **(1)** ตรงตามที่ยืนยัน · **(2)** ทุกอย่างมีที่มา · **(3)** ภาพ · **(4)** ตัวหนังสือและตัวเลข · **(5)** รูปเล่ม. Delivery requires **5/5**.

Rules that are the whole point — do not soften them: **ตรวจไม่ได้ = ไม่ผ่าน** (there is no "น่าจะผ่าน"); one FAIL means fix and **re-review all five layers**, because fixing one breaks another (adding a figure shifts step numbers); review the **exported file**, never the draft in conversation; never deliver with caveats ("ส่งก่อน เดี๋ยวแก้").

**Order matters and changed in 0.16.0: build (Step 7) → review (Step 8) → publish (Step 9).** Review used to run before export, which is backwards — the defects it most needs to catch (font fallback, dropped images, stale TOC, คำพราก) are *created* by the conversion. Confluence publishing is outward-facing, so it must never precede a passing verdict.

`scripts/verify-doc.py` settles the mechanical half (placeholders, `w:cs`, `w:lang w:bidi`, split locked terms, invisible chars, image rels, cover/header/footer/`PAGE`/TOC, heading-number continuity, credential leaks; exit 1 blocks delivery). **Passing it is not passing the review** — it cannot judge whether content matches the real system, whether a circle points at the right button, or whether the layout matches the ต้นแบบ.

**Layer 3's "เลขในวงตรงขั้นตอน 1:1" is enforced by `scripts/verify-annotations.py` (v0.20.0+) because prose did not enforce it.** A delivered manual shipped with circle ② on the control for step 3, ④ on an *alternative* path that was not a numbered step at all, and ⑤ drawn on two different figures — the circles had been placed against an earlier draft of the step list and were never re-derived when the steps were rewritten. Nothing caught it: `review.md` stated the 1:1 rule as a sentence for a human to eyeball, and `verify-doc.py` never looks at figures. The fix has two halves, and **both are required** — annotation now emits **`annotations.json`** (shape in `screenshots.md`) recording every circle's number, file, centre, and label as it is drawn, and the script checks that manifest **against the actual pixels**, so a manifest that lies about what was drawn fails. Writers each own `<section>.annotations.json` (never a shared file — that would collide exactly like a shared draft); the script takes a directory and merges, erroring if two writers claim one section.

**The semantic half was closed in 0.20.1 by pairing `label` with `step_text`, and it rests on a convention the manual already had.** `template.md` requires a step to name its control in quotes (`คลิกปุ่ม “เข้าห้องเรียน”`), so the script extracts the quoted control and requires the circle's `label` to name the same one, comparing after stripping leading role words (ปุ่ม/เมนู/แท็บ/ช่อง/ไอคอน…) so `"ปุ่มเข้าห้องเรียน"` matches `“เข้าห้องเรียน”`. **Steps that quote no control are skipped, not failed** — measured on real ELMS content, 18 of 22 steps quote a control and 4 genuinely do not (`เปิดเบราว์เซอร์ แล้วเข้าที่ https://…`, `คลิกคาบเรียนที่ต้องการในตาราง`), and a check that cannot be satisfied is worse than none.

**The one subtlety worth not re-deriving: the flagship defect lives on a step that quotes nothing, so a literal "skip when unquoted" rule would have skipped the very case the check exists for.** Circle ② carried step 2's text (`คลิกคาบเรียนที่ต้องการในตาราง` — no quoted control) but was labelled `ปุ่มเข้าห้องเรียน`, which step **3** quotes. The rule is therefore **fail on positive evidence, not on absence**: an unquoted step fails only when its label matches a control quoted by a *different step in the same section*, which is exactly the signature of circles placed against an earlier draft and never re-derived. That cross-step match needs similarity ≥ 0.60 of the label's length — without the ratio guard, a legitimate label like `คาบเรียนในตารางสอน` would collide with step 1's `“ตารางสอน”` (measured similarity 0.44, correctly below threshold).

**Do not oversell the script, and do not let anyone "simplify" its detector.** After 0.20.1 it proves numbering, placement, *and* that the circle↔step pairing is textually consistent. **What it still cannot know is whether the control the step names is the right one to click at all** — a step reading `คลิกปุ่ม “ยกเลิก”` where it should read `“บันทึก”`, with the circle honestly on ยกเลิก, passes every check because everything is internally consistent; the defect is in the *step*, which is layer 2's problem. That plus the ~1-in-5 skipped steps is why `review.md` layer 3 still demands a human table and why ตรวจไม่ได้ = ไม่ผ่าน still applies. The detector requires a **near-solid disc of the expected size** (four conditions: bbox ~2r square, aspect 0.80–1.25, fill 0.58–0.86, area within the disc band) rather than "connected red pixels", because the app's own UI is full of red — measured on the 19 real ELMS screenshots, callouts are bbox 37×37 / area 931–1001 / fill 0.68–0.73 / aspect 1.00, while red UI chrome came in at 59×20 (aspect 2.95), 38×20 (fill 0.726 — so **fill alone does not discriminate**), and a roundish 26×24 delete icon at area 325. Every decoy fails at least two conditions; a single-condition filter would not have separated them. Geometry was stable across colour tolerance 20→80 (bbox unchanged, centroid drift < 0.2 px), which is why the 25 px match radius is generous rather than tuned.

Two things here were measured, not assumed: the **คำพราก check is scoped to the locked terms**, because a naive "Thai char + space + Thai char" rule flags legitimate phrase spacing (Thai separates phrases with spaces, not words) and was almost all false positives on a fixture; and **คำพราก is a build-time bug, not a review-time one** — its causes are a space/break inside a word and a Thai run missing `w:lang w:bidi`, so `docx-build.md` requires both `w:cs` and the language tag on every Thai run. There is no local docx renderer to fall back on: Word's AppleScript `save as` is rejected (`-1708`) and LibreOffice is not installed, which is *why* the check is source-level rather than visual.

## Parallel Steps 4–6 + per-section review (v0.17.0+)

Steps 4–6 fan out: **2–3 `manual-section-writer` agents** (`agents/*.md`) each own whole **หัวข้อย่อย** — capture → annotate → draft — plus **one** `manual-section-reviewer` that reviews each หัวข้อย่อย the moment it lands. Contract: `references/parallel.md`. Rationale and trade-offs: `RISK_REGISTER.md` MM-004.

**Partition by หัวข้อย่อย, never by phase.** The tempting split ("one agent screenshots everything, another writes everything") is wrong: **"เลขในวงแดง = เลขขั้นตอน 1:1" is an invariant _inside_ a หัวข้อย่อย**, so splitting capture from drafting forces two agents to renegotiate step numbers across a boundary. Don't "optimize" it back.

**No collisions come from ownership, not etiquette.** A writer may write only `manual-assets/<slug>/<section>-*.png` and `manual-drafts/<slug>/<section>.md`; section numbers are assigned by the main thread **before** dispatch; the `.docx` is assembled only in the main thread; the reviewer is **read-only** (it reports, the owning writer fixes — a reviewer that edits collides with a live writer). Login happens **once** in the main thread and writers get a read-only `storageState`: three concurrent logins risk account lockout and spread the credential further than needed.

**Subagents cannot talk to the user — that is the whole design constraint.** Writers return `BLOCKED`; the reviewer splits findings into `FIX` (the confirmed table or locked-term list already dictates the one correct answer) and `ASK` (**everything else, and everything it is unsure about**). Only the main thread asks, in chat. A หัวข้อย่อย with an open `ASK` is not done and never reaches the file. **One** reviewer, always — several would judge terminology and tone inconsistently, which is precisely the defect they exist to catch.

**`doc-coauthoring` stays in the main thread**, called once for the document-level voice/structure contract that all writers draft against. Calling it per-writer yields three different styles.

**Per-section review is a pre-check, not the gate.** It covers layers 1–4 *at section level* only. Font fallback, คำพราก, TOC, cross-chapter numbering, and all of layer 5 are created by the conversion and provable only on the exported file — so **Step 8 is unchanged**. "Every section passed its review" is not evidence for any layer in `review.md`.

**The ~10-minute progress table rides `PostToolUse`, because Claude Code has no time-based hook.** `hooks/progress-tick.sh` (matcher `Task|Bash`) throttles on wall clock and is inert unless `~/.manual-maker/state/run.active` exists — the skill creates that marker at the Step 2 gate and deletes it at Step 9. Two things checked against the docs/machine, not assumed: **`SubagentStop` supports only `decision`/`reason`, not `hookSpecificOutput.additionalContext`**, so it cannot inject a message and is not a substitute; and `read_epoch` needs its `[ -f "$1" ]` guard because `< "$1"` on a missing file is reported by the shell *before* a trailing `2>/dev/null` applies — without it, every run's first tick printed a redirect error on stderr. Subagent tool calls fire hooks too, so the message itself tells subagents to ignore it. Consequence to keep in mind: **no tool call → no tick**, so reporting on every section status change stays the primary mechanism; the hook is only a silence net.

## Document quality standards (load-bearing — the manual is judged on these)

These live in `template.md` and are enforced in the `SKILL.md` draft + review steps. They are the point of the repo, not decoration — do not weaken them:

- **Tone & language.** Formal, professional, **human** written language — never machine-translated stiffness. **No first/second-person pronouns** (ผม / ฉัน / คุณ / ท่าน) — use the imperative or the locked role term. **No sentence-final particles** (ครับ / ค่ะ / นะ).
- **Terminology consistency.** One **locked term** per concept, used identically throughout (e.g. always "ผู้เรียน", never "นักเรียน" / "นร."). Confirm the term list with the user; if a new term appears mid-draft, ask which word to use.
- **Numbering.** Continuous decimal outline (`1`, `1.1`, `1.1.1`) — no gaps or duplicates; the table of contents matches the body.
- **Font & size.** Taken from the user's reference document or explicitly confirmed — **never assumed**; uniform across the whole manual.
- **Image clarity + annotation.** Every screenshot sharp and legible; when requested, a **box (กรอบ) + numbered marker (เลขลำดับ)** on the click target, in a consistent style throughout.
- **Output format.** Word (`.docx`) / PDF / Confluence / web — the skill **always asks which** when the user hasn't said, phrased for non-technical users.


**A name scrub that cannot fail is not a safeguard.** Screenshot name-masking happens in the DOM immediately before the shutter, and the capture **aborts** if any known name survives a re-read of `document.body.innerText`. This is not belt-and-braces: on the ELMS run the scrub ran, silently missed one account chip, and the real teacher's name reached a delivered `.docx`. The two pixel-masking alternatives were both measured and both worse — a fixed top-right box misses the chip because a `fullPage` capture renders the sticky header wherever the page was scrolled, and a "find the pale header band" heuristic matches white table rows and paints over content (nine places on one image). Names must also be **collected from the page** (the chip's own text, plus `ครู <name>` matches), because a hardcoded list cannot know the account a future run uses — that is exactly how the last leak survived three passes that each reported themselves clean. Student identifiers (`รหัสนักเรียน`, `เลขที่นักเรียน`) are masked too; an ID identifies a minor as surely as a name.

## Second skill — `confluence-docs` (v0.22.0+, this repo hosts two skills now)

The plugin is no longer single-skill. `skills/confluence-docs/` is a **sibling** of `manual-maker`,
auto-loaded the same way (Claude Code discovers every `skills/*/SKILL.md`) — **no manifest change was
needed to register it**, only a version bump so auto-update ships it. Its job is the inverse shape of
manual-maker: instead of producing one screenshot-heavy end-user handbook, it **fills a whole Confluence
doc-space's mock/placeholder pages with the real system's data**, one doc-type per run. Target space/page
are inputs; the default is NDLP's `PLUT` space (cloudId `dfc2cd04-b24b-48cf-81a1-4a3e0ed7569f`, scaffold
root page `3693641732`, four subsystems OLS/ELMS/CBMS/EvMS).

It reuses the parent's whole ethos — **ห้ามมโน · confirm-before-start · every value sourced · in-scope ·
5-layer review before publish** — and the same wrapper-delegate rule (prose drafting → `doc-coauthoring`,
no third-party skill content copied in). Design decisions that were **chosen, not defaulted**, and should
not be "simplified" away:

- **Sourcing is a per-doc-type map, and it blocks.** `references/source-map.md` pins each doc-type to a
  mandatory authoritative source (PRD ← Jira filter, API Doc ← OpenAPI/repo, Data Dictionary ← DB schema,
  Meeting notes ← real minutes…). No source → the run **stops** for that doc-type; a placeholder is never
  guessed. The map's backbone is copied from the scaffold's own "ข้อมูลหลักที่ต้องกรอก" index column.
- **Structure-preserving, not regenerating.** Pages are read and written in `contentFormat: html` (the
  round-trip-safe HTML+ format — panels, macros, tables, local IDs survive). Only placeholder *values*
  change; every column/panel/macro is kept. `verify-confluence.py --original` proves nothing structural
  was dropped. The `Subsystem` column + labels (`ols/elms/cbms/evms`) are the one cross-space convention.
- **Write is capability-gated and this was measured.** The Atlassian connector observed in-session was
  **read-only** — `getAccessibleAtlassianResources` listed only `read:page:confluence`, and no
  `updateConfluencePage`/`createConfluencePage` tool existed. So Step 0 preflights both the tool presence
  **and** the `write:page:confluence` scope, and **stops with instructions** if either is missing rather
  than faking a write. Do not assume writing works because reading does.
- **Diagrams: no file upload exists, so they are Confluence-rendered code.** Atlassian MCP cannot upload
  attachments (same limit manual-maker hit). Diagram doc-types (EA/Sequence/ER/Data Dictionary) embed a
  **Mermaid macro generated from the real source** (ER from the DB schema, sequence from the flow) and
  layer 5 **screenshots the published page** to prove it renders as a diagram, not raw code. No renderable
  macro in the space → ตรวจไม่ได้ = ไม่ผ่าน: stop and ask to install one / attach manually. See
  `references/diagrams.md`. The diagram content is never invented.
- **The 5-layer review is adapted, not the manual-maker file.** `references/review.md` keeps the
  philosophy (ตรวจไม่ได้=ไม่ผ่าน, 5/5, re-review all after a fix) but layers map to Confluence: (1) ตรงตาม
  ยืนยัน (2) ทุกค่ามีที่มา + **ไม่มี mock เหลือ** (3) โครง/ฟอแมตคงเดิม (4) ศัพท์/ตัวเลข/คำพราก (5) **render บนหน้าที่
  publish จริง**. Layers 1–4 are proven on the prepared body **before** any write; layer 5 only after
  publish — the one place publishing precedes a layer's verdict, and only that layer.
- **`scripts/verify-confluence.py`** is the mechanical half of layers 2–4: no mock/placeholder token
  survives (FEATnn, Module A, สมมติ, MOCK, `data-type="placeholder"`, the MOCK warning panel), locked
  terms not split by whitespace/tag (the Confluence คำพราก analogue — no docx renderer here to check
  visually), `Subsystem` column present, no credential/minor-identifier leak, and structure preserved vs
  `--original`. **Exit 1 blocks the write. Passing it is not passing the review** — it cannot know whether
  a filled value is the *correct* real value (layer 2 human) or whether the page renders (layer 5).

**Bare `/confluence-docs` rides the same shim mechanism as `/manual-maker`** — measured, not assumed:
plugin commands only ever resolve as `/manual-maker:confluence-docs`, so `shim/confluence-docs.md` (a
pure pointer to the skill) is copied to the un-namespaced `~/.claude/commands/` by `check-version.sh`.
That hook's `install_shim` was generalized to `install_one_shim` + a loop over **both** shims; keep it a
loop, keep each shim a pure pointer (workflow prose copied in would drift from `SKILL.md`), and keep the
install rails (managed-by marker, no-clobber, atomic, fail-silent, `MANUAL_MAKER_NO_SHIM=1` opt-out).
`shim/` stays inert to the loader — never move it under `commands/`.

## Release workflow & gotchas

There are no build/lint/test commands. The only "commands" are install and version bookkeeping.

**Never hand-edit version strings — run `scripts/bump-version.sh`.** The version lives in FOUR places that must stay in sync: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (both `metadata.version` AND `plugins[0].version`), and the README (shields badge + the `**Version …**` line). A mismatch ships a broken marketplace entry. The script updates all of them at once and stamps a `CHANGELOG.md` entry. Release: `scripts/bump-version.sh minor` (or `patch`/`major`/explicit `0.3.0`) → edit the CHANGELOG stub → commit → push. Users with auto-update on get it automatically next session; everyone else runs `/plugin marketplace update manual-maker-dev`. If you must edit versions by hand, edit *all four* spots.

**Updates are self-driven by the SessionStart hook (Path B) — a deliberate override of the old notify-only design.** The repo owner chose true zero-touch updates on the plugin path over the "correct" native route, accepting the trade-offs (see `RISK_REGISTER.md`, MM-001). Context on the native alternative, still valid and documented in the README "Update" section: Claude Code *can* auto-update third-party plugins natively, but it is **off by default** for third-party marketplaces (only Anthropic's official ones default on) and the author **cannot enable it from the repo** — it is a client-side opt-in, by security design. The native paths (per-user `/plugin` → Marketplaces → **Enable auto-update**, or team-wide `"autoUpdate": true` in `extraKnownMarketplaces`) remain the cleaner options and are offered as such. Either way, auto-update only fires when the `version` string changes — which `bump-version.sh` guarantees.

**The SessionStart hook self-updates.** `hooks/hooks.json` registers `hooks/check-version.sh`, which on every session start compares the installed `plugin.json` version to `main` on GitHub (via `curl`, 3s cap) and, if GitHub is ahead, launches `claude plugin update` **in the background** (detached, non-blocking) and tells the user via `additionalContext`; the new version applies on the next session / `/reload-plugins`. Safety rails baked in and must be preserved: fail-silent when offline/up-to-date/curl-less; **opt-out** via `MANUAL_MAKER_NO_AUTOUPDATE=1` (degrades to notify-only); notify-only degrade if `claude` is not on PATH; an atomic `mkdir` lock (stale after 10 min) prevents overlapping updates; it uses the **supported `claude plugin update` CLI, never a raw git-pull into the plugin cache**. This intentionally bypasses Claude Code's per-marketplace auto-update opt-in — do not "restore" it to notify-only without the owner's say-so; the override is recorded, not accidental. The GitHub owner/repo URL is hardcoded in the script; update it if the repo moves. **Do NOT list `hooks/hooks.json` in `plugin.json`'s `hooks` key** — Claude Code auto-loads the standard `hooks/hooks.json`, so referencing it there causes a fatal "Duplicate hooks file detected" error and the hook silently fails to load (this bit us in 0.3.0–0.4.0, fixed in 0.4.1). `manifest.hooks` is only for *additional* hook files outside the standard path.

**A disabled plugin silently freezes the self-update — check enabled status before version.** The hook only runs while the plugin is enabled, so `"manual-maker@manual-maker-dev": false` under `enabledPlugins` in `~/.claude/settings.json` breaks the loop: the hook never fires → `claude plugin update` never runs → the install stays pinned at whatever version it was disabled at, with no warning and no notification. Seen in the wild: an install sat on 0.11.0 well after 0.12.0 shipped. The tell is that the `manual-maker` skill is missing from the session's skill list entirely. Diagnose with `claude plugin list | grep -A3 'manual-maker@'`, which prints version *and* status together. Recovering takes both steps — `claude plugin enable manual-maker@manual-maker-dev` then `claude plugin update manual-maker@manual-maker-dev` — because enabling alone leaves the stale version in place until some later session's hook run catches it. Restart / `/reload-plugins` to load.

**Bare `/manual-maker` cannot come from the plugin — the `shim/` file installed by the hook is the only mechanism, and this was measured, not assumed.** Claude Code reaches plugin commands and plugin skills *only* as `/plugin-name:command-name`; bare `/manual-maker` returns `Unknown command`. Do not re-derive this from the docs — `slash-commands.md` still claims the "plugin prefix is optional unless there are name collisions" and shows `/command-name` as a direct form, and **that is wrong** for Claude Code 2.1.210. The measurement: a throwaway probe plugin (`mmprobe`) was installed with three shapes — (a) a command with no name collision anywhere, (b) a command with a frontmatter `aliases:` key, (c) a command whose name equalled both the plugin name and a sibling skill (manual-maker's exact shape) — and run headless via `claude -p`. **Every bare form returned `Unknown command`; every `/mmprobe:…` form resolved.** So the failure is not a collision and not fixable by renaming. The bundle's matcher is `e.name===t || userFacingName()===t || aliases?.includes(t)`, and plugin-sourced commands only ever carry qualified names, so no frontmatter key, manifest field, or file rename can expose the short form. Don't retry those three "obvious" fixes (rename the command, add `aliases:`, delete `skills/manual-maker/`) — all three were tested or ruled out at the implementation level, and the last one deletes the actual product. What *does* work: `~/.claude/commands/` is **not** namespaced, so `hooks/check-version.sh` copies `shim/manual-maker.md` there on session start (v0.14.0+, see `RISK_REGISTER.md` MM-003). Keep the shim a **pure pointer** that only invokes the `manual-maker:manual-maker` skill — workflow prose copied into it would silently drift from `SKILL.md`. Keep the install rails too: never overwrite a file lacking the `managed-by: manual-maker-plugin` marker, no-op when content already matches, atomic temp+`mv`, fail-silent, announce only the first install, opt out with `MANUAL_MAKER_NO_SHIM=1`. `shim/` is inert to the plugin loader (only `commands/`, `skills/`, `agents/`, `hooks/hooks.json` are auto-loaded), so it must never move under `commands/` — that would register a duplicate `/manual-maker:manual-maker`. The shim is not removed by `/plugin uninstall`.

**Marketplace name ≠ plugin name, on purpose.** The plugin is `manual-maker`; the marketplace is `manual-maker-dev`. So the install command is `/plugin install manual-maker@manual-maker-dev` and updates target `manual-maker-dev`. This intentional mismatch mirrors the team's other proven-working plugins (`helix-dev`, `retest-bug-dev`, `full-test-dev`). Don't "fix" it to match.

**The repo is its own marketplace** — `source: "./"` in `marketplace.json`. Installs come straight from GitHub (`Thitic9203/manual-maker`); there is no separate registry.

**Validate before every push.** Run `claude plugin validate <repo-path>` before pushing a manifest change. The validator (Claude Code ≥ 2.1.104) **rejects root-level `id` and `description` keys in `marketplace.json`** — keep the root to `name` / `owner` / `metadata` / `plugins` only, and nest description/version under `metadata`. The team's older manifests (`helix-dev` etc.) still carry root `id`/`description` and were grandfathered in, so don't copy them verbatim — a fresh `marketplace add` runs validation and will fail on those keys.

## Two install/distribution paths

- **Personal skill** — `cp -r skills/manual-maker ~/.claude/skills/manual-maker`. A snapshot: it does **not** auto-sync, so re-copy after every change. Skills work without the plugin system. Don't keep this alongside the installed plugin — two skills named `manual-maker` collide; pick one source.
- **Plugin, interactive** — inside a Claude Code TUI session: `/plugin marketplace add Thitic9203/manual-maker` then `/plugin install manual-maker@manual-maker-dev`. `/plugin` is a session-only slash command (not the shell, not desktop/web app).
- **Plugin, headless CLI** (no interactive `/plugin` needed) — from any shell: `claude plugin marketplace add Thitic9203/manual-maker`, `claude plugin install manual-maker@manual-maker-dev`, verify with `claude plugin list`. This is the way to install/verify outside a TUI (desktop/web app, scripts, agents). `claude plugin validate <path>` checks a manifest without installing.

Either way, changes require a restart / new session to load.

## Conventions

- **Bilingual TH/EN.** The audience is a Thai QA team; the skill defaults to Thai output, and docs/intake/template mix Thai and English intentionally. Keep new user-facing strings bilingual and preserve Thai defaults.
- **Safety is part of the spec, not a nicety.** Never record real credentials/tokens — login steps describe the *procedure* only. Screenshots navigate only user-provided URLs. Confluence/web publishing confirms the target before the first post. These rules live in SKILL.md, template.md, and README and must stay consistent across all three.
- **Free tooling only.** Everything the skill depends on is first-party/already installed — no paid services. Don't introduce a dependency that bills.
