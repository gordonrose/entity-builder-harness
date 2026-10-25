<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.architecture.adr.0042-separate-change-and-deployment-proof-ownership
version: 1
status: active
created_on: "2026-10-24"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.governance
disciplines: [agentic, architecture, sre]
kind: adr
purpose: Record authoritative shared completion, deployment proof and provider procedure owners with compatible legacy entry points.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.plan.migration.operational-realization-authority
  path: .agentic/04.deploy/plans/migration/operational-realization-authority.md
-->
# ADR 0042: Separate Change and Deployment Proof Ownership

## Status

Accepted for the authorized local consolidation. This decision grants no
provider execution, publication, secret access, commit, merge or push authority.

## Context

Operational realization rules lived under the harness layer despite owning
provider-neutral deployment proof. Their standard also held a target-specific
PostgreSQL applicability procedure. Layer workflows had no shared authoritative
principles connecting implementation, affected consumers, verification and
completion. The deployment owner routing already requires one owner for each
rule and permits cross-phase standards.

## Decision

[Shared change completion](../../../.agentic/shared/standards/require-change-completion.md)
owns connected implementation, consumer impact, proportionate verification,
continuation and completion evidence. The [deployment realization standard](../../../.agentic/04.deploy/standards/operational-realization-gate.md)
and [workflow](../../../.agentic/04.deploy/workflows/operational-realization-gate.md)
own generic deployment proof, ordered gates and realization semantics.
Lifecycle standards specialize the evidence at their stages. The existing
[AWS applicability standard](../../../.agentic/aws/standards/operational-realization-applicability.md)
owns the bounded PostgreSQL procedure without changing its scope or approvals.

Keep old harness standard/workflow paths as thin compatibility pointers.
Retain schema, template and compiler paths and schema IDs; their deployment
semantics refer to the canonical deployment authority. Active references move
to the owner; historical session evidence remains unchanged.

## Consequences

Relevant workflows reference shared and deployment authority without defining
competing completion conditions. Coverage and check selection can connect
scope requirements and existing validators while preserving their stage and
permission boundaries. Declaration success remains distinct from local
runtime, container, CI and live proof.

The [migration plan](../../../.agentic/04.deploy/plans/migration/operational-realization-authority.md)
records reference buckets, compatibility, checks and recovery. Placement checks
recognize explicit cross-phase authority and provider-wide standards; they do
not relax lifecycle-specific placement. No generic validator gains a
provider-specific branch, and no provider namespace or runtime contract moves.
