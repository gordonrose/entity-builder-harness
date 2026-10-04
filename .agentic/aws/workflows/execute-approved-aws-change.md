<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: aws.workflows.execute-approved-aws-change
  version: 2
  status: active
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
  [bounded PostgreSQL Stage 6 route](../../01.harness/standards/operational-realization-gate.md#bounded-postgresql-stage-6-applicability),
  positively owned disposable-restore cleanup expressly included in that
  approval uses its recovery allowance without asking again. Deleting the
  source database, backups or unrelated resources remains outside that scope.
- Capture the result and verification evidence after execution.

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
