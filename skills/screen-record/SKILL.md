---
name: screen-record
description: Use when recording a screen video (MP4) of a web system — a walkthrough clip for a manual, a demo of a feature, or video evidence of a test case. Runs a structured intake for environment, URL, account and the source that says what to record (manual file, test-case list, spec), remembers those answers so later runs only reconfirm, summarizes everything for explicit confirmation, then records headlessly with Playwright at 1920×1080 / H.264 CRF 20, captures a still at each expected result, and verifies every file against a 7-layer quality gate. Triggers on "อัดวิดีโอ", "อัดหน้าจอ", "อัดคลิป", "ทำวิดีโอสาธิต", "record a video", "screen recording", "record the flow", "screen-record".
---

# Screen Record

## Overview

Screen Record turns a live web flow into a **finished MP4** — the kind that goes into a manual as a
walkthrough, into a ticket as evidence, or to a customer as a demo.

It records **headlessly**: its own Chromium, its own window that never appears. The user's screen is
never taken over, no cursor is painted, no *"Claude is controlling the screen"* glow lands in the
frame, and the user keeps working while the whole batch records unattended.

Everything it produces is built to one spec — the same settings as the team's System / Integration /
Unit test recordings — so a clip made today sits beside one made months ago without looking
different. That spec, and the reasons behind each number, are in
[`references/video-spec.md`](references/video-spec.md).

## Non-negotiable working rules — read first

1. **ห้ามมโน / ห้ามคิดเอง / ห้ามตัดสินใจแทนผู้ใช้.** Missing, vague, or unsure → **STOP and ask**.
   Never invent a URL, an environment, an account, or a step. Recording the wrong flow costs a full
   re-run to discover.
2. **ห้ามเลือก environment เอง.** Which env to record on is the user's call, always — even when one
   env is easier to reach. Ask, and wait.
3. **ยืนยันก่อนเริ่มเสมอ.** When the intake data is complete, **summarize it in chat and get an
   explicit confirmation before the first recording.** Complete data is not permission to start.
4. **ทุกขั้นตอนต้องมีที่มา.** Every step in a clip traces to the source the user gave (manual file,
   test-case list, spec) or to a step list they confirmed. Never add a step the source lacks; never
   skip one it has. Source contradicts the live screen → **stop and ask**, do not pick a winner.
5. **จำไว้ ไม่ถามซ้ำ.** **Every question this user has already answered is remembered** —
   environment, URL, account, login selectors, source, file naming, output folder, video settings,
   destination. All of it is written to the shared profile once the user confirms. On any later
   run, show the saved values back and **reconfirm before starting** — never re-interview. Two
   exceptions only: the **password** (never stored) and **which flows to record this run** (it
   changes every run by nature).
6. **Delivery gate — ผ่านครบ 7 ชั้นเท่านั้น.** Never say "เสร็จแล้ว" / hand a file over / embed a clip
   until every item passes all seven layers of
   [`references/quality-gate.md`](references/quality-gate.md). **ตรวจไม่ได้ = ไม่ผ่าน** — there is no
   "น่าจะผ่าน". A check that could not run is a failure, not a pass.
7. **A short clip is never a small success.** A run that stopped before reaching its target is
   **blocked with a reason**, never a shorter deliverable.

**Running this skill's scripts — always resolve the path first.** `scripts/preflight.sh`,
`scripts/record.js`, `scripts/narrate.py`, and `scripts/verify-video.py` live **next to this file**, never in the user's
project. The run's cwd *is* the user's project, so a bare `scripts/record.js` resolves there, is not
found, and looks like it does not exist — do **not** conclude it is missing and hand-improvise the
step. Neither shortcut works either: `CLAUDE_PLUGIN_ROOT` is **unset** in Bash tool calls (hooks get
it, tool calls do not), and the plugin cache path is version-stamped, so it cannot be hardcoded.
Resolve it in the **same** Bash call as the script — shell state does not survive between calls:

```bash
SR=$(ls -d ~/.claude/plugins/cache/*/manual-maker/*/skills/screen-record 2>/dev/null | sort -V | tail -1); [ -n "$SR" ] || SR=~/.claude/skills/screen-record
"$SR/scripts/preflight.sh" --check
```

`sort -V | tail -1` picks the newest installed version; the fallback covers the personal-skill
install (`cp -r skills/screen-record ~/.claude/skills/`). If `$SR` comes back empty **and** the
fallback path does not exist, say so and stop — do not reimplement the recorder inline.

