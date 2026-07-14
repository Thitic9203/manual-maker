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
