import { deepEqual, equal } from "node:assert/strict";
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
  platformErrorClass,
  platformTraceAttributes,
  platformTraceFields,
  recordPlatformHealthMetric,
  recordPlatformJobMetric,
  recordPlatformRequestMetric,
  startPlatformTraceSpan,
  writePlatformLog,
} from "../src/index";
import { platformReadinessObservationEvent } from "@kanbien/platform-contracts";

async function main(): Promise<void> {
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
  });
  equal(records[1]?.correlationId, "corr-1");
  deepEqual(records[1]?.fields?.["headers"], { cookie: "[REDACTED]", accept: "json" });
  deepEqual(records[1]?.fields?.["error"], { name: "Error", code: "E_NOPE" });
  equal(platformErrorClass(Object.assign(new Error("nope"), { code: "E_NOPE" })), "E_NOPE");
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
  });
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
    errorClass: "do-not-store-secret",
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
  equal(timedOutEvent.diagnosticCode, "persistence.transport-unavailable");
  equal(timedOutRecords[0]?.fields?.["diagnostic_code"], "persistence.transport-unavailable");

}

main()
  .then(() => {
    console.log("platform/observability runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
