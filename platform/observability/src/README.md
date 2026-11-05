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
| `metric-diagnostics.ts` | Closed preparation, rejection, instrument-creation and invocation records, port-bound observation provenance and bounded independent reporting bindings. | Local recording evidence cannot imply export or backend delivery. |
| `metric-lifecycle-diagnostics.ts` | Separate collection issues/failure, export failure and flush/shutdown failure definitions and constructors. | Returned results, rejection, timeout and actual boundary retain different meanings without exposing metric or SDK values. |
| `boundary-definitions.ts`, `boundary-observation.ts` | Closed wrapper-failure/control definitions and optional independently selected own/source reporting. | A local observation cannot displace source primary/eight or imply remote delivery; reporting does not recursively use a failed logger. |
| `tracing.ts` | Safe trace attributes plus safe start/end wrappers around the Core tracer port. | Runtime callers can create a provider-neutral span without an unavailable tracer breaking a request. |
| `index.ts` | Approved public exports only. | Callers keep one stable import while internal source responsibilities remain easy to find. |
| `configuration.ts` | Versioned configuration/construction records and readiness configuration predicates. | Provider-neutral failures stay independent of SDK exceptions and environment variable names. |
| `metric-series-configuration.ts` | Shared metric-series policy with indexed, bounded failures. | Adapters reuse the same label, cardinality and bucket rules rather than redefining them. |

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

The write is deliberately best effort. If field normalisation or the injected
logger throws, the helper swallows that telemetry failure so a completed route
or job does not become a business failure. The file deliberately does not know
about a cloud log service, a console format, retention, a tenant’s log reader,
or security-record policy. A later target composition can choose a delivery
mechanism without making platform runtime code provider-specific.

### `metrics.ts` — small, aggregate measurements

Metrics answer aggregate questions such as “how many requests failed?” or
“how long did this route take?” This file records Core `Metrics` points and
provides the current request, job, and health helpers. It removes `undefined`
labels before the Core metric-label guard validates the remaining bounded
labels.

Metric labels must remain low-cardinality. Route or job identifiers, HTTP
status class, safe outcome, error class, and deployment version can be useful;
tenant, user, request, trace, session, token, raw URL/path, IP, and resource
identifiers must not become shared metric labels. Metric construction and the
injected provider write are deliberately best effort, so an unavailable metric
sink cannot fail work. This file does not create a metrics exporter or a tenant
analytics store.

The optional fourth helper argument supplies a stable diagnostic binding plus a
closed caller-operation identity. Name/unit/label failures come from the actual
Core predicate callback, not parsed native messages. Clock/timestamp and
unclassified preparation failures are separate; recording is not attempted
after preparation failure. A returned promise rejection is observed without
awaiting or replaying work. Adapter companions count as evidence only on the
original thrown object from the same metrics port; copied, accessor or arbitrary
schema-valid companions cannot claim a known rejection or creation phase.
Instrument creation failure means recording was not attempted; a recording
invocation failure leaves its effect unknown. Returning normally is not proof
of SDK retention, collector delivery or backend acceptance.

Failed input or recorder access retains its exact known location (`name`,
`kind`, `value`, `unit`, `label` or `recorder`) with `access-failed`; it does
not become a known validation reason or wrong-type claim before a raw value
was actually read. Original recorder-first argument ordering, two conditional
label reads and receiver binding remain. Public record lookup reads only own
data descriptors before strict parsing; rejected accessors cannot run or spend
the diagnostic budget.

Native returned promises are observed through the captured standard `then`
intrinsic, so an own shadowed `then` accessor cannot leave their rejection
unhandled. Non-native thenables retain standard assimilation. Neither path
awaits business work, replays recording or changes the helper's void return.
Portable observation still depends on usable native constructor/species hooks;
throwing hooks and arbitrary detached errors from malicious implementations
are outside this guarantee. The helper does not mutate returned promises or
install global runtime hooks. The selected synchronous adapter does not use
this asynchronous boundary.

