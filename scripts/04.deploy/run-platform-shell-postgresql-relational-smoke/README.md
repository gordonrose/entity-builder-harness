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

The restore is private and disposable. The controller waits for the restored
instance, checks the fixed smoke state through a dedicated `verify-full` TLS
task, and deletes that recovery instance without a final snapshot. It retains
no endpoint, task identifier, secret, record contents, queue message, raw log,
or provider response; its only terminal output is a safe verdict.
