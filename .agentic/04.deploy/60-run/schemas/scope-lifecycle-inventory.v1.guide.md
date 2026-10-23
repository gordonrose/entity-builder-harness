<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.scope-lifecycle-inventory.v1.guide
version: 1
status: active
created_on: "2026-10-23"
updated_on: "2026-10-23"
layer: 04.deploy
domain: deployment.scope-lifecycle
disciplines: [agentic, security, sre]
kind: guide
purpose: Explain how target scope indexes declare lifecycle, workload ownership, succession, and reversion boundaries.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.schema.scope-lifecycle-inventory.v1
  path: .agentic/04.deploy/60-run/schemas/scope-lifecycle-inventory.v1.schema.yml
-->
# Scope Lifecycle Inventory v1 Guide

The target-local `20-scopes/scope-index.yml` is the authoritative inventory of
new-framework scope lifecycle and operational workload ownership. It is not a
release receipt, an execution journal, or a place for provider responses.

Every scope directory with canonical declaration or workload-binding files must
have one index entry. Its `workload_ownership` is exactly the workload-ID set
in its canonical workload binding. A workload identity may appear in candidate
or historical entries, but exactly one **active** scope may own it.

| State | Meaning | Required relationship |
| --- | --- | --- |
| `active` | Current operational owner of its declared workloads. | It may optionally name its accepted-historical predecessor. |
| `candidate` | Fully declared successor being checked before acceptance. | It names an active predecessor and overlaps at least one workload identity with it. |
| `accepted-historical` | Retained accepted scope/evidence that no longer owns a live release route. | It names its active successor, which names it as predecessor. |

Do not use a lifecycle edit as an emergency provider operation. When a
candidate fails, its predecessor remains active and the candidate records
failure evidence through its release route. After a successor is accepted,
restoring an earlier scope requires the normal release/recovery workflow,
fresh alignment, evidence, and any required mutation authority; changing this
index alone cannot restore a workload.

Independent new scopes do not need a predecessor. A legacy exception remains
for retiring reference infrastructure only and can never cover an indexed
new-framework scope.
