import type { Logger } from "@kanbien/core/logging";
import { noopTracer, type Metrics, type Tracer } from "@kanbien/core/monitoring";
import { fixedClock } from "@kanbien/core/shared";
import {
  createPlatformSafeLogger,
  endPlatformTraceSpan,
  normalizePlatformLogFields,
  recordPlatformJobMetric,
  recordPlatformMetric,
  recordPlatformRequestMetric,
  startPlatformTraceSpan,
} from "../src/index";

const logger: Logger = { write: () => undefined };
const safeLogger: Logger = createPlatformSafeLogger(logger);
safeLogger.write({ level: "info", message: "hello", fields: normalizePlatformLogFields({ ok: true }) });

const metrics: Metrics = { record: () => undefined };
const clock = fixedClock(new Date("2026-07-10T00:00:00.000Z"));
recordPlatformMetric(metrics, clock, { name: "platform.custom.metric", labels: { status: "ok" } });
recordPlatformRequestMetric(metrics, clock, { method: "GET", route: "smoke.echo", status: 200, latencyMs: 1 });
recordPlatformJobMetric(metrics, clock, { job: "smoke.rebuild", status: "succeeded" });

const tracer: Tracer = noopTracer;
const span = startPlatformTraceSpan(tracer, {
  name: "platform.server.request",
  attributes: { method: "GET", route: "smoke.echo" },
});
endPlatformTraceSpan(span, { outcome: "succeeded", attributes: { status: 200 } });

// @ts-expect-error metric names are required
recordPlatformMetric(metrics, clock, { labels: { status: "ok" } });

// @ts-expect-error trace attributes are deliberately scalar rather than objects.
startPlatformTraceSpan(tracer, { name: "platform.server.request", attributes: { route: { nested: true } } });
