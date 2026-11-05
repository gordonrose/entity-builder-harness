import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import type { Logger, LogRecord } from "@kanbien/core/logging";
import { createInMemoryTracer, type MetricPoint, type Metrics } from "@kanbien/core/monitoring";
import { correlationId, fixedClock } from "@kanbien/core/shared";
import { corePersistenceValidationRecord } from "@kanbien/core/persistence";
import { platformCapabilityName, platformObservabilityProfileName } from "@kanbien/platform-contracts";
import { defineDiagnostic, createDiagnosticRecord, diagnosticRelatedRecordLimit, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformObservabilityDiagnosticCatalog } from "@kanbien/platform-observability";
import {
  createPlatformPersistenceTransitionObserver,
  platformPersistenceTransitionProfile,
  persistenceObservedDiagnosticRecord,
  platformPersistenceError,
  platformPersistenceErrorClasses,
  persistenceBoundaryDiagnosticRecord, observePlatformPersistenceDiagnostic, selectPlatformPersistenceDiagnosticEvidence,
  createPlatformOutboxRelay, createInMemoryPlatformOutboxStore, platformPersistenceLeaseOwner, persistenceRelayBoundaryDiagnosticRecord, recordPlatformPersistenceObservation,
  type PlatformOutboxStore, type PlatformPersistenceObserver,
} from "../src/index";

