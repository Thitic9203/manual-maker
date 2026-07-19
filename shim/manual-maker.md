---
description: Build a user handbook end to end (manual-maker). Thin shim — delegates to the manual-maker plugin skill, which owns the whole workflow.
argument-hint: ทำคู่มือ <ชื่อระบบ>  |  create a manual for <system>
---

# /manual-maker — shim

Claude Code namespaces every plugin command as `/plugin:command`, so the `manual-maker`
plugin is only reachable as `/manual-maker:manual-maker`. This user-level command exists so the
shorter `/manual-maker` also works on this machine. It holds **no workflow logic of its own** —
all behavior lives in the plugin, so it never drifts from it.

## Do this

Invoke the **`manual-maker:manual-maker`** skill with the Skill tool, passing the user's request
verbatim as the args:

> $ARGUMENTS

Then follow that skill's workflow exactly, to completion — including its intake, its mandatory
confirmation gate, and its publish confirmation. Do not summarize or re-plan the workflow here.

If the args are empty, still invoke the skill and let its intake ask for the system.

## If the skill is not available

The plugin is missing or disabled on this machine. Do not improvise a manual. Report this and
give the user the recovery steps:

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
