<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.kanbien-core-platform.provision-target-budget.readme
version: 1
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.foundation-cost-control
disciplines: [security, sre]
kind: script-guide
purpose: Explain the bounded route that provisions and verifies the target-filtered monthly budget.
portability: { class: internal, targets: [] }
used_by:
- id: aws.workflow.kanbien-core-platform.provision-target-budget
  path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/10-foundation/provision-target-budget.md
-->
# Provision Target Budget

This is the one permitted bootstrap exception to the normal cost-condition
gate. It cannot update a runtime, create another foundation resource, select a
different target, alter the USD 100 limit, or use another tag filter.

`create` requires fresh verified `Target` tag evidence and a non-empty
`KANBIEN_CORE_PLATFORM_COST_ALERT_EMAIL` operation environment value. It never
prints or records that value. It creates a Foundation UPDATE change set with
`EnableTargetBudget=true`. `review` accepts exactly one proposed resource: the
`Budget` addition. `execute` repeats that review, executes the exact change
set, waits for Foundation completion, and reads the AWS Budget back. `verify`
performs only the final read-only inspection.

After successful verification, update
`10-foundation/evidence/target-filtered-monthly-budget.yml` to `verified`;
then the normal cost-condition gate resumes as the authority for later target
mutations.
