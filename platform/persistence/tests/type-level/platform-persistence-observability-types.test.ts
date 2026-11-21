import type { Logger } from "@kanbien/core/logging";
import { noopTracer, type Metrics } from "@kanbien/core/monitoring";
import { fixedClock } from "@kanbien/core/shared";
import { platformCapabilityName, platformObservabilityProfileName } from "@kanbien/platform-contracts";
import {
  createPlatformPersistenceTransitionObserver,
  platformPersistenceTransitionProfile,
  persistenceBoundaryDiagnosticRecord,
} from "../../src/index";

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
observer.value.record({ transition: "processing.completion_failed", outcome: "failed", diagnosticRecord: persistenceBoundaryDiagnosticRecord({ operation: "transaction", phase: "completion", boundary: "commit", condition: "threw", effect: "unknown" }) });
observer.value.onDiagnostic?.(persistenceBoundaryDiagnosticRecord({ operation: "read_outbox", phase: "invocation", boundary: "decode", condition: "threw", effect: "not-assessed" }));
observer.value.onDiagnostic?.(persistenceBoundaryDiagnosticRecord({ operation: "read_outbox", phase: "invocation", boundary: "decode", condition: "threw", effect: "not-assessed" }), "relay");
// @ts-expect-error only approved persistence observation operations are accepted.
observer.value.onDiagnostic?.(persistenceBoundaryDiagnosticRecord({ operation: "read_outbox", phase: "invocation", boundary: "decode", condition: "threw", effect: "not-assessed" }), "send-to-provider");

// @ts-expect-error persistence transition names remain a closed reviewed vocabulary.
observer.value.record({ transition: "outbox.unreviewed", outcome: "succeeded" });
