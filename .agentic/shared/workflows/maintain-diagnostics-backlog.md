<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.workflow.maintain-diagnostics-backlog
version: 1
status: active
created_on: "2026-11-01"
updated_on: "2026-11-04"
layer: 06.shared
domain: diagnostics
disciplines: [architecture, security, sre, agentic]
kind: workflow
purpose: Maintain agreed future diagnostic tasks without losing their context or completion criteria.
portability: {class: source-only, targets: []}
used_by:
- id: shared.workflow.verify-diagnostic-coverage
  path: .agentic/shared/workflows/verify-diagnostic-coverage.md
- id: shared.plan.diagnostics-backlog
  path: .agentic/shared/plans/implementation/diagnostics-backlog.md
-->
# Maintain diagnostics backlog

## Use when

Use when the user asks to add, amend, review or "update diagnostics backlog".
During an agreed diagnostic review, also record confirmed fixes, changes,
additions or removals as they are discovered within that review's scope.
Always use the [canonical Diagnostics backlog](../plans/implementation/diagnostics-backlog.md)
and [entry template](../templates/diagnostics-backlog-entry.md), including in a
later chat. This is future-work planning, not implementation authorization or a
second active predicate inventory, runtime catalog or diagnostic review ledger.

## Inputs and boundaries

Use the user's requested task or update, or a confirmed finding from the agreed
review, its discovery evidence, and the current backlog. Inspect repo paths before
claiming which files need work. Read the current session record and follow
[shared-process governance](change-shared-process.md); verify the recorded chat
worktree with `scripts/00.chat/worktree/check-write-location/script.sh` before
writing. Preserve existing changes and obtain task write authority as required
by the chat workflow.

Do not import historic gaps or unrelated deferred migrations, invent tasks or
guessed defects, start fixes, create a goal or reopen a completed goal.
A later implementation request follows the
owning workflow and [diagnostic coverage review](verify-diagnostic-coverage.md).
This prose workflow guides review; it adds no mechanical enforcement or CI gate.

## Record or update

1. Read all existing entries, including completed and cancelled ones. Search for
   matching IDs, summaries, affected paths and discovery context before adding.
   Update the matching task rather than duplicating it. If the intended task or
   ownership is ambiguous, pause that update and ask for the missing distinction.
2. For a new task, append the next unused numeric ID, starting at `DIAG-001` and
   increasing from the highest ID ever assigned. Keep at least three digits;
   never reuse, renumber or delete an ID. Remove the empty-state sentence only
   when adding the first real task. Retain closed entries so identity and history
   remain available. If duplicates already exist, retain both IDs and record the
   relationship and requested disposition rather than silently merging history.
3. Record the actual date/time the entry is raised in ISO 8601 with an explicit
   UTC offset and timezone, such as `2026-11-01T12:00:00+00:00 (UTC)`; the example
   is format guidance, not a timestamp to copy. Read the clock when recording a
   new task. Keep this raised timestamp immutable. Describe earlier discovery
   separately; use a supported timestamp or say it was not recorded. Never infer
   a discovery time from a file date, current time or recollection.
4. Fill all six labelled sections from the template. Background must be plain
   prose explaining how the issue was found and with whom: for example the user
   and assistant during a particular review. Identify the actual participants
   only as supported by the conversation. Distinguish observations, decisions
   and uncertainty; include safe evidence references where useful.
5. Write user stories naming the repo part and files that need change, what
   should change and why it matters. Identify the owning layer or package and
   affected producers, wrappers and consumers. Record compatibility and privacy
   requirements, and name unresolved decisions instead of inventing them.
6. Give code, harness and regression fixtures their own observable acceptance
   criteria. For each, specify the result a reviewer can verify, or an explicit
   not-applicable decision with a reason. Harness criteria should address the
   workflow/rule/check omission that allowed the issue. Fixture criteria should
   describe a counterexample that would catch its recurrence. Name existing
   proof commands or tests when known; mark proposed proof as planned.
7. Edit only the requested entry and necessary backlog metadata or empty state.
   Preserve previous decisions, scope and evidence. Add dated update notes with
   explicit offsets/timezones for changed status, scope or decisions; explain
   corrections without rewriting the original discovery or raised timestamp.
   Keep statuses `open`, `planned`, `in-progress`, `blocked`, `done` or `cancelled`.
   Status describes this task; it does not grant implementation authority.

## Review and completion

Review the entry against the user's request: all six sections, clear ownership,
affected files, compatibility/privacy boundaries, and separate code, harness
and fixture outcomes must be present. Do not turn a backlog request into a new
implementation project merely to fill gaps; record genuine unknowns explicitly.

Only mark an entry `done` when its applicable acceptance criteria have evidence,
following [change-completion principles](../standards/require-change-completion.md).
Link implementation and actual check outcomes; distinguish local tests,
container qualification and live proof when relevant. Planned checks and prose
are not completion evidence. A cancellation records the user's decision and
reason without implying successful implementation.

For a documentation-only update, run the existing artifact header checker with
`--paths` limited to changed documents, check their relative links and required
entry structure, and run scoped `git diff --check`. Do not launch runtime,
container or dormant RAG checks solely for backlog prose. If executable behavior
is later changed, its owning workflow determines proportionate proof.

Report the canonical path, IDs added or updated, substantive decisions and check
results. Missing ownership, contradictory history or missing evidence blocks
only the affected update or `done` claim; preserve the existing record and state
the precise question or missing proof. Refresh metadata version/date according
to the existing artifact standard when its guidance or entries change.
