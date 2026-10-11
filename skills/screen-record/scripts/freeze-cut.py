#!/usr/bin/env python3
"""freeze-cut.py — the sanctioned way to cut frozen frames out of a recorded clip.

usage: python3 freeze-cut.py <clip.mp4> [--max-still SECONDS] [--dry-run] [--replace-cut]

Owner order 2026-10-11: a clip that shows the whole expected result but stutters or sits frozen in
places is FIXED BY A CUT — not re-recorded, not rejected forever. Before this tool the only way to
do that was an ad-hoc script that dropped frames and copied the original `.capture.json` beside the
cut unchanged, and verify-video.py correctly refused the result ("manifest describes '<orig>.mp4',
not this file"; "manifest declares a still-hold ending at 21.65s but the file is only 19.25s long").

What it removes — only frames that are a frozen repeat of the frame before them, found with
verify-video.py's own detector and thresholds (imported, never copied):
  * stutter: a run of repeated frames no longer than 0.5 s that verify_video.stutter_frames flags
    inside motion (the frames that make the "N% of the moving frames are frozen repeats" layer
    fail) — removed whole.
  * long freeze: a run of repeats longer than --max-still seconds (default 3.0, must be > 0.5) is
    trimmed to that length — never removed whole, so the screen it holds stays on screen.
    A screen that sits still for 3 s is readable; one that sits for 12 s looks hung.
  Declared still-holds are never touched by the stutter pass (verify excludes them too); a hold
  longer than --max-still is trimmed like any freeze and its span is remapped.

What it writes, beside the source, never touching it:
  <stem>_cut.mp4            same fps / resolution / codec settings as the recorder, no re-timing
  <stem>_cut.capture.json   the source manifest with video/name/framesKept/spanSeconds/holdSpans
                            rewritten for the cut, plus an `edit` record: source_file,
                            source_sha256, source_manifest, source_manifest_sha256, output_sha256,
                            removed_frames, removed_spans[], removed_pct, tool, version.

verify-video.py accepts the cut only after re-deriving every claim in that record from the source
on disk (check_edit). Refused without writing anything: more than 60% of the source would go
(that is a re-record case), the source manifest does not describe the source,
the source is itself a cut, or the clip has audio (a frame cut would desync narration).

Exit 0 = cut written (or dry-run planned), 1 = refused, 2 = could not run.
"""
import bisect
import json
import os
import shlex
import subprocess
import sys

import importlib.util

_spec = importlib.util.spec_from_file_location(
    'verify_video', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify-video.py'))
vv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vv)   # the detector and thresholds come from verify-video.py, never copied

TOOL = 'freeze-cut.py'
VERSION = '1.0.0'
DEFAULT_MAX_STILL = 3.0
# A repeat run this short inside motion is a recorder stall, not a pause anyone meant.
SHORT_RUN_S = 0.5


def _load_source(src):
    """(manifest, fps, series, why). why is None when the source may be cut."""
    if not os.path.isfile(src):
        return None, None, None, f'source not found: {src}'
    man, why = vv.read_manifest(src)
    if man is None:
        return None, None, None, why
    if man.get('video') != os.path.basename(src):
        return None, None, None, (f"manifest describes {man.get('video')!r}, not "
                                  f'{os.path.basename(src)!r} — cut the original recording')
    if man.get('edit'):
        return None, None, None, 'this clip is already a cut — cut the original recording instead'
    info, err = vv.probe(src)
    if info is None:
        return None, None, None, f'unreadable source: {err}'
    streams = info.get('streams', [])
    if any(s.get('codec_type') == 'audio' for s in streams):
        return None, None, None, ('the clip has an audio track — cutting frames would desync it; '
                                  'cut first, then run narrate.py on the cut')
    vs = next((s for s in streams if s.get('codec_type') == 'video'), {})
    fps = vv.eval_fps(vs.get('r_frame_rate'))
    if not fps:
        return None, None, None, 'source frame rate unreadable'
    series = vv.motion_series(src)
    if series is None:
        return None, None, None, 'motion check could not run on the source'
    return man, fps, series, None


