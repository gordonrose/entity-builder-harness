<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.run-platform-shell-postgresql-relational-smoke.readme
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the bounded PostgreSQL relational proof command.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.run-platform-shell-postgresql-relational-smoke.shell
  path: scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh
-->
# PostgreSQL relational smoke proof

`npm run platform:shell:postgresql-relational-smoke -- --validate` checks the
committed `kanbien/staging` policy without contacting AWS.

After the reviewed Foundation and service change sets are deployed, the only
live invocation is:

```bash
npm run platform:shell:postgresql-relational-smoke -- --execute --approve-relational-stage6
```

It has no caller-selected target, credentials, task, queue, database, restore
name, network, payload, or timeout. It first confirms the fixed account,
Foundation/service readiness, public server `1/1`, dormant worker `0/0`, and
empty isolated queues. It then runs one bootstrap task, one migration task,
one fixed-record relay task, one worker task, and one isolated restore check.

Each stage label is single-use across both running **and stopped** ECS tasks.
The initial bootstrap label was consumed by a non-zero exit without retaining a
task log, task identifier, or provider payload. The current reviewed recovery
uses a distinct, fixed `recovery-1` label set only after the corrected immutable
image is deployed. It never replays the consumed label. Bootstrap creates the
two PostgreSQL identities and their connection/schema grants; the migration
identity, which creates future tables, owns its own default-table privileges.

After the corrected image's guarded Service revision is healthy, the first
recovery command is deliberately bootstrap-only:

```bash
npm run platform:shell:postgresql-relational-smoke -- --execute-bootstrap-recovery --approve-relational-bootstrap-recovery
```

It has the same fixed target and aggregate preconditions as the full proof but
cannot start migration, relay, worker, or restore. A successful bootstrap is
evidence for the ownership correction only; continuation requires its own
reviewed recovery step.

If that fixed bootstrap ends non-successfully, do not inspect or paste the
task's raw metadata or logs. The one read-only diagnostic is limited to the
consumed `recovery-1` label and returns an allowlisted category only:

```bash
npm run platform:shell:postgresql-relational-smoke -- --diagnose-bootstrap-recovery --approve-relational-bootstrap-recovery-diagnostic
```

It reads terminal metadata and, only when needed, the fixed task log stream in
memory. It never prints task IDs, stopped reasons, log lines, stack traces,
credentials, or provider responses.

To prepare a recovery decision without starting work, read the fixed aggregate
state instead:

```bash
npm run platform:shell:postgresql-relational-smoke -- --reconcile-current-state
```

This reports only server/worker desired and running counts, isolated queue
totals, source-database posture, and whether the fixed disposable restore target
is absent. It does not receive queue messages, query application rows, start a
task, create a restore, or modify AWS configuration.

## Bootstrap-effect reconciliation before promotion

Aggregate infrastructure health cannot establish that failed bootstrap attempts
left no PostgreSQL roles, grants, or schema effects. The prepared reconciliation
uses the existing `kanbien-staging-platform-relational-bootstrap` task family,
its `relational-bootstrap` container, task role, injected target-owned master,
migration, and runtime secrets, dormant-worker network configuration, and the
already-bound immutable image. It connects as the existing bootstrap master to
`platformsmoke` through the migration endpoint with `verify-full` TLS.

Its only possible invocation is:

```bash
npm run platform:shell:postgresql-relational-smoke -- --reconcile-bootstrap-effects --approve-relational-bootstrap-effects-reconciliation
```

The controller supplies a fixed Node command override. That command accepts no
arguments, begins a read-only transaction, performs one fixed PostgreSQL catalog
`SELECT`, rolls back, and emits only these booleans: expected migration/runtime
roles, bootstrap-to-migration membership, migration/runtime database grants,
schema existence and ownership, runtime schema usage/no-create restriction, and
runtime DML coverage for existing schema relations. It never receives rows,
application data, SQL input, a selected database, or a caller-defined command.
The controller persists the attempted task before launch in the durable Stage 6
ledger, allows one attempt only, waits at most 300 seconds, classifies an
uncertain or timed-out task as owned cleanup work, and accepts a successful exit
only when the one allowlisted log event has exactly those fields.

This is deliberately independent of service promotion: it runs the existing
one-shot task definition and does not update a service, task-definition
reference, image, CloudFormation stack, IAM role, network, TLS setting, or
database configuration. It therefore preserves the qualified candidate evidence
and the final remaining image-publication allowance. It is nevertheless one new
ECS task execution effect, so it remains prepared rather than executable until
that narrow effect is explicitly included in the live scope. A successful
durable reconciliation receipt is required before bootstrap a3 or the full
relational route can start.

The restore is private and disposable. The controller waits for the restored
instance, checks the fixed smoke state through a dedicated `verify-full` TLS
task, and deletes that recovery instance without a final snapshot. It retains
no endpoint, task identifier, secret, record contents, queue message, raw log,
or provider response; its only terminal output is a safe verdict.
