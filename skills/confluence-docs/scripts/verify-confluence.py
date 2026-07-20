#!/usr/bin/env /usr/bin/python3
# -*- coding: utf-8 -*-
"""
confluence-docs — mechanical verifier for a Confluence storage-html body.

Covers the parts of the 5-layer review a machine can decide, so the
human-judgement layers (values correct per the real system, tone, rendered
page) are not diluted by things a regex settles. It never says a page is good —
it only proves specific defects are absent. A clean run is necessary, never
sufficient.

    verify-confluence.py <prepared-body.html> [--original <original-body.html>]
                         [--terms "OLS,ELMS,CBMS,EvMS,ผู้เรียน"]

Exit 0 = no mechanical defect found. Exit 1 = at least one FAIL (do not write / do
not deliver). Exit 2 = usage error.

Pinned to /usr/bin/python3 — stdlib only (re, sys, html), the same interpreter
the rest of the toolchain uses.
"""

import html as _html
import re
import sys

results = []  # (id, name, state, detail)   state in {ok, fail, warn}


def add(cid, name, state, detail=""):
    results.append((cid, name, state, detail))


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def th_texts(body):
    return [
        _html.unescape(strip_tags(m)).strip()
        for m in re.findall(r"<th[^>]*>(.*?)</th>", body, re.S)
    ]


def data_types(body):
    # panel-warning, expand, layout, etc. — structural nodes, excluding placeholder
    return [
        d for d in re.findall(r'data-type="([^"]+)"', body) if d != "placeholder"
    ]


# ---------------------------------------------------------------- mock/placeholder tokens
MOCK_PATTERNS = [
    (r"FEAT\d+", "รหัส feature สมมติ (FEATnn)"),
    (r"\bModule\s+[A-Z]\b", "ชื่อ module สมมติ (Module A/B/…)"),
    (r"สมมติ", "คำว่า 'สมมติ'"),
    (r"(?i)\bmock\b", "คำว่า 'mock/MOCK'"),
    (r"\bTBD\b", "TBD"),
    (r"\bTODO\b", "TODO"),
    (r"\bXXX+\b", "XXX placeholder"),
    (r"\[ระบุ", "[ระบุ…]"),
    (r"(?i)lorem ipsum", "lorem ipsum"),
]

# ---------------------------------------------------------------- credentials
CRED_PATTERNS = [
    (r'(?i)pass(?:word|wd)\s*[:=]\s*\S+', "password ในเนื้อหา"),
    (r'(?i)api[_-]?key\s*[:=]\s*\S+', "api key ในเนื้อหา"),
    (r'(?i)secret\s*[:=]\s*\S+', "secret ในเนื้อหา"),
    (r'(?i)bearer\s+[A-Za-z0-9._\-]{16,}', "bearer token"),
    (r'\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.', "JWT"),
    (r'รหัสนักเรียน\s*[:=]?\s*\d', "รหัสนักเรียน (ข้อมูลเยาวชน)"),
]

INVISIBLE = {"​": "ZERO WIDTH SPACE", "­": "SOFT HYPHEN", "‌": "ZWNJ"}


def check_mock(body):
    hits = []
    for pat, label in MOCK_PATTERNS:
        found = re.findall(pat, body)
        if found:
            hits.append(f"{label} ×{len(found)}")
    if 'data-type="placeholder"' in body:
        n = body.count('data-type="placeholder"')
        hits.append(f'node placeholder ค้าง ×{n}')
    if re.search(r'data-type="panel-warning"[^>]*>.*?MOCK', body, re.S):
        hits.append("warning panel 'MOCK' ยังอยู่")
    if hits:
        add("mock", "ไม่มี mock/placeholder token", "fail", "; ".join(hits))
    else:
        add("mock", "ไม่มี mock/placeholder token", "ok")


def check_terms(body, terms):
    if not terms:
        add("terms", "locked term ไม่ถูกตัดกลาง", "ok", "ไม่ได้ส่ง --terms")
        return
    notag = strip_tags(body)
    nowhite = re.sub(r"\s+", "", notag)
    bad = []
    for t in terms:
        t = t.strip()
        if not t:
            continue
        # whitespace split: contiguous only after removing spaces
        if t not in notag and t in nowhite:
            bad.append(f"'{t}' ถูกเว้นวรรคกลางคำ")
            continue
        # block/break tag inside the term
        for i in range(1, len(t)):
            pat = (
                re.escape(t[:i])
                + r"\s*<(?:br|/p|/td|/th|/li)[^>]*>\s*"
                + re.escape(t[i:])
            )
            if re.search(pat, body):
                bad.append(f"'{t}' ถูกตัดด้วย tag กลางคำ")
                break
    if bad:
        add("terms", "locked term ไม่ถูกตัดกลาง", "fail", "; ".join(bad))
    else:
        add("terms", "locked term ไม่ถูกตัดกลาง", "ok")


def check_credentials(body):
    hits = []
    for pat, label in CRED_PATTERNS:
        if re.search(pat, body):
            hits.append(label)
    if hits:
        add("cred", "ไม่มี credential/ข้อมูลอ่อนไหวหลุด", "fail", "; ".join(hits))
    else:
        add("cred", "ไม่มี credential/ข้อมูลอ่อนไหวหลุด", "ok")


