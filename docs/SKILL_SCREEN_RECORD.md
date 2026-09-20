# Third skill — `screen-record`, and the one invariant that must never be undone (v0.35.0+)

`skills/screen-record/` is the repo's third auto-loaded skill: it records a headless MP4 walkthrough
of a web flow (intake → confirm → record → 7-layer gate), optionally narrated. Most of it reads the
way you would expect. **One thing does not, and it will look like an obvious simplification to
anyone who has not read this: the skill deliberately does NOT use Playwright's `recordVideo`.**

A delivered clip (ELMS-2.4.1) visibly flickered while passing the entire gate. Both causes live
inside `recordVideo`, were read out of `playwright-core` and then **measured**, and **neither is
reachable from Playwright's API** — so "pass an option" is not an available fix:

- **1 Mbps cap → the picture pumps.** It spawns ffmpeg with a hardcoded
  `-c:v vp8 -qmin 0 -qmax 50 -crf 8 -deadline realtime -speed 8 -b:v 1M -threads 1` — 1 Mbps at
  1920×1080. On motion, rate control softens the *whole* frame and then snaps back. Measured on a
  region of the page that never changed: **6.6%** peak-to-trough swing in edge energy, **−5.3% in a
  single frame**.
- **Fixed-rate padding → the motion judders.** `writeFrame` computes
  `frameNumber = floor((t − t₀) × 25)` and fills every delivery gap by **repeating the previous
  frame** onto a 40 ms grid. **21.2%** of the delivered clip's *moving* frames were frozen repeats.

**Do not "fix" this by lowering `deviceScaleFactor`** — that was tested and changes nothing: driving
`Page.screencastFrame` directly gives **59.8 fps at dsf 2** and 58.9 fps at dsf 1 (inside the noise)
on a heavier page. The browser was never the bottleneck; the single-threaded realtime VP8 encoder
behind it was. So `record.js` owns the capture — CDP screencast, **ack first / write second**, every
frame kept with its real timestamp, **one** encode afterwards (JPEG → x264 CRF 18, full→limited
range). There is no `.webm` any more; the WebM *was* the damage.

Three traps here are measured, not assumed, and must not be simplified away:

1. **Never thin the frame stream.** The first cut kept a frame only if `t − lastKept ≥ 1/30`. On a
   page delivering ~31 fps (median gap 22 ms) that dropped every second frame and produced
   **15.4 fps — worse judder than the bug being fixed**. Every decimator aliases when the source
   rate is near the target, and a phase accumulator does the same. Bound the disk
   (`maxScratchMb`), never the frame rate.
2. **`-pix_fmt yuv420p` alone is not enough.** Screencast frames are JPEG, i.e. full-range, so the
   output still comes out tagged `yuvj420p` — which fails the gate's own layer-1 check and crushes
   blacks. The levels must be **converted** (`scale=in_range=full:out_range=limited`), not
   relabelled.
3. **The checkpoint still must hold the picture.** Hiding the pointer for the `expect` screenshot
   also hid it from the video — **0.28 s per checkpoint**, measured. Capture pauses across the
   whole shutter window (`resume()` in a `finally`); a checkpoint is a settled screen, so holding
   is invisible.
4. **Those holds must be DECLARED, or layer 1b fails its own good clips.** A hold repeats one frame
   on purpose, and on a page with a background animation that is indistinguishable from a stall —
   found by regression, not reasoning: a clip captured at 51.9 fps with an 18 ms p95 gap scored
   5.3% and failed purely on its three holds. So `capture.json` carries `holdSpans` (seconds on the
   video timeline) and the verifier excludes exactly those, capped at 25% of the clip so
   "it was all a hold" cannot become the loophole.

**The gate half.** `quality-gate.md` now carries layers **1b** (steady picture) and **1c**
(provenance) plus a **แนวป้องกัน 10 ชั้น** table. `verify-video.py` fails a clip whose *moving*
frames are >5% frozen repeats — a threshold **measured** (flickering clip 21.2%; six good clips
0.00–1.44%) and computed entirely inside ffmpeg (`tblend` + `signalstats`) so it needs neither
numpy nor Pillow. Every run writes `<name>.capture.json` (pipeline, achieved fps, gap distribution,
encoder args, still-holds); the script checks the file **against** it and **fails when it is
missing** — same fail-closed stance as manual-maker's `clean/` folder. `--no-manifest` exists only
for clips this skill did not record.

**Do not oversell those scripts.** Layer 1b proves nothing froze mid-motion; it does **not** prove
the picture is sharp. A generalised "detail-loss" metric was built for exactly that and **rejected**
because it did not separate good from bad (real-OLD 4.13% vs real-NEW 5.04%) — shipping it would
have been decoration. Sharpness, banding and "is this the right screen" stay layer-10 human rows,
and **ตรวจไม่ได้ = ไม่ผ่าน** applies in full. Full record: `RISK_REGISTER.md` MM-006 and
`POST-MORTEM.md` PM-1.

