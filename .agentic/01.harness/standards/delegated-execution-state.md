<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.standards.delegated-execution-state
version: 1
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-20"
layer: 01.harness
domain: delegation
disciplines:
- agentic
- sre
kind: standard
purpose: Define truthful state reporting and completion criteria for a bounded delegated execution packet.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.plan.execution.kanbien-core-platform-bootstrap
  path: .agentic/04.deploy/plans/execution/kanbien-core-platform-bootstrap.md
- id: harness.workflow.operational-realization-gate
  path: .agentic/01.harness/workflows/operational-realization-gate.md
-->
# Delegated Execution State

Every delegated execution packet names its completion criterion, gates, stop
conditions, and evidence locations. A worker may report only one of these
states: `not-started`, `running`, `waiting-on-external-system`,
`phase-complete`, `blocked`, or `complete`.

`complete` is permitted only when the packet's stated completion criterion has
been met. Completing a substep, dispatching an asynchronous workflow, or
waiting for provider propagation is not completion.

Every non-complete report names completed gates, current gate, next permitted
action, evidence reference, and blocking condition where applicable. A worker
must not silently stop while an approved packet remains runnable.
