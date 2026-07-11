---
name: manual-maker
description: Use when creating a user handbook or manual for a web system/app that end users read and follow. Runs a structured intake to gather system-specific details (system name, login, target users, modules, output format), optionally auto-captures UI screenshots with Playwright/Chrome, delegates the actual writing to the doc-coauthoring skill, applies the team's handbook template, and exports to Confluence, PDF, docx, or a web page. Triggers on "write a manual", "create a handbook", "user guide for <system>", "ทำคู่มือการใช้งาน", "คู่มือผู้ใช้".
---

# Manual Maker

## Overview

Manual Maker turns a working web system into a finished **user handbook** — the kind an end user reads and follows step by step.

It does **not** re-implement document writing. It is a thin team wrapper that:

1. **Asks the right system-specific questions first** (intake) so every manual starts from complete, consistent inputs.
2. **Optionally captures screenshots** of the real UI with the Playwright / Chrome MCP.
3. **Delegates the drafting to the official `doc-coauthoring` skill** — you get Anthropic's document-writing engine, plus this team's conventions on top.
4. **Applies the team handbook template** so every manual has the same structure and tone.
5. **Exports / publishes** to the team's channel: Confluence, PDF, docx, or a web page.

## When to Use

Use when the user wants to produce a manual/handbook/user guide for a web system or app, e.g.:
- "ทำคู่มือการใช้งานระบบ X ให้ผู้ใช้"
- "create a user manual for the admin dashboard"
- "write a step-by-step guide for how staff use the booking system"

Do **not** use for API reference docs, code documentation, or internal design docs — those are different deliverables.

## Workflow

Track the run with TodoWrite: `Intake → (Screenshots) → Draft → Template → Export`.

### Step 1 — Intake (always first)

Read `references/intake.md`. Ask the intake questions **one at a time**, each with a recommended default, and let the user answer or accept the default. Do not skip.

At the end, echo back a compact **intake summary table** and get a "go" before writing anything.

**Security:** never store real credentials, tokens, or secrets in the manual or the repo. When login steps are needed, describe the *procedure* ("log in with your SSO account"), not actual usernames/passwords.

### Step 2 — Screenshots (optional)

If the user opted into auto-screenshots:
- Use the Playwright MCP (`mcp__playwright__*`) or Chrome MCP to drive the system.
- Capture one screenshot per meaningful UI state / step.
- Save to a `assets/` folder next to the draft, name them by section+step (e.g. `02-login-01.png`).
- Only navigate URLs the user gave in intake. Do not follow arbitrary links.

If screenshots are provided manually, collect the file paths instead.

### Step 3 — Draft (delegate to doc-coauthoring)

Invoke the **`doc-coauthoring` skill** via the Skill tool. Pass it as context:
- the intake summary,
- the team template from `references/template.md`,
- the screenshot list (if any).

Instruct doc-coauthoring to draft the handbook **section by section**, following the template's structure, in the language chosen at intake (default Thai), using short, task-focused steps a non-technical user can follow.

Let doc-coauthoring own the actual prose, iteration, and refinement — that is its job. This skill's job is inputs, structure, and output.

### Step 4 — Apply team template & conventions

Ensure the draft matches `references/template.md`:
- required sections present and in order,
- numbered step-by-step instructions,
- a screenshot after each action step (where available),
- consistent terminology (one term per concept),
- plain, polite language for the target audience.

### Step 5 — Export / publish

Per the format chosen at intake:

| Format | How |
|--------|-----|
| **Confluence** | Use the Atlassian MCP (`createConfluencePage` / `updateConfluencePage`) to publish under the space + parent page from intake. Confirm space key before posting. |
| **PDF** | Use the `pdf` skill to export the final Markdown to PDF. |
| **docx** | Use the `docx` skill to export to Word. |
| **Web page** | Use the `web-artifacts-builder` skill to build an interactive page. |

Publishing to Confluence is an outward action — show the target space/page and get confirmation before the first publish.

## Composition Note

This skill **composes** the official first-party skills (`doc-coauthoring`, `docx`, `pdf`, `web-artifacts-builder`) via the Skill tool — it does not copy their content. That keeps this repo free of third-party content and lets it benefit from upstream updates.

## Safety

- No secrets in output or repo — describe login procedures, never real credentials.
- Screenshots: navigate only user-provided URLs; never arbitrary or emailed links.
- Confluence/web publish is outward-facing — confirm target before posting.
- All tooling used here is first-party / already installed — no paid services.