async function main(): Promise<void> {
  const profileName = platformObservabilityProfileName("platform.persistence.outbox.relay");
  const capability = platformCapabilityName("platform.persistence.outbox.relay");
  if (!profileName.ok || !capability.ok) {
    throw new Error("Expected valid persistence observability identifiers.");
  }

  const records: LogRecord[] = [];
  const points: MetricPoint[] = [];
  const logger: Logger = { write: (record) => records.push(record) };
  const metrics: Metrics = { record: (point) => { points.push(point); } };
  const tracer = createInMemoryTracer();
  const observer = createPlatformPersistenceTransitionObserver({
    profile: platformPersistenceTransitionProfile({ name: profileName.value, capability: capability.value }),
    executionContext: "worker",
    logger,
    metrics,
    tracer,
    clock: fixedClock(new Date("2026-10-19T00:00:00.000Z")),
  });
  equal(observer.ok, true);
  if (!observer.ok) {
    throw new Error("Expected a valid persistence transition observer.");
  }

  observer.value.record({
    transition: "outbox.claimed",
    outcome: "succeeded",
    correlationId: correlationId("corr-persistence-1"),
  });
  observer.value.record({
    transition: "processing.completion_failed",
    outcome: "failed",
    error: Object.assign(new Error("do not disclose this message"), { code: "PLATFORM_PERSISTENCE_STALE_FENCE" }),
  });

  equal(records[0]?.message, "platform.persistence.outbox.claimed");
  equal(records[0]?.correlationId, "corr-persistence-1");
  deepEqual(records[0]?.fields, {
    capability: "platform.persistence.outbox.relay",
    action: "execute",
    execution_context: "worker",
    outcome: "succeeded",
  });
  deepEqual(records[1]?.fields, {
    capability: "platform.persistence.outbox.relay",
    action: "execute",
    execution_context: "worker",
    outcome: "failed",
    error_class: "PLATFORM_PERSISTENCE_STALE_FENCE",
  });
  equal(points[0]?.name, "platform.persistence.outbox.claimed.outcome");
  equal(tracer.spans()[0]?.name, "platform.persistence.outbox.claimed");
  deepEqual(tracer.spans()[1]?.end?.attributes, {
    capability: "platform.persistence.outbox.relay",
    action: "execute",
    execution_context: "worker",
    outcome: "failed",
    error_class: "PLATFORM_PERSISTENCE_STALE_FENCE",
  });
  const companion = defineDiagnostic({ code: "security.fixture-verification-failed", version: 1,
    classification: { failureKind: "authentication", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { reason: { type: "enum", values: ["fixture-observation"] } } } } as const);
  const related = createDiagnosticRecord(companion, { reason: "fixture-observation" });
  if (!related.ok) throw new Error("fixture-invalid");
  const primary = persistenceObservedDiagnosticRecord({ classification: "tls_trust_invalid", phase: "query", code_status: "recognized" }, "readiness");
  const retained = platformPersistenceError({ code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: "Safe failure", diagnosticRecord: primary, relatedDiagnosticRecords: [related.value], relatedDiagnosticDefinitions: [companion] });
  deepEqual(retained.relatedDiagnosticRecords, [related.value]);
  equal(Object.isFrozen(retained.relatedDiagnosticRecords), true);
  for (const invalid of [Array(1), Array(diagnosticRelatedRecordLimit + 1).fill(related.value), [{ ...related.value, detail: { reason: "synthetic-secret-canary" } }]]) {
    const rejected = platformPersistenceError({ code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: "Safe failure", diagnosticRecord: primary, relatedDiagnosticRecords: invalid, relatedDiagnosticDefinitions: [companion] });
    equal(rejected.diagnosticRecord, primary);
    equal(rejected.relatedDiagnosticRecords, undefined);
  }
  for (const selected of [false, true]) {
    const delivered: LogRecord[] = [];
    const configured = createPlatformPersistenceTransitionObserver({
      profile: platformPersistenceTransitionProfile({ name: profileName.value, capability: capability.value }), executionContext: "worker",
      logger: { write: (record) => delivered.push(record) }, metrics, clock: fixedClock(new Date("2026-10-27T00:00:00.000Z")),
      ...(selected ? { companionDiagnosticCatalogs: [{ owner: "security", definitions: [companion] }] } : {}),
    });
    if (!configured.ok) throw new Error("observer-invalid");
    configured.value.record({ transition: "processing.completion_failed", outcome: "failed", error: { code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: "Safe failure", diagnosticRecord: primary, relatedDiagnosticRecords: [related.value] } });
    deepEqual(delivered.filter((record) => record.message === "platform.diagnostic.observed").map((record) => record.fields?.["diagnostic"]), selected ? [primary, related.value] : [primary]);
  }
  const optedOut: LogRecord[] = [];
  const noLogs = createPlatformPersistenceTransitionObserver({
    profile: { name: profileName.value, capability: capability.value, action: "execute", signals: ["metric"] },
    companionDiagnosticCatalogs: [{ owner: "security", definitions: [companion] }], executionContext: "worker", logger: { write: (record) => optedOut.push(record) }, metrics, clock: fixedClock(new Date()),
  });
  if (!noLogs.ok) throw new Error("observer-invalid");
  noLogs.value.record({ transition: "processing.completion_failed", outcome: "failed", error: retained });
  equal(optedOut.length, 0, "related diagnostics must honor operational-log opt-out");
  const compatibleCompanion = { ...platformObservabilityDiagnosticCatalog };
  const reorderedCopy = { definitions: JSON.parse(JSON.stringify(platformObservabilityDiagnosticCatalog.definitions)) as typeof compatibleCompanion.definitions,
    owner: platformObservabilityDiagnosticCatalog.owner };
  for (const companionDiagnosticCatalogs of [[platformObservabilityDiagnosticCatalog], [compatibleCompanion], [reorderedCopy]]) {
    equal(createPlatformPersistenceTransitionObserver({ profile: platformPersistenceTransitionProfile({ name: profileName.value, capability: capability.value }),
      executionContext: "worker", logger, metrics, clock: fixedClock(new Date()), companionDiagnosticCatalogs }).ok, true,
      "a formerly supported explicit built-in companion must compose once");
  }
  const conflicts = { ...platformObservabilityDiagnosticCatalog, definitions: platformObservabilityDiagnosticCatalog.definitions.slice(1) };
  let companionGetterReads = 0;
  const malformedCompanion = Object.defineProperty({ ...platformObservabilityDiagnosticCatalog }, "owner", { get() { companionGetterReads++; throw new Error("catalog-canary"); } });
  for (const companionDiagnosticCatalogs of [[platformObservabilityDiagnosticCatalog, platformObservabilityDiagnosticCatalog], [conflicts], [malformedCompanion],
    [{ owner: "security", definitions: [companion] }, { owner: "security", definitions: [companion] }]]) {
    equal(createPlatformPersistenceTransitionObserver({ profile: platformPersistenceTransitionProfile({ name: profileName.value, capability: capability.value }),
      executionContext: "worker", logger, metrics, clock: fixedClock(new Date()), companionDiagnosticCatalogs }).ok, false,
      "built-in reconciliation must not accept conflicting, malformed or duplicate caller catalogs");
  }
  equal(companionGetterReads, 0);
  const own = persistenceBoundaryDiagnosticRecord({ operation: "transaction", phase: "completion", boundary: "release", condition: "threw", effect: "commit-completed" });
  const core = corePersistenceValidationRecord({ operation: "record-id", field: "id", reason: "empty" });
  const sourceNine = Object.freeze({ diagnosticRecord: core, relatedDiagnosticRecords: Array(8).fill(primary) });
  const expectedTen = [own, core, ...Array(8).fill(primary)];
  const selectedSource = selectPlatformPersistenceDiagnosticEvidence({}, sourceNine);
  deepEqual(selectedSource, sourceNine);
  equal(selectedSource.relatedDiagnosticRecords === sourceNine.relatedDiagnosticRecords, false);
  for (const mode of ["default", "injected", "unavailable", "disabled"] as const) {
    const logged: LogRecord[] = []; const injected: unknown[] = [];
    const configured = createPlatformPersistenceTransitionObserver({
      profile: { name: profileName.value, capability: capability.value, action: "execute", signals: mode === "disabled" ? ["metric"] : ["operational_log"] },
      executionContext: "worker", logger: { write(record) { logged.push(record); } }, metrics, clock: fixedClock(new Date()),
      ...(mode === "injected" || mode === "unavailable" ? { diagnosticReporter: { report(record: unknown) { injected.push(record); if (mode === "unavailable") throw "unavailable-canary"; return { status: "written" as const }; } } } : {}),
    });
    if (!configured.ok) throw new Error("Expected observer");
    configured.value.record({ transition: "processing.completion_failed", outcome: "failed", diagnosticRecord: own, error: sourceNine });
    deepEqual(logged.filter((record) => record.message === "platform.diagnostic.observed").map((record) => record.fields?.["diagnostic"]), mode === "default" ? expectedTen : []);
    deepEqual(injected, mode === "injected" || mode === "unavailable" ? expectedTen : []);
  }
  const callbackRecords: unknown[] = [];
  deepEqual(observePlatformPersistenceDiagnostic({ onDiagnostic(record) { callbackRecords.push(record); return Promise.reject("sink-canary"); } }, own, sourceNine), sourceNine);
  deepEqual(callbackRecords, expectedTen);
  for (const source of ["primitive-canary", Object.freeze(new Error("frozen-canary")), Object.defineProperty({}, "diagnosticRecord", { get() { throw new Error("accessor-canary"); } })]) {
    const copied: unknown[] = [];
    observePlatformPersistenceDiagnostic({ onDiagnostic(record) { copied.push(record); throw "observer-canary"; } }, own, source);
    const inaccessible = typeof source === "object" && Object.getOwnPropertyDescriptor(source, "diagnosticRecord")?.get !== undefined;
    deepEqual(copied, inaccessible ? [own, { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason: "evidence-inaccessible" } }] : [own]);
  }
  let evidenceGetterReads = 0;
  const malformed = { diagnosticRecord: { ...primary, detail: { canary: "unapproved-canary" } }, relatedDiagnosticRecords: [related.value, primary] };
  deepEqual(selectPlatformPersistenceDiagnosticEvidence({}, malformed), { relatedDiagnosticRecords: [primary] });
  deepEqual(selectPlatformPersistenceDiagnosticEvidence({ diagnosticDefinitions: [companion] }, malformed), { relatedDiagnosticRecords: [related.value, primary] });
  const accessorEvidence = Object.defineProperty({ relatedDiagnosticRecords: [primary] }, "diagnosticRecord", { get() { evidenceGetterReads++; return primary; } });
  deepEqual(selectPlatformPersistenceDiagnosticEvidence({}, accessorEvidence), { relatedDiagnosticRecords: [primary] });
  equal(evidenceGetterReads, 0);
  for (const mode of ["default", "injected", "unavailable", "disabled"] as const) for (const explicit of [false, true]) {
    const logged: LogRecord[] = []; const received: { record: unknown; context: unknown }[] = [];
    const metricsBefore = points.length;
    const configured = createPlatformPersistenceTransitionObserver({
      profile: { name: profileName.value, capability: capability.value, action: "execute", signals: mode === "disabled" ? ["metric"] : ["operational_log"] },
      executionContext: "worker", logger: { write(record) { logged.push(record); } }, metrics, clock: fixedClock(new Date("2026-10-30T18:00:00.000Z")),
      ...(explicit ? { companionDiagnosticCatalogs: [{ owner: "security", definitions: [companion] }] } : {}),
      ...(mode === "injected" || mode === "unavailable" ? { diagnosticReporter: { report(record: unknown, context: unknown) {
        received.push({ record, context }); if (mode === "unavailable") throw "store-reporter-canary"; return { status: "written" as const };
      } } } : {}),
    });
    if (!configured.ok || configured.value.onDiagnostic === undefined) throw new Error("Expected store observer");
    const onDiagnostic = configured.value.onDiagnostic;
    observePlatformPersistenceDiagnostic({ onDiagnostic }, own, sourceNine);
    onDiagnostic(related.value);
    onDiagnostic({ ...primary, detail: { privateValue: "unsafe-record-canary" } });
    const expected: readonly DiagnosticRecord[] = [...expectedTen, ...(explicit ? [related.value] : [])];
    deepEqual(logged.map((record) => record.fields?.["diagnostic"]), mode === "default" ? expected : []);
    deepEqual(received, mode === "injected" || mode === "unavailable" ? expected.map((record) => ({ record, context: { capability: "persistence", operation: "store-observation", stage: "runtime" } })) : []);
    equal(logged.every((record) => record.message === "platform.diagnostic.observed" && record.correlationId === undefined), true);
    equal(points.length, metricsBefore, "store observation must not invent a transition metric");
    equal(JSON.stringify([logged, received]).includes("canary"), false);
  }
  const relayOwner = platformPersistenceLeaseOwner("observer-relay");
  if (!relayOwner.ok) throw new Error("Invalid relay owner");
  const diagnosticModule = require("../src/diagnostics") as Record<string, unknown>;
  for (const mode of ["throws", "undefined", "malformed"] as const) {
    const processing = { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1,
      detail: { reason: mode === "throws" ? "construction-threw" : mode === "malformed" ? "evidence-rejected" : "construction-rejected" } };
    for (const key of ["persistenceRelayBoundaryDiagnosticRecord", "persistenceLocalRejectionDiagnosticRecord"]) {
      const descriptor = Object.getOwnPropertyDescriptor(diagnosticModule, key)!;
      Object.defineProperty(diagnosticModule, key, { ...descriptor, value: () => {
        if (mode === "throws") throw new Error("builder-private-canary");
        return mode === "undefined" ? undefined : { code: "unselected-private-canary" };
      } });
      try {
        const seen: DiagnosticRecord[] = [];
        const store = createInMemoryPlatformOutboxStore({ onDiagnostic(record) { seen.push(record); } });
        if (key === "persistenceLocalRejectionDiagnosticRecord") {
          const result = await store.listDeliverable({ asOf: "2026-11-04T00:00:00.000Z" as never, limit: 0 });
          equal(result.ok, false);
          if (result.ok) throw new Error("Expected limit rejection");
          equal(result.error.code, "PLATFORM_PERSISTENCE_INVALID_LIMIT");
          deepEqual(result.error.diagnosticRecord, processing);
          deepEqual(seen, [processing]);
        } else {
          let sends = 0;
          const relay = createPlatformOutboxRelay({
            outbox: { ...store, async listDeliverable() { throw sourceNine; } },
            queue: { async send() { sends++; return { ok: true, value: undefined }; } },
            owner: relayOwner.value, leaseDurationMs: 1000, clock: fixedClock(new Date("2026-11-04T00:00:00.000Z")),
            observer: { record() {}, onDiagnostic(record) { seen.push(record); } },
          });
          await rejects(relay.runOnce(), (error: unknown) => error === sourceNine);
          equal(sends, 0);
          deepEqual(seen, [processing, core, ...Array(8).fill(primary)]);
        }
        equal(JSON.stringify(seen).includes("private-canary"), false);
      } finally { Object.defineProperty(diagnosticModule, key, descriptor); }
    }
  }
  for (const mode of ["default", "injected", "unavailable", "disabled"] as const) for (const raw of [true, false]) {
    const logged: LogRecord[] = [], received: { record: unknown; context: unknown }[] = [], roles: unknown[] = [];
    let sends = 0, transitions = 0;
    const configured = createPlatformPersistenceTransitionObserver({
      profile: { name: profileName.value, capability: capability.value, action: "execute", signals: mode === "disabled" ? ["metric"] : ["operational_log"] },
      executionContext: "worker", logger: { write(record) { logged.push(record); } }, metrics, clock: fixedClock(new Date("2026-10-30T18:00:00.000Z")),
      ...(mode === "injected" || mode === "unavailable" ? { diagnosticReporter: { report(record: unknown, context: unknown) { received.push({ record, context }); if (mode === "unavailable") throw "relay-reporter-canary"; return { status: "written" as const }; } } } : {}),
    });
    if (!configured.ok) throw new Error("Invalid relay observer");
    const bridge: PlatformPersistenceObserver = { record(observation) { equal(this, bridge); transitions++; configured.value.record(observation); },
      onDiagnostic(record, operation) { equal(this, bridge); roles.push(operation); configured.value.onDiagnostic?.(record, operation); } };
    const failure = { ok: false as const, error: { code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED" as const, defaultMessage: "Safe failure", ...sourceNine } };
    const outbox: PlatformOutboxStore = { async listDeliverable() { if (raw) throw sourceNine; return failure; },
      async create() { throw new Error("Unexpected relay create"); }, async get() { throw new Error("Unexpected relay get"); },
      async claim() { throw new Error("Unexpected relay claim"); }, async markPublished() { throw new Error("Unexpected relay marker"); } };
    const relay = createPlatformOutboxRelay({ outbox, queue: { async send() { sends++; return { ok: true, value: undefined }; } }, observer: bridge,
      owner: relayOwner.value, leaseDurationMs: 1000, clock: fixedClock(new Date("2026-10-30T18:00:00.000Z")) });
    if (raw) await rejects(relay.runOnce(), (error: unknown) => error === sourceNine);
    else equal(await relay.runOnce(), failure);
    const location = persistenceRelayBoundaryDiagnosticRecord({ operation: "run-once", boundary: "list-deliverable", reason: raw ? "threw" : "returned-failure", effect: "relay-send-not-invoked" });
    const expected: readonly DiagnosticRecord[] = [location, core, ...Array(8).fill(primary)];
    deepEqual(logged.filter((record) => record.message === "platform.diagnostic.observed").map((record) => record.fields?.["diagnostic"]), mode === "default" ? expected : []);
    deepEqual(received, mode === "injected" || mode === "unavailable" ? expected.map((record) => ({ record, context: { capability: "persistence", operation: raw ? "relay" : "transition", stage: raw ? "runtime" : "request" } })) : []);
    deepEqual(roles, raw ? Array(10).fill("relay") : []); equal(transitions, raw ? 0 : 1); equal(sends, 0);
    equal(JSON.stringify([logged, received]).includes("canary"), false);
  }
  let promiseReads = 0, callbackReceivers = 0, thenableReceivers = 0;
  const rejectedPromise = Promise.reject("observer-private-canary");
  for (const key of ["then", "catch"]) Object.defineProperty(rejectedPromise, key, { get() { promiseReads++; throw "shadowed-promise-canary"; } });
  const thenable = { then(this: unknown, _resolve: unknown, reject: (reason: unknown) => void) { equal(this, thenable); thenableReceivers++; reject("thenable-private-canary"); } };
  for (const returned of [rejectedPromise, thenable]) {
    const observer: PlatformPersistenceObserver = { record() { equal(this, observer); callbackReceivers++; return returned; } };
    recordPlatformPersistenceObservation(observer, { transition: "outbox.claimed", outcome: "succeeded" });
  }
  await new Promise<void>((resolve) => setImmediate(resolve));
  equal(promiseReads, 0); equal(callbackReceivers, 2); equal(thenableReceivers, 1);
  equal(JSON.stringify(callbackRecords).includes("canary"), false);
  for (const logsEnabled of [true, false]) {
    const delivered: LogRecord[] = []; let metricCalls = 0;
    const failingMetrics = createPlatformPersistenceTransitionObserver({
      profile: { name: profileName.value, capability: capability.value, action: "execute", signals: logsEnabled ? ["metric", "operational_log"] : ["metric"] },
      executionContext: "worker", logger: { write(record) { delivered.push(record); } },
      metrics: { record() { metricCalls++; return Promise.reject(new Error("metric-private-canary")); } }, clock: fixedClock(new Date()),
    });
    if (!failingMetrics.ok) throw new Error("observer-invalid");
    for (let attempt = 0; attempt < 20; attempt++) failingMetrics.value.record({ transition: "outbox.claimed", outcome: "succeeded" });
    await new Promise<void>((resolve) => setImmediate(resolve));
    equal(metricCalls, 20);
    const diagnosticLogs = delivered.filter((record) => record.message === "platform.diagnostic.observed");
    equal(diagnosticLogs.length, logsEnabled ? 1 : 0);
    if (logsEnabled) {
      equal(diagnosticLogs[0]?.fields?.["operation"], "persistence-transition");
      deepEqual(diagnosticLogs[0]?.fields?.["diagnostic"], { schema: "core/diagnostic-record/v1", code: "observability.metric-recording-failed", definitionVersion: 1,
        detail: { reason: "unclassified-invocation-failure", phase: "record-invocation", effect: "unknown" } });
    }
    equal(JSON.stringify(delivered).includes("metric-private-canary"), false);
  }
  const classLogs: LogRecord[] = [], classPoints: MetricPoint[] = [];
  const classTracer = createInMemoryTracer();
  const classObserver = createPlatformPersistenceTransitionObserver({
    profile: { ...platformPersistenceTransitionProfile({ name: profileName.value, capability: capability.value }), errorClasses: ["APP_FIXED"] },
    executionContext: "worker", logger: { write(record) { classLogs.push(record); } },
    metrics: { record(point) { classPoints.push(point); } }, tracer: classTracer, clock: fixedClock(new Date()),
  });
  if (!classObserver.ok) throw new Error("fixture-invalid");
  let classReads = 0;
  const privateClass = "private-class-canary@example.invalid";
  const codeGetter = Object.defineProperty({}, "code", { get() { classReads++; throw privateClass; } });
  for (const error of [...platformPersistenceErrorClasses.map((code) => ({ code })), { code: "APP_FIXED" }, { code: privateClass }, codeGetter]) {
    classObserver.value.record({ transition: "processing.completion_failed", outcome: "failed", error });
  }
  const expectedClasses = [...platformPersistenceErrorClasses, "APP_FIXED", "unknown", "unknown"];
  deepEqual(classLogs.map((record) => record.fields?.["error_class"]), expectedClasses);
  deepEqual(classPoints.map((point) => point.labels?.["error_class"]), expectedClasses);
  deepEqual(classTracer.spans().map((span) => span.end?.attributes?.["error_class"]), expectedClasses);
  equal(classReads, 0);
  equal(JSON.stringify([classLogs, classPoints, classTracer.spans()]).includes(privateClass), false);
  const profileModule = require("../../contracts/src/observability-profiles") as Record<string, unknown>;
  const wrapperFailure = Object.freeze(Object.assign(new Error("wrapper-private-canary"), sourceNine));
  for (const phase of ["profile-projection", "log-projection", "metric-projection", "trace-projection", "error-class"] as const) {
    for (const enabled of [true, false]) {
      const seen: DiagnosticRecord[] = [], wrapperLogs: LogRecord[] = [], wrapperPoints: MetricPoint[] = [];
      let armed = false, failed = false, errorReads = 0;
      const key = phase === "profile-projection" ? "platformProfileAllowsSignal" : phase === "log-projection" ? "platformProfileLogFields"
        : phase === "metric-projection" ? "platformProfileMetricLabels" : "platformProfileTraceFields";
      const descriptor = Object.getOwnPropertyDescriptor(profileModule, key)!;
      const original = descriptor.value as (...args: unknown[]) => unknown;
      if (phase !== "error-class") Object.defineProperty(profileModule, key, { ...descriptor, value: (...args: unknown[]) => {
        if (armed && !failed) { failed = true; throw wrapperFailure; }
        return Reflect.apply(original, undefined, args);
      } });
      try {
        const configured = createPlatformPersistenceTransitionObserver({
          profile: { ...platformPersistenceTransitionProfile({ name: profileName.value, capability: capability.value }),
            signals: enabled ? ["operational_log", "metric", "trace"] : ["metric", "trace"],
            ...(enabled ? {} : { logFieldNames: undefined }) } as never,
          executionContext: "worker", logger: { write(record) { wrapperLogs.push(record); } },
          metrics: { record(point) { wrapperPoints.push(point); } }, tracer: createInMemoryTracer(), clock: fixedClock(new Date()),
          diagnosticReporter: { report(record) { seen.push(record); return { status: "written" }; } },
        });
        if (!configured.ok) throw new Error("fixture-invalid");
        const observation = { transition: "processing.completion_failed" as const, outcome: "failed" as const };
        if (phase === "error-class") Object.defineProperty(observation, "error", { get() { errorReads++; throw wrapperFailure; } });
        armed = true;
        if (phase === "log-projection" && !enabled) configured.value.record(observation);
        else throws(() => configured.value.record(observation), (error) => error === wrapperFailure);
        const expected = { schema: "core/diagnostic-record/v1", code: "observability.boundary-failed", definitionVersion: 1,
          detail: { operation: "persistence-observation", phase, reason: "threw", effect: "observation-incomplete" } };
        deepEqual(seen, enabled ? [expected, core, ...Array(8).fill(primary)] : []);
        equal(errorReads, phase === "error-class" ? 1 : 0, "the catch cannot reread the failed error accessor");
        if (enabled && phase === "trace-projection") { equal(wrapperLogs.length, 1); equal(wrapperPoints.length, 1); }
        equal(JSON.stringify([seen, wrapperLogs, wrapperPoints]).includes("wrapper-private-canary"), false);
      } finally { armed = false; if (phase !== "error-class") Object.defineProperty(profileModule, key, descriptor); }
    }
  }
  for (const selected of [false, true]) {
    const seen: DiagnosticRecord[] = [];
    const failure = Object.freeze(Object.assign(new Error("private-canary"), { diagnosticRecord: related.value, relatedDiagnosticRecords: Array(8).fill(related.value) }));
    const key = "platformProfileLogFields", descriptor = Object.getOwnPropertyDescriptor(profileModule, key)!;
    const original = descriptor.value as (...args: unknown[]) => unknown;
    let armed = false;
    try {
      Object.defineProperty(profileModule, key, { ...descriptor, value: (...args: unknown[]) => {
        if (armed) throw failure; return Reflect.apply(original, undefined, args);
      } });
      const configured = createPlatformPersistenceTransitionObserver({
        profile: platformPersistenceTransitionProfile({ name: profileName.value, capability: capability.value }), executionContext: "worker",
        logger, metrics, clock: fixedClock(new Date()), diagnosticReporter: { report(record) { seen.push(record); return { status: "written" }; } },
        ...(selected ? { companionDiagnosticCatalogs: [{ owner: "security", definitions: [companion] }] } : {}),
      });
      if (!configured.ok) throw new Error("fixture-invalid");
      armed = true;
      recordPlatformPersistenceObservation(configured.value, { transition: "outbox.claimed", outcome: "succeeded" });
      deepEqual(seen, [{ schema: "core/diagnostic-record/v1", code: "observability.boundary-failed", definitionVersion: 1,
        detail: { operation: "persistence-observation", phase: "log-projection", reason: "threw", effect: "observation-incomplete" } },
        ...(selected ? Array(9).fill(related.value) : [])], "even injected reporters only receive explicitly selected source9");
    } finally { Object.defineProperty(profileModule, key, descriptor); }
  }
}

main().then(
  () => console.log("platform/persistence observability runtime test passed."),
  (error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  },
);
