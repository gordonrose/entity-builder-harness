import type { QueueMessage } from "@kanbien/core/queues";
import { isoDateTimeFromDate, type ISODateTime, type Result } from "@kanbien/core/shared";
import { workerFailure, type PlatformWorkerError } from "./errors";
import { captureWorkerDiagnostic, observeWorkerQueueDiagnostic, workerDeliveryBoundaryRecord, workerDeliveryRejectedRecord, type PlatformWorkerQueueDiagnosticOptions, type WorkerDeliveryBoundaryDetail } from "./diagnostics";
import type {
  PlatformWorkerDeadLetter,
  PlatformWorkerIdempotencyStore,
  PlatformWorkerQueue,
  PlatformWorkerQueueEntry,
} from "./types";

export function createInMemoryPlatformWorkerQueue(input: PlatformWorkerQueueDiagnosticOptions & {
  readonly now?: () => ISODateTime;
} = {}): PlatformWorkerQueue {
  const now = input.now ?? (() => defaultNow);
  const pending: PlatformWorkerQueueEntry[] = [];
  const deadLetters: PlatformWorkerDeadLetter[] = [];
  let closed = false;

  return {
    enqueue(message) {
      if (closed) {
        const own = captureWorkerDiagnostic(() => workerDeliveryRejectedRecord({ operation: "queue-enqueue", field: "queue-state", condition: "closed", effect: "queue-not-mutated" }));
        observeWorkerQueueDiagnostic(input, own);
        return workerFailure("PLATFORM_WORKER_QUEUE_CLOSED", "Worker queue is closed.", undefined, undefined, [], own);
      }

      let phase: WorkerDeliveryBoundaryDetail["phase"] = "queue-mutation";
      let stamp: ISODateTime;
      try { pending.push({ message, attempt: 1, enqueuedAt: (phase = "queue-clock", stamp = now(), phase = "queue-mutation", stamp) }); }
      catch (error) { observeWorkerQueueDiagnostic(input, captureWorkerDiagnostic(() => workerDeliveryBoundaryRecord({ operation: "queue-enqueue", phase, reason: "thrown", effect: phase === "queue-clock" ? "queue-not-mutated" : "queue-mutation-unknown" })), error); throw error; }
      return workerSuccess();
    },
    next() {
      return pending.shift();
    },
    retry(entry, delayMs) {
      if (closed) {
        const own = captureWorkerDiagnostic(() => workerDeliveryRejectedRecord({ operation: "queue-retry", field: "queue-state", condition: "closed", effect: "queue-not-mutated" }));
        observeWorkerQueueDiagnostic(input, own);
        return workerFailure("PLATFORM_WORKER_QUEUE_CLOSED", "Worker queue is closed.", undefined, undefined, [], own);
      }

      let phase: WorkerDeliveryBoundaryDetail["phase"] = "queue-mutation";
      let stamp: ISODateTime;
      try { pending.push({
        message: entry.message,
        attempt: entry.attempt + 1,
        enqueuedAt: (phase = "queue-clock", stamp = now(), phase = "queue-mutation", stamp),
        delayMs,
      }); } catch (error) { observeWorkerQueueDiagnostic(input, captureWorkerDiagnostic(() => workerDeliveryBoundaryRecord({ operation: "queue-retry", phase, reason: "thrown", effect: phase === "queue-clock" ? "queue-not-mutated" : "queue-mutation-unknown" })), error); throw error; }
      return workerSuccess();
    },
    deadLetter(entry, error) {
      let phase: WorkerDeliveryBoundaryDetail["phase"] = "queue-mutation";
      let stamp: ISODateTime;
      try { deadLetters.push({
        message: entry.message,
        attempts: entry.attempt,
        failedAt: (phase = "queue-clock", stamp = now(), phase = "queue-mutation", stamp),
        error,
      }); } catch (error) { observeWorkerQueueDiagnostic(input, captureWorkerDiagnostic(() => workerDeliveryBoundaryRecord({ operation: "queue-dead-letter", phase, reason: "thrown", effect: phase === "queue-clock" ? "queue-not-mutated" : "queue-mutation-unknown" })), error); throw error; }
    },
    pending: () => pending.map(copyQueueEntry),
    deadLetters: () => deadLetters.map(copyDeadLetter),
    close() {
      closed = true;
    },
    isClosed: () => closed,
  };
}

export function createInMemoryPlatformWorkerIdempotencyStore(): PlatformWorkerIdempotencyStore {
  const processed = new Set<string>();

  return {
    hasProcessed: (key) => processed.has(key),
    recordProcessed: (key) => {
      processed.add(key);
    },
  };
}

export function workerQueueNow(clock: { readonly now: () => Date }): () => ISODateTime {
  return () => isoDateTimeFromDate(clock.now());
}

function workerSuccess(): Result<void, PlatformWorkerError> {
  return { ok: true, value: undefined };
}

function copyQueueEntry(entry: PlatformWorkerQueueEntry): PlatformWorkerQueueEntry {
  return { ...entry };
}

function copyDeadLetter(deadLetter: PlatformWorkerDeadLetter): PlatformWorkerDeadLetter {
  return {
    ...deadLetter,
    error: { ...deadLetter.error },
  };
}

const defaultNow = "2026-07-10T00:00:00.000Z" as ISODateTime;
