#!/usr/bin/env bash
# screen-record preflight — make the machine ready to record.
#
#   preflight.sh            report only, never touches the machine
#   preflight.sh --check    same as above (explicit)
#   preflight.sh --install  install whatever is missing
#
# Exit 0 = ready to record. Exit 1 = something a human must fix (the message says what).
#
# Node, Playwright and Chromium install into ~/.manual-maker/runtime/ — the SAME sandbox the
# manual-maker skill uses, so a machine already set up for screenshots downloads nothing here.
# Capture then runs as:
#   NODE_PATH="$HOME/.manual-maker/runtime/node_modules" node record.js play.json
#
# ffmpeg is the one piece that must be a real system install: it is the encoder, and the encode
# settings are what make a recording match the reference clips. Without it there is no MP4 —
# only a .webm that most reviewers cannot open. That is a blocked run, never a silent downgrade.
#
# Safe to run repeatedly: every step is a no-op once satisfied.

set -uo pipefail

MODE="check"
case "${1:-}" in
  --install) MODE="install" ;;
  --check|"") MODE="check" ;;
  *) echo "usage: preflight.sh [--check|--install]" >&2; exit 2 ;;
esac

RUNTIME="$HOME/.manual-maker/runtime"
NODE_MODULES="$RUNTIME/node_modules"

REPORT=()
BLOCKED=0
INSTALLED=0

row() { REPORT+=("$1|$2|$3"); }
note() { [ "$MODE" = "install" ] && echo "  → $1" >&2; }

# ---------------------------------------------------------------- 1. Node.js
if command -v node >/dev/null 2>&1; then
  row "Node.js" "ok" "$(node -v)"
else
  row "Node.js" "blocked" "ไม่พบ Node.js — ติดตั้งจาก https://nodejs.org ก่อน"
  BLOCKED=1
fi

# ------------------------------------------------------------- 2. Playwright
# Resolved through NODE_PATH, not a global install: `npm i -g playwright` does NOT make
# require('playwright') work from an arbitrary cwd — the exact failure this check prevents.
pw_present() { NODE_PATH="$NODE_MODULES" node -e "require('playwright')" >/dev/null 2>&1; }

if [ "$BLOCKED" = "1" ]; then
  row "Playwright" "skipped" "รอ Node.js ก่อน"
elif pw_present; then
  PW_V=$(NODE_PATH="$NODE_MODULES" node -e "console.log(require('playwright/package.json').version)" 2>/dev/null)
  row "Playwright" "ok" "v${PW_V:-?}"
elif [ "$MODE" = "check" ]; then
  row "Playwright" "missing" "จะติดตั้งให้ (~50 MB)"
else
  note "ติดตั้ง Playwright ลง $RUNTIME"
  mkdir -p "$RUNTIME"
  [ -f "$RUNTIME/package.json" ] || \
    printf '{\n  "name": "manual-maker-runtime",\n  "private": true\n}\n' > "$RUNTIME/package.json"
  if (cd "$RUNTIME" && npm install --no-audit --no-fund --loglevel=error playwright >&2); then
    PW_V=$(NODE_PATH="$NODE_MODULES" node -e "console.log(require('playwright/package.json').version)" 2>/dev/null)
    row "Playwright" "installed" "v${PW_V:-?}"
    INSTALLED=1
  else
    row "Playwright" "blocked" "npm install ล้มเหลว — ตรวจอินเทอร์เน็ต/พร็อกซี แล้วรันใหม่"
    BLOCKED=1
  fi
fi

# --------------------------------------------------------- 3. Chromium binary
# Ask Playwright where its own browser should be, then check that path exists. A populated
# ~/Library/Caches/ms-playwright is NOT proof — those builds may belong to other versions.
chromium_present() {
  NODE_PATH="$NODE_MODULES" node -e "
    const fs = require('fs');
    process.exit(fs.existsSync(require('playwright').chromium.executablePath()) ? 0 : 1);
  " >/dev/null 2>&1
}

if [ "$BLOCKED" = "1" ]; then
  row "Chromium" "skipped" "รอ Playwright ก่อน"
