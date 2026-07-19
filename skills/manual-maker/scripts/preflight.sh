#!/usr/bin/env bash
# manual-maker preflight — make the machine ready for a screenshot run.
#
# The user is not expected to know that a manual run needs Playwright, a Chromium
# binary, and Pillow. This script finds out and (with --install) fixes it.
#
#   preflight.sh            report only, never touches the machine
#   preflight.sh --check    same as above (explicit)
#   preflight.sh --install  install whatever is missing
#
# Exit 0 = ready to capture. Exit 1 = something a human must fix (message says what).
#
# Everything installs into ~/.manual-maker/runtime/ — a skill-owned sandbox, so the
# user's projects and global npm space are never modified. Capture scripts then run as:
#   NODE_PATH="$HOME/.manual-maker/runtime/node_modules" node capture.js
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

row() { REPORT+=("$1|$2|$3"); }          # name | state | detail
note() { [ "$MODE" = "install" ] && echo "  → $1" >&2; }

# ---------------------------------------------------------------- 1. Node.js
if command -v node >/dev/null 2>&1; then
  row "Node.js" "ok" "$(node -v)"
else
  row "Node.js" "blocked" "ไม่พบ Node.js — ติดตั้งจาก https://nodejs.org ก่อน"
  BLOCKED=1
fi

# ------------------------------------------------------------ 2. playwright
# Resolved through NODE_PATH, not a global install: `npm i -g playwright` does NOT
# make require('playwright') work from an arbitrary cwd, which is the exact failure
# this script exists to prevent.
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
# Ask Playwright where its own browser should be, then check that path exists.
# A populated ~/Library/Caches/ms-playwright is NOT proof — the cached builds may
# belong to other Playwright versions and be unusable by the one installed here.
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
  note "ดาวน์โหลด Chromium (~150 MB) — ครั้งเดียว ใช้ซ้ำได้ทุกคู่มือ"
  if (cd "$RUNTIME" && npx --yes playwright install chromium >&2); then
    row "Chromium" "installed" "พร้อมใช้"
    INSTALLED=1
  else
    row "Chromium" "blocked" "ดาวน์โหลดไม่สำเร็จ — รัน: cd $RUNTIME && npx playwright install chromium"
    BLOCKED=1
  fi
fi

# ------------------------------------------------------- 4. Pillow (annotation)
# Pinned to /usr/bin/python3: the Homebrew python3 on PATH usually has no PIL.
PY="/usr/bin/python3"
if ! [ -x "$PY" ]; then
  row "Pillow" "blocked" "ไม่พบ $PY"
  BLOCKED=1
elif "$PY" -c "import PIL" >/dev/null 2>&1; then
  PIL_V=$("$PY" -c "import PIL; print(PIL.__version__)" 2>/dev/null)
  row "Pillow" "ok" "v${PIL_V:-?}"
elif [ "$MODE" = "check" ]; then
  row "Pillow" "missing" "จะติดตั้งให้ (เล็ก)"
else
  note "ติดตั้ง Pillow สำหรับวงกลมเลขแดงบนภาพ"
  if "$PY" -m pip install --user --quiet Pillow >&2 2>/dev/null \
     || "$PY" -m pip install --user --quiet --break-system-packages Pillow >&2; then
    row "Pillow" "installed" "ok"
    INSTALLED=1
  else
    row "Pillow" "blocked" "ติดตั้งไม่สำเร็จ — รัน: $PY -m pip install --user Pillow"
    BLOCKED=1
  fi
fi

# ------------------------------------------------------------------- report
# Pipe-delimited, not column-padded: printf pads by byte count, and Thai text plus
# emoji make byte width ≠ display width, so padded columns come out ragged.
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
