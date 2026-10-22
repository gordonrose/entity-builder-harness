<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.architecture.adr.0041-select-postgresql-for-core-platform-persistence-proof
version: 1
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.persistence
disciplines: [architecture, security, sre]
kind: adr
purpose: Record PostgreSQL as the selected first application-persistence reference for kanbien-core-platform without authorising provider resources.
portability: { class: internal, targets: [] }
used_by:
- id: deploy.plan.implementation.platform-to-target-chain-control
  path: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md
-->
# ADR 0041: Select PostgreSQL for the Core Platform Persistence Proof

## Status

Accepted as the selection recorded in the core-platform programme. Provider
resource design and live execution remain separate approval boundaries.

## Context

The dependency-free core server has proved its release and controlled recovery
routes. The next application proof creates one synthetic record and retrieves
it after server replacement, with explicit duplicate and failure behaviour.
The programme considered PostgreSQL and DynamoDB; the current work selects the
PostgreSQL reference and prepares its secret declarations before implementation.

Existing PostgreSQL references supply examples to evaluate, but ADR 0033
selects infrastructure for staging and does not select or provision resources
for this target. A generic core-record adapter is still implementation work.

## Decision

Use PostgreSQL for the first application-persistence proof on
`kanbien-core-platform`. Keep runtime access separate from migration and
administrative access. The portable Secret Dependency Contract records only
references, owners, authorised workloads, lifecycle behaviour and safe results;
the secret store holds credential values.

The target-specific design will select hosting, network/TLS, credential
delivery, access policies, cost controls and recovery arrangements. This ADR
does not select a managed-service variant, reuse staging credentials or
resources, or grant permission to create a database, secret, role or deployment.

## Consequences

The first proof can exercise relational access and migration compatibility
while remaining limited to one application-record operation. PostgreSQL adds
credential, schema, connection and data-recovery obligations to the existing
server lifecycle. Those obligations need implementation and evidence before
live acceptance; the declaration validator alone does not prove them.

Persistence across server replacement, compatibility across two persistence-
capable releases, and database backup/restore remain separate proof claims.
The dependency-free bootstrap boundary and its accepted release remain intact.