elif ! pw_present; then
  row "Chromium" "missing" "จะติดตั้งพร้อม Playwright (~150 MB)"
elif chromium_present; then
  row "Chromium" "ok" "พร้อมใช้"
elif [ "$MODE" = "check" ]; then
  row "Chromium" "missing" "จะติดตั้งให้ (~150 MB)"
else
  note "ดาวน์โหลด Chromium (~150 MB) — ครั้งเดียว ใช้ซ้ำได้ทุกงานอัด"
  if (cd "$RUNTIME" && npx --yes playwright install chromium >&2); then
    row "Chromium" "installed" "พร้อมใช้"
    INSTALLED=1
  else
    row "Chromium" "blocked" "ดาวน์โหลดไม่สำเร็จ — รัน: cd $RUNTIME && npx playwright install chromium"
    BLOCKED=1
  fi
fi

# ------------------------------------------------------- 4. ffmpeg (+ ffprobe)
# ffmpeg encodes webm → mp4 at the spec settings; ffprobe is what verify-video.py measures with.
# They ship together, so one check covers both, but both are asserted — a Homebrew install with a
# broken symlink has been seen to leave ffprobe missing while ffmpeg answers.
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  FF_V=$(ffmpeg -version 2>/dev/null | head -1 | sed -E 's/ffmpeg version ([^ ]+).*/\1/')
  row "ffmpeg" "ok" "v${FF_V:-?}"
elif [ "$MODE" = "check" ]; then
  if command -v brew >/dev/null 2>&1; then
    row "ffmpeg" "missing" "จะติดตั้งให้ผ่าน Homebrew (~80 MB)"
  else
    row "ffmpeg" "blocked" "ไม่พบ ffmpeg และไม่มี Homebrew — ติดตั้งจาก https://ffmpeg.org/download.html ก่อน"
    BLOCKED=1
  fi
else
  if command -v brew >/dev/null 2>&1; then
    note "ติดตั้ง ffmpeg (ตัวแปลงวิดีโอ) ผ่าน Homebrew"
    if brew install ffmpeg >&2; then
      if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
        row "ffmpeg" "installed" "v$(ffmpeg -version 2>/dev/null | head -1 | sed -E 's/ffmpeg version ([^ ]+).*/\1/')"
        INSTALLED=1
      else
        row "ffmpeg" "blocked" "ติดตั้งแล้วแต่ยังเรียกไม่ได้ — เปิด terminal ใหม่ หรือตรวจ PATH"
        BLOCKED=1
      fi
    else
      row "ffmpeg" "blocked" "brew install ffmpeg ล้มเหลว — ติดตั้งเองจาก https://ffmpeg.org/download.html"
      BLOCKED=1
    fi
  else
    row "ffmpeg" "blocked" "ไม่พบ Homebrew — ติดตั้ง ffmpeg เองจาก https://ffmpeg.org/download.html"
    BLOCKED=1
  fi
fi

# ------------------------------------------------------------------- report
# Pipe-delimited, not column-padded: printf pads by byte count, and Thai text plus emoji make
# byte width ≠ display width, so padded columns come out ragged.
echo
echo "| เครื่องมือ | สถานะ | รายละเอียด |"
echo "|---|---|---|"
for r in "${REPORT[@]}"; do
  IFS='|' read -r n s d <<< "$r"
  case "$s" in
    ok)        icon="✅ พร้อม" ;;
    installed) icon="✅ ติดตั้งแล้ว" ;;
    missing)   icon="⬇️ ขาด" ;;
    blocked)   icon="❌ ติดขัด" ;;
    *)         icon="— ข้าม" ;;
  esac
  echo "| $n | $icon | $d |"
done
echo

if [ "$BLOCKED" = "1" ]; then
  echo "RESULT: blocked"
  exit 1
fi

if [ "$MODE" = "check" ]; then
  if printf '%s\n' "${REPORT[@]}" | grep -q '|missing|'; then
    echo "RESULT: needs-install"
  else
    echo "RESULT: ready"
  fi
else
  [ "$INSTALLED" = "1" ] && echo "RESULT: ready (installed)" || echo "RESULT: ready"
fi

echo "NODE_PATH=$NODE_MODULES"
exit 0
