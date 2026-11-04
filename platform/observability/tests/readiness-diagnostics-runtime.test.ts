import { deepEqual, equal, rejects } from "node:assert/strict";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import { platformContractDiagnosticCatalog, type PlatformDiagnosticReporter, type PlatformReadinessObservationEvent } from "@kanbien/platform-contracts";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { platformPersistenceDiagnosticCatalog, persistenceObservedDiagnosticRecord } from "../../persistence/src/diagnostics";
import { platformSecurityDiagnosticCatalog, securityPeerIdentityDiagnosticRecord } from "@kanbien/platform-security";
import { createPlatformDiagnosticReporter, createPlatformReadinessObserver, createPlatformSafeLogger, platformObservabilityDiagnosticCatalog,
  reportPlatformDiagnostic, emitPlatformReadinessObservation, type PlatformReadinessObserverOptions } from "../src/index";
import { corePersistenceValidationRecord } from "@kanbien/core/persistence";

const clock = { now: () => new Date("2026-10-30T00:00:00.000Z") };
const expected = (code: string, detail: unknown) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
async function main(): Promise<void> {
  const logs: LogRecord[] = [], points: unknown[] = [];
  const logger = createPlatformSafeLogger({ write(record) { logs.push(record); } });
  const reporter = createPlatformDiagnosticReporter({ catalogs: [platformObservabilityDiagnosticCatalog, platformPersistenceDiagnosticCatalog, platformSecurityDiagnosticCatalog], logger, clock });
  const observed = () => logs.filter((log) => log.message === "platform.diagnostic.observed").map((log) => log.fields?.["diagnostic"]);
  const options = (overrides: Partial<PlatformReadinessObserverOptions> = {}): PlatformReadinessObserverOptions => ({
    identity: { target: "fixture-target", scope: "fixture-scope", workload: "fixture-workload", dependency: "fixture-dependency" },
    probe: async () => ({ readiness: "not-ready" }), logger, metrics: { record(point) { points.push(point); } }, diagnostics: reporter,
    clock, timeoutMs: 100, allowedDiagnosticCodes: ["persistence.transport-unavailable"], defaultDiagnosticCode: "persistence.transport-unavailable", ...overrides,
  });
  for (const [timeoutMs, reason] of [["private-canary", "wrong-type"], [NaN, "not-finite"], [Infinity, "not-finite"], [0.5, "not-integer"], [0, "not-positive"], [-1, "not-positive"]] as const) {
    logs.length = 0; let calls = 0;
    const event = await createPlatformReadinessObserver(options({ timeoutMs: timeoutMs as number, probe: async () => { calls++; return { readiness: "ready" }; } })).observe();
    equal(calls, 0); equal(event.diagnosticCode, "observability.readiness-configuration-invalid");
    deepEqual(observed(), [expected("observability.readiness-configuration-invalid", { field: "timeout", reason, phase: "configuration", effect: "probe-not-invoked" })]);
  }
  for (const diagnosticCode of [undefined, "arbitrary-private-canary", "persistence.transport-unavailable"]) {
    logs.length = 0;
    const event = await createPlatformReadinessObserver(options({ probe: async () => ({ readiness: "not-ready", ...(diagnosticCode === undefined ? {} : { diagnosticCode }) }) })).observe();
    equal(event.diagnosticCode, diagnosticCode === "persistence.transport-unavailable" ? diagnosticCode : "observability.readiness-probe-not-ready");
    deepEqual(observed(), [expected("observability.readiness-probe-not-ready", { phase: "result", effect: "returned-not-ready" })]);
  }
  const primary = persistenceObservedDiagnosticRecord({ classification: "tls_trust_invalid", phase: "pool_query", code_status: "recognized" }, "readiness");
  const related = securityPeerIdentityDiagnosticRecord("hostname-mismatch");
  for (const mode of ["throw", "reject", "returned"] as const) {
    logs.length = 0; let calls = 0;
    const error = Object.assign(new Error("private-canary"), { diagnosticRecord: primary, relatedDiagnosticRecords: [related] });
    const event = await createPlatformReadinessObserver(options({ allowedDiagnosticCodes: [primary.code], defaultDiagnosticCode: primary.code,
      probe: () => { calls++; if (mode === "throw") throw error; if (mode === "reject") return Promise.reject(error);
        return Promise.resolve({ readiness: "not-ready", diagnosticCode: primary.code, diagnosticRecord: primary, relatedDiagnosticRecords: [related] }); } })).observe();
    equal(calls, 1);
    const generic = mode === "throw" ? expected("observability.readiness-probe-threw", { phase: "invocation", effect: "unknown" })
      : mode === "reject" ? expected("observability.readiness-probe-rejected", { phase: "completion", effect: "unknown" })
      : expected("observability.readiness-probe-not-ready", { phase: "result", effect: "returned-not-ready" });
    equal(event.diagnosticCode, mode === "returned" ? primary.code : generic.code);
    deepEqual(observed(), [generic, primary, related]);
    deepEqual(logs.filter((log) => log.message === "platform.diagnostic.observed").map((log) => log.fields?.["capability"]), ["observability", "observability", "observability"]);
    equal(JSON.stringify(logs).includes("private-canary"), false);
  }
  logs.length = 0; let finish!: (value: { readiness: "ready" }) => void; let calls = 0;
  const late = new Promise<{ readiness: "ready" }>((resolve) => { finish = resolve; });
  const event = await createPlatformReadinessObserver(options({ timeoutMs: 1, probe: () => { calls++; return late; } })).observe();
  equal(event.diagnosticCode, "observability.readiness-probe-deadline-observed");
  deepEqual(observed(), [expected("observability.readiness-probe-deadline-observed", { phase: "deadline", effect: "unknown" })]);
  const before = logs.length; finish({ readiness: "ready" }); await late; await Promise.resolve();
  equal(calls, 1); equal(logs.length, before, "late completion does not emit again or cancel/replay work");
  logs.length = 0;
  await rejects(createPlatformReadinessObserver(options({ allowedDiagnosticCodes: [], defaultDiagnosticCode: "unselected.code" })).observe(), /PLATFORM_READINESS_OBSERVATION_DIAGNOSTIC_POLICY_INVALID/);
  await rejects(createPlatformReadinessObserver(options({ allowedDiagnosticCodes: ["invalid-without-namespace"], defaultDiagnosticCode: "invalid-without-namespace" })).observe(), /PLATFORM_OPERATIONAL_EVENT_INVALID/);
  equal(logs.length, 0, "invalid existing policy must still reject before emission");
  const ready = await createPlatformReadinessObserver(options({ probe: async () => ({ readiness: "ready" }), allowedDiagnosticCodes: [] })).observe();
  equal(ready.readiness, "ready"); equal(ready.diagnosticCode, undefined); deepEqual(observed(), []);

  let getters = 0;
  const malformed = Object.defineProperty({ readiness: "not-ready" as const }, "diagnosticRecord", { get() { getters++; throw new Error("private-canary"); } });
  const bad = { schema: "core/diagnostic-record/v1", code: primary.code, definitionVersion: 1, detail: { private: "private-canary" } } as DiagnosticRecord;
  for (const evidence of [malformed, { readiness: "not-ready" as const, diagnosticRecord: bad, relatedDiagnosticRecords: [related] }]) {
    logs.length = 0;
    await createPlatformReadinessObserver(options({ probe: async () => evidence })).observe();
    equal(JSON.stringify(logs).includes("private-canary"), false);
  }
  equal(getters, 0);
  for (const diagnostics of [undefined, { report() { throw new Error("private-canary"); } } as PlatformDiagnosticReporter]) {
    let count = 0;
    const { diagnostics: _omitted, ...isolatedOptions } = options({ logger: { write() { throw new Error("private-canary"); } }, probe: async () => { count++; return { readiness: "not-ready" }; } });
    const isolated = await createPlatformReadinessObserver({ ...isolatedOptions, ...(diagnostics === undefined ? {} : { diagnostics }) }).observe();
    equal(isolated.readiness, "not-ready"); equal(count, 1);
  }
  // Runtime-violating reporters cannot orphan native rejection behind an own then.
  const unhandled: unknown[] = [], onUnhandled = (reason: unknown): void => { unhandled.push(reason); };
  process.on("unhandledRejection", onUnhandled);
  try {
    let thenReads = 0;
    for (const kind of ["native", "thenable", "getter"] as const) {
      const rejected = Promise.reject(new Error("private-canary"));
      if (kind === "native") Object.defineProperty(rejected, "then", { get() { thenReads++; throw new Error("private-canary"); } });
      const returned = kind === "native" ? rejected : kind === "thenable" ? { then(_resolve: unknown, reject: (reason: unknown) => void) { reject("private-canary"); } }
        : Object.defineProperty({}, "then", { get() { throw new Error("private-canary"); } });
      if (kind !== "native") rejected.catch(() => undefined);
      reportPlatformDiagnostic({ report: () => returned } as unknown as PlatformDiagnosticReporter, primary, { capability: "health", operation: "check", stage: "readiness" });
    }
    logs.length = 0;
    const failedProbe = Promise.reject(new Error("private-canary"));
    Object.defineProperty(failedProbe, "then", { get() { thenReads++; throw new Error("private-canary"); } });
    equal((await createPlatformReadinessObserver(options({ probe: () => failedProbe })).observe()).diagnosticCode, "observability.readiness-probe-rejected");
    deepEqual(observed(), [expected("observability.readiness-probe-rejected", { phase: "completion", effect: "unknown" })]);
    await new Promise<void>((resolve) => setImmediate(resolve));
    equal(thenReads, 0); deepEqual(unhandled, []);
  } finally { process.off("unhandledRejection", onUnhandled); }
  equal(JSON.stringify(points).includes("diagnostic"), false);
  await laterBoundaryEvidence();
  await operationalEventEvidence();
  console.log("Readiness exact predicates, actual dependency preservation, deadline uncertainty and independent delivery isolation passed.");
}

