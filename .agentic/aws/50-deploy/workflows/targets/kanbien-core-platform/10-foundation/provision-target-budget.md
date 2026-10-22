<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform.provision-target-budget
version: 1
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.foundation-cost-control
disciplines: [security, sre]
kind: workflow
purpose: Govern the one-time target-budget bootstrap route without bypassing the normal cost gate for later mutations.
portability: { class: internal, targets: [] }
used_by:
- id: deploy.command.kanbien-core-platform.provision-target-budget
  path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/script.sh
-->
# Provision Kanbien Core Platform Target Budget

Use this workflow only while the declared Foundation budget condition is
`not-requested`. It is not a general Foundation update route and it does not
authorise persistence, runtime, network, identity, image, or configuration
changes.

1. Supply the approved cost-alert address only through the operation
   environment variable `KANBIEN_CORE_PLATFORM_COST_ALERT_EMAIL`; do not put
   it in Git, a receipt, command output, or evidence.
2. Run `create` under explicit change-set creation authority.
3. Inspect the returned change set. It must add only
   `AWS::Budgets::Budget` logical resource `Budget`.
4. Run `execute` only under explicit execution authority for that exact change
   set. The command repeats the scope review before execution.
5. Retain its safe read-back observation, set the budget evidence to
   `verified`, then run the normal target cost-condition gate.

If creation or execution is interrupted, inspect that exact change set or
stack before repeating an effect. Do not create a second change set merely
because a local response was lost.

`UPDATE_ROLLBACK_COMPLETE` is a stable recovered Foundation state only after
the failed operation has been inspected. It permits a new reviewed proposal;
it does not turn an unknown or in-progress update into permission to retry.
