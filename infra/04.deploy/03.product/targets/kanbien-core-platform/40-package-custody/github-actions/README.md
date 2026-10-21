<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.03-product.targets.kanbien-core-platform.pipelines.github-actions.readme
version: 1
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-21"
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
  path: infra/04.deploy/03.product/targets/kanbien-core-platform/40-package-custody/github-actions/pipeline-index.yml
-->
# GitHub Actions Delivery Catalogue

The catalogue records how the target's executable package-custody workflow
fits the controlled delivery model. The executable definition is the fixed
workflow in `.github/workflows/`; this record does not duplicate its steps or
create deployment authority.

`core-server-package-custody` is manual-dispatch only, requires the protected
`kanbien-core-platform` GitHub Environment, accepts only `main`, and may build,
scan, attest, publish one immutable image, and retain a safe receipt. It may
not create, select, update, verify, restart, or roll back a workload. Those
remain separate target-bound deploy and run controls.
