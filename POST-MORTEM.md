# Post-mortem log — manual-maker

Written when a delivered artefact was wrong, or when a defect reached a user. Format follows the
`ols-qa` template (`post-mortem-template.md`): sequential ids, **root cause = mechanism, not
symptom**, and a lesson in one sentence. Deeper design records live in `RISK_REGISTER.md`.

## PM-1: screen-record — the delivered video flickered (2026-08-27)

**Problem.** A clip the skill recorded and handed over (`ELMS-2.4.1-เปิดหน้าต่างผู้ช่วย.mp4`,
1920×1080, 24.48 s) visibly flickered, while `verify-video.py` reported **PASS** on every check
with only cosmetic warnings. The gate measured that the file was big enough and in the right
codec; nothing in it measured whether the *picture was steady*, so the defect had nothing to pass
through.

**Root cause.** Both mechanisms live inside Playwright's `recordVideo`, were read out of
`playwright-core` and then measured, and **neither is reachable from its API**:

1. **Bitrate cap → quality pumping.** It spawns ffmpeg with a hardcoded
   `-c:v vp8 -qmin 0 -qmax 50 -crf 8 -deadline realtime -speed 8 -b:v 1M -threads 1` — 1 Mbps for
   1920×1080. When the page moves, rate control raises the quantiser and the whole frame softens,
   then snaps back. Measured on a region of the page that never changed: **6.6%** peak-to-trough
   swing in edge energy, **−5.3% in one frame**.
2. **Fixed-rate padding → judder.** `writeFrame` computes `frameNumber = floor((t − t₀) × 25)` and
   fills every delivery gap by **repeating the previous frame** onto a 40 ms grid. **21.2%** of the
   clip's *moving* frames were frozen repeats.
3. **(found while fixing) The pointer blinked out.** Hiding the arrow for each `expect` still also
   hid it from the video — **0.28 s per checkpoint**, measured on a two-checkpoint clip.

The plausible-sounding cause was tested and **rejected**: driving `Page.screencastFrame` directly on
the same machine gave **59.8 fps at `deviceScaleFactor` 2** (58.9 at dsf 1 — inside the noise) on a
*heavier* page. The browser was never the bottleneck; the single-threaded realtime VP8 encoder
behind it was, so lowering `deviceScaleFactor` would have fixed nothing and blurred every still.

**Fixes applied** (v0.35.0).

- `record.js` drives `Page.startScreencast` itself, **acks each frame before touching the disk**,
  keeps **every** frame with its real timestamp, and encodes **once** afterwards — deleting a whole
  lossy generation (JPEG → x264, not JPEG → VP8@1 Mbps → x264). No `.webm` sidecar; it was the damage.
- Capture **holds the picture** across every `expect` shutter, so the pointer never blinks out.
- Explicit full→limited range conversion: JPEG frames are full-range and a bare `-pix_fmt yuv420p`
  still emits `yuvj420p`, which fails layer 1 and crushes blacks.
- **Fail-closed at record time**: the run dies if the achieved rate is under `minUniqueFps`, if
  `maxScratchMb` was hit, or if any frame failed to write.
- **Gate layers 1b + 1c** and a **10-layer defense** in `quality-gate.md`; `verify-video.py` fails
  >5% frozen frames inside moving stretches and requires a `<name>.capture.json` that matches the file.

Measured after: frozen frames **21.2% → 0.00–1.44%**, static-region swing **6.6% → 0.5%**, pointer
blink-outs **2 → 0**, capture 59.3 fps at a 17.6 ms p95 gap. The flickering clip now **FAILs** the gate.

**A bug nearly introduced by the fix.** The first cut thinned the stream with
`keep if t − lastKept ≥ 1/30` to bound disk. On a page delivering ~31 fps (median gap 22 ms) it
dropped every second frame — 22 ms is under the 31 ms minimum, so the filter always waits for the
next one — yielding **15.4 fps, worse judder than the defect being fixed**. Every decimator aliases
that way when the source rate is near the target. Rule kept: **bound the disk, never the frame rate.**

**Lesson.** A gate that only measures *file format* is not a quality gate — until something
mechanically measures the property a user actually complains about, that property is unprotected;
and a third-party tool's defaults must be read from its source and measured, never assumed fit for
a deliverable.
