import type { QueueMessage } from "@kanbien/core/queues";
import { isoDateTimeFromDate, type ISODateTime, type Result } from "@kanbien/core/shared";
import { workerFailure, type PlatformWorkerError } from "./errors";
import type {
  PlatformWorkerDeadLetter,
  PlatformWorkerIdempotencyStore,
  PlatformWorkerQueue,
  PlatformWorkerQueueEntry,
} from "./types";

export function createInMemoryPlatformWorkerQueue(input: {
  readonly now?: () => ISODateTime;
} = {}): PlatformWorkerQueue {
  const now = input.now ?? (() => defaultNow);
  const pending: PlatformWorkerQueueEntry[] = [];
  const deadLetters: PlatformWorkerDeadLetter[] = [];
  let closed = false;

  return {
    enqueue(message) {
      if (closed) {
        return workerFailure("PLATFORM_WORKER_QUEUE_CLOSED", "Worker queue is closed.");
      }

      pending.push({ message, attempt: 1, enqueuedAt: now() });
      return workerSuccess();
    },
    next() {
      return pending.shift();
    },
    retry(entry, delayMs) {
      if (closed) {
        return workerFailure("PLATFORM_WORKER_QUEUE_CLOSED", "Worker queue is closed.");
      }

      pending.push({
        message: entry.message,
        attempt: entry.attempt + 1,
        enqueuedAt: now(),
        delayMs,
      });
      return workerSuccess();
    },
    deadLetter(entry, error) {
      deadLetters.push({
        message: entry.message,
        attempts: entry.attempt,
        failedAt: now(),
        error,
      });
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
