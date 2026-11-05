import { deepEqual, equal, throws } from "node:assert/strict"; // Use strict assertions to prove target catalogue enforcement and instrument translation.
import { isoDateTimeFromDate } from "@kanbien/core/shared"; // Construct the Core-required timestamp without involving a real clock.
import { metricName, metricUnit, coreMonitoringValidationDiagnosticRecord, type MetricKind, type MetricLabelValue, type MetricPoint } from "@kanbien/core/monitoring"; // Build valid provider-neutral points for the adapter boundary.
import { createPlatformMetricDiagnosticBinding, recordPlatformMetric, type PlatformObservationDiagnostics } from "@kanbien/platform-observability";
import { MeterProvider } from "@opentelemetry/sdk-metrics";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { // Import only the public adapter surface under test.
  cloudWatchOtelMetricViews, // Inspect the generated SDK policy for histogram boundaries and cardinality limits.
  createCloudWatchOtelMetrics, // Adapt Core points through a deterministic fake meter.
  createCloudWatchOtelMetricsRuntime, // Prove unsafe exporter configuration fails before a target can serve traffic.
  validateCloudWatchOtelMetricsConfiguration,
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
}), /reviewed private collector/); // Require startup to refuse an arbitrary telemetry delivery destination.

// A separate collector task remains private when target composition selects a
// bounded service-discovery route; it must not require the server task's role.
const dedicated = createCloudWatchOtelMetricsRuntime({
  endpoint: "http://observability-collector.kanbien-core-platform.internal:4318/v1/metrics",
  region: "eu-west-1",
  serviceName: "kanbien-core-server-persistence",
  serviceVersion: "test",
  deploymentEnvironment: "kanbien-core-platform",
  exportIntervalMs: 60_000,
  exportTimeoutMs: 10_000,
  series,
});
void dedicated.shutdown(); // No metric is recorded in this boundary test; stop its periodic reader without introducing an asynchronous test harness.

console.log("CloudWatch OTel metrics adapter runtime test passed."); // Make successful standalone execution clear in governed check output.

