<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.script.run-platform-shell-worker-smoke.readme
version: 5
status: active
created_on: "2026-09-23"
updated_on: "2026-10-26"
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the guarded side-effect-free staging worker-consumer proof and its separate fixed telemetry observation.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.run-platform-shell-worker-smoke
  path: scripts/04.deploy/run-platform-shell-worker-smoke/script.sh
-->
# Platform-shell worker smoke

This command is a guarded, disposable **consumer** proof. Its offline
`--validate` mode checks that the staging target still declares the exact
two-message policy. Its live mode is deliberately unavailable without both
`--execute` and `--approve-live-worker-smoke`, plus a current approved staging
operation.

When explicitly run, it confirms the source queue, DLQ, and worker service are
empty/dormant; sends a first harmless `platform-smoke.rebuild` envelope; sets
only the worker service to one task; waits for bounded settlement; keeps the
task alive for 75 seconds; sends a second harmless envelope; waits for its
settlement and the reviewed 75-second metric-export wait; then always sets the
service back to desired count zero. The two fixed deliveries establish and
advance the fresh cumulative counter needed by the read-only PromQL
`increase()` evidence query. Output contains only a safe verdict, duration,
and task revision.

It never prints a message body or identity, receipt handle, queue URL, raw AWS
response, task ARN, token, or secret. It is not an outbox producer, a state
transaction, or proof that future business side effects are duplicate-safe.

After a successful run and the declared telemetry arrival grace, the operator
uses `npm run platform:shell:metric-coverage -- --coverage-target worker` to
observe the one fixed delivery counter. Queue settlement and metric delivery
are intentionally two separate proof steps: a queue can settle even when the
collector/exporter path is unavailable.

Cleanup is armed before the first message submission. A timeout or lost response
from queue submission or worker scale-up therefore still triggers the bounded
scale-down and observation path. The original proof failure is retained if
cleanup observation also fails. Scale-down response failure alone is not proof
of failure: the command observes the service and queues before classifying the
outcome.

A completed cleanup requires worker desired, running and pending counts all
zero, plus visible and in-flight counts both zero on the source queue and DLQ.
Residual or unobservable messages cannot be reported as clean, and this command
does not delete or purge messages to manufacture completion.

After interruption or an uncertain response, observe the declared effects before
requesting another approved execution:

```bash
npm run platform:shell:worker-smoke -- --reconcile
```

Reconciliation is read-only. It reports `cleaned-up` only for the complete
observed zero state, `pending` for remaining effects, or `uncertain` when a
required observation fails. Only `cleaned-up` exits successfully. A new execution
also rechecks every zero-state precondition before it sends a message. These
results describe bounded observations of the provider's approximate queue
counts; they do not establish business-message idempotency.
