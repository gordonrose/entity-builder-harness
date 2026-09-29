<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.standard.autonomous-delivery-envelope.v1
version: 1
status: active
layer: 01.harness
domain: delivery.autonomy
disciplines: [agentic, architecture, sre]
kind: standard
purpose: Define when an authorised implementation programme continues autonomously and the narrow conditions that require a user boundary.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: harness.workflow.sustained-implementation
  path: .agentic/01.harness/workflows/sustained-implementation.md
-->
# Autonomous delivery envelope v1

## Modes

`read-only` permits inspection only. `source-batch` permits repository plans,
contracts, source, tests, local checks, ordinary repair, and previously
authorised commit/rebase checkpoints. `approved-target-operation` additionally
permits only the explicitly approved external operation.

## Source-batch rule

A delivery unit is complete only when its contract, implementation, focused
tests, documentation, verification, session record, and next queued unit are
present. A small edit, test, rebase, formatting check, or routine local failure
is not a completion or stop condition.

Continue autonomously through ordinary implementation and repair. Stop only
for an unapproved external mutation, destructive/irreversible action,
security/privacy exposure, irreducible business-policy choice, or unresolvable
worktree ownership conflict. Record the exact stop reason; do not call routine
ambiguity a blocker.

## Required session declaration

```yaml
execution_mode: source-batch
delivery_unit: contract-implementation-tests-docs-verification
next_unit_required: true
stop_only_for: [external-mutation, destructive-action, security-exposure, policy-choice, ownership-conflict]
```

## Closeout check

Do not close a source-batch session while approved work remains without a
completed delivery unit, an explicit next unit, or one of the declared stop
conditions.
