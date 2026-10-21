<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.03-product.targets.kanbien-core-platform.scope.bootstrap-runtime.readme
version: 2
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines:
- architecture
- security
- sre
kind: scope-guide
purpose: Explain the accepted dependency-free core server workload and its controlled update lifecycle.
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
The release-verification endpoint is a safe private route used by its one-shot
verifier. It does not expose a public route.

`../../cloudformation/bootstrap-runtime.yml` is the private workload template.
It accepts only a qualified `repository@sha256:...` identity, places both the server
and the one-shot verifier in selected private subnets, and supplies only the
task execution role. The application container and verifier receive no task
role or data-access permission. The service has one private task, Cloud Map
registration, a container readiness health check, and circuit-breaker rollback.
The verifier is not a service: the target-bound control starts it once and
accepts only the expected safe source revision response. `accepted-release.yml`
records the retained immutable baseline. A candidate update cannot replace that
record until private verification succeeds; restoration selects that exact
retained digest rather than rebuilding old source.

`rehearsals/` holds safe evidence for deliberate candidate-and-restoration
exercises. A repeated verification command reuses a completed, accepted
verifier task from the same runtime deployment; it does not start another
task. An incomplete or rejected verifier task remains a blocker.
