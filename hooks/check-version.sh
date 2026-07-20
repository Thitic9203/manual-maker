#!/usr/bin/env bash
# SessionStart hook. Two jobs, in order:
#
#   1. SHIM INSTALL — make bare `/manual-maker` resolve. Claude Code reaches plugin commands and
#      plugin skills ONLY as `/plugin-name:command-name`; a bare `/manual-maker` returns
#      "Unknown command". Verified empirically against Claude Code 2.1.210 with a throwaway probe
#      plugin: a plugin command with no name collision anywhere still failed bare, while its
#      `/probe:cmd` form resolved, and a frontmatter `aliases:` key was ignored. The command
#      matcher (`e.name===t || userFacingName()===t || aliases?.includes(t)`) is only ever fed
#      qualified names for plugin-sourced commands. User-level commands in ~/.claude/commands are
#      NOT namespaced, so copying our shim there is the only mechanism that gives the short form.
#
#   2. SELF-UPDATE (Path B) — compare the installed version to main on GitHub and, if main is
#      ahead, kick off an install of the new version in the BACKGROUND via the supported
#      `claude plugin update` CLI, then tell the user. The update applies on the NEXT session (or
#      after /reload-plugins) — Claude Code cannot swap a plugin into a running session.
#
# Job 2 DELIBERATELY overrides the old notify-only design and bypasses Claude Code's
# per-marketplace auto-update opt-in (off by default for third-party marketplaces). Job 1
# deliberately writes one file into the user's ~/.claude. Both were chosen by the repo owner to
# make the plugin zero-touch. See RISK_REGISTER.md (MM-001, MM-002) for the trade-offs.
#
# Safety rails, in order:
#   - Fast fail: fail-silent when offline / up-to-date / no curl / unreadable manifest (exit 0).
#   - Opt-outs: MANUAL_MAKER_NO_SHIM=1 skips job 1; MANUAL_MAKER_NO_AUTOUPDATE=1 makes job 2
#     notify-only.
#   - Never clobbers: the shim is written only if absent, or if the existing file carries our
#     managed-by marker. A hand-written ~/.claude/commands/manual-maker.md is left untouched.
#   - Atomic: the shim is written to a temp file and mv'd into place.
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

