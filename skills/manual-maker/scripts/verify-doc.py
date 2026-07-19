#!/usr/bin/env /usr/bin/python3
# -*- coding: utf-8 -*-
"""
manual-maker — mechanical verifier for a built .docx.

This covers the parts of the 5-layer review that a machine can decide, so the
human-judgement layers (sourcing, tone, visual correctness) are not diluted by
things a regex settles. It never says a manual is good — it only proves a
specific defect is absent. A clean run is necessary, never sufficient.

    verify-doc.py <file.docx> [--terms "ผู้เรียน,ครูผู้สอน"] [--annotations required|none]

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
        print("usage: verify-doc.py <file.docx> [--terms \"a,b\"] [--annotations required|none]",
              file=sys.stderr)
        return 2

    path = sys.argv[1]
    terms, annotations = [], None
    for i, a in enumerate(sys.argv):
        if a == '--terms' and i + 1 < len(sys.argv):
            terms = [t.strip() for t in sys.argv[i + 1].split(',') if t.strip()]
        if a == '--annotations' and i + 1 < len(sys.argv):
            annotations = sys.argv[i + 1].strip()

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
