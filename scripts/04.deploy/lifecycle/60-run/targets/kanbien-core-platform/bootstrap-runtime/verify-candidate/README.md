<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.command.kanbien-core-platform.verify-candidate.readme
version: 1
status: draft
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines:
- architecture
- security
- sre
kind: documentation
purpose: Explain the fixed-target live-verification control.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.command.kanbien-core-platform.verify-candidate
  path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/verify-candidate/script.sh
-->
# Verify Core-Platform Candidate

`script.sh` is fixed to `kanbien-core-platform/bootstrap-runtime`; it accepts
no target selector. A later live verifier will require a candidate id,
immutable image digest, and safe receipt reference before joining package,
workload, and server identity evidence.

Until E0 selects the target and the approved deployment change exists, it
returns a deterministic blocked report without reading or changing any live
system.
