#!/usr/bin/env python3
"""narrate.py — speak a recorded clip's narration onto it, at the moments it belongs.

    narrate.py --sample <play.json> [--tone presenter] [--out s.mp3]   # hear the voice BEFORE recording
    narrate.py --prepare <play.json> [--tone presenter]   # pass 1 — measure each line, so recording can pace to it
    narrate.py <video.mp4> [--lang th|en] [--gender male|female] [--voice NAME] [--tone NAME] [--rate +4%] [--dry-run]

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

import hashlib
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


def resolve_voice(name):
    """'hyunsu' -> the full voice id; a full id passes through untouched."""
    return ALT_VOICES.get(str(name or '').strip().lower(), name)
DEFAULT_RATE = '-4%'          # slightly under default: unhurried reads as human, hurried reads as machine
DEFAULT_PITCH = '-6Hz'
DEFAULT_VOLUME = '-10%'

# Tone presets — asked at intake, never assumed. Each is a (rate, pitch) pair; nothing else about
# the voice changes, so a tone swap cannot alter which person is speaking.
# (rate, pitch, volume). Thai has exactly two neural voices, so tone cannot mean "another actor" —
# it is prosody. Raising pitch and rate is what makes a synthetic voice sound like it is SHOUTING;
# the calmer presets lower all three, which is what reads as a person talking rather than announcing.
TONES = {
    'calm':         ('-4%', '-6Hz', '-10%'),  # สงบ นุ่ม — default: closest to someone explaining
    'warm':         ('-1%', '-3Hz',  '-8%'),  # เป็นกันเอง อบอุ่น
    'professional': ('+2%', '+0Hz',  '-5%'),  # ทางการ สุภาพ
    'soft':         ('-7%', '-9Hz', '-15%'),  # เบา ช้า ชัด — training, complex steps
    'energetic':    ('+8%', '+6Hz',  '+0%'),  # กระตือรือร้น — promo only; the loudest preset
    'conversational': ('-1%', '-4Hz', '-8%'), # คุยกับคนดู — a host talking you through it, not reading
    'lively':       ('+6%', '+2Hz',  '-4%'),  # กระฉับกระเฉง — the pace people actually talk at
    'presenter':    ('+4%', '+0Hz',  '-5%'),  # สุภาพ เป็นทางการ แต่ไม่แข็ง — ส่งลูกค้านอกองค์กร (ค่าเริ่มต้นงานส่งมอบ)
    'upbeat':       ('+11%', '+5Hz', '-2%'),  # เร็ว สดใส — short clips, product highlights
    'narrator':     ('-8%', '-12Hz', '-12%'),  # เล่าเรื่อง ทุ้ม ช้า — walkthroughs someone watches end to end
    'documentary':  ('-12%', '-16Hz', '-14%'), # ทุ้มลึก ช้าที่สุด — long-form, weighty subject
    # จังหวะพอดแคสต์ — a host explaining something to one person, not announcing it to a room.
    # Unhurried and level rather than bright: the character comes from the PAUSES (see TONE_GAPS /
    # TONE_SPLICE / TONE_BREATH below), which are the longest of any preset. Reaching for a
    # conversational feel by raising rate or pitch produces the opposite — that is the setting that
    # reads as shouting. This is the preset for a demo someone watches all the way through.
    'podcast':      ('-3%', '-3Hz',  '-8%'),   # คุยกับคนฟัง ไม่รีบ เว้นจังหวะให้คิดตาม
    # ทุ้ม ละมุน — the warmest preset, and the only one that also gets post-processing (see WARMTH).
    # Chosen by ear over four candidates for a customer-facing walkthrough; pairs with a
    # multilingual voice rather than th-TH-Niwat, which was the one judged "still sounds AI".
    'mellow':       ('-12%', '-12Hz', '-13%'),  # ทุ้ม อุ่น ไม่รีบ — ส่งลูกค้า งานที่ต้องฟังยาว
}

# Voices outside the th-TH pair. The multilingual models speak Thai and are a generation newer;
# side by side on the same sentence, Hyunsu was picked by ear where th-TH-NiwatNeural was rejected
# as sounding synthetic. Set one explicitly with `narration.voice` in the play file — the gender
# table above stays the default so existing runs keep the voice they were approved with.
ALT_VOICES = {
    'hyunsu': 'ko-KR-HyunsuMultilingualNeural',    # male, warm and low — the current pick for Thai
    'andrew': 'en-US-AndrewMultilingualNeural',    # male, conversational
    'brian': 'en-US-BrianMultilingualNeural',      # male, deep
    'ava': 'en-US-AvaMultilingualNeural',          # female, bright
    'emma': 'en-US-EmmaMultilingualNeural',        # female, soft
    'vivienne': 'fr-FR-VivienneMultilingualNeural',  # female
    'thalita': 'pt-BR-ThalitaMultilingualNeural',    # female
}

# A tone may also stretch the pauses: an unhurried delivery needs more room between phrases than a
# brisk one, or it reads as slow speech rather than considered speech.
TONE_GAPS = {
    'mellow':         (0.24, 0.92),
    'podcast':        (0.16, 0.34),
    'presenter':      (0.10, 0.22),
    'lively':         (0.08, 0.18),
    'upbeat':         (0.06, 0.15),
    'conversational': (0.11, 0.24),
    'narrator':    (0.17, 0.34),
    'documentary': (0.20, 0.40),
    'soft':        (0.15, 0.30),
}
DEFAULT_TONE = 'calm'

# Pause lengths, in seconds. Short on purpose: measured against the same line spoken as ONE
# utterance, phrases spliced with 0.22 s / 0.40 s gaps ran 11.88 s against 8.42 s — because each
# synthesized phrase arrives with its own head and tail silence, which stacks on top of the gap we
# add. Trimming that silence (see `trim`) and keeping the gaps in the 90-260 ms band is what makes
# the result read as a person speaking instead of a machine reading a list.
BASE_GAP_CLAUSE = 0.13
BASE_GAP_SENTENCE = 0.26
GAP_CLAUSE = BASE_GAP_CLAUSE
GAP_SENTENCE = BASE_GAP_SENTENCE

# The breath a speaker takes AFTER finishing a line, before the next one starts.
#
# This is the pause that was missing. `trim` leaves 120 ms of tail on an utterance — enough that a
# sentence does not end mid-release, nowhere near enough to read as a person finishing a thought.
# Every line therefore ended 0.12 s after its last syllable and the next line began at its own
# measured offset, which the recorder had already advanced to: sentence, sentence, sentence, with
# no room between them. A presenter leaves half a second there; a narrator leaves more.
#
# It has to live in the AUDIO, not in the recorder, because the measured duration is what paces the
# recording: a breath added here lengthens the step that holds for it, so the picture waits too.
BASE_BREATH = 0.45
TONE_BREATH = {
    'mellow': 1.10, 'podcast': 0.70, 'documentary': 0.75, 'narrator': 0.68, 'soft': 0.60, 'presenter': 0.55,
    'calm': 0.50, 'professional': 0.50, 'warm': 0.48, 'conversational': 0.44,
    'lively': 0.34, 'upbeat': 0.30, 'energetic': 0.28,
}

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

# Thai sentence-final politeness particles — the mirror image of TH_BREAKS. Those words START a
# clause; these END one, and a phrase may never begin with one.
#
# It matters more here than anywhere else in this file, because a particle carries its meaning in
# its TONE: ค่ะ falls, คะ is high. The engine gives every synthesis chunk the same shape — it opens
# at the top of the range and falls at the end (measured in the note above ONE_SHOT_TH) — so where
# the particle sits inside a chunk decides WHICH WORD is heard.
#
# Measured on fr-FR-VivienneMultilingualNeural, rate -12% / pitch -12Hz, reading
# "สวัสดีค่ะ วันนี้จะพาชม…" the way this file used to hand it over — one utterance, no split point,
# because Thai narration carries no full stop for `sentences` to find:
#
#     …สวัสดี ends 0.62 s at 184 Hz · 60 ms of silence · ค่ะ at 0.72-0.90 s peaking at 247 Hz
#     the same line with the particle deleted has no such peak — it runs on at 183-196 Hz
#
# i.e. the break landed BEFORE the particle and the particle was spoken at the top of the range:
# "สวัสดี · คะ วันนี้", which is exactly what the listener reported. The same particle closing its
# own chunk falls 164 → 137 Hz — ค่ะ, with the pause after it where it belongs.
#
# Three rules follow, all keyed off this one list:
#   1. a particle with more line behind it ENDS a sentence, so it closes a chunk and takes the fall;
#   2. a space written in front of a particle is closed up before synthesis;
#   3. no phrase may START with a particle — whatever produced the cut, it is folded back.
# Longest first, so 'นะคะ' matches before 'คะ'.
TH_PARTICLES = ('นะครับ', 'ครับผม', 'นะคะ', 'ครับ', 'ค่ะ', 'ค่า', 'คะ', 'จ๊ะ', 'จ้ะ', 'จ้า', 'ฮะ')

# The subset that can never begin a Thai word, so it is safe to recognise mid-run — with no space
# after it to prove it is a particle. The others are excluded on purpose: 'คะ' opens คะแนน, 'ค่า'
# opens ค่าใช้จ่าย, 'จ้า' opens จ้าง. Treating those as particles wherever they appear would tear a
# real word in half, which is the same class of mistake as breaking on 'แล้ว' (see TH_BREAKS).
TH_PARTICLES_GLUED = ('นะครับ', 'ครับผม', 'นะคะ', 'ครับ', 'ค่ะ')

_P_ANY = '|'.join(TH_PARTICLES)
_P_SAFE = '|'.join(TH_PARTICLES_GLUED)
# a particle standing as its own token: a space, or the end of the line, behind it
PARTICLE_TOKEN = re.compile(rf'(?:{_P_ANY})(?=\s|$)')
# whitespace that has detached a particle from the phrase it closes — "ขอบคุณ ค่ะ"
PARTICLE_ORPHAN = re.compile(rf'\s+(?=(?:{_P_ANY})(?:\s|$))')
# a phrase that OPENS with a particle, either as a token or glued to the next word
PARTICLE_LEADS = re.compile(rf'^(?:(?:{_P_ANY})(?=\s|$)|(?:{_P_SAFE}))')

# The shortest head worth speaking as its own chunk. A greeting ("สวัสดีค่ะ" — 9) clears it; a bare
# particle left over from an earlier cut does not, and must not become a chunk of its own.
MIN_CHUNK_TH = 6


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


# --- Latin acronyms in Thai narration ----------------------------------------------------------
#
# A Thai voice reading "OLS" does not spell it — it tries to say it as a Thai word, and what comes
# out is "โอ๊ต". Every acronym in a Thai script has this problem: NDLP, PDF, QR, OTP. The engine is
# not wrong to guess; there is nothing in the text telling it these are letters.
#
# So the letters are spelled out FOR the engine, at synthesis time only. The script, the subtitles
# and everything the user reads keep "OLS" — this is a pronunciation fix, not a rewrite, exactly as
# a mispronounced ค่ะ is fixed in what is fed to the voice and never in the written line.
THAI_LETTER = {
    'A': 'เอ', 'B': 'บี', 'C': 'ซี', 'D': 'ดี', 'E': 'อี', 'F': 'เอฟ', 'G': 'จี', 'H': 'เอช',
    'I': 'ไอ', 'J': 'เจ', 'K': 'เค', 'L': 'แอล', 'M': 'เอ็ม', 'N': 'เอ็น', 'O': 'โอ', 'P': 'พี',
    'Q': 'คิว', 'R': 'อาร์', 'S': 'เอส', 'T': 'ที', 'U': 'ยู', 'V': 'วี', 'W': 'ดับเบิลยู',
    'X': 'เอ็กซ์', 'Y': 'วาย', 'Z': 'แซด',
}

# Words that are written in capitals but SAID as words, not spelled. Without this list the fix
# would turn "EXCEL" into "อี เอ็กซ์ ซี อี แอล", which is worse than what it set out to repair.
SAY_AS_WORD = {'EXCEL', 'WORD', 'LINE', 'ZOOM', 'TEAMS', 'GOOGLE', 'MICROSOFT', 'OK', 'FILE',
               'EMAIL', 'LOGIN', 'MENU', 'ADMIN', 'USER'}

ACRONYM = re.compile(r'(?<![A-Za-z])([A-Z]{2,6})(?![A-Za-z])')


def spell_acronyms(text, lang):
    """Spell Latin acronyms out in Thai letters, for the voice only."""
    if lang != 'th':
        return text
    def one(m):
        word = m.group(1)
        if word in SAY_AS_WORD:
            return word
        return ' '.join(THAI_LETTER.get(ch, ch) for ch in word)
    return ACRONYM.sub(one, text)


def glue_particles(text, lang):
    """Close up a space written in FRONT of a closing particle — for the voice only.

    "ขอบคุณ ค่ะ" is written all the time and reads fine on the page, but a Thai space is a phrase
    break: the voice stops, opens a new phrase on the particle, and opens it at the top of its
    range — which is the other word. Removing the space is never visible to anyone; like
    spell_acronyms this touches only what is handed to the engine, never the script or the subtitles."""
    if lang != 'th':
        return text
    return PARTICLE_ORPHAN.sub('', text)


def _th_sentences(text):
    """Cut AFTER a closing particle that still has line behind it. That is a sentence end.

    Thai narration rarely carries a full stop, so `sentences` below finds nothing and the whole
    line goes to the engine in one piece — which is how the particle ends up mid-utterance, spoken
    high, with the pause landing in front of it instead of after it. Cutting here is what gives the
    particle the terminal fall AND puts the breath where a person leaves it."""
    out, start = [], 0
    for m in PARTICLE_TOKEN.finditer(text):
        head, tail = text[start:m.end()].strip(), text[m.end():].strip()
        if tail and len(head) >= MIN_CHUNK_TH:
            out.append(head)
            start = m.end()
    rest = text[start:].strip()
    if rest:
        out.append(rest)
    return out or [text]


def _keep_particles_attached(pieces):
    """Last line of defence: no phrase may START with a particle.

    _split_long takes its cut from a connective, from a space, or — when the clause offers neither —
    from a bare character index, and none of the three knows what a particle is. Wherever the cut
    came from, a piece that opens with one is folded back onto the piece it closes."""
    fixed = []
    for piece in pieces:
        m = PARTICLE_LEADS.match(piece)
        if m and fixed:
            fixed[-1] = (fixed[-1] + piece[:m.end()]).strip()
            rest = piece[m.end():].strip()
            if rest:
                fixed.append(rest)
        else:
            fixed.append(piece)
    return [p for p in fixed if p]


def split_phrases(text, lang):
    """Break one narration line into breath-sized phrases.

    Returns [(phrase, gap_after_seconds)]. The gap after the last phrase is 0 — spacing between
    lines comes from their measured offsets, not from padding."""
    text = re.sub(r'\s+', ' ', str(text)).strip()
    if not text:
        return []
    text = spell_acronyms(text, lang)
    text = glue_particles(text, lang)

    # Sentence level first: real punctuation is the strongest signal a writer gives us.
    sentences = [s for s in re.split(r'(?<=[.!?。])\s+|\n+', text) if s.strip()]
    # Thai writes almost none of that punctuation, but it does mark the end of a sentence — with a
    # closing particle. Read it as the full stop it is, or the line has no split point at all.
    if lang == 'th':
        sentences = [part for s in sentences for part in _th_sentences(s.strip())]

    out = []
    for si, sentence in enumerate(sentences):
        sentence = sentence.strip()
        # Then clause level, on punctuation the author actually wrote.
        clauses = [c for c in re.split(r'(?<=[,;:·])\s*', sentence) if c.strip()]
        pieces = []
        for clause in clauses:
            pieces.extend(_split_long(clause.strip(), lang))
        if lang == 'th':
            pieces = _keep_particles_attached(pieces)
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


def cached_phrase(edge, voice, rate, text, pitch=DEFAULT_PITCH, volume=DEFAULT_VOLUME):
    """Synthesize one phrase, or reuse the identical one from a previous pass.

    The two-pass flow (measure, then record, then speak) would otherwise pay for every line twice,
    and — worse — could get two subtly different takes of the same sentence."""
    import hashlib
    key = hashlib.sha1(f'{voice}|{rate}|{pitch}|{volume}|{text}'.encode()).hexdigest()[:20]
    path = os.path.join(cache_dir(), key + '.mp3')
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        return True, path, None
    ok, why = speak(edge, voice, rate, text, path, pitch, volume)
    if not ok:
        return False, None, why
    return True, path, None


# A line under this many characters is spoken in ONE breath — one synthesis call, no splicing.
# This is the difference between speech and a read-aloud list. Every separate call gets its own
# sentence intonation: it starts high and FALLS at the end. Measured on one Thai line whose median
# pitch was 205 Hz, each spliced phrase ended at 145-151 Hz — a full terminal fall, three times,
# inside what should be one continuous sentence. No amount of gap tuning fixes that; the fall is
# baked into each fragment. Handing the whole line to the engine lets it carry the intonation
# across the phrases, and the pauses come from the punctuation and spacing already in the text.
# A pause between two spoken sentences, as opposed to between phrases inside one. A presenter
# holds this longer than the default: the pause is what tells a listener one point has landed
# before the next one starts.
BASE_SPLICE = 0.38
TONE_SPLICE = {
    'mellow': 0.92, 'podcast': 0.64, 'documentary': 0.70, 'narrator': 0.62, 'soft': 0.56, 'presenter': 0.52,
    'calm': 0.44, 'professional': 0.44, 'warm': 0.42, 'conversational': 0.40,
    'lively': 0.34, 'upbeat': 0.32, 'energetic': 0.30,
}
SENTENCE_SPLICE = BASE_SPLICE
LINE_BREATH = BASE_BREATH

ONE_SHOT_TH = 220
ONE_SHOT_EN = 340

# --- Human unevenness -------------------------------------------------------------------------
#
# A person does not speak level. One sentence is leaned into, the next eased off; a pause runs long
# where the thought needed room and short where it did not. Held perfectly flat — one pitch, one
# speed, one pause length repeated — the delivery reads as a machine no matter how good the voice
# is, which is what "โมโนโทนไปเรื่อยๆ" describes.
#
# edge-tts 7.2.8 takes rate, pitch and volume per synthesis call and supports no SSML, so the
# variation has to be applied per utterance rather than inside one. Every sentence therefore gets
# its own small offsets, and every pause its own length.
#
# The offsets are DERIVED FROM THE TEXT, never random. The measuring pass and the muxing pass
# synthesize the same lines independently; anything random would give them different durations, the
# recording would be paced to one and the narration muxed at the other, and every line would drift
# from the step it describes. Same words in, same voice out — always.
VARIATION = {                       # (pitch Hz, rate %, volume %, pause fraction)
    'mellow': (5.0, 4.0, 4.0, 0.40),
    'podcast': (3.0, 3.0, 3.0, 0.30),
    'narrator': (3.0, 2.5, 3.0, 0.28),
    'documentary': (2.5, 2.0, 2.5, 0.25),
    'conversational': (3.0, 3.0, 3.0, 0.28),
    'warm': (2.5, 2.5, 2.5, 0.25),
    'presenter': (2.0, 2.0, 2.0, 0.20),
    'calm': (2.0, 2.0, 2.0, 0.22),
    'soft': (2.0, 1.5, 2.0, 0.22),
    'professional': (1.5, 1.5, 1.5, 0.18),
    'lively': (2.5, 2.5, 2.5, 0.18),
    'upbeat': (2.0, 2.0, 2.0, 0.15),
    'energetic': (2.0, 2.0, 2.0, 0.15),
}
BASE_VARIATION = (2.0, 2.0, 2.0, 0.20)
SPREAD = BASE_VARIATION


def wobble(text, salt, spread):
    """A repeatable offset in [-spread, +spread], decided by the words themselves."""
    if spread <= 0:
        return 0.0
    h = int(hashlib.sha1(f'{salt}|{text}'.encode()).hexdigest()[:8], 16)
    return ((h % 2001) / 1000.0 - 1.0) * spread


def _num(setting):
    """'-12Hz' -> -12, '+4%' -> 4. Only the number matters; the unit is fixed per field."""
    m = re.search(r'-?\d+(?:\.\d+)?', str(setting or '0'))
    return float(m.group()) if m else 0.0


def voice_of(text, rate, pitch, volume):
    """The prosody for ONE utterance: the tone's settings, nudged off level by this text."""
    p_sp, r_sp, v_sp, _ = SPREAD
    return (f'{_num(rate) + wobble(text, "rate", r_sp):+.0f}%',
            f'{_num(pitch) + wobble(text, "pitch", p_sp):+.0f}Hz',
            f'{_num(volume) + wobble(text, "vol", v_sp):+.0f}%')


