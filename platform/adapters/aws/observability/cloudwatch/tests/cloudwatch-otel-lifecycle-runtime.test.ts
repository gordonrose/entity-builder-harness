import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import { createServer } from "node:http";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { AggregationTemporality, AggregationType, InstrumentType, MeterProvider, PeriodicExportingMetricReader, TimeoutError,
  type CollectionResult, type PushMetricExporter } from "@opentelemetry/sdk-metrics";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { metricName, metricUnit, coreMonitoringValidationDiagnosticRecord } from "@kanbien/core/monitoring";
import { isoDateTimeFromDate } from "@kanbien/core/shared";
import { createPlatformMetricLifecycleDiagnosticBinding, type PlatformMetricLifecycleDiagnosticBinding, type PlatformObservationDiagnostics } from "@kanbien/platform-observability";
import { ObservedPeriodicMetricReader, observeMetricExporter, observeMetricLifecycle } from "../src/lifecycle-observation";
import { createCloudWatchOtelMetricsRuntime } from "../src/index";

// These fixtures exercise the installed SDK, not a reimplementation of its reader.
// A failing callback is deliberately independent from the promise returned by flush.
async function sdkBoundaryBaseline(): Promise<void> {
  let exports = 0, flushes = 0;
  const exporter: PushMetricExporter = {
    export(_data, callback) { exports++; callback({ code: 1, error: new Error("synthetic-export-private") }); },
    async forceFlush() { flushes++; }, async shutdown() {},
  };
  const reader = new PeriodicExportingMetricReader({ exporter, exportIntervalMillis: 60_000, exportTimeoutMillis: 1_000 });
  const provider = new MeterProvider({ readers: [reader] });
  try {
    const meter = provider.getMeter("fixture");
    meter.createCounter("fixture.counter").add(1);
    await provider.forceFlush();
    equal(exports, 1); equal(flushes, 1, "failed callback does not imply a rejected flush");
    meter.createObservableGauge("fixture.broken").addCallback(() => { throw new Error("synthetic-collection-private"); });
    const mixed = await reader.collect();
    equal(mixed.errors.length, 1);
    equal(mixed.resourceMetrics.scopeMetrics.length, 1, "collection errors and collected data coexist");
  } finally { await provider.shutdown(); }
  const unbound = new PeriodicExportingMetricReader({ exporter, exportIntervalMillis: 60_000 });
  await rejects(unbound.collect(), /not bound/);
  // An empty successful collection has no error and is not a delivery failure.
  const emptyReader = new PeriodicExportingMetricReader({ exporter, exportIntervalMillis: 60_000 });
  const emptyProvider = new MeterProvider({ readers: [emptyReader] });
  try { const empty = await emptyReader.collect(); deepEqual(empty.errors, []); deepEqual(empty.resourceMetrics.scopeMetrics, []); }
  finally { await emptyProvider.shutdown(); }
}

function capture() {
  const records: DiagnosticRecord[] = [];
  const binding = createPlatformMetricLifecycleDiagnosticBinding({ report(record) { records.push(record); return { status: "written" }; } }, { capability: "observability" });
  return { binding, records };
}
const envelope = (code: string, detail: unknown) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });

