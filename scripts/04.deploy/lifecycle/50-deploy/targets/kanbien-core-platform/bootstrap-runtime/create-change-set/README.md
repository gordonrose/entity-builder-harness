<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.kanbien-core-platform.create-change-set.readme
version: 1
status: active
created_on: "2026-10-20"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines: [architecture, security, sre]
kind: script-guide
purpose: Explain the bounded update or restoration change-set creation command.
portability: { class: internal, targets: [] }
used_by:
  - id: deploy.command.kanbien-core-platform.create-change-set
    path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/create-change-set/script.sh
-->
# Create Core Runtime Change Set

This command has one permitted effect: create a CloudFormation UPDATE change
set for the existing `kanbien-core-platform-bootstrap-runtime`. Its operation
is `update` or `restore`; it does not create an absent runtime. It obtains every runtime
parameter from the fixed foundation outputs and the qualified custody receipt.
It never accepts a target, region, stack, image, or source-revision selector.

The change set is an intermediate review artifact. Creating it is not
deployment; a separate execution control must validate its exact changes and
receive mutation authority before it can run.

The [AWS release workflow](../../../../../../../../.agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/review-and-execute-ecs-runtime-update.md)
owns qualification, approval and review order. Repeating this command is not a
resume operation; inspect an existing change set before repeating a request.
