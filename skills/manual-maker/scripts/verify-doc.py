#!/usr/bin/env /usr/bin/python3
# -*- coding: utf-8 -*-
"""
manual-maker — mechanical verifier for a built .docx.

This covers the parts of the 5-layer review that a machine can decide, so the
human-judgement layers (sourcing, tone, visual correctness) are not diluted by
things a regex settles. It never says a manual is good — it only proves a
specific defect is absent. A clean run is necessary, never sufficient.

    verify-doc.py <file.docx> [--terms "ผู้เรียน,ครูผู้สอน"] [--annotations required|none]
                  [--captions required] [--thai-distribute required]

Exit 0 = no mechanical defect found. Exit 1 = at least one FAIL (do not deliver).

Pinned to /usr/bin/python3 — stdlib only (zipfile + re), same interpreter that
carries PIL for the annotation step.
"""

import re
import sys
import zipfile

THAI = re.compile(r'[฀-๿]')
THAI_CONSONANT = r'ก-ฮ'
INVISIBLE = {'​': 'ZERO WIDTH SPACE', '­': 'SOFT HYPHEN', '‌': 'ZWNJ'}

results = []   # (id, name, state, detail)


def add(cid, name, state, detail=""):
    results.append((cid, name, state, detail))


def text_of(xml_fragment):
    return ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', xml_fragment, re.S))


