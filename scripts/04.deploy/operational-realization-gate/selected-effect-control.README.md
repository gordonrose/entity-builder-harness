<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.script.selected-effect-control.readme
  version: 1
  status: active
  layer: 04.deploy
  domain: deployment.realization
  disciplines: [architecture, security, sre]
  kind: readme
  purpose: Define the one selected source route command and the live receipts required before execution.
  portability: {class: internal, targets: [kanbien/staging]}
  used_by:
  - id: deploy.script.selected-effect-control
    path: scripts/04.deploy/operational-realization-gate/selected_effect_control.py
-->
# Selected effect control

Use the source route compiler to inspect the declared operation set and its
required live receipts:

    python3 -B scripts/04.deploy/operational-realization-gate/selected_effect_control_cli.py \
      --selected-effect-route \
      --route candidate-execution-preflight \
      --mode execute \
      --json

The relational route accepts the reviewed modes `execute`,
`execute-bootstrap-recovery`, `execute-recovery-continuation`, and
`diagnose-bootstrap-recovery`.

This command only compiles a source record. It always reports blocked release
and operation authority. The candidate and relational wrappers call the same
boundary before their provider code. They require six independently checked
live receipts: selected admission, selected operation record, store event,
immutable evidence, selected control-plane result, and authenticated transport.

The source contract deliberately cannot manufacture these receipts. P16 runs
the prepared hosted source check; P17–P19 provide the published artifact and
current target evidence; P20 reviews the immutable change plan; P21 provisions
the approved store and permissions. Until then, no command in this route can
start a task, mutate the database, or perform recovery work.