def uneven(seconds, text, salt):
    """A pause of about `seconds`, never exactly `seconds` twice in a row."""
    _p, _r, _v, frac = SPREAD
    return max(0.05, seconds * (1.0 + wobble(text, salt, frac)))


# Post-processing, applied to the finished track. A synthesized voice is dry, level and pushed hard
# in the 3-7 kHz band where "clarity" lives — which is a large part of what a listener identifies as
# AI. This chain lands closer to a person recorded through a microphone: chest weight back in,
# that clarity band eased off, dynamics gently evened, and a room short enough to hear but not
# notice. It runs before loudnorm so the normalizer works on the finished tone.
WARMTH = ('highpass=f=65,'
          'equalizer=f=220:t=q:w=1.2:g=2.5,'      # อก — body
          'equalizer=f=3200:t=q:w=1.8:g=-3.5,'    # the band that reads as synthetic
          'equalizer=f=6500:t=q:w=2:g=-2,'        # sibilance
          'acompressor=threshold=-20dB:ratio=2.5:attack=20:release=260,'
          'aecho=0.9:0.9:22:0.06,')               # a small room, not an effect
WARM_TONES = {'mellow'}
WARM = False


def apply_tone(tone):
    """Resolve a tone into prosody, and install the pause lengths that belong with it.

    Returns (rate, pitch, volume), or None if the tone is unknown.

    Every entry point calls this — the sample, the measuring pass and the mux. That is the whole
    point of it existing: `tone` used to be read only where the sample was built, so the voice a
    user approved and the voice that reached the clip were resolved by different code. The
    measuring pass never saw the tone at all and referred to `pitch`/`volume` that were never
    assigned, which is a NameError, not a wrong sound — `--prepare` could not run.
    """
    if tone not in TONES:
        return None
    global GAP_CLAUSE, GAP_SENTENCE, SENTENCE_SPLICE, LINE_BREATH, SPREAD, WARM
    rate, pitch, volume = TONES[tone]
    GAP_CLAUSE, GAP_SENTENCE = TONE_GAPS.get(tone, (BASE_GAP_CLAUSE, BASE_GAP_SENTENCE))
    SENTENCE_SPLICE = TONE_SPLICE.get(tone, BASE_SPLICE)
    LINE_BREATH = TONE_BREATH.get(tone, BASE_BREATH)
    SPREAD = VARIATION.get(tone, BASE_VARIATION)
    WARM = tone in WARM_TONES
    return rate, pitch, volume


