# Platform Observability

`platform/observability` provides provider-neutral helpers for safe runtime
diagnostics: bounded structured-log fields, log writing, metric recording, and
safe trace-span adaptation through the Core tracer port. It is the
platform-side operational-record boundary; it does not define durable audit
evidence or provider delivery.

Error code/name projection uses finite Contracts classification options, shared
by log normalization and explicit metric/trace helpers. Only own code data is
examined; getters, names, messages and causes cannot supply a classification.
A present undeclared code is `unknown`; absent code may use an actual native
error-type group. Capability owners compose their existing classes with the
selected profile's app declarations, without claiming root-cause evidence.

It does not select a logging, metrics, tracing, SIEM, or cloud provider;
provision a sink; set retention; or decide app-specific audit and
security policy. Those responsibilities belong to approved adapters,
target-profile and infrastructure decisions, and apps/products respectively.

## Boundary

Consumers import `@kanbien/platform-observability`. Source may depend on public
Core contracts and platform observability-profile contracts. It must not import
persistence, app or infrastructure code, cloud SDKs, or provider implementation
vocabulary. The package boundary test protects that dependency direction.

## Responsibility map

| Path | Responsibility | Verification |
| --- | --- | --- |
| `src/normalization.ts` | Redacts, bounds, and converts unknown log and trace values into safe JSON-shaped fields. | `npm run platform:observability:check` |
| `src/logging.ts` | Adapts a Core logger so normal runtime writes pass through the normalisation boundary. | `npm run platform:observability:check` |
| `src/metrics.ts` | Records provider-neutral metric points and the current request, job, and health helper measurements. | `npm run platform:observability:check` |
| `src/metric-diagnostics.ts` | Closed local-recording evidence, same-port provenance and independent finite-budget diagnostic bindings. | `npm run platform:observability:check` |
| `src/boundary-definitions.ts`, `src/boundary-observation.ts` | Pure wrapper-boundary/control definitions and selected independent own/source delivery through the existing reporter. | `npm run platform:observability:check` |
| `src/metric-lifecycle-diagnostics.ts` | Closed collection issues/failure, export failure and flush/shutdown failure contracts with explicit uncertainty. | `npm run platform:observability:check` |
| `src/tracing.ts` | Prepares bounded safe trace attributes and safely adapts Core `Tracer` spans. | `npm run platform:observability:check` |
| `src/index.ts` | Deliberate public package exports only. | `npm run platform:observability:check` |
| `src/configuration.ts` | Closed configuration/construction diagnostics, bounded issue merging and readiness identity/timing validation. | `npm run platform:observability:check` |
| `src/metric-series-configuration.ts` | Provider-neutral series identities, kinds, labels, cardinality and histogram-bucket policy. | `npm run platform:observability:check` |
| `src/readiness-diagnostics.ts` | Closed probe configuration, returned not-ready, invocation, rejection and observed-deadline meanings. | `npm run platform:observability:check` |
| `src/readiness-observation.ts` | One bounded probe, closed readiness event, internal evidence and gauge without cancellation or cause inference. | `npm run platform:observability:check` |

The [source map](src/README.md) explains why the topics remain separate and
how their dependencies flow. The server and worker now create safe
provider-neutral spans; a worker may use the Core trace parent carried in its
queue message without exposing it to application handlers. The topic files are
internal organisation, not public subpath APIs. A tracing adapter is still
future work: no provider, exporter, external propagation format, sampling
policy, retention decision, or trace store is selected here.

## Configuration diagnostics

`validatePlatformMetricSeries` and `validatePlatformReadinessConfiguration`
return all independently provable issues without constructing a runtime.
`observability.configuration-invalid` version 1 carries logical setting/reason
pairs, not supplied configuration values. `index` locates a series;
`attributeIndex` locates a label or bucket within it; `relatedIndex` locates
the first conflicting series/label or the preceding bucket. All are zero-based.
Issues remain in deterministic check order, with at most 32 retained and an
explicit `truncated` flag when additional issues exist. Dependent comparisons
run only when their participating values passed their individual checks.

The AWS adapter owns collector URL and region checks. Target composition owns
environment bindings, provider selection, numeric conversion and delivery-boundary
selection. The target validates configuration before constructing its exporter
or database pool. Historical accepted text/numeric spellings are preserved.
Unexpected construction exceptions instead produce
`observability.runtime-construction-failed` with an unclassified cause and
unassessed effects; native exception text is never diagnostic evidence.