const configuration = { endpoint: "http://127.0.0.1:4318/v1/metrics", region: "eu-west-1", serviceName: "fixture-service", serviceVersion: "test", deploymentEnvironment: "fixture", exportIntervalMs: 1000, exportTimeoutMs: 1000, series };
equal(validateCloudWatchOtelMetricsConfiguration(configuration).ok, true);
function rejectedOptions(overrides: Record<string, unknown>) {
  const r = validateCloudWatchOtelMetricsConfiguration({ ...configuration, ...overrides }); if (r.ok) throw Error("Expected rejected provider options");
  equal(JSON.stringify(r.error).includes("synthetic-private"), false); return r.error.issues;
}
for (const [endpoint, reasons] of [
  ["synthetic-private", ["malformed-url"]], ["https://127.0.0.1:4318/v1/metrics", ["protocol-not-allowed"]],
  ["http://127.0.0.1:4319/v1/metrics", ["port-not-allowed"]], ["http://127.0.0.1:4318/private", ["path-not-allowed"]],
  ["http://synthetic-private@127.0.0.1:4318/v1/metrics", ["credentials-not-allowed"]],
  ["http://127.0.0.1:4318/v1/metrics?token=synthetic-private", ["query-not-allowed"]],
  ["http://127.0.0.1:4318/v1/metrics#synthetic-private", ["fragment-not-allowed"]],
  ["http://synthetic-private.example:4318/v1/metrics", ["host-not-allowed"]],
] as const) deepEqual(rejectedOptions({ endpoint }), reasons.map(reason => ({ setting: "metrics.endpoint", reason })));
for (const [key, setting] of [["endpoint", "metrics.endpoint"], ["region", "metrics.region"], ["serviceName", "metrics.service-name"], ["serviceVersion", "metrics.service-version"], ["deploymentEnvironment", "metrics.deployment-environment"]] as const) {
  for (const [raw, reason] of [[undefined, "missing"], [null, "wrong-type"], [42, "wrong-type"], ["", "blank"]] as const) deepEqual(rejectedOptions({ [key]: raw }), [{ setting, reason }]);
}
deepEqual(rejectedOptions({ region: "synthetic-private" }), [{ setting: "metrics.region", reason: "invalid-format" }]);
for (const region of ["eu-west-1", "us-gov-west-1", "aa-x-123"]) equal(validateCloudWatchOtelMetricsConfiguration({ ...configuration, region }).ok, true);
for (const [key, setting] of [["exportIntervalMs", "metrics.export-interval"], ["exportTimeoutMs", "metrics.export-timeout"]] as const) {
  for (const [raw, reason] of [[undefined, "missing"], ["1000", "wrong-type"], [null, "wrong-type"], [NaN, "invalid-integer"], [Infinity, "not-finite"], [1.5, "invalid-integer"], [0, "not-positive"]] as const) deepEqual(rejectedOptions({ [key]: raw }), [{ setting, reason }]);
}
deepEqual(rejectedOptions({ exportIntervalMs: 999, exportTimeoutMs: 1000 }), [
  { setting: "metrics.export-interval", reason: "interval-too-short" }, { setting: "metrics.export-timeout", reason: "timeout-exceeds-interval" },
]);
let providerGetterReads = 0;
const hostileOptions = Object.defineProperty({ ...configuration }, "endpoint", { get() { providerGetterReads++; throw Error("synthetic-private"); } });
equal(validateCloudWatchOtelMetricsConfiguration(hostileOptions).ok, false); equal(providerGetterReads, 0);
throws(() => createCloudWatchOtelMetricsRuntime({ ...configuration, region: "synthetic-private" }),
  (error: unknown) => error instanceof RangeError && JSON.stringify((error as RangeError & { diagnosticRecord: unknown }).diagnosticRecord).includes('"setting":"metrics.region"'));

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