def _runs(values):
    """Maximal runs of consecutive working indices j whose value is a frozen repeat."""
    runs, cur = [], []
    for j, v in enumerate(values):
        if v < vv.MOTION_DUP:
            cur.append(j)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def plan(series, fps, hold_spans, max_still=DEFAULT_MAX_STILL):
    """Source frame indices to remove, and why each goes. Pure: no files touched.

    Works on RUNS of repeated frames, never frame by frame, so a deliberate still can never be
    eroded away: an earlier frame-by-frame loop re-ran the stutter detector after every removal and
    ate a 4 s freeze from its edges inward until nothing of it was left (measured on the synthetic
    test clip) — on a real clip that is the ER screen vanishing.
      * a run of at most SHORT_RUN_S that the detector flags inside motion -> removed whole (stutter)
      * a run longer than max_still -> trimmed to max_still (long_freeze)
      * anything else -> kept
    The working series after a removal comes from the source series: a removed frame repeats the
    one before it, so its successor differs from the new predecessor by the same amount.
    check_edit re-measures the real cut file, so none of this is trusted downstream."""
    n = len(series) + 1
    keep_run = int(round(max_still * fps))
    short = max(1, int(round(SHORT_RUN_S * fps)))
    if keep_run <= short:
        raise ValueError(f'--max-still must be over {SHORT_RUN_S}s so a kept still is never '
                         'mistaken for a stutter')
    held_src = set()
    for lo, hi in vv.hold_ranges(hold_spans, fps):
        held_src.update(range(lo, hi + 1))
    kept = list(range(n))
    reasons = {}

    def working():
        w = [series[kept[j + 1] - 1] for j in range(len(kept) - 1)]
        ex = [(j, j) for j in range(len(w)) if kept[j + 1] - 1 in held_src]
        return w, ex

    for _ in range(3):                      # a removal can expose a neighbour; 3 passes is ample
        w, ex = working()
        flagged = set(vv.stutter_frames(w, ex)[0])
        held_w = {j for j, _ in ex}
        drop = {}
        for run in _runs(w):
            if len(run) <= short and flagged & set(run) and not held_w & set(run):
                for j in run:
                    drop[kept[j + 1]] = 'stutter'
            elif len(run) > keep_run:
                for j in run[keep_run:]:
                    drop[kept[j + 1]] = 'long_freeze'
        if not drop:
            break
        reasons.update(drop)
        kept[:] = [k for k in kept if k not in drop]
    return sorted(reasons), reasons


def _spans(removed, reasons, fps):
    out = []
    for k in removed:
        why = reasons.get(k, 'unspecified')
        if out and out[-1]['to_frame'] == k - 1 and out[-1]['reason'] == why:
            out[-1]['to_frame'] = k
        else:
            out.append({'from_frame': k, 'to_frame': k, 'reason': why})
    for s in out:
        s['from_s'] = round(s['from_frame'] / fps, 3)
        s['to_s'] = round((s['to_frame'] + 1) / fps, 3)
    return out