async function laterBoundaryEvidence(): Promise<void> {
  const selected = Array.from({ length: 9 }, (_, index) => corePersistenceValidationRecord({ operation: "page-request", field: "limit", reason: index % 2 === 0 ? "not-positive" : "not-integer" }));
  const thrown = Object.assign(new Error("private-later-boundary-canary"), { diagnosticRecord: selected[0], relatedDiagnosticRecords: selected.slice(1) });
  const probeResult = { readiness: "ready" as const, diagnosticRecord: selected[0]!, relatedDiagnosticRecords: selected.slice(1) };
  for (const failed of ["probe", "timeout", "identity", "clock", "policy", "result", "event"] as const) {
    const records: DiagnosticRecord[] = [], order: string[] = [];
    let probeCalls = 0, evidenceReads = 0;
    const result = new Proxy(failed === "policy" ? { ...probeResult, readiness: "not-ready" as const } : probeResult, {
      get(target, key, receiver) {
        if (key === "diagnosticRecord" || key === "relatedDiagnosticRecords") evidenceReads++;
        if (key === "readiness") { order.push("readiness"); if (failed === "result") throw thrown; }
        return Reflect.get(target, key, receiver);
      },
    });
    const options: PlatformReadinessObserverOptions = {
      get probe(): PlatformReadinessObserverOptions["probe"] { order.push("probe"); if (failed === "probe") throw thrown; return async () => { probeCalls++; return result; }; },
      get timeoutMs(): number { order.push("timeout"); if (failed === "timeout") throw thrown; return 100; },
      get identity(): PlatformReadinessObserverOptions["identity"] { order.push("identity"); if (failed === "identity") throw thrown;
        return { target: failed === "event" ? "invalid-private-canary".repeat(10) : "fixture-target", scope: "fixture-scope", workload: "fixture-workload", dependency: "fixture-dependency" }; },
      get allowedDiagnosticCodes(): readonly string[] { if (failed === "policy") throw thrown; return []; }, defaultDiagnosticCode: "fixture.failure",
      clock: { now() { order.push("clock"); if (failed === "clock") throw thrown; return clock.now(); } },
      logger: { write() { throw new Error("output must not be reached"); } }, metrics: { record() { throw new Error("metric must not be reached"); } },
      observations: { context: { capability: "fixture", operation: "readiness-observation", stage: "readiness" }, reporter: { report(record) { records.push(record); return { status: "written" }; } } },
    };
    const observer = createPlatformReadinessObserver(options);
    await rejects(observer.observe(), (error) => failed === "event" ? error instanceof Error && error.message === "PLATFORM_OPERATIONAL_EVENT_INVALID" : error === thrown);
    const detail = records[0]?.detail as { phase: string; field: string; effect: string; reason: string };
    equal(records[0]?.code, "observability.boundary-failed"); equal(records[0]?.definitionVersion, 1);
    deepEqual(detail, { operation: "readiness-observation", phase: failed === "probe" || failed === "timeout" ? "input-projection" : failed === "identity" ? "identity-projection" : failed === "clock" ? "clock" : failed === "policy" ? "policy-selection" : failed === "event" ? "event-validation" : "result-projection",
      field: failed === "probe" ? "provider" : failed === "timeout" || failed === "policy" ? "policy" : failed === "identity" ? "identity" : failed === "clock" ? "clock" : failed === "event" ? "event" : "result",
      reason: failed === "event" ? "invalid-event" : "threw", effect: "event-not-returned" });
    if (failed === "event") {
      deepEqual(records[1], expected("platform-contracts.operational-event-rejected", { operation: "readiness-event", field: "target", condition: "invalid-format", phase: "validation", effect: "predicate-rejected" }));
      deepEqual(records.slice(2), selected); equal(records.length, 11);
    } else {
      deepEqual(records.slice(1, 10), selected);
      if (failed !== "probe" && failed !== "timeout") deepEqual(records.slice(10), selected, "thrown source9 and earlier successful result9 are independent");
      else equal(records.length, 10);
    }
    equal(probeCalls, failed === "probe" || failed === "timeout" ? 0 : 1);
    equal(evidenceReads, 0, "source selection must use own descriptors, never probe-result getters");
    deepEqual(order.slice(0, failed === "probe" ? 1 : 2), failed === "probe" ? ["probe"] : ["probe", "timeout"]);
    equal(JSON.stringify(records).includes("private"), false);
  }
}

