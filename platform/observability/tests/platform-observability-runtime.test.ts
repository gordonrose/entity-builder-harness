import { deepEqual, equal, throws, rejects } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { corePersistenceValidationDiagnostic } from "@kanbien/core/persistence";
import type { Logger, LogRecord } from "@kanbien/core/logging";
import { createInMemoryTracer, type MetricPoint, type Metrics, type Tracer } from "@kanbien/core/monitoring";
import { correlationId, fixedClock } from "@kanbien/core/shared";
import {
  createPlatformReadinessObserver,
  createPlatformSafeLogger,
  endPlatformTraceSpan,
  elapsedMilliseconds,
  normalizePlatformError,
  normalizePlatformLogFields,
  normalizePlatformValue,
  platformErrorClass,
  platformTraceAttributes,
  platformTraceFields,
  recordPlatformHealthMetric,
  recordPlatformJobMetric,
  recordPlatformRequestMetric,
  startPlatformTraceSpan,
  writePlatformLog,
  reportPlatformObservationBoundary,
  reportPlatformObservationSources,
  type PlatformObservationDiagnostics,
  type PlatformObservationBoundaryDetail,
} from "../src/index";
import { platformReadinessObservationEvent } from "@kanbien/platform-contracts";

async function main(): Promise<void> {
  classificationProof();
  await boundaryCoverage();
  const circular: Record<string, unknown> = { name: "loop" };
  circular["self"] = circular;

  const normalized = normalizePlatformLogFields({
    authorization: "Bearer secret",
    nested: { apiKey: "abc", keep: "visible" },
    circular,
    long: "x".repeat(20),
  }, { maxStringLength: 8 });

  equal(normalized["authorization"], "[REDACTED]");
  deepEqual(normalized["nested"], { apiKey: "[REDACTED]", keep: "visible" });
  deepEqual(normalized["circular"], { name: "loop", self: "[Circular]" });
  equal(normalized["long"], "xxxxxxxx...[truncated]");

  const records: LogRecord[] = [];
  const logger: Logger = { write: (record) => records.push(record) };
  const safeLogger = createPlatformSafeLogger(logger);
  safeLogger.write({
    level: "info",
    message: "safe",
    fields: { password: "secret", ok: true },
  });
  equal(records[0]?.fields?.["password"], "[REDACTED]");

  writePlatformLog(logger, {
    level: "error",
    message: "failed",
    correlationId: correlationId("corr-1"),
    fields: { headers: { cookie: "secret", accept: "json" } },
    error: Object.assign(new Error("nope"), { code: "E_NOPE" }),
  }, { errorClasses: ["E_NOPE"] });
  equal(records[1]?.correlationId, "corr-1");
  deepEqual(records[1]?.fields?.["headers"], { cookie: "[REDACTED]", accept: "json" });
  deepEqual(records[1]?.fields?.["error"], { name: "Error", code: "E_NOPE" });
  equal(platformErrorClass(Object.assign(new Error("nope"), { code: "E_NOPE" }), { errorClasses: ["E_NOPE"] }), "E_NOPE");
  deepEqual(normalizePlatformError("plain"), { type: "non-error-value" });

  const points: MetricPoint[] = [];
  const metrics: Metrics = {
    record: (point) => {
      points.push(point);
    },
  };
  const clock = fixedClock(new Date("2026-07-10T00:00:00.000Z"));
  recordPlatformRequestMetric(metrics, clock, {
    method: "GET",
    route: "smoke.echo",
    status: 200,
    latencyMs: 12,
  });
  recordPlatformJobMetric(metrics, clock, {
    job: "smoke.rebuild",
    status: "retry",
    retryCount: 1,
    errorClass: "PLATFORM_WORKER_HANDLER_FAILED",
  }, undefined, { errorClasses: ["PLATFORM_WORKER_HANDLER_FAILED"] });
  recordPlatformHealthMetric(metrics, clock, { healthState: "ready" });

  equal(points.length, 3);
  equal(points[0]?.name, "platform.server.request");
  equal(points[0]?.labels?.["route"], "smoke.echo");
  equal(points[1]?.labels?.["retry_count"], 1);
  equal(points[2]?.labels?.["health_state"], "ready");

  deepEqual(platformTraceFields({
    requestId: "req-1",
    correlationId: "corr-1",
    tenant: "tenant-a",
    route: "smoke.echo",
    latencyMs: elapsedMilliseconds(new Date("2026-07-10T00:00:00.000Z"), new Date("2026-07-10T00:00:00.025Z")),
  }), {
    requestId: "req-1",
    correlationId: "corr-1",
    tenant: "tenant-a",
    route: "smoke.echo",
    job: null,
    errorClass: null,
    latencyMs: 25,
    retryCount: null,
    healthState: null,
    method: null,
    status: null,
    outcome: null,
  });

  deepEqual(platformTraceAttributes({
    method: "GET",
    route: "smoke.echo",
    status: 200,
    outcome: "succeeded",
    errorClass: "do-not-store-secret",
  }), {
    method: "GET",
    route: "smoke.echo",
    status: 200,
    outcome: "succeeded",
    errorClass: "unknown",
  });
  deepEqual(platformTraceAttributes({
    capability: "smoke.worker.execute",
    action: "execute",
    execution_context: "worker",
    job_delivery_disposition: "succeeded",
    outcome: "succeeded",
  }), {
    capability: "smoke.worker.execute",
    action: "execute",
    execution_context: "worker",
    job_delivery_disposition: "succeeded",
    outcome: "succeeded",
  });

  const tracer = createInMemoryTracer();
  const span = startPlatformTraceSpan(tracer, {
    name: "platform.server.request",
    attributes: { method: "GET", route: "smoke.echo" },
  });
  endPlatformTraceSpan(span, {
    outcome: "succeeded",
    attributes: { status: 200, latencyMs: 12 },
  });
  deepEqual(tracer.spans(), [
    {
      name: "platform.server.request",
      context: { traceId: "trace-1", spanId: "span-1" },
      attributes: { method: "GET", route: "smoke.echo" },
      end: { outcome: "succeeded", attributes: { status: 200, latencyMs: 12 } },
    },
  ]);

  const unavailableTracer: Tracer = {
    startSpan: () => {
      throw new Error("telemetry unavailable");
    },
  };
  const fallbackSpan = startPlatformTraceSpan(unavailableTracer, { name: "platform.server.request" });
  endPlatformTraceSpan(fallbackSpan, { outcome: "failed" });

  const unavailableLogger: Logger = { write: () => { throw new Error("logger unavailable"); } };
  writePlatformLog(unavailableLogger, { level: "info", message: "best-effort" });
  const unavailableMetrics: Metrics = { record: () => { throw new Error("metrics unavailable"); } };
  recordPlatformHealthMetric(unavailableMetrics, clock, { healthState: "ready" });

  // This is the actual readiness-event emission boundary, not just the
  // generic field-normalisation helper.  The emitted JSON has a closed,
  // allowlisted shape and cannot carry a raw provider error or secret.
  const readinessRecords: LogRecord[] = [];
  const readinessPoints: MetricPoint[] = [];
  const observer = createPlatformReadinessObserver({
    identity: { target: "kanbien-core-platform", scope: "core-server-persistence", workload: "core-server", dependency: "postgresql" },
    probe: async () => ({ readiness: "not-ready", diagnosticCode: "persistence.credential-rejected" }),
    logger: { write: (record) => { readinessRecords.push(record); } },
    metrics: { record: (point) => { readinessPoints.push(point); } },
    clock,
    timeoutMs: 5,
    allowedDiagnosticCodes: ["persistence.transport-unavailable", "persistence.credential-rejected"],
    defaultDiagnosticCode: "persistence.transport-unavailable",
  });
  const readinessEvent = await observer.observe();
  equal(readinessEvent.readiness, "not-ready");
  equal(readinessRecords[0]?.message, "platform.dependency.readiness_observed");
  equal(readinessPoints[0]?.name, "platform.dependency.readiness");
  equal(readinessPoints[0]?.value, 0);
  const serializedReadinessRecord = JSON.stringify(readinessRecords[0]);
  equal(serializedReadinessRecord.includes("password"), false);
  equal(serializedReadinessRecord.includes("provider_message"), false);
  equal(serializedReadinessRecord.includes("persistence.credential-rejected"), true);

  const rejectedEnvelope = platformReadinessObservationEvent({
    ...readinessEvent,
    raw_provider_error: { password: "synthetic-secret", message: "do not emit" },
  });
  equal(rejectedEnvelope.ok, false);

  const timedOutRecords: LogRecord[] = [];
  const timedOut = createPlatformReadinessObserver({
    identity: { target: "kanbien-core-platform", scope: "core-server-persistence", workload: "core-server", dependency: "postgresql" },
    probe: async () => new Promise(() => undefined),
    logger: { write: (record) => { timedOutRecords.push(record); } },
    metrics: { record: () => undefined },
    clock,
    timeoutMs: 1,
    allowedDiagnosticCodes: ["persistence.transport-unavailable"],
    defaultDiagnosticCode: "persistence.transport-unavailable",
  });
  const timedOutEvent = await timedOut.observe();
  equal(timedOutEvent.diagnosticCode, "observability.readiness-probe-deadline-observed");
  equal(timedOutRecords[0]?.fields?.["diagnostic_code"], "observability.readiness-probe-deadline-observed");

}

