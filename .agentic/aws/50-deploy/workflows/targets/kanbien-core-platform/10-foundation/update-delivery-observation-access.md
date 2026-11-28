<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform.update-delivery-observation-access
version: 2
status: active
created_on: "2026-11-27"
updated_on: "2026-11-28"
layer: 04.deploy
domain: deployment.foundation-access
disciplines: [security, sre]
kind: workflow
purpose: Govern the exact existing-repository observation permission adoption through retained nonreplacing CloudFormation intent.
portability: {class: internal, targets: []}
used_by:
- id: deploy.capability.foundation-access-update
  path: scripts/04.deploy/lifecycle/50-deploy/capabilities/foundation-access-update/script.py
-->
# Update delivery repository observation access

Use only the adopted [permission-only applicability rule](../../../../../standards/operational-realization-applicability.md#foundation-delivery-repository-observation-access)
and [technical-access declaration](../../../../../../../infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/technical-access.yml).
This grants the existing publisher one repository read. It does not deploy a
workload, change trust, create roles, delete resources or repair another policy.

1. Confirm the session's explicit authority for this action and its exact target.
   Complete source review, affected local checks, diagnostic review and ordinary
   metadata preparation. Record their matching identities in the existing plan.
   Use a clean committed source and its reviewed ancestor foundation template.
2. Invoke the [controller](../../../../../../../scripts/04.deploy/lifecycle/50-deploy/capabilities/foundation-access-update/script.py)
   with operation `plan`, `--predecessor` set to that full ancestor revision, and
   `--json`. This observes AWS and retains an immutable private intent, but does
   not create or execute a change set. Review its source/binding hashes and safe
   before/after fingerprints with the exact proposed policy delta. The sole
   operation adds `ecr:DescribeRepositories` on `ExistingRepositoryArn` to
   `DeliveryRole` / `publish-core-image`.
3. Under explicit change-set creation authority, invoke operation `prepare`
   with that same predecessor and returned `--approved-plan-sha256`. The controller
   preserves every deployed parameter, checks unchanged resources and actual
   IAM policy, retains a reservation, then creates the single UPDATE change set.
   If pending, use `review` or `observe`; never generate another intent or token.
4. Require `reviewed`, independently inspect the exact one-role, Policies-only,
   nonreplacing change set, and record the exact plan approval. Invoke `execute`
   with the unchanged predecessor and approved plan hash. The controller repeats
   live readback and review immediately before its one execution request.
5. Use `observe` until the original attempt is terminal. Keep calls bounded;
   no internal wait or retry is hidden in the controller. Only `completed`
   establishes its exact successor template, unchanged resource incarnations,
   actual IAM policy and original-token root completion event. Retain the safe
   report and original private intent/reservations in the existing session record.
   Then rerun the existing publisher's actual repository observation; do not
   substitute this foundation report for image qualification/publication.

AWS operations are explicitly approval-sensitive under
[execute approved AWS change](../../../../../workflows/execute-approved-aws-change.md).
The controller has `aws-mutation` effects and is not admitted by the generic
always-runnable or persistent approved-action runner. The workflow is the
execution boundary; invoking the command or supplying a plan hash does not
create user authority.

Private evidence is under the current worktree's Git directory, in
`foundation-access-update/`. Do not edit, delete, copy over or reset its files.
An already adopted successor without this attempt's history is not execution
success. Changed source, missing lineage, permission denial, unexpected resource
change, rollback or uncertain response stops dependent publication. Investigate
read-only through the original operation. Any repair or inverse requires its
own governed decision after the original attempt is reconciled; this route
does not mint replacement attempts.

## Resume after a checked controller correction

The user approved this bounded continuation on 2026-11-28. A corrected clean,
committed descendant may review and resume the same retained attempt after
affected checks and source review pass. The controller reconstructs the original
committed source and verifies the original prepare reservation. Between that
source and the corrected revision, allow only this workflow, the foundation
controller and its smoke test, the existing diagnostic review ledger and normal
session records. Require tracked regular files; template, account, configuration,
shared helper, permission and binding changes are not admitted by this route.

Keep the original intent bytes, plan hash, prepare reservation and change set.
Record the corrected controller revision separately; never restamp the original
source or create another prepare attempt. Continue with `review`, then the exact
previously approved plan's `execute`, and `observe`; an existing execution selects
observation only. Repeat live template, policy, parameter and resource checks
before execution. All original approval and nonreplacement requirements remain.

`ChangeSetType=UPDATE` is required in the original submission, not in the
`DescribeChangeSet` response: [AWS does not return that response field](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_DescribeChangeSet.html).
Review instead verifies the original stack, change-set name and operation-token
description, exact successor template and parameters, and sole nonreplacing
Policies modification. Other mismatches remain blocked; this correction does not
permit broader recovery or establish live scheduler acceptance.
