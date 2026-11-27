import type { Tracer } from "@kanbien/core/monitoring";
import type { QueueMessage } from "@kanbien/core/queues";
import type { ISODateTime, Result } from "@kanbien/core/shared";
import type { PlatformApp, PlatformDiagnosticCatalog, PlatformJobName, PlatformMountDeps } from "@kanbien/platform-contracts";
import type { PlatformReadinessSummary } from "@kanbien/platform-health";
import type {
  PlatformPersistenceLeaseOwner,
  PlatformPersistenceObserver,
  PlatformProcessingStore,
  PlatformOutboxStore,
} from "@kanbien/platform-persistence";
import type { PlatformRuntimeLifecycleController, PlatformRuntimeMountResult } from "@kanbien/platform-runtime";
import type { PlatformWorkerError } from "./errors";

export interface PlatformWorkerQueueEntry {
  readonly message: QueueMessage;
  readonly attempt: number;
  readonly enqueuedAt: ISODateTime;
  readonly delayMs?: number;
}

export interface PlatformWorkerDeadLetter {
  readonly message: QueueMessage;
  readonly attempts: number;
  readonly failedAt: ISODateTime;
  readonly error: PlatformWorkerError;
}

export interface PlatformWorkerQueue {
  enqueue(message: QueueMessage): Result<void, PlatformWorkerError>;
  next(): PlatformWorkerQueueEntry | undefined;
  retry(entry: PlatformWorkerQueueEntry, delayMs: number): Result<void, PlatformWorkerError>;
  deadLetter(entry: PlatformWorkerQueueEntry, error: PlatformWorkerError): void;
  pending(): readonly PlatformWorkerQueueEntry[];
  deadLetters(): readonly PlatformWorkerDeadLetter[];
  close(): void;
  isClosed(): boolean;
}

export interface PlatformWorkerIdempotencyStore {
  hasProcessed(key: string): Promise<boolean> | boolean;
  recordProcessed(key: string): Promise<void> | void;
}

export type PlatformWorkerRunStatus = "idle" | "succeeded" | "retry" | "dead-lettered";
export type PlatformWorkerIdempotencyOutcome =
  | "none"
  | "processed"
  | "skipped"
  | "durable-processed"
  | "durable-skipped";

/** Enables durable-outbox processing for one worker shell and its queue. */
export interface PlatformWorkerDurableOutboxProcessingOptions {
  readonly processingStore: PlatformProcessingStore;
  readonly owner: PlatformPersistenceLeaseOwner;
  readonly leaseDurationMs: number;
  readonly observer?: PlatformPersistenceObserver;
  /** Required for external delivery: the selected scope's authoritative envelope. */
  readonly outbox?: Pick<PlatformOutboxStore, "get">;
}

/** Terminal is retained for transport redrive, not a claimed failed-queue send. */
export type PlatformWorkerDeliveryResult =
  | Exclude<PlatformWorkerRunNextResult, { readonly status: "idle" | "dead-lettered" }>
  | (Omit<Extract<PlatformWorkerRunNextResult, { readonly status: "dead-lettered" }>, "status"> & { readonly status: "terminal" });

export type PlatformWorkerRunNextResult =
  | { readonly status: "idle" }
  | {
      readonly status: "succeeded";
      readonly jobName: PlatformJobName;
      readonly message: QueueMessage;
      readonly attempt: number;
      readonly idempotency: PlatformWorkerIdempotencyOutcome;
    }
  | {
      readonly status: "retry";
      readonly jobName?: PlatformJobName;
      readonly message: QueueMessage;
      readonly attempt: number;
      readonly nextAttempt: number;
      readonly delayMs: number;
      readonly error: PlatformWorkerError;
    }
  | {
      readonly status: "dead-lettered";
      readonly jobName?: PlatformJobName;
      readonly message: QueueMessage;
      readonly attempt: number;
      readonly error: PlatformWorkerError;
    };

export interface PlatformWorkerShellOptions {
  readonly diagnosticCatalogs?: readonly PlatformDiagnosticCatalog[];
  readonly apps: readonly PlatformApp[];
  readonly deps: PlatformMountDeps;
  readonly queue?: PlatformWorkerQueue;
  readonly idempotency?: PlatformWorkerIdempotencyStore;
  readonly durableOutboxProcessing?: PlatformWorkerDurableOutboxProcessingOptions;
  readonly tracer?: Tracer;
  readonly maxAttempts?: number;
  readonly retryBackoffMs?: (attempt: number) => number;
}

export interface PlatformWorkerRunUntilIdleOptions {
  readonly maxIterations?: number;
}

export interface PlatformWorkerShell {
  readonly mounted: PlatformRuntimeMountResult;
  readonly queue: PlatformWorkerQueue;
  readonly lifecycle: PlatformRuntimeLifecycleController;
  start(): Promise<Result<void, PlatformWorkerError>>;
  enqueue(message: QueueMessage): Result<void, PlatformWorkerError>;
  runNext(): Promise<Result<PlatformWorkerRunNextResult, PlatformWorkerError>>;
  runDelivery(message: QueueMessage): Promise<Result<PlatformWorkerDeliveryResult, PlatformWorkerError>>;
  runUntilIdle(options?: PlatformWorkerRunUntilIdleOptions): Promise<Result<readonly PlatformWorkerRunNextResult[], PlatformWorkerError>>;
  health(): Promise<PlatformReadinessSummary>;
  shutdown(): Promise<Result<void, PlatformWorkerError>>;
}
