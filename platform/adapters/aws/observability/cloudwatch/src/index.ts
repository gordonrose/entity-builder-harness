import type { Attributes, Counter, Gauge, Histogram } from "@opentelemetry/api"; // Use the OpenTelemetry instrument contracts without exposing them to application code.
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-proto"; // Send metric batches to the task-local collector using OTLP over HTTP/protobuf.
import { resourceFromAttributes } from "@opentelemetry/resources"; // Attach stable deployment identity to every exported metric.
import { // Import the SDK pieces that construct bounded metric aggregation and lifecycle behaviour.
  AggregationType, // Select explicit histogram buckets for latency distributions.
  createAllowListAttributesProcessor, // Drop any attribute that is not approved by the target metric catalogue.
  MeterProvider, // Own a local meter provider instead of mutating a global process singleton.
  PeriodicExportingMetricReader, // Batch and periodically export metrics outside the request path.
  type ViewOptions, // Describe histogram, attribute, and cardinality policy to the SDK.
} from "@opentelemetry/sdk-metrics"; // Keep provider SDK use inside the AWS observability adapter.
import { capturePlatformMetricDiagnostic, platformObservabilityDiagnosticCatalog, observabilityConfigurationRecord, validatePlatformMetricSeries, type PlatformMetricSeries,
  attachPlatformMetricDiagnostic, metricRejectionRecord, metricCreationRecord, metricRecordingRecord } from "@kanbien/platform-observability";
import { reportPlatformObservationBoundary, type PlatformMetricLifecycleDiagnosticBinding, type PlatformObservationDiagnostics, type PlatformObservationBoundaryDetail } from "@kanbien/platform-observability";
import { ObservedPeriodicMetricReader, observeMetricExporter, observeMetricLifecycle, metricObservationContext, CloudWatchConstructionObservation } from "./lifecycle-observation";
import { validateCloudWatchOtelMetricsConfiguration } from "./configuration";
export { validateCloudWatchOtelMetricsConfiguration } from "./configuration";
import type { MetricKind, MetricPoint, Metrics } from "@kanbien/core/monitoring"; // Implement the existing provider-neutral Core metrics port.
import { captureDiagnosticRecord, requireDiagnosticRecord } from "@kanbien/core/diagnostics";

export interface CloudWatchOtelMetricSeries extends PlatformMetricSeries {}

export interface CloudWatchOtelMetricsOptions { // Describe the target-owned runtime settings needed to emit CloudWatch OTel metrics.
  readonly endpoint: string; // Require the task-local collector's full OTLP metrics endpoint URL.
  readonly region: string; // Attach the target-selected AWS region as a resource attribute without hardcoding an environment.
  readonly serviceName: string; // Attach the stable target service identity as an OTel resource attribute.
  readonly serviceVersion: string; // Attach the deployed source/image version without using it as a metric label.
  readonly deploymentEnvironment: string; // Attach the named deployment environment as a resource attribute.
  readonly exportIntervalMs: number; // Bound how frequently the SDK exports buffered aggregates.
  readonly exportTimeoutMs: number; // Bound a single export attempt so shutdown and failure remain controlled.
  readonly series: readonly CloudWatchOtelMetricSeries[]; // Supply the complete reviewed target catalogue before serving traffic.
}

export interface CloudWatchOtelMetricsRuntime { // Return the Core-facing metrics port together with explicit lifecycle controls.
  readonly metrics: Metrics; // Give server and worker composition the provider-neutral dependency they already understand.
  forceFlush(): Promise<void>; // Let a controlled test or shutdown path request export of current aggregates.
  shutdown(): Promise<void>; // Stop the reader and attempt a final bounded flush during process shutdown.
}

export interface CloudWatchOtelMetricMeter { // Define the small OTel meter subset needed for deterministic adapter tests.
  createCounter(name: string, options: { readonly description: string; readonly unit: string }): Counter; // Create a monotonic occurrence instrument.
  createGauge(name: string, options: { readonly description: string; readonly unit: string }): Gauge; // Create a current-value instrument when a target explicitly permits one.
  createHistogram(name: string, options: { readonly description: string; readonly unit: string }): Histogram; // Create a distribution instrument for timers and histograms.
}

