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
import type { MetricKind, MetricPoint, Metrics } from "@kanbien/core/monitoring"; // Implement the existing provider-neutral Core metrics port.

export interface CloudWatchOtelMetricSeries { // Define one target-approved Core-to-OTel metric mapping.
  readonly sourceName: string; // Name the provider-neutral Core metric accepted from platform runtime code.
  readonly sourceKind: MetricKind; // Require the Core metric kind so incompatible data cannot share a series.
  readonly sourceUnit: string; // Require the Core unit so a value is never silently reinterpreted.
  readonly instrumentName: string; // Name the stable OpenTelemetry instrument exported to CloudWatch.
  readonly description: string; // Explain the operational meaning of the series for operators and dashboards.
  readonly allowedLabelNames: readonly string[]; // List the only safe, bounded attributes this series may export.
  readonly cardinalityLimit: number; // Cap the number of distinct attribute combinations retained by this process.
  readonly histogramBucketBoundaries?: readonly number[]; // Supply explicit latency/distribution boundaries when the source is a timer or histogram.
}

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
): CloudWatchOtelMetricsRuntime { // Return the Core port plus lifecycle operations needed by the target process.
  validateCloudWatchOtelMetricsOptions(options); // Fail before traffic when the target configuration is malformed or unsafe.
  const exporter = new OTLPMetricExporter({ url: options.endpoint }); // Configure one metric-only exporter to the task-local collector endpoint.
  const reader = new PeriodicExportingMetricReader({ // Construct bounded periodic export outside request and worker execution paths.
    exporter, // Give the reader the OTLP exporter selected above.
    exportIntervalMillis: options.exportIntervalMs, // Use the reviewed target batching interval.
    exportTimeoutMillis: options.exportTimeoutMs, // Bound one exporter attempt so lifecycle shutdown has a limit.
    cardinalityLimits: { default: maxCardinalityLimit(options.series) }, // Apply a defensive reader-level cap in addition to each series view.
    maxExportBatchSize: options.series.length, // Prevent a first target with only fixed series from creating unbounded export batches.
  }); // Finish the controlled metric-reader configuration.
  const provider = new MeterProvider({ // Create an isolated SDK provider so this adapter never changes a process-global OTel provider.
    resource: resourceFromAttributes({ // Attach stable resource attributes instead of putting them on every metric series.
      "service.name": options.serviceName, // Identify the service that produced the metrics.
      "service.version": options.serviceVersion, // Identify the deployed build or revision.
      "deployment.environment.name": options.deploymentEnvironment, // Identify the bounded deployment environment.
      "cloud.provider": "aws", // State the selected cloud provider as resource context.
      "cloud.region": options.region, // Record the target-selected AWS region as resource context.
    }), // Finish the safe target resource attributes.
    readers: [reader], // Attach the periodic exporter to this provider only.
    views: cloudWatchOtelMetricViews(options.series), // Enforce each series' labels, cardinality cap, and histogram buckets in the SDK.
  }); // Finish the isolated provider construction.
  const meter = provider.getMeter("kanbien.platform", options.serviceVersion); // Create the one instrumentation scope used by this adapter.

  return { // Return the Core-facing adapter and lifecycle operations to the target composition root.
    metrics: createCloudWatchOtelMetrics({ meter, series: options.series }), // Adapt approved Core points to OTel instruments.
    forceFlush: () => provider.forceFlush({ timeoutMillis: options.exportTimeoutMs }), // Allow controlled evidence tests to request an immediate export.
    shutdown: () => provider.shutdown({ timeoutMillis: options.exportTimeoutMs }), // Stop periodic export and attempt one final bounded flush.
  }; // Keep lifecycle ownership with target composition, not routes or app handlers.
}

export function createCloudWatchOtelMetrics( // Adapt Core metric points to a supplied OpenTelemetry meter.
  options: { readonly meter: CloudWatchOtelMetricMeter; readonly series: readonly CloudWatchOtelMetricSeries[] }, // Allow deterministic tests to use a small in-memory meter double.
): Metrics { // Return only the established provider-neutral Core metrics port.
  validateMetricSeries(options.series); // Reject ambiguous or unsafe catalogue entries before the first metric is recorded.
  const seriesBySourceName = new Map(options.series.map((series) => [series.sourceName, series])); // Resolve each incoming Core point only through the reviewed catalogue.
  const instruments = new Map<string, Counter | Gauge | Histogram>(); // Reuse one SDK instrument per approved OTel identity and avoid per-request construction.

  return { // Implement the existing Core `Metrics` interface.
    record: (point) => { // Translate one provider-neutral point synchronously into an SDK instrument recording.
      const series = seriesBySourceName.get(String(point.name)); // Find the exact target-approved source metric identity.
      if (series === undefined) { // Reject an unreviewed point rather than inventing an exporter series.
        throw new RangeError("CloudWatch OTel metric is not declared by the target catalogue."); // Keep target policy authoritative over exported telemetry.
      }
      assertPointMatchesSeries(point, series); // Reject mismatched kind, unit, numeric value, or label shape.
      const attributes = point.labels ?? {}; // Use only Core-validated scalar labels after the series approval check.
      const instrument = instruments.get(series.sourceName) ?? createInstrument(options.meter, series); // Reuse an instrument or create the one matching this approved series.
      instruments.set(series.sourceName, instrument); // Retain the instrument so future requests do not rebuild SDK state.
      recordInstrument(instrument, series.sourceKind, point.value, attributes); // Record the point using the semantics of its declared Core kind.
    }, // Keep all provider work behind the Core metrics port.
  }; // End the Core metrics adapter implementation.
}

