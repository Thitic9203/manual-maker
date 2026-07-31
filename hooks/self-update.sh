#!/usr/bin/env bash
# USER-SCOPE SessionStart hook — the survive-disable half of manual-maker's auto-update.
#
# WHY THIS EXISTS (separate from hooks/check-version.sh):
#   Claude Code does NOT run a *disabled* plugin's hooks. So the plugin's own
#   check-version.sh freezes the moment the install is disabled — it bit a real machine
#   (stuck at 0.22.0 with the skill silently missing from the session). This script is
#   installed into ~/.claude/settings.json (user scope) by check-version.sh while the
#   plugin is enabled, and a user-scope hook runs on EVERY session regardless of any
#   plugin's enabled state — so it keeps working after a disable.
#
# WHAT IT DOES (state machine, keyed on installed-vs-GitHub version + enabled/disabled):
#   opt-out set .................................. exit (MANUAL_MAKER_NO_AUTOUPDATE=1)
#   plugin not installed ......................... exit (nothing to update)
#   checked within the throttle window ........... exit (once per 6h, not every session)
#   up to date ................................... exit silent
#   behind + ENABLED ............................. exit silent  (check-version.sh handles it — no double update)
#   behind + DISABLED ............................ enable + update in the background, then notify
#
# Auto-enabling a disabled install is deliberate and is the repo owner's explicit choice
# for this internal team tool (see RISK_REGISTER.md MM-005): the whole point is a
# zero-touch install that stays current. The trigger is a *new version* only, so a user
# who disables an up-to-date install is left alone; there is no re-enable loop. Anyone who
# truly wants it off sets MANUAL_MAKER_NO_AUTOUPDATE=1, which stops this script entirely.
#
# Safety rails mirror check-version.sh: fail-silent everywhere, 3s network cap, a 6h
# throttle, a shared single-flight lock, background/non-blocking update, supported
# `claude plugin` CLI only (never a raw cache mutation).
set -u

[ "${MANUAL_MAKER_NO_AUTOUPDATE:-}" = "1" ] && exit 0
[ -n "${HOME:-}" ] || exit 0

MARKETPLACE="manual-maker-dev"
PLUGIN="manual-maker@manual-maker-dev"
REPO_RAW="https://raw.githubusercontent.com/Thitic9203/manual-maker/main/.claude-plugin/plugin.json"
SETTINGS="${HOME}/.claude/settings.json"
STATE_DIR="${HOME}/.manual-maker/state"
STAMP="${STATE_DIR}/last-selfcheck"

# --- Resolve the installed version from the plugin cache (version-stamped path) --------
# newest installed version dir wins; if nothing is installed, there is nothing to do.
LOCAL_MANIFEST="$(ls "${HOME}"/.claude/plugins/cache/*/manual-maker/*/.claude-plugin/plugin.json 2>/dev/null | sort -V | tail -1)"
[ -n "$LOCAL_MANIFEST" ] && [ -f "$LOCAL_MANIFEST" ] || exit 0

