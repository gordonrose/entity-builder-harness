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
| `diagnostics.ts` | Closed, value-free metric validation observations. | The optional constructor callback observes the current failed predicate without parsing exceptions or owning runtime reporting. |
| `signals.ts` | Signal purpose, owner, intent, and optional metric definition. | A signal explains why a measurement exists; it is not the measurement itself. |
| `tracing.ts` | Trace context, span and tracer ports, plus no-op/in-memory helpers. | Trace relationships need a portable shape before any provider adapter is chosen. |
| `validation.ts` | Private syntax and finite-value checks shared by the topic files. | It prevents duplicated validation without becoming a public utility surface. |
| `index.ts` | Deliberate public exports. | Existing package imports stay stable while the capability remains scanable. |

The trace contract does not select an exporter, a propagation format, a sampler,
or a storage backend. Provider adapters and target profiles will decide those
later. The in-memory tracer is test evidence only, not a durable record sink.

`metricName`/`metricUnit` optionally accept a `MetricValidationObserver`;
`metricLabels` accepts it as its third argument after existing label options.
The callback runs only at a failed existing name/unit/label predicate and cannot
change the original TypeError if it throws. Existing calls and accepted values
remain supported. Observations contain only field, closed reason and optional
zero-based label index, never submitted keys or values. A previously thrown
error rethrown from an input getter does not establish a current predicate.
The separate optional `CoreMonitoringDiagnosticOptions` argument observes the
existing non-metric identifier, component, health, signal, point and label-limit
predicates, and raw projection/copy/trace boundaries. `metricLabels` accepts it
as argument four, after the unchanged metric facts observer. No diagnostic fields
are read from old input or label-option objects. Guard-created TypeErrors carry
`core.monitoring.validation-rejected/v1`; arbitrary throws retain identity and are
observed as `core.monitoring.boundary-failed/v1`, never classified from their text.
Pure definitions live in `boundary-diagnostics.ts`; `observations.ts` consults
the completed explicit Core catalog only at invocation. Optional, isolated
callbacks receive own evidence and selected source primary/eight independently,
with one finite owning context. There is no automatic logger or remote sink.
Trace effects distinguish sequence advance, uncertain append, completed append,
and end-marking before replacement. No outcome, redaction or trace admission
policy, public health shape, retry, or delivery assurance is added.
