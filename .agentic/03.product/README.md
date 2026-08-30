<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.readme
version: 1
status: active
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
- Runtime contracts: `platform/contracts/`
- Product composition: `products/`
- Application source: `apps/`

## Boundary

Use this layer for local product and runtime work. Use `04.deploy` for cloud
infrastructure, deployment target execution, DNS, secrets, account
configuration, and runtime operations against deployed environments.
