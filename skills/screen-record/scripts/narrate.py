#!/usr/bin/env python3
"""narrate.py — speak a recorded clip's narration onto it, at the moments it belongs.

    narrate.py --prepare <play.json>     # pass 1 — measure each line, so recording can pace to it
    narrate.py <video.mp4> [--lang th|en] [--gender male|female] [--voice NAME] [--rate +4%] [--dry-run]

Reads `<video>.narration.json`, which `record.js` writes during the run: one line per step that
carried a `say`, each stamped with the millisecond it started. Timing is **measured, never
guessed** — a narration track laid out from estimated offsets drifts away from the thing it is
describing within a few steps.

What it does per line:

  1. splits the text into breath-sized phrases at natural boundaries;
  2. speaks each phrase with a neural voice;
  3. joins them with real pauses — longer at a sentence end than inside a clause;
  4. places each finished line at its measured offset in the video;
  5. normalizes the whole track to broadcast loudness and muxes it in, video stream untouched.

Voices are neural, in the language and gender chosen at intake — th-TH-NiwatNeural /
th-TH-PremwadeeNeural / en-US-GuyNeural / en-US-AriaNeural. A robotic
formant voice is what makes narration sound machine-made; macOS `say` cannot meet that bar for
Thai — its only Thai voice is female and audibly synthetic — so edge-tts is required, not
optional. It is free and needs no account; preflight.sh --install puts it in the skill's sandbox.

Exit 0 = narrated. 1 = a real failure. 2 = could not run (no edge-tts, no ffmpeg, no timeline).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

# Neural voices, natural enough to pass for a person reading a script. Both genders in both
# languages — the choice is the user's, asked at intake, never assumed.
VOICES = {
    ('th', 'male'): 'th-TH-NiwatNeural',
    ('th', 'female'): 'th-TH-PremwadeeNeural',
    ('en', 'male'): 'en-US-GuyNeural',
    ('en', 'female'): 'en-US-AriaNeural',
}
DEFAULT_GENDER = 'male'


def pick_voice(lang, gender):
    return VOICES.get((lang, (gender or DEFAULT_GENDER).lower()))
DEFAULT_RATE = '+4%'          # a touch above default reads as engaged rather than sleepy

# Pause lengths, in seconds. These are what turn a wall of speech into narration: a listener needs
# a beat to place the clause, and a longer one to close a sentence.
GAP_CLAUSE = 0.22
GAP_SENTENCE = 0.40

# Phrase ceilings. Thai has no inter-word spaces, so a "long" line hits the ear as one breathless
# run; these caps are in characters and are deliberately short.
MAX_TH = 62
MAX_EN = 95

# Thai connectives that a reader naturally pauses *before*. Splitting here — rather than at a fixed
# character count — is the difference between phrasing and chopping.
#
# Only words that genuinely START a clause belong here. Thai writes without spaces, so a particle
# that usually ENDS one will be found in the middle of a compound and cut it in half: breaking on
# 'แล้ว' turned "แสดงผลเรียบร้อยแล้ว" into "…เรียบร้อย" + "แล้ว ให้สังเกต…", which a listener hears as a
# stumble. Same reason 'ให้' is absent — it is bound inside ทำให้ / ส่งให้ far more often than it opens
# a clause. 'แล้วจึง' is safe because the pair only ever starts one.
TH_BREAKS = ['จากนั้น', 'หลังจากนั้น', 'ต่อมา', 'แล้วจึง', 'เพื่อให้', 'เพื่อ', 'โดยการ', 'โดย',
             'ซึ่ง', 'และ', 'หรือ', 'ถ้า', 'เมื่อ', 'ก่อนที่', 'หลังจาก', 'ระบบจะ', 'จะเห็น']
EN_BREAKS = [' and ', ' then ', ' so that ', ' which ', ' before ', ' after ', ' when ', ' if ',
             ' to ', ' with ']


# Every external call gets a deadline. A synth request that stalls with no timeout does not fail —
# it hangs the whole pass forever, which is exactly what happened: two `--prepare` runs sat on one
# voice until they were killed, while that same voice answered a single request in 3.9 s. A hang is
# harder to diagnose than an error, so nothing here is allowed to wait indefinitely.
def run(cmd, timeout=300, **kw):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kw)
    except subprocess.TimeoutExpired:
        class _Timeout:
            returncode = 124
            stdout = ''
            stderr = f'timed out after {timeout}s'
        return _Timeout()


def find_edge_tts():
    """Prefer the skill's sandboxed venv, then anything on PATH."""
    sandbox = os.path.expanduser('~/.manual-maker/runtime/tts/bin/edge-tts')
    if os.path.isfile(sandbox) and os.access(sandbox, os.X_OK):
        return sandbox
    found = shutil.which('edge-tts')
    return found