// Assert meaning, not merely the presence of a schema-valid companion.
const basic = { name: series[0]!.sourceName, kind: "counter" as const, value: 1, unit: "count" };
let creations = 0, invocations = 0;
const isolatedMeter: CloudWatchOtelMetricMeter = {
  createCounter() { creations++; return { add() { invocations++; } } as any; },
  createGauge() { creations++; return { record() { invocations++; } } as any; },
  createHistogram() { creations++; return { record() { invocations++; } } as any; },
};
const checkedPort = createCloudWatchOtelMetrics({ meter: isolatedMeter, series });
const metricProducers = require("../../../../../observability/src/metric-diagnostics") as Record<string, unknown>;
for (const key of ["metricRejectionRecord", "metricCreationRecord", "metricRecordingRecord"] as const) {
  const descriptor = Object.getOwnPropertyDescriptor(metricProducers, key)!;
  for (const mode of ["throw", "undefined"] as const) {
    let creations = 0, invocations = 0;
    const build = () => {
      creations++;
      if (key === "metricCreationRecord") throw new Error("PRIVATE_CREATION");
      return { add() { invocations++; throw new Error("PRIVATE_RECORDING"); } } as any;
    };
    const port = createCloudWatchOtelMetrics({ meter: { createCounter: build, createGauge: build, createHistogram: build }, series });
    try {
      Object.defineProperty(metricProducers, key, { ...descriptor, value: () => { if (mode === "throw") throw new Error("PRIVATE_DIAGNOSTIC"); return undefined; } });
      throws(() => port.record(point({ ...basic, ...(key === "metricRejectionRecord" ? { name: "undeclared.metric" } : {}) })), error => {
        equal(error instanceof Error, true);
        equal((error as Error).message, key === "metricRejectionRecord" ? "CloudWatch OTel metric is not declared by the target catalogue."
          : key === "metricCreationRecord" ? "Metric instrument creation did not complete." : "Metric recording invocation did not complete.");
        deepEqual(Object.getOwnPropertyDescriptor(error, "diagnosticRecord")?.value, {
          schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1,
          detail: { reason: mode === "throw" ? "construction-threw" : "construction-rejected" },
        });
        return true;
      });
      equal(creations, key === "metricRejectionRecord" ? 0 : 1);
      equal(invocations, key === "metricRecordingRecord" ? 1 : 0);
    } finally { Object.defineProperty(metricProducers, key, descriptor); }
  }
}
for (const [input, expected] of [
  [{ ...basic, name: "synthetic.private" }, { reason: "undeclared-metric" }],
  [{ ...basic, kind: "gauge" as const, unit: "ms", value: NaN }, { reason: "kind-mismatch", seriesIndex: 0 }],
  [{ ...basic, unit: "ms", value: NaN }, { reason: "unit-mismatch", seriesIndex: 0 }],
  [{ ...basic, value: NaN }, { reason: "not-finite", seriesIndex: 0 }],
  [{ ...basic, value: Infinity }, { reason: "not-finite", seriesIndex: 0 }],
  [{ ...basic, value: -1 }, { reason: "negative-counter", seriesIndex: 0 }],
  [{ name: series[1]!.sourceName, kind: "timer" as const, value: -1, unit: "ms" }, { reason: "negative-distribution", seriesIndex: 1 }],
  [{ ...basic, labels: { outcome: "succeeded", private_extra: "synthetic-canary" } }, { reason: "unapproved-label", seriesIndex: 0, index: 1 }],
] as const) {
  const observed: DiagnosticRecord[] = [];
  const binding = createPlatformMetricDiagnosticBinding({ report(record, context) { observed.push(record); equal(context.operation, "request-outcome"); return { status: "written" }; } }, { capability: "observability", stage: "request" });
  recordPlatformMetric(checkedPort, { now: () => new Date() }, input, { binding, operation: "request-outcome" });
  deepEqual(observed, [{ schema: "core/diagnostic-record/v1", code: "observability.metric-rejected", definitionVersion: 1,
    detail: { phase: "point-validation", effect: "recording-not-attempted", ...expected } }], "adapter must report the independently expected rejecting predicate");
  equal(creations, 0); equal(invocations, 0);
  equal(JSON.stringify(observed).includes("synthetic-canary"), false);
}
checkedPort.record(point(basic)); checkedPort.record(point({ ...basic, value: 0 }));
equal(creations, 1); equal(invocations, 2, "accepted counter preserves calls and reuses its instrument");
for (const [values, expectedReason, expectedReads] of [
  [[NaN, 1], "not-finite", 1], [[Infinity, -1], "not-finite", 1], [[1, -1], "negative-counter", 2],
] as const) {
  let valueReads = 0;
  const mutable = Object.defineProperty(point(basic), "value", { get() { return values[Math.min(valueReads++, values.length - 1)]; } });
  throws(() => checkedPort.record(mutable), (error: unknown) => {
    equal(error instanceof RangeError, true);
    deepEqual(Object.getOwnPropertyDescriptor(error, "diagnosticRecord")?.value,
      { schema: "core/diagnostic-record/v1", code: "observability.metric-rejected", definitionVersion: 1,
        detail: { phase: "point-validation", reason: expectedReason, effect: "recording-not-attempted", seriesIndex: 0 } },
      "numeric diagnosis must use the exact observed rejecting check, not a later getter value");
    return true;
  });
  equal(valueReads, expectedReads); equal(creations, 1); equal(invocations, 2);
}
const gaugeSeries: CloudWatchOtelMetricSeries = { ...series[0]!, sourceName: "fixture.gauge", sourceKind: "gauge", instrumentName: "fixture.gauge", allowedLabelNames: ["safe"] };
const gaugePort = createCloudWatchOtelMetrics({ meter: isolatedMeter, series: [gaugeSeries] });
gaugePort.record(point({ name: "fixture.gauge", kind: "gauge", unit: "count", value: -10, labels: { safe: false } }));
equal(invocations, 3, "negative gauges and approved scalar attributes remain accepted");
for (const kind of ["counter", "gauge", "histogram", "timer"] as const) {
  const one: CloudWatchOtelMetricSeries = { ...series[0]!, sourceName: "fixture.instrument", instrumentName: "fixture.instrument", sourceKind: kind,
    ...(kind === "timer" || kind === "histogram" ? { histogramBucketBoundaries: [1, 2] } : {}) };
  for (const phase of ["creation", "record"] as const) {
    let createAttempts = 0, recordAttempts = 0;
    const create = () => { createAttempts++; if (phase === "creation") throw new Error("SDK-private-canary");
      const fail = () => { recordAttempts++; throw new Error("SDK-private-canary"); };
      return { add: fail, record: fail } as any; };
    const port = createCloudWatchOtelMetrics({ meter: { createCounter: create, createGauge: create, createHistogram: create }, series: [one] });
    const observed: DiagnosticRecord[] = [];
    const binding = createPlatformMetricDiagnosticBinding({ report(record) { observed.push(record); return { status: "written" }; } }, { capability: "observability", stage: "request" });
    recordPlatformMetric(port, { now: () => new Date() }, { name: "fixture.instrument", kind }, { binding, operation: "metric" });
    deepEqual(observed, [phase === "creation"
      ? { schema: "core/diagnostic-record/v1", code: "observability.metric-instrument-creation-failed", definitionVersion: 1,
        detail: { reason: "unclassified-creation-failure", phase: "instrument-creation", effect: "recording-not-attempted", seriesIndex: 0 } }
      : { schema: "core/diagnostic-record/v1", code: "observability.metric-recording-failed", definitionVersion: 1,
        detail: { reason: "unclassified-invocation-failure", phase: "record-invocation", effect: "unknown", seriesIndex: 0 } }],
      "creation and invocation meanings must be independent of the production record constructors");
    equal(createAttempts, 1); equal(recordAttempts, phase === "creation" ? 0 : 1);
    equal(JSON.stringify(observed).includes("SDK-private-canary"), false);
  }
}

