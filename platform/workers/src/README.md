# Platform Worker Source Map

This directory implements `@kanbien/platform-workers`. Consumers import the
package root; `index.ts` is a deliberate public barrel rather than the place
where worker mechanics accumulate.

| File | Owns | Why it remains separate |
| --- | --- | --- |
| `errors.ts` | Worker error codes and safe local error construction. | Queue and execution paths can return one stable error shape without coupling to one another's control flow. |
| `types.ts` | Public worker shell, in-memory queue, idempotency, delivery, and result contracts. | The package boundary remains visible without mixing it with execution logic. |
| `queue.ts` | Deterministic in-memory queue state and idempotency store. | Local test mechanics stay separate from a future provider adapter and from business job execution. |
| `worker.ts` | App mounting, job resolution, validation, lifecycle, retry/dead-letter decisions, context creation, logs, metrics, and spans. | It is the only place that adapts a delivered queue message into an app job. |
| `index.ts` | Approved public exports only. | Callers remain independent of internal source organisation. |

## Job lineage and traces

The worker preserves an incoming correlation ID for the whole logical
workflow. It gives the app job context a causation ID made from the input queue
message ID, because that message directly triggered this job execution. If the
message itself was caused by an earlier event, that earlier fact remains on the
message; it is not incorrectly substituted for the direct job cause.

Each non-idle delivery creates one `platform.worker.job` span. When the
versioned message supplies a Core `traceParent`, the span becomes its child;
otherwise it begins a new trace. The span carries only the safe job identifier,
attempt-derived retry count, latency, outcome, and bounded error class. Trace
context is neither a metric label nor an app-handler context field, and an
unavailable tracer falls back safely to no-op behavior.

Retries retain the same message, correlation, causation history, and trace
parent, while their delivery attempt increments. A retry therefore records a
new execution attempt without inventing a new business cause.
