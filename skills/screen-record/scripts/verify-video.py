#!/usr/bin/env python3
"""verify-video.py — measure a recording against the spec instead of eyeballing it.

    verify-video.py <file.mp4> [...] [--min-seconds 5] [--width 1920] [--height 1080] [--expect-audio]

Covers the machine-checkable half of the 7-layer gate (references/quality-gate.md):

    layer 1  resolution, codec, pixel format, and that the encode did not blur the text
    layer 6  the file plays end to end, is not blank, is not truncated, and is named correctly

The other layers — whole flow, reached the target, expected result on screen, legible wording,
attached-and-resolves — are about *content*, and no probe can judge them. This script passing is
therefore necessary, never sufficient: it says the file is sound, not that the clip proves anything.

Exit 0 = every file passed. Exit 1 = at least one failed. Exit 2 = could not run (missing ffprobe,
missing file) — which is NOT a pass; a check that could not run has proven nothing.
"""

import json
import os
import re
import subprocess
import sys

MIN_SECONDS = 5.0
WANT_W, WANT_H = 1920, 1080
# Blankness is measured as the per-frame luma RANGE (YMAX - YMIN), sampled once a second.
# A solid fill gives 0 — measured: a gray test clip reports YMIN=YMAX=126. Any real screen has
# near-black text on a near-white ground and reports well over 200. 24 sits far from both, so a
# dark-themed or dimmed UI is not mistaken for a blank recording.
BLANK_LUMA_RANGE = 24


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def have(binary):
    return subprocess.run(['which', binary], capture_output=True).returncode == 0


def probe(path):
    r = run(['ffprobe', '-v', 'error', '-print_format', 'json',
             '-show_format', '-show_streams', path])
    if r.returncode != 0:
        return None, r.stderr.strip()[:200]
    try:
        return json.loads(r.stdout), None
    except json.JSONDecodeError as e:
        return None, f'ffprobe output not JSON: {e}'


def luma_range(path):
    """Largest per-frame luma range (YMAX - YMIN) over one sampled frame per second.
    0 means every sampled frame was a single flat colour — nothing was captured.

    signalstats writes its numbers to **stderr** at info level, and `-show_entries
    frame_tags=` comes back empty on ffmpeg 8, so the values are parsed from the
    `metadata=print` output instead. Returns None only if ffmpeg itself failed."""
    r = run(['ffmpeg', '-i', path, '-vf', 'fps=1,signalstats,metadata=print', '-f', 'null', '-'])
    if not r.stderr:
        return None
    ymin = None
    best = None
    for key, val in re.findall(r'lavfi\.signalstats\.(YMIN|YMAX)=([0-9.]+)', r.stderr):
        v = float(val)
        if key == 'YMIN':
            ymin = v                       # signalstats emits YMIN before YMAX, once per frame
        elif ymin is not None:
            rng = v - ymin
            best = rng if best is None else max(best, rng)
            ymin = None
    return best


def decodes_cleanly(path):
    """Decode the whole file and report whether it played through without errors.

    This is the honest form of 'plays start to end, not truncated': a header can survive a
    truncation that the frames do not. Any decoder complaint on stderr is a failure."""
    r = run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'null', '-'])
    if r.returncode != 0:
        return False, (r.stderr.strip().splitlines() or ['decode failed'])[0][:160]
    if r.stderr.strip():
        return False, r.stderr.strip().splitlines()[0][:160]
    return True, None


def faststart(path):
    """True when `moov` precedes `mdat` — the layout that lets a player start without the
    whole file. Read from the bytes; ffprobe does not report it."""
    try:
        with open(path, 'rb') as fh:
            head = fh.read(2 * 1024 * 1024)
    except OSError:
        return False
    moov, mdat = head.find(b'moov'), head.find(b'mdat')
    if moov == -1:
        return False          # moov not even in the first 2 MB → definitely not faststart
    return mdat == -1 or moov < mdat