// Independent own/source evidence must not consume a source's ninth slot.
const sourceNine = Array.from({ length: 9 }, (_, ordinal) => coreMonitoringValidationDiagnosticRecord({ operation: "signal-definition", field: "signal-intent", ordinal, reason: "closed-value-rejected", effect: "rejected" }));
const sourceFailure = Object.freeze({ diagnosticRecord: sourceNine[0], relatedDiagnosticRecords: sourceNine.slice(1), message: "SDK-private-canary" });
const boundaryRecords: DiagnosticRecord[] = [], boundaryContexts: unknown[] = [];
const observationOptions: PlatformObservationDiagnostics = {
  reporter: { report(record, context) { equal(this, observationOptions.reporter); boundaryRecords.push(record); boundaryContexts.push(context); return { status: "written" }; } },
  context: { capability: "observability", operation: "metrics", stage: "startup" },
};
for (const phase of ["creation", "record"] as const) {
  let createCalls = 0, recordCalls = 0;
  const create = () => { createCalls++; if (phase === "creation") throw sourceFailure; return { add() { recordCalls++; throw sourceFailure; } } as any; };
  const port = createCloudWatchOtelMetrics({ meter: { createCounter: create, createGauge: create, createHistogram: create }, series }, observationOptions);
  boundaryRecords.length = 0; boundaryContexts.length = 0;
  let wrapped: unknown;
  try { port.record(point(basic)); } catch (error) { wrapped = error; }
  equal(wrapped instanceof Error, true);
  equal((wrapped as Error).message, phase === "creation" ? "Metric instrument creation did not complete." : "Metric recording invocation did not complete.");
  equal(Object.getOwnPropertyDescriptor(wrapped, "diagnosticRecord")?.value.code, phase === "creation" ? "observability.metric-instrument-creation-failed" : "observability.metric-recording-failed");
  equal(boundaryRecords.length, 10); deepEqual(boundaryRecords.slice(1), sourceNine);
  deepEqual(boundaryRecords[0]?.detail, { operation: phase === "creation" ? "metric-instrument-creation" : "metric-recording", phase: phase === "creation" ? "instrument-creation" : "instrument-recording", field: phase === "creation" ? "meter" : "record", reason: "threw", effect: "unknown" });
  equal(createCalls, 1); equal(recordCalls, phase === "creation" ? 0 : 1);
  equal(JSON.stringify(boundaryRecords).includes("SDK-private-canary"), false);
  deepEqual(boundaryContexts, Array.from({ length: 10 }, () => ({ capability: "observability", operation: "metrics", stage: "runtime" })));
}
const rawPort = createCloudWatchOtelMetrics({ meter: isolatedMeter, series }, observationOptions);
boundaryRecords.length = 0;
throws(() => rawPort.record({ ...point(basic), get name(): never { throw sourceFailure; } }), (error) => error === sourceFailure);
deepEqual(boundaryRecords[0]?.detail, { operation: "metric-recording", phase: "input-projection", field: "name", reason: "threw", effect: "not-attempted" });
deepEqual(boundaryRecords.slice(1), sourceNine);
let oldGuard: unknown;
try { rawPort.record(point({ ...basic, value: -1 })); } catch (error) { oldGuard = error; }
boundaryRecords.length = 0;
throws(() => rawPort.record({ ...point(basic), get name(): never { throw oldGuard; } }), (error) => error === oldGuard);
deepEqual(boundaryRecords.map(({ code }) => code), ["observability.boundary-failed", "observability.metric-rejected"]);
for (const [property, field] of [["endpoint", "endpoint"], ["exportIntervalMs", "export-interval"], ["exportTimeoutMs", "export-timeout"], ["serviceName", "service-name"], ["serviceVersion", "service-version"], ["deploymentEnvironment", "environment"], ["region", "region"]] as const) {
  boundaryRecords.length = 0;
  const mutable = new Proxy(configuration, { get(target, key, receiver) { if (key === property) throw sourceFailure; return Reflect.get(target, key, receiver); } });
  throws(() => createCloudWatchOtelMetricsRuntime(mutable, undefined, observationOptions), (error) => error === sourceFailure);
  deepEqual(boundaryRecords[0]?.detail, { operation: "metric-runtime-construction", phase: "input-projection", field, reason: "threw", effect: "unknown" });
  equal(boundaryRecords.length, 10, "one per-current-call report, never nested duplicate source9");
  deepEqual(boundaryRecords.slice(1), sourceNine);
}
const nativeGetMeter = MeterProvider.prototype.getMeter;
let selectedProvider: MeterProvider | undefined;
boundaryRecords.length = 0;
try {
  MeterProvider.prototype.getMeter = function () { selectedProvider = this; throw sourceFailure; };
  throws(() => createCloudWatchOtelMetricsRuntime(configuration, undefined, observationOptions), (error) => error === sourceFailure);
} finally { MeterProvider.prototype.getMeter = nativeGetMeter; void selectedProvider?.shutdown(); }
deepEqual(boundaryRecords[0]?.detail, { operation: "metric-runtime-construction", phase: "meter-selection", reason: "threw", effect: "unknown" });
deepEqual(boundaryRecords.slice(1), sourceNine);
boundaryRecords.length = 0;
let catalogueReads = 0;
const changingCatalogue = new Proxy(configuration, { get(target, key, receiver) { if (key === "series" && ++catalogueReads === 4) throw sourceFailure; return Reflect.get(target, key, receiver); } });
try {
  MeterProvider.prototype.getMeter = function (...args) { selectedProvider = this; return Reflect.apply(nativeGetMeter, this, args); };
  throws(() => createCloudWatchOtelMetricsRuntime(changingCatalogue, undefined, observationOptions), (error) => error === sourceFailure);
} finally { MeterProvider.prototype.getMeter = nativeGetMeter; void selectedProvider?.shutdown(); }
equal(catalogueReads, 4);
deepEqual(boundaryRecords[0]?.detail, { operation: "metric-runtime-construction", phase: "input-projection", field: "series", reason: "threw", effect: "unknown" });
deepEqual(boundaryRecords.slice(1), sourceNine);
boundaryRecords.length = 0;
let versionReads = 0;
const changingVersion = new Proxy(configuration, { get(target, key, receiver) { if (key === "serviceVersion" && ++versionReads === 2) throw sourceFailure; return Reflect.get(target, key, receiver); } });
const nativeGetMeterDescriptor = Object.getOwnPropertyDescriptor(MeterProvider.prototype, "getMeter")!;
try {
  Object.defineProperty(MeterProvider.prototype, "getMeter", { configurable: true, get(this: MeterProvider) { selectedProvider = this; return nativeGetMeter; } });
  throws(() => createCloudWatchOtelMetricsRuntime(changingVersion, undefined, observationOptions), (error) => error === sourceFailure);
} finally { Object.defineProperty(MeterProvider.prototype, "getMeter", nativeGetMeterDescriptor); void selectedProvider?.shutdown(); }
equal(versionReads, 2);
deepEqual(boundaryRecords[0]?.detail, { operation: "metric-runtime-construction", phase: "input-projection", field: "service-version", reason: "threw", effect: "unknown" });
equal(boundaryRecords.length, 10); deepEqual(boundaryRecords.slice(1), sourceNine);
boundaryRecords.length = 0;
const nativeReaderFailure = new Proxy(configuration, { get(target, key, receiver) { return key === "exportIntervalMs" ? -1 : Reflect.get(target, key, receiver); } });
throws(() => createCloudWatchOtelMetricsRuntime(nativeReaderFailure, undefined, observationOptions), Error);
deepEqual(boundaryRecords[0]?.detail, { operation: "metric-runtime-construction", phase: "reader-construction", reason: "threw", effect: "unknown" });
equal(boundaryRecords.length, 1, "opaque SDK constructor failure does not inherit the last successful field read");
const reads: PropertyKey[] = [];
const readOrder = new Proxy(configuration, { get(target, key, receiver) { reads.push(key); return Reflect.get(target, key, receiver); } });
const orderRuntime = createCloudWatchOtelMetricsRuntime(readOrder, undefined, observationOptions);
deepEqual(reads, ["endpoint", "exportIntervalMs", "exportTimeoutMs", "series", "series", "serviceName", "serviceVersion", "deploymentEnvironment", "region", "series", "serviceVersion", "series"]);
void orderRuntime.shutdown();
let contextReads = 0;
const accessorContext = { get capability() { contextReads++; return "observability"; }, operation: "metrics", stage: "startup" as const };
boundaryRecords.length = 0;
const invalidContextPort = createCloudWatchOtelMetrics({ meter: { ...isolatedMeter, createCounter() { throw sourceFailure; } }, series }, { ...observationOptions, context: accessorContext });
throws(() => invalidContextPort.record(point(basic)), /Metric instrument creation/);
equal(contextReads, 0); equal(boundaryRecords.length, 0, "context accessors remain invalid and are never flattened into trusted data");
let definitionReads = 0;
const definitionFallback: PlatformObservationDiagnostics = { ...observationOptions, get definitions(): never { definitionReads++; throw sourceFailure; } };
const fallbackPort = createCloudWatchOtelMetrics({ meter: { ...isolatedMeter, createCounter() { throw sourceFailure; } }, series }, definitionFallback);
equal(definitionReads, 0, "stage binding must not eagerly read optional definition getters");
boundaryRecords.length = 0;
throws(() => fallbackPort.record(point(basic)), /Metric instrument creation/);
equal(definitionReads, 1); equal(boundaryRecords.length, 11); deepEqual(boundaryRecords.slice(1, 10), sourceNine);
deepEqual(boundaryRecords[10], { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason: "definition-selection-failed" } });
