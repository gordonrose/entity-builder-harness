<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.readme
version: 10
status: active
created_on: "2026-08-30"
updated_on: "2026-11-09"
layer: 03.product
domain: governance
disciplines:
- agentic
- architecture
kind: layer-readme
purpose: Explain the product governance layer and its canonical surfaces.
portability:
  class: source-only
  targets: []
used_by:
- id: repo.agents
  path: AGENTS.md
-->
# 03.product Layer

## Purpose

Own product, application, platform runtime, and runtime contract governance for
this repo.

This layer covers product-facing code, app composition, platform runtime shell
contracts, and local product/runtime implementation workflows. Deployment
planning and AWS mutation remain governed by `04.deploy`.

## Source Of Truth

- Product workflows: `.agentic/03.product/workflows/`
- Product migration plans: `.agentic/03.product/plans/migration/`
- Product implementation plans: `.agentic/03.product/plans/implementation/`
- Product standards: `.agentic/03.product/standards/`
- [Feature governance](feature/README.md): the canonical standards, workflow,
  readiness checklist, pilot plan, and skill for real app features.
- [Entity governance](entity/README.md): the specialization for durable entities
  implemented as features, including the staged entity-builder path.
- [Test requirements](tests/README.md): existing testing obligations separated
  into Core, Platform and app/product owners.
- [Configuration and runtime settings](standards/config-runtime-settings.md):
  authoritative configuration requirements, formerly held in a legacy docs ruleset.
- [Public module structure](standards/public-module-structure.md): export-only
  public indexes, named implementation files and bounded legacy/refactoring rules.
- [Core module architecture: config proof](plans/implementation/core-module-architecture-config-proof.md):
  complete responsibility map, approved contract/capability layout and bounded
  consumer-context proof, with implementation and verification evidence.
- [Configuration ownership and loading](plans/implementation/configuration-ownership-and-loading.md):
  planned Core/Platform/adapter responsibilities, staged reference migration and
  evidence gates; implementation has not started.
- Product harness foundation plan:
  `.agentic/03.product/plans/implementation/product-harness-foundation.md`
- Persistence foundation v1 plan:
  `.agentic/03.product/plans/implementation/persistence-foundation-v1.md`
- Initial identity-security baseline:
  `.agentic/03.product/standards/identity-security-baseline.v1.md`
- [Deferred security capability work](plans/implementation/security-capabilities-follow-on.md):
  sessions, cookies, CSRF, secret lifecycle, tenant isolation and future integrations;
  separate from the current diagnostics and observability work.
- Runtime contracts: `platform/contracts/`
- [Deferred telemetry implementation and assurance](plans/implementation/telemetry-implementation-follow-on.md):
  recording contracts, validation/privacy, delivery guarantees, readiness,
  collector qualification, signal coverage and notification assurance;
  revisit after the diagnostics project, with separately approved slices.
- Product composition: `products/`
- Application source: `apps/`

## Boundary

Use this layer for local product and runtime work. Use `04.deploy` for cloud
infrastructure, deployment target execution, DNS, secrets, account
configuration, and runtime operations against deployed environments.
