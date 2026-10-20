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

`../../cloudformation/bootstrap-runtime.yml` is the later E4 workload template.
It accepts only an E3 `repository@sha256:...` identity, places both the server
and the one-shot verifier in selected private subnets, and supplies only the
task execution role. The application container and verifier receive no task
role or data-access permission. The service has one private task, Cloud Map
registration, a container readiness health check, and circuit-breaker rollback.
The verifier is not a service: a later target-bound control starts it once and
accepts only the expected safe source revision response.
