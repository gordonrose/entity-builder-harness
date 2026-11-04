# Platform Workers

The [retry configuration module](src/configuration/README.md) owns the attempt
limit and retry-delay requirements. It checks startup values before queue
selection and calculator answers before retry submission. Shared lease-duration
checks belong to Platform persistence. Valid defaults remain three attempts and
`attempt * 1000` milliseconds; the in-memory queue's scheduling limitation is
documented separately from configuration validation.

Swallowed log/trace helper faults use the selected profile's independent
observability diagnostics. Escaping observation faults retain the existing B06
Worker boundary and source primary/eight, without a duplicate generic record or
any change to retries, settlement, clocks or handler execution.

`platform/workers` runs app-declared background jobs through provider-neutral
queue mechanics. It mounts apps through public contracts, validates delivered
message payloads, applies bounded retry/dead-letter and idempotency mechanics,
and emits safe operational logs, metrics, and traces.

It does not choose SQS, another broker, a cloud SDK, a queue resource, a trace
exporter, an application job's business meaning, or a retention policy. Those
belong respectively to a future adapter/target profile, infrastructure, and
the application capability that declares the job.

The shell's `health()` aggregates registered checks through the selected
internal reporter and the health-owned catalog. It preserves generic check
observations and explicitly catalogued upstream records without changing
polling, waiting, cleanup or the returned summary. Generic health evidence is
independent from job-profile signal selection; existing job opt-outs remain.

## Responsibility map

| Path | Responsibility | Verification |
| --- | --- | --- |
| `src/errors.ts` | Stable worker failure vocabulary and local failure constructors. | `npm run platform:workers:check` |
| `src/diagnostics.ts` | Worker-owned closed definitions and explicit data-only evidence preservation/delivery. | `npm run platform:workers:check` |
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

## Runtime and process evidence

Worker shell/process options accept optional `diagnosticCatalogs` for explicit
target composition. The built-in selection includes the runtime catalog. Mount
observations select the validated app catalog snapshot before lazy output; lifecycle
callbacks deliver their own location and selected source records without a second
generic worker emission. Returned worker errors retain a validated upstream primary
and all eight possible companions. Invalid, unselected, or accessor evidence is not
trusted; a malformed primary does not discard independently valid companions.

Runtime context construction emits only its own location. The worker captures that
record and emits it, plus selected source evidence once, before settlement/retry can
supersede that failure, only when the job profile allows operational logs. A distinct
cleanup failure still gets its existing evidence. An argument projection failure before the Runtime factory
has Worker `context-input` provenance. Neither failure is relabelled as proof that
the app handler ran. Existing handlerStarted/timer population is unchanged by this
diagnostic slice; refining that historical metric interval is separate work.

The Worker catalog also owns `platform-worker.boundary-failed` version one for
context-input, the pre-context delivery clock, queue-close, process startup/shutdown
logging, and signal registration.
Those records include only closed operation/phase/boundary/effect fields, never
native messages, signals, job/message IDs, dependency values, or names. A zero-argument
queue-close call cannot distinguish property selection from invocation without
changing its native call behavior, so it reports `selection-or-invocation` explicitly.

Raw source throws retain their exact identity. Queue close still precedes lifecycle
shutdown; a queue-close throw still prevents it. Process `close(): Promise<void>`
still ignores unsuccessful shutdown Results, whose runtime observer nevertheless
delivers the failure. Signal callbacks remain void, keep their existing one-shot
guard, and retain their existing rejection behavior. Optional sinks cannot trigger
cleanup, replay source records at a broader process-close boundary, alter retry or
settlement, or replace a raw source throw.

Delivery predicates now distinguish lifecycle/job/payload/identity/claim-result
rejections through `delivery-rejected/v1`; lease contention and duplicate skips
use informational `coordination-observed/v1`. Additive `boundary-failed/v2`
identifies the actual validator, claim, lookup, completion, recording or cleanup
boundary without changing v1. In particular a thrown completion keeps the old
handler-catch settlement path, but is not labelled as a thrown app handler.
Independent location evidence and selected primary/eight are attempted before
cleanup can supersede them, only under the matched job's operational-log profile.
Unmatched admission returns safe evidence for explicit target handling; it does
not authorize unprofiled logging. The local queue optionally accepts its own
`diagnosticDefinitions`/`onDiagnostic` and preserves raw mutation-clock throws.
