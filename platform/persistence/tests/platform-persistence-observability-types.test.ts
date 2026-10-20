import type { Logger } from "@kanbien/core/logging";
import { noopTracer, type Metrics } from "@kanbien/core/monitoring";
import { fixedClock } from "@kanbien/core/shared";
import { platformCapabilityName, platformObservabilityProfileName } from "@kanbien/platform-contracts";
import {
  createPlatformPersistenceTransitionObserver,
  platformPersistenceTransitionProfile,
} from "../src/index";

const profileName = platformObservabilityProfileName("platform.persistence.outbox.relay");
const capability = platformCapabilityName("platform.persistence.outbox.relay");
if (!profileName.ok || !capability.ok) {
  throw new Error("Expected valid persistence observability identifiers.");
}

const logger: Logger = { write: () => undefined };
const metrics: Metrics = { record: () => undefined };
const observer = createPlatformPersistenceTransitionObserver({
  profile: platformPersistenceTransitionProfile({ name: profileName.value, capability: capability.value }),
  executionContext: "worker",
  logger,
  metrics,
  tracer: noopTracer,
  clock: fixedClock(new Date("2026-10-19T00:00:00.000Z")),
});
if (!observer.ok) {
  throw new Error("Expected a valid persistence transition observer.");
}
observer.value.record({ transition: "outbox.claimed", outcome: "succeeded" });

// @ts-expect-error persistence transition names remain a closed reviewed vocabulary.
observer.value.record({ transition: "outbox.unreviewed", outcome: "succeeded" });
