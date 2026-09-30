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
uses a distinct, fixed `recovery-4` label set only after the corrected immutable
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
consumed `recovery-4` label and returns an allowlisted category only:

```bash
npm run platform:shell:postgresql-relational-smoke -- --diagnose-bootstrap-recovery --approve-relational-bootstrap-recovery-diagnostic
```

It reads terminal metadata and, only when needed, the fixed task log stream in
memory. It never prints task IDs, stopped reasons, log lines, stack traces,
credentials, or provider responses.

The restore is private and disposable. The controller waits for the restored
instance, checks the fixed smoke state through a dedicated `verify-full` TLS
task, and deletes that recovery instance without a final snapshot. It retains
no endpoint, task identifier, secret, record contents, queue message, raw log,
or provider response; its only terminal output is a safe verdict.

The recovery labels describe the existing fixed controller policy. These source
changes do not approve reusing a consumed attempt, deploy the current candidate,
or prove that a previously deployed image contains the new code. Current source
requires a newly qualified immutable artifact and separately approved execution.

## Fixed task database preflight

The five compiled relational entrypoints accept exactly one optional argument,
`--preflight`. Without arguments they retain their existing effect behavior.
Unknown arguments, repeated flags or additional values fail before a pool is
created or an effect begins. No SQL, principal, secret, endpoint or queue can be
selected through this argument.

Preflight uses the same injected credentials, configuration, public CA bundle
and verify-full connection pool as the corresponding task. It reserves one
connection, begins `READ ONLY`, runs fixed catalog queries, then rolls back and
releases that connection. A failed query or rollback produces a failed result;
no preflight path issues role/schema/data changes or sends/receives a queue
message. Database sessions and telemetry may still create normal operational
activity; “read-only” refers to the declared application/database operations.

| Task | Necessary database checks |
| --- | --- |
| Bootstrap | Actual authenticated principal; database identity; read-only transaction; TLS and PostgreSQL 17; role creation and database schema-creation privileges. |
| Migration | Exact migration principal without elevated attributes or memberships; schema usage/creation and ownership. |
| Relay and worker | Exact runtime principal without elevated attributes or memberships; schema usage with no schema/database creation or schema ownership; all four DML privileges independently present on each of the four required application/platform tables. |
| Restore verification | The existing isolated restore-host restriction, exact runtime principal and least privilege, and SELECT on the two tables the existing verifier reads. It cannot substitute the live primary endpoint. |

The result uses the closed
`infra/04.deploy/contracts/release-control/v1/relational-task-preflight.schema.yml`
contract. Its fixed fields are `schema`, `scope`, `operation`, `verdict` and
`authorized: false`. It never emits the task's effect-completion event, raw SQL
rows, usernames, endpoints, credentials, query exceptions or provider output.
The controller must bind the result to the exact task revision, immutable image,
command plus preflight mode, and current attempt. An uploaded result or process
exit code alone is insufficient.

This mode proves necessary database prerequisites only. It does not prove queue
send/receive authority, migration effects, restore contents or release
eligibility. In particular, the relay identity is intentionally send-only;
adding GetQueueAttributes solely to make a preflight pass would broaden its
policy. Target role/network/configuration inspections and later independent
effect checks remain separate obligations.

Preflights are sequential: bootstrap's check precedes bootstrap; migration's
check follows bootstrap; runtime checks follow migration; restore's check needs
the actual isolated restored instance. Running all five before the first
bootstrap cannot prove principals or tables that do not yet exist. The current
Python live controller has not yet adopted these task-mode calls. The next
controller integration must preserve this ordering, exact immutable revision
binding, durable attempts and cleanup; this source addition authorizes no live
execution.

Focused mocked verification uses the pinned TypeScript 5.9.3 compiler and Node
22.23.3 supplied by the existing toolchain qualification:

```sh
RELATIONAL_PREFLIGHT_TYPESCRIPT_ROOT=/path/to/verified/typescript \
  /path/to/verified/node --test \
  scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/test_preflight_runtime.mjs
```

These tests transpile and execute the actual helper and all five entrypoints in
an isolated mock context. They verify fixed read-only calls, argument rejection,
principal/TLS/privilege failures, missing tables, cleanup, output redaction and
unchanged default effect dispatch. They are not real database, queue, container
or target evidence. The final qualified image and disposable/target runs remain
required at their respective boundaries.


## Immutable deployed task revision

The existing controller resolves each stage from its named
`Relational*TaskDefinitionArn` output on the fixed service stack. It requires
that exact stack name and account/region ARN to remain `UPDATE_COMPLETE`, rejects
missing/duplicate/malformed bindings, and reads the stack's immutable `ImageUri`
for the existing `platform-shell` repository. A task-family name without an
explicit revision is no longer an execution selector.

Before starting the stage, the controller describes the exact ARN and checks
its returned ARN, family, integer revision, active status, Fargate/awsvpc shape,
sole named container, fixed compiled command, lack of entrypoint override/ports,
and image equality with the stack parameter. The subsequent `run-task` call
uses that same ARN. A newly registered latest family revision therefore cannot
replace the checked revision between inspection and execution.

The launch response and each poll must refer to the same task ARN, cluster,
fixed stage label, Fargate launch type and task-definition ARN. Only the sole
expected container's integer exit code zero on that task can satisfy completion.
Missing or conflicting provider identity fields fail with fixed safe messages;
no ARN, raw provider response, image, or credential is emitted.

These checks bind execution to a deployed revision; they do not establish that
the revision is built from current repository source, grant release authority,
or prove deployment effects. Durable attempts, shared locking/fencing,
interrupted/lost-response reconciliation, reliable predecessor evidence, and
verified timeout cleanup remain necessary controller integration work. Existing
approval flags and modes are unchanged, and this source change authorizes no
AWS operation.

Focused offline test: `python3 -B -m unittest discover -s
scripts/04.deploy/run-platform-shell-postgresql-relational-smoke
-p 'test_task_revision_binding.py'`. Provider calls are mocked.

The checked fields are documented by the official [CloudFormation Stack
API](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_Stack.html),
[ECS TaskDefinition API](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_TaskDefinition.html)
and [ECS Task API](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Task.html).
