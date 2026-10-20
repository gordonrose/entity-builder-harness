<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.command.kanbien-core-platform.deploy-candidate.readme
version: 1
status: draft
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines:
- architecture
- security
- sre
kind: documentation
purpose: Explain the fixed-target deployment control.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.command.kanbien-core-platform.deploy-candidate
  path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/script.sh
-->
# Deploy Core-Platform Candidate

`script.sh` is fixed to `kanbien-core-platform/bootstrap-runtime`; it has no
target selector. Once a target exists, it will require a candidate id,
immutable image digest, and approved change-set reference. It reports only
whether those fields were supplied, never their values.

At the current E0 boundary it always fails closed before a provider read or
mutation. It does not turn a static declaration into permission to deploy.
