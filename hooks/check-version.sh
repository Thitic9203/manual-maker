#!/usr/bin/env bash
# SessionStart hook — SELF-UPDATING (Path B). On every session start it compares the installed
# version to main on GitHub and, if main is ahead, kicks off an install of the new version in
# the BACKGROUND via the supported `claude plugin update` CLI, then tells the user it is doing so.
# The update applies on the NEXT session (or after /reload-plugins) — Claude Code cannot swap a
# plugin into the already-running session.
#
# This DELIBERATELY overrides the old notify-only design and bypasses Claude Code's per-marketplace
# auto-update opt-in (which is off by default for third-party marketplaces). It was chosen by the
# repo owner to make updates truly zero-touch on the plugin path. See RISK_REGISTER.md for the
# trade-offs (mutates the install without a per-session prompt; reimplements a native feature).
#
# Safety rails, in order:
#   - Fast fail: fail-silent when offline / up-to-date / no curl / unreadable manifest (exit 0).
#   - Opt-out: MANUAL_MAKER_NO_AUTOUPDATE=1 degrades to notify-only.
#   - No CLI: if `claude` is not on PATH, degrade to notify-only (never errors the session).
#   - Non-blocking: the update runs detached (nohup &) so session start is never delayed.
#   - Single-flight: an atomic mkdir lock (stale after 10 min) stops overlapping updates.
#   - Supported path: uses `claude plugin update`, never a raw git-pull into the plugin cache.
#
# Fail-silent: offline, no curl, unreadable manifest, up-to-date, or any parse error => no
# output, exit 0. It must never block or slow a session start (3s network cap).
set -u

REPO_RAW="https://raw.githubusercontent.com/Thitic9203/manual-maker/main/.claude-plugin/plugin.json"
ROOT="${CLAUDE_PLUGIN_ROOT:-}"
LOCAL_MANIFEST="${ROOT}/.claude-plugin/plugin.json"

# Need the installed manifest to know the local version.
[ -n "$ROOT" ] && [ -f "$LOCAL_MANIFEST" ] || exit 0

extract_version() {
  # reads stdin, prints the first x.y.z found in a "version": "..." field
  grep -m1 '"version"' | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/'
}

LOCAL_VER="$(extract_version < "$LOCAL_MANIFEST" 2>/dev/null)"
[ -n "$LOCAL_VER" ] || exit 0

# Try the system curl first: on macOS /usr/bin/curl uses Secure Transport + the system
# keychain and is reliable, whereas a MacPorts/Homebrew curl on PATH may have a broken CA
# bundle (SSL error 60). Fall back to whatever curl is on PATH for non-macOS.
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

# Compare core semver only; strip any pre-release suffix (0.2.0-rc1 -> 0.2.0).
lv="${LOCAL_VER%%-*}"
rv="${REMOTE_VER%%-*}"

ver_gt() { # true (0) if $1 > $2 as numeric major.minor.patch
  local a1 a2 a3 b1 b2 b3
  IFS=. read -r a1 a2 a3 <<<"$1"
  IFS=. read -r b1 b2 b3 <<<"$2"
  a1=${a1:-0}; a2=${a2:-0}; a3=${a3:-0}
  b1=${b1:-0}; b2=${b2:-0}; b3=${b3:-0}
  case "${a1}${a2}${a3}${b1}${b2}${b3}" in *[!0-9]*) return 1 ;; esac
  [ "$a1" -gt "$b1" ] && return 0; [ "$a1" -lt "$b1" ] && return 1
  [ "$a2" -gt "$b2" ] && return 0; [ "$a2" -lt "$b2" ] && return 1
  [ "$a3" -gt "$b3" ]
}

emit() { printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$1"; }

# Up to date (or local ahead) => silent.
ver_gt "$rv" "$lv" || exit 0

# --- Behind: trigger self-update (Path B) --------------------------------------
# Opt-out escape hatch: this hook auto-updates the install, which bypasses Claude
# Code's deliberate per-marketplace opt-in. Set MANUAL_MAKER_NO_AUTOUPDATE=1 to
# fall back to notify-only.
if [ "${MANUAL_MAKER_NO_AUTOUPDATE:-}" = "1" ]; then
  emit "manual-maker: มีเวอร์ชันใหม่ v${REMOTE_VER} (ติดตั้ง v${LOCAL_VER}) แต่ auto-update ถูกปิดไว้ (MANUAL_MAKER_NO_AUTOUPDATE=1). แจ้ง user ให้อัปเดตเอง: /plugin marketplace update manual-maker-dev แล้ว /reload-plugins หรือเปิด session ใหม่."
  exit 0
fi

# Self-update needs the claude CLI on PATH; if absent, degrade to notify-only.
CLAUDE_BIN="$(command -v claude 2>/dev/null || true)"
if [ -z "$CLAUDE_BIN" ]; then
  emit "manual-maker: มีเวอร์ชันใหม่ v${REMOTE_VER} (ติดตั้ง v${LOCAL_VER}). อัปเดตอัตโนมัติทำไม่ได้เพราะไม่พบคำสั่ง claude ใน PATH. แจ้ง user ให้อัปเดตเองใน Claude Code: /plugin marketplace update manual-maker-dev แล้ว /reload-plugins."
  exit 0
fi

# Concurrency guard: one background update at a time across sessions. mkdir is
# atomic. Clear a stale lock (>10 min) left by a crashed run before claiming it.
LOCK="${TMPDIR:-/tmp}/manual-maker-autoupdate.lock"
find "$LOCK" -maxdepth 0 -mmin +10 -exec rmdir {} \; 2>/dev/null
if ! mkdir "$LOCK" 2>/dev/null; then
  emit "manual-maker: กำลังดาวน์โหลดเวอร์ชันใหม่ v${REMOTE_VER} อยู่เบื้องหลัง (อีก session สั่งไปแล้ว). แจ้ง user ว่าเปิด session ใหม่ หรือ /reload-plugins เพื่อใช้เวอร์ชันใหม่."
  exit 0
fi

# Run the update detached so session start never blocks on the download. Uses the
# supported CLI (not a raw cache mutation). Applies on the NEXT session / reload.
LOG="${TMPDIR:-/tmp}/manual-maker-autoupdate.log"
CLAUDE_BIN="$CLAUDE_BIN" LOCK="$LOCK" nohup sh -c '
  "$CLAUDE_BIN" plugin marketplace update manual-maker-dev </dev/null
  "$CLAUDE_BIN" plugin update manual-maker@manual-maker-dev </dev/null
  rmdir "$LOCK" 2>/dev/null
' >"$LOG" 2>&1 &

emit "manual-maker: กำลังอัปเดตอัตโนมัติ v${LOCAL_VER} → v${REMOTE_VER} เบื้องหลัง — จะใช้งานได้เมื่อเปิด session ใหม่ (หรือพิมพ์ /reload-plugins หลังดาวน์โหลดเสร็จ). แจ้ง user สั้นๆ ตามนี้ และบอกว่าถ้าไม่อยากให้อัปเดตอัตโนมัติ ให้ตั้ง env MANUAL_MAKER_NO_AUTOUPDATE=1."
exit 0