The code-owned definitions generate `contracts/diagnostics.v1.json` for strict
cross-language readers. A configuration success establishes syntax/policy
acceptance only—not collector availability, backend delivery or alerting.
Local recording diagnostics now distinguish preparation, exact catalogue/point
rejection, instrument creation and invocation failure. Existing three-argument
helpers remain supported; an optional fourth argument carries the independent
reporter binding/location. Per-binding deduplication and a 128-attempt lifetime
budget bound failure reporting; suppression is not diagnostic completeness.
The final budget slot is reserved:127 substantive attempts are followed by one
`observability.diagnostic-reporting-suppressed` control when another distinct
valid observation arrives; no further attempts occur. Attempted is not delivered.
Server, worker, persistence and readiness consumers select bindings and preserve
operational-log opt-outs even where metrics are enabled. See the source map for
provenance, effect and isolation guarantees.

Log/trace/metric/readiness helpers accept additive local
`PlatformObservationDiagnostics` (reporter, optional explicit definitions and
context). `reportPlatformObservationBoundary` independently attempts its closed
location and selected source primary/eight; `reportPlatformObservationSources`
retains sources when an existing producer already owns the precise record.
Optional selection failures retain built-in Core/Observability evidence. No
missing reporter activates logging, and the failed sink is never its own fallback.
Raw fallback/projection throws and getter/call ordering remain unchanged.

Reporter `written` means only synchronous local port handoff. A returned promise
or thenable is rejection-isolated and returns `unavailable`, not a claim of
completed or remote delivery. The provenance-aware safe logger signals this
unconfirmed asynchronous handoff to its reporter without recursively logging it.

## Readiness diagnostics

The observer distinguishes invalid timeout type/finite/integer/positive checks,
an actual returned not-ready result, a synchronous throw, asynchronous rejection
and an observed deadline. A deadline leaves the dependency operation outcome
unknown and does not cancel it. Approved dependency-returned codes remain in
the closed event. An absent/unapproved code receives the observer's own
classification; the configured default remains validated under the existing
policy but is no longer treated as evidence of a transport failure.

The independently selected reporter receives the generic observation plus
actual upstream primary/related records. No diagnostic detail enters metric
labels or the event envelope. Optional reporting is isolated from probe work,
including native promises with a shadowed `then` and ordinary thenables;
usable native constructor/species hooks remain the portable assumption. Sink
absence/rejection is not proof that records were delivered. Callers retain
cadence, staleness and scheduling ownership.

After a deadline observation, inspect the configured budget and actual probe
evidence without assuming cancellation or replay authority. A configuration
observation identifies the timeout predicate; a thrown/rejected invocation
requires that dependency's own evidence. A returned not-ready result only proves
its returned state. Check reporter catalog selection and actual output when
delivery rejects a record.

## Metric lifecycle diagnostics

Five additive identities cover four families: collection issues versus failed
collection are separate schemas so a returned result cannot be confused with
rejection. A returned error count does not prove that any measurements were
returned, lost or complete. Export failure distinguishes the failed callback
from an invocation throw. Flush and shutdown failures name the actual exporter
or runtime boundary and distinguish rejection, synchronous throw and a positively
observed SDK timeout. Effects remain unknown; timeout never proves cancellation.

`createPlatformMetricLifecycleDiagnosticBinding` reuses the existing first-per-
predicate/location deduplication, 128-attempt lifetime limit and reentry isolation.
This binding accepts only lifecycle definitions; local recording provenance
continues to accept only recording definitions and the same error/port. Failed
delivery spends the attempt, suppression is not completeness, and no retry or
metric fallback is introduced. Background delivery uses the additive `runtime`
stage; shutdown uses `shutdown`. Targets select process-owned lifecycle evidence
independently from route observability profiles. Generic adapters remain silent
without an explicit binding.

Definitions allow no raw measurements, names, attributes, endpoints or error
objects. Successful SDK calls do not establish backend delivery. Some SDK reader
errors/timeouts are absorbed internally without a public failure observation;
these remain a coverage gap, not a diagnosis manufactured from log text. Remote
collector/backend assurance, general buffering/retry/coverage design and live
proof remain deferred in the existing telemetry follow-on plan. No series,
collector setting, lifecycle policy or deployment resource is added here.