def line_audio(edge, voice, rate, phrases, workdir, tag, pitch=DEFAULT_PITCH,
               volume=DEFAULT_VOLUME, lang='th'):
    """Build one narration line. Returns (path, seconds, error).

    Short line  → one utterance, no splice: the engine phrases it itself.
    Long line   → split only at SENTENCE boundaries, where a falling contour is what a listener
                  expects anyway, and join those with a real pause."""
    limit = ONE_SHOT_TH if lang == 'th' else ONE_SHOT_EN

    # Rebuild the spoken text from the phrases. A Thai space is itself a phrasing cue, so the
    # boundaries we found are preserved as text rather than enforced with scissors.
    joined = ' '.join(ph for ph, _gap in phrases).strip()

    # A sentence boundary inside the line is not a formatting detail: it is the one place the voice
    # MUST land a falling contour and leave a breath — and in Thai a closing particle creates one.
    # Handed over as a single utterance the engine phrases the line wherever it likes, which is
    # exactly how ค่ะ ended up spoken at the top of the range with the pause in front of it. So the
    # one-shot shortcut applies only when the line has no boundary to honour.
    ends_a_sentence = any(gap >= GAP_SENTENCE for _ph, gap in phrases[:-1])

    if len(joined) <= limit and not ends_a_sentence:
        u_rate, u_pitch, u_volume = voice_of(joined, rate, pitch, volume)
        ok, mp3, why = cached_phrase(edge, voice, u_rate, joined, u_pitch, u_volume)
        if not ok:
            return None, 0.0, why
        out = breathe(trim(mp3, os.path.join(workdir, f'{tag}_one.mp3')), workdir, tag, joined)
        return out, (duration(out) or 0.0), None

    # Too long for one breath. Group phrases into sentence-sized chunks — a chunk ends where the
    # phrase list said a sentence ended (its gap is the sentence gap), never mid-clause.
    chunks, cur = [], []
    for ph, gap in phrases:
        cur.append(ph)
        if gap >= GAP_SENTENCE or sum(len(x) for x in cur) > limit:
            chunks.append(' '.join(cur)); cur = []
    if cur:
        chunks.append(' '.join(cur))

    parts = []
    for k, chunk in enumerate(chunks):
        # Each sentence gets its own prosody. This is where an even delivery turns uneven: the
        # engine already gives every separate call its own contour, so leaning one sentence lower
        # and the next a shade faster costs nothing and is what a person actually does.
        u_rate, u_pitch, u_volume = voice_of(chunk, rate, pitch, volume)
        ok, mp3, why = cached_phrase(edge, voice, u_rate, chunk, u_pitch, u_volume)
        if not ok:
            return None, 0.0, why
        parts.append(trim(mp3, os.path.join(workdir, f'{tag}_{k}_t.mp3')))
        if k < len(chunks) - 1:
            # A chunk boundary IS a sentence boundary, so it takes a sentence-sized pause. The
            # per-tone gaps were tuned when this code spliced phrases; reusing the phrase gap here
            # (180 ms on the lively preset) ran one sentence into the next. Its length varies with
            # the sentence it follows — pauses of identical length are their own kind of robotic.
            sil = os.path.join(workdir, f'{tag}_{k}_gap.mp3')
            if silence(uneven(max(GAP_SENTENCE, SENTENCE_SPLICE), chunk, 'splice'), sil):
                parts.append(sil)
    joined_path = os.path.join(workdir, f'{tag}.mp3')
    if not concat(parts, joined_path, workdir):
        return None, 0.0, 'could not join sentences'
    out = breathe(joined_path, workdir, tag, joined)
    return out, (duration(out) or 0.0), None


