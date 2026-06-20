<!-- agentic-artifact:
owner: harness
kind: standard
purpose: Define the missing-governance stop-condition policy that prevents improvised recovery.
domain: governance
portability: llm-workbench-required
used_by:
  - AGENTS.md
  - .agentic/01.harness/workflows/change-harness.md
  - .agentic/shared/workflows/capability-resolution-workflow.md
-->

# Missing Governance Stop Condition

## Purpose

Use this standard when an agent encounters a necessary action, recovery path,
workaround, or substitution that is not covered by the current workflow, gate,
script, or standard.

The goal is to make harness gaps visible at the moment they matter, so the
harness can be updated deliberately instead of relying on improvised agent
judgment.

## Core Rule

Missing governance is a stop condition.

Agents must not use ordinary engineering judgment as a substitute for missing
harness governance. If the current workflow, gate, script, or standard does not
govern a required action, stop before acting.

## What Counts As Missing Governance

Governance is missing when the agent needs to do something material to continue
the task, but no currently loaded or referenced harness artifact owns that move.

Examples include:

- choosing an unlisted recovery path after a command, gate, or workflow step
  fails
- using a workaround because the documented path is blocked
- substituting one tool, script, workflow, artifact, or command for another
- resolving a conflict or generated artifact problem through an unnamed process
- changing branch, filesystem, runtime, dependency, deployment, database, or
  data state through an ungoverned path
- bypassing a required gate because it appears inconvenient, broken, stale, or
  incomplete

## What Does Not Count

This standard does not block normal execution of documented steps.

It is acceptable to continue when:

- the current workflow names the recovery path
- a script or gate defines the action and failure behavior
- the relevant standard explicitly permits the substitution or exception
- the user has approved an action that is already governed by the current
  workflow's permission rules
- the next step is read-only inspection to understand and report the gap

User approval alone does not create governance for a new class of action. If
the harness does not govern the action, the agent should ask whether to update
the harness or proceed as a one-off exception, and record the decision.

## Required Stop Response

<!-- deterministic-check: allow reason="requires human judgment to identify governance gaps and name the missing owner" -->
When stopping for missing governance, answer with:

```txt
Blocked: required action is not governed.
Action needed: <action>
Blocking condition: <condition>
Missing governance: <workflow, gate, script, or standard gap>
Confirm update the harness or approve a one-off exception?
```

Keep the response specific. Name the artifact that appears to own the area and
the exact gap that prevents safe continuation.

## Examples

### Branch Refresh

<!-- deterministic-check: allow reason="examples illustrate human-governed stop conditions rather than defining a deterministic branch gate" -->
If a branch refresh encounters dirty work, merge conflicts, generated summary
changes, or state preservation needs that the current workflow does not cover,
stop. Do not invent stash, reset, checkout, restore, regeneration, or conflict
resolution behavior.

### Generated Files

If a generated file blocks progress and the workflow does not name the
regeneration command and review path, stop. Do not infer that regeneration is
safe from file names or prior experience.

### Dependency Or Tool Substitution

If an expected tool is unavailable and the workflow does not allow a
substitute, stop. Do not install dependencies, switch tools, or rewrite the
approach without governed permission.

### Deployment, Migration, Or Data Repair

If deployment, migration, runtime, database, or data state needs repair and the
current workflow does not define the recovery path, stop. Do not perform
manual fixes, backfills, rollbacks, or retries through an ungoverned path.

## Updating The Harness

When a gap is confirmed, add the smallest artifact that can govern future
occurrences:

- workflow section for ordered recovery steps
- script for deterministic action or validation
- gate for a blocking check
- standard for durable judgment rules
- checklist for reviewable completion criteria
- ADR for durable process tradeoffs

Do not add a hook first unless the trigger is deterministic and lifecycle-bound.
Unexpectedness itself is not a hook trigger.

## One-Off Exceptions

A one-off exception may be approved by the user when updating the harness would
be disproportionate or premature.

Record the exception in the session log with:

- the action approved
- why existing governance did not cover it
- why a one-off exception was accepted
- whether follow-up harness work is needed

Do not treat a one-off exception as precedent for future chats.
