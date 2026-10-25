<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.layer.readme
version: 3
status: active
created_on: "2026-10-06"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.governance
disciplines:
- agentic
- architecture
- sre
kind: layer-readme
purpose: Define the provider-neutral deployment governance layer and its transition boundary with AWS-specific governance.
portability:
  class: source-only
  targets: []
used_by:
- id: repo.agents
  path: AGENTS.md
- id: deploy.plan.migration.aws-provider-neutral-transition
  path: .agentic/04.deploy/plans/migration/aws-provider-neutral-transition.md
-->
# 04.deploy Layer

## Purpose

Own provider-neutral deployment governance: target discovery and alignment,
release lifecycle controls, and provider-adapter boundaries.

## Transitional Boundary

This layer is being established without moving existing AWS governance.
`.agentic/aws/` remains the authoritative location for AWS inspection,
planning, execution, PostgreSQL Stage 6 work, and AWS-specific workflows until
the migration plan explicitly advances to a later phase.

Do not duplicate AWS execution authority here. A provider-neutral workflow may
reference an existing provider workflow during the transition, but may not
weaken or replace its approval gates.

## Source Of Truth

- Lifecycle workflows, standards and schemas: `.agentic/04.deploy/<phase>/`
- [Current lifecycle routes](lifecycle/README.md): build, package, deploy and run entry points
- Cross-phase and not-yet-migrated authority: `workflows/`, `standards/`, `schemas/`
- Migration plans: `.agentic/04.deploy/plans/migration/`
- Future provider adapters: `.agentic/04.deploy/providers/`
- Current AWS-specific governance: `.agentic/aws/`
- Deployable target definitions: `infra/04.deploy/`
- Deploy corpus and durable deployment documentation: `docs/04.deploy/`
- Deploy capabilities and checks: `scripts/04.deploy/`

## Initial Capabilities

Declaration Coverage comes first: it records the bounded local requirements
and their proof paths. Target Alignment Preflight then compares that covered
declaration with safe, fresh target facts. Their design and offline checks must
be established before any provider read adapter or live target operation is
added.

## Completion and Proof Ownership

[Shared change completion](../shared/standards/require-change-completion.md) owns cross-layer implementation and evidence principles. The [operational realization standard](standards/operational-realization-gate.md) owns deployment proof semantics, with lifecycle standards specifying their applicable evidence. [Provider owners](providers/README.md) retain exact procedures and authority.
