<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.kanbien-core-platform.deploy-candidate.readme
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

For an existing healthy runtime, AWS may omit `ChangeSetType` even though the
change set is a valid update. The control accepts that omission only when the
stack independently proves `CREATE_COMPLETE` or `UPDATE_COMPLETE`; it still
rejects a CREATE type, an absent/review stack, or any in-progress stack.

It has no target selector and no retry loop. A failed stack wait is a blocker,
not permission to resubmit or replace the release.
