<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.03-product.targets.kanbien-core-platform.foundation.readme
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
kind: foundation-guide
purpose: Explain shared target facilities required by the planned bootstrap target.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien-core-platform.foundation.index
  path: infra/04.deploy/03.product/targets/kanbien-core-platform/foundation/foundation-index.yml
-->
# Foundation

Foundation records facilities shared by workloads in this target, not a
workload’s application behaviour. Every record is still an unresolved E0 fact:
these files declare what must be decided, not a provider resource to create.

`technical-access.yml` separates the future delivery identity from the
workload startup identity. `network.yml` reserves a private verifier boundary;
it deliberately declares no public ingress, endpoint, security group, or
network identifier.
