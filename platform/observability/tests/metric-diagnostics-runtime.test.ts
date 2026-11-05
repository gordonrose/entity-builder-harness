import { deepEqual, equal, throws } from "node:assert/strict";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { metricName, type MetricPoint, type Metrics } from "@kanbien/core/monitoring";
import type { LogRecord } from "@kanbien/core/logging";
import type { PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { recordPlatformMetric, recordPlatformHealthMetric, recordPlatformJobMetric, recordPlatformRequestMetric,
  createPlatformMetricDiagnosticBinding, createPlatformDiagnosticReporter, createPlatformSafeLogger,
  platformObservabilityDiagnosticCatalog, attachPlatformMetricDiagnostic, metricCreationRecord, metricRecordingRecord,
  metricRejectionRecord, platformMetricDiagnosticLimit, createPlatformReadinessObserver } from "../src/index";
import { createPlatformMetricLifecycleDiagnosticBinding, metricCollectionIssuesRecord } from "../src/index";

const clock = { now: () => new Date("2026-10-29T00:00:00.000Z") };
const valid = { name: "fixture.point" };
function capture() {
  const logs: LogRecord[] = [];
  const reporter = createPlatformDiagnosticReporter({ catalogs: [platformObservabilityDiagnosticCatalog], clock,
    logger: createPlatformSafeLogger({ write: (record) => logs.push(record) }) });
  const binding = createPlatformMetricDiagnosticBinding(reporter, { capability: "observability", stage: "request" });
  return { logs, binding, options: { binding, operation: "metric" as const },
    records: () => logs.map((log) => log.fields?.["diagnostic"] as DiagnosticRecord) };
}
function detail(record: DiagnosticRecord | undefined): unknown { return record?.detail; }

async function main(): Promise<void> {
  const producers = require("../src/metric-diagnostics") as Record<string, unknown>;
  for (const key of ["metricPreparationRecord", "metricRecordingRecord"] as const) {
    const descriptor = Object.getOwnPropertyDescriptor(producers, key)!;
    for (const mode of ["throw", "undefined", "invalid"] as const) {
      const fixture = capture(); let calls = 0;
      try {
        Object.defineProperty(producers, key, { ...descriptor, value: () => {
          if (mode === "throw") throw new Error("PRIVATE_METRIC_BUILDER");
          return mode === "undefined" ? undefined : { code: "private-canary" };
        } });
        recordPlatformMetric({ record() { calls++; throw new Error("PRIVATE_METRIC_OPERATION"); } }, clock,
          key === "metricPreparationRecord" ? { name: "" } : valid, fixture.options);
        equal(calls, key === "metricPreparationRecord" ? 0 : 1);
        deepEqual(fixture.records(), [{ schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1,
          detail: { reason: mode === "throw" ? "construction-threw" : mode === "undefined" ? "construction-rejected" : "evidence-rejected" } }]);
        equal(JSON.stringify(fixture.logs).includes("PRIVATE_"), false);
      } finally { Object.defineProperty(producers, key, descriptor); }
    }
  }
  for (const [input, expected] of [
    [{ name: "" }, { field: "name", reason: "empty" }],
    [{ name: " fixture.point" }, { field: "name", reason: "untrimmed" }],
    [{ name: "Fixture.point" }, { field: "name", reason: "invalid-format" }],
    [{ ...valid, unit: "" }, { field: "unit", reason: "empty" }],
    [{ ...valid, unit: "ms " }, { field: "unit", reason: "untrimmed" }],
    [{ ...valid, unit: "MS" }, { field: "unit", reason: "invalid-format" }],
    [{ ...valid, labels: { fine: 1, Bad: "synthetic-canary" } }, { field: "label", reason: "invalid-format", index: 1 }],
    [{ ...valid, labels: { password: "synthetic-canary" } }, { field: "label", reason: "unsafe-name", index: 0 }],
    [{ ...valid, labels: { safe: NaN } }, { field: "label", reason: "not-finite", index: 0 }],
    [{ ...valid, labels: { safe: "" } }, { field: "label", reason: "empty", index: 0 }],
    [{ ...valid, labels: { safe: "x".repeat(129) } }, { field: "label", reason: "too-long", index: 0 }],
  ] as const) {
    const fixture = capture(); let calls = 0;
    recordPlatformMetric({ record() { calls++; } }, clock, input, fixture.options);
    equal(calls, 0, "preparation rejection must precede the metric call");
    equal(fixture.records()[0]?.code, "observability.metric-preparation-failed");
    equal(fixture.records()[0]?.definitionVersion, 1);
    deepEqual(detail(fixture.records()[0]), { ...expected, phase: "point-preparation", effect: "recording-not-attempted" });
    equal(fixture.logs[0]?.fields?.["operation"], "metric");
    equal(JSON.stringify(fixture.logs).includes("synthetic-canary"), false);
  }
  const ordered = capture();
  recordPlatformMetric({ record() { throw new Error("must not call"); } }, { now() { throw new Error("clock-canary"); } }, { name: "", unit: "" }, ordered.options);
  deepEqual(detail(ordered.records()[0]), { field: "name", reason: "empty", phase: "point-preparation", effect: "recording-not-attempted" });
  const points: MetricPoint[] = [], accepted = capture();
  const metrics: Metrics = { record: (point) => { points.push(point); } };
  recordPlatformMetric(metrics, clock, { ...valid, kind: "gauge", value: -2, labels: { safe: "x".repeat(128), finite: -1, zero: 0, truth: false, omitted: undefined } }, accepted.options);
  deepEqual(points, [{ name: "fixture.point", kind: "gauge", value: -2, unit: "count", recordedAt: "2026-10-29T00:00:00.000Z",
    labels: { safe: "x".repeat(128), finite: -1, zero: 0, truth: false } }]);
  equal(accepted.logs.length, 0);
  // Old three-argument helpers and point kind/value acceptance are unchanged.
  recordPlatformMetric(metrics, clock, valid);
  recordPlatformHealthMetric(metrics, clock, { healthState: "healthy" });
  recordPlatformJobMetric(metrics, clock, { job: "fixture.job", status: "succeeded" });
  recordPlatformRequestMetric(metrics, clock, { method: "GET", route: "fixture.route", status: 200, latencyMs: 1 });
  equal(points.length, 5);
  let labelReads = 0;
  recordPlatformMetric(metrics, clock, Object.defineProperty({ ...valid }, "labels", { get() { labelReads++; return { safe: true }; } }));
  equal(labelReads, 2, "retain the established conditional label read semantics");
  const receiverPort: Metrics = { record() { equal(this, receiverPort); } };
  recordPlatformMetric(receiverPort, clock, valid);
  const reads: string[] = [];
  const orderedPort = Object.defineProperty({}, "record", { get() { reads.push("recorder"); return function(this: unknown) { equal(this, orderedPort); reads.push("invoke"); }; } }) as Metrics;
  const orderedInput = Object.defineProperties({}, Object.fromEntries(Object.entries({ name: "fixture.point", kind: "counter", value: 1, unit: "count", labels: { safe: true } })
    .map(([field, value]) => [field, { get() { reads.push(field); return value; } }])));
  recordPlatformMetric(orderedPort, { now() { reads.push("clock"); return clock.now(); } }, orderedInput as never);
  deepEqual(reads, ["recorder", "name", "kind", "value", "unit", "clock", "labels", "labels", "invoke"]);
  const clockFailure = capture();
  recordPlatformMetric(metrics, { now() { throw new Error("clock-canary"); } }, valid, clockFailure.options);
  deepEqual(detail(clockFailure.records()[0]), { field: "clock", reason: "clock-threw", phase: "point-preparation", effect: "recording-not-attempted" });
  const badDate = capture();
  recordPlatformMetric(metrics, { now: () => new Date(NaN) }, valid, badDate.options);
  deepEqual(detail(badDate.records()[0]), { field: "timestamp", reason: "invalid-date", phase: "point-preparation", effect: "recording-not-attempted" });
  const exoticDate = capture();
  recordPlatformMetric(metrics, { now: () => ({ toISOString() { throw new Error("canary"); } } as unknown as Date) }, valid, exoticDate.options);
  equal((detail(exoticDate.records()[0]) as { reason: string }).reason, "unclassified-preparation-failure");
  let original: unknown;
  try { metricName(""); } catch (error) { original = error; }
  for (const [input, expectedField, expectedReason] of [[Object.defineProperty({}, "name", { get() { throw original; } }), "name", "access-failed"],
    [{ name: { length: 1, trim() { throw original; } } }, "name", "wrong-type"],
    [{ name: 42 }, "name", "wrong-type"], [{ ...valid, unit: 42 }, "unit", "wrong-type"],
    [{ ...valid, labels: Object.defineProperty({}, "safe", { enumerable: true, get() { throw original; } }) }, "label", "access-failed"]] as const) {
    const fixture = capture();
    recordPlatformMetric(metrics, clock, input as never, fixture.options);
    deepEqual(detail(fixture.records()[0]), { field: expectedField, reason: expectedReason, phase: "point-preparation", effect: "recording-not-attempted" });
  }
  for (const [property, field] of [["name", "name"], ["kind", "kind"], ["value", "value"], ["unit", "unit"], ["labels", "label"]] as const) {
    const fixture = capture(); let calls = 0;
    const input = Object.defineProperty({ ...valid }, property, { get() { throw new Error("access-private-canary"); } });
    recordPlatformMetric({ record() { calls++; } }, clock, input, fixture.options);
    deepEqual(detail(fixture.records()[0]), { field, reason: "access-failed", phase: "point-preparation", effect: "recording-not-attempted" });
    equal(calls, 0);
  }
  const recorderAccess = capture(); let nameReads = 0;
  recordPlatformMetric(Object.defineProperty({}, "record", { get() { throw new Error("access-private-canary"); } }) as Metrics, clock,
    Object.defineProperty({}, "name", { get() { nameReads++; return "fixture.point"; } }) as never, recorderAccess.options);
  deepEqual(detail(recorderAccess.records()[0]), { field: "recorder", reason: "access-failed", phase: "point-preparation", effect: "recording-not-attempted" });
  equal(nameReads, 0, "a failed recorder lookup must retain the original pre-argument evaluation order");
  let companionAccesses = 0;
  for (const error of [new Error("provider-canary"), { diagnosticRecord: metricCreationRecord(0) },
    Object.defineProperty({}, "diagnosticRecord", { get() { companionAccesses++; throw new Error("must not read"); } }),
    new Proxy({}, { getOwnPropertyDescriptor() { companionAccesses++; throw new Error("must not trap"); }, get() { companionAccesses++; throw new Error("must not access"); } })]) {
    const fixture = capture();
    recordPlatformMetric({ record() { throw error; } }, clock, valid, fixture.options);
    deepEqual(detail(fixture.records()[0]), { reason: "unclassified-invocation-failure", phase: "record-invocation", effect: "unknown" });
    equal(JSON.stringify(fixture.logs).includes("provider-canary"), false);
  }
  equal(companionAccesses, 0, "classification must not even inspect untrusted error companions");
  const malformed = capture(); let publicRecordReads = 0;
  for (const property of ["code", "definitionVersion", "detail"] as const) {
    const bad = Object.defineProperty({ ...metricRecordingRecord() }, property, { get() { publicRecordReads++; throw new Error("record-getter-canary"); } });
    for (let attempt = 0; attempt < 150; attempt++) malformed.binding.report(bad as never, "metric");
    const unchanged = new Error("safe");
    throws(() => attachPlatformMetricDiagnostic(metrics, unchanged, bad as never), /^TypeError: OBSERVABILITY_METRIC_DIAGNOSTIC_INVALID$/);
    equal(Object.getOwnPropertyDescriptor(unchanged, "diagnosticRecord"), undefined);
  }
  equal(publicRecordReads, 0); equal(malformed.logs.length, 0);
  malformed.binding.report(metricRecordingRecord(), "metric");
  equal(malformed.logs.length, 1, "malformed records must not consume the binding budget");
  const observed = capture();
  const port: Metrics = { record() { throw attachPlatformMetricDiagnostic(port, new RangeError("private-canary"), metricRejectionRecord("kind-mismatch", 3)); } };
  recordPlatformMetric(port, clock, valid, observed.options);
  deepEqual(observed.records()[0], metricRejectionRecord("kind-mismatch", 3));
  const foreign = capture();
  let branded: unknown;
  try { port.record(points[0]!); } catch (error) { branded = error; }
  recordPlatformMetric({ record() { throw branded; } }, clock, valid, foreign.options);
  deepEqual(foreign.records()[0], metricRecordingRecord());

  let attempts = 0;
  for (const record of [() => Promise.resolve(), () => Promise.reject(new Error("async-canary")),
    () => ({ get then() { throw new Error("then-canary"); } }) as unknown as Promise<void>]) {
    const fixture = capture();
    recordPlatformMetric({ record() { attempts++; return record(); } }, clock, valid, fixture.options);
    await new Promise<void>((resolve) => setImmediate(resolve));
    equal(fixture.logs.length, attempts === 1 ? 0 : 1);
    if (fixture.logs.length) deepEqual(fixture.records()[0], metricRecordingRecord());
  }
  equal(attempts, 3, "failure handling must not replay a measurement");
  // This file already runs in a separate process under the existing package runner.
  // Observe actual unhandledRejection events, not just the helper's diagnostic count.
  let unhandledRejections = 0, shadowedThenReads = 0, shadowedAttempts = 0;
  const onUnhandled = () => { unhandledRejections++; };
  process.on("unhandledRejection", onUnhandled);
  try {
    const fixture = capture();
    const pending = Promise.reject(new Error("native-promise-private-canary"));
    Object.defineProperty(pending, "then", { get() { shadowedThenReads++; throw new Error("shadowed-then-private-canary"); } });
    recordPlatformMetric({ record() { shadowedAttempts++; return pending; } }, clock, valid, fixture.options);
    await new Promise<void>((resolve) => setImmediate(resolve));
    await new Promise<void>((resolve) => setImmediate(resolve));
    equal(unhandledRejections, 0, "returned native rejection must be handled even when its own then accessor throws");
    equal(shadowedThenReads, 0, "native observation must not consult the shadowed then");
    equal(shadowedAttempts, 1);
    deepEqual(fixture.records(), [{ schema: "core/diagnostic-record/v1", code: "observability.metric-recording-failed", definitionVersion: 1,
      detail: { reason: "unclassified-invocation-failure", phase: "record-invocation", effect: "unknown" } }]);
    equal(JSON.stringify(fixture.logs).includes("private-canary"), false);
  } finally { process.off("unhandledRejection", onUnhandled); }
  const bounded = capture(); let metricCalls = 0;
  const failing: Metrics = { record() { metricCalls++; throw new Error("canary"); } };
  for (let i = 0; i < 500; i++) recordPlatformMetric(failing, clock, valid, { binding: bounded.binding, operation: "request-outcome" });
  equal(metricCalls, 500); equal(bounded.logs.length, 1, "binding budget persists across fresh options literals");
  for (let index = 0; index < 200; index++) bounded.binding.report(metricRejectionRecord("unapproved-label", 0, index), "request-outcome");
  equal(bounded.logs.length, platformMetricDiagnosticLimit);
  equal(bounded.records().slice(0, 127).every((record) => record.code !== "observability.diagnostic-reporting-suppressed"), true);
  deepEqual(bounded.records()[127], { schema: "core/diagnostic-record/v1", code: "observability.diagnostic-reporting-suppressed", definitionVersion: 1,
    detail: { reason: "attempt-limit", limit: 128, attempted: 127, effect: "further-observations-not-attempted" } });
  for (let index = 200; index < 250; index++) bounded.binding.report(metricRejectionRecord("unapproved-label", 0, index), "request-outcome");
  equal(bounded.logs.length, 128); equal(metricCalls, 500);

  let reports = 0;
  let recursive: ReturnType<typeof createPlatformMetricDiagnosticBinding>;
  const reentrant: PlatformDiagnosticReporter = { report() {
    reports++;
    recordPlatformMetric(failing, clock, valid, { binding: recursive, operation: "job" });
    queueMicrotask(() => recordPlatformMetric(failing, clock, valid, { binding: recursive, operation: "metric" }));
    return { status: "written" };
  } };
  recursive = createPlatformMetricDiagnosticBinding(reentrant, { capability: "observability", stage: "request" });
  recordPlatformMetric(failing, clock, valid, { binding: recursive, operation: "metric" });
  await new Promise<void>((resolve) => setImmediate(resolve));
  equal(reports, 1);
  for (const reporter of [undefined, { report() { throw new Error("sink-canary"); } } as PlatformDiagnosticReporter,
    createPlatformDiagnosticReporter({ catalogs: [platformObservabilityDiagnosticCatalog], logger: { write() { throw new Error("sink-canary"); } }, clock }),
    createPlatformDiagnosticReporter({ catalogs: [platformObservabilityDiagnosticCatalog], logger: { write() { throw new Error("must not call"); } }, clock: { now() { throw new Error("clock-canary"); } } })]) {
    recordPlatformMetric(failing, clock, valid, { binding: createPlatformMetricDiagnosticBinding(reporter, { capability: "observability", stage: "request" }), operation: "metric" });
  }
  const readiness = capture();
  const observer = createPlatformReadinessObserver({ identity: { target: "fixture-target", scope: "fixture-scope", workload: "fixture-workload", dependency: "fixture-dependency" },
    probe: async () => ({ readiness: "ready" }), metrics: failing, logger: { write() {} }, clock, timeoutMs: 100,
    allowedDiagnosticCodes: ["fixture.failed"], defaultDiagnosticCode: "fixture.failed",
    diagnostics: { report(record, context) { readiness.binding.report(record, "readiness"); equal(context.operation, "readiness"); return { status: "written" }; } } });
  for (let i = 0; i < 10; i++) equal((await observer.observe()).readiness, "ready");
  equal(readiness.logs.length, 1);
  await bindingSinkCoverage();
  console.log("Metric preparation, rejection provenance, async isolation, bounded independent reporting and readiness wiring passed.");
}

async function bindingSinkCoverage(): Promise<void> {
  const unhandled: unknown[] = [], onUnhandled = (reason: unknown): void => { unhandled.push(reason); };
  process.on("unhandledRejection", onUnhandled);
  try {
    let shadowReads = 0;
    for (const lifecycle of [false, true]) for (const mode of ["native", "shadowed", "thenable", "then-getter", "throw"] as const) {
      let calls = 0;
      const reporter = { report(record: DiagnosticRecord, context: unknown) {
        equal(this, reporter); calls++;
        deepEqual(record, lifecycle ? metricCollectionIssuesRecord(1) : metricRecordingRecord());
        deepEqual(context, { capability: "observability", operation: lifecycle ? "collection" : "metric", stage: lifecycle ? "runtime" : "request" });
        if (mode === "throw") throw new Error("private-sink-canary");
        if (mode === "thenable") return { then(_resolve: unknown, reject: (reason: unknown) => void) { reject(new Error("private-sink-canary")); } };
        if (mode === "then-getter") return Object.defineProperty({}, "then", { get() { throw new Error("private-sink-canary"); } });
        const pending = Promise.reject(new Error("private-sink-canary"));
        if (mode === "shadowed") Object.defineProperty(pending, "then", { get() { shadowReads++; throw new Error("must bypass own then"); } });
        return pending;
      } } as unknown as PlatformDiagnosticReporter;
      if (lifecycle) {
        const binding = createPlatformMetricLifecycleDiagnosticBinding(reporter, { capability: "observability" });
        binding.report(metricCollectionIssuesRecord(1), "collection"); binding.report(metricCollectionIssuesRecord(1), "collection");
        binding.report({ ...metricCollectionIssuesRecord(2), extra: "private-canary" } as DiagnosticRecord, "collection");
      } else {
        const binding = createPlatformMetricDiagnosticBinding(reporter, { capability: "observability", stage: "request" });
        binding.report(metricRecordingRecord(), "metric"); binding.report(metricRecordingRecord(), "metric");
        binding.report({ ...metricRecordingRecord(), extra: "private-canary" } as DiagnosticRecord, "metric");
      }
      equal(calls, 1);
    }
    const records: DiagnosticRecord[] = [];
    const reporter: PlatformDiagnosticReporter = { report(record) { records.push(record); return { status: "unavailable" }; } };
    const binding = createPlatformMetricLifecycleDiagnosticBinding(reporter, { capability: "observability" });
    for (let count = 1; count <= 127; count++) binding.report(metricCollectionIssuesRecord(count), "collection");
    binding.report(metricCollectionIssuesRecord(1), "collection");
    binding.report({ ...metricCollectionIssuesRecord(128), detail: { private: "canary" } }, "collection");
    equal(records.length, 127, "duplicates/malformed input cannot consume the reserved control slot");
    binding.report(metricCollectionIssuesRecord(128), "collection");
    deepEqual(records[127], { schema: "core/diagnostic-record/v1", code: "observability.diagnostic-reporting-suppressed", definitionVersion: 1,
      detail: { reason: "attempt-limit", limit: 128, attempted: 127, effect: "further-observations-not-attempted" } });
    binding.report(metricCollectionIssuesRecord(129), "collection"); equal(records.length, 128);
    await new Promise<void>((resolve) => setImmediate(resolve)); equal(shadowReads, 0); deepEqual(unhandled, []);
  } finally { process.off("unhandledRejection", onUnhandled); }
}
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
