# AWS CloudWatch OpenTelemetry Metrics Adapter

`@kanbien/platform-adapter-aws-observability-cloudwatch` adapts the
provider-neutral Core `Metrics` port to an OpenTelemetry metric provider which
exports to a target-reviewed private OTLP collector. The collector, not this package,
delivers the resulting metrics to AWS CloudWatch.

It is deliberately an adapter package. Routes, jobs, apps, Core contracts, and
provider-neutral platform modules do not import it.

## Files

| File | Responsibility | Why it is separate |
| --- | --- | --- |
| `src/index.ts` | Core-to-OTel translation, validated exporter construction, runtime label/cardinality enforcement, and lifecycle flush/shutdown. | AWS and OpenTelemetry implementation stays out of generic platform observability. |
| `src/configuration.ts` | Pure collector URL, region, resource and export-timing checks; composes shared metric-series validation. | Provider-specific predicates stay at the adapter boundary; series policy belongs to Platform observability. |
| `src/lifecycle-observation.ts` | Observes public reader collection, exporter callbacks and lifecycle promises once. | Collection data/results, callbacks, selectors and lifecycle outcomes stay SDK-owned; no private hooks or replacement retry policy. |
| `tests/cloudwatch-otel-adapter-runtime.test.ts` | Proves counter and timer translation, target-label rejection, threshold-aligned histogram policy, and local-collector endpoint enforcement. | It proves the adapter's contract without sending telemetry over a network. |
| `tests/cloudwatch-otel-lifecycle-runtime.test.ts` | Real SDK and local HTTP failure/success, exact records, unchanged callbacks/selectors/call counts, timeout uncertainty and dispatcher failure proof. | Local evidence is not CloudWatch delivery or live failure qualification. |
| `tests/cloudwatch-otel-adapter-boundaries.test.mjs` | Prevents imports from app and infra layers. | Provider adapters translate a provider; they do not own app meaning or CloudFormation resources. |
| `tests/run-runtime-tests.mjs` | Makes compiled Core JavaScript available to the CommonJS runtime test. | Test code must never execute workspace TypeScript through a package symlink. |
| `package.json` | Declares this adapter's OTel SDK dependencies and public package identity. | Dependencies stay visible at the provider boundary. |

## What the adapter does

The platform runtime emits a safe Core metric point. This adapter accepts it
only if it matches an explicitly supplied target metric-series catalogue.

```text
Route or job profile
       ↓ permits a metric and safe labels
Platform `Metrics` port
       ↓ emits a Core counter or timer point
This adapter
       ↓ validates the target catalogue and creates an OTel instrument
Target-reviewed private OTLP collector
       ↓ exports to the AWS CloudWatch OTel backend
CloudWatch dashboard / SLO calculation / alert
```

For example, a Core timer named
`platform.server.request_response_latency` may map to the OTel histogram
`kanbien.platform.server.request.duration`. Its metric-series policy supplies
the allowed labels and buckets. The initial target includes `300ms` and
`750ms` as exact bucket boundaries, so the later SLO policy can evaluate those
thresholds truthfully.

## Guardrails

`validateCloudWatchOtelMetricsConfiguration` returns bounded, value-free issues
without creating an SDK/exporter. It delegates generic series rules to
`@kanbien/platform-observability`. The existing runtime constructor still rejects
invalid options with `RangeError`, now carrying a validated `diagnosticRecord`.
Neither native error messages nor configured URL/region/series values appear
in that record. Unexpected SDK construction exceptions are classified separately
by target composition, never guessed to be known configuration failures.

At recording, the adapter also supplies exact local rejection records: missing
catalogue entry, kind/unit mismatch, nonfinite/negative-for-kind value and
unapproved label. Catalogue/label positions are zero-based; raw incoming names,
label keys/values and SDK errors are excluded. Existing rejection RangeErrors
and their messages remain compatible. Instrument creation and instrument
invocation have separate records: creation failure proves recording was not
attempted, whereas invocation failure leaves the effect unknown. Each SDK
failure is wrapped without its native exception text and bound to the emitting
Core port. The Platform helper does not trust copied companions or evidence
originating on another port. A normal SDK return is not export or delivery proof.

