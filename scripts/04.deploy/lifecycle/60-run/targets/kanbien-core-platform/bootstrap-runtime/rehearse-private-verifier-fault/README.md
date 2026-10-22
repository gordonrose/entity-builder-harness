<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.kanbien-core-platform.rehearse-private-verifier-fault.readme
version: 1
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines: [security, sre]
kind: documentation
purpose: Explain the bounded private-verifier rejection and timeout fixtures.
portability: { class: internal, targets: [] }
used_by:
- id: deploy.command.kanbien-core-platform.rehearse-private-verifier-fault
  path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/script.sh
-->
# Rehearse Private Verifier Faults

This fixed-target, AWS-mutating command accepts only two cases. It never
accepts a target, image, command, source revision, cluster, or task selector.

`expected-source-mismatch` runs the existing verifier task definition with one
fixed impossible expected source revision. It must stop non-zero with
`KANBIEN_CORE_RELEASE_VERIFICATION_FAILED`, while the accepted server stays
unchanged.

`controller-deadline` runs the same task definition with a fixed 121-second
sleep-only Node command. At the declared 120-second controller deadline it
must report a still-running remote task and start no duplicate. With
`--execute`, it stops only that returned fixture task, waits for it to stop,
and confirms the accepted server remains unchanged.

Both cases run accepted-release, cost-condition, alignment, service-health,
task-definition, private-network, and deadline preflight first. They are not
evidence of readiness-failure recovery or ECS circuit-breaker rollback.
