<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: aws.workflows.execute-approved-aws-change
  version: 8
  status: active
  created_on: "2026-06-19"
  updated_on: "2026-11-28"
  layer: 04.deploy
  domain: infra.ci-cd
  disciplines:
  - agentic
  - sre
  kind: workflow
  purpose: Document Execute Approved AWS Change Workflow.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: repo.agents
    path: AGENTS.md
-->
# Execute Approved AWS Change Workflow

## Use When

Use this only after the user explicitly approves an AWS command or change plan
that may mutate cloud state, or requests an end-to-end live delivery covering
those effects under the [delivery-authority rule](../../04.deploy/standards/operational-realization-gate.md#end-to-end-live-delivery-authority).

## Required Gates

Before running a mutating command, confirm:

- AWS profile or account context
- AWS region, when the service is regional
- target environment
- exact intended change
- rollback or recovery path

## Rules

- Do not run mutating AWS commands without explicit approval in the current
  chat.
- Use the narrowest command that performs the approved change.
- Do not print or store secret values.
- Stop and ask before destructive actions not covered by the recorded delivery
  authority, such as deleting resources,
  replacing persistent storage, revoking access broadly, or changing DNS in a
  way that could interrupt service. For an explicitly adopted and approved
  [bounded PostgreSQL Stage 6 route](../standards/operational-realization-applicability.md#bounded-postgresql-stage-6-applicability),
  positively owned disposable-restore cleanup expressly included in that
  approval uses its recovery allowance without asking again. Deleting the
  source database, backups or unrelated resources remains outside that scope.
- Capture the result and verification evidence after execution.

For the explicitly approved scheduler proof only, the separate
[proof-only recovery resource rule](../standards/operational-realization-applicability.md#scheduler-proof-only-recovery-resources)
permits cleanup of newly reserved disposable copies and snapshots. It does not
permit deleting existing backups or the source database. Follow the native
identity, terminal-dependency, retained-evidence and single-submission checks;
the cost horizon is not a deletion instruction or automatic expiry.

## Bounded operator quota request

Use only for an explicitly approved account/region, service, quota code and
desired value recorded in the existing session/change record. This is an
operator use of the existing AWS CLI, not a runtime adapter or an unattended
quota-management capability. Scheduler deployment approval alone does not
authorize changing an account-wide quota.

1. Read `sts get-caller-identity`, `service-quotas get-service-quota` and
   `list-requested-service-quota-change-history-by-quota` using the explicit
   profile/region. Match the approved identity and adjustable regional quota.
   If effective capacity already suffices, do not submit. Observe an existing
   matching request rather than creating another; an incompatible pending
   request or failed observation requires a decision before submission.
2. Before the one submission, retain the exact approved request, account,
   region, source revision and approval reference in the worktree's private
   Git directory using the existing
   [exclusive evidence writer](../../../scripts/04.deploy/shared/provider-adapters/aws/resource_reservation.py).
   An existing intent selects observation only. Never overwrite or delete it
   to obtain another attempt. Retain the actual request ID/status separately.
3. Invoke `service-quotas request-service-quota-increase` once with those exact
   arguments and automatic CLI retries disabled (`AWS_MAX_ATTEMPTS=1`). A
   timeout, missing result or failed evidence retention is uncertain submission,
   not permission to retry. Reconcile quota request history and the original
   request ID. Access denial does not authorize IAM changes or attaching
   `ServiceQuotasFullAccess`; stop if additional permissions are required.
4. Observe the original ID with `get-requested-service-quota-change` and read
   the consuming service's effective capacity before resuming its deployment.
   Submission, a support case or approval without effective capacity is not
   readiness. Denied/partial outcomes retain their original evidence; a further
   request needs a new decision. Do not assume cancellation or automatic quota
   reduction is available as rollback: recovery is observation or an explicit
   AWS Support decision, with dependent activation still blocked.

For Lambda, use `lambda get-account-settings` to establish available capacity
for the declared reservations plus AWS's required unreserved pool. Raising the
regional quota does not change function reservations, enable processing or
authorize provisioned concurrency. Existing workload caps and activation gates
remain mandatory. Record status and the effective readback in the existing
plan/session record. AWS approval timing is outside the deployment controller.
Reviewed against [AWS quota requests](https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html)
and [Lambda reservations](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html)
on 2026-11-28.

## Bounded ordinary-release approval

An explicit end-to-end live-delivery request supplies approval for the complete
named release, including declared verification and conditional restoration of
the exact accepted predecessor. Record the actual request, account/region,
target/scope, declared operations and protected resources in the existing
session/change record. Bind the immutable candidate and compatible predecessor
packages when their validated receipts are available; do not ask again because
those identities could not exist before the approved build. Approval merely to
implement this mechanism is not approval of a concrete AWS release.

Some step plans depend on earlier live results. They need fresh exact hashes,
but do not need another user prompt solely because those hashes become
available later. Before using the existing exact-plan execution interface,
match the generated plan to the approved release's identity and allowed effects
and pass the existing change-shape, custody and execution gates. A generated
hash is never approval by itself. Missing/mismatched evidence blocks execution
until corrected. A corrected candidate within the same authorized delivery
requires fresh qualification and plan bindings, not renewed user approval.
Broader effects, a different target, broader permissions or deletion/resources
outside the declared boundary require a new decision before that effect.

Conditional restoration requires a positively terminal failed verification
after completed deployment. Admission blocks, pending/unknown outcomes,
malformed reports and collection/promotion conflicts are not that evidence.
Reconcile original operations first; never replay an uncertain operation.
Use the existing separately labelled compatible-image restoration controller,
preserve data and accepted history, and privately verify the restored release.
Restoration is not successful delivery or acceptance of the failed candidate.
An ordinary image-update boundary does not authorize generic failed-stack
repair; the separately approved bounded recovery below is distinct from
application verification rollback. It does not authorize migrations, permission changes, undeclared requalification or repeated
recovery attempts. Declared successor requalification must appear explicitly in
the reviewed delivery boundary; end-to-end wording does not bypass its gates.

The ordinary-update connector enforces this boundary with its reviewed
`--plan-release` fingerprint and matching `--approved-release` execution input.
Existing exact-plan commands and original task/change-set records remain
authoritative. Local connected tests, package qualification and live acceptance
are separate evidence levels; implementation alone establishes neither live
recovery nor the delivery-time target.

## Bounded failed-update recovery

Under explicitly recorded failed-update recovery authority, an operator may use
AWS `rollback-stack` once to restore an owned UPDATE_FAILED stack to its last
accepted stable state. This is not a generic retry or stack recreation route.
Before submission, independently validate accepted release/package custody,
exact account/region/stack ARN and ownership tags, original reserved execution
token and its terminal failed root event. Require a prior successful root event
on that same stack, predating the failed update, and the accepted template,
unchanged non-image parameters and resource inventory. Reject initial creation
failures or absent last stable state: AWS may delete a stack with no stable state.

Record the exact rollback request and one client token exclusively before its
single submission using the existing immutable reservation writer. Do not set
RoleARN, RetainExceptOnCreate or resource-skip/delete options. An existing intent
or uncertain response selects observation only, never another submission. Keep
raw provider output private; retain only approved identity/hash/status facts.
Completion requires the original recovery token's UPDATE_ROLLBACK_COMPLETE root
event, the same stack ARN, accepted template/parameters and unchanged non-task
resource identities, plus the exact accepted image running with no pending tasks.
Failed, absent or uncertain evidence is not successful recovery or acceptance.

Only then may a corrected, freshly checked delivery use a new immutable candidate
and reservation. Preserve the failed delivery and recovery evidence. Never reuse
its consumed change set or overwrite its plan. Successor image-only updates and
compatible-image restorations explicitly enable provider rollback; this restores
the prior stack if provisioning fails, and cannot promote a failed candidate.
Initial creation/count-only activation keep their separately declared policy.
Application proof and acceptance remain mandatory after a successful update.

This operator recovery uses the existing AWS CLI and immutable evidence writer;
it is not an unattended recovery capability or proof of the delivery-time target.
See [AWS rollback semantics](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/rollback-stack.html).

## Entity-smoke read-only preflight

For the isolated entity-smoke observation task, apply the provider-owned
[read-only preflight rule](../standards/operational-realization-applicability.md#entity-smoke-read-only-execution-preflight)
before supplying task-launch capability. Its adopted ordering allowance does
not replace the concrete AWS approval required above or admit business writes.
Require actual probe evidence before proceeding to the later operation; do not
mark a generic gate passed merely because the exception was selected.

## Entity-smoke disposable restore cleanup

For entity-smoke disposable restore cleanup, use the
[bounded cleanup rule](../standards/operational-realization-applicability.md#entity-smoke-disposable-restore-cleanup).
Match the concrete owned-resource deletion plan to the delivery's declared
cleanup authority before execution; do not ask again when it is already covered.
Rule adoption, a compiler pass or clone-creation-only approval is not deletion
authority. Preserve the original readback/ownership gates and
single-submission journal; uncertain deletion is reconciled, not retried.

## Bounded PostgreSQL Repair and Resume

For that adopted and approved route only, the concrete plan's allowance covers
reconciliation, safe diagnosis, relevant source/configuration repair, affected
checks, changed-image qualification/publication and bounded reattempts.
An ordinary failure pauses its operation and dependants while this work proceeds;
continue from the correct checkpoint once verified. Do not stop merely to report
an error that can be safely fixed within the existing authority. Enforce all
cumulative attempt/time/cost/recovery limits and existing preflights. Escalate
new effects, broader permissions, exhausted limits or unsafe unresolved outcomes.
Before requesting execution approval, demonstrate both effective instruction
coverage and actual support in the existing controllers; prose is not proof.

## Output

Report what changed, which profile/region/environment was targeted, whether
verification passed, and any follow-up needed. PostgreSQL closeout also includes
acceptance evidence and completed material-failure/prevention records: failure
and evidence; cause and missed-check gap; correction and verification; prevention
with proof; and resumed outcome or precise remaining blocker.
