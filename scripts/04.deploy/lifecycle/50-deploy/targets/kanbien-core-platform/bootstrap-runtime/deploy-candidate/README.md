<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.kanbien-core-platform.deploy-candidate.readme
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

`script.sh` is fixed to `kanbien-core-platform/bootstrap-runtime`; it accepts
a qualified receipt and the one deterministic change-set name derived from its
digest. It re-reads the change set, confirms the selected digest and source
revision, and rejects resource types outside the two declared ECS resource
types before execution.

It has no target selector and no retry loop. A failed stack wait is a blocker,
not permission to resubmit or replace the release.
