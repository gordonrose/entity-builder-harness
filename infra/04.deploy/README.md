<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: guide
purpose: Define deploy-layer infrastructure implementation tracks.
portability:
  class: internal
  targets: []
used_by:
- id: infra.readme
  path: infra/README.md
- id: deploy.corpus.readme
  path: docs/04.deploy/README.md
-->
# 04.deploy Infra

This directory contains deploy-layer implementation artifacts. It is organized
by the system being deployed, matching the deploy corpus track names.

Current tracks:

- `02.rag-rulebook/` for the RAG/rulebook context service and future MCP access
  surface.
- `03.product/` for product-layer deployment artifacts, currently the platform
  runtime shell image boundary and blocked staging readiness proof.

Deployment source material and structured RAG-readable deploy rules still live
under `docs/04.deploy/`. This directory is where those rules become concrete
container, environment, IaC, and workflow definitions.
