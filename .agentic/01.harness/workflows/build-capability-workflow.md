<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.workflows.build-capability-workflow
version: 2
status: active
created_on: "2026-06-15"
updated_on: "2026-11-26"
layer: 01.harness
domain: governance
disciplines:
- agentic
kind: workflow
purpose: Govern how to choose and create the smallest safe artifact set for a new
  repeatable capability.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: shared.workflows.capability-resolution-workflow
  path: .agentic/shared/workflows/capability-resolution-workflow.md
- id: harness.standards.agentic-artifact-standards
  path: .agentic/01.harness/standards/agentic-artifact-standards.md
- id: harness.adr.0020-use-scripts-for-layer-command-surfaces
  path: docs/01.harness/adrs/0020-use-scripts-for-layer-command-surfaces.md
-->

# Build Capability Workflow

## Use When

Use this when a request needs a new repeatable capability, behaviour, process, automation, skill, workflow, standard, checklist, script, agent, orchestrator, or combination of these.

This workflow may create artifacts for any owning layer. Use the current
repository instructions and applicable routing policy rather than copying a
second layer list here.

## Goal

<!-- deterministic-check: allow reason="requires human/model judgment to choose the smallest safe artifact set" -->
Find an existing capability if one exists. If none exists, propose the smallest safe artifact set needed to satisfy the request.

Do not create files until the user explicitly grants edit permission in the current chat.

## Step 1: Resolve the Current Request

Use the session log for the recorded worktree, branch, authority and task
continuity. Resolve ownership and the applicable workflow from the current
request, repository instructions and available context router. Do not assign
the whole chat a durable layer, mode or workflow, or switch worktrees because
the current task crosses layers.

The target layer describes the capability being changed, not every earlier or
later task in this session. Stop at an unresolved ownership or authority gap.

Expected inputs:

- `task`: the current request and its recorded acceptance criteria
- `layer`: the actual owning layer or layers for this change
- `workflow`: this workflow path

Example:

```txt
Task: move package-check input derivation to its existing selector owner
Layer: shared
Workflow: .agentic/01.harness/workflows/build-capability-workflow.md
```

## Step 2: Check Existing Artifacts

Before proposing a new artifact, inspect only the relevant layer folders:

- `.agentic/<target-layer>/workflows/`
- `.agentic/<target-layer>/skills/`
- `.agentic/<target-layer>/standards/`
- `.agentic/<target-layer>/checklists/`
- `.agentic/<target-layer>/templates/`
- `.agentic/<target-layer>/examples/`
- `.agentic/<target-layer>/evals/`
- `.agentic/<target-layer>/hooks/`
- `.agentic/<target-layer>/agents/`
- the implemented script owners and their direct callers, using
  `docs/00.chat/script-layout.md` for navigation when deterministic code is
  needed; include existing `scripts/repo/` owners for repository machinery

Do not scan unrelated layers unless the task clearly crosses layers.

Do not create new scripts under `scripts/shared/`. Shared process work should
either use an existing layer-owned command surface or first record a governed
script namespace decision.

## Step 3: Choose Minimum Artifact Set

Use this decision table:

| Need | Artifact |
|---|---|
| deterministic action or validation | script |
| blocking safety or completion check | gate |
| repeated ordered process | workflow |
| reusable model procedure | skill |
| durable quality rule | standard |
| completion/safety criteria | checklist |
| lifecycle automation | hook |
| behavior regression protection | eval |
| reusable output/document shape | template |
| canonical few-shot sample | example |
| durable session state | session log |
| durable architecture decision | ADR |
| vendor-specific compatibility | adapter |
| bounded review or execution role | agent |
| coordination across multiple agents/workflows | orchestrator |

For detailed placement rules, use
`.agentic/01.harness/standards/agentic-artifact-standards.md`.

Prefer fewer artifacts.

Before adding a script or changing its role, owner, consumers or execution
lane, use the [script-admission standard](../standards/script-admission.md).
Record the real need, reused owner, primary role, proposed home, direct
consumers, named risk, execution effects, invalidating inputs and expected
cost in the existing task record. An approved future layout is not the current
execution path. Move a bounded owner and its callers through the existing
path-migration workflow; do not leave a compatibility copy without a real need.

Do not create an agent if a skill is enough.
Do not create a workflow if a script plus checklist is enough.
Do not create an orchestrator unless multiple independent workflows must be coordinated.
Do not create vendor-specific adapters unless the vendor format adds necessary metadata, scoping, or enforcement.

## Step 4: Safety Rules

- Scripts that delete, move, commit, push, clean, or overwrite anything must support dry-run mode first.
- Destructive actions require explicit user approval.
- Branch deletion must never affect the current branch.
- Commit log deletion must only happen when the matching branch is confirmed safe to remove.
- Dirty worktree handling must never auto-commit without explicit user approval.
- Do not reference files or scripts that do not exist unless creating them is part of the approved change.

## Step 5: Proposal Format

Before editing, record the bounded proposal. If the user already authorised
this scope, an intermediate update is sufficient; do not demand repeated
approval for routine steps. New scope, new external effects and new source
files above the admission standard's size limit still require prior approval.

```txt
Target layer: <actual owning layer or layers>
Capability name: <name>
Existing artifact found: yes|no
Recommended artifacts:
- <path> — <why>

Not creating:
- <artifact type> — <why not>

Safety gates:
- <gate>

Edit permission: <already granted for this scope | needed>
```

## Step 6: Prove the Actual Handoff

Use the existing registered check and its declared runner for final focused
proof. Follow [test execution](../../shared/testing/standards/test-execution.md)
and [change completion](../../shared/standards/require-change-completion.md)
for source review, affected consumers, matching-evidence reuse and later-stage
requirements. A helper move is not a reason to replay every package or deploy
check; preserve proof of its named risk and real consumer boundary.

Report what changed, what now selects the proof, actual effects and measured
cost, and what remains unproved. Selection never grants cloud, Git or other
external authority. Do not create another runner, registry or test gate merely
to enforce this prose workflow.
