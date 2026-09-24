import type { TraceContext } from "@kanbien/core/monitoring"; // Preserve optional trace continuity without choosing a tracing provider.
import type { CorrelationId } from "@kanbien/core/shared"; // Preserve the existing safe cross-system correlation primitive without exposing business data.

export const platformPersistenceTransitions = [ // Name the finite persistence coordination transitions that may produce operational evidence.
  "outbox.delivery.lookup_failed", // Report that the relay could not inspect due durable work.
  "outbox.claim_failed", // Report that the relay could not acquire a durable outbox claim.
  "outbox.claimed", // Report that one relay acquired the current fenced outbox claim.
  "outbox.lease_active", // Report that another valid relay lease already owns the outbox work.
  "outbox.queue_send_failed", // Report that the relay could not hand its minimal envelope to the queue.
  "outbox.publish_marker_failed", // Report that queue acceptance occurred but the durable publication marker could not be written.
  "outbox.published", // Report that a durable outbox obligation was safely marked published.
  "outbox.envelope_rejected", // Report that a durable outbox entry could not form a safe Core queue envelope.
  "processing.envelope_rejected", // Report that a worker delivery did not preserve the one required outbox identity.
  "processing.claim_failed", // Report that a worker could not read or claim its durable processing state.
  "processing.claimed", // Report that one worker acquired the current fenced processing claim.
  "processing.lease_active", // Report that a different valid worker claim currently owns the delivery.
  "processing.duplicate_succeeded", // Report that a previously successful delivery was safely suppressed.
  "processing.duplicate_terminal_failure", // Report that a prior terminal failure was safely suppressed while retaining its DLQ outcome.
  "processing.completed", // Report that durable successful processing was recorded before acknowledgement.
  "processing.completion_failed", // Report that a worker could not record a required durable completion marker.
  "processing.retry_released", // Report that a temporary failure made the durable claim immediately eligible for a later retry.
  "processing.terminal_failure_recorded", // Report that a terminal failure was durably recorded before the DLQ outcome.
  "processing.settlement_failed", // Report that a required retry-release or terminal-completion transition could not be stored.
] as const; // Preserve the literal union so callers cannot invent unreviewed transition names.

export type PlatformPersistenceTransition = (typeof platformPersistenceTransitions)[number]; // Represent one reviewed durable-coordination transition.

export type PlatformPersistenceTransitionOutcome = "succeeded" | "rejected" | "failed"; // Keep transition outcomes bounded and separate from provider-specific queue results.

export interface PlatformPersistenceObservation { // Describe the minimal provider-neutral fact emitted after one persistence transition.
  readonly transition: PlatformPersistenceTransition; // Name the fixed transition rather than exposing a store operation or provider call.
  readonly outcome: PlatformPersistenceTransitionOutcome; // State whether this transition completed, was precondition-rejected, or failed.
  readonly correlationId?: CorrelationId; // Carry only the existing safe correlation reference for logs, never as a metric label or trace attribute.
  readonly traceParent?: TraceContext; // Continue an existing trace when the calling boundary has one.
  readonly error?: unknown; // Let the selected observability implementation reduce an error to a bounded classification.
}

export interface PlatformPersistenceObserver { // Define the narrow port through which persistence can request operational evidence.
  record(observation: PlatformPersistenceObservation): void; // Accept one safe transition fact without returning a provider result into persistence control flow.
}

export function recordPlatformPersistenceObservation( // Deliver one optional observation without allowing telemetry failure to alter durable work semantics.
  observer: PlatformPersistenceObserver | undefined, // Allow source-only and deterministic callers to omit telemetry explicitly.
  observation: PlatformPersistenceObservation, // Receive the already bounded transition fact.
): void { // Keep the port synchronous so persistence state sequencing remains direct and testable.
  if (observer === undefined) { // Avoid constructing an observability dependency when composition did not select one.
    return; // Preserve the same persistence behaviour with no telemetry sink.
  }

  try { // Isolate arbitrary observer implementation failure from the state transition that has already occurred.
    observer.record(observation); // Delegate the safe fact to the target-selected observability implementation.
  } catch { // Treat operational evidence as best effort, consistent with the platform observability policy.
    // A logger, metrics exporter, or tracer outage must not turn durable work into a false persistence failure.
  }
}
