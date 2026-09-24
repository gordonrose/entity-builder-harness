# Platform Worker Source Map

This directory implements `@kanbien/platform-workers`. Consumers import the
package root; `index.ts` is a deliberate public barrel rather than the place
where worker mechanics accumulate.

| File | Owns | Why it remains separate |
| --- | --- | --- |
| `errors.ts` | Worker error codes and safe local error construction. | Queue and execution paths can return one stable error shape without coupling to one another's control flow. |
| `types.ts` | Public worker shell, in-memory queue, idempotency, durable-outbox processing, delivery, and result contracts. | The package boundary remains visible without mixing it with execution logic. |
| `queue.ts` | Deterministic in-memory queue state and idempotency store. | Local test mechanics stay separate from a future provider adapter and from business job execution. |
| `worker.ts` | App mounting, job resolution, validation, lifecycle, retry/dead-letter decisions, context creation, logs, metrics, and spans. | It is the only place that adapts a delivered queue message into an app job. |
| `main.ts` | Long-running worker-process composition, config source creation, signal handling, and orderly shutdown. | Provider-neutral process lifecycle remains distinct from a selected queue provider and its acknowledgement mechanics. |
| `index.ts` | Approved public exports only. | Callers remain independent of internal source organisation. |

## Job lineage and traces

The worker preserves an incoming correlation ID for the whole logical
workflow. It gives the app job context a causation ID made from the input queue
message ID, because that message directly triggered this job execution. If the
message itself was caused by an earlier event, that earlier fact remains on the
message; it is not incorrectly substituted for the direct job cause.

For a job with an observability profile, each non-idle delivery first resolves
that profile from the mounted registry. The worker emits an operational log,
metric counter, declared latency measurements, and/or a `platform.worker.job`
span only when that signal is permitted. Each emitted field is projected through
the profile's relevant allowlist; the worker cannot add its raw message type,
payload, tenant, message ID, retry count, delay, or error object by default.
An explicit profile opt-out emits no capability telemetry. An unregistered
queue message also has no app-owned profile, so it is dead-lettered without
pretending to be a known capability.

When the profile permits a trace and the versioned message supplies a Core
`traceParent`, the span becomes its child; otherwise it begins a new trace.
Trace context is neither a metric label nor an app-handler context field. A
failing logger, metrics sink, or tracer is best effort and cannot turn a
completed handler into a worker failure.

Retries retain the same message, correlation, causation history, and trace
parent, while their delivery attempt increments. A retry therefore records a
new execution attempt without inventing a new business cause.

## Durable outbox mode

When composition explicitly supplies `durableOutboxProcessing`, `worker.ts`
uses `platform/persistence` only as a provider-neutral processing-store port.
It requires the Core message ID, idempotency key, and payload
`outboxEntryId` to match. This prevents a provider delivery ID from silently
becoming the durable business-processing identity.

The worker claims before the app handler, marks success before returning a
successful delivery result, releases a current claim before the existing retry
path, and records terminal failure before the existing dead-letter result. A
completed success can return success without running the handler again; a
completed terminal failure returns the existing non-success dead-letter result
without running it again. The generic worker still does not receive,
acknowledge, or release a provider message; target composition retains those
transport operations.

An optional persistence transition observer can receive only fixed,
payload-free durable-processing facts. A Core correlation reference may link
its logs, while existing trace context may parent its spans; neither is emitted
as a metric label or general trace attribute. The observer does not receive an
outbox ID, tenant, fence, attempt, payload, receipt handle, or provider
response. `platform/observability` turns those facts into profile-governed
signals when target composition supplies its observer; the worker retains no
cloud telemetry implementation.
