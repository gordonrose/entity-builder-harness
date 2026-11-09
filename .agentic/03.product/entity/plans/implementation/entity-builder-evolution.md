<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.entity.plan.builder-evolution
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: entity-governance
disciplines: [architecture, backend, agentic]
kind: implementation-plan
purpose: Stage evolution from a handwritten smoke entity to a verified declarative entity builder.
portability: {class: source-only, targets: []}
used_by:
- id: product.entity.workflow.create
  path: .agentic/03.product/entity/workflows/create-entity.md
-->
# Entity-builder evolution

## Stage 0 — handwritten smoke entity

Build one entity as an ordinary persistence-backed feature at `apps/<app>/features/smoke-record`. It is the reference consumer for feature/entity governance, Core lifecycle, Platform persistence, app mounting, product composition, and staged deployment proof.

It has one identity, a small fixed attribute set, one deliberately named index, business archive, logical deletion, restore-window handling, and purge-eligibility assessment. It has no relationships, dynamic attributes, entity registry, generated UI, or generic CRUD abstraction.

## Stage 1 — declarative entity definition

Introduce one TypeScript-checked declarative definition as the source of truth only after its schema, owner, validation, and generation boundaries are specified. It replaces duplicated handwritten entity metadata; it is never a loose JSON blob.

## Stage 2 — deterministic generation

Generate the artifacts justified by the declared entity model: inferred types, runtime schemas, persistence metadata/migrations, API contracts, UI configuration, and tests. Generator inputs, outputs, placement, deterministic regeneration, and freshness checks must be governed before any output is described as generated.

## Stage 3 — broader entity model

Add relationships, policy/authorization hooks, projections, and reusable entity-builder tooling only as separate bounded capabilities. Each must preserve app ownership, explicit lifecycle, and deployment-proof boundaries.

## Evidence rule

The earlier legacy entity rule pack is useful source material for the intended generated chain. It is not proof that a generator, generated output, or entity-builder runtime exists today. The smoke entity is successful only when its actual handwritten feature and staged proof work; it must not simulate later stages.