def split_phrases(text, lang):
    """Break one narration line into breath-sized phrases.

    Returns [(phrase, gap_after_seconds)]. The gap after the last phrase is 0 — spacing between
    lines comes from their measured offsets, not from padding."""
    text = re.sub(r'\s+', ' ', str(text)).strip()
    if not text:
        return []

    # Sentence level first: real punctuation is the strongest signal a writer gives us.
    sentences = [s for s in re.split(r'(?<=[.!?。])\s+|\n+', text) if s.strip()]

    out = []
    for si, sentence in enumerate(sentences):
        sentence = sentence.strip()
        # Then clause level, on punctuation the author actually wrote.
        clauses = [c for c in re.split(r'(?<=[,;:·])\s*', sentence) if c.strip()]
        pieces = []
        for clause in clauses:
            pieces.extend(_split_long(clause.strip(), lang))
        for pi, piece in enumerate(pieces):
            last_of_sentence = pi == len(pieces) - 1
            last_overall = last_of_sentence and si == len(sentences) - 1
            gap = 0.0 if last_overall else (GAP_SENTENCE if last_of_sentence else GAP_CLAUSE)
            out.append((piece, gap))
    return out


def _split_long(chunk, lang):
    """Split a clause that is still too long to say in one breath, at a connective if there is one."""
    limit = MAX_TH if lang == 'th' else MAX_EN
    breaks = TH_BREAKS if lang == 'th' else EN_BREAKS
    if len(chunk) <= limit:
        return [chunk]

    # Cut before the connective nearest the middle — a split there keeps both halves speakable.
    best, best_dist = None, None
    mid = len(chunk) / 2
    for word in breaks:
        start = 1
        while True:
            idx = chunk.find(word, start)
            if idx == -1:
                break
            # Refuse cuts that would leave a stub too short to be a phrase.
            if idx > 8 and len(chunk) - idx > 8:
                dist = abs(idx - mid)
                if best_dist is None or dist < best_dist:
                    best, best_dist = idx, dist
            start = idx + 1
    if best is None:
        # No natural seam. Fall back to a space (English) or a hard cut (Thai has none), still
        # aiming for the middle so neither half is a fragment.
        space = chunk.rfind(' ', 0, int(mid) + 20)
        best = space if space > 8 else int(mid)
    left, right = chunk[:best].strip(), chunk[best:].strip()
    return _split_long(left, lang) + _split_long(right, lang)


def cache_dir():
    d = os.path.expanduser('~/.manual-maker/runtime/tts-cache')
    os.makedirs(d, exist_ok=True)
    return d


def cached_phrase(edge, voice, rate, text):
    """Synthesize one phrase, or reuse the identical one from a previous pass.

    The two-pass flow (measure, then record, then speak) would otherwise pay for every line twice,
    and — worse — could get two subtly different takes of the same sentence."""
    import hashlib
    key = hashlib.sha1(f'{voice}|{rate}|{text}'.encode()).hexdigest()[:20]
    path = os.path.join(cache_dir(), key + '.mp3')
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        return True, path, None
    ok, why = speak(edge, voice, rate, text, path)
    if not ok:
        return False, None, why
    return True, path, None


def line_audio(edge, voice, rate, phrases, workdir, tag):
    """Build one narration line: phrases spoken, joined by their pauses. Returns (path, seconds)."""
    parts = []
    for k, (phrase, gap) in enumerate(phrases):
        ok, mp3, why = cached_phrase(edge, voice, rate, phrase)
        if not ok:
            return None, 0.0, why
        parts.append(mp3)
        if gap > 0:
            sil = os.path.join(workdir, f'{tag}_{k}_gap.mp3')
            if silence(gap, sil):
                parts.append(sil)
    joined = os.path.join(workdir, f'{tag}.mp3')
    if not concat(parts, joined, workdir):
        return None, 0.0, 'could not join phrases'
    return joined, (duration(joined) or 0.0), None