export const adapterMetadata = { // Publish scanable identity for target composition and adapter review.
  provider: "aws", // Identify AWS as the selected target provider.
  capability: "observability", // Identify ordinary operational telemetry as the capability boundary.
  implementation: "cloudwatch-otel", // Name the CloudWatch OpenTelemetry delivery path.
  packageName: "@kanbien/platform-adapter-aws-observability-cloudwatch", // Publish the stable workspace package identity.
} as const; // Preserve literals for deterministic metadata checks.

export function createCloudWatchOtelMetricsRuntime( // Construct the production OTLP metric runtime owned by a target composition root.
  options: CloudWatchOtelMetricsOptions, // Receive reviewed target configuration rather than reading an app-owned configuration directly.
  diagnostics?: PlatformMetricLifecycleDiagnosticBinding,
  observations?: PlatformObservationDiagnostics,
): CloudWatchOtelMetricsRuntime { // Return the Core port plus lifecycle operations needed by the target process.
  const construction = new CloudWatchConstructionObservation(observations);
  return construction.run(() => {
  construction.at("input-projection", "record", () => validateCloudWatchOtelMetricsOptions(options), "not-attempted"); // Fail before traffic when the target configuration is malformed or unsafe.
  const exporter = construction.at("exporter-construction", undefined, () => new OTLPMetricExporter({ url: construction.at("input-projection", "endpoint", () => options.endpoint) })); // Configure one metric-only exporter to the reviewed private collector endpoint.
  const readerOptions = { // Keep SDK scheduling and aggregation options unchanged.
    exporter: diagnostics === undefined && observations === undefined ? exporter : observeMetricExporter(exporter, diagnostics, observations, construction),
    exportIntervalMillis: construction.at("input-projection", "export-interval", () => options.exportIntervalMs), // Use the reviewed target batching interval.
    exportTimeoutMillis: construction.at("input-projection", "export-timeout", () => options.exportTimeoutMs), // Bound one exporter attempt so lifecycle shutdown has a limit.
    cardinalityLimits: { default: construction.at("reader-construction", "series", () => maxCardinalityLimit(options.series)) }, // Apply a defensive reader-level cap in addition to each series view.
    maxExportBatchSize: construction.at("input-projection", "series", () => options.series.length), // Prevent a first target with only fixed series from creating unbounded export batches.
  };
  const reader = construction.at("reader-construction", undefined, () => diagnostics === undefined && observations === undefined ? new PeriodicExportingMetricReader(readerOptions) : new ObservedPeriodicMetricReader(readerOptions, diagnostics, observations));
  const provider = construction.at("provider-construction", undefined, () => new MeterProvider({ // Create an isolated SDK provider so this adapter never changes a process-global OTel provider.
    resource: resourceFromAttributes({ // Attach stable resource attributes instead of putting them on every metric series.
      "service.name": construction.at("input-projection", "service-name", () => options.serviceName), // Identify the service that produced the metrics.
      "service.version": construction.at("input-projection", "service-version", () => options.serviceVersion), // Identify the deployed build or revision.
      "deployment.environment.name": construction.at("input-projection", "environment", () => options.deploymentEnvironment), // Identify the bounded deployment environment.
      "cloud.provider": "aws", // State the selected cloud provider as resource context.
      "cloud.region": construction.at("input-projection", "region", () => options.region), // Record the target-selected AWS region as resource context.
    }), // Finish the safe target resource attributes.
    readers: [reader], // Attach the periodic exporter to this provider only.
    views: cloudWatchOtelMetricViews(construction.at("input-projection", "series", () => options.series)), // Enforce each series' labels, cardinality cap, and histogram buckets in the SDK.
  })); // Finish the isolated provider construction.
  const meter = construction.at("meter-selection", undefined, () => provider.getMeter("kanbien.platform", construction.at("input-projection", "service-version", () => options.serviceVersion))); // Create the one instrumentation scope used by this adapter.

  return { // Return the Core-facing adapter and lifecycle operations to the target composition root.
    metrics: buildCloudWatchOtelMetrics({ meter, series: construction.at("input-projection", "series", () => options.series) }, observations, construction), // Adapt approved Core points to OTel instruments.
    forceFlush: () => diagnostics === undefined && observations === undefined ? provider.forceFlush({ timeoutMillis: options.exportTimeoutMs })
      : runtimeLifecycle(provider, options, "flush", diagnostics, observations),
    shutdown: () => diagnostics === undefined && observations === undefined ? provider.shutdown({ timeoutMillis: options.exportTimeoutMs })
      : runtimeLifecycle(provider, options, "shutdown", diagnostics, observations),
  }; // Keep lifecycle ownership with target composition, not routes or app handlers.
  });
}

