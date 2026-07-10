<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: guide
purpose: Define the product deploy implementation track for the platform runtime shell.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.readme
  path: infra/04.deploy/README.md
-->
# 03.product

This deploy track contains product-layer deployment implementation artifacts.

The first artifact is the provider-neutral platform shell image boundary. It
packages the local platform server entrypoint so the shell can be built and
smoke-tested before AWS deployment readiness.

The first AWS planning runtime family is recorded in
`aws-runtime-family.decision.yml`: ECS Fargate. That decision is planning-only
and does not authorize AWS mutation, DNS changes, image publishing, or
production exposure.

This track does not create cloud resources. AWS planning and execution remain
governed by `.agentic/aws/` workflows.
