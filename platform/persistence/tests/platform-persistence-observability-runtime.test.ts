import { deepEqual, equal } from "node:assert/strict";
import type { Logger, LogRecord } from "@kanbien/core/logging";
import { createInMemoryTracer, type MetricPoint, type Metrics } from "@kanbien/core/monitoring";
import { correlationId, fixedClock } from "@kanbien/core/shared";
import { platformCapabilityName, platformObservabilityProfileName } from "@kanbien/platform-contracts";
import {
  createPlatformPersistenceTransitionObserver,
  platformPersistenceTransitionProfile,
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
}

main().then(
  () => console.log("platform/persistence observability runtime test passed."),
  (error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  },
);
