import type { OutboxEntryId } from "@kanbien/core/persistence";
import type { ISODateTime, Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError } from "./errors";
import {
  nextPlatformPersistenceLease,
  initialPlatformPersistenceAttempt,
  platformLeaseExpired,
  platformProcessingRecord,
  type PlatformPersistenceFence,
  type PlatformPersistenceLeaseOwner,
  type PlatformProcessingOutcome,
  type PlatformProcessingRecord,
} from "./types";

export type PlatformProcessingClaimResult =
  | { readonly disposition: "claimed"; readonly record: PlatformProcessingRecord }
  | { readonly disposition: "lease-active"; readonly record: PlatformProcessingRecord }
  | { readonly disposition: "already-completed"; readonly record: PlatformProcessingRecord };

export type PlatformProcessingCompletionResult =
  | { readonly disposition: "completed"; readonly record: PlatformProcessingRecord }
  | { readonly disposition: "already-completed"; readonly record: PlatformProcessingRecord };

export interface PlatformProcessingStore {
  get(outboxEntryId: OutboxEntryId): Promise<PlatformProcessingRecord | null>;
  claim(input: {
    readonly outboxEntryId: OutboxEntryId;
    readonly owner: PlatformPersistenceLeaseOwner;
    readonly acquiredAt: ISODateTime;
    readonly leaseDurationMs: number;
  }): Promise<Result<PlatformProcessingClaimResult, PlatformPersistenceError>>;
  complete(input: {
    readonly outboxEntryId: OutboxEntryId;
    readonly fence: PlatformPersistenceFence;
    readonly outcome: PlatformProcessingOutcome;
    readonly completedAt: ISODateTime;
  }): Promise<Result<PlatformProcessingCompletionResult, PlatformPersistenceError>>;
  release(input: {
    readonly outboxEntryId: OutboxEntryId;
    readonly fence: PlatformPersistenceFence;
    readonly releasedAt: ISODateTime;
  }): Promise<Result<PlatformProcessingRecord, PlatformPersistenceError>>;
}

export function createInMemoryPlatformProcessingStore(): PlatformProcessingStore {
  const records = new Map<OutboxEntryId, PlatformProcessingRecord>();

  return {
    async get(outboxEntryId) {
      const record = records.get(outboxEntryId);
      return record === undefined ? null : copyProcessingRecord(record);
    },

    async claim(input) {
      const record = records.get(input.outboxEntryId);
      if (record?.state === "completed") {
        return success({ disposition: "already-completed", record: copyProcessingRecord(record) });
      }

      if (record?.state === "claimed" && record.lease !== undefined && !platformLeaseExpired(record.lease, input.acquiredAt)) {
        return success({ disposition: "lease-active", record: copyProcessingRecord(record) });
      }

      const lease = nextPlatformPersistenceLease({
        owner: input.owner,
        ...(record?.lease === undefined ? {} : { priorLease: record.lease }),
        priorAttempt: record?.attempt ?? initialPlatformPersistenceAttempt,
        acquiredAt: input.acquiredAt,
        durationMs: input.leaseDurationMs,
      });
      if (!lease.ok) {
        return { ok: false, error: lease.error };
      }

      const claimed = platformProcessingRecord({
        outboxEntryId: input.outboxEntryId,
        state: "claimed",
        attempt: lease.value.attempt,
        lease: lease.value,
      });
      records.set(input.outboxEntryId, claimed);
      return success({ disposition: "claimed", record: copyProcessingRecord(claimed) });
    },

    async complete(input) {
      const record = records.get(input.outboxEntryId);
      if (record === undefined) {
        return failure(
          "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
          "Processing must be claimed before it can complete.",
          "platform.persistence.processing.not_claimed",
        );
      }

      if (record.state === "completed") {
        return success({ disposition: "already-completed", record: copyProcessingRecord(record) });
      }

      if (record.state !== "claimed" || record.lease === undefined) {
        return failure(
          "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
          "Processing must have an active claim before it can complete.",
          "platform.persistence.processing.not_claimed",
        );
      }

      if (record.lease.fence !== input.fence) {
        return failure(
          "PLATFORM_PERSISTENCE_STALE_FENCE",
          "Processing completion used a stale fence.",
          "platform.persistence.processing.stale_fence",
        );
      }

      if (platformLeaseExpired(record.lease, input.completedAt)) {
        return failure(
          "PLATFORM_PERSISTENCE_LEASE_EXPIRED",
          "Processing completion used an expired lease.",
          "platform.persistence.processing.lease.expired",
        );
      }

      const completed = platformProcessingRecord({
        outboxEntryId: record.outboxEntryId,
        state: "completed",
        attempt: record.attempt,
        completion: { outcome: input.outcome, completedAt: input.completedAt },
      });
      records.set(input.outboxEntryId, completed);
      return success({ disposition: "completed", record: copyProcessingRecord(completed) });
    },

    async release(input) {
      const record = records.get(input.outboxEntryId);
      if (record === undefined || record.state !== "claimed" || record.lease === undefined) {
        return failure(
          "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
          "Processing must have an active claim before it can be released.",
          "platform.persistence.processing.not_claimed",
        );
      }

      if (record.lease.fence !== input.fence) {
        return failure(
          "PLATFORM_PERSISTENCE_STALE_FENCE",
          "Processing release used a stale fence.",
          "platform.persistence.processing.stale_fence",
        );
      }

      if (platformLeaseExpired(record.lease, input.releasedAt)) {
        return failure(
          "PLATFORM_PERSISTENCE_LEASE_EXPIRED",
          "Processing release used an expired lease.",
          "platform.persistence.processing.lease.expired",
        );
      }

      const released = platformProcessingRecord({
        outboxEntryId: record.outboxEntryId,
        state: "retry-eligible",
        attempt: record.attempt,
        lease: record.lease,
        releasedAt: input.releasedAt,
      });
      records.set(input.outboxEntryId, released);
      return success(copyProcessingRecord(released));
    },
  };
}

function copyProcessingRecord(record: PlatformProcessingRecord): PlatformProcessingRecord {
  return platformProcessingRecord(record);
}

function success<TValue>(value: TValue): Result<TValue, PlatformPersistenceError> {
  return { ok: true, value };
}

function failure(
  code: PlatformPersistenceError["code"],
  defaultMessage: string,
  key: string,
): Result<never, PlatformPersistenceError> {
  return {
    ok: false,
    error: platformPersistenceError({ code, defaultMessage, messageKey: key }),
  };
}
