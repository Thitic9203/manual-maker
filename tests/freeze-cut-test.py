#!/usr/bin/env python3
"""Known-answer tests for the sanctioned freeze-cut path (freeze-cut.py + verify-video.py).

Owner order 2026-10-11: a clip that shows the full ER but stutters or freezes in places is fixed
by CUTTING the frozen frames — never re-recorded, never rejected forever. The cut is only
acceptable when verify-video.py can prove, from the untouched source on disk, that every frame
removed was a frozen repeat. These tests pin both halves.

Must PASS (positive): a synthetic stuttering clip that fails verify -> freeze_cut -> the cut
passes every layer verify runs.
Must FAIL (negatives):
  N1 stale manifest — the original manifest copied beside the cut unchanged
  N2 edit record whose source hash was tampered
  N3 a cut that removed frames that were NOT frozen
  N4 a cut that removed more than 60% of the source
  N5 the cut file was replaced after the edit record was written
  N6 the source the edit record points at is gone
  N7 freeze_cut refuses (writes nothing) when the cut would remove > 60%
Every case runs on real mp4 files made by ffmpeg and the real check() — no stubs.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

import importlib.util

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'skills', 'screen-record', 'scripts')


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


vv = _load('verify_video', 'verify-video.py')
fc = _load('freeze_cut', 'freeze-cut.py')

FPS = 8
RESULTS = []


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)


def build_source(path, vf, seconds=14):
    """testsrc2 is in motion on every frame; `vf` injects frozen repeats (loop filter).
    Lossless (-qp 0) on purpose: at crf 18 x264 keeps refining a static picture over successive
    P-frames, which broke a 32-frame injected freeze into runs of 12/16/4 (measured), so the
    known answer would no longer be known."""
    ffmpeg('-f', 'lavfi', '-i', f'testsrc2=size=1920x1080:rate={FPS}:duration={seconds}',
           '-vf', vf, '-fps_mode', 'passthrough', '-c:v', 'libx264', '-qp', '0',
           '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-color_range', 'tv',
           '-movflags', '+faststart', path)
    man = path[:-4] + '.capture.json'
    with open(man, 'w') as fh:
        json.dump({'name': os.path.basename(path)[:-4], 'video': os.path.basename(path),
                   'viewport': {'width': 1920, 'height': 1080}, 'outFps': FPS,
                   'pipeline': vv.GOOD_PIPELINE, 'minUniqueFps': 6.4, 'uniqueFps': 18.0,
                   'framesKept': 200, 'spanSeconds': seconds, 'writeErrors': 0,
                   'overBudget': False, 'holds': 0, 'holdSpans': []}, fh)
    return man


# Isolated single-frame repeats inside motion (the stutter verify measures) + one 4 s freeze.
STUTTER_VF = ','.join([f'loop=loop=1:size=1:start={k}' for k in (10, 22, 34, 46, 58, 70, 82, 94)]
                      + ['loop=loop=32:size=1:start=100'])


def record(name, ok, detail=''):
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f' — {detail}' if detail else ''))


def fails_of(mp4):
    fails, _ = vv.check(mp4, 5, 1920, 1080, )
    return fails


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rewrite(man_path, mutate):
    m = json.load(open(man_path))
    mutate(m)
    json.dump(m, open(man_path, 'w'))


def main():
    tmp = tempfile.mkdtemp(prefix='freeze_cut_')
    src = os.path.join(tmp, 'CLIP.mp4')
    build_source(src, STUTTER_VF)

    before = fails_of(src)
    record('precondition: the stuttering source FAILS verify on stutter',
           any('frozen repeats' in f for f in before), '; '.join(before)[:200])

    # ---- positive -----------------------------------------------------------------------
    rc = fc.main([src])
    cut = os.path.join(tmp, 'CLIP_cut.mp4')
    cutman = os.path.join(tmp, 'CLIP_cut.capture.json')
    record('freeze_cut exits 0 and writes the cut + its own manifest',
           rc == 0 and os.path.isfile(cut) and os.path.isfile(cutman))
    record('freeze_cut never deletes or changes the source',
           os.path.isfile(src) and os.path.isfile(src[:-4] + '.capture.json'))
    after = fails_of(cut)
    record('P1 the cut PASSES every verify layer', after == [], '; '.join(after)[:300])
    m = json.load(open(cutman))
    e = m.get('edit') or {}
    record('cut manifest names the cut file and carries the edit record',
           m.get('video') == 'CLIP_cut.mp4' and e.get('source_file') == 'CLIP.mp4'
           and e.get('source_sha256') == sha(src) and e.get('removed_spans'))

    kinds = {}
    for sp in e.get('removed_spans') or []:
        kinds[sp['reason']] = kinds.get(sp['reason'], 0) + sp['to_frame'] - sp['from_frame'] + 1
    # 8 injected single repeats; the 4 s (32-repeat) freeze trimmed to the 3 s default = 8 gone.
    record('P2 isolated repeats cut; a long freeze is TRIMMED to --max-still, never erased',
           kinds == {'stutter': 8, 'long_freeze': 8}, str(kinds))

    # ---- N1 stale manifest (exactly what the lane's ad-hoc script produced) --------------
    d1 = os.path.join(tmp, 'n1'); os.makedirs(d1)
    shutil.copy2(cut, os.path.join(d1, 'CLIP_cut.mp4'))
    shutil.copy2(src[:-4] + '.capture.json', os.path.join(d1, 'CLIP_cut.capture.json'))
    f1 = fails_of(os.path.join(d1, 'CLIP_cut.mp4'))
    record('N1 stale copied manifest FAILS ("manifest describes")',
           any('manifest describes' in f for f in f1), '; '.join(f1)[:200])

    def variant(tag, mutate=None, after_copy=None):
        d = os.path.join(tmp, tag); os.makedirs(d)
        for f in ('CLIP.mp4', 'CLIP.capture.json', 'CLIP_cut.mp4', 'CLIP_cut.capture.json'):
            shutil.copy2(os.path.join(tmp, f), os.path.join(d, f))
        if mutate:
            rewrite(os.path.join(d, 'CLIP_cut.capture.json'), mutate)
        if after_copy:
            after_copy(d)
        return fails_of(os.path.join(d, 'CLIP_cut.mp4'))

    f2 = variant('n2', lambda m: m['edit'].__setitem__('source_sha256', '0' * 64))
    record('N2 tampered source hash FAILS', any('source' in f and 'sha256' in f for f in f2),
           '; '.join(f2)[:200])

    f5 = variant('n5', after_copy=lambda d: shutil.copy2(
        os.path.join(d, 'CLIP.mp4'), os.path.join(d, 'CLIP_cut.mp4')))
    record('N5 cut file swapped after the record FAILS', any('output_sha256' in f or 'cut file' in f
                                                             for f in f5), '; '.join(f5)[:200])

    f6 = variant('n6', after_copy=lambda d: os.remove(os.path.join(d, 'CLIP.mp4')))
    record('N6 source missing FAILS', any('source' in f and 'not found' in f for f in f6),
           '; '.join(f6)[:200])

    # ---- N3 a cut that removed MOVING frames, built with the tool's own writer -----------
    d3 = os.path.join(tmp, 'n3'); os.makedirs(d3)
    s3 = os.path.join(d3, 'CLIP.mp4'); shutil.copy2(src, s3)
    shutil.copy2(src[:-4] + '.capture.json', s3[:-4] + '.capture.json')
    fc.write_cut(s3, sorted(set(range(3, 9))), reasons={}, enforce_cap=False)
    f3 = fails_of(os.path.join(d3, 'CLIP_cut.mp4'))
    record('N3 cut that removed non-frozen frames FAILS', any('not a frozen repeat' in f for f in f3),
           '; '.join(f3)[:200])

    # ---- P3 many separate spans: a real 25 fps clip needed ~100 spans and a select expression
    # that long broke ffmpeg's parser ("Error while parsing expression"), so nothing was cut.
    d9 = os.path.join(tmp, 'p3'); os.makedirs(d9)
    s9 = os.path.join(d9, 'CLIP.mp4')
    build_source(s9, 'null', seconds=30)                # 240 frames
    many = list(range(2, 220, 2))                       # 109 one-frame spans (parser broke at ~95)
    rc9, msg9 = fc.write_cut(s9, many, reasons={}, enforce_cap=False)
    record('P3 a cut with 109 separate spans encodes frame-exact', rc9 == 0 and
           vv.count_frames(os.path.join(d9, 'CLIP_cut.mp4')) == 240 - len(many), msg9[:200])

    # ---- N4 > 60 % removed: verify refuses a record that claims it -----------------------
    d4 = os.path.join(tmp, 'n4'); os.makedirs(d4)
    s4 = os.path.join(d4, 'CLIP.mp4')
    build_source(s4, 'loop=loop=200:size=1:start=20', seconds=4)   # 3 s motion + 25 s frozen
    n4_frames = len(vv.motion_series(s4)) + 1
    frozen = list(range(21, 221))
    fc.write_cut(s4, frozen, reasons={}, enforce_cap=False)
    f4 = fails_of(os.path.join(d4, 'CLIP_cut.mp4'))
    record(f'N4 cut removing {100 * len(frozen) / n4_frames:.0f}% FAILS (cap 60%)',
           any('60%' in f for f in f4), '; '.join(f4)[:200])

    # ---- N7 the tool itself refuses that cut ---------------------------------------------
    d7 = os.path.join(tmp, 'n7'); os.makedirs(d7)
    s7 = os.path.join(d7, 'CLIP.mp4'); shutil.copy2(s4, s7)
    shutil.copy2(s4[:-4] + '.capture.json', s7[:-4] + '.capture.json')
    rc7 = fc.main([s7, '--max-still', '1.0'])
    record('N7 freeze_cut refuses > 60% and writes nothing',
           rc7 != 0 and not os.path.exists(os.path.join(d7, 'CLIP_cut.mp4')))

    # ---- the guard that existed before stays: _cut name without an edit record -----------
    d8 = os.path.join(tmp, 'n8'); os.makedirs(d8)
    shutil.copy2(cut, os.path.join(d8, 'X_cut.mp4'))
    rewrite_target = os.path.join(d8, 'X_cut.capture.json')
    m8 = json.load(open(cutman)); m8.pop('edit'); m8['video'] = 'X_cut.mp4'
    json.dump(m8, open(rewrite_target, 'w'))
    f8 = fails_of(os.path.join(d8, 'X_cut.mp4'))
    record('N8 a *_cut.mp4 with no edit record FAILS', any('edit record' in f for f in f8),
           '; '.join(f8)[:200])

    bad = [n for n, ok in RESULTS if not ok]
    print(f'\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed  (tmp: {tmp})')
    if not bad:
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
