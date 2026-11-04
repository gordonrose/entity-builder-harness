import type { OutboxEntryId } from "@kanbien/core/persistence";
import type { ISODateTime, Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError } from "./errors";
import { observePlatformPersistenceDiagnostic, persistenceLocalRejectionDiagnosticRecord, type PersistenceLocalRejectionDetail, type PlatformPersistenceDiagnosticOptions } from "./diagnostics";
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

export function createInMemoryPlatformProcessingStore(options: PlatformPersistenceDiagnosticOptions = {}): PlatformProcessingStore {
  const records = new Map<OutboxEntryId, PlatformProcessingRecord>();
  const reject = (code: PlatformPersistenceError["code"], message: string, key: string,
    operation: PersistenceLocalRejectionDetail["operation"], field: PersistenceLocalRejectionDetail["field"], condition: PersistenceLocalRejectionDetail["condition"]) =>
    failure(code, message, key, { operation, field, condition, phase: "state-check", effect: "local-state-unchanged" }, options);

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
        if (lease.error.diagnosticRecord !== undefined) observePlatformPersistenceDiagnostic(options, lease.error.diagnosticRecord,
          { relatedDiagnosticRecords: lease.error.relatedDiagnosticRecords });
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
        return reject(
          "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
          "Processing must be claimed before it can complete.",
          "platform.persistence.processing.not_claimed",
          "complete_processing", "record", "not-found",
        );
      }

      if (record.state === "completed") {
        return success({ disposition: "already-completed", record: copyProcessingRecord(record) });
      }

      if (record.state !== "claimed" || record.lease === undefined) {
        return reject(
          "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
          "Processing must have an active claim before it can complete.",
          "platform.persistence.processing.not_claimed",
          "complete_processing", record.state !== "claimed" ? "state" : "lease", record.state !== "claimed" ? "wrong-state" : "absent",
        );
      }

      if (record.lease.fence !== input.fence) {
        return reject(
          "PLATFORM_PERSISTENCE_STALE_FENCE",
          "Processing completion used a stale fence.",
          "platform.persistence.processing.stale_fence",
          "complete_processing", "fence", "stale",
        );
      }

      if (platformLeaseExpired(record.lease, input.completedAt)) {
        return reject(
          "PLATFORM_PERSISTENCE_LEASE_EXPIRED",
          "Processing completion used an expired lease.",
          "platform.persistence.processing.lease.expired",
          "complete_processing", "lease", "expired",
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
        return reject(
          "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
          "Processing must have an active claim before it can be released.",
          "platform.persistence.processing.not_claimed",
          "release_processing", record === undefined ? "record" : record.state !== "claimed" ? "state" : "lease",
          record === undefined ? "not-found" : record.state !== "claimed" ? "wrong-state" : "absent",
        );
      }

      if (record.lease.fence !== input.fence) {
        return reject(
          "PLATFORM_PERSISTENCE_STALE_FENCE",
          "Processing release used a stale fence.",
          "platform.persistence.processing.stale_fence",
          "release_processing", "fence", "stale",
        );
      }

      if (platformLeaseExpired(record.lease, input.releasedAt)) {
        return reject(
          "PLATFORM_PERSISTENCE_LEASE_EXPIRED",
          "Processing release used an expired lease.",
          "platform.persistence.processing.lease.expired",
          "release_processing", "lease", "expired",
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
  detail: PersistenceLocalRejectionDetail,
  options: PlatformPersistenceDiagnosticOptions,
): Result<never, PlatformPersistenceError> {
  const diagnosticRecord = persistenceLocalRejectionDiagnosticRecord(detail);
  observePlatformPersistenceDiagnostic(options, diagnosticRecord);
  return {
    ok: false,
    error: platformPersistenceError({ code, defaultMessage, messageKey: key, diagnosticRecord }),
  };
}
