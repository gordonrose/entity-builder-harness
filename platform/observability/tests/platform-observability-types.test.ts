import type { Logger } from "@kanbien/core/logging";
import type { Metrics } from "@kanbien/core/monitoring";
import { fixedClock } from "@kanbien/core/shared";
import {
  createPlatformSafeLogger,
  normalizePlatformLogFields,
  recordPlatformJobMetric,
  recordPlatformMetric,
  recordPlatformRequestMetric,
} from "../src/index";

const logger: Logger = { write: () => undefined };
const safeLogger: Logger = createPlatformSafeLogger(logger);
safeLogger.write({ level: "info", message: "hello", fields: normalizePlatformLogFields({ ok: true }) });

const metrics: Metrics = { record: () => undefined };
const clock = fixedClock(new Date("2026-07-10T00:00:00.000Z"));
recordPlatformMetric(metrics, clock, { name: "platform.custom.metric", labels: { status: "ok" } });
recordPlatformRequestMetric(metrics, clock, { method: "GET", route: "smoke.echo", status: 200, latencyMs: 1 });
recordPlatformJobMetric(metrics, clock, { job: "smoke.rebuild", status: "succeeded" });

// @ts-expect-error metric names are required
recordPlatformMetric(metrics, clock, { labels: { status: "ok" } });