async function boundaryCoverage(): Promise<void> {
  const records: DiagnosticRecord[] = [];
  const context = { capability: "fixture", operation: "request-observation", stage: "request" } as const;
  const observations: PlatformObservationDiagnostics = { context, reporter: { report(record, copied) {
    equal(this, observations.reporter); deepEqual(copied, context); records.push(record); return { status: "written" };
  } } };
  const detail: PlatformObservationBoundaryDetail = { operation: "log-write", phase: "sink-invocation", field: "logger", reason: "threw", effect: "unknown" };
  // Select an actual closed Core record with nine distinguishable valid records,
  // rather than synthetic objects which could bypass the source selector.
  const finite = defineDiagnostic({ code: "fixture.boundary-source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" },
    detail: { type: "object", properties: { index: { type: "integer", minimum: 0, maximum: 8 } } } } as const);
  const sourceRecords = Array.from({ length: 9 }, (_, index) => {
    const checked = createDiagnosticRecord(finite, { index }); if (!checked.ok) throw checked.error; return checked.value;
  });
  const source = Object.assign(new Error("private-boundary-canary@example.invalid"), { diagnosticRecord: sourceRecords[0], relatedDiagnosticRecords: sourceRecords.slice(1) });
  const selected = { ...observations, definitions: [finite] };
  const assertOwnNine = (): void => {
    equal(records.length, 10); equal(records[0]?.code, "observability.boundary-failed"); equal(records[0]?.definitionVersion, 1);
    deepEqual(records[0]?.detail, detail); deepEqual(records.slice(1), sourceRecords);
    equal(JSON.stringify(records).includes("private-boundary-canary"), false); records.length = 0;
  };
  reportPlatformObservationBoundary(selected, detail, source); assertOwnNine();
  reportPlatformObservationSources(selected, source); deepEqual([...records], sourceRecords); records.length = 0;
  reportPlatformObservationBoundary(selected, { ...detail, field: "private" } as unknown as PlatformObservationBoundaryDetail, source);
  deepEqual([...records], sourceRecords); records.length = 0;
  let reads = 0;
  reportPlatformObservationSources(selected, Object.defineProperty({}, "diagnosticRecord", { get() { reads++; throw source; } }));
  equal(reads, 0); equal(records.length, 0);
  reportPlatformObservationSources(observations, source); equal(records.length, 0, "unselected application records stay unavailable");
  reportPlatformObservationSources(selected, { diagnosticRecord: { ...sourceRecords[0], private: "canary" } }); equal(records.length, 0);
  reportPlatformObservationBoundary({ ...selected, context: Object.defineProperty({ capability: "fixture", stage: "request" }, "operation", { get() { reads++; return "private"; }, enumerable: true }) as never }, detail, source);
  equal(reads, 0); equal(records.length, 0);
  // A failed optional catalog must leave independently trusted Core records usable.
  const coreSource = (() => { const checked = createDiagnosticRecord(corePersistenceValidationDiagnostic, { operation: "page-request", field: "limit", reason: "not-positive", effect: "rejected" }); return checked.ok ? checked.value : undefined; })();
  const builtin = coreSource;
  if (builtin === undefined) throw new Error("Core persistence fixture no longer matches its selected definition");
  const coreNine = { diagnosticRecord: builtin, relatedDiagnosticRecords: Array.from({ length: 8 }, () => builtin) };
  for (const bad of [Object.defineProperty({ ...observations }, "definitions", { get() { throw source; } }), { ...observations, definitions: [{ code: "private" }] }] as const) {
    reportPlatformObservationBoundary(bad as PlatformObservationDiagnostics, detail, coreNine);
    equal(records[0]?.code, "observability.boundary-failed"); equal(records.length, 10); deepEqual(records.slice(1), Array.from({ length: 9 }, (): DiagnosticRecord => builtin)); records.length = 0;
  }
  let recursive = 0;
  const reentrant: PlatformObservationDiagnostics = { context, reporter: { report(): { status: "written" } { recursive++; reportPlatformObservationBoundary(reentrant, detail, source); return { status: "written" }; } } };
  reportPlatformObservationBoundary(reentrant, detail); equal(recursive, 1);
  const expect = (expected: PlatformObservationBoundaryDetail): void => { equal(records[0]?.code, "observability.boundary-failed"); deepEqual(records[0]?.detail, expected); deepEqual(records.slice(1), sourceRecords); records.length = 0; };
  let writes = 0;
  const logger: Logger = { write() { equal(this, logger); writes++; throw source; } };
  writePlatformLog(logger, { level: "info", message: "fixed" }, undefined, selected); equal(writes, 1); expect(detail);
  const order: string[] = [];
  const throwingSelection = Object.defineProperty({}, "write", { get() { order.push("write"); throw source; } }) as Logger;
  writePlatformLog(throwingSelection, { get level(): "info" { order.push("level"); return "info"; }, message: "fixed" }, undefined, selected);
  deepEqual(order, ["write"]); expect({ ...detail, phase: "sink-selection", effect: "not-attempted" });
  throws(() => createPlatformSafeLogger(logger, undefined, selected).write(Object.defineProperty({}, "level", { get() { throw source; } }) as never), (error) => error === source);
  expect({ operation: "log-write", phase: "input-projection", field: "level", reason: "threw", effect: "not-attempted" });
  writePlatformLog({ write() { return Promise.reject(source) as never; } }, { level: "info", message: "fixed" }, undefined, selected);
  await new Promise<void>((resolve) => setImmediate(resolve)); expect({ ...detail, phase: "sink-completion", reason: "rejected" });
  const tracer: Tracer = { startSpan() { equal(this, tracer); throw source; } };
  const fallback = startPlatformTraceSpan(tracer, { name: "fixture.trace" }, undefined, selected);
  equal(typeof fallback.end, "function"); expect({ operation: "trace-start", phase: "span-invocation", field: "provider", reason: "threw", effect: "unknown" });
  startPlatformTraceSpan({ startSpan() { return source as never; } }, { name: "fixture.trace" }, undefined, selected);
  expect({ operation: "trace-start", phase: "span-validation", field: "result", reason: "invalid-span", effect: "unknown" });
  let parentReads = 0;
  throws(() => startPlatformTraceSpan(tracer, { name: "fixture.trace", get parent(): never { parentReads++; throw source; } }, undefined, selected), (error) => error === source);
  equal(parentReads, 2); equal(records.length, 20); equal((records[0]?.detail as PlatformObservationBoundaryDetail).phase, "input-projection"); equal((records[10]?.detail as PlatformObservationBoundaryDetail).effect, "fallback-threw"); records.length = 0;
  endPlatformTraceSpan({ context: fallback.context, end() { return Promise.reject(source) as never; } }, { outcome: "failed" }, undefined, selected);
  await new Promise<void>((resolve) => setImmediate(resolve)); expect({ operation: "trace-end", phase: "span-completion", field: "provider", reason: "rejected", effect: "unknown" });
  throws(() => platformTraceFields(Object.defineProperty({}, "route", { get() { throw source; } }), undefined, selected), (error) => error === source);
  expect({ operation: "trace-fields", phase: "input-projection", field: "route", reason: "threw", effect: "not-attempted" });
  const clock = fixedClock(new Date("2026-10-30T00:00:00Z"));
  const metrics: Metrics = { record() { throw new Error("must not call"); } };
  throws(() => recordPlatformRequestMetric(metrics, clock, Object.defineProperty({}, "latencyMs", { get() { throw source; } }) as never, undefined, undefined, selected), (error) => error === source);
  expect({ operation: "request-metric", phase: "input-projection", field: "latency", reason: "threw", effect: "not-attempted" });
  throws(() => recordPlatformJobMetric(metrics, clock, Object.defineProperty({}, "job", { get() { throw source; } }) as never, undefined, undefined, selected), (error) => error === source);
  expect({ operation: "job-metric", phase: "input-projection", field: "job", reason: "threw", effect: "not-attempted" });
  throws(() => recordPlatformHealthMetric(metrics, clock, Object.defineProperty({}, "healthState", { get() { throw source; } }) as never, undefined, selected), (error) => error === source);
  expect({ operation: "health-metric", phase: "input-projection", field: "health-state", reason: "threw", effect: "not-attempted" });
  throws(() => elapsedMilliseconds(new Date(), { getTime() { throw source; } } as unknown as Date, selected), (error) => error === source);
  expect({ operation: "request-observation", phase: "elapsed-computation", field: "latency", reason: "threw", effect: "observation-incomplete" });
  const readiness = createPlatformReadinessObserver({ identity: { target: "fixture", scope: "fixture", workload: "fixture", dependency: "fixture" }, probe: async () => ({ readiness: "ready" }),
    get logger(): never { throw source; }, metrics, clock, timeoutMs: 5, allowedDiagnosticCodes: ["fixture.failure"], defaultDiagnosticCode: "fixture.failure", observations: selected });
  await rejects(readiness.observe(), (error) => error === source);
  expect({ operation: "readiness-observation", phase: "input-projection", field: "logger", reason: "threw", effect: "event-not-returned" });
}