def prepare(play_path, lang_override, voice_override, rate, gender_override=None):
    """Pass one: measure how long each narrated step will take to say.

    record.js reads the result and holds each step open until its line has finished, so the
    narration never talks over the action that follows it. Guessing a duration from character
    count drifts; this speaks the real line with the real voice and measures it."""
    with open(play_path) as fh:
        play = json.load(fh)
    narr = play.get('narration') or {}
    lang = lang_override or narr.get('lang') or 'th'
    gender = gender_override or narr.get('gender') or DEFAULT_GENDER
    voice = voice_override or narr.get('voice') or pick_voice(lang, gender)
    if not voice:
        print(f'error: no voice for language "{lang}" / gender "{gender}" — pass --voice',
              file=sys.stderr)
        return 2
    edge = find_edge_tts()
    if not edge:
        print('error: edge-tts not found — run preflight.sh --install', file=sys.stderr)
        return 2

    steps = play.get('steps') or []
    out = {'lang': lang, 'gender': gender, 'voice': voice, 'rate': rate, 'steps': {}}
    work = tempfile.mkdtemp(prefix='sr-prepare-')
    try:
        for i, s in enumerate(steps):
            if not s.get('say'):
                continue
            phrases = split_phrases(s['say'], lang)
            if not phrases:
                continue
            _f, dur, why = line_audio(edge, voice, rate, phrases, work, f'p{i}')
            if why:
                print(f'FAIL  step {i + 1}: {why}', file=sys.stderr)
                return 1
            out['steps'][str(i + 1)] = round(dur, 2)
            print(f'  step {i + 1:>2}  {dur:5.1f}s  {s["say"][:58]}')
    finally:
        shutil.rmtree(work, ignore_errors=True)

    dest = os.path.splitext(play_path)[0] + '.saydur.json'
    with open(dest, 'w') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print()
    print(f'RESULT: measured {len(out["steps"])} lines  →  {dest}')
    print('        record.js picks this up automatically and paces each step to fit its line.')
    return 0


SYNTH_TIMEOUT = 60          # one short phrase; a healthy call returns in 1-4 s
SYNTH_TRIES = 3


def speak(edge, voice, rate, text, out_mp3):
    """Speak one phrase, retrying a stalled or failed request rather than hanging on it."""
    last = 'edge-tts produced nothing'
    for attempt in range(1, SYNTH_TRIES + 1):
        r = run([edge, '--voice', voice, '--rate', rate, '--text', text, '--write-media', out_mp3],
                timeout=SYNTH_TIMEOUT)
        if r.returncode == 0 and os.path.isfile(out_mp3) and os.path.getsize(out_mp3) > 0:
            return True, None
        last = (r.stderr or r.stdout or last).strip()[:200]
        if os.path.isfile(out_mp3) and os.path.getsize(out_mp3) == 0:
            os.remove(out_mp3)          # never leave a zero-byte file for the cache to trust
        if attempt < SYNTH_TRIES:
            print(f'    retry {attempt}/{SYNTH_TRIES - 1} — {last}')
            time.sleep(2 * attempt)
    return False, last


def silence(seconds, out_mp3):
    # 24 kHz mono matches edge-tts output, so the pieces concatenate without re-encoding.
    run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
         '-t', f'{seconds:.3f}', '-c:a', 'libmp3lame', '-b:a', '48k', out_mp3])
    return os.path.isfile(out_mp3)


def concat(parts, out_mp3, workdir):
    lst = os.path.join(workdir, 'concat.txt')
    with open(lst, 'w') as fh:
        for p in parts:
            fh.write(f"file '{p}'\n")
    r = run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
             '-c', 'copy', out_mp3])
    return r.returncode == 0 and os.path.isfile(out_mp3)


