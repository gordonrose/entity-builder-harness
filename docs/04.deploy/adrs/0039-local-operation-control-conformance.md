<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.architecture.adr.0039-local-operation-control-conformance
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: adr
purpose: Define a bounded local reference store for durable operation-control conformance.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# ADR 0039: Local operation-control conformance

## Status

Accepted implementation boundary for local source conformance under the IaaS
release-control plan. Production provider/storage selection remains open.

## Context

The existing realization gate needs to prove intent-before-effect, exclusive
scope ownership, stale-owner refusal and retrievable safe evidence after a
process dies. In-memory receipts and successful exit codes cannot establish
those properties. Implementing the local protocol first permits deterministic
failure cases without granting provider authority.

## Decision

Keep the Operational Realization Gate as the public surface. Add closed versioned
operation-control, journal and evidence contracts and a private local SQLite
reference store. Immutable intent binds release, artifact, environment, profile,
policy, idempotency key and all declared resource scopes. Resource-scope identity
is independent of release identity; acquisition is atomic over every scope.

Use DELETE rollback journaling and FULL synchronization, verify those settings,
and record the actual SQLite runtime. Refuse existing incompatible journal modes,
changed schema fingerprints or host boot without silently migrating. Bound files,
records, pages and journal length. Only the explicit local-fixture namespace is
admitted by this unit; provider normalization is future adapter work.

Persist intent before effect, maintain fencing generations after closure, and
make expired owners reconcile before any further action. Completed states retain
scope ownership until current cleanup evidence is accepted. Save full typed
bounded evidence and revalidate its content, phase, attempt, revision, fences and
freshness when consumed. Hashes detect corruption; they provide no independent
authentication against a malicious host.

The public conformance creates a fresh unique private store, runs fixed inert
fixtures with real process races and kills, and emits a safe closed receipt.
It cannot accept a provider target, arbitrary command, production policy override
or another store to mutate. All source/release/operation/qualification authority
stays blocked. Missing or broken dependencies produce a fixed safe error envelope.

## Consequences

This proves local process-restart and transaction semantics under explicit trusted
host, clock, filesystem and same-UID assumptions. It does not qualify distributed
locking, host reboot, power-loss durability, encrypted/authenticated cloud storage,
retention/RPO policy or provider-side cancellation. A fence cannot cancel an
already in-flight provider request. Unknown outcomes stay unresolved until the
later engine and provider adapters establish what actually happened.

The next unit binds this store to the existing finite container engine, preserving
resource identity before dispatch and testing actual interruption/reconciliation.
Production evidence storage and provider qualification remain required later work.
