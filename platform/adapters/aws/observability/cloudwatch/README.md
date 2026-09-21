# AWS CloudWatch OpenTelemetry Metrics Adapter

`@kanbien/platform-adapter-aws-observability-cloudwatch` adapts the
provider-neutral Core `Metrics` port to an OpenTelemetry metric provider which
exports to a task-local OTLP collector. The collector, not this package,
delivers the resulting metrics to AWS CloudWatch.

It is deliberately an adapter package. Routes, jobs, apps, Core contracts, and
provider-neutral platform modules do not import it.

## Files

| File | Responsibility | Why it is separate |
| --- | --- | --- |
| `src/index.ts` | Catalogue validation, Core-to-OTel translation, OTLP exporter configuration, label/cardinality enforcement, and lifecycle flush/shutdown. | The implementation is AWS and OpenTelemetry specific, so it stays out of generic platform observability. |
| `tests/cloudwatch-otel-adapter-runtime.test.ts` | Proves counter and timer translation, target-label rejection, threshold-aligned histogram policy, and local-collector endpoint enforcement. | It proves the adapter's contract without sending telemetry over a network. |
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
Task-local OTLP collector
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

- A Core metric name, kind, unit, and label set must match a reviewed target
  series exactly. The adapter rejects undeclared or mismatched points.
- The OpenTelemetry SDK applies the same label allowlist and a per-series
  cardinality cap as defence in depth.
- Timer and histogram series require strictly increasing explicit buckets.
- The exporter accepts only `http://127.0.0.1:4318/v1/metrics`. An application
  cannot turn the metrics adapter into an arbitrary external data-delivery
  channel through an environment value.
- The OTel reader batches export off the request and worker paths. `shutdown()`
  gives target composition a bounded final flush hook.

This package does not provision a collector, IAM permission, CloudWatch
backend, dashboard, alarm, synthetic check, or data-retention policy. Those
belong to the selected deployment target and its IaC.

## How target composition consumes it

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
