# Platform Workers

`platform/workers` runs app-declared background jobs through provider-neutral
queue mechanics. It mounts apps through public contracts, validates delivered
message payloads, applies bounded retry/dead-letter and idempotency mechanics,
and emits safe operational logs, metrics, and traces.

It does not choose SQS, another broker, a cloud SDK, a queue resource, a trace
exporter, an application job's business meaning, or a retention policy. Those
belong respectively to a future adapter/target profile, infrastructure, and
the application capability that declares the job.

## Responsibility map

| Path | Responsibility | Verification |
| --- | --- | --- |
| `src/errors.ts` | Stable worker failure vocabulary and local failure constructors. | `npm run platform:workers:check` |
| `src/types.ts` | Public worker shell, queue, delivery, idempotency, durable-outbox processing, and result shapes. | `npm run platform:workers:check` |
| `src/queue.ts` | In-memory queue and idempotency implementations for deterministic local proof. | `npm run platform:workers:check` |
| `src/worker.ts` | Job execution, payload validation, lifecycle, retry/dead-letter decisions, safe telemetry, and context creation. | `npm run platform:workers:check` |
| `src/main.ts` | Provider-neutral worker-process startup, dependency construction, graceful signal shutdown, and access to the started worker shell. | `npm run platform:workers:check` |
| `src/index.ts` | Deliberate public exports only. | `npm run platform:workers:check` |

See the [source map](src/README.md) for the execution and observability model.

`main.ts` deliberately does not poll a queue. A deployment composition root
selects a provider adapter, turns received provider deliveries into declared
Core queue messages, and decides how acknowledgement or release maps to that
provider. This keeps reusable process lifecycle free of AWS, SQS URLs,
credentials, and target-specific retry policy.

## Optional durable-outbox processing

A worker shell may be explicitly configured with a provider-neutral
`PlatformProcessingStore`, lease owner, and lease duration. That mode is for a
queue whose messages came from the persistence outbox—not for every background
job by default.

Before an app handler runs, the worker verifies that its queue-message ID,
idempotency key, and payload `outboxEntryId` name the same stable obligation.
It then claims the durable processing record. A completed successful duplicate
skips the handler and reports success so target composition may acknowledge it.
A completed `terminal-failure` also skips the handler, but returns its
non-success dead-letter result so target composition can preserve provider
redrive/DLQ behaviour. A handler success records durable completion before
success is reported; a retry releases the current fenced claim; and final
failure records `terminal-failure` before the normal dead-letter result. The
target adapter remains responsible for the actual receipt handle and provider
acknowledgement/release operation.

When selected by composition, the same durable-outbox options may include a
provider-neutral persistence transition observer. The worker emits fixed,
payload-free facts such as `processing.claimed`, `processing.retry_released`,
and `processing.terminal_failure_recorded`; the observer decides, under its
profile, whether those become safe logs, metrics, or traces. This never puts
outbox IDs, tenant data, fence values, attempts, payloads, or receipt handles
into metric labels or general telemetry fields.
