import { deepEqual, equal } from "node:assert/strict";
import type { Logger, LogRecord } from "@kanbien/core/logging";
import type { MetricPoint, Metrics } from "@kanbien/core/monitoring";
import { correlationId, fixedClock } from "@kanbien/core/shared";
import {
  createPlatformSafeLogger,
  elapsedMilliseconds,
  normalizePlatformError,
  normalizePlatformLogFields,
  platformErrorClass,
  platformTraceFields,
  recordPlatformHealthMetric,
  recordPlatformJobMetric,
  recordPlatformRequestMetric,
  writePlatformLog,
} from "../src/index";

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
  deepEqual(records[1]?.fields?.["error"], { name: "Error", message: "nope", code: "E_NOPE" });
  equal(platformErrorClass(Object.assign(new Error("nope"), { code: "E_NOPE" })), "E_NOPE");
  deepEqual(normalizePlatformError("plain"), { message: "plain" });

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
  });
}

main()
  .then(() => {
    console.log("platform/observability runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
