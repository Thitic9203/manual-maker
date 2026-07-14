# Saved Intake Profile — remember a user's answers, don't re-ask

Goal: if this user has already documented a system, **do not make them retype the same
intake answers**. Load what they gave last time, show it back, and ask only for what is
**missing** or **changed**. This never weakens a gate — it only removes redundant typing.

## Where it lives (per-user local)

```
~/.manual-maker/profiles/<slug>.json
```

- **Per-user, per-machine.** Not committed to any repo, not shared with a team.
- `<slug>` is a short lowercase ASCII id you derive from the system name (e.g. "MICA2 EvMS"
  → `mica2-evms`). The human-readable name is also stored *inside* the file, so matching does
  not depend on guessing the slug (see Load).
- Create `~/.manual-maker/profiles/` if it does not exist (`mkdir -p`) before writing.

## What is stored — and what is NEVER stored

**Store (stable preferences, safe to remember):**

```json
{
  "schema_version": 1,
  "system": "MICA2 EvMS",
  "urls": ["https://evms.example.com"],
  "vpn_required": true,
  "step_sources": ["https://confluence.example.com/pages/12345", "spec.pdf"],
  "reference_doc": "handbook-template.docx",
  "audience": "non-technical end users",
  "scope": ["Login", "Create evaluation", "Reports"],
  "depth": "step-by-step for core tasks",
  "screenshots": { "capture": "auto", "annotation": "red box + numbered marker" },
  "font": "follow reference doc (TH Sarabun, 16pt body / 20pt heading)",
  "numbering": "decimal outline 1 / 1.1 / 1.1.1",
  "locked_terms": [ { "use": "ผู้เรียน", "never": ["นักเรียน", "นร."] } ],
  "language": "th",
  "output": { "format": "confluence", "space": "MICA", "parent": "MICA2 Handbooks" },
  "updated": "2026-07-14"
}
```

**NEVER store (credentials & secrets — safety rule, non-negotiable):**

- passwords, usernames used to log in, tokens, API keys, cookies, session data
- VPN credentials (store only the boolean `vpn_required`, never the secret)
- **credentials embedded in a URL** — HTTP basic-auth (`https://user:pass@host`) or secret query
  params (`?token=`, `?access_token=`, `?apikey=`, `?sig=`). Before storing any `urls` or
  `step_sources` value, **strip these** — keep only the bare `scheme://host/path`.

If a field would leak a secret, drop it. Credentials are asked **fresh, in-session, every run**
— exactly as before. For `updated`, write today's date as a plain `YYYY-MM-DD` literal; do not
compute a timestamp.

## Load — at the very start of intake (after the system name is known)

1. Learn the **system name** (intake Q1) — or take it from the `/manual-maker` argument.
2. List `~/.manual-maker/profiles/`, **read each profile's JSON**, and find the one whose stored
   `system` (or a `urls` entry) matches what the user named — match on the file's **contents**,
   not the filename/slug, so a slightly different slug still hits. **If more than one profile
   matches, show the candidates and ask which one** (do not guess). Remember which file you
   loaded — the Save step overwrites that same file.
3. **If a profile is found:** print it as a summary table and ask, verbatim:
   **"พบข้อมูลเดิมของระบบนี้ที่เคยบันทึกไว้ ยังใช้ได้เหมือนเดิมหรือไม่ หรือมีส่วนใดเปลี่ยนแปลง"**
   - For every field the user confirms is unchanged → **skip that intake question entirely.**
   - Ask intake questions **only** for fields that are missing from the profile or that the
     user says have changed.
   - **Always still ask fresh, regardless of the profile:**
     - **Credentials** (Q3) — never stored; ask at screenshot time, in-session.
     - **URL(s)** and **VPN state** (Q2, Q4) — show the saved value as the default and ask the
       user to **confirm it still holds** (do not silently reuse; live access must be verified).
4. **If no profile is found:** run the full intake as normal.

## Save — right after the Confirmation Gate passes

Once the user gives the explicit "go" at the Confirmation Gate (data is locked and confirmed):

1. Ensure `~/.manual-maker/profiles/` exists.
2. **If a profile was loaded this run, overwrite that same file.** Derive a fresh `<slug>` from
   the system name **only** when creating a brand-new profile. Write the confirmed values
   **minus every credential/secret**, setting `updated` to today's date. Never write a second
   file for a system that already has one — that spawns duplicate, ambiguous profiles.
3. Tell the user briefly: **"บันทึกข้อมูลระบบนี้ไว้แล้ว ครั้งถัดไปไม่ต้องกรอกใหม่ (ยกเว้นรหัสผ่านที่ต้องใส่สดทุกครั้ง)"**

Saving happens **after** confirmation, never before — a profile only ever holds user-confirmed
data, never a guess.
