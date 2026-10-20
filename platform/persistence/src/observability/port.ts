import type { TraceContext } from "@kanbien/core/monitoring";
import type { CorrelationId } from "@kanbien/core/shared";

export const platformPersistenceTransitions = [
  "outbox.delivery.lookup_failed",
  "outbox.claim_failed",
  "outbox.claimed",
  "outbox.lease_active",
  "outbox.queue_send_failed",
  "outbox.publish_marker_failed",
  "outbox.published",
  "outbox.envelope_rejected",
  "processing.envelope_rejected",
  "processing.claim_failed",
  "processing.claimed",
  "processing.lease_active",
  "processing.duplicate_succeeded",
  "processing.duplicate_terminal_failure",
  "processing.completed",
  "processing.completion_failed",
  "processing.retry_released",
  "processing.terminal_failure_recorded",
  "processing.settlement_failed",
] as const;

export type PlatformPersistenceTransition = (typeof platformPersistenceTransitions)[number];

export type PlatformPersistenceTransitionOutcome = "succeeded" | "rejected" | "failed";

export interface PlatformPersistenceObservation {
  readonly transition: PlatformPersistenceTransition;
  readonly outcome: PlatformPersistenceTransitionOutcome;
  readonly correlationId?: CorrelationId;
  readonly traceParent?: TraceContext;
  readonly error?: unknown;
}

export interface PlatformPersistenceObserver {
  record(observation: PlatformPersistenceObservation): void;
}

export function recordPlatformPersistenceObservation(
  observer: PlatformPersistenceObserver | undefined,
  observation: PlatformPersistenceObservation,
): void {
  if (observer === undefined) {
    return;
  }

  try {
    observer.record(observation);
  } catch {
    // Telemetry failure must not alter an already-completed durable transition.
  }
}