## Workflow

### Step 1 — Load what this user already told us

Follow [`references/intake.md`](references/intake.md) § 0. The store is
`~/.manual-maker/profiles/<slug>.json`, shared with the `manual-maker` skill — so a system that
already has a manual already has its URL and login selectors on file. Match on the profile's
**contents**, not its filename.

Found → print it back and ask what changed. **Reconfirm, do not re-interview.**

### Step 2 — Intake

Run [`references/intake.md`](references/intake.md), one question at a time, skipping every field the
user confirmed unchanged. The four that are always asked, every run:

- **Environment** (dev / staging / pre-prod / production) — never chosen for the user.
- **URL** — shown as a default from the profile, confirmed live.
- **Account + role**, with the password fresh in-session and never stored.
- **What to record this run** — from the **source** (manual file, test-case list link, spec). No
  source → have the user list the steps, then read them back for confirmation.
- **Where the finished files go** — the output folder, and whether anything is uploaded afterwards.
  Never assume a location; offer `~/Downloads/recordings/` and let the user confirm or redirect.
  With a profile, show the saved folder and reconfirm rather than asking again.
- **Narration — wanted or not, in Thai or English, male or female.** All three are the user's
  choice; never pick a language or a voice gender for them. If wanted, write one `say` line per
  step **from the same source as the steps** (never invented) and read the whole script back for
  confirmation before recording.

### Step 3 — Preflight

```bash
SR=$(ls -d ~/.claude/plugins/cache/*/manual-maker/*/skills/screen-record 2>/dev/null | sort -V | tail -1); [ -n "$SR" ] || SR=~/.claude/skills/screen-record
"$SR/scripts/preflight.sh" --check
```

Report the table in the confirmation summary (what is ready, what will be installed, how large).
After the user's "go", run `--install`. It installs into `~/.manual-maker/runtime/` — the same
sandbox `manual-maker` uses, so a machine already set up downloads nothing.

`ffmpeg` must be a real system install; without it there is no MP4. If it cannot be installed, that
is a **blocked** run — say so. Never silently deliver a `.webm` instead.

### Step 4 — Confirmation Gate (mandatory)

Print the full summary table from `intake.md` — env, URL, VPN, account, source, **the numbered list
of what will be recorded**, file names, output folder, video settings, tool status, destination —
and ask, verbatim:

> **"ยืนยันข้อมูลทั้งหมดถูกต้อง และเริ่มอัดได้หรือไม่"**

**Do not record until the user confirms explicitly.** Then save the profile (minus every secret) and
tell them it was saved.

### Step 5 — Write one play file per clip

A play file is JSON: where to go, what to click, what must appear. Schema and every step action:
[`references/video-spec.md`](references/video-spec.md) § The play file. Two fields carry the gate:

- **`waitFor`** on every step that navigates or changes state — what must be visible afterwards.
  The run **fails closed** if it never appears (layer 3). Never remove one to make a run go green.
- **`expect`** wherever an outcome must be proven — asserted, then captured as a still (layers 4
  and 5).

The clip must look like **a person using the system and recording their own screen**. That is what
the recorder already does by default: a mouse pointer glides to each control and flashes on click
(tracking the *real* pointer through the page's own mouse events, so it can never show a click that
did not happen), text is typed character by character, and scrolling is paced. The pointer is the
**only** thing drawn into the page — never add a banner, a URL strip, or a step counter "just for
this run", because it lands in every frame of the deliverable. Diagnostics go to the run log.

Derive the steps and the wording from the **source**, and name each clip after the source's own id
(`TC_01` → `TC_01.mp4`). Credentials never go in a play file.

### Step 4b — Play a voice sample and get approval (narrated runs only, mandatory)

```bash
"$SR/scripts/narrate.py" --sample play-TC_01.json --out /tmp/sample.mp3
```

Speaks the run's **own opening lines** in the exact voice, gender and tone the run would use, then
hand the file to the user and **wait for an explicit approval before recording anything**.

Two reasons this gate exists rather than trusting the settings:

- Recording is the expensive half — a 90-second clip costs 90 seconds per take, and a voice
  rejected afterwards means re-recording every clip in the batch.
