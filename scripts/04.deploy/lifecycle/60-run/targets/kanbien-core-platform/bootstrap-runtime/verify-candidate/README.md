<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.kanbien-core-platform.verify-candidate.readme
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
matching reviewed change set. Before launching it, the command looks for a
completed verifier task created by the current runtime update. It reuses that
task only if its exit result and safe log code prove acceptance; otherwise a
completed but inconclusive task is a blocker. This reuses completed proof; it
does not provide protection for concurrent calls or an earlier verifier that
is still pending/running. After an interrupted response, inspect the existing
task through the governed AWS read route before any further invocation. The
restoration wrapper already invokes verification; do not launch a separate
verifier while that wrapper may still be active.

The [AWS release workflow](../../../../../../../../.agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/review-and-execute-ecs-runtime-update.md)
owns that sequence. A failed check is a recorded blocker for diagnosis or
explicit recovery.
