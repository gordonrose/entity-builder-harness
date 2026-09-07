# Platform Observability Source Map

This directory implements `@kanbien/platform-observability`. Consumers use the
package root rather than importing these topic files directly. The
[package README](../README.md) owns the public boundary, dependency direction,
and verification route.

`index.ts` is a deliberate public barrel. It re-exports the existing supported
API after the source split, but does not make every local helper a permanent
external promise.

| File | Owns | Why the boundary matters |
| --- | --- | --- |
| `normalization.ts` | Safe JSON-shaped fields, redaction, size/depth bounds, circular-value handling, and bounded error facts. | Logging and tracing need the same safety rule without either becoming a provider implementation. |
| `logging.ts` | Safe Core-logger adaptation and structured runtime log writes. | It sends already-normalised facts to an injected logger; it does not select or configure a sink. |
| `metrics.ts` | Metric recording plus request, job, health, and elapsed-time helpers. | Metric identity and low-cardinality labels stay separate from log-value normalisation and trace attributes. |
| `tracing.ts` | Safe trace-attribute preparation. | A future span/exporter adapter can receive bounded attributes without tracing mechanics leaking into every runtime caller. |
| `index.ts` | Approved public exports only. | Callers keep one stable import while internal source responsibilities remain easy to find. |

## Detailed guide to the files

### `normalization.ts` — the safety gateway for unknown values

Runtime values are often unsafe to export unchanged: they can contain headers,
credentials, circular objects, enormous strings, buffers, provider objects, or
unexpected nested data. This file converts those values into bounded
JSON-shaped facts, redacts known sensitive key names, and reports only a small
error shape (`name` and an optional string `code`).

It does not decide whether an app action is auditable, store an audit event,
or choose where an operational record goes. It is a reusable safety mechanism
for the logging and tracing helpers in this package.

### `logging.ts` — safe writing, not log-provider selection

This file accepts the Core `Logger` port and makes sure normal runtime writes
cross the normalisation gateway. `createPlatformSafeLogger` wraps an existing
logger; `writePlatformLog` handles the common one-off structured write.

The file deliberately does not know about a cloud log service, a console
format, retention, a tenant’s log reader, or security-record policy. A later
target composition can choose a delivery mechanism without making platform
runtime code provider-specific.

### `metrics.ts` — small, aggregate measurements

Metrics answer aggregate questions such as “how many requests failed?” or
“how long did this route take?” This file records Core `Metrics` points and
provides the current request, job, and health helpers. It removes `undefined`
labels before the Core metric-label guard validates the remaining bounded
labels.

Metric labels must remain low-cardinality. Route or job identifiers, HTTP
status class, safe outcome, error class, and deployment version can be useful;
tenant, user, request, trace, session, token, raw URL/path, IP, and resource
identifiers must not become shared metric labels. This file does not create a
metrics exporter or a tenant analytics store.

### `tracing.ts` — prepared attributes before a tracing engine exists

The current tracing seam prepares a safe attribute object for a future tracer.
It does not create a trace ID, start a span, determine sampling, or export a
span. Those need a selected tracing contract, adapter, target configuration,
and operating model.

Using the same normalisation gateway prevents tracing from becoming a bypass
around log redaction. Trace attributes need the same data minimisation and
bounded-value discipline as structured logs.

### `index.ts` — the one public doorway

`index.ts` is the package barrel: the deliberate list of supported types and
functions imported through `@kanbien/platform-observability`. The barrel keeps
callers independent of internal file layout while leaving the layout itself
easy for maintainers to scan.

## Dependency direction

`normalization.ts` is foundational. `logging.ts` and `tracing.ts` use it;
`metrics.ts` is independent and relies directly on Core metric and clock
contracts. Finally, `index.ts` exports the supported public surface. Internal
relative imports stay inside this package, while external source imports are
limited to public Core modules.

## What this split does not change

The split does not add a log, metric, or trace provider; alter redaction rules;
create durable audit or security records; select a cloud service; or make the
current trace-field helper a complete tracing implementation. It only makes
the existing provider-neutral responsibilities visible and preserves the
existing public package import.