def main():
    if len(sys.argv) < 2:
        print("usage: verify-doc.py <file.docx> [--terms \"a,b\"] [--annotations required|none] "
              "[--captions required] [--thai-distribute required]",
              file=sys.stderr)
        return 2

    path = sys.argv[1]
    terms, annotations = [], None
    captions, thai_distribute = None, None
    for i, a in enumerate(sys.argv):
        if a == '--terms' and i + 1 < len(sys.argv):
            terms = [t.strip() for t in sys.argv[i + 1].split(',') if t.strip()]
        if a == '--annotations' and i + 1 < len(sys.argv):
            annotations = sys.argv[i + 1].strip()
        if a == '--captions' and i + 1 < len(sys.argv):
            captions = sys.argv[i + 1].strip()
        if a == '--thai-distribute' and i + 1 < len(sys.argv):
            thai_distribute = sys.argv[i + 1].strip()

    try:
        z = zipfile.ZipFile(path)
    except Exception as e:
        print(f"ไม่สามารถเปิดไฟล์: {e}", file=sys.stderr)
        return 2

    names = z.namelist()
    doc = z.read('word/document.xml').decode('utf-8', 'replace')
    body_text = text_of(doc)

    # -- 1. placeholders left behind ------------------------------------------
    stray = []
    for pat in (r'TODO', r'SCREENSHOT PLACEHOLDER', r'\[ระบุ[^\]]*\]', r'\bTBD\b',
                r'<[^<>]*ใส่[^<>]*>', r'XXX+'):
        stray += [m.group(0) for m in re.finditer(pat, body_text)]
    add("1", "ไม่มี placeholder ค้าง", "FAIL" if stray else "PASS",
        f"พบ {len(stray)} จุด: {', '.join(sorted(set(stray))[:4])}" if stray else "ไม่พบ")

    # -- 2. Thai complex-script font slot -------------------------------------
    # Miss w:cs and Word silently renders Thai in a fallback font.
    runs = re.findall(r'<w:r[ >].*?</w:r>', doc, re.S)
    thai_runs = [r for r in runs if THAI.search(text_of(r))]
    no_cs = [r for r in thai_runs if 'w:cs=' not in r and 'w:cs ' not in r]
    add("2", "ฟอนต์ไทยตั้ง w:cs ครบ", "FAIL" if no_cs else ("SKIP" if not thai_runs else "PASS"),
        f"{len(no_cs)}/{len(thai_runs)} run ไทยไม่มี w:cs — Word จะ fallback ฟอนต์"
        if no_cs else f"ตรวจ {len(thai_runs)} run ไทย")

    # -- 3. Thai line-breaking (the คำพราก root cause) ------------------------
    # Without a Thai bidi/complex-script language tag Word has no dictionary to
    # break on, so it breaks mid-word: "นัก" ends a line, "เรียน" starts the next.
    no_bidi = [r for r in thai_runs if 'w:bidi' not in r]
    add("3", "ตั้งภาษาไทยให้ Word ตัดคำถูก", "FAIL" if no_bidi else ("SKIP" if not thai_runs else "PASS"),
        f"{len(no_bidi)}/{len(thai_runs)} run ไทยไม่มี w:lang w:bidi — เสี่ยงคำพราก"
        if no_bidi else "ครบทุก run")

    # -- 4. คำพราก in the source ---------------------------------------------
    # Scoped to the locked terms on purpose: Thai uses spaces BETWEEN phrases,
    # so flagging every "Thai space Thai" would be almost all false positives.
    broken = []
    for term in terms:
        if len(term) < 4:
            continue
        for cut in range(2, len(term) - 1):
            probe = term[:cut] + ' ' + term[cut:]
            if probe in body_text:
                broken.append(probe)
    invisible_hits = [n for ch, n in INVISIBLE.items() if ch in body_text]
    hard_break = len(re.findall(r'<w:br\s*/>', doc))
    detail = []
    if broken:
        detail.append("คำถูกเว้นวรรคกลางคำ: " + ", ".join(f'"{b}"' for b in broken[:4]))
    if invisible_hits:
        detail.append("อักขระล่องหน: " + ", ".join(invisible_hits))
    add("4", "ไม่มีคำพรากในต้นฉบับ", "FAIL" if (broken or invisible_hits) else
        ("SKIP" if not terms else "PASS"),
        " / ".join(detail) if detail else
        (f"ตรวจ {len(terms)} คำล็อก, <w:br/> {hard_break} จุด" if terms
         else "ไม่ได้ส่ง --terms มา จึงข้าม"))

    # -- 5. images actually embedded ------------------------------------------
    rels = z.read('word/_rels/document.xml.rels').decode('utf-8', 'replace') \
        if 'word/_rels/document.xml.rels' in names else ''
    embeds = set(re.findall(r'r:embed="([^"]+)"', doc))
    media = {n for n in names if n.startswith('word/media/')}
    dangling = []
    for rid in embeds:
        m = re.search(r'Id="%s"[^>]*Target="([^"]+)"' % re.escape(rid), rels)
        if not m:
            dangling.append(rid)
        else:
            tgt = m.group(1).lstrip('/')
            if not tgt.startswith('word/'):
                tgt = 'word/' + tgt
            if tgt not in media:
                dangling.append(f"{rid}→{m.group(1)}")
    add("5", "รูปฝังจริงและ rel ไม่หลุด", "FAIL" if dangling else ("SKIP" if not embeds else "PASS"),
        f"อ้างรูปแต่หาไฟล์ไม่เจอ: {', '.join(dangling[:4])}" if dangling
        else f"{len(embeds)} รูป, media {len(media)} ไฟล์")

    # -- 6. cover / header / footer / TOC -------------------------------------
    has_header = any(n.startswith('word/header') for n in names)
    has_footer = any(n.startswith('word/footer') for n in names)
    footer_xml = ''.join(z.read(n).decode('utf-8', 'replace')
                         for n in names if n.startswith('word/footer'))
    has_page_field = 'PAGE' in footer_xml
    has_toc = 'TOC' in doc and 'instrText' in doc
    missing = []
    if not has_header:
        missing.append("header")
    if not has_footer:
        missing.append("footer")
    elif not has_page_field:
        missing.append("เลขหน้าใน footer (PAGE field)")
    if not has_toc:
        missing.append("TOC field")
    add("6", "ปก/header/footer/TOC ครบ", "FAIL" if missing else "PASS",
        "ขาด: " + ", ".join(missing) if missing else "ครบ (ยังต้องเทียบฟอร์แมตต้นแบบด้วยสายตา)")

    # -- 7. heading numbering continuity --------------------------------------
    tops = []
    for line in re.findall(r'<w:t[^>]*>(.*?)</w:t>', doc, re.S):
        m = re.match(r'\s*(\d+)\.\s*\S', line)
        if m:
            tops.append(int(m.group(1)))
    seq_problem = ""
    if tops:
        seen, expect = [], 1
        for n in tops:
            if n in seen:
                continue
            seen.append(n)
        for i, n in enumerate(seen, 1):
            if n != i:
                seq_problem = f"ลำดับหัวข้อสะดุดที่ {n} (คาดว่า {i}) — ลำดับที่พบ: {seen[:8]}"
                break
    add("7", "เลขหัวข้อต่อเนื่อง", "FAIL" if seq_problem else ("SKIP" if not tops else "PASS"),
        seq_problem or (f"หัวข้อระดับบน {len(set(tops))} ข้อ เรียงต่อเนื่อง" if tops
                        else "ไม่พบหัวข้อที่ขึ้นต้นด้วยเลข"))

    # -- 8. credentials must never reach the document -------------------------
    leaks = []
    for pat in (r'password\s*[:=]\s*\S+', r'passwd\s*[:=]\s*\S+',
                r'รหัสผ่าน\s*[:=]\s*\S+', r'\b(?:sk|ghp|xox[baprs])-[A-Za-z0-9_\-]{8,}',
                r'Bearer\s+[A-Za-z0-9._\-]{12,}'):
        leaks += [m.group(0)[:24] for m in re.finditer(pat, body_text, re.I)]
    add("8", "ไม่มี credential หลุด", "FAIL" if leaks else "PASS",
        f"พบ {len(leaks)} จุดต้องสงสัย" if leaks else "ไม่พบ")

    # -- annotation expectation ----------------------------------------------
    if annotations in ("required", "none"):
        n_img = len(embeds)
        if annotations == "required" and n_img == 0:
            add("9", "ต้องมีภาพประกอบตามที่ยืนยัน", "FAIL", "ผู้ใช้สั่งให้มีภาพ แต่เอกสารไม่มีรูปเลย")
        else:
            add("9", "จำนวนภาพสอดคล้องกับที่ยืนยัน", "PASS",
                f"{n_img} รูป (โหมด: {annotations}) — วงแดงถูก/ผิดต้องดูด้วยสายตา")

    # ---------------------------------------------------- 10. ระยะบรรทัดพอสำหรับภาษาไทย
    # Thai sets vowel and tone marks above and below the baseline, so a wrapped line can
    # collide with the paragraph beneath it. Two conditions are unambiguous hazards and are
    # the only ones flagged, because anything looser fires on the pristine template itself
    # (measured: a whole-document scan flagged 23 untouched TOC paragraphs that render fine):
    #   * lineRule="exact" — a fixed line box clips Thai marks outright;
    #   * a paragraph-level w:line TIGHTER than the document default — i.e. something
    #     deliberately squeezed this paragraph below the rhythm the template chose.
    def _spacing_attrs(fragment):
        m = re.search(r"<w:spacing(\s[^>]*?)?/>", fragment or "")
        return dict(re.findall(r'w:(\w+)="([^"]*)"', m.group(0))) if m else {}

    styles_xml = ""
    try:
        styles_xml = z.read("word/styles.xml").decode("utf8", "ignore")
    except Exception:
        pass
    dd = re.search(r"<w:docDefaults>.*?</w:docDefaults>", styles_xml, re.S)
    base = _spacing_attrs(dd.group(0) if dd else "")
    default_line = int(base["line"]) if base.get("line", "").isdigit() else 240

    exact, squeezed = [], []
    for m in re.finditer(r"<w:p(?:\s[^>]*)?>.*?</w:p>", doc, re.S):
        para = m.group(0)
        body = text_of(para)
        if len(body) < 40 or not re.search(r"[\u0e00-\u0e7f]", body):
            continue
        ppr = re.search(r"<w:pPr>.*?</w:pPr>", para, re.S)
        own = _spacing_attrs(ppr.group(0) if ppr else "")
        if not own:
            continue
        if own.get("lineRule") == "exact":
            exact.append(body[:40])
        elif own.get("line", "").isdigit() and int(own["line"]) < default_line:
            squeezed.append(body[:40])

    if exact or squeezed:
        bits = []
        if exact:
            bits.append(f'lineRule="exact" {len(exact)} ย่อหน้า (เช่น: {exact[0]}…)')
        if squeezed:
            bits.append(f"ตั้ง w:line แคบกว่าค่าเริ่มต้น {default_line} จำนวน {len(squeezed)} ย่อหน้า "
                        f"(เช่น: {squeezed[0]}…)")
        add("10", "ระยะบรรทัดพอสำหรับภาษาไทย", "FAIL",
            "; ".join(bits) + " — สระบน-ล่างจะถูกตัดหรือบรรทัดซ้อนกัน")
    else:
        add("10", "ระยะบรรทัดพอสำหรับภาษาไทย", "PASS",
            f"ไม่มีย่อหน้าไทยที่บีบระยะบรรทัดต่ำกว่าค่าเริ่มต้น ({default_line}) และไม่มี lineRule=exact")

    # -- 11. figure captions present (feedback: images/tables need captions) --
    # Every content figure must carry a caption ("รูปที่ N: …") so figures order
    # and cross-reference correctly. Scoped to INLINE images: anchored images are
    # decorative (cover background / logo), not content figures — counting them
    # would false-positive. Caption = a paragraph whose text starts with
    # รูปที่/ภาพที่/แผนภาพที่/Figure, or a paragraph carrying a SEQ Figure field.
    if captions == "required":
        inline_imgs = len(re.findall(r'<wp:inline[\s>]', doc))
        fig_caps = 0
        for m in re.finditer(r"<w:p(?:\s[^>]*)?>.*?</w:p>", doc, re.S):
            para = m.group(0)
            ptext = text_of(para).strip()
            if re.match(r'^(รูปที่|ภาพที่|แผนภาพที่|Figure\b)', ptext) \
                    or re.search(r'SEQ\s+(Figure|รูป|ภาพ)', para):
                fig_caps += 1
        add("11", "ทุกรูปมีคำบรรยาย (caption)",
            "FAIL" if inline_imgs > fig_caps else ("SKIP" if inline_imgs == 0 else "PASS"),
            f"รูป inline {inline_imgs} แต่พบ caption รูปเพียง {fig_caps} — บางรูปไม่มีคำบรรยาย เรียงลำดับไม่ได้"
            if inline_imgs > fig_caps else
            (f"{inline_imgs} รูป มี caption ครบ (ตารางเนื้อหาต้องตรวจ caption ด้วยตา)"
             if inline_imgs else "ไม่มีรูป inline"))

    # -- 14. content-table captions (feedback: "รูปภาพ หรือ ตาราง" → ตาราง too) --
    # Every *content* table needs a "ตารางที่ N" caption so tables order too. The
    # step-layout table is NOT a content table — exclude it by its header signature
    # (contains ภาพประกอบ together with ขั้นตอน/ลำดับ) so this never fires on a step
    # table. Same floor logic as figures: FAIL if content tables outnumber captions.
    if captions == "required":
        content_tbls = 0
        for tm in re.finditer(r"<w:tbl[ >].*?</w:tbl>", doc, re.S):
            ttext = text_of(tm.group(0))
            is_step = "ภาพประกอบ" in ttext and ("ขั้นตอน" in ttext or "ลำดับ" in ttext)
            if not is_step:
                content_tbls += 1
        tbl_caps = 0
        for m in re.finditer(r"<w:p(?:\s[^>]*)?>.*?</w:p>", doc, re.S):
            ptext = text_of(m.group(0)).strip()
            if re.match(r'^(ตารางที่|Table\b)', ptext) or re.search(r'SEQ\s+(Table|ตาราง)', m.group(0)):
                tbl_caps += 1
        add("14", "ตารางเนื้อหามีคำบรรยาย (caption)",
            "FAIL" if content_tbls > tbl_caps else ("SKIP" if content_tbls == 0 else "PASS"),
            f"ตารางเนื้อหา {content_tbls} แต่พบ caption ตารางเพียง {tbl_caps} — บางตารางไม่มีคำบรรยาย"
            if content_tbls > tbl_caps else
            (f"{content_tbls} ตารางเนื้อหา มี caption ครบ (ตารางขั้นตอนไม่นับ)"
             if content_tbls else "ไม่มีตารางเนื้อหา (ตารางขั้นตอนไม่นับ)"))

    # -- 12. Thai Distribute justification (feedback: การตัดคำใช้ Thai Distribute)
    # Authored Thai body paragraphs should justify with w:jc w:val="thaiDistribute"
    # (even Thai wrapping + margins). Conservative, false-positive-free floor: fail
    # only when there are several long Thai paragraphs and thaiDistribute is absent
    # everywhere (document AND styles) — i.e. the rule was skipped wholesale. A
    # compliant build always carries it, so this never fires on correct output.
    if thai_distribute == "required":
        long_thai = 0
        for m in re.finditer(r"<w:p(?:\s[^>]*)?>.*?</w:p>", doc, re.S):
            body = text_of(m.group(0))
            if len(re.findall(r'[฀-๿]', body)) >= 40:
                long_thai += 1
        td_hits = doc.count('w:val="thaiDistribute"') + styles_xml.count('w:val="thaiDistribute"')
        if long_thai >= 3 and td_hits == 0:
            add("12", "จัดแนว/ตัดคำแบบ Thai Distribute", "FAIL",
                f"ย่อหน้าไทยยาว {long_thai} ย่อหน้า แต่ไม่พบ w:jc w:val=\"thaiDistribute\" เลย — ยังไม่ได้ตั้ง")
        else:
            add("12", "จัดแนว/ตัดคำแบบ Thai Distribute",
                "SKIP" if long_thai < 3 else "PASS",
                f"พบ thaiDistribute {td_hits} จุด, ย่อหน้าไทยยาว {long_thai} ย่อหน้า" if long_thai >= 3
                else f"ย่อหน้าไทยยาว {long_thai} ย่อหน้า — น้อยเกินกว่าจะตัดสิน")

    # -- 13. headings auto-numbered, not double-numbered (feedback: Numbering) -
    # Feedback wants headings numbered by Word (multilevel list on the Heading
    # styles), not hand-typed. The false-positive-free half is the double-number
    # guard: a heading that has BOTH auto numbering AND a manual outline number in
    # its text is unambiguously wrong. Absence of numbering only SKIPs (a base
    # template may legitimately dictate its own scheme) with a nudge in detail.
    # Numbering counts whether it is bound on the PARAGRAPH (numPr in the <w:p>) or
    # on the STYLE (docx-build.md §3.2 recommends the style) — a style-numbered
    # heading with a hand-typed number is the likeliest real double-number, so the
    # guard must see style-level numPr too or it misses exactly that case.
    autonum_styles = set()
    for sm in re.finditer(r'<w:style\b[^>]*?w:styleId="([^"]+)"[^>]*?>(.*?)</w:style>', styles_xml, re.S):
        if '<w:numPr' in sm.group(2):
            autonum_styles.add(sm.group(1))
    heading_paras, auto_num, dbl = 0, 0, []
    for m in re.finditer(r"<w:p(?:\s[^>]*)?>.*?</w:p>", doc, re.S):
        para = m.group(0)
        pstyle = re.search(r'<w:pStyle w:val="([^"]*)"', para)
        is_heading = (pstyle and re.search(r'[Hh]eading|หัวข้อ', pstyle.group(1))) or '<w:outlineLvl' in para
        if not is_heading:
            continue
        heading_paras += 1
        has_numpr = '<w:numPr' in para or (pstyle and pstyle.group(1) in autonum_styles)
        if has_numpr:
            auto_num += 1
        if has_numpr and re.match(r'^\d+(\.\d+)*[.)]?\s', text_of(para).strip()):
            dbl.append(text_of(para).strip()[:30])
    if dbl:
        add("13", "หัวข้อใช้เลขอัตโนมัติ ไม่ซ้อนเลขมือ", "FAIL",
            f"{len(dbl)} หัวข้อมีทั้งเลขอัตโนมัติ (numPr) และเลขพิมพ์มือในข้อความ เช่น: {dbl[0]}…")
    elif heading_paras:
        add("13", "หัวข้อใช้เลขอัตโนมัติ ไม่ซ้อนเลขมือ",
            "PASS" if auto_num else "SKIP",
            f"หัวข้อ {heading_paras} ข้อ · เลขอัตโนมัติ {auto_num} ข้อ"
            + ("" if auto_num else " — ไม่พบ numPr; ถ้าไม่มีต้นแบบบังคับ ควรผูก Heading กับ multilevel list"))
    else:
        add("13", "หัวข้อใช้เลขอัตโนมัติ ไม่ซ้อนเลขมือ", "SKIP", "ไม่พบย่อหน้าที่เป็นหัวข้อ")

    # -- 15. step screenshots live inside the step table's rows (feedback 4) ---
    # The defect to prevent: walkthrough screenshots dumped outside their step
    # rows. False-positive-safe signature: a doc that HAS step tables and HAS
    # inline images but with NONE inside any table cell → images were collected
    # outside the rows. Standalone UI-orientation figures are fine, so this only
    # fires on the total-miss case, and SKIPs when there is no step table.
    step_tables = [tm.group(0) for tm in re.finditer(r"<w:tbl[ >].*?</w:tbl>", doc, re.S)
                   if "ภาพประกอบ" in text_of(tm.group(0))
                   and ("ขั้นตอน" in text_of(tm.group(0)) or "ลำดับ" in text_of(tm.group(0)))]
    inline_total = len(re.findall(r'<wp:inline[\s>]', doc))
    inline_in_cells = sum(len(re.findall(r'<wp:inline[\s>]', tc))
                          for tc in re.findall(r"<w:tc>.*?</w:tc>", doc, re.S))
    if step_tables and inline_total and inline_in_cells == 0:
        add("15", "รูปขั้นตอนอยู่ในแถวของตารางขั้นตอน", "FAIL",
            f"มีตารางขั้นตอน {len(step_tables)} และรูป {inline_total} แต่ไม่มีรูปอยู่ในเซลล์เลย "
            f"— รูปถูกวางนอกแถวขั้นตอน")
    elif step_tables:
        add("15", "รูปขั้นตอนอยู่ในแถวของตารางขั้นตอน", "PASS",
            f"ตารางขั้นตอน {len(step_tables)} · รูปในเซลล์ {inline_in_cells}/{inline_total} "
            f"(รูปนอกตารางอาจเป็นภาพแนะนำหน้าจอ — ยืนยันด้วยตา)")
    else:
        add("15", "รูปขั้นตอนอยู่ในแถวของตารางขั้นตอน", "SKIP",
            "ไม่พบตารางขั้นตอน (คู่มือข้อความล้วน หรือยังไม่ประกอบตารางขั้นตอน)")

    # ------------------------------------------------------------------ report
    print()
    print("| # | ตรวจ | ผล | รายละเอียด |")
    print("|---|---|---|---|")
    icon = {"PASS": "✅ ผ่าน", "FAIL": "❌ ไม่ผ่าน", "SKIP": "— ข้าม"}
    for cid, name, state, detail in results:
        print(f"| {cid} | {name} | {icon[state]} | {detail} |")
    print()

    failed = [r for r in results if r[2] == "FAIL"]
    if failed:
        print(f"RESULT: fail ({len(failed)} รายการ) — ห้ามส่งมอบ แก้แล้วรีวิวใหม่ทั้ง 5 ชั้น")
        return 1
    print("RESULT: pass (เฉพาะข้อที่เครื่องตรวจได้ — ชั้นที่ใช้วิจารณญาณยังต้องตรวจเอง)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
