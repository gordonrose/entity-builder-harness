<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.03-product.targets.kanbien-core-platform.foundation.readme
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
kind: foundation-guide
purpose: Explain shared target facilities used by the accepted bootstrap runtime.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien-core-platform.foundation.index
  path: infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/foundation-index.yml
-->
# Foundation

Foundation records facilities shared by workloads in this target, not a
workload’s application behaviour. The recorded facilities are live-verified
starting facts; fresh alignment still checks that they remain fit for a proposed
update or restoration.

`technical-access.yml` separates the delivery identity from the workload
startup identity. `network.yml` declares the private verifier boundary and the
distinct private paths needed to
retrieve an immutable image: registry control plane, registry data plane, and
the object store that serves image layers. The latter must be restricted to the
provider-managed object-store prefix list, not widened to general internet
egress.

`cost-control.yml` records that AWS currently exposes the `Target` tag as
inactive. Its `evidence/` record holds the narrowly approved, expiring waiver
for this rehearsal; no update or restoration may mutate AWS after that record
expires unless fresh provider evidence or a new waiver replaces it.
