#!/usr/bin/env /usr/bin/python3
# -*- coding: utf-8 -*-
"""
manual-maker — pixel verifier for the red numbered callouts.

`review.md` ชั้นที่ 3 อ้างว่า "เลขในวงตรงกับเลขขั้นตอน 1:1" มาตลอด แต่เดิมเป็นแค่ประโยคให้คนกวาดตาดู
จึงหลุดมาแล้วจริง: วง ② ไปวางบนปุ่มของขั้นตอนที่ 3, วง ④ ไปอยู่บนทางเลือกที่ไม่ใช่ขั้นตอนที่มีเลข,
และวง ⑤ ถูกวาดซ้ำสองรูป — เพราะวงถูกวาดตามดราฟต์เก่า แล้วไม่ได้ไล่ใหม่ตอนเรียบเรียงขั้นตอนใหม่.

สคริปต์นี้ทำให้ข้ออ้างนั้น **มีหลักฐาน** โดยเทียบ `annotations.json` กับ **พิกเซลจริง** ในไฟล์ PNG:
แมนิเฟสต์ที่โกหกว่าวาดอะไรไว้ จะไม่ผ่าน.

    verify-annotations.py <annotations.json> --assets <dir> [--docx <file.docx>]
                          [--radius 18] [--tol 40] [--max-dist 25] [--color "#E53935"]

อาร์กิวเมนต์แรกเป็น **ไฟล์เดียว** หรือ **โฟลเดอร์** ที่มี `<หัวข้อ>.annotations.json` หลายไฟล์ก็ได้
(ผู้เขียนขนานใน Step 4–6 ต่างคนต่างเขียนไฟล์ของหัวข้อตัวเอง สคริปต์รวมให้เอง — ดู parallel.md)

Exit 0 = ไม่พบข้อผิดเชิงกล   Exit 1 = มี FAIL อย่างน้อยหนึ่งข้อ (ห้ามส่งมอบ)   Exit 2 = เปิด/อ่านไม่ได้

ขอบเขตที่สคริปต์นี้ **ตัดสินไม่ได้**: วงอยู่บน "ปุ่มที่ถูกต้อง" หรือไม่ — นั่นคือความหมาย ไม่ใช่เรขาคณิต
สคริปต์พิสูจน์ได้แค่ว่า *เลขครบและไม่ซ้ำ* และ *แมนิเฟสต์ตรงกับวงที่วาดจริง* เท่านั้น (ดู review.md ชั้นที่ 3).

Pinned to /usr/bin/python3 — stdlib + Pillow เท่านั้น (PIL อยู่บนอินเทอร์พรีเตอร์นี้ เหมือนขั้นตอน annotate).
"""

import json
import os
import re
import sys
import zipfile

try:
    from PIL import Image, ImageChops
except ImportError:
    print("ไม่พบ Pillow บน /usr/bin/python3 — รัน preflight.sh --install ก่อน", file=sys.stderr)
    sys.exit(2)

results = []   # (id, name, state, detail)


def add(cid, name, state, detail=""):
    results.append((cid, name, state, detail))


# ------------------------------------------------------------------ label vs step text
# คู่มือมีธรรมเนียมของตัวเองอยู่แล้ว (บังคับใน template.md): ขั้นตอนต้อง **อ้างชื่อคอนโทรลจริงในเครื่องหมายคำพูด**
# เช่น `คลิกปุ่ม “เข้าห้องเรียน”` จึงเทียบได้เชิงกลว่า label ของวงพูดถึงคอนโทรลเดียวกับขั้นตอนของตัวเองไหม
QUOTE_PATTERNS = (r'“([^”]+)”', r'"([^"]+)"', r'‘([^’]+)’', r'«([^»]+)»')

# คำบอกชนิดคอนโทรลที่ label มักขึ้นต้น — ตัดทิ้งก่อนเทียบ ไม่งั้น "ปุ่มเข้าห้องเรียน" จะไม่แมตช์ "เข้าห้องเรียน"
ROLE_WORDS = ('ปุ่ม', 'เมนู', 'แท็บ', 'ช่อง', 'ไอคอน', 'ตัวเลือก', 'ลิงก์', 'กล่อง', 'แถบ',
              'คอลัมน์', 'หน้าต่าง', 'รายการ', 'button', 'menu', 'tab', 'field', 'icon')