def check(path, min_seconds, want_w, want_h, expect_audio=False):
    fails, warns = [], []

    if not os.path.isfile(path):
        return [f'file not found: {path}'], []
    if os.path.getsize(path) == 0:
        return ['file is 0 bytes'], []

    info, err = probe(path)
    if info is None:
        return [f'unreadable / not a valid video: {err}'], []

    vs = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), None)
    if vs is None:
        return ['no video stream'], []

    w, h = vs.get('width'), vs.get('height')
    if (w, h) != (want_w, want_h):
        # Smaller than asked for blurs text (layer 1). Larger is fine.
        if (w or 0) < want_w or (h or 0) < want_h:
            fails.append(f'resolution {w}x{h} is below the required {want_w}x{want_h} — text will not be legible')
        else:
            warns.append(f'resolution {w}x{h} differs from {want_w}x{want_h} (larger, allowed)')

    if vs.get('codec_name') != 'h264':
        fails.append(f"codec is {vs.get('codec_name')}, expected h264")
    if vs.get('pix_fmt') != 'yuv420p':
        fails.append(f"pix_fmt is {vs.get('pix_fmt')}, expected yuv420p (other formats fail in some players)")

    dur = info.get('format', {}).get('duration')
    try:
        dur = float(dur)
    except (TypeError, ValueError):
        dur = None
    if dur is None:
        fails.append('duration missing — the file is likely truncated')
    elif dur < min_seconds:
        fails.append(f'duration {dur:.1f}s is under the {min_seconds:.0f}s minimum — a clip this short cannot show a flow')

    ok, why = decodes_cleanly(path)
    if not ok:
        fails.append(f'does not decode end to end (truncated or corrupt): {why}')

    rng = luma_range(path)
    if rng is None:
        fails.append('blank-frame check could not run — a check that cannot run is not a pass')
    elif rng < BLANK_LUMA_RANGE:
        fails.append(f'frames are effectively blank (max luma range {rng:.0f}) — nothing was captured')

    if not faststart(path):
        fails.append('not +faststart (moov after mdat) — may not stream/preview in the browser')

    # Narration was asked for, so a silent file is a failure, not a variant.
    astream = next((s for s in info.get('streams', []) if s.get('codec_type') == 'audio'), None)
    if expect_audio:
        if astream is None:
            fails.append('narration was requested but the file has no audio stream — '
                         'run narrate.py, then re-check')
        else:
            adur = astream.get('duration')
            try:
                adur = float(adur)
            except (TypeError, ValueError):
                adur = None
            if adur is not None and adur < 1.0:
                fails.append(f'audio stream is only {adur:.1f}s — narration did not land')
            if dur and adur and adur > dur + 0.5:
                warns.append(f'narration ({adur:.1f}s) outlasts the video ({dur:.1f}s) — the tail is cut off')
    elif astream is not None:
        warns.append('file has an audio track but narration was not expected for this run')

    if not re.match(r'^[A-Za-z0-9._-]+\.mp4$', os.path.basename(path)):
        warns.append('file name has spaces or unusual characters — rename before attaching')

    return fails, warns


def main():
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return 2

    min_seconds, want_w, want_h, files = MIN_SECONDS, WANT_W, WANT_H, []
    expect_audio = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--expect-audio':
            expect_audio = True
        elif a == '--min-seconds':
            i += 1; min_seconds = float(args[i])
        elif a == '--width':
            i += 1; want_w = int(args[i])
        elif a == '--height':
            i += 1; want_h = int(args[i])
        else:
            files.append(a)
        i += 1

    if not files:
        print('error: no files given', file=sys.stderr)
        return 2
    missing = [b for b in ('ffprobe', 'ffmpeg') if not have(b)]
    if missing:
        print(f"error: {' and '.join(missing)} not found — run preflight.sh --install. "
              'A check that cannot run is not a pass.', file=sys.stderr)
        return 2

    bad = 0
    for f in files:
        fails, warns = check(f, min_seconds, want_w, want_h, expect_audio)
        name = os.path.basename(f)
        if fails:
            bad += 1
            print(f'FAIL  {name}')
            for m in fails:
                print(f'        ✗ {m}')
        else:
            print(f'PASS  {name}')
        for m in warns:
            print(f'        ! {m}')

    print()
    print(f'RESULT: {len(files) - bad}/{len(files)} passed'
          + ('' if bad else '  (layers 1 & 6 only — content layers 2-5 & 7 are judged by a human)'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
