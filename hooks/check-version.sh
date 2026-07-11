#!/usr/bin/env bash
# SessionStart hook — notify (only) when a newer manual-maker version exists on GitHub.
#
# Notify-only by design: it never mutates the install, never runs git/pull, never fights
# Claude Code's plugin cache. It just compares the installed version to main on GitHub and,
# if main is ahead, asks Claude to tell the user how to update.
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

if ver_gt "$rv" "$lv"; then
  MSG="manual-maker: มีเวอร์ชันใหม่ v${REMOTE_VER} (ติดตั้งอยู่ v${LOCAL_VER}). แจ้ง user ว่าถ้าติดตั้งแบบ plugin ให้พิมพ์ใน Claude Code: /plugin marketplace update manual-maker-dev แล้ว restart; ถ้าเป็น personal skill ให้ re-copy: cp -r skills/manual-maker ~/.claude/skills/manual-maker"
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$MSG"
fi
exit 0
