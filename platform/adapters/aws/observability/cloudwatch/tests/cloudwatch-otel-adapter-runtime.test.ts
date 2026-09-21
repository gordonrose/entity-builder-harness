import { deepEqual, throws } from "node:assert/strict"; // Use strict assertions to prove target catalogue enforcement and instrument translation.
import { isoDateTimeFromDate } from "@kanbien/core/shared"; // Construct the Core-required timestamp without involving a real clock.
import { metricName, metricUnit, type MetricKind, type MetricLabelValue, type MetricPoint } from "@kanbien/core/monitoring"; // Build valid provider-neutral points for the adapter boundary.
import { // Import only the public adapter surface under test.
  cloudWatchOtelMetricViews, // Inspect the generated SDK policy for histogram boundaries and cardinality limits.
  createCloudWatchOtelMetrics, // Adapt Core points through a deterministic fake meter.
  createCloudWatchOtelMetricsRuntime, // Prove unsafe exporter configuration fails before a target can serve traffic.
  type CloudWatchOtelMetricMeter, // Type the fake meter to the small adapter-owned OTel surface.
  type CloudWatchOtelMetricSeries, // Type the reviewed catalogue fixture.
} from "../src/index"; // Test the package's deliberate public barrel.

const series: readonly CloudWatchOtelMetricSeries[] = [ // Define the initial bounded target catalogue used by this adapter test.
  { // Define the capability outcome counter series.
    sourceName: "platform.server.request.outcome", // Match the profile-governed server counter name.
    sourceKind: "counter", // Require monotonic count semantics.
    sourceUnit: "count", // Count completed outcomes.
    instrumentName: "kanbien.platform.server.request.outcome", // Give CloudWatch OTel a semantic stable instrument name.
    description: "Completed protected platform capability requests by approved outcome.", // State what operators may infer from this metric.
    allowedLabelNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"], // Match the complete bounded profile projection for the initial protected route.
    cardinalityLimit: 32, // Cap local combinations well below the SDK default.
  }, // End the counter policy.
  { // Define the protected request latency distribution.
    sourceName: "platform.server.request_response_latency", // Match the profile-governed server timer name.
    sourceKind: "timer", // Require a duration distribution rather than a count.
    sourceUnit: "ms", // Keep thresholds and observations in milliseconds.
    instrumentName: "kanbien.platform.server.request.duration", // Use a semantic OTel duration instrument name.
    description: "Protected platform capability request and response latency in milliseconds.", // State the truthful measured interval.
    allowedLabelNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"], // Match the complete bounded profile projection needed to classify the SLO population.
    cardinalityLimit: 32, // Cap per-process histogram attribute combinations.
    histogramBucketBoundaries: [50, 100, 300, 750, 1_500], // Include both initial 300ms and 750ms SLO thresholds exactly.
  }, // End the latency policy.
] as const; // Preserve literal catalogue values for clear review.

const records: Array<{ readonly type: string; readonly name: string; readonly value: number; readonly attributes: Readonly<Record<string, unknown>> }> = []; // Keep an ordered public test record of every adapter observation.
const meter: CloudWatchOtelMetricMeter = { // Capture OTel instrument creation and recordings without opening a network connection.
  createCounter: (name: string) => ({ add: (value: number, attributes: Readonly<Record<string, unknown>>) => records.push({ type: "counter", name, value, attributes }) } as any), // Capture OTel counter additions.
  createGauge: (name: string) => ({ record: (value: number, attributes: Readonly<Record<string, unknown>>) => records.push({ type: "gauge", name, value, attributes }) } as any), // Capture OTel gauge recordings.
  createHistogram: (name: string) => ({ record: (value: number, attributes: Readonly<Record<string, unknown>>) => records.push({ type: "histogram", name, value, attributes }) } as any), // Capture OTel histogram recordings.
}; // Finish the small deterministic fake meter.
const metrics = createCloudWatchOtelMetrics({ meter, series }); // Build the Core metrics port against the deterministic fake meter.

metrics.record(point({ // Record one profile-approved counter point.
  name: "platform.server.request.outcome", // Use the declared Core counter identity.
  kind: "counter", // Match the counter series kind.
  value: 1, // Count one completed request.
  unit: "count", // Match the declared count unit.
  labels: { capability: "platform-smoke.smoke.read", action: "read", execution_context: "server", http_method: "GET", http_status_code: 200, outcome: "succeeded", error_class: "none" }, // Supply the complete target-approved bounded label projection.
})); // Finish the counter record.

