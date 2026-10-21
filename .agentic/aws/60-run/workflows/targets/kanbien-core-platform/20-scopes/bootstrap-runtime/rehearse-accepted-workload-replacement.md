<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform.bootstrap-runtime.rehearse-accepted-workload-replacement
version: 1
status: active
created_on: "2026-10-21"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines: [security, sre]
kind: workflow
purpose: Govern a bounded, controlled-stop rehearsal of ECS replacement for the accepted private bootstrap runtime.
portability: { class: internal, targets: [] }
used_by:
- id: deploy.command.kanbien-core-platform.rehearse-accepted-workload-replacement
  path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/script.sh
-->
# Rehearse Accepted Workload Replacement

## Use when

Use only to prove that the already accepted, dependency-free bootstrap runtime
is replaced by ECS after a deliberately stopped task. This is an equivalent
orchestrator-recovery rehearsal. It does **not** prove a readiness detector,
deployment circuit-breaker rollback, or dependency recovery.

## Required sequence

1. Validate the accepted release, cost condition, and live update alignment.
2. Confirm exactly one healthy service task is running the accepted task
   definition and immutable image.
3. Run the fixed script without `--execute`; review its safe preflight report.
4. With the recorded approval, run it with `--execute`. It stops only that
   accepted task, waits for a different healthy replacement using the same task
   definition, and requires private verification completed after the stop.
5. Record the resulting safe rehearsal evidence and update the scope proof.

## Stop conditions

Stop without mutation if alignment or cost validation fails, the service has
more or fewer than one task, the accepted image/task definition differs from
the live workload, the original task does not stop, replacement is not healthy
within the bounded wait, or the fresh private verifier does not accept.

If replacement cannot be confirmed, inspect safely and use the separate
reviewed accepted-release restoration workflow; do not start another rehearsal
task or retry the stop action.