async function wrapperPreservation(): Promise<void> {
  const fixture = capture(), data = { resource: resourceFromAttributes({}), scopeMetrics: [] };
  const receiver = {}, failure = { code: 1, error: new Error("synthetic-export-private") };
  let calls = 0, callbackCalls = 0;
  const exporter: PushMetricExporter = {
    export(actual, callback) { equal(this, exporter); equal(actual, data); calls++; Reflect.apply(callback, receiver, [failure]); },
    async forceFlush() { equal(this, exporter); }, async shutdown() { equal(this, exporter); },
  };
  const wrapped = observeMetricExporter(exporter, fixture.binding);
  equal(Object.hasOwn(wrapped, "selectAggregation"), false); equal(Object.hasOwn(wrapped, "selectAggregationTemporality"), false);
  wrapped.export(data, function(this: unknown, result) { equal(this, receiver); equal(result, failure); callbackCalls++; });
  equal(calls, 1); equal(callbackCalls, 1);
  deepEqual(fixture.records, [envelope("observability.metric-export-failed", { phase: "export", reason: "callback-failed", effect: "unknown" })]);
  await wrapped.forceFlush(); await wrapped.shutdown(); equal(fixture.records.length, 1);
  let aggregationReads = 0, temporalityReads = 0;
  Object.defineProperty(exporter, "selectAggregation", { get() { aggregationReads++; return function(this: unknown, kind: InstrumentType) { equal(this, exporter); equal(kind, InstrumentType.COUNTER); return { type: AggregationType.SUM }; }; } });
  Object.defineProperty(exporter, "selectAggregationTemporality", { get() { temporalityReads++; return function(this: unknown, kind: InstrumentType) { equal(this, exporter); equal(kind, InstrumentType.COUNTER); return AggregationTemporality.DELTA; }; } });
  const selected = observeMetricExporter(exporter, fixture.binding);
  deepEqual(selected.selectAggregation?.(InstrumentType.COUNTER), { type: AggregationType.SUM });
  equal(selected.selectAggregationTemporality?.(InstrumentType.COUNTER), AggregationTemporality.DELTA);
  equal(aggregationReads, 1); equal(temporalityReads, 1);
  const thrown = new Error("synthetic-invocation-private"), direct = capture();
  const throwing = observeMetricExporter({ ...exporter, export() { throw thrown; } }, direct.binding);
  throws(() => throwing.export(data, () => {}), (error) => error === thrown);
  deepEqual(direct.records, [envelope("observability.metric-export-failed", { phase: "export", reason: "invocation-threw", effect: "unknown" })]);
  const callbackFailure = capture(), downstreamError = new Error("synthetic-callback-private");
  const synchronous = observeMetricExporter({ ...exporter, export(_data, callback) { callback({ code: 0 }); } }, callbackFailure.binding);
  throws(() => synchronous.export(data, () => { throw downstreamError; }), (error) => error === downstreamError);
  equal(callbackFailure.records.length, 0, "a downstream callback throw is not exporter failure evidence");
  const failingSink: PlatformMetricLifecycleDiagnosticBinding = { report() { throw new Error("synthetic-sink-private"); } };
  let isolatedCallbacks = 0;
  observeMetricExporter(exporter, failingSink).export(data, () => { isolatedCallbacks++; }); equal(isolatedCallbacks, 1);
  for (const phase of ["flush", "shutdown"] as const) for (const boundary of ["exporter", "runtime"] as const) {
    for (const [error, reason] of [[thrown, "rejected"], [new TimeoutError("synthetic-timeout-private"), "sdk-timeout"],
      [new Proxy({}, { getPrototypeOf() { throw new Error("synthetic-classification-private"); } }), "rejected"]] as const) {
      const observed = capture(); let invocations = 0;
      await rejects(observeMetricLifecycle(() => { invocations++; return Promise.reject(error); }, phase, boundary, observed.binding), (actual) => actual === error);
      equal(invocations, 1);
      deepEqual(observed.records, [envelope(`observability.metric-${phase}-failed`, { phase, boundary, reason, effect: "unknown" })]);
    }
    const sync = capture();
    throws(() => observeMetricLifecycle(() => { throw thrown; }, phase, boundary, sync.binding), (actual) => actual === thrown);
    deepEqual(sync.records, [envelope(`observability.metric-${phase}-failed`, { phase, boundary, reason: "invocation-threw", effect: "unknown" })]);
  }
  // Inherited native-promise regression: do not read a shadowed own then.
  const shadowed = capture(); let thenReads = 0, unhandled = 0;
  const onUnhandled = () => { unhandled++; }; process.on("unhandledRejection", onUnhandled);
  try {
    const pending = Promise.reject(thrown);
    Object.defineProperty(pending, "then", { get() { thenReads++; throw new Error("synthetic-then-private"); } });
    await rejects(observeMetricLifecycle(() => pending, "flush", "exporter", shadowed.binding), (actual) => actual === thrown);
    await new Promise<void>((resolve) => setImmediate(resolve));
    equal(unhandled, 0); equal(thenReads, 0); equal(shadowed.records.length, 1);
  } finally { process.off("unhandledRejection", onUnhandled); }
  await rejects(observeMetricLifecycle(() => Promise.reject(thrown), "flush", "exporter", failingSink), (actual) => actual === thrown);
  equal(JSON.stringify([...fixture.records, ...direct.records, ...shadowed.records]).includes("synthetic-"), false);
}