def check_invisible(body):
    hits = [name for ch, name in INVISIBLE.items() if ch in body]
    if hits:
        add("invis", "ไม่มีอักขระล่องหน", "fail", ", ".join(hits))
    else:
        add("invis", "ไม่มีอักขระล่องหน", "ok")


def check_subsystem(body):
    if "<table" not in body:
        add("subsys", "คอลัมน์ Subsystem (ถ้ามีตาราง)", "ok", "ไม่มีตาราง")
        return
    if any("subsystem" in h.lower() for h in th_texts(body)):
        add("subsys", "คอลัมน์ Subsystem (ถ้ามีตาราง)", "ok")
    else:
        add(
            "subsys",
            "คอลัมน์ Subsystem (ถ้ามีตาราง)",
            "warn",
            "มีตารางแต่ไม่พบคอลัมน์ Subsystem — doc-type ที่ไม่แยกตาม subsystem (เช่น Wording Guideline) ข้ามได้",
        )


def check_structure(body, original):
    orig_th = set(t for t in th_texts(original) if t)
    prep_th = set(t for t in th_texts(body) if t)
    missing_cols = orig_th - prep_th
    orig_dt = {}
    for d in data_types(original):
        orig_dt[d] = orig_dt.get(d, 0) + 1
    prep_dt = {}
    for d in data_types(body):
        prep_dt[d] = prep_dt.get(d, 0) + 1
    # panel-warning legitimately drops (the MOCK warning); ignore it here
    missing_dt = [
        d for d, n in orig_dt.items()
        if d != "panel-warning" and prep_dt.get(d, 0) < n
    ]
    orig_tables = len(re.findall(r"<table", original))
    prep_tables = len(re.findall(r"<table", body))
    problems = []
    if missing_cols:
        problems.append("คอลัมน์หายจากต้นฉบับ: " + ", ".join(sorted(missing_cols)))
    if missing_dt:
        problems.append("macro/panel หายจากต้นฉบับ: " + ", ".join(sorted(missing_dt)))
    if prep_tables < orig_tables:
        problems.append(f"จำนวนตารางลดลง ({orig_tables}→{prep_tables})")
    if problems:
        add("struct", "โครง/ฟอแมตคงเดิม (เทียบ --original)", "fail", "; ".join(problems))
    else:
        add("struct", "โครง/ฟอแมตคงเดิม (เทียบ --original)", "ok")


def main():
    args = sys.argv[1:]
    if not args:
        print(
            "usage: verify-confluence.py <body.html> [--original <f>] [--terms \"a,b\"]",
            file=sys.stderr,
        )
        return 2
    path = args[0]
    original_path = None
    terms = []
    i = 1
    while i < len(args):
        if args[i] == "--original" and i + 1 < len(args):
            original_path = args[i + 1]
            i += 2
        elif args[i] == "--terms" and i + 1 < len(args):
            terms = [t for t in args[i + 1].split(",") if t.strip()]
            i += 2
        else:
            print(f"unknown arg: {args[i]}", file=sys.stderr)
            return 2

    try:
        with open(path, encoding="utf-8") as f:
            body = f.read()
    except OSError as e:
        print(f"cannot read {path}: {e}", file=sys.stderr)
        return 2

    check_mock(body)
    check_terms(body, terms)
    check_credentials(body)
    check_invisible(body)
    check_subsystem(body)

    if original_path:
        try:
            with open(original_path, encoding="utf-8") as f:
                original = f.read()
            check_structure(body, original)
        except OSError as e:
            add("struct", "โครง/ฟอแมตคงเดิม (เทียบ --original)", "warn",
                f"อ่านต้นฉบับไม่ได้: {e}")
    else:
        add("struct", "โครง/ฟอแมตคงเดิม (เทียบ --original)", "warn",
            "ไม่ได้ส่ง --original — ตรวจโครงเทียบต้นฉบับไม่ได้ (ตรวจไม่ได้ = ต้องตรวจด้วยตา)")

    failed = sum(1 for _, _, s, _ in results if s == "fail")
    warned = sum(1 for _, _, s, _ in results if s == "warn")

    print("verify-confluence — " + path)
    print("| ตรวจ | ผล | รายละเอียด |")
    print("|---|---|---|")
    for _, name, state, detail in results:
        mark = {"ok": "✅ ok", "fail": "❌ FAIL", "warn": "⚠️ warn"}[state]
        print(f"| {name} | {mark} | {detail} |")
    print()
    if failed:
        print(f"ไม่ผ่าน {failed} ข้อ (warn {warned}) — ห้ามเขียน/ห้ามส่ง แก้ก่อน")
        return 1
    print(f"ผ่านการตรวจเชิงกล (warn {warned}) — ยังต้องตรวจชั้น 2/4/5 ด้วยตา: ผ่านสคริปต์ ≠ ผ่านรีวิว")
    return 0


if __name__ == "__main__":
    sys.exit(main())
