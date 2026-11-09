import { deepEqual, equal, throws } from "node:assert/strict";
import { createDiagnosticRecord, parseDiagnosticRecord } from "@kanbien/core/diagnostics";
import { createPlatformDiagnosticReporter, observabilityConfigurationDiagnostic, observabilityConfigurationRecord, observabilityConstructionRecord,
  platformObservabilityDiagnosticCatalog, validatePlatformMetricSeries, validatePlatformReadinessConfiguration, type PlatformMetricSeries } from "../../src/index";

const row: PlatformMetricSeries = { sourceName: "fixture.metric", sourceKind: "gauge", sourceUnit: "count", instrumentName: "fixture.instrument",
  description: "Fixture description", allowedLabelNames: ["outcome"], cardinalityLimit: 16 };
function issues(value: unknown) { const r = validatePlatformMetricSeries(value); equal(r.ok, false); if (r.ok) throw new Error("Expected rejected series"); return r.error; }
deepEqual(validatePlatformMetricSeries([row]), { ok: true, value: [row] });
for (const [raw, reason] of [[undefined, "missing"], [null, "wrong-shape"], [{}, "wrong-shape"], [[], "empty"]] as const) deepEqual(issues(raw), { issues: [{ setting: "metrics.series", reason }], truncated: false });
deepEqual(issues([null]).issues, [{ setting: "metrics.series", reason: "wrong-shape", index: 0 }]);
for (const [key, setting] of [["sourceName", "series.source-name"], ["sourceKind", "series.source-kind"], ["sourceUnit", "series.source-unit"],
  ["instrumentName", "series.instrument-name"], ["description", "series.description"]] as const) {
  for (const [raw, reason] of [[undefined, "missing"], [null, "wrong-type"], [42, "wrong-type"], ["", "blank"], [" \t", "blank"]] as const) {
    deepEqual(issues([{ ...row, [key]: raw }]).issues, [{ setting, reason, index: 0 }]);
  }
}
deepEqual(issues([{ ...row, sourceKind: "synthetic-sensitive" }]).issues, [{ setting: "series.source-kind", reason: "unsupported", index: 0 }]);
for (const [raw, reason] of [[undefined, "missing"], ["16", "wrong-type"], [null, "wrong-type"], [NaN, "invalid-integer"], [Infinity, "not-finite"],
  [1.5, "invalid-integer"], [0, "not-positive"], [-1, "not-positive"], [1001, "out-of-range"]] as const) {
  deepEqual(issues([{ ...row, cardinalityLimit: raw }]).issues, [{ setting: "series.cardinality", reason, index: 0 }]);
}
for (const limit of [1, 1000]) equal(validatePlatformMetricSeries([{ ...row, cardinalityLimit: limit }]).ok, true);
for (const [raw, reason] of [[undefined, "missing"], [null, "wrong-type"], ["labels", "wrong-type"]] as const) {
  deepEqual(issues([{ ...row, allowedLabelNames: raw }]).issues, [{ setting: "series.allowed-labels", reason, index: 0 }]);
}
deepEqual(issues([{ ...row, allowedLabelNames: ["outcome", "Bad", 42, "outcome"] }]).issues, [
  { setting: "series.allowed-labels", reason: "invalid-format", index: 0, attributeIndex: 1 },
  { setting: "series.allowed-labels", reason: "wrong-type", index: 0, attributeIndex: 2 },
  { setting: "series.allowed-labels", reason: "duplicate", index: 0, attributeIndex: 3, relatedIndex: 0 },
]);
const distribution = { ...row, sourceKind: "histogram" as const };
deepEqual(issues([distribution]).issues, [{ setting: "series.buckets", reason: "required-for-kind", index: 0 }]);
deepEqual(issues([{ ...distribution, histogramBucketBoundaries: [] }]).issues, [{ setting: "series.buckets", reason: "empty", index: 0 }]);
deepEqual(issues([{ ...row, histogramBucketBoundaries: [] }]).issues, [{ setting: "series.buckets", reason: "forbidden-for-kind", index: 0 }]);
deepEqual(issues([{ ...distribution, histogramBucketBoundaries: "private" }]).issues, [{ setting: "series.buckets", reason: "wrong-type", index: 0 }]);
deepEqual(issues([{ ...distribution, histogramBucketBoundaries: [1, 1, 0, "private", Infinity, 4, 3] }]).issues, [
  { setting: "series.buckets", reason: "not-strictly-increasing", index: 0, attributeIndex: 1, relatedIndex: 0 },
  { setting: "series.buckets", reason: "not-positive", index: 0, attributeIndex: 2 },
  { setting: "series.buckets", reason: "wrong-type", index: 0, attributeIndex: 3 },
  { setting: "series.buckets", reason: "not-finite", index: 0, attributeIndex: 4 },
  { setting: "series.buckets", reason: "not-strictly-increasing", index: 0, attributeIndex: 6, relatedIndex: 5 },
]);
for (const sourceKind of ["timer", "histogram"] as const) equal(validatePlatformMetricSeries([{ ...row, sourceKind, histogramBucketBoundaries: [0.1, 1, 2.5] }]).ok, true);
deepEqual(issues([row, { ...row, description: "" }]).issues, [
  { setting: "series.source-name", reason: "duplicate", index: 1, relatedIndex: 0 },
  { setting: "series.instrument-name", reason: "duplicate", index: 1, relatedIndex: 0 },
  { setting: "series.description", reason: "blank", index: 1 },
]);
equal(validatePlatformMetricSeries([{ ...row, sourceName: " source ", sourceUnit: " count ", description: " description ", instrumentName: " instrument ", allowedLabelNames: [], extra: "ignored" }]).ok, true, "nonempty text is preserved, not silently normalized or tightened");
let getterReads = 0;
const getter = () => { getterReads++; throw new Error("synthetic-sensitive-canary"); };
for (const key of Object.keys(row)) issues([Object.defineProperty({ ...row }, key, { enumerable: true, get: getter })]);
issues(Object.defineProperty([row], "0", { enumerable: true, get: getter }));
issues(Object.defineProperty([row], "map", { get: getter }));
issues([ { ...row, allowedLabelNames: Object.defineProperty(["outcome"], "0", { enumerable: true, get: getter }) } ]);
equal(getterReads, 0);
const overflow = issues(Array.from({ length: 50 }, () => null)); equal(overflow.issues.length, 32); equal(overflow.truncated, true);
deepEqual(overflow.issues.map((i) => i.index), Array.from({ length: 32 }, (_, i) => i));
equal(issues(Array.from({ length: 32 }, () => null)).truncated, false);

