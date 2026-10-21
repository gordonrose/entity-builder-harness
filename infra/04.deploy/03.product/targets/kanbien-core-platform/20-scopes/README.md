<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.03-product.targets.kanbien-core-platform.scopes.readme
version: 2
status: active
created_on: "2026-10-20"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines:
- architecture
- security
- sre
kind: scope-guide
purpose: Explain workload-owned declarations for the planned Kanbien core-platform target.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien-core-platform.scope.bootstrap-runtime.contract
  path: infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml
-->
# Target Scopes

A scope groups one deployable workload with the configuration names,
permissions, dependencies, verification operation, recovery evidence, and
exclusions that belong to it. Foundation facilities remain outside the scope.

The only current scope is `bootstrap-runtime`. It proves the smallest private
server release and explicitly excludes persistence, application identity,
queues, product capabilities, public ingress, and full observability delivery.
