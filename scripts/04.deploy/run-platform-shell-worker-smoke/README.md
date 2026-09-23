<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.run-platform-shell-worker-smoke.readme
version: 4
status: active
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
one-message policy. Its live mode is deliberately unavailable without both
`--execute` and `--approve-live-worker-smoke`, plus a current approved staging
operation.

When explicitly run, it confirms the source queue, DLQ, and worker service are
empty/dormant; sends one harmless `platform-smoke.rebuild` envelope; sets only
the worker service to one task; waits for bounded settlement; keeps the task
alive for 75 seconds; sends one second harmless envelope; waits for its
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