const schedule = { target: "fixture-target", scope: "fixture-scope", workload: "fixture-workload", dependency: "fixture-dependency", cadenceMs: 1000, timeoutMs: 100, staleAfterMs: 1100 };
equal(validatePlatformReadinessConfiguration(schedule).ok, true);
for (const key of ["target", "scope", "workload", "dependency"] as const) for (const [raw, reason] of [[undefined, "missing"], [null, "wrong-type"], ["", "blank"], ["Bad", "invalid-format"]] as const) {
  const r = validatePlatformReadinessConfiguration({ ...schedule, [key]: raw }); if (r.ok) throw new Error("Expected invalid identity");
  deepEqual(r.error.issues, [{ setting: "readiness." + key, reason }]);
}
for (const [key, setting] of [["cadenceMs", "readiness.cadence"], ["timeoutMs", "readiness.timeout"], ["staleAfterMs", "readiness.stale-after"]] as const) {
  for (const [raw, reason] of [[undefined, "missing"], [null, "wrong-type"], ["", "blank"], [NaN, "invalid-integer"], [Infinity, "not-finite"], [1.5, "invalid-integer"], [0, "not-positive"]] as const) {
    const r = validatePlatformReadinessConfiguration({ ...schedule, [key]: raw }); if (r.ok) throw new Error("Expected invalid timing"); deepEqual(r.error.issues, [{ setting, reason }]);
  }
}
const independent = validatePlatformReadinessConfiguration({ ...schedule, target: "Bad", timeoutMs: 1000, staleAfterMs: 1000 });
if (independent.ok) throw new Error("Expected independent failures");
deepEqual(independent.error.issues, [{ setting: "readiness.target", reason: "invalid-format" }, { setting: "readiness.timeout", reason: "timeout-not-shorter-than-cadence" }, { setting: "readiness.stale-after", reason: "stale-deadline-too-short" }]);
const accessorSchedule = validatePlatformReadinessConfiguration(Object.defineProperty({ ...schedule }, "cadenceMs", { enumerable: true, get: getter }));
equal(accessorSchedule.ok, false); equal(getterReads, 0);

const diagnostic = observabilityConfigurationRecord(overflow);
equal(parseDiagnosticRecord<unknown>(observabilityConfigurationDiagnostic, diagnostic).ok, true);
equal(JSON.stringify(diagnostic).includes("synthetic"), false);
for (const detail of [{ issues: [], truncated: false, phase: "configuration-validation", effect: "not-started" },
  { ...diagnostic.detail as object, rawValue: "synthetic-sensitive-canary" }, { ...diagnostic.detail as object, issues: [{ setting: "unknown", reason: "missing" }] },
  { ...diagnostic.detail as object, issues: [{ setting: "metrics.series", reason: "missing", index: -1 }] },
  { ...diagnostic.detail as object, issues: [{ setting: "metrics.series", reason: "missing", attributeIndex: 1.5 }] }]) {
  equal(createDiagnosticRecord<unknown>(observabilityConfigurationDiagnostic, detail).ok, false);
}
throws(() => observabilityConfigurationRecord(Object.defineProperty({ issues: [], truncated: false }, "issues", { enumerable: true, get: getter })), /OBSERVABILITY_CONFIGURATION_DIAGNOSTIC_INVALID/);
equal(getterReads, 0);
const construction = observabilityConstructionRecord();
deepEqual(construction.detail, { phase: "runtime-construction", reason: "unclassified-construction-failure", effect: "not-assessed" });
const logs: unknown[] = [];
const reporter = createPlatformDiagnosticReporter({ catalogs: [platformObservabilityDiagnosticCatalog], logger: { write: record => logs.push(record) }, clock: { now: () => new Date(0) } });
equal(reporter.report(diagnostic, { capability: "observability", operation: "configure", stage: "configuration" }).status, "written");
equal(logs.length, 1);
const unavailable = createPlatformDiagnosticReporter({ catalogs: [platformObservabilityDiagnosticCatalog], logger: { write() { throw Error("private"); } }, clock: { now: () => new Date(0) } });
equal(unavailable.report(diagnostic, { capability: "observability", operation: "configure", stage: "configuration" }).status, "unavailable");
console.log("Observability configuration: exact predicates, positions, relationships, bounds, safe constructors and delivery passed.");
