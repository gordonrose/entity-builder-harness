<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.kanbien-core-platform.verify-candidate.readme
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
only the qualified package receipt. It verifies that the running ECS service
uses that receipt's immutable digest and runs the one-shot private verifier
once. It cannot select another target, stack, region, route, or image.

The verifier runs only after the fixed deployment command has accepted the
matching reviewed change set. It has no retry loop: a failed check is a
recorded blocker for diagnosis or explicit recovery.
