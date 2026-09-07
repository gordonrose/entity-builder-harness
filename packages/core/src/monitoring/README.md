# Core Monitoring Source Map

`@kanbien/core/monitoring` defines the portable vocabulary for health checks,
metrics, signal definitions, and traces. Its public entry point remains
`@kanbien/core/monitoring`; these files are internal organisation, not
additional supported import paths.

| File | Owns | Why it is separate |
| --- | --- | --- |
| `identifiers.ts` | Branded monitoring, metric, signal, trace, and span names plus component references. | Stable names need one consistent syntax without becoming a runtime host. |
| `health.ts` | Health-check types, results, metadata copying, and fixed test checks. | Health probes have different semantics from metrics and traces. |
| `metrics.ts` | Metric points, the `Metrics` port, low-cardinality label policy, and `noopMetrics`. | Metric cardinality is a distinct operational-safety concern. |
| `signals.ts` | Signal purpose, owner, intent, and optional metric definition. | A signal explains why a measurement exists; it is not the measurement itself. |
| `tracing.ts` | Trace context, span and tracer ports, plus no-op/in-memory helpers. | Trace relationships need a portable shape before any provider adapter is chosen. |
| `validation.ts` | Private syntax and finite-value checks shared by the topic files. | It prevents duplicated validation without becoming a public utility surface. |
| `index.ts` | Deliberate public exports. | Existing package imports stay stable while the capability remains scanable. |

The trace contract does not select an exporter, a propagation format, a sampler,
or a storage backend. Provider adapters and target profiles will decide those
later. The in-memory tracer is test evidence only, not a durable record sink.
