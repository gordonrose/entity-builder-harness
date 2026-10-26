<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.kanbien-core-platform.deploy-candidate.readme
version: 3
status: active
created_on: "2026-10-20"
updated_on: "2026-10-26"
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
revision, and rejects changes outside the three declared ECS logical resources
before execution. It fetches the selected change set's `Original` template body
and the existing stack's `Original` template body, requiring both to equal the
repository template checked by the release contract. A source and proposal
changed together still fail when the deployed configuration differs. This includes task roles, execution roles, commands,
environment and private-network configuration; a permitted resource type alone
does not qualify a configuration change.

The selected proposal must supply exactly the template's declared parameter set.
Only `ImageDigest` and `SourceRevision` may differ from the observed current stack,
and both must match the qualified receipt. `UsePreviousValue` resolves against
the uniquely observed current parameter value. Duplicate, missing, masked,
conflicting or malformed bindings cannot authorize execution. Unavailable,
malformed, duplicate-key or mismatched template observations fail before
`execute-change-set`; a source change during the checks also blocks.

The same controls apply to image updates and qualified restoration. Restoration
still uses the retained accepted receipt and the existing alignment prerequisite;
it cannot broaden configuration or permissions while returning to an older image.

For an existing healthy runtime, AWS may omit `ChangeSetType` even though the
change set is a valid update. The control accepts that omission only when the
stack independently proves `CREATE_COMPLETE` or `UPDATE_COMPLETE`; it still
rejects a CREATE type, an absent/review stack, or any in-progress stack.

It has no target selector and no retry loop. A failed stack wait is a blocker,
not permission to resubmit or replace the release.
