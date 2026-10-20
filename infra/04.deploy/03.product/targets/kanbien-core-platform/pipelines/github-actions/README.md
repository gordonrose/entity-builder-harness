<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.targets.kanbien-core-platform.pipelines.github-actions.readme
version: 1
status: draft
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines:
- architecture
- security
- sre
kind: pipeline-guide
purpose: Explain the declaration-only future GitHub Actions delivery route for the planned core-platform target.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien-core-platform.pipelines.github-actions.index
  path: infra/04.deploy/03.product/targets/kanbien-core-platform/pipelines/github-actions/pipeline-index.yml
-->
# GitHub Actions Delivery Catalogue

This catalogue is deliberately not a GitHub Actions workflow. It records what
a later reviewed workflow must prove and which E0 facts it needs. It has no
workflow filename, OIDC role, registry, publish step, deployment step, or
target credentials.

A later workflow may be added only after custody, identity, and target facts
are selected. It must remain unable to deploy without the separately approved
target-bound deploy capability and current change set.
