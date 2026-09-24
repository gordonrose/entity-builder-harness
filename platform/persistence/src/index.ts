export { platformPersistenceError } from "./errors";
export type { PlatformPersistenceError, PlatformPersistenceErrorCode } from "./errors";

export { recordPlatformPersistenceObservation } from "./observability";
export type {
  PlatformPersistenceObservation,
  PlatformPersistenceObserver,
  PlatformPersistenceTransition,
  PlatformPersistenceTransitionOutcome,
} from "./observability";

export {
  initialPlatformPersistenceAttempt,
  nextPlatformPersistenceLease,
  platformLeaseExpired,
  platformOutboxRecord,
  platformPersistenceAttempt,
  platformPersistenceFence,
  platformPersistenceLease,
  platformPersistenceLeaseOwner,
  platformProcessingRecord,
} from "./types";
export type {
  PlatformOutboxRecord,
  PlatformOutboxState,
  PlatformPersistenceAttempt,
  PlatformPersistenceFence,
  PlatformPersistenceLease,
  PlatformPersistenceLeaseOwner,
  PlatformProcessingCompletion,
  PlatformProcessingOutcome,
  PlatformProcessingRecord,
  PlatformProcessingState,
} from "./types";

export { createInMemoryPlatformOutboxStore } from "./outbox";
export type { PlatformOutboxClaimResult, PlatformOutboxStore } from "./outbox";

export { createInMemoryPlatformProcessingStore } from "./processing";
export type {
  PlatformProcessingClaimResult,
  PlatformProcessingCompletionResult,
  PlatformProcessingStore,
} from "./processing";

export { createInMemoryPlatformRecordChangeStore } from "./lineage";
export type { PlatformRecordChangeStore } from "./lineage";

export {
  createPlatformOutboxRelay,
  platformOutboxQueueMessage,
} from "./relay";
export type {
  PlatformOutboxQueuePayload,
  PlatformOutboxRelay,
  PlatformOutboxRelayOptions,
  PlatformOutboxRelayRunResult,
} from "./relay";

export { platformPersistenceMutation } from "./transaction";
export type {
  PlatformPersistenceAtomicWriter,
  PlatformPersistenceMutation,
  PlatformPersistenceTransactionScope,
} from "./transaction";
