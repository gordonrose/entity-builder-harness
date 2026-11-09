<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.entity.readme
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: entity-governance
disciplines: [architecture, backend, agentic]
kind: capability-readme
purpose: Explain how durable entities are built as governed app features and later evolve into entity-builder inputs.
portability: {class: source-only, targets: []}
used_by:
- id: product.entity.workflow.create
  path: .agentic/03.product/entity/workflows/create-entity.md
-->
# Product entity governance

An entity is a durable business resource implemented as an app feature. For example, the first smoke entity will be a small record with identity, validated attributes, an index, business archiving, and Core lifecycle state. It is not a generic CRUD framework or a database table that bypasses feature rules.

This capability specializes [feature governance](../feature/README.md). Feature governance owns the general contract, transport, domain, persistence, mount, and deployment-proof path. Entity governance adds durable identity, attributes, indexed access patterns, entity lifecycle, and the path toward a future declarative entity builder.

## What each file does

- [standard](standards/entity-as-feature.md) defines the entity-specific boundary and the separation between handwritten pilot code and future generated artifacts.
- [workflow](workflows/create-entity.md) creates an entity through the feature workflow, then applies entity choices and proof.
- [readiness checklist](checklists/entity-readiness.md) makes entity identity, attributes, indexes, migrations, and lifecycle reviewable.
- [entity-builder evolution plan](plans/implementation/entity-builder-evolution.md) records the staged path from the smoke entity to a declarative, generated chain.
- [entity-creation skill](skills/create-entity.md) is the reusable procedure. The Codex discovery adapter is `.agents/skills/create-product-entity/SKILL.md`.

## How it fits into the repo

```text
apps/<app>/features/<entity>/
  ├── contract/      identity and attribute schemas, errors, diagnostics
  ├── domain/        entity invariants and named use-case services
  ├── persistence/   repository mapping and named indexes
  └── index.ts       feature's deliberate public surface
           │
           └── public app mount → product composition → deployment proof
```

The app owns its ordered migration stream. Core supplies lifecycle meaning; Platform supplies provider-neutral persistence contracts; deployment selects and executes against a concrete target.

## Limits

The smoke entity is handwritten by design. Declarative entity definitions, generated types/schemas/migrations/UI metadata, relationships, authorization policy, and an entity registry are **not yet implemented**. They become work only through the evolution plan and a separately governed implementation slice.