Separate optional `PlatformObservationDiagnostics` arguments observe raw public
construction, projection, instrument and lifecycle boundaries. Existing lifecycle
bindings stay argument two on the runtime factory; observations are argument
three (argument two on the direct meter adapter/views factory). Original throws,
safe wrapper messages and same-port metric provenance are unchanged. Own unknown
boundary evidence and selected source primary/eight are reported independently,
never packed into one capped envelope. Collection inspects at most eight own-data
public error entries, without invoking error accessors or custom iterators;
returned error counts remain the existing positive collection-issues meaning.
Callback nonzero results retain their existing metric-export record rather than
being called a thrown/rejected operation. Startup/runtime/shutdown context is
local to the binding. Private swallowed SDK errors remain unavailable: there is
no watchdog, private hook, retry, cancellation or new backend assurance.

- A Core metric name, kind, unit, and label set must match a reviewed target
  series exactly. The adapter rejects undeclared or mismatched points.
- The OpenTelemetry SDK applies the same label allowlist and a per-series
  cardinality cap as defence in depth.
- Timer and histogram series require strictly increasing explicit buckets.
- The exporter accepts only a task-local loopback endpoint or a bounded
  private-service-discovery hostname, on `http` port `4318` at `/v1/metrics`.
  It rejects credentials, queries, fragments, external hosts, and arbitrary
  protocols. Target composition selects the exact route and its network policy;
  an application cannot turn the adapter into an arbitrary external delivery
  channel through request or application configuration.
- The OTel reader batches export off the request and worker paths. `shutdown()`
  gives target composition a bounded final flush hook.

This package does not provision a collector, IAM permission, CloudWatch
backend, dashboard, alarm, synthetic check, or data-retention policy. Those
belong to the selected deployment target and its IaC.

## How target composition consumes it

The optional second runtime-constructor argument selects a Platform lifecycle
diagnostic binding. With no binding, the original SDK construction path is retained
and the adapter chooses no logger. With one, public `collect()` is observed without
changing its options/result/error, and exporter callbacks retain their receiver,
result identity and count. Optional aggregation/temporality selectors remain absent
when absent and retain their original exporter receiver when supplied.

Collection errors can accompany data or an empty result: only the returned errors
count and unknown completeness are reported. Failed export callbacks are observed
even when the reader absorbs them and flush resolves. Exporter versus runtime
flush/shutdown failures are separate observations, preserving the original thrown
object and existing repeated-shutdown/no-op policy. SDK timeout means unknown
completion, never cancellation. No extra collection/export/lifecycle call occurs.

Reader-internal export timeouts with no failure callback/public rejection remain
unsupported evidence; a regression explicitly proves that gap instead of inventing
a diagnosis. No global SDK logging interception, private hook, watchdog, SDK upgrade
or backend-delivery promise is introduced. Native lifecycle promises are observed
through the captured standard then intrinsic; standard thenables use assimilation.
As with local recording, hostile native constructor/species hooks and detached
implementation errors are outside portable observation guarantees.

The shared target factory retains injected construction as argument two and uses
argument three for an optional binding or explicit `false` disablement. Its default
selects one bounded independent process-owned diagnostic logger per runtime; this
is not governed by a request profile or implied by metric permission. Disabled
provider configuration constructs neither runtime nor reporter. No new environment
toggle or provider resource is introduced.
If optional target reporter setup itself fails, runtime construction continues
without that binding; only a failure of the original runtime constructor maps to
the existing construction-failure result. No recursive fallback logger is added.

The target composition root constructs the adapter with its approved region,
service resource identity, local collector endpoint, export interval, and
metric-series catalogue. It passes only the returned Core `Metrics` port to the
generic server or worker process, then owns the returned `forceFlush()` and
`shutdown()` lifecycle operations.

The canonical target policy remains under:

```text
infra/04.deploy/03.product/targets/<client>/<environment>/target-profile.yml
  observability.metric_series
  observability.slos
```

The target policy, not this README or an application profile, decides the
actual metric series, SLO thresholds, dashboard, alert response, retention,
and access audience.

## Verification

Run the governed package check:

```text
npm run platform:adapter:aws:observability:cloudwatch:check
```

That proves local adapter behaviour only. A target is operationally proven
later by a deployed public smoke request, collector export evidence, SLO query,
dashboard, controlled failure coverage, and alert-delivery verification.