def breathe(body, workdir, tag, text=''):
    """Give the line its closing breath, in the audio itself.

    Its length varies with the line it closes, for the same reason the sentence pauses do.

    Returns the lengthened file, or `body` untouched if the pause could not be built — a missing
    breath is a clip that sounds rushed, which is worth shipping over no clip at all."""
    if LINE_BREATH <= 0:
        return body
    sil = os.path.join(workdir, f'{tag}_breath.mp3')
    out = os.path.join(workdir, f'{tag}_b.mp3')
    if not silence(uneven(LINE_BREATH, text, 'breath'), sil) or not concat([body, sil], out, workdir):
        return body
    return out


def sample(play_path, lang_override, voice_override, rate, gender_override, tone_override, out_path):
    """Speak a short sample in the exact voice a run would use, for approval BEFORE recording.

    Recording is the expensive half: a 90-second clip takes 90 seconds to make and every retake
    costs that again. Judging the voice from a name (`th-TH-NiwatNeural`, tone `presenter`) is not
    judging it at all — the first four presets were each rejected by ear after being described as
    correct on paper. So the workflow plays a sample first and records only once someone has heard
    what they are getting."""
    with open(play_path) as fh:
        play = json.load(fh)
    narr = play.get('narration') or {}
    lang = lang_override or narr.get('lang') or 'th'
    gender = gender_override or narr.get('gender') or DEFAULT_GENDER
    tone = tone_override or narr.get('tone') or DEFAULT_TONE
    voice = voice_override or narr.get('voice') or pick_voice(lang, gender)
    if not voice:
        print(f'error: no voice for "{lang}" / "{gender}" — pass --voice', file=sys.stderr)
        return 2
    if tone not in TONES:
        print(f'error: unknown tone "{tone}". Choose one of: {", ".join(sorted(TONES))}',
              file=sys.stderr)
        return 2

    t_rate, t_pitch, t_volume = apply_tone(tone)
    # The play file wins over the tone preset, the same way the muxing pass already lets a stored
    # timeline override it. Without this, `"pitch"`/`"volume"` in a play file were silently ignored
    # here while `"rate"` was honoured — so a voice asked for at its own natural timbre still came
    # out damped, and the sample the user approved was not the sample the run would speak.
    rate = rate or narr.get('rate') or t_rate
    t_pitch = narr.get('pitch') or t_pitch
    t_volume = narr.get('volume') or t_volume
    edge = find_edge_tts()
    if not edge or not shutil.which('ffmpeg'):
        print('error: edge-tts or ffmpeg missing — run preflight.sh --install', file=sys.stderr)
        return 2

    # The sample is the run's OWN opening lines, not a stock sentence: register is what decides
    # whether narration sounds human, so a generic sample would approve the wrong thing.
    lines = [s['say'] for s in (play.get('steps') or []) if s.get('say')][:2]
    if not lines:
        print('error: no step carries a `say` line — nothing to sample', file=sys.stderr)
        return 2

    out_path = out_path or os.path.join(os.path.dirname(os.path.abspath(play_path)),
                                        f'sample-{lang}-{gender}-{tone}.mp3')
    work = tempfile.mkdtemp(prefix='sr-sample-')
    try:
        parts = []
        for i, line in enumerate(lines):
            f, _d, why = line_audio(edge, voice, rate, split_phrases(line, lang), work,
                                    f's{i}', t_pitch, t_volume, lang)
            if why:
                print(f'FAIL {why}', file=sys.stderr)
                return 1
            parts.append(f)
            if i < len(lines) - 1:
                sil = os.path.join(work, f's{i}_gap.mp3')
                if silence(SENTENCE_SPLICE, sil):
                    parts.append(sil)
        joined = os.path.join(work, 'sample.mp3')
        if not concat(parts, joined, work):
            print('FAIL could not join the sample', file=sys.stderr)
            return 1
        r = run(['ffmpeg', '-y', '-v', 'error', '-i', joined,
                 '-af', (WARMTH if WARM else '') + 'loudnorm=I=-17:TP=-2:LRA=12',
                 '-c:a', 'libmp3lame', '-b:a', '160k', out_path], timeout=120)
        if r.returncode != 0 or not os.path.isfile(out_path):
            print('FAIL could not write the sample', file=sys.stderr)
            return 1
        print(f'voice   {voice}   tone {tone}   rate {rate}  pitch {t_pitch}  volume {t_volume}')
        print(f'lines   {len(lines)} (the run\'s own opening narration)')
        print(f'sample  {out_path}  {duration(out_path) or 0:.1f}s')
        print()
        print('Play it for the user and get an explicit approval before recording anything.')
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