async function collectionAndSdkObservation(): Promise<void> {
  const fixture = capture(); let exports = 0;
  const exporter: PushMetricExporter = { export(_data, callback) { exports++; callback({ code: 1, error: new Error("synthetic-private") }); }, async forceFlush() {}, async shutdown() {} };
  const reader = new ObservedPeriodicMetricReader({ exporter: observeMetricExporter(exporter, fixture.binding), exportIntervalMillis: 60_000 }, fixture.binding);
  const provider = new MeterProvider({ readers: [reader] });
  try {
    const meter = provider.getMeter("fixture"); meter.createCounter("fixture.counter").add(1);
    await observeMetricLifecycle(() => provider.forceFlush(), "flush", "runtime", fixture.binding);
    equal(exports, 1);
    deepEqual(fixture.records, [envelope("observability.metric-export-failed", { phase: "export", reason: "callback-failed", effect: "unknown" })], "resolved flush must not drop the export observation or invent flush failure");
    meter.createObservableGauge("fixture.broken").addCallback(() => { throw new Error("synthetic-private"); });
    const mixed = await reader.collect(); equal(mixed.errors.length, 1); equal(mixed.resourceMetrics.scopeMetrics.length, 1);
    deepEqual(fixture.records[1], envelope("observability.metric-collection-issues", { phase: "collection", reason: "errors-returned", effect: "collection-result-returned-completeness-unknown", errorCount: 1 }));
  } finally { await provider.shutdown(); }
  // Public collect fixture proves exact result identity and empty-result+errors,
  // including failure of diagnostic-only count inspection, without private hooks.
  const originalCollect = PeriodicExportingMetricReader.prototype.collect;
  const quiet = capture(), observed = new ObservedPeriodicMetricReader({ exporter, exportIntervalMillis: 60_000 }, quiet.binding);
  const result: CollectionResult = { resourceMetrics: { resource: resourceFromAttributes({}), scopeMetrics: [] }, errors: [new Error("synthetic-private")] };
  try {
    let calls = 0; const options = { timeoutMillis: 17 };
    PeriodicExportingMetricReader.prototype.collect = async function(actual) { equal(this, observed); equal(actual, options); calls++; return result; };
    equal(await observed.collect(options), result); equal(calls, 1);
    deepEqual(quiet.records, [envelope("observability.metric-collection-issues", { phase: "collection", reason: "errors-returned", effect: "collection-result-returned-completeness-unknown", errorCount: 1 })]);
    const hostile = Object.defineProperty({ resourceMetrics: result.resourceMetrics }, "errors", { get() { throw new Error("synthetic-count-private"); } }) as CollectionResult;
    PeriodicExportingMetricReader.prototype.collect = async () => hostile;
    equal(await observed.collect(), hostile); equal(quiet.records.length, 1, "inspection cannot turn a returned result into failure");
    PeriodicExportingMetricReader.prototype.collect = async () => result;
    const sinkFailure = new ObservedPeriodicMetricReader({ exporter, exportIntervalMillis: 60_000 }, { report() { throw new Error("synthetic-private"); } });
    equal(await sinkFailure.collect(), result);
    for (const [error, reason] of [[new Error("synthetic-private"), "rejected"], [new TimeoutError("synthetic-private"), "sdk-timeout"]] as const) {
      const fail = capture(), rejected = new ObservedPeriodicMetricReader({ exporter, exportIntervalMillis: 60_000 }, fail.binding);
      PeriodicExportingMetricReader.prototype.collect = async () => { throw error; };
      await rejects(rejected.collect(), (actual) => actual === error);
      deepEqual(fail.records, [envelope("observability.metric-collection-failed", { phase: "collection", reason, effect: "unknown" })]);
    }
  } finally { PeriodicExportingMetricReader.prototype.collect = originalCollect; }
  const empty = capture(), emptyReader = new ObservedPeriodicMetricReader({ exporter, exportIntervalMillis: 60_000 }, empty.binding);
  const emptyProvider = new MeterProvider({ readers: [emptyReader] });
  try { deepEqual((await emptyReader.collect()).resourceMetrics.scopeMetrics, []); equal(empty.records.length, 0); }
  finally { await emptyProvider.shutdown(); }
  const hidden = capture();
  const stalled: PushMetricExporter = { export() {}, async forceFlush() {}, async shutdown() {} };
  const timeoutReader = new ObservedPeriodicMetricReader({ exporter: observeMetricExporter(stalled, hidden.binding), exportIntervalMillis: 60_000, exportTimeoutMillis: 5 }, hidden.binding);
  const timeoutProvider = new MeterProvider({ readers: [timeoutReader] });
  timeoutProvider.getMeter("fixture").createCounter("fixture.counter").add(1);
  await observeMetricLifecycle(() => timeoutProvider.forceFlush({ timeoutMillis: 1_000 }), "flush", "runtime", hidden.binding);
  equal(hidden.records.length, 0, "a swallowed reader timeout has no public evidence: do not invent a diagnosis");
  await timeoutProvider.shutdown();
  const publicTimeout = capture(); let finishFlush!: () => void, completed = false;
  const delayed: PushMetricExporter = { export(_data, cb) { cb({ code: 0 }); }, forceFlush() { return new Promise<void>((resolve) => { finishFlush = () => { completed = true; resolve(); }; }); }, async shutdown() {} };
  const delayedReader = new ObservedPeriodicMetricReader({ exporter: observeMetricExporter(delayed, publicTimeout.binding), exportIntervalMillis: 60_000 }, publicTimeout.binding);
  const delayedProvider = new MeterProvider({ readers: [delayedReader] });
  await rejects(observeMetricLifecycle(() => delayedProvider.forceFlush({ timeoutMillis: 5 }), "flush", "runtime", publicTimeout.binding), (error) => error instanceof TimeoutError);
  equal(completed, false);
  deepEqual(publicTimeout.records, [envelope("observability.metric-flush-failed", { phase: "flush", boundary: "runtime", reason: "sdk-timeout", effect: "unknown" })]);
  finishFlush(); await new Promise<void>((resolve) => setImmediate(resolve)); equal(completed, true, "timeout is not cancellation");
  delayed.forceFlush = async () => {}; await delayedProvider.shutdown();
  const flushFailure = capture(), flushError = new Error("synthetic-flush-private");
  const failingFlushReader = new ObservedPeriodicMetricReader({ exporter: observeMetricExporter({ export(_data, cb) { cb({ code: 0 }); }, async forceFlush() { throw flushError; }, async shutdown() {} }, flushFailure.binding), exportIntervalMillis: 60_000 }, flushFailure.binding);
  const failingFlushProvider = new MeterProvider({ readers: [failingFlushReader] });
  await rejects(observeMetricLifecycle(() => failingFlushProvider.forceFlush(), "flush", "runtime", flushFailure.binding), (error) => error === flushError);
  deepEqual(flushFailure.records, [envelope("observability.metric-flush-failed", { phase: "flush", boundary: "exporter", reason: "rejected", effect: "unknown" }),
    envelope("observability.metric-flush-failed", { phase: "flush", boundary: "runtime", reason: "rejected", effect: "unknown" })]);
  // Its shutdown must clear the interval even though the existing flush still fails.
  await rejects(failingFlushProvider.shutdown(), (error) => error === flushError);
  const closing = capture(), closeError = new Error("synthetic-shutdown-private"); let shutdowns = 0;
  const closingReader = new ObservedPeriodicMetricReader({ exporter: observeMetricExporter({ export(_data, cb) { cb({ code: 0 }); }, async forceFlush() {}, async shutdown() { shutdowns++; throw closeError; } }, closing.binding), exportIntervalMillis: 60_000 }, closing.binding);
  const closingProvider = new MeterProvider({ readers: [closingReader] });
  await rejects(observeMetricLifecycle(() => closingProvider.shutdown(), "shutdown", "runtime", closing.binding), (error) => error === closeError);
  await observeMetricLifecycle(() => closingProvider.shutdown(), "shutdown", "runtime", closing.binding);
  await closingProvider.forceFlush(); equal(shutdowns, 1, "failed shutdown does not authorize replay or change provider no-op state");
  deepEqual(closing.records, [envelope("observability.metric-shutdown-failed", { phase: "shutdown", boundary: "exporter", reason: "rejected", effect: "unknown" }),
    envelope("observability.metric-shutdown-failed", { phase: "shutdown", boundary: "runtime", reason: "rejected", effect: "unknown" })]);
}

