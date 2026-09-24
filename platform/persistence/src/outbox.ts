import type { OutboxEntry, OutboxEntryId } from "@kanbien/core/persistence";
import type { ISODateTime, Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError } from "./errors";
import {
  nextPlatformPersistenceLease,
  platformLeaseExpired,
  platformOutboxRecord,
  type PlatformOutboxRecord,
  type PlatformPersistenceFence,
  type PlatformPersistenceLeaseOwner,
} from "./types";

export type PlatformOutboxClaimResult =
  | { readonly disposition: "claimed"; readonly record: PlatformOutboxRecord }
  | { readonly disposition: "lease-active"; readonly record: PlatformOutboxRecord }
  | { readonly disposition: "already-published"; readonly record: PlatformOutboxRecord };

export interface PlatformOutboxStore {
  create(entry: OutboxEntry): Promise<Result<PlatformOutboxRecord, PlatformPersistenceError>>;
  get(id: OutboxEntryId): Promise<PlatformOutboxRecord | null>;
  listDeliverable(input: {
    readonly asOf: ISODateTime;
    readonly limit: number;
  }): Promise<Result<readonly PlatformOutboxRecord[], PlatformPersistenceError>>;
  claim(input: {
    readonly id: OutboxEntryId;
    readonly owner: PlatformPersistenceLeaseOwner;
    readonly acquiredAt: ISODateTime;
    readonly leaseDurationMs: number;
  }): Promise<Result<PlatformOutboxClaimResult, PlatformPersistenceError>>;
  markPublished(input: {
    readonly id: OutboxEntryId;
    readonly fence: PlatformPersistenceFence;
    readonly publishedAt: ISODateTime;
  }): Promise<Result<PlatformOutboxRecord, PlatformPersistenceError>>;
}

export function createInMemoryPlatformOutboxStore(): PlatformOutboxStore {
  const records = new Map<OutboxEntryId, PlatformOutboxRecord>();

  return {
    async create(entry) {
      if (records.has(entry.id)) {
        return failure(
          "PLATFORM_PERSISTENCE_DUPLICATE_OUTBOX_ENTRY",
          "Outbox entry already exists.",
          "platform.persistence.outbox.duplicate",
        );
      }

      const record = platformOutboxRecord({ entry });
      records.set(entry.id, record);
      return success(copyOutboxRecord(record));
    },

    async get(id) {
      const record = records.get(id);
      return record === undefined ? null : copyOutboxRecord(record);
    },

    async listDeliverable(input) {
      if (!Number.isInteger(input.limit) || input.limit <= 0) {
        return failure(
          "PLATFORM_PERSISTENCE_INVALID_LIMIT",
          "Outbox delivery limit must be a positive integer.",
          "platform.persistence.outbox.limit.invalid",
        );
      }

      const deliverable = [...records.values()]
        .filter((record) => record.state === "pending" || (record.lease !== undefined && platformLeaseExpired(record.lease, input.asOf)))
        .sort((left, right) => Date.parse(left.entry.createdAt) - Date.parse(right.entry.createdAt))
        .slice(0, input.limit)
        .map(copyOutboxRecord);

      return success(deliverable);
    },

    async claim(input) {
      const record = records.get(input.id);
      if (record === undefined) {
        return failure(
          "PLATFORM_PERSISTENCE_OUTBOX_NOT_FOUND",
          "Outbox entry was not found.",
          "platform.persistence.outbox.not_found",
        );
      }

      if (record.state === "published") {
        return success({ disposition: "already-published", record: copyOutboxRecord(record) });
      }

      if (record.lease !== undefined && !platformLeaseExpired(record.lease, input.acquiredAt)) {
        return success({ disposition: "lease-active", record: copyOutboxRecord(record) });
      }

      const lease = nextPlatformPersistenceLease({
        owner: input.owner,
        ...(record.lease === undefined ? {} : { priorLease: record.lease }),
        priorAttempt: record.attempt,
        acquiredAt: input.acquiredAt,
        durationMs: input.leaseDurationMs,
      });
      if (!lease.ok) {
        return { ok: false, error: lease.error };
      }

      const claimed = platformOutboxRecord({
        entry: record.entry,
        state: "leased",
        attempt: lease.value.attempt,
        lease: lease.value,
      });
      records.set(input.id, claimed);
      return success({ disposition: "claimed", record: copyOutboxRecord(claimed) });
    },

    async markPublished(input) {
      const record = records.get(input.id);
      if (record === undefined) {
        return failure(
          "PLATFORM_PERSISTENCE_OUTBOX_NOT_FOUND",
          "Outbox entry was not found.",
          "platform.persistence.outbox.not_found",
        );
      }

      if (record.state === "published") {
        return success(copyOutboxRecord(record));
      }

      if (record.state !== "leased" || record.lease === undefined) {
        return failure(
          "PLATFORM_PERSISTENCE_OUTBOX_NOT_LEASED",
          "Outbox entry must be leased before it can be published.",
          "platform.persistence.outbox.not_leased",
        );
      }

      if (record.lease.fence !== input.fence) {
        return failure(
          "PLATFORM_PERSISTENCE_STALE_FENCE",
          "Outbox publish used a stale fence.",
          "platform.persistence.outbox.stale_fence",
        );
      }

      if (platformLeaseExpired(record.lease, input.publishedAt)) {
        return failure(
          "PLATFORM_PERSISTENCE_LEASE_EXPIRED",
          "Outbox publish used an expired lease.",
          "platform.persistence.outbox.lease.expired",
        );
      }

      const published = platformOutboxRecord({
        entry: record.entry,
        state: "published",
        attempt: record.attempt,
        publishedAt: input.publishedAt,
      });
      records.set(input.id, published);
      return success(copyOutboxRecord(published));
    },
  };
}

function copyOutboxRecord(record: PlatformOutboxRecord): PlatformOutboxRecord {
  return platformOutboxRecord({
    ...record,
    entry: {
      ...record.entry,
      subject: { ...record.entry.subject },
    },
  });
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
