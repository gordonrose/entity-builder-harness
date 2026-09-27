<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.runbook.kanbien-staging-postgresql-relational-reference-v1-stage6
version: 2
status: active
layer: 04.deploy
domain: persistence.operations
disciplines:
- security
- sre
kind: runbook
purpose: Operate the one bounded Kanbien staging PostgreSQL relational delivery and isolated restore rehearsal.
portability:
  class: target-specific
  targets:
  - kanbien/staging
-->
# Kanbien staging PostgreSQL relational Stage 6 runbook

## Scope

This runbook operates one fixed, harmless proof. It is not a general database
administration command, a migration tool for product data, a scheduler, or a
way to replay work. It does not modify the public server's default persistence
provider.

The controller is [the fixed relational smoke
script](../../scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py).
It owns the only permissible order:

```text
preflight → bootstrap → migrate → accept/relay once → worker once
          → private restore → TLS state verification → recovery cleanup
```

Every arrow is conditional: failure prevents the next stage. If the controller
created a recovery instance, it still attempts cleanup before reporting its
safe failure verdict.

## Bootstrap recovery boundary

The initial fixed bootstrap stage exited non-zero. No later Stage 6 task was
started, and the public server, dormant worker, and isolated queue boundary
remained in their required terminal state. The task label is permanently
consumed: stopped tasks count as consumed as well as running tasks.

The reviewed recovery corrects the PostgreSQL ownership split before it creates
one new fixed `recovery-1` label set. Bootstrap is limited to creating the
migration/runtime identities and connection/schema grants. The migration role
sets default privileges for tables it will itself create, which matches
PostgreSQL's role-ownership rules. A corrected immutable image, normal
task-definition-only Service update, stack-health check, and live-boundary
check must all pass before recovery begins. The rollout guard permits only the
eight existing task-definition revision replacements and the two existing
in-place service references: no new resources, IAM, queue, database, routing,
or listener change is admissible. The first recovery invocation runs
**bootstrap only**; it must pass before a separately reviewed continuation can
touch migration or any later stage. Do not reuse the original labels or
inspect/paste raw task logs.

## Before running

Confirm all of these through the controller's source validation and reviewed
CloudFormation change sets:

- Foundation and service stacks are `UPDATE_COMPLETE`.
- The public server is healthy at desired/running `1/1`.
- The pre-existing worker remains `0/0`.
- The new relational source and dead-letter queues are empty.
- The database remains private, encrypted, `rds.force_ssl` is required, and
  the only database-group egress is the approved loopback rule.
- The Foundation/service change sets add only the reviewed relational queue,
  task definitions, task roles, outputs, and deployment-role pass-role scope.

If continuous reconciliation reports only expired deployment-artifact drift
evidence, refresh that fact before retrying reconciliation. This is not a
deployment or a workaround: it performs drift detection and status polling on
the one fixed artifact stack, accepting only an in-sync result.

```bash
npm run platform:shell:artifact-active-drift-assessment -- \
  --execute-approved-active-artifact-drift-assessment \
  --evidence-file /tmp/new-safe-evidence.json \
  --json
```

Do not use this command to inspect stack-resource details or S3 contents. An
out-of-sync result is a stop condition for the reviewed route.

Run the local, no-AWS validation first:

```bash
npm run platform:shell:postgresql-relational-smoke -- --validate
```

After the guarded corrected-image revision has reached a healthy service
rollout, invoke only the bootstrap recovery first:

```bash
npm run platform:shell:postgresql-relational-smoke -- --execute-bootstrap-recovery --approve-relational-bootstrap-recovery
```

This fixed command cannot progress to migration, relay, worker, or restore.
Those steps remain deliberately unavailable until the bootstrap verdict has
been assessed.

If, and only if, that bootstrap returns its safe passed verdict, continue with
the separately guarded command below. It first proves that exactly one stopped
bootstrap task exists for the fixed recovery label and that its only reviewed
container exited successfully. It does not re-run bootstrap. It then performs
the single migration, relay, worker, restore, and cleanup sequence.

```bash
npm run platform:shell:postgresql-relational-smoke -- --execute-recovery-continuation --approve-relational-recovery-continuation
```

A failed continuation consumes its stage label. It never falls back to a
replay: any later repair requires a new reviewed source recovery route.

For a non-successful bootstrap, use only the fixed diagnostic command before
changing source. It can inspect the consumed recovery label's terminal
metadata and fixed log stream internally, but emits only one allowlisted
failure category; it does not print task identifiers, stopped reasons, log
text, stack traces, credentials, or provider responses.

## Run the proof

The one live command is:

```bash
npm run platform:shell:postgresql-relational-smoke -- --execute --approve-relational-stage6
```

There are deliberately no flags for a task family, queue URL, database,
endpoint, record, payload, secret, target, network, restore identifier, or
timeout. The command derives all of them from committed staging policy and
Foundation outputs. It emits one of two safe results:

- `{"postgresql_relational_smoke":"passed"}` — all fixed stages ran and the
  recovery instance was removed.
- `{"postgresql_relational_smoke":"failed"}` — do not rerun under the same
  fixed labels. Preserve only safe stage/aggregate evidence and prepare a
  reviewed source correction plus one new fixed recovery label set.

Never retrieve or paste task logs, SQL, rows, queue messages, endpoints,
credentials, request/response bodies, task identifiers, or AWS provider
responses into an issue, commit, or evidence record.

## Recovery and rollback

- A public server rollout issue uses the existing ECS service rollback; Stage 6
  does not change its service or task definition reference.
- A migration failure is forward-repair only. Do not improvise a schema
  rollback against the reference.
- A restore failure does not permit restore-over-live. The controller uses one
  private disposable recovery identifier and attempts its deletion without a
  final snapshot. If it cannot complete cleanup, treat the remaining instance
  as a cost/security exception and resolve it with an explicitly reviewed
  recovery action.
- A non-empty relational queue or DLQ is not cleared directly. Preserve safe
  aggregate evidence and design the recovery action; direct message deletion
  would destroy the proof trail.

## Evidence to record

Record only: source commit/image digest, change-set scope verdict, stage
verdicts, aggregate queue counts, server/worker counts, restore duration
category, cleanup status, alarms/alert destination status, cost posture, and
residual limits. The Stage 6 evidence template is
[`kanbien-staging-postgresql-relational-reference-v1-stage6-evidence.md`](kanbien-staging-postgresql-relational-reference-v1-stage6-evidence.md).