CROSS_MIN = 0.60      # ความคล้ายขั้นต่ำก่อนจะกล้าฟันธงว่า label ไปตรงกับ "ขั้นตอนอื่น"


def quoted_controls(text):
    out = []
    for pat in QUOTE_PATTERNS:
        out += [m.group(1).strip() for m in re.finditer(pat, text or '')]
    return [c for c in out if c]


def core(s):
    """ตัดคำบอกชนิดคอนโทรลที่นำหน้าออก: 'ปุ่มเข้าห้องเรียน' -> 'เข้าห้องเรียน'."""
    s = (s or '').strip()
    changed = True
    while changed:
        changed = False
        for wd in ROLE_WORDS:
            if len(s) > len(wd) and s[:len(wd)].lower() == wd.lower():
                s = s[len(wd):].strip()
                changed = True
    return s


def sim(a, b):
    """0..1 — ฝ่ายหนึ่งเป็นสตริงย่อยของอีกฝ่ายหรือไม่ คิดสัดส่วนความยาวเพื่อกันการแมตช์บังเอิญ."""
    a, b = core(a), core(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return min(len(a), len(b)) / float(max(len(a), len(b)))
    return 0.0


def label_verdict(label, own_text, others):
    """
    คืน ('PASS'|'FAIL'|'SKIP', เหตุผล).

    `others` = {เลขขั้นตอนอื่น: step_text} ในหัวข้อเดียวกัน

    ตรรกะสำคัญ — **ฟันธงจากหลักฐานที่มี ไม่ใช่จากการไม่มีหลักฐาน**:
      * ขั้นตอนของตัวเองอ้างคอนโทรลในเครื่องหมายคำพูด → label ต้องพูดถึงตัวใดตัวหนึ่ง ไม่งั้น FAIL
      * ขั้นตอนของตัวเอง **ไม่ได้อ้างคอนโทรลเลย** (เช่น "เปิดเบราว์เซอร์ แล้วเข้าที่ https://…")
        → ปกติ SKIP เพราะไม่มีอะไรให้เทียบ **ยกเว้น** label ดันไปตรงกับคอนโทรลที่ *ขั้นตอนอื่น* อ้างไว้
        ซึ่งเป็นลายเซ็นของบั๊กตัวจริง (วงถูกวางตามดราฟต์เก่า เลยไปนั่งบนคอนโทรลของขั้นตอนข้างเคียง)
    """
    own_q = quoted_controls(own_text)
    best_n, best_s = None, 0.0
    for m, txt in others.items():
        for q in quoted_controls(txt):
            s = sim(q, label)
            if s > best_s:
                best_n, best_s = m, s

    if own_q:
        if any(sim(q, label) > 0 for q in own_q):
            return 'PASS', ''
        hint = (' — ไปตรงกับคอนโทรลของขั้นตอนที่ %s แทน' % best_n) if best_s >= CROSS_MIN else ''
        return 'FAIL', ('label "%s" ไม่ตรงกับคอนโทรลที่ขั้นตอนนี้อ้างไว้ (%s)%s'
                        % (label, ', '.join('"%s"' % q for q in own_q), hint))

    if best_s >= CROSS_MIN:
        return 'FAIL', ('ขั้นตอนนี้ไม่ได้อ้างคอนโทรลในเครื่องหมายคำพูด แต่ label "%s" '
                        'ไปตรงกับคอนโทรลของขั้นตอนที่ %s — วงน่าจะไปอยู่บนคอนโทรลของขั้นตอนนั้น'
                        % (label, best_n))
    return 'SKIP', ''


# --------------------------------------------------------------------------- detection
def _mask(im, target, tol):
    """Binary mask (mode 'L', 0/255) of pixels within `tol` of `target` on every channel."""
    bands = im.split()[:3]
    out = None
    for ch, c in zip(bands, target):
        lo, hi = c - tol, c + tol
        b = ch.point(lambda v, lo=lo, hi=hi: 255 if lo <= v <= hi else 0, mode='L').convert('1')
        out = b if out is None else ImageChops.logical_and(out, b)
    return out.convert('L')


def find_circles(path, target, tol, radius):
    """
    Locate the filled callout discs and return [(cx, cy, area), …].

    หัวใจอยู่ที่การ **ไม่** จับ "พิกเซลแดงติดกัน" เฉย ๆ เพราะ UI ของระบบเองก็มีสีแดง (ไอคอนลบ, badge
    สถานะ, แถบแจ้งเตือน). ที่วัดจากภาพจริง 19 รูป: วง callout ได้ bbox 37x37, area 931–1001,
    fill 0.68–0.73, aspect 1.00 ทุกวง ส่วนของแดงใน UI ได้ 59x20 (aspect 2.95), 38x20 (1.90),
    26x24 (area 325, fill 0.52), 21x30 (fill 0.20) — จึงคัดด้วย "แผ่นกลมตันขนาดที่คาด" ครบ 4 เงื่อนไข
    (กลม + ตัน + ขนาด bbox + พื้นที่) ไม่ใช่เงื่อนไขเดียว; ของแดงใน UI ทุกชิ้นตกอย่างน้อย 2 เงื่อนไข.

    เลข **สีขาว** อยู่กลางวง จึงเจาะเนื้อแดงหายไปบางส่วน — fill ของแผ่นกลมสมบูรณ์คือ π/4 ≈ 0.785
    แต่ที่วัดได้จริงคือ 0.68–0.73 ช่วงที่ยอมรับจึงเผื่อไว้ด้านต่ำ.

    `radius` คือรัศมีของ **เนื้อแดง** ไม่ใช่รัศมีที่ตาเห็น — วงมีขอบขาว 3px ล้อมอยู่ ดังนั้นวงที่ดู
    "รัศมี ~21" มีเนื้อแดงรัศมี ~18 (วัดได้ bbox 37 → r 18.5) ค่าเริ่มต้นจึงเป็น 18.

    ค่าที่ตั้งไว้ทนต่อ `--tol`: ลองที่ 20/40/60/80 บนภาพจริง bbox ยัง 37x37 เท่าเดิม จุดกึ่งกลาง
    ขยับ < 0.2px — ระยะจับคู่ 25px จึงเผื่อเหลือเฟือ ไม่ใช่ค่าที่จูนมาพอดี.
    """
    im = Image.open(path).convert('RGB')
    w, h = im.size
    data = _mask(im, target, tol).tobytes()          # 1 byte/px, row-major, no padding
    seen = bytearray(len(data))

    d_exp = 2.0 * radius
    dim_lo, dim_hi = 0.72 * d_exp, 1.30 * d_exp
    area_lo, area_hi = 0.45 * 3.14159 * radius ** 2, 1.20 * 3.14159 * radius ** 2

    found, pos = [], 0
    while True:
        i = data.find(b'\xff', pos)                  # C-speed skip over the empty majority
        if i < 0:
            break
        pos = i + 1
        if seen[i]:
            continue
        # flood fill, accumulating moments only (never a point list — a red banner could be huge)
        stack, seen[i] = [i], 1
        n = sx = sy = 0
        x0 = x1 = i % w
        y0 = y1 = i // w
        while stack:
            p = stack.pop()
            y, x = divmod(p, w)
            n += 1
            sx += x
            sy += y
            if x < x0: x0 = x
            if x > x1: x1 = x
            if y < y0: y0 = y
            if y > y1: y1 = y
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
                           (x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    q = ny * w + nx
                    if data[q] and not seen[q]:
                        seen[q] = 1
                        stack.append(q)

        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        if not (dim_lo <= bw <= dim_hi and dim_lo <= bh <= dim_hi):
            continue                                  # wrong size for a callout
        if not (area_lo <= n <= area_hi):
            continue                                  # not enough / too much red for the disc
        if not (0.80 <= bw / float(bh) <= 1.25):
            continue                                  # not round (kills badges and bars)
        if not (0.58 <= n / float(bw * bh) <= 0.86):
            continue                                  # not solid (kills rings, glyphs, icons)
        found.append((sx / float(n), sy / float(n), n))
    return found, (w, h)


# ------------------------------------------------------------------------------- docx
def _fingerprint(im):
    """Coarse content fingerprint that survives a re-encode: size + 16x16 grey, quantised."""
    g = im.convert('L').resize((16, 16))
    return im.size, bytes(v & 0xF0 for v in g.getdata())


def docx_media(path):
    """Return (byte-hashes, fingerprints) of every image actually embedded and reachable."""
    import hashlib
    z = zipfile.ZipFile(path)
    names = z.namelist()
    doc = z.read('word/document.xml').decode('utf-8', 'replace')
    rels = (z.read('word/_rels/document.xml.rels').decode('utf-8', 'replace')
            if 'word/_rels/document.xml.rels' in names else '')
    # only media that a live r:embed relationship points at — an orphan in word/media/ is not "in" the doc
    live = set()
    for rid in set(re.findall(r'r:embed="([^"]+)"', doc)):
        m = re.search(r'Id="%s"[^>]*Target="([^"]+)"' % re.escape(rid), rels)
        if not m:
            continue
        tgt = m.group(1).lstrip('/')
        if not tgt.startswith('word/'):
            tgt = 'word/' + tgt
        if tgt in names:
            live.add(tgt)
    hashes, prints = set(), []
    for n in live:
        raw = z.read(n)
        hashes.add(hashlib.sha1(raw).hexdigest())
        try:
            import io
            prints.append(_fingerprint(Image.open(io.BytesIO(raw))))
        except Exception:
            pass
    return hashes, prints


def embedded(asset_path, hashes, prints):
    import hashlib
    with open(asset_path, 'rb') as fh:
        raw = fh.read()
    if hashlib.sha1(raw).hexdigest() in hashes:       # the documented path: PNG copied verbatim
        return True
    try:                                              # survives a re-encode by the build step
        fp = _fingerprint(Image.open(asset_path))
    except Exception:
        return False
    return fp in prints


# ------------------------------------------------------------------------------- main
def main():
    args = sys.argv[1:]
    if not args or args[0].startswith('-'):
        print('usage: verify-annotations.py <annotations.json> --assets <dir> [--docx <file.docx>]\n'
              '                             [--radius 18] [--tol 40] [--max-dist 25] [--color "#E53935"]',
              file=sys.stderr)
        return 2

    man_path = args[0]
    assets = docx_path = None
    radius, tol, max_dist, color = 18.0, 40, 25.0, '#E53935'
    for i, a in enumerate(args):
        nxt = args[i + 1] if i + 1 < len(args) else None
        if a == '--assets' and nxt: assets = nxt
        if a == '--docx' and nxt: docx_path = nxt
        if a == '--radius' and nxt: radius = float(nxt)
        if a == '--tol' and nxt: tol = int(nxt)
        if a == '--max-dist' and nxt: max_dist = float(nxt)
        if a == '--color' and nxt: color = nxt

    if not assets:
        print('ต้องระบุ --assets <dir> (โฟลเดอร์ manual-assets/<slug>/)', file=sys.stderr)
        return 2
    c = color.lstrip('#')
    try:
        target = (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    except Exception:
        print(f'--color ไม่ถูกต้อง: {color}', file=sys.stderr)
        return 2

    # A directory is accepted so the parallel writers of Step 4–6 never share a file:
    # each writer emits `<section>.annotations.json` (its own section prefix = its own
    # ownership lane, per parallel.md) and this merges them. Two writers claiming the same
    # section is a collision, not something to silently last-write-wins.
    def load_one(p):
        with open(p, encoding='utf-8') as fh:
            obj = json.load(fh)
        if not isinstance(obj, dict) or not isinstance(obj.get('sections'), dict):
            raise ValueError('รูปแบบผิด: ต้องเป็น {"sections": {"<หัวข้อ>": {"steps": N, "circles": [...]}}}')
        return obj['sections']

    try:
        if os.path.isdir(man_path):
            parts = sorted(f for f in os.listdir(man_path) if f.endswith('.annotations.json'))
            if not parts:
                print(f'ไม่พบ *.annotations.json ใน {man_path}', file=sys.stderr)
                return 2
            merged, owner = {}, {}
            for f in parts:
                for sec, body in load_one(os.path.join(man_path, f)).items():
                    if sec in merged:
                        print(f'หัวข้อ {sec} ถูกประกาศซ้ำใน {owner[sec]} และ {f} '
                              f'— ผู้เขียนสองตัวอ้างหัวข้อเดียวกัน', file=sys.stderr)
                        return 2
                    merged[sec], owner[sec] = body, f
            manifest = {'sections': merged}
        else:
            manifest = {'sections': load_one(man_path)}
    except Exception as e:
        print(f'อ่าน annotations.json ไม่ได้: {e}', file=sys.stderr)
        return 2
    if not os.path.isdir(assets):
        print(f'ไม่พบโฟลเดอร์ภาพ: {assets}', file=sys.stderr)
        return 2

    sections = manifest['sections']

    # -- 0. manifest shape ----------------------------------------------------
    # A malformed entry is not "probably fine" — it makes every later check unverifiable.
    bad, nolabel, total = [], 0, 0
    for sec, body in sections.items():
        if not isinstance(body, dict) or not isinstance(body.get('circles'), list) \
                or not isinstance(body.get('steps'), int):
            bad.append(f'{sec}: ขาด steps (int) หรือ circles (list)')
            continue
        for k, ci in enumerate(body['circles']):
            total += 1
            if not isinstance(ci, dict):
                bad.append(f'{sec}[{k}]: ไม่ใช่ object'); continue
            miss = [f for f in ('n', 'file', 'x', 'y') if f not in ci]
            if miss:
                bad.append(f'{sec}[{k}]: ขาดคีย์ {"/".join(miss)}'); continue
            if not isinstance(ci['n'], int) or not isinstance(ci['file'], str) \
                    or not isinstance(ci['x'], (int, float)) or not isinstance(ci['y'], (int, float)):
                bad.append(f'{sec}[{k}]: ชนิดข้อมูลผิด')
            if not str(ci.get('label', '')).strip():
                nolabel += 1
    add('0', 'แมนิเฟสต์ครบรูปแบบ', 'FAIL' if bad else 'PASS',
        '; '.join(bad[:4]) if bad else
        f'{len(sections)} หัวข้อ / {total} วง' +
        (f' (ไม่มี label {nolabel} วง — คนต้องใช้ label เทียบกับข้อความขั้นตอน)' if nolabel else ''))
    if bad:
        return report()

    ok_secs = {s: b for s, b in sections.items()}

    # -- 1..3 numbering -------------------------------------------------------
    # ต้นเหตุของ defect ที่ทำให้มีสคริปต์นี้: วงถูกวาดตาม "ดราฟต์ก่อนหน้า" ของรายการขั้นตอน
    missing, dupes, out_of_range = [], [], []
    for sec, body in ok_secs.items():
        n_steps = body['steps']
        nums = [ci['n'] for ci in body['circles']]
        seen_once = set()
        for n in nums:
            if n in seen_once:
                dupes.append(f'{sec}: เลข {n} ซ้ำ')
            seen_once.add(n)
        gap = sorted(set(range(1, n_steps + 1)) - set(nums))
        if gap:
            missing.append(f'{sec}: ขาดวงของขั้นตอน {gap} (steps={n_steps})')
        bad_n = sorted({n for n in nums if n < 1 or n > n_steps})
        if bad_n:
            out_of_range.append(f'{sec}: เลข {bad_n} หลุดช่วง 1..{n_steps}')

    spread = ", ".join('%s=1..%d' % (s, b['steps']) for s, b in list(ok_secs.items())[:4])
    add('1', 'เลขวงครบ 1..N ตามจำนวนขั้นตอน', 'FAIL' if missing else 'PASS',
        '; '.join(missing[:4]) if missing
        else 'ครบทุกหัวข้อ (%s%s)' % (spread, ' …' if len(ok_secs) > 4 else ''))
    add('2', 'ไม่มีเลขวงซ้ำในหัวข้อเดียวกัน', 'FAIL' if dupes else 'PASS',
        '; '.join(dupes[:4]) if dupes else 'ไม่พบเลขซ้ำ (นับข้ามรูปในหัวข้อเดียวกันด้วย)')
    add('3', 'เลขวงไม่หลุดช่วง 1..N', 'FAIL' if out_of_range else 'PASS',
        '; '.join(out_of_range[:4]) if out_of_range else 'อยู่ในช่วงทุกวง')

    # -- 4. files exist -------------------------------------------------------
    by_file = {}
    for sec, body in ok_secs.items():
        for ci in body['circles']:
            by_file.setdefault(ci['file'], []).append((sec, ci))
    absent = sorted(f for f in by_file if not os.path.isfile(os.path.join(assets, f)))
    add('4', 'ไฟล์ภาพที่อ้างมีอยู่จริง', 'FAIL' if absent else 'PASS',
        f'หาไม่เจอใน {assets}: {", ".join(absent[:4])}' if absent
        else f'ครบ {len(by_file)} ไฟล์')

    # -- 5. ≤ 5 callouts per image -------------------------------------------
    crowded = [f'{f} มี {len(v)} วง' for f, v in sorted(by_file.items()) if len(v) > 5]
    add('5', 'ไม่เกิน 5 วงต่อรูป', 'FAIL' if crowded else 'PASS',
        '; '.join(crowded[:4]) if crowded
        else f'มากสุด {max((len(v) for v in by_file.values()), default=0)} วง/รูป')

    # -- 6..7 pixel agreement -------------------------------------------------
    # ชั้นที่ทำให้ gate นี้ "จริง" แทนที่จะเป็นการรายงานตัวเอง: แมนิเฟสต์ที่อ้างว่าวาดวงไว้ตรงไหน
    # ต้องตรงกับวงที่ **วาดไว้จริง** ในพิกเซล
    count_bad, pos_bad, unreadable = [], [], []
    for fname in sorted(by_file):
        p = os.path.join(assets, fname)
        if not os.path.isfile(p):
            continue
        try:
            detected, _ = find_circles(p, target, tol, radius)
        except Exception as e:
            unreadable.append(f'{fname}: {e}')
            continue
        claimed = by_file[fname]
        if len(detected) != len(claimed):
            count_bad.append(f'{fname}: แมนิเฟสต์อ้าง {len(claimed)} วง แต่ในภาพมี {len(detected)}')
        # one-to-one nearest match, closest pairs first
        pairs = sorted(
            ((((ci['x'] - dx) ** 2 + (ci['y'] - dy) ** 2) ** 0.5, k, j)
             for k, (sec, ci) in enumerate(claimed)
             for j, (dx, dy, _a) in enumerate(detected)),
            key=lambda t: t[0])
        used_c, used_d = set(), set()
        for dist, k, j in pairs:
            if k in used_c or j in used_d or dist > max_dist:
                continue
            used_c.add(k); used_d.add(j)
        for k, (sec, ci) in enumerate(claimed):
            if k not in used_c:
                near = min((((ci['x'] - dx) ** 2 + (ci['y'] - dy) ** 2) ** 0.5
                            for dx, dy, _a in detected), default=None)
                pos_bad.append(
                    f'{fname} วง {ci["n"]} (หัวข้อ {sec}) อ้างพิกัด ({ci["x"]},{ci["y"]}) '
                    + (f'แต่วงจริงที่ใกล้สุดห่าง {near:.0f}px' if near is not None
                       else 'แต่ในภาพไม่มีวงเลย'))

    if unreadable:
        add('6', 'จำนวนวงในภาพตรงกับแมนิเฟสต์', 'FAIL', 'อ่านภาพไม่ได้: ' + '; '.join(unreadable[:3]))
    else:
        add('6', 'จำนวนวงในภาพตรงกับแมนิเฟสต์', 'FAIL' if count_bad else 'PASS',
            '; '.join(count_bad[:4]) if count_bad
            else f'ตรวจ {len(by_file)} รูป — นับวงที่วาดจริงตรงกับที่อ้างทุกรูป')
    add('7', 'พิกัดวงตรงกับวงที่วาดจริง', 'FAIL' if pos_bad else 'PASS',
        '; '.join(pos_bad[:3]) if pos_bad
        else f'ทุกวงห่างจากวงจริงไม่เกิน {max_dist:.0f}px')

    # -- 8. embedded in the delivered document --------------------------------
    if docx_path:
        try:
            hashes, prints = docx_media(docx_path)
        except Exception as e:
            add('8', 'ภาพถูกฝังในเอกสารจริง', 'FAIL', f'เปิด .docx ไม่ได้: {e}')
        else:
            miss = sorted(f for f in by_file
                          if os.path.isfile(os.path.join(assets, f))
                          and not embedded(os.path.join(assets, f), hashes, prints))
            add('8', 'ภาพถูกฝังในเอกสารจริง', 'FAIL' if miss else 'PASS',
                f'อ้างในแมนิเฟสต์แต่ไม่อยู่ในเอกสาร: {", ".join(miss[:4])}' if miss
                else f'ครบ {len(by_file)} รูป (เทียบไบต์ ตกมาที่ลายนิ้วมือภาพถ้าไฟล์ถูกเข้ารหัสใหม่)')
    else:
        add('8', 'ภาพถูกฝังในเอกสารจริง', 'SKIP', 'ไม่ได้ส่ง --docx มา จึงข้าม')

    # -- 9. label ตรงกับคอนโทรลที่ขั้นตอนของตัวเองอ้างไว้ ----------------------
    # ปิดช่องว่างที่เหลือจาก 0.20.0: เลขถูกต้องครบถ้วน แต่ "วง ② ไปนั่งบนปุ่มที่ขั้นตอนที่ 3 พูดถึง"
    # ยังผ่านได้ เพราะเลขกับพิกัดสอดคล้องกันเอง ผิดที่ *ความหมาย* ของการจับคู่
    no_text, verdicts = [], []
    for sec, body in ok_secs.items():
        texts = {ci['n']: ci.get('step_text', '') for ci in body['circles']}
        for ci in body['circles']:
            st = str(ci.get('step_text', '') or '').strip()
            if not st:
                no_text.append('%s วง %s' % (sec, ci['n']))
                continue
            others = {m: t for m, t in texts.items() if m != ci['n'] and t}
            state, why = label_verdict(str(ci.get('label', '') or ''), st, others)
            verdicts.append((sec, ci['n'], state, why))

    bad_lbl = [(s, n, w) for s, n, st, w in verdicts if st == 'FAIL']
    skipped = [1 for _s, _n, st, _w in verdicts if st == 'SKIP']
    checked = [1 for _s, _n, st, _w in verdicts if st == 'PASS']

    if no_text:
        add('9', 'label ตรงกับคอนโทรลในข้อความขั้นตอน', 'FAIL',
            'ไม่มี step_text %d วง (%s%s) — เทียบไม่ได้ = ไม่ผ่าน'
            % (len(no_text), ', '.join(no_text[:4]), ' …' if len(no_text) > 4 else ''))
    elif bad_lbl:
        add('9', 'label ตรงกับคอนโทรลในข้อความขั้นตอน', 'FAIL',
            '; '.join('%s วง %s: %s' % (s, n, w) for s, n, w in bad_lbl[:3]))
    elif not verdicts:
        add('9', 'label ตรงกับคอนโทรลในข้อความขั้นตอน', 'SKIP', 'ไม่มีวงให้ตรวจ')
    else:
        add('9', 'label ตรงกับคอนโทรลในข้อความขั้นตอน', 'PASS',
            'ตรงกัน %d วง / ข้าม %d วง (ขั้นตอนไม่ได้อ้างคอนโทรลในเครื่องหมายคำพูด '
            'เช่น "เปิดเบราว์เซอร์ แล้วเข้าที่ https://…") — '
            '"คอนโทรลที่อ้างเป็นตัวที่ควรคลิกจริงไหม" ยังต้องใช้คนตัดสิน'
            % (len(checked), len(skipped)))

    return report()


def report():
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
    print("RESULT: pass (เลขวงและพิกัดตรงกัน — 'วงชี้ถูกปุ่มไหม' ยังต้องตรวจด้วยสายตา)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
