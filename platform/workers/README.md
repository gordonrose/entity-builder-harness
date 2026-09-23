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
| `src/types.ts` | Public worker shell, queue, delivery, idempotency, and result shapes. | `npm run platform:workers:check` |
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