export function createCloudWatchOtelMetrics( // Adapt Core metric points to a supplied OpenTelemetry meter.
  options: { readonly meter: CloudWatchOtelMetricMeter; readonly series: readonly CloudWatchOtelMetricSeries[] }, // Allow deterministic tests to use a small in-memory meter double.
  observations?: PlatformObservationDiagnostics,
): Metrics { // Return only the established provider-neutral Core metrics port.
  const construction = new CloudWatchConstructionObservation(observations);
  return construction.run(() => buildCloudWatchOtelMetrics(options, observations, construction));
}
function buildCloudWatchOtelMetrics(options: { readonly meter: CloudWatchOtelMetricMeter; readonly series: readonly CloudWatchOtelMetricSeries[] },
  observations: PlatformObservationDiagnostics | undefined, construction: CloudWatchConstructionObservation): Metrics {
  construction.at("port-construction", "series", () => validateMetricSeries(options.series)); // Reject ambiguous or unsafe catalogue entries before the first metric is recorded.
  const seriesBySourceName = construction.at("port-construction", "series", () => new Map(options.series.map((series, index) => [series.sourceName, { series, index }]))); // Resolve exact approved identities and their safe catalogue positions.
  const instruments = construction.at("port-construction", undefined, () => new Map<string, Counter | Gauge | Histogram>()); // Reuse one SDK instrument per approved OTel identity and avoid per-request construction.
  const runtimeObservations = metricObservationContext(observations, "runtime");

  const metrics: Metrics = { // Bind trusted observations to this exact Core port.
    record: (point) => { // Translate one provider-neutral point synchronously into an SDK instrument recording.
      let currentFailure: unknown = {};
      let field: PlatformObservationBoundaryDetail["field"] = "name";
      try {
      const matched = seriesBySourceName.get(String(point.name)); // Find the exact target-approved source metric identity.
      if (matched === undefined) { // Reject an unreviewed point rather than inventing an exporter series.
        throw known(attachPlatformMetricDiagnostic(metrics, new RangeError("CloudWatch OTel metric is not declared by the target catalogue."), capturePlatformMetricDiagnostic(() => metricRejectionRecord("undeclared-metric"))));
      }
      const { series, index } = matched;
      field = "record";
      assertPointMatchesSeries(point, series, metrics, index, known); // Reject mismatched kind, unit, numeric value, or label shape.
      field = "attributes";
      const attributes = point.labels ?? {}; // Use only Core-validated scalar labels after the series approval check.
      field = "series";
      let instrument = instruments.get(series.sourceName);
      if (instrument === undefined) {
        try { instrument = createInstrument(options.meter, series); }
        catch (error) {
          reportPlatformObservationBoundary(runtimeObservations, { operation: "metric-instrument-creation", phase: "instrument-creation", field: "meter", reason: "threw", effect: "unknown" }, error);
          throw known(attachPlatformMetricDiagnostic(metrics, new Error("Metric instrument creation did not complete."), capturePlatformMetricDiagnostic(() => metricCreationRecord(index))));
        }
      }
      instruments.set(series.sourceName, instrument); // Retain the instrument so future requests do not rebuild SDK state.
      try { recordInstrument(instrument, series.sourceKind, point.value, attributes); }
      catch (error) {
        reportPlatformObservationBoundary(runtimeObservations, { operation: "metric-recording", phase: "instrument-recording", field: "record", reason: "threw", effect: "unknown" }, error);
        throw known(attachPlatformMetricDiagnostic(metrics, new Error("Metric recording invocation did not complete."), capturePlatformMetricDiagnostic(() => metricRecordingRecord(index))));
      }
      } catch (error) {
        if (error !== currentFailure) reportPlatformObservationBoundary(runtimeObservations, { operation: "metric-recording", phase: "input-projection", field, reason: "threw", effect: "not-attempted" }, error);
        throw error;
      }
      function known<T>(error: T): T { currentFailure = error; return error; }
    }, // Keep all provider work behind the Core metrics port.
  }; // End the Core metrics adapter implementation.
  return metrics;
}

