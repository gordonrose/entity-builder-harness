<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.source-material.03-product.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: source-material-readme
purpose: Define the product deploy source-material track for product applications and runtime services.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.source-material.readme
  path: docs/04.deploy/source-material/README.md
-->
# 03.product Deploy Source Material

Use this track for deploying product applications, product services, and
runtime targets.

This includes app deployment, product runtime configuration, platform services,
database migration coordination, and product health checks.

Deployment governance remains owned by `04.deploy`; this track names the system
being deployed.
