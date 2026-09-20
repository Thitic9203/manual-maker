# Second skill — `confluence-docs` (v0.22.0+, this repo hosts two skills now)

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
- **Two deliberate exceptions to structure-preservation (v0.26.0+), each a mechanical gate.** Both were
  team feedback, both proven on RED/GREEN fixtures (not real pages). **(a) Table column headers are always
  English + bold.** A Thai scaffold header (`ฟีเจอร์`, `เนื้อหา`…) is *translated* to English and wrapped in
  `<strong>`; column **count and order are still preserved**, only the header word changes. This is why
  `check_structure`'s `--original` comparison had to move from **exact header-text-set equality to `<th>`
  count** — a translated header would otherwise register as a "dropped column". The new
  `check_table_headers` FAILs any header still containing a Thai codepoint (`[฀-๿]`) or lacking
  `<strong>/<b>`; it fires whenever a `<table>` exists, warns (not fails) when a table has no `<th>` to
  judge. What it *cannot* know — whether `ฟีเจอร์→Feature` is the *correct* translation — stays layer-3
  human, exactly like "วงชี้ปุ่มที่ถูกไหม". **(b) The standalone page-level `SUBSYSTEM: <X>` badge is
  removed** (redundant with the page title `[EvMS] …` + labels + the in-table `Subsystem` column).
  `check_subsystem_badge` matches on the **colon+value shape** (`subsystem\s*:\s*(ols|elms|cbms|evms)`), so
  it FAILs the badge but never the bare `<th>Subsystem</th>` column header — that distinction is the whole
  reason the regex is false-positive-free. The in-table Subsystem convention is untouched.
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
- **Diagrams must be white-background only — a 5-layer defense (v0.24.1/0.24.2), because nothing checked it.**
  Mermaid's stock theme tints its own output — `note` blocks render **yellow**, actors/activation lavender —
  and a delivered EvMS sequence diagram shipped with exactly that yellow. The fix is not "pick a nicer theme":
  it is a white-only palette pinned per diagram plus five layers, split across the two owners the skill already
  has. **(1)** authoring — every Mermaid source opens with a mandatory `%%{init:{'theme':'base',…white…}}%%`
  directive (`diagrams.md` item 3), bans `style`/`classDef`/`fill:` backgrounds and the pre-baked
  `forest`/`neutral`/`dark`/`default` themes; **(2)** drafting-agent self-check before write; **(3)** the
  enforceable gate — `verify-confluence.py`'s `check_diagrams` (exit 1 blocks the write); **(4)** the layer-5
  rendered-page screenshot; **(5)** the layer-5 human row + re-review-all-on-fix. The load-bearing idea in
  check 3 is that the mandated palette is **white/black/grey only, i.e. every hex is greyscale (R==G==B)**, so
  the mechanical rule is exact and false-positive-free: inside each Mermaid block (scoped to CDATA /
  `<ac:plain-text-body>` / `<pre>` so unrelated Confluence panel colours aren't scanned) **every hex must be
  greyscale and the white-init directive must be present**; a yellow `#fff5ad` or lavender `#ECECFF` is R≠G≠B
  and fails. Proven on RED/GREEN fixtures, not real pages. **What it cannot know** (say so, don't oversell): it
  proves the *source* is clean, never that the *rendered* pixels are white — a macro could ignore the
  directive, and it only sees Mermaid stored in those three forms. That gap is exactly why layers 4–5
  (screenshot + human) stay mandatory and ตรวจไม่ได้ = ไม่ผ่าน still applies.
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

