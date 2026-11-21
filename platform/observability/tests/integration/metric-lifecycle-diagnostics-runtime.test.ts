import { deepEqual, equal, throws } from "node:assert/strict";
import { parseDiagnosticRecord, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import { createPlatformDiagnosticReporter, createPlatformMetricDiagnosticBinding, createPlatformMetricLifecycleDiagnosticBinding,
  platformObservabilityDiagnosticCatalog, platformMetricDiagnosticLimit, attachPlatformMetricDiagnostic,
  metricCollectionDiagnostic, metricCollectionFailureDiagnostic, metricCollectionIssuesRecord, metricCollectionFailureRecord, metricExportFailureRecord, metricLifecycleFailureRecord } from "../../src/index";

const logs: LogRecord[] = [];
const reporter = createPlatformDiagnosticReporter({ catalogs: [platformObservabilityDiagnosticCatalog],
  clock: { now: () => new Date("2026-10-30T00:00:00.000Z") }, logger: { write(record) { logs.push(record); } } });
const binding = createPlatformMetricLifecycleDiagnosticBinding(reporter, { capability: "observability" });
const expected: DiagnosticRecord[] = [
  { schema: "core/diagnostic-record/v1", code: "observability.metric-collection-issues", definitionVersion: 1, detail: { phase: "collection", reason: "errors-returned", effect: "collection-result-returned-completeness-unknown", errorCount: 2 } },
  { schema: "core/diagnostic-record/v1", code: "observability.metric-collection-failed", definitionVersion: 1, detail: { phase: "collection", reason: "rejected", effect: "unknown" } },
  { schema: "core/diagnostic-record/v1", code: "observability.metric-collection-failed", definitionVersion: 1, detail: { phase: "collection", reason: "sdk-timeout", effect: "unknown" } },
  { schema: "core/diagnostic-record/v1", code: "observability.metric-export-failed", definitionVersion: 1, detail: { phase: "export", reason: "callback-failed", effect: "unknown" } },
  { schema: "core/diagnostic-record/v1", code: "observability.metric-export-failed", definitionVersion: 1, detail: { phase: "export", reason: "invocation-threw", effect: "unknown" } },
];
const actual = [metricCollectionIssuesRecord(2), metricCollectionFailureRecord("rejected"), metricCollectionFailureRecord("sdk-timeout"),
  metricExportFailureRecord("callback-failed"), metricExportFailureRecord("invocation-threw")];
deepEqual(actual, expected, "independent literal expectations distinguish each actual predicate");
for (const bad of [
  { phase: "collection", reason: "errors-returned", effect: "collection-result-returned-completeness-unknown" },
  { phase: "collection", reason: "errors-returned", effect: "unknown", errorCount: 1 },
  { phase: "collection", reason: "rejected", effect: "collection-result-returned-completeness-unknown", errorCount: 1 },
]) equal(parseDiagnosticRecord(metricCollectionDiagnostic, { schema: "core/diagnostic-record/v1", code: "observability.metric-collection-issues", definitionVersion: 1, detail: bad }).ok, false);
equal(parseDiagnosticRecord(metricCollectionFailureDiagnostic, { ...expected[1]!, detail: { phase: "collection", reason: "rejected", effect: "unknown", errorCount: 1 } }).ok, false);
actual.forEach((record) => binding.report(record, record.code === "observability.metric-export-failed" ? "export" : "collection"));
for (const phase of ["flush", "shutdown"] as const) for (const boundary of ["exporter", "runtime"] as const) for (const reason of ["rejected", "sdk-timeout", "invocation-threw"] as const) {
  const record = metricLifecycleFailureRecord(phase, boundary, reason);
  deepEqual(record, { schema: "core/diagnostic-record/v1", code: `observability.metric-${phase}-failed`, definitionVersion: 1, detail: { phase, boundary, reason, effect: "unknown" } });
  binding.report(record, phase);
}
equal(logs.length, 17);
equal(logs[0]?.fields?.["stage"], "runtime"); equal(logs[11]?.fields?.["stage"], "shutdown");
deepEqual(logs.slice(0, 5).map((record) => record.fields?.["diagnostic"]), expected);
for (const count of [0, -1, NaN, Infinity, 1.5]) throws(() => metricCollectionIssuesRecord(count), /OBSERVABILITY_METRIC_LIFECYCLE_DIAGNOSTIC_INVALID/);
let getterReads = 0;
const getterRecord = Object.defineProperty({}, "code", { get() { getterReads++; throw new Error("synthetic-private"); } });
binding.report(getterRecord as never, "export"); equal(getterReads, 0);
binding.report({ ...expected[3]!, detail: { phase: "export", reason: "synthetic-private", effect: "unknown" } }, "export");
binding.report(expected[3]!, "synthetic-private" as never);
equal(logs.length, 17);
// Lifecycle records must not enter the trusted same-error/same-metric-port path.
const recording = createPlatformMetricDiagnosticBinding(reporter, { capability: "observability", stage: "runtime" });
recording.report(expected[3]!, "metric"); equal(logs.length, 17);
throws(() => attachPlatformMetricDiagnostic({ record() {} }, new Error("safe"), expected[3]!), /OBSERVABILITY_METRIC_DIAGNOSTIC_INVALID/);
// Per-runtime attempts are bounded even when a sink cannot accept delivery.
let attempts = 0;
const unavailable = createPlatformMetricLifecycleDiagnosticBinding({ report() { attempts++; return { status: "unavailable" }; } }, { capability: "observability" });
for (let index = 1; index <= 1_000; index++) unavailable.report(metricCollectionIssuesRecord(index), "collection");
equal(attempts, platformMetricDiagnosticLimit);
let recursiveAttempts = 0;
const recursive = createPlatformMetricLifecycleDiagnosticBinding({ report(record) {
  recursiveAttempts++; recursive.report(record, "collection"); throw new Error("synthetic-sink-private");
} }, { capability: "observability" });
recursive.report(expected[0]!, "collection"); recursive.report(expected[0]!, "collection"); equal(recursiveAttempts, 1);
const disabled = createPlatformMetricLifecycleDiagnosticBinding(undefined, { capability: "observability" });
disabled.report(expected[3]!, "export");
equal(JSON.stringify(logs).includes("synthetic-private"), false);
console.log("Metric lifecycle contracts, bounded delivery and recording provenance passed.");
