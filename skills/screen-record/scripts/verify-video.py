#!/usr/bin/env python3
"""verify-video.py — measure a recording against the spec instead of eyeballing it.

    verify-video.py <file.mp4> [...] [--min-seconds 5] [--width 1920] [--height 1080]
                                     [--expect-audio] [--no-manifest]

Covers the machine-checkable half of the 7-layer gate (references/quality-gate.md):

    layer 1   resolution, codec, pixel format, and that the encode did not blur the text
    layer 1b  the picture is STEADY — no frozen frames inside a moving stretch
    layer 1c  provenance — the clip came from this skill's recorder, at the rate it claims
    layer 6   the file plays end to end, is not blank, is not truncated, and is named correctly

Layers 1b and 1c exist because a 1920x1080 / h264 / yuv420p clip passed every other check here
while visibly flickering (ELMS-2.4.1, 2026-08-27). Being big enough and in the right codec says
nothing about whether frames arrived on time or whether the encoder was starved.

`--no-manifest` downgrades the missing-manifest failure to a warning. It is for inspecting a clip
this skill did not record. A DELIVERABLE checked that way has not passed layer 1c.

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
# Share of MOVING frames allowed to be frozen repeats before the clip counts as juddering. See
# stutter_ratio() for how this number was measured rather than chosen.
MAX_STUTTER_PCT = 5.0
# The only recorder whose output may be delivered. record.js stamps this into the capture manifest.
GOOD_PIPELINE = 'cdp-screencast->x264'


def eval_fps(rate):
    """'25/1' -> 25.0. Returns None on anything unparseable."""
    try:
        num, _, den = str(rate).partition('/')
        return float(num) / float(den or 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


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


def motion_series(path):
    """Mean absolute difference between each pair of consecutive frames, 0-255, one value per pair.

    Computed entirely inside ffmpeg — `tblend=all_mode=difference` then signalstats' YAVG — so this
    needs no numpy and no Pillow and runs wherever the rest of the script runs. Downscaled to
    320x180 first: the metric is about WHOLE-FRAME steadiness, and small is 20x faster.

    Returns None only when ffmpeg itself failed."""
    r = run(['ffmpeg', '-i', path, '-vf',
             'scale=320:180,format=gray,tblend=all_mode=difference,'
             'signalstats,metadata=print:key=lavfi.signalstats.YAVG',
             '-f', 'null', '-'])
    if not r.stderr:
        return None
    # ffmpeg prints a very small YAVG in scientific notation (`1.73611e-05` — one changed
    # pixel out of 320x180). A `[0-9.]+` class stops at the `e`, so that value parses as
    # **1.736** — a hundred thousand times too big, above the 0.35 motion threshold. Every
    # static frame then reads as "moving", and the identical frames beside it as frozen
    # repeats, so a clip of still pages scores 60-85% stutter with nothing wrong in it.
    vals = [float(v) for v in re.findall(r'lavfi\.signalstats\.YAVG=([0-9.]+(?:[eE][+-]?[0-9]+)?)', r.stderr)]
    return vals or None


def stutter_ratio(series, excluded=None):
    """Fraction of MOVING frames that are byte-for-byte repeats of the frame before them.

    This is the judder half of the flicker defect, and the scoping is the whole point. A raw
    duplicate-frame count cannot be used: a clip that legitimately rests on one screen for three
    seconds is nearly all duplicates and is perfectly good. What is never good is a repeated frame
    sitting INSIDE a stretch that is moving — that is the recorder failing to deliver, and the eye
    reads it as a stutter.

    So a frame counts only when the motion around it (median of the ±6 neighbours, excluding
    itself) says the picture is in motion. Returns (stutter_pct, moving_frames).

    Measured, not guessed — the delivered ELMS-2.4.1 clip that prompted this check scores 21.2%,
    while six clips judged good (three from each pipeline, static-heavy and motion-heavy) score
    0.00-1.44%. The 5% threshold sits ~3.5x above the worst good clip and ~4x below the bad one.

    `excluded` holds the still-hold spans the recorder DECLARED, as (first, last) frame indices.
    They have to be excluded or the check contradicts another fix: capture pauses across each
    `expect` shutter so the pointer cannot blink out of the video, which deliberately repeats one
    frame — and on a page with a background animation that is indistinguishable from a stall.
    Measured: a clip captured at 51.9 fps with an 18 ms p95 gap, i.e. objectively healthy, scored
    5.3% and failed purely on its three holds. The caller bounds how much may be excluded."""
    flagged, moving = stutter_frames(series, excluded)
    return (100.0 * len(flagged) / moving if moving else 0.0), moving


# The detector's thresholds. freeze_cut.py imports these (and stutter_frames) rather than copying
# them, so the tool that removes frozen frames and the check that judges the result cannot drift.
MOTION_MOVE, MOTION_DUP, MOTION_WIN = 0.35, 0.02, 6


def stutter_frames(series, excluded=None):
    """The detector behind stutter_ratio(): (indices into `series` that are frozen repeats inside
    motion, count of moving frames). series[i] is the difference between frame i+1 and frame i —
    measured on a clip whose frames 9 and 10 were identical (PSNR 68 dB): series[9] was ~0 — so a
    flagged index i means FRAME i+1 repeats frame i."""
    held = set()
    for lo, hi in (excluded or []):
        held.update(range(max(0, lo), hi + 1))
    flagged, moving = [], 0
    for i, v in enumerate(series):
        if i in held:
            continue
        lo, hi = max(0, i - MOTION_WIN), min(len(series), i + MOTION_WIN + 1)
        nb = sorted(series[lo:i] + series[i + 1:hi])
        if not nb:
            continue
        if nb[len(nb) // 2] > MOTION_MOVE:   # the neighbourhood is moving
            moving += 1
            if v < MOTION_DUP:               # ...but this frame did not change at all
                flagged.append(i)
    return flagged, moving


def hold_ranges(spans, fps):
    """Declared still-hold spans (seconds) -> (first, last) series indices, the conversion check()
    uses for exclusion. Malformed spans are skipped exactly as check() skips them."""
    out = []
    for span in (spans or []):
        try:
            lo = int(round(float(span['from']) * fps))
            hi = int(round(float(span['to']) * fps))
        except (KeyError, TypeError, ValueError):
            continue
        if hi >= lo:
            out.append((lo, hi))
    return out


# ---- sanctioned freeze-cut (freeze-cut.py) ---------------------------------------------------
# Owner order 2026-10-11: a clip that shows the whole ER but stutters/freezes in places is fixed by
# cutting the frozen frames out, never by re-recording. A cut file is only as trustworthy as the
# proof that what was removed was frozen, so the proof is re-derived HERE from the untouched source
# — the edit record is a claim, this is the check of it.
MAX_CUT_PCT = 60.0      # a cut that removes more than 60% of a clip is a re-record case
CUT_NAME_RE = re.compile(r'_cut\.mp4$')


def sha256_of(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def count_frames(path):
    r = run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
             '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', path])
    try:
        return int(r.stdout.strip().split(',')[0])
    except (ValueError, IndexError):
        return None


def remap_holds(spans, removed, fps, n_out):
    """Where each declared hold lands once `removed` source frames are gone: a source time t maps
    to (kept frames before frame round(t*fps)) / fps, clamped to the cut's length. A hold that
    collapses to nothing is dropped."""
    gone = sorted(set(removed))
    dur = n_out / fps
    out = []

    def shift(t):
        f = int(round(float(t) * fps))
        import bisect
        return max(0.0, min(dur, (f - bisect.bisect_left(gone, f)) / fps))

    for span in (spans or []):
        try:
            a, b = shift(span['from']), shift(span['to'])
        except (KeyError, TypeError, ValueError):
            continue
        if b > a:
            out.append({'from': round(a, 3), 'to': round(b, 3)})
    return out


def check_edit(path, man, fps):
    """Every way a cut can fail to prove itself, as a list of failure strings (empty = proven)."""
    fails = []
    e = man.get('edit')
    if not isinstance(e, dict):
        return ['edit record is not an object — the cut cannot be traced to a source']
    here = os.path.dirname(os.path.abspath(path))
    sname, mname = e.get('source_file'), e.get('source_manifest')
    for label, n in (('source_file', sname), ('source_manifest', mname)):
        if not isinstance(n, str) or not n or os.path.basename(n) != n:
            return [f'edit record {label} {n!r} must be a bare file name beside the cut']
    src, smanp = os.path.join(here, sname), os.path.join(here, mname)
    if os.path.basename(path) == sname:
        return ['edit record names the cut itself as its source']
    if not os.path.isfile(src):
        return [f'edit record source {sname!r} not found beside the cut — the removed frames '
                'cannot be re-checked, so the cut proves nothing (keep the original)']
    if not os.path.isfile(smanp):
        return [f'edit record source manifest {mname!r} not found beside the cut']
    if sha256_of(src) != e.get('source_sha256'):
        fails.append(f'source {sname!r} sha256 does not match the edit record — the source '
                     'changed after the cut, or the record was edited')
    if sha256_of(smanp) != e.get('source_manifest_sha256'):
        fails.append(f'source manifest {mname!r} sha256 does not match the edit record')
    if sha256_of(path) != e.get('output_sha256'):
        fails.append('cut file sha256 does not match the edit record output_sha256 — the cut '
                     'file was replaced after it was made')
    if fails:
        return fails
    try:
        with open(smanp, encoding='utf-8') as fh:
            sman = json.load(fh)
    except (OSError, json.JSONDecodeError) as ex:
        return [f'source manifest unreadable: {ex}']
    if sman.get('video') != sname:
        fails.append(f"source manifest describes {sman.get('video')!r}, not the source {sname!r}")
    if sman.get('edit'):
        fails.append('the source is itself a cut — cut the original recording, not a cut of it')

    removed = e.get('removed_frames')
    if not isinstance(removed, list) or not all(isinstance(k, int) for k in removed):
        return fails + ['edit record removed_frames must be a list of source frame indices']
    if len(set(removed)) != len(removed):
        fails.append('edit record removed_frames lists a frame twice')
    series = motion_series(src)
    if series is None:
        return fails + ['motion check on the source could not run — the cut cannot be proven']
    n_src = len(series) + 1
    pct = 100.0 * len(set(removed)) / n_src
    if pct > MAX_CUT_PCT:
        fails.append(f'the cut removed {pct:.0f}% of the source ({len(set(removed))}/{n_src} '
                     f'frames), above the {MAX_CUT_PCT:.0f}% cap — this needs a re-record, not a cut')
    bad = [k for k in removed if not (1 <= k < n_src) or series[k - 1] >= MOTION_DUP]
    if bad:
        fails.append(f'{len(bad)} removed frame(s) are not a frozen repeat of the frame before '
                     f'them in the source (first: {bad[:5]}) — the cut took out real picture')
    n_cut = count_frames(path)
    if n_cut is None or n_cut != n_src - len(set(removed)):
        fails.append(f'cut file has {n_cut} frames, expected {n_src - len(set(removed))} '
                     f'({n_src} source - {len(set(removed))} removed) — it is not this cut of this source')
    src_info, _ = probe(src)
    sv = next((s for s in (src_info or {}).get('streams', []) if s.get('codec_type') == 'video'), {})
    src_fps = eval_fps(sv.get('r_frame_rate'))
    if src_fps is None or abs(src_fps - fps) > 0.01:
        fails.append(f'cut is {fps:g} fps but the source is {src_fps} fps — a cut must not re-time')
    if n_cut and not fails:
        want = remap_holds(sman.get('holdSpans'), removed, fps, n_cut)
        got = man.get('holdSpans') or []
        try:
            same = len(want) == len(got) and all(
                abs(float(a['from']) - float(b['from'])) <= 1.0 / fps and
                abs(float(a['to']) - float(b['to'])) <= 1.0 / fps for a, b in zip(want, got))
        except (KeyError, TypeError, ValueError):
            same = False
        if not same:
            fails.append('cut manifest holdSpans are not the source holds remapped through the '
                         'cut — a cut may not declare new holds')
    return fails


def read_manifest(path):
    """The `<name>.capture.json` written by record.js, or (None, why)."""
    guess = re.sub(r'\.mp4$', '', path) + '.capture.json'
    if not os.path.isfile(guess):
        return None, f'no capture manifest beside the file ({os.path.basename(guess)})'
    try:
        with open(guess, encoding='utf-8') as fh:
            return json.load(fh), None
    except (OSError, json.JSONDecodeError) as e:
        return None, f'capture manifest unreadable: {e}'


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


def check(path, min_seconds, want_w, want_h, expect_audio=False, require_manifest=True):
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

    # ---- layer 1c: provenance — which pipeline produced this file -------------------------
    # The flicker was not a setting anyone chose; it was baked into Playwright's own recordVideo
    # (1 Mbps VP8, realtime, plus fixed-rate frame padding). No probe of the finished mp4 can tell
    # which recorder made it, so record.js writes a manifest and this checks it. A missing manifest
    # is a FAIL, not a shrug: ตรวจไม่ได้ = ไม่ผ่าน.
    man, why = read_manifest(path)
    if man is None:
        (fails if require_manifest else warns).append(
            f'{why} — cannot prove which recorder produced this clip')
    else:
        if man.get('pipeline') != GOOD_PIPELINE:
            fails.append(f"capture pipeline is {man.get('pipeline')!r}, expected "
                         f'{GOOD_PIPELINE!r} — this clip came from the recorder that flickers')
        if man.get('overBudget'):
            fails.append('capture hit its scratch budget and stopped early — the clip is cut short')
        if man.get('writeErrors'):
            fails.append(f"{man['writeErrors']} frames failed to write during capture — "
                         'the clip is missing picture it should have')
        uf, floor = man.get('uniqueFps'), man.get('minUniqueFps')
        if uf is not None and floor is not None and uf < floor:
            fails.append(f'capture ran at {uf} unique fps against its own {floor} floor — '
                         'the clip shows fewer real frames than it claims')
        # A manifest that does not describe THIS file proves nothing about it.
        if man.get('video') and man['video'] != os.path.basename(path):
            fails.append(f"manifest describes {man['video']!r}, not this file")
        mv = man.get('viewport') or {}
        if mv.get('width') and (mv['width'], mv.get('height')) != (w, h):
            fails.append(f"manifest records a {mv.get('width')}x{mv.get('height')} capture but the "
                         f'file is {w}x{h} — they are not the same recording')
        try:
            declared = float(man.get('outFps'))
            actual = eval_fps(vs.get('r_frame_rate'))
            if actual and abs(actual - declared) > 0.51:
                fails.append(f'manifest says {declared:g} fps, the file is {actual:g} fps')
        except (TypeError, ValueError):
            pass
        # A cut is accepted only with an edit record that proves, from the source on disk, that
        # every removed frame was a frozen repeat (freeze-cut.py writes it; check_edit re-derives it).
        if 'edit' in man:
            fps_cut = eval_fps(vs.get('r_frame_rate'))
            fails.extend(check_edit(path, man, fps_cut) if fps_cut else
                         ['cut file frame rate unreadable — the edit record cannot be checked'])
        elif CUT_NAME_RE.search(os.path.basename(path)):
            fails.append('this is a cut (*_cut.mp4) but its manifest carries no edit record — cut '
                         'with freeze-cut.py so the removed frames can be proven frozen')

    # ---- layer 1b: the picture is STEADY, not merely large enough -------------------------
    # Added after a 1920x1080 / h264 / yuv420p clip passed every check above while visibly
    # flickering. Resolution and codec say nothing about whether frames arrive on time or whether
    # the encoder was starved; these two checks are what closes that hole.
    # Still-hold spans the recorder declared, converted onto the output frame grid. Excluding them
    # is required (see stutter_ratio) but must not become a loophole, so the total is capped: a
    # manifest that declares most of the clip held has explained nothing.
    excluded, held_frames = [], 0
    fps_out = eval_fps(vs.get('r_frame_rate')) or 25.0
    for span in ((man or {}).get('holdSpans') or []):
        try:
            lo = int(round(float(span['from']) * fps_out))
            hi = int(round(float(span['to']) * fps_out))
        except (KeyError, TypeError, ValueError):
            continue
        if hi >= lo:
            excluded.append((lo, hi))
            held_frames += hi - lo + 1

    series = motion_series(path)
    if series is None:
        fails.append('motion check could not run — a check that cannot run is not a pass')
    else:
        if held_frames > 0.25 * len(series):
            fails.append(f'the capture manifest declares {100.0 * held_frames / len(series):.0f}% '
                         'of the clip as still-holds — too much of it is a frozen frame to judge, '
                         'and too much to deliver')
        pct, moving = stutter_ratio(series, excluded)
        if moving < 25:
            warns.append(f'too little motion to judge stutter ({moving} moving frames) — '
                         'a clip this static cannot judder, but nothing was proven either')
        elif pct > MAX_STUTTER_PCT:
            fails.append(f'{pct:.1f}% of the moving frames are frozen repeats (limit '
                         f'{MAX_STUTTER_PCT:.0f}%) — the recording stalled mid-motion and the '
                         'clip will visibly stutter')

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
    require_manifest = True
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--expect-audio':
            expect_audio = True
        elif a == '--no-manifest':
            # Only for a clip this skill did not record. A deliverable without its manifest has
            # not proven which recorder made it, and forfeits layer 1c.
            require_manifest = False
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
        fails, warns = check(f, min_seconds, want_w, want_h, expect_audio, require_manifest)
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
          + ('' if bad else '  (layers 1/1b/1c & 6 only — content layers 2-5 & 7 are judged by a human)'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