def write_cut(src, removed, reasons, enforce_cap=True, replace=False):
    """Encode the cut and write its manifest. Returns (exit_code, message).

    enforce_cap=False exists ONLY so the tests can build the forged cuts verify must refuse."""
    man, fps, series, why = _load_source(src)
    if why:
        return 1, why
    n_src = len(series) + 1
    removed = sorted(set(removed))
    pct = 100.0 * len(removed) / n_src
    if enforce_cap and pct > vv.MAX_CUT_PCT:
        return 1, (f'refused: the cut would remove {pct:.0f}% of the clip ({len(removed)}/{n_src} '
                   f'frames), above the {vv.MAX_CUT_PCT:.0f}% cap — this clip needs a re-record')
    stem = src[:-4]
    out, outman = stem + '_cut.mp4', stem + '_cut.capture.json'
    if not replace and (os.path.exists(out) or os.path.exists(outman)):
        return 1, f'{os.path.basename(out)} already exists — pass --replace-cut to overwrite it'
    tmp = stem + '_cut.part.mp4'
    # Frame-exact by construction: decode to raw frames, drop the removed indices here, encode the
    # rest. A `select='not(between(n,a,b)+...)'` filter was used first and ffmpeg's expression
    # parser rejects it past ~95 terms (measured: 90 ok, 100 "Error while parsing expression") —
    # a real 25 fps clip needed 139 removals and could not be cut at all.
    info, _ = vv.probe(src)
    vs = next(s for s in info['streams'] if s.get('codec_type') == 'video')
    w, h = int(vs['width']), int(vs['height'])
    frame_bytes = w * h * 3 // 2                          # yuv420p
    dec_cmd = ['ffmpeg', '-v', 'error', '-i', src, '-map', '0:v:0', '-fps_mode', 'passthrough',
               '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-']
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p',
           '-s', f'{w}x{h}', '-r', f'{fps:g}', '-color_range', 'tv', '-i', '-',
           '-an', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p',
           '-color_range', 'tv', '-movflags', '+faststart', '-f', 'mp4', tmp]
    gone = set(removed)
    dec = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    idx = 0
    try:
        while True:
            buf = dec.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            if idx not in gone:
                enc.stdin.write(buf)
            idx += 1
    finally:
        enc.stdin.close()
    dec_err = dec.stderr.read().decode(errors='replace')
    enc_err = enc.stderr.read().decode(errors='replace')
    dec.wait()
    enc.wait()
    if dec.returncode != 0 or enc.returncode != 0 or idx != n_src:
        if os.path.exists(tmp):
            os.remove(tmp)
        return 2, (f're-encode failed (decoded {idx}/{n_src} frames): '
                   f'{(dec_err or enc_err).strip()[:300]}')
    n_cut = vv.count_frames(tmp)
    if n_cut != n_src - len(removed):
        os.remove(tmp)
        return 2, (f'encoded cut has {n_cut} frames, expected {n_src - len(removed)} — '
                   'nothing written')
    os.replace(tmp, out)

    srcman = stem + '.capture.json'
    new = dict(man)
    new['name'] = os.path.basename(stem) + '_cut'
    new['video'] = os.path.basename(out)
    new['framesKept'] = n_cut
    new['spanSeconds'] = round(n_cut / fps, 3)
    new['holdSpans'] = vv.remap_holds(man.get('holdSpans'), removed, fps, n_cut)
    new['holds'] = len(new['holdSpans'])
    new['encoderArgs'] = (' '.join(shlex.quote(c) for c in cmd[3:-1]) + ' ' + os.path.basename(out)
                          + f'  (raw frames of {os.path.basename(src)} minus edit.removed_frames)')
    new['edit'] = {
        'tool': TOOL, 'version': VERSION,
        'source_file': os.path.basename(src), 'source_sha256': vv.sha256_of(src),
        'source_manifest': os.path.basename(srcman), 'source_manifest_sha256': vv.sha256_of(srcman),
        'output_sha256': vv.sha256_of(out),
        'fps': fps, 'source_frames': n_src, 'output_frames': n_cut,
        'removed_frames': removed, 'removed_pct': round(pct, 2),
        'removed_spans': _spans(removed, reasons, fps),
        'thresholds': {'move': vv.MOTION_MOVE, 'dup': vv.MOTION_DUP, 'win': vv.MOTION_WIN},
        'source_capture': {k: man.get(k) for k in ('framesKept', 'spanSeconds', 'holdSpans')},
    }
    part = outman + '.part'
    with open(part, 'w', encoding='utf-8') as fh:
        json.dump(new, fh, ensure_ascii=False, indent=2)
    os.replace(part, outman)
    return 0, (f'CUT {os.path.basename(out)}: removed {len(removed)}/{n_src} frames '
               f'({pct:.1f}%), {n_src / fps:.2f}s -> {n_cut / fps:.2f}s')


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return 2
    max_still, dry, replace, files = DEFAULT_MAX_STILL, False, False, []
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--max-still':
            i += 1
            max_still = float(args[i])
        elif a == '--dry-run':
            dry = True
        elif a == '--replace-cut':
            replace = True
        else:
            files.append(a)
        i += 1
    if len(files) != 1:
        print('error: give exactly one clip', file=sys.stderr)
        return 2
    src = files[0]
    man, fps, series, why = _load_source(src)
    if why:
        print(f'REFUSED  {os.path.basename(src)}: {why}')
        return 1
    try:
        removed, reasons = plan(series, fps, man.get('holdSpans'), max_still)
    except ValueError as ex:
        print(f'error: {ex}', file=sys.stderr)
        return 2
    n_src = len(series) + 1
    pct = 100.0 * len(removed) / n_src
    print(f'PLAN  {os.path.basename(src)}: {n_src} frames @ {fps:g} fps, remove {len(removed)} '
          f'({pct:.1f}%) — ' + ', '.join(f"{s['reason']} {s['from_s']:.2f}-{s['to_s']:.2f}s"
                                          for s in _spans(removed, reasons, fps)[:12]))
    if not removed:
        print('nothing frozen to cut — verify the original as it is')
        return 0
    if dry:
        return 0 if pct <= vv.MAX_CUT_PCT else 1
    rc, msg = write_cut(src, removed, reasons, replace=replace)
    print(msg)
    if rc == 0:
        print(f'next: verify-video.py {src[:-4]}_cut.mp4')
    return rc


if __name__ == '__main__':
    sys.exit(main())