extract_version() { grep -m1 '"version"' | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/'; }
LOCAL_VER="$(extract_version < "$LOCAL_MANIFEST" 2>/dev/null)"
[ -n "$LOCAL_VER" ] || exit 0

# --- Throttle: check GitHub at most once per 6h, not on every session start ------------
if [ -f "$STAMP" ] && [ -z "$(find "$STAMP" -mmin +360 2>/dev/null)" ]; then
  exit 0
fi
mkdir -p "$STATE_DIR" 2>/dev/null && : > "$STAMP" 2>/dev/null || true

emit() { printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$1"; }

fetch_remote() {
  local url="$1" bin out
  for bin in /usr/bin/curl curl; do
    command -v "$bin" >/dev/null 2>&1 || continue
    out="$("$bin" -fsS --max-time 3 "$url" 2>/dev/null)" && [ -n "$out" ] && { printf '%s' "$out"; return 0; }
  done
  return 1
}

REMOTE_JSON="$(fetch_remote "$REPO_RAW")" || exit 0
REMOTE_VER="$(printf '%s' "$REMOTE_JSON" | extract_version 2>/dev/null)"
[ -n "$REMOTE_VER" ] || exit 0

lv="${LOCAL_VER%%-*}"; rv="${REMOTE_VER%%-*}"
ver_gt() {
  local a1 a2 a3 b1 b2 b3
  IFS=. read -r a1 a2 a3 <<<"$1"; IFS=. read -r b1 b2 b3 <<<"$2"
  a1=${a1:-0}; a2=${a2:-0}; a3=${a3:-0}; b1=${b1:-0}; b2=${b2:-0}; b3=${b3:-0}
  case "${a1}${a2}${a3}${b1}${b2}${b3}" in *[!0-9]*) return 1 ;; esac
  [ "$a1" -gt "$b1" ] && return 0; [ "$a1" -lt "$b1" ] && return 1
  [ "$a2" -gt "$b2" ] && return 0; [ "$a2" -lt "$b2" ] && return 1
  [ "$a3" -gt "$b3" ]
}

# Up to date (or local ahead) => nothing to do. Respect a disabled up-to-date install.
ver_gt "$rv" "$lv" || exit 0

# Behind + ENABLED => check-version.sh (the plugin's own hook) is already handling it.
# Only act when the install is DISABLED, which is exactly when that hook cannot run.
is_disabled() {
  [ -f "$SETTINGS" ] || return 1
  grep -Eq '"manual-maker@manual-maker-dev"[[:space:]]*:[[:space:]]*false' "$SETTINGS"
}
is_disabled || exit 0

# Disabled + behind. Needs the claude CLI; without it, degrade to a notify.
CLAUDE_BIN="$(command -v claude 2>/dev/null || true)"
if [ -z "$CLAUDE_BIN" ]; then
  emit "manual-maker: ปลั๊กอินถูกปิดอยู่และมีเวอร์ชันใหม่ v${REMOTE_VER} (ติดตั้ง v${LOCAL_VER}) แต่ไม่พบคำสั่ง claude ใน PATH จึงอัปเดตอัตโนมัติไม่ได้. แจ้ง user ให้เปิดและอัปเดตเองใน Claude Code: /plugin enable แล้ว /plugin marketplace update manual-maker-dev."
  exit 0
fi

# Single-flight, shared with check-version.sh so the two hooks never double-update.
LOCK="${TMPDIR:-/tmp}/manual-maker-autoupdate.lock"
find "$LOCK" -maxdepth 0 -mmin +10 -exec rmdir {} \; 2>/dev/null
mkdir "$LOCK" 2>/dev/null || exit 0

# Enable, then refresh + update — detached so session start never blocks. Enable-then-update
# is required: enabling alone leaves the stale version pinned until a later hook run.
LOG="${TMPDIR:-/tmp}/manual-maker-autoupdate.log"
CLAUDE_BIN="$CLAUDE_BIN" PLUGIN="$PLUGIN" MARKETPLACE="$MARKETPLACE" LOCK="$LOCK" nohup sh -c '
  "$CLAUDE_BIN" plugin enable "$PLUGIN" </dev/null
  "$CLAUDE_BIN" plugin marketplace update "$MARKETPLACE" </dev/null
  "$CLAUDE_BIN" plugin update "$PLUGIN" </dev/null
  rmdir "$LOCK" 2>/dev/null
' >"$LOG" 2>&1 &

emit "manual-maker: ปลั๊กอินถูกปิดอยู่และมีเวอร์ชันใหม่ v${REMOTE_VER} — กำลังเปิดใช้งานและอัปเดตอัตโนมัติเป็น v${REMOTE_VER} เบื้องหลัง (จาก v${LOCAL_VER}). จะใช้งานได้เมื่อเปิด session ใหม่ หรือพิมพ์ /reload-plugins หลังดาวน์โหลดเสร็จ. แจ้ง user สั้นๆ ตามนี้ และบอกว่าถ้าไม่อยากให้อัปเดต/เปิดอัตโนมัติ ให้ตั้ง env MANUAL_MAKER_NO_AUTOUPDATE=1."
exit 0
