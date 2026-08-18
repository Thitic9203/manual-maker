# Quality gate — 7 layers, fail-closed

Every recording must clear **all seven layers** before it counts as delivered. **Miss one and the
job is not finished** — do not hand the file over, do not embed it, do not mark the item done.

The reason this is absolute: a clip that *looks* like a recording but skips a step, cuts off before
its target, or is too blurry to read is **worse than no clip at all** — it is proof of nothing that
gets filed as proof of something. Re-record; never wave it through.

| # | Layer | Passes only when | Checked by |
|:--:|---|---|---|
| **1** | **Max quality** | Recorded at the full spec — viewport ≥ 1920×1080, `deviceScaleFactor` 2, H.264 CRF 20, `yuv420p`, no downscale that blurs text. On-screen labels are legible. | `verify-video.py` |
| **2** | **Whole flow, no skip** | Drives **every** step from the start, on the **real UI** (clicks, not an API shortcut) — no jump-cut, no starting mid-flow, no fast-forward past a step. | you, against the source |
| **3** | **Reaches the stated target** | Where a step says "scroll to XX / open YY / find ZZ", the clip **visibly arrives** and acts on it. **Never end before arriving.** Unreachable ⇒ the item is **blocked with the reason**, not a short clip passed off as done. | `waitFor` in the play file, fail-closed |
| **4** | **The result is on screen** | The exact state that decides each expected result is **visible in the video** — the resulting screen, toast, or value is shown, not implied by a click. One provable moment each. | `expect` in the play file |
| **5** | **Legible / text-backed** | The wording, labels, counts, and values under review are **readable in frame**. If the video cannot render them legibly, the still screenshot supplements it. | `expect` stills + your eyes |
| **6** | **File integrity + match** | Plays start to end, **non-blank, non-truncated**, sane duration, correct name, and is the clip for **that exact item** — not another one's. | `verify-video.py` |
| **6b** | **Narration, when it was asked for** | An audio track exists and is audible; every line is spoken over the step it describes, **finishes before the next action starts**, and says what the source says — no invented sentence. Voice and language match what was confirmed. | `verify-video.py --expect-audio` + listening |
| **6c** | **The voice is the one that was approved** | Measured, not read off a setting: median speaking pitch inside the profile's band, the greeting closing on its Thai particle (`ค่ะ` / `ครับ`) with a real pause after it, no clipping. A clip can name the right voice in every log and still be 23 Hz off the timbre the user approved — that is what this catches. | `check-narration.py --profile male\|female` |
| **7** | **Delivered + link verified** | Landed where it was meant to (folder / Drive / ticket / embedded in the document) and the reference **actually resolves and plays** from there — opened and confirmed, not assumed. | you, by opening it |

## What the script can and cannot decide

`scripts/verify-video.py` measures layers **1 and 6** (add `--expect-audio` on a narrated run) — resolution, codec, pixel format,
faststart, duration, truncation, blank frames, file naming. It is mechanical and it is honest:

- **Exit 0** = those two layers pass.
- **Exit 1** = at least one file failed; the message names which check.
- **Exit 2** = the check could not run (no `ffprobe`, missing file). **This is not a pass.** A
  check that could not run has proven nothing — treat it exactly as a failure.

Layers **2, 3, 4, 5, 7** are about *content and destination*. No probe can judge whether a clip
followed the source, arrived where it claimed, or is now attached to the right place. Those are
judged by watching the clip against the source list. **The script passing is necessary, never
sufficient** — never report "verified" on the strength of the script alone.

## Running it

```bash
SR=$(ls -d ~/.claude/plugins/cache/*/manual-maker/*/skills/screen-record 2>/dev/null | sort -V | tail -1); [ -n "$SR" ] || SR=~/.claude/skills/screen-record
"$SR/scripts/verify-video.py" ~/Downloads/recordings/*.mp4
```

Options: `--min-seconds N` (default 5), `--width` / `--height` (default 1920 × 1080) when the user
approved a different frame size at intake.

Narrated clips take a second, separate pass — the picture being to spec says nothing about the
voice:

```bash
"$SR/scripts/check-narration.py" --profile female ~/Downloads/recordings/*.mp4
```

`--profile` picks the approved voice from [`voice-profile.md`](voice-profile.md). Add
`--no-greeting-pause` only when the opening line genuinely has no sentence-final particle;
`--print-only` reports the numbers without judging, which is how a new profile gets measured in the
first place. **Exit 2 means the check could not run — that is a failure, not a pass.**

## When a layer fails

1. **Name the layer and the item.** "TC_03 — layer 3: never reached the ‘รายงาน’ menu."
2. **Fix the cause, not the symptom.** A missing `waitFor` target is a selector or a flow problem.
   Do **not** delete the `waitFor` to make the run go green — that removes the only thing standing
   between a truncated clip and a delivered one.
3. **Re-record that item, then re-run the whole gate on it** — including the layers that passed
   before. A re-record can break a layer that was previously green.
4. **Cannot be made to pass** (the target genuinely does not exist, access is missing) → report the
   item as **blocked with the specific reason**. Never substitute a partial clip.

## Reporting

Report per item, with the evidence, never as a bare total:

```
TC_01  ✅ recorded  1920x1080 · 00:47 · 3.1 MB · 2 stills   layers 1-7 green
TC_02  ✅ recorded  1920x1080 · 01:12 · 5.4 MB · 3 stills   layers 1-7 green
TC_03  ⛔ blocked   the "รายงาน" menu does not appear for this role — layer 3
```

Never write "อัดครบแล้ว" while any item is red or unverified. **ตรวจไม่ได้ = ไม่ผ่าน.**
