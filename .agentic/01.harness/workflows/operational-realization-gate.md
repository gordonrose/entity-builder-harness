<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.workflow.operational-realization-gate
version: 3
status: active
created_on: "2026-09-27"
updated_on: "2026-10-25"
layer: 01.harness
domain: deployment.realization
disciplines: [agentic, architecture, sre]
kind: workflow
purpose: Retain the legacy path as a compatibility pointer to deployment-owned authority.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.workflow.operational-realization-gate
  path: .agentic/04.deploy/workflows/operational-realization-gate.md
-->
# Operational Realization Workflow Compatibility Pointer

The authoritative workflow is [owned by 04.deploy](../../04.deploy/workflows/operational-realization-gate.md).
This retained path defines no additional requirements. The
[migration plan](../../04.deploy/plans/migration/operational-realization-authority.md)
records compatibility and validation.
