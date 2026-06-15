# Build Capability Workflow

## Use When

Use this when a request needs a new repeatable capability, behaviour, process, automation, skill, workflow, standard, checklist, script, agent, orchestrator, or combination of these.

This workflow may create artifacts for any target layer: `shared`, `harness`, or `product`.

## Goal

Find an existing capability if one exists. If none exists, propose the smallest safe artifact set needed to satisfy the request.

Do not create files until the user explicitly grants edit permission in the current chat.

## Step 1: Consume Session Context

Use the `layer`, `workflow`, and `task` already resolved by chat startup

Do not reclassify the layer unless the session metadata is missing, incomplete, or marked `unknown`.

Expected inputs:

- `task`: from the current chat/session log or pasted startup prompt
- `layer`: `shared`, `harness`, `product`, or `mixed`
- `workflow`: this workflow path

The selected `layer` is the target layer for the capability being built.

Example:

```txt
Task: update my harness so whenever I start a new chat, empty branches and commitLogs are cleaned up
Layer: shared
Workflow: .agentic/harness/workflows/build-capability.md

## Step 2: Check Existing Artifacts

Before proposing a new artifact, inspect only the relevant layer folders:

- `.agentic/<target-layer>/workflows/`
- `.agentic/<target-layer>/skills/`
- `.agentic/<target-layer>/standards/`
- `.agentic/<target-layer>/checklists/`
- `scripts/<target-layer>/`

Do not scan unrelated layers unless the task clearly crosses layers.

## Step 3: Choose Minimum Artifact Set

Use this decision table:

| Need | Artifact |
|---|---|
| deterministic action | script |
| repeated ordered process | workflow |
| reusable model procedure | skill |
| quality rule | standard |
| completion/safety criteria | checklist |
| bounded review or execution role | agent |
| coordination across multiple agents/workflows | orchestrator |

Prefer fewer artifacts.

Do not create an agent if a skill is enough.
Do not create a workflow if a script plus checklist is enough.
Do not create an orchestrator unless multiple independent workflows must be coordinated.

## Step 4: Safety Rules

- Scripts that delete, move, commit, push, clean, or overwrite anything must support dry-run mode first.
- Destructive actions require explicit user approval.
- Branch deletion must never affect the current branch.
- Commit log deletion must only happen when the matching branch is confirmed safe to remove.
- Dirty worktree handling must never auto-commit without explicit user approval.
- Do not reference files or scripts that do not exist unless creating them is part of the approved change.

## Step 5: Proposal Format

Before editing, output:

```txt
Target layer: <shared|harness|product|mixed>
Capability name: <name>
Existing artifact found: yes|no
Recommended artifacts:
- <path> — <why>

Not creating:
- <artifact type> — <why not>

Safety gates:
- <gate>

Edit permission needed: yes