export function cloudWatchOtelMetricViews( // Build SDK views that enforce target catalogue policy even if an instrument is misused later.
  series: readonly CloudWatchOtelMetricSeries[], // Read the complete reviewed metric-series catalogue.
  observations?: PlatformObservationDiagnostics,
): ViewOptions[] { // Return one explicit view per approved metric series.
  const construction = new CloudWatchConstructionObservation(observations);
  return construction.run(() => construction.at("port-construction", "series", () => {
  validateMetricSeries(series); // Ensure invalid catalogue data cannot become SDK configuration.
  return series.map((definition) => ({ // Create the view that owns one stable OTel instrument identity.
    instrumentName: definition.instrumentName, // Select only this exact instrument, never a wildcard collection.
    attributesProcessors: [createAllowListAttributesProcessor([...definition.allowedLabelNames])], // Drop attributes outside the reviewed target allowlist as defence in depth.
    aggregationCardinalityLimit: definition.cardinalityLimit, // Bound in-process series memory for this metric identity.
    ...(isDistributionKind(definition.sourceKind) // Apply special histogram policy only to timers and histograms.
      ? { aggregation: { type: AggregationType.EXPLICIT_BUCKET_HISTOGRAM, options: { boundaries: [...(definition.histogramBucketBoundaries ?? [])] } } } // Preserve threshold-aligned buckets for latency/SLO evaluation.
      : {}), // Leave counters and gauges on their standard compatible aggregation.
  })); // Return a deterministic view per catalogue entry.
  }));
}

function createInstrument( // Construct the OTel instrument that exactly matches one Core metric kind.
  meter: CloudWatchOtelMetricMeter, // Receive the target-local meter selected by composition.
  series: CloudWatchOtelMetricSeries, // Read the already validated approved metric mapping.
): Counter | Gauge | Histogram { // Return the matching synchronous SDK instrument.
  const options = { description: series.description, unit: series.sourceUnit }; // Keep the configured meaning and unit attached to the OTel instrument.
  if (series.sourceKind === "counter") { // Map a Core counter to an OTel monotonic counter.
    return meter.createCounter(series.instrumentName, options); // Create the counter once for all matching points.
  }
  if (series.sourceKind === "gauge") { // Map a Core gauge to an OTel synchronous gauge.
    return meter.createGauge(series.instrumentName, options); // Record each current-value observation directly.
  }
  return meter.createHistogram(series.instrumentName, options); // Map timers and Core histograms to a real OTel distribution instrument.
}

function recordInstrument( // Record an already validated point with the matching OTel synchronous instrument operation.
  instrument: Counter | Gauge | Histogram, // Receive the instrument previously created for the approved series.
  kind: MetricKind, // Read the Core semantic kind that selected the instrument.
  value: number, // Record the finite value already checked against the series.
  attributes: Attributes, // Attach only Core scalar labels that passed the target allowlist check.
): void { // Finish the provider translation without a network call on the work path.
  if (kind === "counter") { // Counters accumulate occurrences or quantities.
    (instrument as Counter).add(value, attributes); // Add the non-negative value to the monotonic OTel counter.
    return; // Prevent a counter from being handled as a gauge or histogram.
  }
  if (kind === "gauge") { // Gauges represent the most recent current value.
    (instrument as Gauge).record(value, attributes); // Record the current scalar observation.
    return; // Prevent a gauge from being handled as a histogram.
  }
  (instrument as Histogram).record(value, attributes); // Record timers and histograms into the explicit target-controlled distribution.
}

