---
description: Record an MP4 screen video of a web flow (screen-record). Thin shim — delegates to the screen-record plugin skill, which owns the whole workflow.
argument-hint: อัดวิดีโอ <ระบบ/ฟีเจอร์>  |  record a video of <flow>
---

<!-- managed-by: manual-maker-plugin — installed automatically so bare /screen-record resolves.
     Safe to delete; set MANUAL_MAKER_NO_SHIM=1 to stop it being reinstalled. Edits are
     overwritten on plugin update — delete the marker line above to take ownership and keep them. -->

# /screen-record — shim

Claude Code namespaces every plugin command as `/plugin:command`, so the `screen-record` skill in
the `manual-maker` plugin is only reachable as `/manual-maker:screen-record`. This user-level
command exists so the shorter `/screen-record` also works on this machine. It holds **no workflow
logic of its own** — all behavior lives in the plugin skill, so it never drifts from it.

## Do this

Invoke the **`manual-maker:screen-record`** skill with the Skill tool, passing the user's request
verbatim as the args:

> $ARGUMENTS

Then follow that skill's workflow exactly, to completion — including its preflight, its intake
(environment, URL, account, and the source that says what to record), its mandatory confirmation
gate, and its 7-layer quality gate before any file is called done.

If the args are empty, still invoke the skill and let its intake ask what to record.

## If the skill is not available

The plugin is missing or disabled on this machine. Do not improvise a recorder. Report this and give
the user the recovery steps:

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
