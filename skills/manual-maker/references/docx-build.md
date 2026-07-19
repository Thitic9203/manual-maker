# Building the Word file (.docx)

## 1. The customer's base template is the deliverable — copy it exactly (ต้นแบบ)

When the user supplies a **base/ต้นแบบ `.docx`**, the manual **is** that template. Reuse, verbatim:

- the **cover** (background image + delivery/contract text),
- the **header** (agency logo + organisation line),
- the **footer** (the `PAGE` field — page numbers),
- the **table of contents** (a real `TOC` field, **grouped by role**),
- the **styles** (`Heading1`/`Heading2`/`Caption`…) and the **section structure**.

Do **not** rebuild any of these from scratch. A hand-made look-alike will be rejected — the user
asked for the template, "เลียนแบบมาเลย".

**docx-js cannot open an existing file.** To keep the shell, edit the OOXML directly:

```bash
unzip -q template.docx -d unpacked/
# edit unpacked/word/document.xml  (insert your section)
(cd unpacked && zip -Xrq ../out.docx .)
```

**Adding an image:** drop the PNG into `word/media/`, add a `<Relationship … Type=".../image"
Target="media/imageN.png"/>` to `word/_rels/document.xml.rels`, and reference it from a
`<w:drawing><wp:inline>` block. Easiest and safest: **copy an existing image block from the
template** and swap `r:embed` plus the **two** extents (`<wp:extent>` and `<a:ext>`) — recompute
`cy` from the new image's aspect ratio (`cy = cx × height / width`) or the picture will stretch.

Use `docx-js` only for documents **created from nothing**.

## 2. Chapters by role (แยกตามบทบาท)

Structure the manual by **user role**, matching the template:
**บทนำ → ครูผู้สอน → ผู้เรียน → ผู้ดูแลระบบ**. Each role is a chapter (`บทที่ N`); each task is a
numbered sub-section (`4.3 วิธี…`). The TOC groups by these chapters.

## 3. Font

**TH SarabunPSK** — body **16 pt** (`w:sz 32`), headings **18 pt bold** (`w:sz 36`) — unless the
template dictates otherwise; then follow the template.

> Thai is a **complex script**. Set **all four** `w:rFonts` slots — `w:ascii`, `w:hAnsi`,
> `w:eastAsia`, and above all **`w:cs`**. Miss `w:cs` and Word silently renders the Thai text in a
> fallback font.

### Line spacing — a wrapped Thai paragraph must not collide with the next one

`w:cs` fixes the glyphs; it does **not** fix the line box. Thai stacks vowel and tone marks above
and below the baseline, so a paragraph squeezed below the document's own default line height
overlaps the paragraph beneath it **as soon as it wraps**. Observed on a real delivery: a one-line
bullet rendered perfectly while the two-line bullet under it printed straight through its neighbour.
The defect is invisible until the text is long enough to wrap, so short test content never reveals it.

Two hazards, both flagged by `scripts/verify-doc.py` check 10:

- **`w:lineRule="exact"`** on a paragraph carrying real Thai text — a fixed line box clips the marks
  outright. (Template *spacer* paragraphs legitimately use `w:line="1" w:lineRule="exact"`; the check
  ignores them by requiring ≥ 40 Thai characters, so do not "fix" those.)
- **A paragraph-level `w:line` tighter than `docDefaults`** — something deliberately squeezed this
  paragraph below the rhythm the template chose.

When authoring a paragraph, either inherit the template's spacing untouched or set an explicit
`<w:spacing w:line="300" w:lineRule="auto"/>` with a little `w:after`. Never invent a value below the
document default. Judge inheritance, not the tag alone: most template paragraphs carry **no**
`<w:spacing>` at all and inherit a perfectly safe value from `docDefaults` — a checker that reads the
paragraph tag in isolation flags the pristine template (measured: 23 false positives on untouched
TOC entries).

### คำพราก — prevent it here, at build time

A Thai word split across two lines ("นัก" ends one line, "เรียน" starts the next) is **not** something
to fix in review — it is caused at build time, by exactly two things:

1. **A space or break inserted inside a word.** Thai puts spaces *between phrases*, never inside a
   word, so any space mid-word survives into the render as a break point. Never insert one for
   "spacing"; never let a `<w:br/>` land mid-sentence.
2. **A Thai run with no language tag.** Word breaks Thai lines using a Thai dictionary — but only
   when the run says it is Thai. Without it Word has no word boundaries and breaks anywhere.

So every Thai run carries **both** the `w:cs` font slot and the language tag:

```xml
<w:rPr>
  <w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK"
            w:eastAsia="TH SarabunPSK" w:cs="TH SarabunPSK"/>
  <w:sz w:val="32"/><w:szCs w:val="32"/>
  <w:lang w:bidi="th-TH"/>          <!-- ← ให้ Word ตัดคำไทยตามพจนานุกรม -->
</w:rPr>
```

`scripts/verify-doc.py` fails the build when either is missing (checks 3 and 4), so a manual that
would แตกคำ cannot reach the user — but the fix belongs here, not there.

## 4. Verify before delivering

- The image really is embedded: `word/media/imageN.png` exists, a relationship points at it, and the
  `<w:drawing>` block is complete.
- No template placeholder text survives (`SCREENSHOT PLACEHOLDER`, `[ระบุ…]`).
- Font, sizes, numbering, and the TOC match the template.

## 5. Word has the file open

A `~$<name>.docx` lock file means **Word is holding the document**. Writing to disk still succeeds,
but Word keeps the *old* copy in memory and will overwrite yours if the user saves. Tell the user:

1. **Close Word — do not Save.**
2. Reopen the file.
3. Answer **"Update fields?" → Yes** so the TOC, page numbers, and figure numbers refresh.
