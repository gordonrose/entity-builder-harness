<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.entity.skill.create
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: entity-governance
disciplines: [architecture, backend, agentic]
kind: skill
purpose: Provide a reusable procedure for creating a durable entity as a product feature.
portability: {class: source-only, targets: []}
used_by:
- id: product.entity.workflow.create
  path: .agentic/03.product/entity/workflows/create-entity.md
-->
# Create an entity

Use this skill for a durable product resource with identity, attributes, an index, and lifecycle. First apply the feature-creation skill; then read the [entity workflow](../workflows/create-entity.md), [entity boundary](../standards/entity-as-feature.md), and the entity evolution plan.

For the currently available stage, build a handwritten entity feature: runtime schemas, entity invariants, one service per use case, private repository mapping, app-owned ordered migration, safe diagnostics/errors, deliberate public index, app mount, and product composition. Keep archive separate from logical deletion and hard purge separate from eligibility assessment.

Do not invent an entity registry, declarative metadata, generator, generated output, relationship model, or UI builder. Stop when the requested proof needs an unselected persistence target, migration execution route, package/deployment declaration, or AWS authority.