export function cloudWatchOtelMetricViews( // Build SDK views that enforce target catalogue policy even if an instrument is misused later.
  series: readonly CloudWatchOtelMetricSeries[], // Read the complete reviewed metric-series catalogue.
): ViewOptions[] { // Return one explicit view per approved metric series.
  validateMetricSeries(series); // Ensure invalid catalogue data cannot become SDK configuration.
  return series.map((definition) => ({ // Create the view that owns one stable OTel instrument identity.
    instrumentName: definition.instrumentName, // Select only this exact instrument, never a wildcard collection.
    attributesProcessors: [createAllowListAttributesProcessor([...definition.allowedLabelNames])], // Drop attributes outside the reviewed target allowlist as defence in depth.
    aggregationCardinalityLimit: definition.cardinalityLimit, // Bound in-process series memory for this metric identity.
    ...(isDistributionKind(definition.sourceKind) // Apply special histogram policy only to timers and histograms.
      ? { aggregation: { type: AggregationType.EXPLICIT_BUCKET_HISTOGRAM, options: { boundaries: [...(definition.histogramBucketBoundaries ?? [])] } } } // Preserve threshold-aligned buckets for latency/SLO evaluation.
      : {}), // Leave counters and gauges on their standard compatible aggregation.
  })); // Return a deterministic view per catalogue entry.
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
): void { // Throw a safe configuration-style error before any provider recording occurs.
  if (point.kind !== series.sourceKind) { // Prevent a counter and a timer from sharing an OTel identity.
    throw new RangeError("CloudWatch OTel metric kind does not match its target catalogue definition."); // Keep metric semantics queryable and unambiguous.
  }
  if (String(point.unit) !== series.sourceUnit) { // Prevent values with different units from being aggregated together.
    throw new RangeError("CloudWatch OTel metric unit does not match its target catalogue definition."); // Protect SLO threshold meaning.
  }
  if (!Number.isFinite(point.value) || (isDistributionKind(point.kind) && point.value < 0) || (point.kind === "counter" && point.value < 0)) { // Reject invalid values before they reach the SDK.
    throw new RangeError("CloudWatch OTel metric value is invalid for its declared kind."); // Keep counters and latency distributions mathematically meaningful.
  }
  const allowedLabels = new Set(series.allowedLabelNames); // Build the approved label-name lookup once per checked point.
  for (const labelName of Object.keys(point.labels ?? {})) { // Inspect every requested Core label before it becomes a provider attribute.
    if (!allowedLabels.has(labelName)) { // Reject a label the target did not explicitly review.
      throw new RangeError("CloudWatch OTel metric label is not declared by the target catalogue."); // Prevent tenant, request, raw path, or ad-hoc labels from leaking into metrics.
    }
  }
}

function validateCloudWatchOtelMetricsOptions( // Validate runtime configuration before the process accepts traffic.
  options: CloudWatchOtelMetricsOptions, // Receive the target-owned exporter configuration.
): void { // Throw safe configuration errors with no secret or endpoint payload values.
  const endpoint = new URL(options.endpoint); // Parse the configured endpoint once before enforcing the task-local boundary.
  if (endpoint.protocol !== "http:" || endpoint.hostname !== "127.0.0.1" || endpoint.port !== "4318" || endpoint.pathname !== "/v1/metrics") { // Permit only the local collector's reviewed HTTP/protobuf endpoint.
    throw new RangeError("CloudWatch OTel metrics require the task-local http://127.0.0.1:4318/v1/metrics endpoint."); // Prevent this metrics path from becoming arbitrary outbound data delivery.
  }
  assertNonEmpty("serviceName", options.serviceName); // Require a stable service resource identity.
  assertAwsRegion("region", options.region); // Require an AWS-region-shaped target configuration value.
  assertNonEmpty("serviceVersion", options.serviceVersion); // Require a deployed-version resource identity.
  assertNonEmpty("deploymentEnvironment", options.deploymentEnvironment); // Require a bounded environment resource identity.
  assertPositiveInteger("exportIntervalMs", options.exportIntervalMs); // Ensure export scheduling is meaningful and bounded.
  assertPositiveInteger("exportTimeoutMs", options.exportTimeoutMs); // Ensure each export attempt has a bounded duration.
  if (options.exportIntervalMs < 1_000 || options.exportTimeoutMs > options.exportIntervalMs) { // Reject intervals too small for a stable task-local collector and timeouts that overlap the next cycle.
    throw new RangeError("CloudWatch OTel export timeout must be positive, no greater than the interval, and the interval must be at least one second."); // Keep exporter scheduling controlled.
  }
  validateMetricSeries(options.series); // Validate the complete series catalogue before creating SDK instruments.
}

