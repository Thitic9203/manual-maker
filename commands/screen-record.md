---
description: Record an MP4 screen video of a web flow end to end — intake (environment, URL, account, source) → confirm → preflight → record headlessly at 1920×1080 H.264 → verify against the 7-layer quality gate → deliver.
argument-hint: อัดวิดีโอ <ระบบ/ฟีเจอร์>  |  record a video of <flow>
---

# /screen-record — record a web flow as a finished MP4

The user invoked this command to get **video** of a live web system. Their request:

> $ARGUMENTS

## Your job

Own this from intake to a verified file on disk. **Load the `screen-record` skill using the Skill
tool** — invoke it by name, do not depend on a filesystem path. Once loaded, the skill pulls in its
own references (`references/intake.md`, `references/video-spec.md`, `references/quality-gate.md`);
follow its workflow verbatim.

Run **every** step of that workflow in order and **auto-continue between them** — do not stop to ask
"shall I move to the next step?". Pause only at the gates the skill marks as mandatory, and report
progress as each clip finishes so a long batch never looks like a hung one.

## The gates that are not yours to skip

- **Environment is the user's choice.** Never pick dev / staging / pre-prod / production for them.
- **The Confirmation Gate.** When the intake data is complete, summarize everything in chat —
  including the numbered list of what will be recorded — and get an explicit confirmation. Complete
  data is not permission to start.
- **Source-driven steps.** What gets recorded comes from the source the user named (manual file,
  test-case list, spec) or a step list they confirmed. Never invent a step, never drop one.
- **The 7-layer quality gate.** Nothing is "done" until every clip passes. **ตรวจไม่ได้ = ไม่ผ่าน.**
  A run that stopped before its target is **blocked with a reason**, never a shorter deliverable.

If the args are empty, still load the skill and let its intake ask what to record.

## If the skill is not available

The plugin is missing or disabled on this machine. Do not improvise a recorder. Report it and give
the recovery steps:

```
claude plugin list | grep -A3 'manual-maker@'
claude plugin enable manual-maker@manual-maker-dev
claude plugin update manual-maker@manual-maker-dev
```

Then restart Claude Code (or `/reload-plugins`). If it was never installed:

```
claude plugin marketplace add Thitic9203/manual-maker
claude plugin install manual-maker@manual-maker-dev
```