def prepare(play_path, lang_override, voice_override, rate, gender_override=None,
            tone_override=None):
    """Pass one. `rate` may be None here — the play file's `narration.rate` fills it in."""
    """Pass one: measure how long each narrated step will take to say.

    record.js reads the result and holds each step open until its line has finished, so the
    narration never talks over the action that follows it. Guessing a duration from character
    count drifts; this speaks the real line with the real voice and measures it."""
    with open(play_path) as fh:
        play = json.load(fh)
    narr = play.get('narration') or {}
    lang = lang_override or narr.get('lang') or 'th'
    gender = gender_override or narr.get('gender') or DEFAULT_GENDER
    # The tone decides prosody AND every pause length, so it has to be resolved here and not just
    # where the sample is built: measuring at one tone and speaking at another gives every line a
    # different length than the recording was paced to, and the narration walks into the next step.
    tone = tone_override or narr.get('tone') or DEFAULT_TONE
    prosody = apply_tone(tone)
    if not prosody:
        print(f'error: unknown tone "{tone}". Choose one of: {", ".join(sorted(TONES))}',
              file=sys.stderr)
        return 2
    t_rate, pitch, volume = prosody
    rate = rate or narr.get('rate') or t_rate
    pitch = narr.get('pitch') or pitch          # play file overrides the tone preset — see above
    volume = narr.get('volume') or volume
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
    # Carry the tone into the durations file too. record.js copies it onto the timeline, so the
    # muxing pass speaks at the tone the measuring pass measured — without it the two passes agree
    # on the words and disagree on the delivery.
    out = {'lang': lang, 'gender': gender, 'voice': voice, 'rate': rate, 'tone': tone,
           'pitch': pitch, 'volume': volume, 'breath': LINE_BREATH, 'steps': {}}
    print(f'voice   {voice}   tone {tone}   rate {rate}  pitch {pitch}  volume {volume}')
    print(f'pauses  clause {GAP_CLAUSE:.2f}s   sentence {SENTENCE_SPLICE:.2f}s   '
          f'breath after each line {LINE_BREATH:.2f}s')
    print()
    work = tempfile.mkdtemp(prefix='sr-prepare-')
    try:
        for i, s in enumerate(steps):
            if not s.get('say'):
                continue
            phrases = split_phrases(s['say'], lang)
            if not phrases:
                continue
            _f, dur, why = line_audio(edge, voice, rate, phrases, work, f'p{i}',
                                       pitch, volume, lang)
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