- A voice cannot be judged from its name. `th-TH-NiwatNeural` at tone `presenter` reads as correct
  on paper; four presets were each approved on paper and then rejected by ear ("shouting",
  "fragmented", "colliding", "too casual for a customer").

The sample uses the run's real script, never a stock sentence — **register is the biggest single
factor** in whether narration sounds human, so a generic sample would approve the wrong thing.

Rejected → change tone / gender / wording, re-sample, ask again. Never record on a maybe.

### Step 5b — Measure the narration first (narrated runs only)

```bash
"$SR/scripts/narrate.py" --prepare play-TC_01.json
```

This speaks each line with the real voice and writes `play-TC_01.saydur.json`. `record.js` picks it
up automatically and **holds each narrated step open until its sentence finishes**, so the voice
never talks over the next click. Skipping this does not break the run — it just records unpaced,
and the first narrated run without it had three lines running 5–6 s into the following step.

Review the phrasing it prints (`--dry-run` on a finished video shows the same split). Lines are cut
into breath-sized phrases at natural boundaries, with a longer pause at a sentence end than inside
a clause.

### Step 6 — Record

```bash
SR=$(ls -d ~/.claude/plugins/cache/*/manual-maker/*/skills/screen-record 2>/dev/null | sort -V | tail -1); [ -n "$SR" ] || SR=~/.claude/skills/screen-record
SR_USER='<user>' SR_PASS='<password>' NODE_PATH="$HOME/.manual-maker/runtime/node_modules" \
  node "$SR/scripts/record.js" play-TC_01.json
```

Credentials go **inline on the command** — out of the shell profile, out of every file. Never echo
them back; write `password provided (not shown)`.

One clip per run. Batch by looping over the play files, and **report progress as each finishes** —
a long silent batch is indistinguishable from a hung one.

A non-zero exit is a real failure. Read what it says (a `waitFor` that never appeared, a login that
never reached `readySelector`) and fix that cause — the flow, the selector, or the account. Do not
retry the same command hoping for a different result, and do not weaken the play file.

### Step 6b — Speak the narration onto the clip (narrated runs only)

```bash
"$SR/scripts/narrate.py" ~/Downloads/recordings/TC_01.mp4
```

Reads the timeline `record.js` wrote during the run — offsets are **measured, never estimated** —
speaks each line, places it at its moment, normalizes the track to broadcast loudness, and muxes it
in with the video stream copied untouched. It warns if a line overruns its step or the video's end.

### Step 7 — Verify (fail-closed)

```bash
"$SR/scripts/verify-video.py" ~/Downloads/recordings/*.mp4        # add --expect-audio if narrated
```

If the user approved a frame size other than 1920×1080 at intake, pass `--width` / `--height` to
match it — the checker defaults to the spec size and will otherwise fail a clip for being the size
the user asked for.

That covers layers 1 and 6. Then judge layers 2–5 and 7 **by watching each clip against the source
list** — did it drive every step, arrive at each target, show each result legibly, and land where it
was supposed to. Full procedure: [`references/quality-gate.md`](references/quality-gate.md).

Any layer red → fix the cause, re-record that item, **re-run the whole gate on it**.

### Step 8 — Deliver

Report per item, never as a bare total:

```
TC_01  ✅ recorded  1920x1080 · 00:47 · 3.1 MB · 2 stills   layers 1-7 green
TC_03  ⛔ blocked   the "รายงาน" menu does not appear for this role — layer 3
```

Say where the files are, list anything blocked with its reason, and state plainly that nothing was
skipped silently. Files land in `~/Downloads/recordings/` unless the user chose otherwise.

**Embedding a clip in a manual:** hand the paths to the `manual-maker` skill — this skill produces
the video and stops there. It does not write documents.

## What this skill does not do

- **Does not write or edit documents** — that is `manual-maker`.
- **Does not upload anywhere by default.** Uploading to Drive / a ticket / Confluence happens only
  when the user asked for it at intake, and layer 7 then requires opening the link to confirm it
  plays.
- **Does not perform destructive actions to make a nicer clip.** Recording drives the flow the
  source describes. Creating, editing, or deleting live records to make a screen look full needs the
  user's explicit authorisation for that run.
- **Does not record the user's real screen.** Everything is headless. If a flow genuinely cannot be
  automated (SSO / MFA / captcha), the user logs in themselves and supplies a `storageState.json` —
  see [`references/video-spec.md`](references/video-spec.md).
