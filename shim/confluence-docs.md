---
description: Replace mock content in a Confluence doc-space with real data (confluence-docs). Thin shim — delegates to the confluence-docs plugin skill, which owns the whole workflow.
argument-hint: อัปเดต confluence <doc-type>  |  populate the doc space
---

<!-- managed-by: manual-maker-plugin — installed automatically so bare /confluence-docs resolves.
     Safe to delete; set MANUAL_MAKER_NO_SHIM=1 to stop it being reinstalled. Edits are
     overwritten on plugin update — delete the marker line above to take ownership and keep them. -->

# /confluence-docs — shim

Claude Code namespaces every plugin command as `/plugin:command`, so the `confluence-docs`
skill in the `manual-maker` plugin is only reachable as `/manual-maker:confluence-docs`. This
user-level command exists so the shorter `/confluence-docs` also works on this machine. It holds
**no workflow logic of its own** — all behavior lives in the plugin skill, so it never drifts from it.

## Do this

Invoke the **`manual-maker:confluence-docs`** skill with the Skill tool, passing the user's request
verbatim as the args:

> $ARGUMENTS

Then follow that skill's workflow exactly, to completion — including its write-capability preflight,
its intake, its mandatory confirmation gate, and its 5-layer review before any publish. Do not
summarize or re-plan the workflow here.

If the args are empty, still invoke the skill and let its intake ask what to work on.

## If the skill is not available

The plugin is missing or disabled on this machine. Do not improvise Confluence edits. Report this and
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
