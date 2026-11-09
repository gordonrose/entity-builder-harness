<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.entity.standard.entity-as-feature
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: entity-governance
disciplines: [architecture, backend, security]
kind: standard
purpose: Define the durable entity responsibilities added to the general product-feature boundary.
portability: {class: source-only, targets: []}
used_by:
- id: product.entity.workflow.create
  path: .agentic/03.product/entity/workflows/create-entity.md
-->
# Entity as feature

## Purpose

An entity is an app-owned feature representing a durable business resource. It follows the [feature boundary](../../feature/standards/feature-boundary.md); this standard adds only the entity-specific responsibilities. It does not prescribe a universal app architecture or authorize an entity generator.

## Entity boundary

An entity feature lives at `apps/<app>/features/<entity>/`. Its domain entity is the validated business representation, not a provider row. Its repository mapping is private to the feature. Platform may see the owning app's public mount but not the entity's service, repository, database mapping, or migration implementation.

An entity defines:

- one stable entity identity and the rule that creates/validates it;
- named, runtime-validated attributes and their domain invariants;
- named indexes as supported access patterns, not incidental provider indexes;
- business visibility such as `active`/`archived`, separately from Core logical deletion;
- use cases with one named service file per operation;
- safe caller errors and structured diagnostics at actual decision boundaries.

The app owns the ordered migration stream containing the entity's migration. A feature must not introduce an unordered per-entity migration mechanism.

## Handwritten pilot shape

Until the declarative entity-builder stage is implemented, the entity feature owns ordinary source files:

```text
contract/types.ts       static entity and input types
contract/schemas.ts     runtime attribute validation
contract/errors.ts      stable caller-facing errors/messages
contract/diagnostics.ts safe structured observations
domain/entity.ts        entity invariants and state transitions
domain/services/        one named use case per file
persistence/repository.ts and mapping.ts
index.ts                deliberate public exports
```

`transport/` is added when the entity has a route, job, or other transport boundary. Empty folders are not required.

## Lifecycle and persistence

Archive changes business visibility. Logical deletion changes Core lifecycle state and excludes ordinary reads. Restore follows the recovery-window rule. A hard purge is not a normal entity delete; it requires separately governed retention, legal-hold, eligibility, and execution evidence.

Entity diagnostics use the existing code/classification/detail model. Do not put native errors, row values, secrets, or provider wording into diagnostic details. Entity errors use existing message descriptors; they are not a duplicate diagnostic system.

## Future declarative builder

The eventual source of truth will be a TypeScript-checked declarative entity definition. It may generate types, runtime schemas, persistence metadata, migrations, API/UI configuration, and tests. That is **not yet implemented**. Until a generator and freshness checks exist, do not create fake generated files, loose JSON definitions, or hand-maintained artifacts presented as generated output.
