#!/usr/bin/env python3
"""check-narration.py — prove a narrated clip still sounds like the voice that was approved.

`verify-video.py` proves the picture is to spec. Nothing proved the *voice* was, and the voice is
what drifted: a tone preset silently overrode the play file's prosody, and a clip shipped 23 Hz
below the timbre the user had approved by ear. It read as "female Vivienne" in every log and every
setting, and only measurement caught it.

So this measures the audio and compares it to a stored profile:

  * an audio stream exists at all (a muxing failure is silent otherwise),
  * the median speaking pitch sits inside the profile's band,
  * the Thai sentence-final particle closes the greeting — heard as a real pause after ค่ะ / ครับ
    rather than the particle running into the next word,
  * nothing clips.

Exit 0 all green · 1 a check failed · 2 the check could not run. **2 is not a pass** — an
unmeasurable clip is an unverified clip.

    check-narration.py --profile female clip.mp4
    check-narration.py --profile male --no-greeting-pause other.mp4
    check-narration.py --print-only clip.mp4        # just report the numbers

Profiles live in references/voice-profile.md; the numbers here are that file in executable form.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

# --------------------------------------------------------------------------- approved profiles
#
# Measured from the two clips the user approved on 2026-08-18 (OLS login walkthrough, Thai).
# `f0` is the median speaking pitch over voiced frames; the band is deliberately wide enough for a
# different script in the same voice and narrow enough to catch a tone preset damping the voice
# (the real defect was 23 Hz low, less than half this band away from the edge).
PROFILES = {
    'male': {
        'voice': 'ko-KR-HyunsuMultilingualNeural',
        'tone': 'mellow', 'rate': '+0%', 'pitch': '-6Hz', 'volume': '-13%',
        'f0': 120.0, 'f0_tol': 15.0,
        'particle': 'ครับ',
    },
    'female': {
        'voice': 'fr-FR-VivienneMultilingualNeural',
        'tone': 'mellow', 'rate': '+0%', 'pitch': '+12Hz', 'volume': '+0%',
        'f0': 195.0, 'f0_tol': 18.0,
        'particle': 'ค่ะ',
    },
}

# The greeting particle must end the first phrase, so a real gap follows it. Anything shorter than
# this is the particle running into the next word — the "สวัสดี · คะวันนี้" defect.
GREETING_PAUSE_MIN = 0.45      # seconds of silence
GREETING_PAUSE_BY = 3.0        # ...and it has to happen this early, i.e. after the greeting


def die(msg):
    print(f'error: {msg}', file=sys.stderr)
    sys.exit(2)


def ffmpeg_bin(name):
    p = shutil.which(name)
    if not p:
        die(f'{name} not found — run preflight.sh --install')
    return p


def has_audio(path):
    out = subprocess.run([ffmpeg_bin('ffprobe'), '-v', 'error', '-select_streams', 'a',
                          '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', path],
                         capture_output=True, text=True).stdout.strip()
    return out.splitlines()[0] if out else ''


def peak_db(path):
    out = subprocess.run([ffmpeg_bin('ffmpeg'), '-hide_banner', '-i', path,
                          '-af', 'astats=metadata=1', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    vals = [float(m) for m in re.findall(r'Peak level dB:\s*(-?\d+\.?\d*)', out)]
    return max(vals) if vals else None


def first_gap(path, upto=8.0, floor='-40dB', minlen=0.20):
    """(start, duration) of the first silence in the opening seconds, or None."""
    out = subprocess.run([ffmpeg_bin('ffmpeg'), '-hide_banner', '-t', str(upto), '-i', path,
                          '-af', f'silencedetect=noise={floor}:d={minlen}', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    starts = [float(m) for m in re.findall(r'silence_start:\s*(-?\d+\.?\d*)', out)]
    durs = [float(m) for m in re.findall(r'silence_duration:\s*(\d+\.?\d*)', out)]
    if not starts or not durs:
        return None
    return starts[0], durs[0]


def median_f0(path):
    """Median speaking pitch, by autocorrelation over 40 ms windows of 16 kHz mono."""
    try:
        import numpy as np
    except ImportError:
        die('numpy is required to measure pitch — run preflight.sh --install '
            '(a pitch check that cannot run is not a pass)')
    raw = subprocess.run([ffmpeg_bin('ffmpeg'), '-v', 'error', '-i', path,
                          '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    if x.size < 16000:
        return None, 0
    sr, win, hop = 16000, 640, 160
    lo, hi = sr // 400, sr // 70          # 70–400 Hz covers both a low male and a high female voice
    picks = []
    for i in range(0, x.size - win, hop):
        seg = x[i:i + win]
        if np.sqrt((seg ** 2).mean()) < 0.01:      # unvoiced / silence
            continue
        seg = seg - seg.mean()
        ac = np.correlate(seg, seg, 'full')[win - 1:]
        if hi >= ac.size:
            continue
        p = int(np.argmax(ac[lo:hi])) + lo
        if ac[p] > 0.3 * ac[0]:                    # weak periodicity is not a pitch
            picks.append(sr / p)
    if not picks:
        return None, 0
    a = np.array(picks)
    return float(np.median(a)), a.size


def check(path, prof, greeting_pause, print_only):
    name = os.path.basename(path)
    if not os.path.exists(path):
        die(f'{path}: no such file')
    notes, failed = [], False

    codec = has_audio(path)
    if not codec:
        print(f'FAIL  {name}\n        ✗ no audio stream — narration never reached the file')
        return False
    notes.append(f'audio {codec}')

    f0, frames = median_f0(path)
    if f0 is None:
        print(f'FAIL  {name}\n        ✗ no voiced audio to measure')
        return False
    notes.append(f'pitch {f0:.1f}Hz over {frames} frames')

    if prof and not print_only:
        lo, hi = prof['f0'] - prof['f0_tol'], prof['f0'] + prof['f0_tol']
        if not (lo <= f0 <= hi):
            failed = True
            notes.append(f'✗ pitch {f0:.1f}Hz is outside the approved band {lo:.0f}-{hi:.0f}Hz '
                         f'for {prof["voice"]} — a tone preset is probably overriding the play '
                         f'file (expected rate {prof["rate"]}, pitch {prof["pitch"]}, '
                         f'volume {prof["volume"]})')

    if greeting_pause and not print_only:
        gap = first_gap(path)
        particle = prof['particle'] if prof else 'the particle'
        if gap is None:
            failed = True
            notes.append(f'✗ no pause at all in the opening — "{particle}" runs into the next word')
        else:
            start, dur = gap
            notes.append(f'first pause {dur:.2f}s at {start:.2f}s')
            if dur < GREETING_PAUSE_MIN or start > GREETING_PAUSE_BY:
                failed = True
                notes.append(f'✗ the greeting does not close on "{particle}" — expected a pause of '
                             f'at least {GREETING_PAUSE_MIN}s starting within {GREETING_PAUSE_BY}s')

    pk = peak_db(path)
    if pk is not None:
        notes.append(f'peak {pk:.1f}dB')
        if pk > -0.5 and not print_only:
            failed = True
            notes.append('✗ peaks at/over 0 dB — the track is clipping')

    head = 'INFO' if print_only else ('FAIL' if failed else 'PASS')
    print(f'{head}  {name}')
    for n in notes:
        print(f'        {"" if n.startswith("✗") else "· "}{n}')
    return print_only or not failed


def main():
    ap = argparse.ArgumentParser(description='Check a narrated clip against an approved voice profile.')
    ap.add_argument('files', nargs='+')
    ap.add_argument('--profile', choices=sorted(PROFILES), help='the approved voice this clip used')
    ap.add_argument('--no-greeting-pause', action='store_true',
                    help='the script has no sentence-final particle in its opening line')
    ap.add_argument('--print-only', action='store_true', help='report the numbers, judge nothing')
    a = ap.parse_args()

    if not a.profile and not a.print_only:
        die('pass --profile male|female (or --print-only to just read the numbers)')
    prof = PROFILES.get(a.profile)
    if prof:
        print(f'profile {a.profile}: {prof["voice"]}  tone {prof["tone"]}  '
              f'rate {prof["rate"]}  pitch {prof["pitch"]}  volume {prof["volume"]}  '
              f'→ {prof["f0"]:.0f}±{prof["f0_tol"]:.0f}Hz\n')

    ok = 0
    for f in a.files:
        if check(f, prof, not a.no_greeting_pause, a.print_only):
            ok += 1
    print(f'\nRESULT: {ok}/{len(a.files)} passed')
    sys.exit(0 if ok == len(a.files) else 1)


if __name__ == '__main__':
    main()
