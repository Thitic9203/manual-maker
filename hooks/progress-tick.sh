#!/usr/bin/env bash
# PostToolUse hook — nudge the main thread to print a progress table for the user during a
# manual run, at most once per interval (default 10 minutes).
#
# WHY THIS SHAPE, and not a timer:
#   Claude Code has NO time-based hook. Hooks fire on events only (SessionStart, Pre/PostToolUse,
#   UserPromptSubmit, Stop, SubagentStop, ...). "Tell the user every 10 minutes" therefore has to
#   ride on an event that keeps happening during a run and then be throttled by wall clock. During
#   Steps 4-6 the run is a stream of tool calls (the main thread's Task dispatches plus every
#   writer's Bash capture), so PostToolUse fires often enough that a 10-minute throttle lands close
#   to on time. It is a floor, not a guarantee: no tool call => no tick.
#
#   SubagentStop was the obvious alternative and does NOT work: that event supports only
#   `decision`/`reason` (block-or-allow), NOT `hookSpecificOutput.additionalContext`, so it cannot
#   put a message into the conversation. PostToolUse is the only per-tool event that can.
#
# RUN MARKER — why this hook is silent everywhere else:
#   It emits nothing unless ~/.manual-maker/state/run.active exists. The skill creates that file at
#   the Step 2 confirmation gate and removes it at Step 9 delivery. Without the marker this hook
#   would nag on every Bash call in every unrelated project.
#
# SUBAGENT SAFETY:
#   Subagent tool calls fire hooks too, so the nudge can land in a writer's context instead of the
#   main thread's. Subagents cannot talk to the user, so the message itself says: main thread
#   prints the table, subagent ignores it and carries on. The subagent prompts already forbid
#   talking to the user, so the no-op is doubly enforced.
#
# Safety rails:
#   - Fail-silent: no marker, unreadable state, bad numbers, unwritable dir => exit 0, no output.
#   - Opt out: MANUAL_MAKER_NO_PROGRESS=1.
#   - Tunable: MANUAL_MAKER_PROGRESS_INTERVAL=<seconds> (default 600).
#   - Stale-run guard: a marker older than 12h is deleted, never nags forever after an abandoned run.
#   - Never blocks: emits advisory additionalContext only, never `decision: block`.
set -u

[ "${MANUAL_MAKER_NO_PROGRESS:-0}" = "1" ] && exit 0

STATE_DIR="$HOME/.manual-maker/state"
RUN="$STATE_DIR/run.active"
TICK="$STATE_DIR/last-tick"

# Not inside a manual run -> this hook does not exist.
[ -f "$RUN" ] || exit 0

NOW=$(date +%s 2>/dev/null) || exit 0

read_epoch() {
  # echo a positive integer from $1, or nothing. The -f test is not redundant: `< "$1"` on a
  # missing file is reported by the shell before a trailing 2>/dev/null takes effect, so without
  # it every run's first tick printed a redirect error on stderr.
  [ -f "$1" ] || return 0
  local v
  v=$(tr -dc '0-9' < "$1" 2>/dev/null | head -c 20)
  [ -n "$v" ] && printf '%s' "$v"
}

STARTED=$(read_epoch "$RUN")
[ -n "$STARTED" ] || exit 0

# Abandoned run: forget it rather than nag for days.
if [ "$(( NOW - STARTED ))" -gt 43200 ]; then
  rm -f "$RUN" "$TICK" 2>/dev/null
  exit 0
fi

INTERVAL="${MANUAL_MAKER_PROGRESS_INTERVAL:-600}"
case "$INTERVAL" in ''|*[!0-9]*) INTERVAL=600 ;; esac
[ "$INTERVAL" -lt 60 ] && INTERVAL=60

LAST=$(read_epoch "$TICK")
[ -n "$LAST" ] || LAST="$STARTED"

ELAPSED=$(( NOW - LAST ))
[ "$ELAPSED" -ge "$INTERVAL" ] || exit 0

# Claim the tick BEFORE emitting, so two near-simultaneous tool calls can't double-report.
printf '%s' "$NOW" > "$TICK" 2>/dev/null || exit 0

MINS=$(( ELAPSED / 60 ))

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "[manual-maker] ผ่านมา ${MINS} นาทีตั้งแต่รายงานความคืบหน้าครั้งล่าสุด.\n\nถ้าคุณเป็น subagent (ผู้เขียน/ผู้รีวิวหัวข้อ) — ข้ามข้อความนี้ ทำงานต่อ ห้ามพิมพ์ตาราง คุณคุยกับผู้ใช้ไม่ได้.\n\nถ้าคุณเป็น main thread ของงานทำคู่มือ — พิมพ์ตารางความคืบหน้าให้ผู้ใช้เห็นในข้อความถัดไป ตามรูปแบบใน references/parallel.md: บรรทัดแรกเป็น '~N% เสร็จ' แล้วตามด้วยตาราง | ขั้น | สถานะ | โดยแถวคือขั้นตอนจริงของรอบนี้ สถานะใช้ ✅ เสร็จ / 🟡 กำลังทำ (ใส่ตัวเลขที่วัดได้ เช่น จับภาพแล้วกี่ไฟล์ หัวข้อย่อยผ่านรีวิวกี่หัวข้อ) / ⬜ ยังไม่เริ่ม. ถ้ามีคำถามค้างจากรีวิว ให้ขึ้นบรรทัดต่อท้ายว่าค้างกี่ข้อและถามผู้ใช้เลย.\n\nรายงานเฉพาะสิ่งที่เกิดขึ้นจริง ห้ามเดาเปอร์เซ็นต์ให้ดูดี ห้ามนับหัวข้อที่ยังมีคำถามค้างว่าเสร็จ."
  }
}
EOF
exit 0
