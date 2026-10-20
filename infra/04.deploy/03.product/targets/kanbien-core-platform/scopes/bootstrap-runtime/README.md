<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.03-product.targets.kanbien-core-platform.scope.bootstrap-runtime.readme
version: 1
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-20"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines:
- architecture
- security
- sre
kind: scope-guide
purpose: Explain the first dependency-free core server workload declaration.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien-core-platform.scope.bootstrap-runtime.contract
  path: infra/04.deploy/03.product/targets/kanbien-core-platform/scopes/bootstrap-runtime/declaration-contract.yml
-->
# Bootstrap Runtime

This scope runs only the declared `kanbien-core-server` package candidate. It
has no persistence, queue, product route, provider adapter, or public ingress.
The release-verification endpoint is a safe, private route used by a later
selected verifier. It does not make the workload live or expose a route now.