def duration(path):
    r = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', path])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def main():
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return 2

    video, lang, voice, rate, dry = None, None, None, DEFAULT_RATE, False
    gender, prep = None, None
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--prepare':
            i += 1; prep = args[i]
        elif a == '--lang':
            i += 1; lang = args[i]
        elif a == '--gender':
            i += 1; gender = args[i]
        elif a == '--voice':
            i += 1; voice = args[i]
        elif a == '--rate':
            i += 1; rate = args[i]
        elif a == '--dry-run':
            dry = True
        else:
            video = a
        i += 1

    if prep:
        if not os.path.isfile(prep):
            print(f'error: play file not found: {prep}', file=sys.stderr)
            return 2
        return prepare(prep, lang, voice, rate, gender)

    if not video or not os.path.isfile(video):
        print(f'error: video not found: {video}', file=sys.stderr)
        return 2

    timeline_path = os.path.splitext(video)[0] + '.narration.json'
    if not os.path.isfile(timeline_path):
        print(f'error: no timeline beside the video ({os.path.basename(timeline_path)}). '
              'Narration offsets are measured during recording — give the steps a `say` field and '
              're-record; they cannot be reconstructed afterwards.', file=sys.stderr)
        return 2

    with open(timeline_path) as fh:
        tl = json.load(fh)
    lines = tl.get('lines') or []
    if not lines:
        print('error: timeline has no lines', file=sys.stderr)
        return 2

    lang = lang or tl.get('lang') or 'th'
    gender = gender or tl.get('gender') or DEFAULT_GENDER
    voice = voice or tl.get('voice') or pick_voice(lang, gender)
    if not voice:
        print(f'error: no voice for language "{lang}" / gender "{gender}" — pass --voice',
              file=sys.stderr)
        return 2

    for binary in ('ffmpeg', 'ffprobe'):
        if not shutil.which(binary):
            print(f'error: {binary} not found — run preflight.sh --install', file=sys.stderr)
            return 2
    edge = find_edge_tts()
    if not edge:
        print('error: edge-tts not found — run preflight.sh --install. macOS `say` is not a '
              'substitute: its only Thai voice is female and audibly synthetic, which fails the '
              'brief for a natural male narrator.', file=sys.stderr)
        return 2

    vdur = duration(video)
    print(f'voice   {voice}   rate {rate}   lang {lang}   gender {gender}')
    print(f'video   {os.path.basename(video)}  {vdur:.1f}s' if vdur else 'video   (duration unknown)')
    print()

    plan = []
    for ln in lines:
        phrases = split_phrases(ln.get('text', ''), lang)
        if not phrases:
            continue
        plan.append({'atMs': int(ln.get('atMs', 0)), 'step': ln.get('step'), 'phrases': phrases})
        at = int(ln.get('atMs', 0)) / 1000.0
        print(f'  {at:6.1f}s  step {ln.get("step")}')
        for ph, gap in phrases:
            print(f'            · {ph}' + (f'   ⟨{gap:.2f}s⟩' if gap else ''))
    print()

    if dry:
        print('RESULT: dry run — nothing written')
        return 0

    work = tempfile.mkdtemp(prefix='sr-narrate-')
    try:
        line_files = []
        for n, item in enumerate(plan):
            joined, dur, why = line_audio(edge, voice, rate, item['phrases'], work, f'line{n}')
            if why:
                print(f'FAIL  step {item["step"]}: {why}', file=sys.stderr)
                return 1
            line_files.append((item, joined, dur))

        # Overlap is a scripting problem, not a fault here — say so and carry on, because the
        # honest fix is a shorter line or a longer step, both of which are the author's call.
        for idx in range(len(line_files) - 1):
            item, _, dur = line_files[idx]
            nxt = line_files[idx + 1][0]
            end = item['atMs'] / 1000.0 + dur
            if end > nxt['atMs'] / 1000.0 + 0.05:
                print(f'  ! step {item["step"]} narration runs {end - nxt["atMs"] / 1000.0:.1f}s '
                      f'into step {nxt["step"]} — shorten the line or lengthen the step')
        if vdur:
            item, _, dur = line_files[-1]
            end = item['atMs'] / 1000.0 + dur
            if end > vdur + 0.05:
                print(f'  ! the last line ends {end - vdur:.1f}s after the video does — '
                      'it will be cut off')

        # One filter graph: delay each line to its measured offset, mix, then normalize the whole
        # track to broadcast loudness so no line is louder than another.
        cmd = ['ffmpeg', '-y', '-v', 'error', '-i', video]
        for _, f, _d in line_files:
            cmd += ['-i', f]
        chains, labels = [], []
        for n, (item, _f, _d) in enumerate(line_files):
            lab = f'a{n}'
            chains.append(f'[{n + 1}:a]adelay={item["atMs"]}|{item["atMs"]}[{lab}]')
            labels.append(f'[{lab}]')
        if len(labels) > 1:
            chains.append(''.join(labels) + f'amix=inputs={len(labels)}:normalize=0[mix]')
            src = '[mix]'
        else:
            src = labels[0]
        chains.append(f'{src}loudnorm=I=-16:TP=-1.5:LRA=11[a]')
        out = os.path.splitext(video)[0] + '.narrated.mp4'
        cmd += ['-filter_complex', ';'.join(chains),
                '-map', '0:v', '-map', '[a]',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
                # No -shortest. The narration track is usually a little shorter than the picture,
                # and -shortest would answer that by CUTTING THE VIDEO — measured: a 19.1s clip came
                # back 17.3s, losing its closing frames. The video is the deliverable; it is never
                # trimmed to fit the audio.
                '-movflags', '+faststart', out]
        r = run(cmd)
        if r.returncode != 0 or not os.path.isfile(out):
            print('FAIL  mux: ' + (r.stderr.strip().splitlines() or ['ffmpeg failed'])[-1][:200],
                  file=sys.stderr)
            return 1

        # Prove the track is really there before claiming it is.
        probe = run(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                     '-show_entries', 'stream=codec_name,duration', '-of', 'csv=p=0', out])
        if not probe.stdout.strip():
            print('FAIL  the muxed file has no audio stream', file=sys.stderr)
            return 1

        os.replace(out, video)     # the deliverable keeps its name; the .webm remains the mute source
        print()
        print(f'RESULT: narrated  {len(line_files)} lines  →  {video}')
        print(f'        audio: {probe.stdout.strip()}')
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
