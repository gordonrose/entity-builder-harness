<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.feature.standard.boundary
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: feature-governance
disciplines: [architecture, backend, security]
kind: standard
purpose: Define ownership, dependency and lifecycle boundaries for a real product feature.
portability: {class: source-only, targets: []}
used_by:
- id: product.feature.workflow.create
  path: .agentic/03.product/feature/workflows/create-feature.md
-->
# Feature boundary

## Purpose

A product feature is an app-owned unit of behaviour with a clear public contract and use cases. It may be mounted into a product, but its internal files remain app-owned. This standard defines the minimum boundary for a new, persistence-backed feature; a feature without one of these concerns does not need an empty folder for it.

## Required ownership

When present, feature responsibilities belong in these groups:

| Group | Owns | Does not own |
| --- | --- | --- |
| `contract/` | public types, runtime schemas, feature errors, safe diagnostic definitions | provider clients, route framework objects, database rows |
| `transport/` | request/response adaptation and transport-specific validation mapping | business decisions or persistence implementation |
| `domain/` | entities, business rules, and one file per use case under `services/` | HTTP/AWS details or SQL |
| `persistence/` | feature repository port/use, record mapping, and app-owned migration references | AWS client selection, target credentials, or lifecycle policy invention |
| feature `index.ts` | intentionally public feature exports | a second implementation location |

The owning app exposes the feature through its public `app.mount.ts` and public app exports. Platform and product composition may consume that mount, never a feature-private service, repository, or migration file.

## Validation, errors, and diagnostics

Runtime schemas validate attributes at the feature boundary. Domain services must re-use or invoke the validated contract rather than trusting a transport caller. A feature error gives an API/UI caller a stable code and message descriptor. A diagnostic record gives operators safe structured evidence of the decision: code, supported detail such as field/reason/effect, and classification.

Do not put native exception text, submitted values, database rows, connection strings, or secrets into an error detail or diagnostic record. Reuse existing Core diagnostics and message descriptors; do not build another logging or error framework.

## Persistence and lifecycle

Use Core lifecycle contracts and Platform persistence ports. The feature owns its business state and repository mapping. In particular, archived is a business visibility state; it is not a substitute for logical deletion.

- ordinary reads exclude logically deleted records;
- restore is allowed only inside the Core-defined recovery window;
- hard purge is a separately governed operation after retention and legal-hold eligibility are assessed;
- a feature must not use provider TTL or a normal CRUD delete as a purge policy.

An app that persists data owns its ordered migration stream under the app. The selected deployment scope owns executing it against a concrete target.

## Dependency direction

Features may depend on public Core and Platform contracts. They may not depend on AWS adapters, `infra/04.deploy`, target profiles, or cloud SDKs. A provider adapter may translate a public persistence port, but must not learn feature business meaning.

## Required documentation and proof

A multi-file feature has a local README that maps its files, public surface, call flow, verification route, and present limits. Local tests prove feature rules and repository mapping. Product/mount tests prove composition. Package, target, and AWS evidence are distinct proof stages and must not be inferred from local tests.
