<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: aws.workflows.execute-approved-aws-change
  version: 6
  status: active
  created_on: "2026-06-19"
  updated_on: "2026-11-19"
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
that may mutate cloud state.

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
- Stop and ask again before destructive actions such as deleting resources,
  replacing persistent storage, revoking access broadly, or changing DNS in a
  way that could interrupt service. For an explicitly adopted and approved
  [bounded PostgreSQL Stage 6 route](../standards/operational-realization-applicability.md#bounded-postgresql-stage-6-applicability),
  positively owned disposable-restore cleanup expressly included in that
  approval uses its recovery allowance without asking again. Deleting the
  source database, backups or unrelated resources remains outside that scope.
- Capture the result and verification evidence after execution.

## Bounded ordinary-release approval

An explicit approval may cover a complete ordinary release, including its
declared verification and conditional restoration of the exact accepted
predecessor. Record that approval in the existing session/change record. It
must identify the account/region, target/scope, immutable candidate package,
accepted predecessor, compatible rollback package, declared operations and
protected resources. Approval of implementing this mechanism is not approval
of a concrete AWS release.

Some step plans depend on earlier live results. They need fresh exact hashes,
but do not need another user prompt solely because those hashes become
available later. Before using the existing exact-plan execution interface,
match the generated plan to the approved release's identity and allowed effects
and pass the existing change-shape, custody and execution gates. A generated
hash is never approval by itself. An absent/mismatched binding, broader effects,
changed release identity, broader permissions, data deletion or resources
outside the approved update requires a new decision before that effect.

Conditional restoration requires a positively terminal failed verification
after completed deployment. Admission blocks, pending/unknown outcomes,
malformed reports and collection/promotion conflicts are not that evidence.
Reconcile original operations first; never replay an uncertain operation.
Use the existing separately labelled compatible-image restoration controller,
preserve data and accepted history, and privately verify the restored release.
Restoration is not successful delivery or acceptance of the failed candidate.
This approval does not authorise generic failed-stack repair, migrations,
permission changes, requalification or repeated recovery attempts.

The ordinary-update connector enforces this boundary with its reviewed
`--plan-release` fingerprint and matching `--approved-release` execution input.
Existing exact-plan commands and original task/change-set records remain
authoritative. Local connected tests, package qualification and live acceptance
are separate evidence levels; implementation alone establishes neither live
recovery nor the delivery-time target.

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
Obtain explicit approval of the concrete owned-resource deletion plan before
execution. Rule adoption, a compiler pass or previous clone-creation approval
is not deletion authority. Preserve the original readback/ownership gates and
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