Each shell/observer owns one `createPlatformMetricDiagnosticBinding`, independent
of the metrics port. It attempts only the first observation per closed predicate,
caller operation and approved index location, with a hard 128-attempt lifetime
limit and synchronous re-entry protection. The final attempt is reserved for a
closed suppression control after127 substantive observations when another distinct
valid observation arrives. The state is finite and scoped to
that binding; creating a fresh fourth-argument options literal does not reset it.
Distinct indexed locations can exceed the limit: subsequent evidence is
suppressed, not certified complete or delivered. Failed/unavailable reports also
consume the attempt; there is no retry or recursive fallback. A restart/new
shell creates a new budget. Capability metric permission does not imply
operational-log permission; an opted-out log path has no diagnostic binding.

### Metric lifecycle — evidence, not a delivery guarantee

The lifecycle catalog distinguishes collection results with errors from rejected
collection. Issues include a count, not raw errors or a claim of nonempty/complete
measurements. Export failure means a failed exporter callback or thrown invocation;
flush may still resolve after a callback failure. Lifecycle failures identify the
exporter versus runtime boundary, preserve unknown effect and never authorize
replay. Only a positively observed SDK timeout gets the timeout reason.

`createPlatformMetricLifecycleDiagnosticBinding` shares bounded delivery mechanics
with recording bindings but not their accepted definitions or exception-provenance
registry. Its process-owned operations are collection/export/flush/shutdown; stage
is `runtime` except shutdown. Normal operations are quiet. Binding lifetime and
unavailable-delivery suppression remain finite and are not coverage assurance.
Target selection is distinct from a route's operational-log profile opt-out.

### `tracing.ts` — safe trace mechanics, not an exporter

The Core monitoring package now supplies a provider-neutral `Tracer` port,
trace context, span names, and no-op/in-memory implementations. This file
prepares an explicit allowlist of scalar trace attributes and safely starts or
ends a span through that port. If the supplied tracer throws or has an invalid
shape, it falls back to the no-op tracer rather than changing request outcome.

The current server uses only method, stable route name, status, latency,
outcome, and a bounded error class. The worker resolves its app job's registered
observability profile, then sends only that profile's canonical capability,
action, execution context, delivery disposition, outcome, and bounded error
class fields to a trace. It may parent a span from a queue message's internal
Core trace parent. Neither path places request IDs, correlation IDs, tenant
IDs, headers, bodies, raw paths, credentials, or trace IDs into these general
trace attributes.

Using the same normalisation gateway prevents tracing from becoming a bypass
around log redaction. The code still does not choose a propagation format,
sampling policy, exporter, or storage provider; those need a later adapter,
target configuration, and operating model.

### `index.ts` — the one public doorway

`readiness-diagnostics.ts` owns the additive closed probe observations;
`readiness-observation.ts` applies them at the single invocation, completion or
deadline boundary and preserves selected upstream records. Generic fallback
codes never infer a dependency cause from timeout or missing detail. The
independent reporting helper in `diagnostics.ts` isolates synchronous and
asynchronous delivery failures without changing calls or waiting for a sink.

`index.ts` is the package barrel: the deliberate list of supported types and
functions imported through `@kanbien/platform-observability`. The barrel keeps
callers independent of internal file layout while leaving the layout itself
easy for maintainers to scan.

## Dependency direction

`normalization.ts` is foundational. `logging.ts` and `tracing.ts` use it;
`metrics.ts` is independent and relies directly on Core metric and clock
contracts. Profile declaration and field projection deliberately live in
`platform/contracts`. Persistence-owned translation lives under
`platform/persistence/src/observability/`, which may use this package but is
not a generic-observability dependency. Finally, `index.ts` exports the
supported public surface.

## What this split does not change

The split does not add a log, metric, or trace provider; alter redaction rules;
create durable audit or security records; select a cloud service; or make the
current trace-field helper a complete tracing implementation. It only makes
the existing provider-neutral responsibilities visible and preserves the
existing public package import.
