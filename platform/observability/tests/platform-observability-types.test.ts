import type { Logger } from "@kanbien/core/logging";
import { noopTracer, type Metrics, type Tracer } from "@kanbien/core/monitoring";
import { fixedClock } from "@kanbien/core/shared";
import {
  createPlatformSafeLogger,
  createPlatformMetricDiagnosticBinding,
  endPlatformTraceSpan,
  normalizePlatformLogFields,
  recordPlatformJobMetric,
  recordPlatformMetric,
  recordPlatformRequestMetric,
  startPlatformTraceSpan,
  reportPlatformObservationBoundary,
  reportPlatformObservationSources,
  type PlatformObservationDiagnostics,
} from "../src/index";

const logger: Logger = { write: () => undefined };
const observations: PlatformObservationDiagnostics = { context: { capability: "fixture", operation: "log-write", stage: "runtime" },
  reporter: { report() { return { status: "written" }; } }, definitions: [] };
reportPlatformObservationBoundary(observations, { operation: "log-write", phase: "sink-invocation", reason: "threw", effect: "unknown" });
reportPlatformObservationSources(observations, undefined);
createPlatformSafeLogger(logger, undefined, observations);
const safeLogger: Logger = createPlatformSafeLogger(logger);
const classBinding = { errorClasses: ["APP_FIXED"] } as const;
createPlatformSafeLogger(logger, classBinding);
safeLogger.write({ level: "info", message: "hello", fields: normalizePlatformLogFields({ ok: true }) });

const metrics: Metrics = { record: () => undefined };
const clock = fixedClock(new Date("2026-07-10T00:00:00.000Z"));
recordPlatformMetric(metrics, clock, { name: "platform.custom.metric", labels: { status: "ok" } });
recordPlatformRequestMetric(metrics, clock, { method: "GET", route: "smoke.echo", status: 200, latencyMs: 1 });
recordPlatformJobMetric(metrics, clock, { job: "smoke.rebuild", status: "succeeded" });
recordPlatformJobMetric(metrics, clock, { job: "smoke.rebuild", status: "failed", errorClass: "APP_FIXED" }, undefined, classBinding);
recordPlatformRequestMetric(metrics, clock, { method: "GET", route: "smoke.echo", status: 503, latencyMs: 1, errorClass: "APP_FIXED" }, undefined, classBinding);
const metricBinding = createPlatformMetricDiagnosticBinding(undefined, { capability: "observability", stage: "request" });
recordPlatformMetric(metrics, clock, { name: "fixture.metric" }, { binding: metricBinding, operation: "request-outcome" });
// @ts-expect-error caller operations are closed, not arbitrary runtime input.
recordPlatformMetric(metrics, clock, { name: "fixture.metric" }, { binding: metricBinding, operation: "provider-secret" });

const tracer: Tracer = noopTracer;
const span = startPlatformTraceSpan(tracer, {
  name: "platform.server.request",
  attributes: { method: "GET", route: "smoke.echo" },
});
endPlatformTraceSpan(span, { outcome: "succeeded", attributes: { status: 200 } });
endPlatformTraceSpan(span, { outcome: "failed", attributes: { error_class: "APP_FIXED" } }, classBinding);
startPlatformTraceSpan(tracer, { name: "platform.server.request" }, classBinding, observations);
endPlatformTraceSpan(span, { outcome: "succeeded" }, classBinding, observations);
recordPlatformRequestMetric(metrics, clock, { method: "GET", route: "smoke.echo", status: 200, latencyMs: 1 }, undefined, classBinding, observations);
// @ts-expect-error selected error classes are string declarations, never arbitrary values.
createPlatformSafeLogger(logger, { errorClasses: [42] });

// @ts-expect-error metric names are required
recordPlatformMetric(metrics, clock, { labels: { status: "ok" } });

// @ts-expect-error trace attributes are deliberately scalar rather than objects.
startPlatformTraceSpan(tracer, { name: "platform.server.request", attributes: { route: { nested: true } } });
