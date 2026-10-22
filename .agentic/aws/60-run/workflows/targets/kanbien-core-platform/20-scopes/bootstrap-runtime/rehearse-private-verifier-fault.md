<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform.bootstrap-runtime.private-verifier-fault-rehearsal
version: 1
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines: [security, sre]
kind: workflow
purpose: Govern bounded private-verifier rejection and deadline fixtures without changing the accepted server release.
portability: { class: internal, targets: [] }
used_by:
- id: deploy.command.kanbien-core-platform.rehearse-private-verifier-fault
  path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/script.sh
-->
# Rehearse Private Verifier Faults

## Use when

Use only after accepted-release, cost-condition, alignment, and healthy-service
preflight pass. This tests the verifier controller and task boundaries; it does
not test readiness-failure replacement or an ECS deployment circuit breaker.

## Required sequence

1. Run each fixed case without `--execute` and review its safe preflight.
2. With recorded approval, execute `expected-source-mismatch`. It must produce
   the fixed rejection code and non-zero exit while the accepted service task,
   definition, and image remain unchanged.
3. With recorded approval, execute `controller-deadline`. At the declared
   deadline, it must report a still-running task without launching another one.
   The same command stops only its returned task ARN and confirms it stopped.
4. Inspect the accepted service again. Stop rather than retry if it changed,
   the fixture outcome differs, AWS state is uncertain, or cleanup fails.

## Boundaries

The only permitted task command overrides are the fixed mismatch environment
value and fixed 121-second sleep-only command implemented by the target-bound
script. No caller-provided command, image, source revision, network, target,
or task selector is permitted. Do not restore automatically; use the separate
accepted-release restoration route only if final-state inspection requires it.