function assertPointMatchesSeries( // Validate that a Core point exactly fits the target-approved series definition.
  point: MetricPoint, // Receive the provider-neutral point supplied by platform runtime code.
  series: CloudWatchOtelMetricSeries, // Receive the resolved reviewed series mapping.
  metrics: Metrics,
  seriesIndex: number,
  known: <T>(error: T) => T,
): void { // Throw a safe configuration-style error before any provider recording occurs.
  if (point.kind !== series.sourceKind) { // Prevent a counter and a timer from sharing an OTel identity.
    throw known(attachPlatformMetricDiagnostic(metrics, new RangeError("CloudWatch OTel metric kind does not match its target catalogue definition."), capturePlatformMetricDiagnostic(() => metricRejectionRecord("kind-mismatch", seriesIndex))));
  }
  if (String(point.unit) !== series.sourceUnit) { // Prevent values with different units from being aggregated together.
    throw known(attachPlatformMetricDiagnostic(metrics, new RangeError("CloudWatch OTel metric unit does not match its target catalogue definition."), capturePlatformMetricDiagnostic(() => metricRejectionRecord("unit-mismatch", seriesIndex))));
  }
  // Keep the original short-circuit predicate/read order; never reread a mutable
  // point to explain which already-observed numeric predicate rejected it.
  if (!Number.isFinite(point.value)) rejectValue("not-finite");
  if (isDistributionKind(point.kind) && point.value < 0) rejectValue("negative-distribution");
  if (point.kind === "counter" && point.value < 0) rejectValue("negative-counter");
  function rejectValue(reason: "not-finite" | "negative-counter" | "negative-distribution"): never {
    throw known(attachPlatformMetricDiagnostic(metrics, new RangeError("CloudWatch OTel metric value is invalid for its declared kind."), capturePlatformMetricDiagnostic(() => metricRejectionRecord(reason, seriesIndex))));
  }
  const allowedLabels = new Set(series.allowedLabelNames); // Build the approved label-name lookup once per checked point.
  for (const [index, labelName] of Object.keys(point.labels ?? {}).entries()) { // Inspect every requested Core label before it becomes a provider attribute.
    if (!allowedLabels.has(labelName)) { // Reject a label the target did not explicitly review.
      throw known(attachPlatformMetricDiagnostic(metrics, new RangeError("CloudWatch OTel metric label is not declared by the target catalogue."), capturePlatformMetricDiagnostic(() => metricRejectionRecord("unapproved-label", seriesIndex, index))));
    }
  }
}

function validateCloudWatchOtelMetricsOptions(options: CloudWatchOtelMetricsOptions): void {
  const checked = validateCloudWatchOtelMetricsConfiguration(options);
  if (!checked.ok) throw Object.assign(new RangeError("CloudWatch OTel metrics require a reviewed private collector and valid metric configuration."), { diagnosticRecord: requireDiagnosticRecord(platformObservabilityDiagnosticCatalog.definitions, captureDiagnosticRecord(() => observabilityConfigurationRecord(checked.error))) });
}
function validateMetricSeries(series: readonly CloudWatchOtelMetricSeries[]): void {
  const checked = validatePlatformMetricSeries(series);
  if (!checked.ok) throw Object.assign(new RangeError("CloudWatch OTel metric series configuration is invalid."), { diagnosticRecord: requireDiagnosticRecord(platformObservabilityDiagnosticCatalog.definitions, captureDiagnosticRecord(() => observabilityConfigurationRecord(checked.error))) });
}

function maxCardinalityLimit(series: readonly CloudWatchOtelMetricSeries[]): number { // Derive a reader-level defensive cap from the reviewed per-series limits.
  return Math.max(...series.map((definition) => definition.cardinalityLimit)); // Avoid a broader default than any target-approved series needs.
}

function isDistributionKind(kind: MetricKind): boolean { // Identify the Core kinds that need OTel histograms and bucket policy.
  return kind === "histogram" || kind === "timer"; // Treat timers as histograms because percentiles require a distribution.
}

function runtimeLifecycle(provider: MeterProvider, options: CloudWatchOtelMetricsOptions, phase: "flush" | "shutdown",
  diagnostics: PlatformMetricLifecycleDiagnosticBinding | undefined, observations: PlatformObservationDiagnostics | undefined): Promise<void> {
  let projectingTimeout = false;
  const timeout = (): number => { projectingTimeout = true; const value = options.exportTimeoutMs; projectingTimeout = false; return value; };
  return observeMetricLifecycle(phase === "flush" ? () => provider.forceFlush({ timeoutMillis: timeout() }) : () => provider.shutdown({ timeoutMillis: timeout() }),
    phase, "runtime", diagnostics, observations, () => projectingTimeout ? { phase: "input-projection", field: "export-timeout" } : undefined);
}
