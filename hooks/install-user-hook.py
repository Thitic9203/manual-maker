#!/usr/bin/env /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Register (or refresh) manual-maker's USER-SCOPE self-update SessionStart hook in
~/.claude/settings.json — the one piece that must live OUTSIDE the plugin so it keeps
running after the plugin is disabled (a disabled plugin's own hooks never fire).

Called by hooks/check-version.sh while the plugin is enabled. Kept a standalone script so
the settings.json surgery — the only genuinely risky edit this plugin makes — is unit-testable.

    install-user-hook.py --settings <path> --command <cmd> --marker <str>

Contract (blast-radius first — a user's settings.json breaks their whole Claude Code):
  * NEVER clobbers: only our own entry (identified by <marker> inside the command) is ever
    touched; every other key and hook is preserved byte-for-byte through a full json round-trip.
  * Refuses to guess: if settings.json exists but is not valid JSON, or has a hooks/SessionStart
    shape we don't recognise, it exits non-zero and writes NOTHING.
  * Idempotent: present and identical -> exit 0, no write. Present but the command changed
    (e.g. the script path moved) -> update in place.
  * Atomic + backed up: writes a temp file then os.replace()s it in; keeps a one-time
    settings.json.mm-bak of the original before the first modification.

Exit 0 = installed / refreshed / already-current (or opted out).
Exit 2 = could not act safely (unreadable/foreign shape) — caller treats this as fail-silent.
"""
import argparse
import json
import os
import sys


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--settings', required=True)
    p.add_argument('--command', required=True)
    p.add_argument('--marker', required=True)
    return p.parse_args()


def load_settings(path):
    """Return (obj, existed). Missing file -> ({}, False). Invalid JSON -> raise."""
    if not os.path.exists(path):
        return {}, False
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    if not text.strip():
        return {}, True
    return json.loads(text), True          # a JSONDecodeError here aborts the run (caller: fail-silent)


def ensure_session_start(settings):
    """Return the SessionStart list to mutate, or raise if the shape is foreign."""
    hooks = settings.setdefault('hooks', {})
    if not isinstance(hooks, dict):
        raise ValueError('hooks is not an object')
    ss = hooks.setdefault('SessionStart', [])
    if not isinstance(ss, list):
        raise ValueError('hooks.SessionStart is not a list')
    return ss


def find_ours(ss, marker):
    """Yield every command-hook dict whose command carries our marker."""
    for group in ss:
        if not isinstance(group, dict):
            continue
        for h in group.get('hooks', []) or []:
            if isinstance(h, dict) and marker in str(h.get('command', '')):
                yield h


def atomic_write(path, obj):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + '.mm-tmp.%d' % os.getpid()
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write('\n')
    os.replace(tmp, path)


def main():
    a = parse_args()
    try:
        settings, existed = load_settings(a.settings)
    except (ValueError, OSError):
        # unreadable or not JSON — do NOT overwrite a file we can't safely parse
        return 2

    try:
        ss = ensure_session_start(settings)
    except ValueError:
        return 2

    ours = list(find_ours(ss, a.marker))
    if ours:
        if all(h.get('command') == a.command for h in ours):
            return 0                        # already current — no write, no churn
        for h in ours:
            h['command'] = a.command        # path/command changed — refresh in place
    else:
        ss.append({'hooks': [{'type': 'command', 'command': a.command}]})

    # one-time backup of the original before our first modification
    if existed:
        bak = a.settings + '.mm-bak'
        if not os.path.exists(bak):
            try:
                with open(a.settings, encoding='utf-8') as src, open(bak, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            except OSError:
                pass

    try:
        atomic_write(a.settings, settings)
    except OSError:
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