metrics.record(point({ // Record one profile-approved latency observation.
  name: "platform.server.request_response_latency", // Use the declared Core timer identity.
  kind: "timer", // Match the timer series kind.
  value: 275, // Record an observation below the initial typical-experience threshold.
  unit: "ms", // Match the declared millisecond unit.
  labels: { capability: "platform-smoke.smoke.read", action: "read", execution_context: "server", http_method: "GET", http_status_code: 200, outcome: "succeeded", error_class: "none" }, // Supply the complete target-approved bounded label projection.
})); // Finish the timer record.

deepEqual(records, [ // Prove Core counter and timer semantics reached different OTel instrument operations.
  { type: "counter", name: "kanbien.platform.server.request.outcome", value: 1, attributes: { capability: "platform-smoke.smoke.read", action: "read", execution_context: "server", http_method: "GET", http_status_code: 200, outcome: "succeeded", error_class: "none" } }, // Counters use OTel `add` with every reviewed profile label.
  { type: "histogram", name: "kanbien.platform.server.request.duration", value: 275, attributes: { capability: "platform-smoke.smoke.read", action: "read", execution_context: "server", http_method: "GET", http_status_code: 200, outcome: "succeeded", error_class: "none" } }, // Timers use OTel histogram `record` with every reviewed profile label.
]); // Confirm the complete semantic translation.

const views = cloudWatchOtelMetricViews(series); // Generate the SDK enforcement views from the same catalogue.
deepEqual(views[1]?.aggregation, { type: 4, options: { boundaries: [50, 100, 300, 750, 1_500] } }); // Prove the explicit histogram contains both adopted SLO thresholds.
deepEqual(views[1]?.aggregationCardinalityLimit, 32); // Prove the target cardinality limit reaches SDK configuration.

throws(() => metrics.record(point({ // Attempt to record a Core metric the target did not declare.
  name: "platform.worker.job.delivery", // Use an undeclared source metric identity.
  kind: "counter", // Supply a superficially valid counter shape.
  value: 1, // Supply a valid count value.
  unit: "count", // Supply a valid count unit.
})), /not declared/); // Require target catalogue rejection rather than automatic metric creation.

throws(() => metrics.record(point({ // Attempt to add a potentially high-cardinality or unreviewed label.
  name: "platform.server.request.outcome", // Use a declared series so only label policy is under test.
  kind: "counter", // Match the declared counter kind.
  value: 1, // Supply a valid count value.
  unit: "count", // Match the declared unit.
  labels: { capability: "platform-smoke.smoke.read", action: "read", execution_context: "server", http_method: "GET", http_status_code: 200, outcome: "succeeded", error_class: "none", request_id: "request-1" }, // Add a label not approved by the catalogue.
})), /label is not declared/); // Require the adapter to reject the label before SDK recording.

throws(() => createCloudWatchOtelMetricsRuntime({ // Attempt to start the adapter with an external endpoint.
  endpoint: "https://metrics.example.test/v1/metrics", // Deliberately violate the task-local collector boundary.
  region: "eu-west-1", // Supply a valid target-selected AWS region.
  serviceName: "kanbien-platform-shell", // Supply otherwise valid stable resource identity.
  serviceVersion: "test", // Supply otherwise valid version identity.
  deploymentEnvironment: "staging", // Supply otherwise valid bounded environment identity.
  exportIntervalMs: 60_000, // Supply a valid export interval.
  exportTimeoutMs: 10_000, // Supply a valid export timeout.
  series, // Supply the valid reviewed metric catalogue.
}), /task-local/); // Require startup to refuse an arbitrary telemetry delivery destination.

console.log("CloudWatch OTel metrics adapter runtime test passed."); // Make successful standalone execution clear in governed check output.

function point(input: { // Construct one valid Core MetricPoint from readable test input.
  readonly name: string; // Accept one test metric identity.
  readonly kind: MetricKind; // Accept one Core metric kind.
  readonly value: number; // Accept one numeric observation.
  readonly unit: string; // Accept one Core metric unit.
  readonly labels?: Readonly<Record<string, MetricLabelValue>>; // Accept optional bounded test labels.
}): MetricPoint { // Return the branded Core point expected by the adapter.
  return { // Construct the exact Core metric shape.
    name: metricName(input.name), // Brand and validate the dotted metric identity.
    kind: input.kind, // Preserve the requested Core kind.
    value: input.value, // Preserve the requested measurement.
    unit: metricUnit(input.unit), // Brand and validate the metric unit token.
    recordedAt: isoDateTimeFromDate(new Date("2026-09-21T00:00:00.000Z")), // Use a deterministic non-sensitive timestamp.
    ...(input.labels === undefined ? {} : { labels: input.labels }), // Include labels only when the test supplied them.
  }; // Finish the provider-neutral point.
}
