# Voice profiles — the approved sound, in numbers

A voice cannot be judged from its name, and it cannot be *defended* from its name either. A clip
can carry the right voice id, the right language and the right gender in every log line and still
not sound like the thing the user approved — because a tone preset quietly damped it. That is not
hypothetical: a female clip shipped 23 Hz below the approved timbre while every setting in the run
read as correct.

So an approved voice is recorded here as **measurements**, and
[`check-narration.py`](../scripts/check-narration.py) enforces them. The script is the executable
copy of this file; if you change one, change the other.

## Approved profiles (OLS login walkthrough, Thai — approved by the user 2026-08-18)

| | male | female |
|---|---|---|
| voice | `ko-KR-HyunsuMultilingualNeural` | `fr-FR-VivienneMultilingualNeural` |
| tone | `mellow` | `mellow` |
| rate · pitch · volume | `-12%` · `-12Hz` · `-13%` | `+0%` · `+12Hz` · `+0%` |
| median speaking pitch | **115 Hz** (band 100–130) | **195 Hz** (band 177–213) |
| greeting particle | `ครับ` | `ค่ะ` |
| measured pause after the greeting | 1.49 s | 0.96 s |
| peak level | −1.4 dB | −1.5 dB |

Both are **multilingual** voices speaking Thai. They were chosen by ear from a comparison set; do
not substitute a `th-TH-*` voice because it looks more correct on paper — the user picked these two
timbres.

**The female row is the one with the history.** `mellow` carries `-12% / -12Hz / -13%`, and those
were being applied *on top of* the voice the user had approved at its natural settings, which is
where the 23 Hz went. The row now says `+0% / +12Hz / +0%`: natural rate and volume, and `+12Hz`
because that is what measurement said closed the remaining gap to the reference sample
(188.2 Hz measured on both, exactly). The male row keeps `mellow`'s damping because the male voice
was approved *with* it.

## How a number here was produced — and how to re-derive one

Median speaking pitch, over voiced frames only, by autocorrelation on 16 kHz mono (70–400 Hz
search band, frames under −40 dBFS RMS and frames with weak periodicity discarded):

```bash
"$SR/scripts/check-narration.py" --print-only clip.mp4
```

Two things to know before reading a number:

- **A whole clip reads a few Hz higher than a one-line sample** of the same voice — more sentence
  starts, more question-ish contours. The female sample matched the reference at 188.2 Hz while the
  finished 42-second clip measured 195.1 Hz. Both are the same voice; compare like with like.
- **The band is deliberately wider than the drift it catches.** ±15–18 Hz tolerates a different
  script in the same voice; the defect it exists for was 23–30 Hz.

## Approving a new voice

1. Render the run's **own opening lines** in the candidate voice (`narrate.py --sample`) — never a
   stock sentence. Register is most of what makes narration sound human, so a generic sample
   approves the wrong thing.
2. Hand the audio to the user and **wait for an explicit yes**. A voice is approved by ear, never
   by settings.
3. Once approved, measure it (`--print-only`), add a row here and a matching entry in
   `PROFILES` in `check-narration.py`, and state the numbers back to the user.

Then every later run is defended by measurement rather than by anyone remembering what was chosen.

## The Thai particle rule this profile depends on

`ค่ะ` / `ครับ` and their relatives end a phrase, so the voice lands a falling contour on them and a
real pause follows. Written into `narrate.py`'s splitter and explained, with the pitch measurements
behind it, in [`script-writing.md`](script-writing.md). Layer 6c checks the audible half: the first
pause of the clip must be at least 0.45 s and must arrive within the first 3 s — i.e. right after
the greeting. Without it the particle runs into the next word and "สวัสดีค่ะ วันนี้…" is heard as
"สวัสดี · คะวันนี้".
