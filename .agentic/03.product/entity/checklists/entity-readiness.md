<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.entity.checklist.readiness
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: entity-governance
disciplines: [architecture, backend, sre]
kind: checklist
purpose: Make entity identity, attribute, index, lifecycle, and proof claims observable.
portability: {class: source-only, targets: []}
used_by:
- id: product.entity.workflow.create
  path: .agentic/03.product/entity/workflows/create-entity.md
-->
# Entity readiness checklist

## Entity contract

- [ ] The entity has a stable identity, runtime-validated attributes, and named domain invariants.
- [ ] Each index has a named supported access pattern and a focused behaviour test.
- [ ] Caller errors and safe diagnostics describe entity decisions without private values or raw causes.
- [ ] The entity's public index and app mount expose only the intended surface.

## Lifecycle and persistence

- [ ] Business archive is distinct from Core logical deletion.
- [ ] Ordinary reads exclude logically deleted entities; restore-window behaviour is proven.
- [ ] Hard purge is limited to eligibility assessment unless a separate retention/legal-hold/execution scope exists.
- [ ] The entity migration belongs to the owning app's ordered stream and uses a public persistence contract.

## Evolution and proof

- [ ] The implementation is labelled handwritten pilot or declarative-builder; no generated claim lacks a generator/freshness check.
- [ ] Focused entity, mount, product-composition, and applicable persistence tests cover accepted and rejected paths.
- [ ] Package, target, and AWS evidence are reported separately from local behaviour.
