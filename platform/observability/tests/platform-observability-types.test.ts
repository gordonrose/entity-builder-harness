import type { Logger } from "@kanbien/core/logging";
import { noopTracer, type Metrics, type Tracer } from "@kanbien/core/monitoring";
import { fixedClock } from "@kanbien/core/shared";
import {
  platformCapabilityName,
  platformObservabilityProfileName,
} from "@kanbien/platform-contracts";
import {
  createPlatformSafeLogger,
  createPlatformPersistenceTransitionObserver,
  endPlatformTraceSpan,
  normalizePlatformLogFields,
  recordPlatformJobMetric,
  recordPlatformMetric,
  recordPlatformRequestMetric,
  startPlatformTraceSpan,
  platformPersistenceTransitionProfile,
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

const persistenceProfileName = platformObservabilityProfileName("platform.persistence.outbox.relay");
const persistenceCapabilityName = platformCapabilityName("platform.persistence.outbox.relay");
if (!persistenceProfileName.ok || !persistenceCapabilityName.ok) {
  throw new Error("Expected valid persistence observability identifiers.");
}
const persistenceProfile = platformPersistenceTransitionProfile({
  name: persistenceProfileName.value,
  capability: persistenceCapabilityName.value,
});
const persistenceObserver = createPlatformPersistenceTransitionObserver({
  profile: persistenceProfile,
  executionContext: "worker",
  logger,
  metrics,
  clock,
});
if (!persistenceObserver.ok) {
  throw new Error("Expected valid persistence transition observer.");
}
persistenceObserver.value.record({ transition: "outbox.claimed", outcome: "succeeded" });

// @ts-expect-error persistence transition names are a closed reviewed vocabulary.
persistenceObserver.value.record({ transition: "outbox.anything", outcome: "succeeded" });

// @ts-expect-error metric names are required
recordPlatformMetric(metrics, clock, { labels: { status: "ok" } });

// @ts-expect-error trace attributes are deliberately scalar rather than objects.
startPlatformTraceSpan(tracer, { name: "platform.server.request", attributes: { route: { nested: true } } });
