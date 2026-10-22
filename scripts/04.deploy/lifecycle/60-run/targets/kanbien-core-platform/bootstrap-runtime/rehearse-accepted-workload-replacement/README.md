<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.kanbien-core-platform.rehearse-accepted-workload-replacement.readme
version: 1
status: active
created_on: "2026-10-21"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines: [security, sre]
kind: documentation
purpose: Explain the target-bound controlled ECS replacement rehearsal command.
portability: { class: internal, targets: [] }
used_by:
- id: deploy.command.kanbien-core-platform.rehearse-accepted-workload-replacement
  path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/script.sh
-->
# Accepted Workload Replacement Rehearsal

`script.sh` is fixed to `kanbien-core-platform/bootstrap-runtime`. Without
`--execute` it only validates the accepted baseline, cost condition and target
alignment. With `--execute`, it stops one current accepted ECS task, proves
that ECS creates a different healthy task with the identical accepted task
definition, and calls the private verifier with the stop time as its freshness
boundary.

The command never changes the image, task definition, service desired count,
network, IAM, or CloudFormation stack. It must not be used to simulate an
application readiness failure.