function validateMetricSeries(series: readonly CloudWatchOtelMetricSeries[]): void { // Validate all target catalogue entries as a complete set.
  if (series.length === 0) { // Reject a runtime that claims observability but has no approved series.
    throw new RangeError("CloudWatch OTel metrics require at least one declared target metric series."); // Make an empty catalogue a startup failure rather than silent telemetry loss.
  }
  const sourceNames = new Set<string>(); // Detect duplicate Core source identities.
  const instrumentNames = new Set<string>(); // Detect duplicate OTel instrument identities with incompatible definitions.
  for (const definition of series) { // Validate each declaration before the adapter accepts points.
    assertNonEmpty("sourceName", definition.sourceName); // Require a stable Core point identity.
    assertNonEmpty("instrumentName", definition.instrumentName); // Require a stable OTel metric identity.
    assertNonEmpty("description", definition.description); // Require an operator-readable meaning.
    assertNonEmpty("sourceUnit", definition.sourceUnit); // Require a declared unit for safe aggregation.
    assertPositiveInteger("cardinalityLimit", definition.cardinalityLimit); // Require an explicit in-process series bound.
    if (definition.cardinalityLimit > 1_000) { // Keep the initial low-cost smoke target's per-instrument memory bound conservative.
      throw new RangeError("CloudWatch OTel metric cardinality limit must not exceed 1000."); // Prevent target policy from silently bypassing bounded aggregation.
    }
    if (sourceNames.has(definition.sourceName) || instrumentNames.has(definition.instrumentName)) { // Prevent one source or OTel name from having two policy meanings.
      throw new RangeError("CloudWatch OTel metric source and instrument names must be unique."); // Make ambiguity a startup error.
    }
    sourceNames.add(definition.sourceName); // Remember the accepted Core source identity.
    instrumentNames.add(definition.instrumentName); // Remember the accepted OTel instrument identity.
    if (new Set(definition.allowedLabelNames).size !== definition.allowedLabelNames.length || definition.allowedLabelNames.some((label) => !/^[a-z][a-z0-9_]*$/.test(label))) { // Require a unique snake-case safe-label vocabulary.
      throw new RangeError("CloudWatch OTel metric label names must be unique lowercase snake_case values."); // Keep labels scanable and compatible with Core policy.
    }
    if (isDistributionKind(definition.sourceKind)) { // Require complete histogram policy for latency and distribution metrics.
      const boundaries = definition.histogramBucketBoundaries; // Read the optional bucket list once for validation.
      if (boundaries === undefined || boundaries.length === 0 || boundaries.some((boundary) => !Number.isFinite(boundary) || boundary <= 0) || boundaries.some((boundary, index) => index > 0 && boundary <= (boundaries[index - 1] ?? 0))) { // Require strictly increasing finite positive bucket boundaries.
        throw new RangeError("CloudWatch OTel timer and histogram metrics require strictly increasing positive bucket boundaries."); // Preserve a usable distribution for SLO queries.
      }
    } else if (definition.histogramBucketBoundaries !== undefined) { // Reject meaningless bucket policy on counters and gauges.
      throw new RangeError("CloudWatch OTel counter and gauge metrics must not declare histogram bucket boundaries."); // Keep one metric identity one semantic shape.
    }
  }
}

function maxCardinalityLimit(series: readonly CloudWatchOtelMetricSeries[]): number { // Derive a reader-level defensive cap from the reviewed per-series limits.
  return Math.max(...series.map((definition) => definition.cardinalityLimit)); // Avoid a broader default than any target-approved series needs.
}

function isDistributionKind(kind: MetricKind): boolean { // Identify the Core kinds that need OTel histograms and bucket policy.
  return kind === "histogram" || kind === "timer"; // Treat timers as histograms because percentiles require a distribution.
}

function assertNonEmpty(name: string, value: string): void { // Validate one required configuration string without returning unsafe source values.
  if (value.trim().length === 0) { // Reject absent or whitespace-only configuration.
    throw new RangeError(name + " must not be empty."); // Give startup a safe actionable error category.
  }
}

function assertPositiveInteger(name: string, value: number): void { // Validate one bounded-count configuration value.
  if (!Number.isInteger(value) || value <= 0) { // Reject fractional, zero, negative, and non-finite values.
    throw new RangeError(name + " must be a positive integer."); // Keep scheduling and cardinality bounds meaningful.
  }
}

function assertAwsRegion(name: string, value: string): void { // Validate the target-selected AWS regional identifier without embedding one target in this adapter.
  if (!/^[a-z]{2}(?:-gov)?-[a-z]+-\d+$/.test(value)) { // Require the ordinary AWS region token shape.
    throw new RangeError(name + " must be a valid AWS region identifier."); // Fail safely before the adapter exports target telemetry.
  }
}