def speak(edge, voice, rate, text, out_mp3, pitch=DEFAULT_PITCH, volume=DEFAULT_VOLUME):
    """Speak one phrase, retrying a stalled or failed request rather than hanging on it."""
    last = 'edge-tts produced nothing'
    for attempt in range(1, SYNTH_TRIES + 1):
        r = run([edge, '--voice', voice, '--rate', rate, '--pitch', pitch, '--volume', volume,
                 '--text', text, '--write-media', out_mp3], timeout=SYNTH_TIMEOUT)
        if r.returncode == 0 and os.path.isfile(out_mp3) and os.path.getsize(out_mp3) > 0:
            return True, None
        last = (r.stderr or r.stdout or last).strip()[:200]
        if os.path.isfile(out_mp3) and os.path.getsize(out_mp3) == 0:
            os.remove(out_mp3)          # never leave a zero-byte file for the cache to trust
        if attempt < SYNTH_TRIES:
            print(f'    retry {attempt}/{SYNTH_TRIES - 1} — {last}')
            time.sleep(2 * attempt)
    return False, last


def trim(in_mp3, out_mp3):
    """Strip the dead air edge-tts wraps around every utterance — without clipping the voice.

    Two settings matter, and both were wrong at first:

    * **Threshold −55 dB, not −45 dB.** A sentence does not stop, it decays. Cutting at −45 dB
      lands mid-release of the final syllable, so the clip ends on a chopped-off word. Measured:
      1.00 s (male) and 1.07 s (female) removed from a 5.6 s / 5.2 s utterance, with the true
      tail sitting at −91 dB — i.e. there was real silence to remove, but the knife started while
      the voice was still sounding.
    * **Keep 120 ms of silence.** A speaker releases a sentence and breathes; splicing the next one
      onto a hard zero is what makes the join sound like the words collide.
    """
    f = ('silenceremove=start_periods=1:start_silence=0.05:start_threshold=-55dB:detection=peak,'
         'areverse,'
         'silenceremove=start_periods=1:start_silence=0.12:start_threshold=-55dB:detection=peak,'
         'areverse')
    r = run(['ffmpeg', '-y', '-v', 'error', '-i', in_mp3, '-af', f,
             '-ar', '24000', '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '48k', out_mp3], timeout=60)
    if r.returncode != 0 or not os.path.isfile(out_mp3) or os.path.getsize(out_mp3) == 0:
        return in_mp3          # trimming is an improvement, never a gate: fall back to the original
    return out_mp3


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

    video, lang, voice, rate, dry = None, None, None, None, False
    gender, prep, samp, tone, out_path = None, None, None, None, None
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--prepare':
            i += 1; prep = args[i]
        elif a == '--sample':
            i += 1; samp = args[i]
        elif a == '--tone':
            i += 1; tone = args[i]
        elif a == '--out':
            i += 1; out_path = args[i]
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

    if samp:
        if not os.path.isfile(samp):
            print(f'error: play file not found: {samp}', file=sys.stderr)
            return 2
        return sample(samp, lang, voice, rate, gender, tone, out_path)

    if prep:
        if not os.path.isfile(prep):
            print(f'error: play file not found: {prep}', file=sys.stderr)
            return 2
        return prepare(prep, lang, voice, rate, gender, tone)

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
    # Tone before rate: it decides the pitch, the volume and every pause length, and the timeline
    # carries the one the measuring pass actually used. Resolving it here is what keeps the clip
    # identical to the sample that was approved — the same reason `gender` is read back, one step
    # further along the same wire.
    tone = tone or tl.get('tone') or DEFAULT_TONE
    prosody = apply_tone(tone)
    if not prosody:
        print(f'error: unknown tone "{tone}". Choose one of: {", ".join(sorted(TONES))}',
              file=sys.stderr)
        return 2
    t_rate, pitch, volume = prosody
    pitch = tl.get('pitch') or pitch
    volume = tl.get('volume') or volume
    # Speed matters as much as the voice: the recording was paced to how long each line took at
    # the rate the measuring pass used. Reading it back from the timeline keeps the two passes in
    # step — a mux at a different rate makes every line the wrong length and the narration walks
    # into the next action, the same silent drift that dropping `gender` caused.
    rate = rate or tl.get('rate') or t_rate

    # Fail closed rather than pick a voice. A silent default is what shipped four demo clips with
    # the wrong narrator: the timeline carried no gender, the default was male, and every clip
    # requested as female was read by a man. Nothing about the file looked wrong.
    gender = gender or tl.get('gender')
    voice = voice or tl.get('voice')
    if not voice and not gender:
        print('error: the timeline says nothing about which voice to use (no `gender`, no `voice`), '
              'and guessing one is how a clip ends up narrated by the wrong person. '
              'Pass --gender male|female (or --voice NAME), or re-record with '
              '`narration: {lang, gender}` in the play file.', file=sys.stderr)
        return 2
    voice = voice or pick_voice(lang, gender)
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
    print(f'voice   {voice}   tone {tone}   rate {rate}   lang {lang}   gender {gender}')
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
            joined, dur, why = line_audio(edge, voice, rate, item['phrases'], work, f'line{n}',
                                          pitch, volume, lang)
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
        chains.append(f'{src}{WARMTH if WARM else ""}loudnorm=I=-16:TP=-1.5:LRA=11[a]')
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
        print(f'RESULT: narrated  {len(line_files)} lines  in {voice}  →  {video}')
        print(f'        audio: {probe.stdout.strip()}')
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
