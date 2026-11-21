<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.entity.workflow.create
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: entity-governance
disciplines: [architecture, backend, security, agentic]
kind: workflow
purpose: Govern creation of a durable entity as an app feature and route future generator work separately.
portability: {class: source-only, targets: []}
used_by:
- id: product.entity.skill.create
  path: .agentic/03.product/entity/skills/create-entity.md
-->
# Create an entity

Use this workflow when the requested feature represents a durable business resource with identity, attributes, indexed access, and lifecycle. First follow [create a product feature](../../feature/workflows/create-feature.md). This workflow adds entity-specific decisions; it does not duplicate the feature procedure.

Follow [entity as feature](../standards/entity-as-feature.md), the entity evolution plan, the shared change-completion standard, and diagnostic coverage.

## Required inputs

- owning app, product, entity name, and public mount consumer;
- entity identity, attributes, runtime validation, and business invariants;
- supported index/access patterns;
- business archive meaning and Core lifecycle/retention choices;
- selected persistence capability, ordered migration stream, and intended proof stage;
- whether this is the handwritten pilot or a separately approved declarative-builder slice.

## Procedure

1. Record the entity decisions, exclusions, consumers, and intended proof in the entity plan or session record.
2. Confirm the feature workflow's required inputs and the chosen persistence capability. Stop if target/deployment evidence is absent for a claimed stage.
3. For the currently available handwritten-pilot stage, implement the entity through contract, domain, persistence, and only needed transport files. Keep each use case in its own domain-service file.
4. Add the entity migration to the owning app's ordered stream and connect the feature through the app's public mount and product composition only.
5. Prove identity/attribute validation, index behavior, archive versus logical-delete distinction, restore-window behavior, purge eligibility, error mapping, and safe diagnostic propagation.
6. For package, target, or AWS work, use the existing 04.deploy declaration, package, deploy, and run workflows. Do not turn a successful local entity test into target evidence.

## Stop conditions

Stop and record the gap when:

- the task asks for a declarative definition, generated output, or generator freshness proof before that capability is implemented;
- an entity attempts direct provider/AWS access or a target-specific migration path;
- a claimed index has no named access pattern or proof;
- an archive state is used as a substitute for deletion, or hard purge bypasses retention/legal-hold eligibility;
- relationships, authorization policy, tenancy, public ingress, UI generation, or telemetry are introduced without their own selected scope.

## Output

Report the entity's identity, attributes, indexes, lifecycle rules, files, public mount/product consumer, completed proof stages, and each deferred entity-builder capability.