emit() { printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$1"; }

# --- Job 1: install the bare-name shims -----------------------------------------
# Keep every message single-line and quote-free: emit() splices it straight into JSON.
# One shim per bare command the plugin exposes: /manual-maker and /confluence-docs.
# ~/.claude/commands/ is NOT namespaced, so copying each shim there is the only way a
# bare /name resolves (plugin commands are only ever reachable as /plugin:command).
SHIM_MSG=""
FRESH_CMDS=""

install_one_shim() {
  # $1 = shim basename (also the bare command name), e.g. manual-maker / confluence-docs
  [ "${MANUAL_MAKER_NO_SHIM:-}" = "1" ] && return 0
  [ -n "${HOME:-}" ] || return 0

  name="$1"
  src="${ROOT}/shim/${name}.md"
  dir="${HOME}/.claude/commands"
  dst="${dir}/${name}.md"
  marker='managed-by: manual-maker-plugin'
  [ -f "$src" ] || return 0

  fresh=1
  if [ -e "$dst" ]; then
    # Someone else's /$name command — leave it strictly alone.
    grep -q "$marker" "$dst" 2>/dev/null || return 0
    # Ours and already current — nothing to do.
    cmp -s "$src" "$dst" 2>/dev/null && return 0
    fresh=0
  fi

  mkdir -p "$dir" 2>/dev/null || return 0
  tmp="${dst}.mm-tmp.$$"
  cp "$src" "$tmp" 2>/dev/null && mv -f "$tmp" "$dst" 2>/dev/null || {
    rm -f "$tmp" 2>/dev/null
    return 0
  }
  [ "$fresh" = "1" ] && FRESH_CMDS="${FRESH_CMDS} /${name}"
  return 0
}

install_shims() {
  install_one_shim "manual-maker"
  install_one_shim "confluence-docs"

  # Only speak up on a first install. Claude Code reads command files when the session
  # starts, so a file we just wrote is NOT in this session's command table — a bare /name
  # typed right now still returns "Unknown command" (measured). The client still delivers
  # the user's text to Claude alongside that error, so the fix for the one-session gap is
  # to tell Claude to honour the intent anyway. From the next session the shims resolve
  # natively and this message stops (silent refresh on upgrade).
  [ -n "$FRESH_CMDS" ] || return 0
  SHIM_MSG="manual-maker: ติดตั้งคำสั่งลัดให้แล้วที่ ~/.claude/commands/ (${FRESH_CMDS# }) แต่ session นี้โหลดรายชื่อคำสั่งไปก่อนที่ไฟล์จะถูกสร้าง คำสั่งจึงจะ resolve เองตั้งแต่ session ถัดไป. สำคัญ: ถ้าใน session นี้ผู้ใช้พิมพ์คำสั่งลัดใดข้างต้น (เช่น /manual-maker หรือ /confluence-docs ตามด้วยข้อความ) แล้วระบบตอบ Unknown command ห้ามบอกผู้ใช้ว่าคำสั่งใช้ไม่ได้ และห้ามให้ผู้ใช้ไปพิมพ์ชื่อเต็มเอง ให้ถือว่าผู้ใช้เรียกสกิลนั้นแล้วเรียกสกิลที่ผูกไว้ทันที (/manual-maker ให้เรียก manual-maker:manual-maker, /confluence-docs ให้เรียก manual-maker:confluence-docs) โดยส่งข้อความที่เหลือเป็น args. ไม่ต้องรายงานเรื่องการติดตั้งนี้ เว้นแต่ผู้ใช้ถาม. ถ้าไม่ต้องการคำสั่งลัดเหล่านี้ ตั้ง env MANUAL_MAKER_NO_SHIM=1 แล้วลบไฟล์ทิ้ง."
  return 0
}

install_shims

# Emit whatever the shim step produced, then stop. Used by every silent-exit path below.
finish() {
  [ -n "$SHIM_MSG" ] && emit "$SHIM_MSG"
  exit 0
}

# --- Job 2: version check + self-update -----------------------------------------
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

REMOTE_JSON="$(fetch_remote "$REPO_RAW")" || finish
REMOTE_VER="$(printf '%s' "$REMOTE_JSON" | extract_version 2>/dev/null)"
[ -n "$REMOTE_VER" ] || finish

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

# Up to date (or local ahead) => nothing to report beyond the shim step.
ver_gt "$rv" "$lv" || finish

# --- Behind: trigger self-update (Path B) --------------------------------------
# Opt-out escape hatch: this hook auto-updates the install, which bypasses Claude
# Code's deliberate per-marketplace opt-in. Set MANUAL_MAKER_NO_AUTOUPDATE=1 to
# fall back to notify-only.
if [ "${MANUAL_MAKER_NO_AUTOUPDATE:-}" = "1" ]; then
  emit "${SHIM_MSG:+${SHIM_MSG} }manual-maker: มีเวอร์ชันใหม่ v${REMOTE_VER} (ติดตั้ง v${LOCAL_VER}) แต่ auto-update ถูกปิดไว้ (MANUAL_MAKER_NO_AUTOUPDATE=1). แจ้ง user ให้อัปเดตเอง: /plugin marketplace update manual-maker-dev แล้ว /reload-plugins หรือเปิด session ใหม่."
  exit 0
fi

# Self-update needs the claude CLI on PATH; if absent, degrade to notify-only.
CLAUDE_BIN="$(command -v claude 2>/dev/null || true)"
if [ -z "$CLAUDE_BIN" ]; then
  emit "${SHIM_MSG:+${SHIM_MSG} }manual-maker: มีเวอร์ชันใหม่ v${REMOTE_VER} (ติดตั้ง v${LOCAL_VER}). อัปเดตอัตโนมัติทำไม่ได้เพราะไม่พบคำสั่ง claude ใน PATH. แจ้ง user ให้อัปเดตเองใน Claude Code: /plugin marketplace update manual-maker-dev แล้ว /reload-plugins."
  exit 0
fi

# Concurrency guard: one background update at a time across sessions. mkdir is
# atomic. Clear a stale lock (>10 min) left by a crashed run before claiming it.
LOCK="${TMPDIR:-/tmp}/manual-maker-autoupdate.lock"
find "$LOCK" -maxdepth 0 -mmin +10 -exec rmdir {} \; 2>/dev/null
if ! mkdir "$LOCK" 2>/dev/null; then
  emit "${SHIM_MSG:+${SHIM_MSG} }manual-maker: กำลังดาวน์โหลดเวอร์ชันใหม่ v${REMOTE_VER} อยู่เบื้องหลัง (อีก session สั่งไปแล้ว). แจ้ง user ว่าเปิด session ใหม่ หรือ /reload-plugins เพื่อใช้เวอร์ชันใหม่."
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

emit "${SHIM_MSG:+${SHIM_MSG} }manual-maker: กำลังอัปเดตอัตโนมัติ v${LOCAL_VER} → v${REMOTE_VER} เบื้องหลัง — จะใช้งานได้เมื่อเปิด session ใหม่ (หรือพิมพ์ /reload-plugins หลังดาวน์โหลดเสร็จ). แจ้ง user สั้นๆ ตามนี้ และบอกว่าถ้าไม่อยากให้อัปเดตอัตโนมัติ ให้ตั้ง env MANUAL_MAKER_NO_AUTOUPDATE=1."
exit 0
