<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.rules.03-product.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: rulebook-readme
purpose: Define the structured deploy-rule track for product platform and application deployment.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.rules.readme
  path: docs/04.deploy/rules/README.md
- id: deploy.rules.03-product.platform-shell-runtime-family
  path: docs/04.deploy/rules/03.product/platform-shell-runtime-family.yml
-->
# 03.product Deploy Rules

Use this track for deploy rules that apply to product applications, product
services, and platform runtime services.

Deployment governance remains owned by `04.deploy`; this track names the
system being deployed.

## Rule Inventory

- `platform-shell-runtime-family.yml` records that ECS Fargate is the first AWS
  planning runtime family for the platform shell and names the blockers before
  AWS mutation.