async function operationalEventEvidence(): Promise<void> {
  const logs: LogRecord[] = [];
  const source9 = Array.from({ length: 9 }, (_, ordinal) => corePersistenceValidationRecord({ operation: "page-request", field: "limit", reason: ordinal % 2 === 0 ? "not-positive" : "not-integer" }));
  const raw = Object.freeze(Object.assign(new Error("PRIVATE-operational-event-canary"), { diagnosticRecord: source9[0], relatedDiagnosticRecords: source9.slice(1) }));
  const reporter = createPlatformDiagnosticReporter({ catalogs: [coreDiagnosticCatalog, platformObservabilityDiagnosticCatalog, platformContractDiagnosticCatalog], logger: { write(record) { logs.push(record); } }, clock });
  const observations = { reporter, context: { capability: "fixture", operation: "readiness-observation", stage: "readiness" as const } };
  const base: PlatformReadinessObservationEvent = { type: "dependency.readiness-observed", target: "fixture-target", scope: "fixture-scope", workload: "fixture-workload", dependency: "fixture-dependency", readiness: "ready", observedAt: "2026-10-31T00:00:00.000Z" };
  const diagnosticRecords = (): readonly unknown[] => logs.filter((log) => log.message === "platform.diagnostic.observed").map((log) => log.fields?.["diagnostic"]);
  let writes = 0;
  emitPlatformReadinessObservation({ write() { writes++; } }, { ...base, target: "PRIVATE-operational-event-canary" }, observations);
  deepEqual(diagnosticRecords(), [expected("observability.boundary-failed", { operation: "readiness-observation", phase: "event-validation", field: "event", reason: "invalid-event", effect: "event-not-written" }),
    expected("platform-contracts.operational-event-rejected", { operation: "readiness-event", field: "target", condition: "invalid-format", phase: "validation", effect: "predicate-rejected" })]);
  equal(writes, 0);
  logs.length = 0;
  let targetReads = 0;
  try { emitPlatformReadinessObservation({ write() { writes++; } }, { ...base, get target(): string { targetReads++; throw raw; } }, observations); throw new Error("Expected original parser throw"); }
  catch (error) { equal(error, raw); }
  equal(targetReads, 1); equal(writes, 0);
  deepEqual(diagnosticRecords(), [expected("platform-contracts.operational-boundary-failed", { operation: "readiness-event", phase: "field-projection", field: "target", reason: "threw", effect: "event-not-produced" }),
    expected("observability.boundary-failed", { operation: "readiness-observation", phase: "event-validation", field: "event", reason: "threw", effect: "event-not-written" }), ...source9]);
  logs.length = 0;
  const originalParse = Date.parse;
  let parses = 0, probes = 0;
  try {
    Date.parse = () => { parses++; throw raw; };
    await rejects(createPlatformReadinessObserver({ identity: { target: base.target, scope: base.scope, workload: base.workload, dependency: base.dependency }, probe: async () => { probes++; return { readiness: "ready" }; },
      logger: { write() { writes++; } }, metrics: { record() { throw new Error("Metric must not be reached"); } }, clock, timeoutMs: 100, allowedDiagnosticCodes: [], defaultDiagnosticCode: "fixture.failure", observations }).observe(), (error) => error === raw);
  } finally { Date.parse = originalParse; }
  equal(parses, 1); equal(probes, 1); equal(writes, 0);
  deepEqual(diagnosticRecords(), [expected("platform-contracts.operational-boundary-failed", { operation: "readiness-event", phase: "time-parsing", field: "observed-at", reason: "threw", effect: "event-not-produced" }),
    expected("observability.boundary-failed", { operation: "readiness-observation", phase: "event-validation", field: "event", reason: "threw", effect: "event-not-returned" }), ...source9]);
  equal(JSON.stringify(logs).includes("PRIVATE-"), false);
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