function classificationProof(): void {
  const canary = "private-class-canary@example.invalid";
  const binding = { errorClasses: ["APP_FIXED"] };
  for (const [error, expected] of [[new Error(canary), "Error"], [new EvalError(canary), "EvalError"],
    [new RangeError(canary), "RangeError"], [new ReferenceError(canary), "ReferenceError"], [new SyntaxError(canary), "SyntaxError"],
    [new TypeError(canary), "TypeError"], [new URIError(canary), "URIError"], [new AggregateError([], canary), "AggregateError"]] as const) {
    Object.defineProperty(error, "name", { get() { throw canary; } });
    equal(platformErrorClass(error), expected);
    deepEqual(normalizePlatformError(error), { name: expected });
    Object.defineProperty(error, "code", { value: canary });
    equal(platformErrorClass(error, binding), "unknown", "present undeclared code must not infer the native type");
    deepEqual(normalizePlatformError(error, binding), { name: expected, code: "unknown" });
  }
  let reads = 0;
  const accessor = Object.defineProperties(new TypeError(canary), {
    code: { get() { reads++; throw canary; } }, name: { get() { reads++; throw canary; } },
  });
  equal(platformErrorClass(accessor, binding), "unknown");
  deepEqual(normalizePlatformError(accessor, binding), { name: "TypeError", code: "unknown" });
  const object = Object.defineProperties({}, { code: { get() { reads++; throw canary; } }, name: { get() { reads++; throw canary; } } });
  equal(platformErrorClass(object, binding), "unknown");
  deepEqual(normalizePlatformError(object, binding), { type: "non-error-object", code: "unknown", name: "unknown" });
  equal(reads, 0);
  equal(platformErrorClass({ code: "APP_FIXED" }), "unknown");
  equal(platformErrorClass({ code: "APP_FIXED" }, binding), "APP_FIXED");
  equal(platformErrorClass({ name: "TypeError" }, binding), "unknown");
  equal(platformErrorClass(Object.create({ code: "APP_FIXED" }), binding), "unknown");
  const proxy = new Proxy({}, { getOwnPropertyDescriptor() { throw canary; }, get() { throw canary; }, getPrototypeOf() { throw canary; } });
  equal(platformErrorClass(proxy, binding), "unknown");
  deepEqual(normalizePlatformError(proxy, binding), { type: "non-error-object" });
  const privateError = Object.assign(new Error(canary), { code: canary });
  deepEqual(normalizePlatformValue({ nested: privateError }, binding), { nested: { name: "Error", code: "unknown" } });
  const logs: LogRecord[] = [];
  const logger: Logger = { write(record) { logs.push(record); } };
  writePlatformLog(logger, { level: "error", message: "fixture.class", error: privateError });
  createPlatformSafeLogger(logger, binding).write({ level: "error", message: "fixture.nested", fields: { error: Object.assign(new Error(canary), { code: "APP_FIXED" }) } });
  deepEqual(logs[0]?.fields?.["error"], { name: "Error", code: "unknown" });
  deepEqual(logs[1]?.fields?.["error"], { name: "Error", code: "APP_FIXED" });
  const points: MetricPoint[] = [];
  const metrics: Metrics = { record(point) { points.push(point); } };
  const clock = fixedClock(new Date("2026-10-30T00:00:00Z"));
  recordPlatformRequestMetric(metrics, clock, { method: "GET", route: "fixture", status: 503, latencyMs: 1, errorClass: "APP_FIXED" }, undefined, binding);
  recordPlatformJobMetric(metrics, clock, { job: "fixture", status: "failed", errorClass: canary }, undefined, binding);
  recordPlatformJobMetric(metrics, clock, { job: "fixture", status: "failed", errorClass: "APP_FIXED" });
  equal(points.length, 3);
  deepEqual(points.map((point) => point.labels?.["error_class"]), ["APP_FIXED", "unknown", "unknown"]);
  equal(platformTraceFields({ errorClass: canary }, binding)["errorClass"], "unknown");
  deepEqual(platformTraceAttributes({ errorClass: "APP_FIXED", error_class: canary }, binding), { errorClass: "APP_FIXED", error_class: "unknown" });
  const tracer = createInMemoryTracer();
  const span = startPlatformTraceSpan(tracer, { name: "fixture.class", attributes: { error_class: "APP_FIXED" } }, binding);
  endPlatformTraceSpan(span, { outcome: "failed", attributes: { error_class: "APP_FIXED" } }, binding);
  equal(tracer.spans()[0]?.attributes?.["error_class"], "APP_FIXED");
  equal(tracer.spans()[0]?.end?.attributes?.["error_class"], "APP_FIXED");
  equal(JSON.stringify({ logs, points, traces: tracer.spans() }).includes(canary), false);
  const observed = <T extends object>(value: T, reads: string[]): T => new Proxy(value, {
    get(target, key, receiver) { reads.push(String(key)); return Reflect.get(target, key, receiver); },
  });
  let fieldReads: string[] = [];
  platformTraceFields(observed({ errorClass: "APP_FIXED" }, fieldReads), binding);
  deepEqual(fieldReads, ["requestId", "correlationId", "tenant", "route", "job", "errorClass", "latencyMs", "retryCount", "healthState", "method", "status", "outcome"]);
  fieldReads = [];
  platformTraceAttributes(observed({ errorClass: "APP_FIXED", error_class: "APP_FIXED" }, fieldReads), binding);
  deepEqual(fieldReads, ["capability", "action", "actor_type", "interaction_source", "execution_context", "http_method", "http_status_code", "job_delivery_disposition", "route", "job", "errorClass", "error_class", "latencyMs", "retryCount", "healthState", "method", "status", "outcome"]);
  fieldReads = [];
  recordPlatformJobMetric(metrics, clock, observed({ job: "fixture", status: "failed", errorClass: "APP_FIXED" }, fieldReads), undefined, binding);
  deepEqual(fieldReads, ["job", "status", "retryCount", "errorClass"]);
  fieldReads = [];
  recordPlatformRequestMetric(metrics, clock, observed({ method: "GET", route: "fixture", status: 503, latencyMs: 1, errorClass: "APP_FIXED" }, fieldReads), undefined, binding);
  deepEqual(fieldReads, ["latencyMs", "method", "route", "status", "status", "errorClass"]);
}

main()
  .then(() => {
    console.log("platform/observability runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