async function httpExporterObservation(): Promise<void> {
  let requests = 0, fail = true;
  const server = createServer((request, response) => { requests++; request.resume(); response.writeHead(fail ? 400 : 200).end(); });
  await new Promise<void>((resolve, reject) => server.once("error", reject).listen(4318, "127.0.0.1", resolve));
  const fixture = capture();
  const options = { endpoint: "http://127.0.0.1:4318/v1/metrics", region: "eu-west-1", serviceName: "fixture", serviceVersion: "test", deploymentEnvironment: "fixture",
    exportIntervalMs: 60_000, exportTimeoutMs: 1_000, series: [{ sourceName: "fixture.counter", sourceKind: "counter" as const, sourceUnit: "count", instrumentName: "fixture.counter", description: "Fixture counter", allowedLabelNames: [], cardinalityLimit: 4 }] };
  const runtime = createCloudWatchOtelMetricsRuntime(options, fixture.binding);
  const point = { name: metricName("fixture.counter"), kind: "counter" as const, value: 1, unit: metricUnit("count"), recordedAt: isoDateTimeFromDate(new Date()) };
  try {
    runtime.metrics.record(point); await runtime.forceFlush(); equal(requests, 1);
    deepEqual(fixture.records, [envelope("observability.metric-export-failed", { phase: "export", reason: "callback-failed", effect: "unknown" })]);
    fail = false; runtime.metrics.record(point); await runtime.forceFlush(); equal(requests, 2); equal(fixture.records.length, 1);
    await runtime.shutdown(); const afterClose = requests; await runtime.shutdown(); await runtime.forceFlush(); equal(requests, afterClose);
    // Generic adapter is opt-in: an unbound failing exporter remains silent here.
    fail = true; const unbound = createCloudWatchOtelMetricsRuntime(options);
    try { unbound.metrics.record(point); await unbound.forceFlush(); } finally { await unbound.shutdown(); }
    equal(fixture.records.length, 1);
  } finally {
    await runtime.shutdown();
    await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
}

function runnerDispatchProof(): void {
  const root = mkdtempSync(join(tmpdir(), "kanbien-metric-lifecycle-dispatch-"));
  const directory = join(root, "platform/adapters/aws/observability/cloudwatch/tests"); mkdirSync(directory, { recursive: true });
  try {
    for (const [first, second, status, output] of [[0, 0, 0, "first\nsecond\n"], [7, 0, 7, "first\n"], [0, 9, 9, "first\nsecond\n"]] as const) {
      writeFileSync(join(directory, "cloudwatch-otel-adapter-runtime.test.js"), `console.log("first"); process.exitCode = ${first};\n`);
      writeFileSync(join(directory, "cloudwatch-otel-lifecycle-runtime.test.js"), `console.log("second"); process.exitCode = ${second};\n`);
      const child = spawnSync(process.execPath, ["platform/adapters/aws/observability/cloudwatch/tests/run-runtime-tests.mjs"], {
        env: { ...process.env, KANBIEN_CLOUDWATCH_OTEL_RUNTIME_ROOT: root }, encoding: "utf8",
      });
      equal(child.status, status); equal(child.stdout, output); equal(child.stderr, "");
    }
  } finally { rmSync(root, { recursive: true, force: true }); }
}

async function independentPublicSources(): Promise<void> {
  const sources = Array.from({ length: 9 }, (_, ordinal) => coreMonitoringValidationDiagnosticRecord({ operation: "signal-definition", field: "signal-intent", ordinal, reason: "closed-value-rejected", effect: "rejected" }));
  const cause = Object.freeze({ diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1), message: "synthetic-private-source" });
  const records: DiagnosticRecord[] = [], contexts: Array<{ readonly stage: string }> = [];
  const observations: PlatformObservationDiagnostics = { reporter: { report(record, context) { equal(this, observations.reporter); records.push(record); contexts.push(context); return { status: "written" }; } }, context: { capability: "observability", operation: "metrics", stage: "startup" } };
  const data = { resource: resourceFromAttributes({}), scopeMetrics: [] };
  const exporter: PushMetricExporter = { export(_data, callback) { callback({ code: 1, error: cause as never }); }, async forceFlush() {}, async shutdown() {} };
  for (const [property, field] of [["selectAggregation", "aggregation-selector"], ["selectAggregationTemporality", "temporality-selector"]] as const) {
    records.length = 0;
    const getter = Object.defineProperty({ ...exporter }, property, { get() { throw cause; } });
    throws(() => observeMetricExporter(getter, undefined, observations), (error) => error === cause);
    deepEqual(records[0]?.detail, { operation: "metric-runtime-construction", phase: "sink-selection", field, reason: "threw", effect: "unknown" });
    equal(records.length, 10); deepEqual(records.slice(1), sources);
    for (const binding of ["selection", "invocation"] as const) {
      records.length = 0;
      const selector = () => undefined;
      Object.defineProperty(selector, "bind", binding === "selection" ? { get() { throw cause; } } : { value() { throw cause; } });
      throws(() => observeMetricExporter({ ...exporter, [property]: selector } as PushMetricExporter, undefined, observations), (error) => error === cause);
      deepEqual(records[0]?.detail, { operation: "metric-runtime-construction", phase: binding === "selection" ? "sink-selection" : "sink-invocation", field, reason: "threw", effect: "unknown" });
      equal(records.length, 10); deepEqual(records.slice(1), sources);
    }
  }
  const selectionOrder: string[] = [];
  const selectedExporter = { ...exporter };
  for (const property of ["selectAggregation", "selectAggregationTemporality"] as const) {
    const selector = function (this: unknown) { equal(this, selectedExporter); return undefined; };
    Object.defineProperty(selector, "bind", { value(this: unknown, receiver: unknown) { equal(this, selector); equal(receiver, selectedExporter); selectionOrder.push(`bind-${property}`); return Reflect.apply(Function.prototype.bind, selector, [receiver]); } });
    Object.defineProperty(selectedExporter, property, { get() { selectionOrder.push(`read-${property}`); return selector; } });
  }
  observeMetricExporter(selectedExporter, undefined, observations);
  deepEqual(selectionOrder, ["read-selectAggregation", "read-selectAggregationTemporality", "bind-selectAggregation", "bind-selectAggregationTemporality"]);
  records.length = 0;
  const existing = capture();
  observeMetricExporter(exporter, existing.binding, observations).export(data, () => {});
  deepEqual(records, sources, "a positive callback result uses existing lifecycle own evidence, never an invented thrown boundary");
  deepEqual(existing.records, [envelope("observability.metric-export-failed", { phase: "export", reason: "callback-failed", effect: "unknown" })]);
  records.length = 0;
  const callbackFailure = observeMetricExporter({ ...exporter, export(_data, callback) { callback({ code: 0 }); } }, existing.binding, observations);
  throws(() => callbackFailure.export(data, () => { throw cause; }), (error) => error === cause);
  equal(records.length, 10); deepEqual(records.slice(1), sources);
  deepEqual(records[0]?.detail, { operation: "metric-export", phase: "sink-invocation", field: "result", reason: "threw", effect: "unknown" });
  equal(existing.records.length, 1, "callback failure is not exporter-failed evidence");
  for (const [object, phase] of [
    [{ ...exporter, get export(): never { throw cause; } }, "sink-selection"],
    [{ ...exporter, export() { throw cause; } }, "export"],
  ] as const) {
    records.length = 0;
    throws(() => observeMetricExporter(object, undefined, observations).export(data, () => {}), (error) => error === cause);
    deepEqual(records[0]?.detail, { operation: "metric-export", phase, reason: "threw", effect: "unknown" });
    deepEqual(records.slice(1), sources);
  }
  records.length = 0;
  let callbacks = 0, codeReads = 0, privateErrorReads = 0;
  observeMetricExporter({ ...exporter, export(_data, callback) { callback({ get code(): never { codeReads++; throw cause; } }); } }, undefined, observations)
    .export(data, () => { callbacks++; });
  equal(codeReads, 1); equal(callbacks, 1);
  deepEqual(records[0]?.detail, { operation: "metric-export", phase: "result-projection", field: "result", reason: "threw", effect: "observation-incomplete" });
  deepEqual(records.slice(1), sources);
  records.length = 0;
  observeMetricExporter({ ...exporter, export(_data, callback) { callback({ code: 1, get error(): never { privateErrorReads++; throw cause; } }); } }, undefined, observations).export(data, () => {});
  equal(privateErrorReads, 0); equal(records.length, 0, "source accessors are unavailable, not invoked");
  for (const phase of ["flush", "shutdown"] as const) for (const boundary of ["runtime", "exporter"] as const) for (const rejected of [false, true]) {
    records.length = 0; contexts.length = 0;
    let calls = 0;
    const operation = () => { calls++; if (!rejected) throw cause; return Promise.reject(cause); };
    if (rejected) await rejects(observeMetricLifecycle(operation, phase, boundary, undefined, observations), (error) => error === cause);
    else throws(() => observeMetricLifecycle(operation, phase, boundary, undefined, observations), (error) => error === cause);
    equal(calls, 1); equal(records.length, 10); deepEqual(records.slice(1), sources);
    deepEqual(records[0]?.detail, { operation: `metric-${phase}`, phase, reason: rejected ? "rejected" : "threw", effect: "unknown" });
    equal(contexts.every((context) => context.stage === (phase === "shutdown" ? "shutdown" : "runtime")), true);
  }
  const originalGetMeter = MeterProvider.prototype.getMeter;
  let provider: MeterProvider | undefined;
  let timeoutReads = 0;
  const runtimeOptions = new Proxy({ endpoint: "http://127.0.0.1:4318/v1/metrics", region: "eu-west-1", serviceName: "fixture", serviceVersion: "test", deploymentEnvironment: "fixture", exportIntervalMs: 60_000, exportTimeoutMs: 1_000,
    series: [{ sourceName: "fixture.counter", sourceKind: "counter" as const, sourceUnit: "count", instrumentName: "fixture.counter", description: "Fixture counter", allowedLabelNames: [], cardinalityLimit: 4 }] },
    { get(target, key, receiver) { if (key === "exportTimeoutMs" && ++timeoutReads > 1) throw cause; return Reflect.get(target, key, receiver); } });
  try {
    MeterProvider.prototype.getMeter = function (...args) { provider = this; return Reflect.apply(originalGetMeter, this, args); };
    const runtime = createCloudWatchOtelMetricsRuntime(runtimeOptions, undefined, observations);
    for (const phase of ["flush", "shutdown"] as const) {
      records.length = 0;
      throws(() => phase === "flush" ? runtime.forceFlush() : runtime.shutdown(), (error) => error === cause);
      deepEqual(records[0]?.detail, { operation: `metric-${phase}`, phase: "input-projection", field: "export-timeout", reason: "threw", effect: "not-attempted" });
      equal(records.length, 10); deepEqual(records.slice(1), sources);
    }
    equal(timeoutReads, 3, "one original timeout read for reader construction and each lifecycle invocation");
  } finally { MeterProvider.prototype.getMeter = originalGetMeter; await provider?.shutdown(); }
  const originalCollect = PeriodicExportingMetricReader.prototype.collect;
  const collection = capture();
  const reader = new ObservedPeriodicMetricReader({ exporter, exportIntervalMillis: 60_000 }, collection.binding, observations);
  try {
    let errorReads = 0, lengthReads = 0, ninthReads = 0;
    const publicErrors = Array.from({ length: 9 }, () => cause);
    Object.defineProperty(publicErrors, "8", { get() { ninthReads++; throw cause; } });
    const errors = new Proxy(publicErrors, { get(target, property, receiver) { if (property === "length") lengthReads++; return Reflect.get(target, property, receiver); } });
    const result: CollectionResult = { resourceMetrics: data, get errors() { errorReads++; return errors as never; } };
    PeriodicExportingMetricReader.prototype.collect = async () => result;
    records.length = 0;
    equal(await reader.collect(), result);
    equal(errorReads, 1); equal(lengthReads, 1); equal(ninthReads, 0);
    equal(records.length, 72);
    deepEqual(records, Array.from({ length: 8 }, () => sources).flat());
    deepEqual(collection.records, [envelope("observability.metric-collection-issues", { phase: "collection", reason: "errors-returned", effect: "collection-result-returned-completeness-unknown", errorCount: 9 })]);
    records.length = 0;
    const inaccessible: CollectionResult = { resourceMetrics: data, get errors(): never { throw cause; } };
    PeriodicExportingMetricReader.prototype.collect = async () => inaccessible;
    equal(await reader.collect(), inaccessible);
    deepEqual(records[0]?.detail, { operation: "metric-collection", phase: "result-projection", field: "result", reason: "threw", effect: "observation-incomplete" });
    deepEqual(records.slice(1), sources);
    records.length = 0;
    const descriptorFailure = new Proxy([cause, cause], { getOwnPropertyDescriptor(target, key) { if (key === "1") throw cause; return Reflect.getOwnPropertyDescriptor(target, key); } });
    const partial: CollectionResult = { resourceMetrics: data, errors: descriptorFailure as never };
    PeriodicExportingMetricReader.prototype.collect = async () => partial;
    equal(await reader.collect(), partial);
    equal(records.length, 19); deepEqual(records.slice(0, 9), sources);
    deepEqual(records[9]?.detail, { operation: "metric-collection", phase: "result-projection", field: "result", reason: "threw", effect: "observation-incomplete" });
    deepEqual(records.slice(10), sources);
    records.length = 0;
    PeriodicExportingMetricReader.prototype.collect = async () => { throw cause; };
    await rejects(reader.collect(), (error) => error === cause);
    deepEqual(records[0]?.detail, { operation: "metric-collection", phase: "collection", reason: "rejected", effect: "unknown" });
    deepEqual(records.slice(1), sources);
    equal(JSON.stringify(records).includes("synthetic-private-source"), false);
  } finally { PeriodicExportingMetricReader.prototype.collect = originalCollect; }
  const hostile: PlatformObservationDiagnostics = { reporter: { report() { return Promise.reject(cause) as never; } }, context: observations.context };
  await rejects(observeMetricLifecycle(() => Promise.reject(cause), "flush", "runtime", undefined, hostile), (error) => error === cause);
  const hostileBinding: PlatformMetricLifecycleDiagnosticBinding = { report() { const pending = Promise.reject(cause); Object.defineProperty(pending, "then", { get() { throw cause; } }); return pending; } };
  await rejects(observeMetricLifecycle(() => Promise.reject(cause), "flush", "runtime", hostileBinding), (error) => error === cause);
  await new Promise<void>((resolve) => setImmediate(resolve));
}

async function main(): Promise<void> { runnerDispatchProof(); await sdkBoundaryBaseline(); await wrapperPreservation(); await collectionAndSdkObservation(); await independentPublicSources(); await httpExporterObservation(); }
void main().then(() => console.log("Metric lifecycle SDK boundaries, preservation, uncertainty and local HTTP export passed."));
