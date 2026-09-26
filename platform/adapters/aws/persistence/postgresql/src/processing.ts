import type { OutboxEntryId } from "@kanbien/core/persistence";
import type { Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError, type PlatformProcessingRecord, type PlatformProcessingStore } from "@kanbien/platform-persistence";
import type { PostgreSqlConnectionPool, PostgreSqlQueryClient } from "./connection";
import type { PostgreSqlPersistenceConfiguration } from "./config";
import { postgreSqlPersistenceOperationError } from "./errors";
import { processingRecordFromRow, relation, type PostgreSqlProcessingRow } from "./records";

export interface PostgreSqlPlatformProcessingStoreOptions { readonly configuration: PostgreSqlPersistenceConfiguration; readonly pool: PostgreSqlConnectionPool; }

export function createPostgreSqlPlatformProcessingStore(options: PostgreSqlPlatformProcessingStoreOptions): PlatformProcessingStore {
  const table = relation(options.configuration.schema, "platform_processing");
  return {
    get: async (id) => {
      try {
        return await findProcessing(options.pool, table, id);
      } catch (cause) {
        throw postgreSqlPersistenceOperationError("read_processing", cause);
      }
    },
    claim: async (input) => {
      if (!Number.isInteger(input.leaseDurationMs) || input.leaseDurationMs <= 0 || Number.isNaN(Date.parse(input.acquiredAt))) return invalidLease();
      const expiresAt = new Date(Date.parse(input.acquiredAt) + input.leaseDurationMs).toISOString();
      try {
        const updated = await options.pool.query<PostgreSqlProcessingRow>({
          text: `INSERT INTO ${table} (outbox_entry_id, state, attempt, lease_owner, lease_fence, lease_acquired_at, lease_expires_at) VALUES ($1, 'claimed', 1, $2, 1, $3, $4) ON CONFLICT (outbox_entry_id) DO UPDATE SET state = 'claimed', attempt = ${table}.attempt + 1, lease_owner = EXCLUDED.lease_owner, lease_fence = ${table}.lease_fence + 1, lease_acquired_at = EXCLUDED.lease_acquired_at, lease_expires_at = EXCLUDED.lease_expires_at, released_at = NULL WHERE ${table}.state <> 'completed' AND (${table}.state = 'retry-eligible' OR ${table}.lease_expires_at <= EXCLUDED.lease_acquired_at) RETURNING *`,
          values: [String(input.outboxEntryId), String(input.owner), input.acquiredAt, expiresAt],
        });
        const record = updated.rows[0] === undefined ? undefined : processingRecordFromRow(updated.rows[0]);
        if (record !== undefined) return { ok: true, value: { disposition: "claimed", record } };
        const current = await findProcessing(options.pool, table, input.outboxEntryId);
        if (current?.state === "completed") return { ok: true, value: { disposition: "already-completed", record: current } };
        if (current !== null) return { ok: true, value: { disposition: "lease-active", record: current } };
        return invalidStoredProcessing();
      } catch (cause) { return { ok: false, error: postgreSqlPersistenceOperationError("claim_processing", cause) }; }
    },
    complete: async (input) => {
      try {
        const updated = await options.pool.query<PostgreSqlProcessingRow>({
          text: `UPDATE ${table} SET state = 'completed', completion_outcome = $3, completed_at = $4, lease_owner = NULL, lease_fence = NULL, lease_acquired_at = NULL, lease_expires_at = NULL WHERE outbox_entry_id = $1 AND state = 'claimed' AND lease_fence = $2 AND lease_expires_at > $4 RETURNING *`,
          values: [String(input.outboxEntryId), Number(input.fence), input.outcome, input.completedAt],
        });
        const record = updated.rows[0] === undefined ? undefined : processingRecordFromRow(updated.rows[0]);
        if (record !== undefined) return { ok: true, value: { disposition: "completed", record } };
        const current = await findProcessing(options.pool, table, input.outboxEntryId);
        if (current?.state === "completed") return { ok: true, value: { disposition: "already-completed", record: current } };
        if (current === null || current.state !== "claimed" || current.lease === undefined) return notClaimed();
        if (current.lease.fence !== input.fence) return staleFence();
        return leaseExpired();
      } catch (cause) { return { ok: false, error: postgreSqlPersistenceOperationError("complete_processing", cause) }; }
    },
    release: async (input) => {
      try {
        const updated = await options.pool.query<PostgreSqlProcessingRow>({
          text: `UPDATE ${table} SET state = 'retry-eligible', released_at = $3 WHERE outbox_entry_id = $1 AND state = 'claimed' AND lease_fence = $2 AND lease_expires_at > $3 RETURNING *`,
          values: [String(input.outboxEntryId), Number(input.fence), input.releasedAt],
        });
        const record = updated.rows[0] === undefined ? undefined : processingRecordFromRow(updated.rows[0]);
        if (record !== undefined) return { ok: true, value: record };
        const current = await findProcessing(options.pool, table, input.outboxEntryId);
        if (current === null || current.state !== "claimed" || current.lease === undefined) return notClaimed();
        if (current.lease.fence !== input.fence) return staleFence();
        return leaseExpired();
      } catch (cause) { return { ok: false, error: postgreSqlPersistenceOperationError("release_processing", cause) }; }
    },
  };
}

async function findProcessing(pool: PostgreSqlQueryClient, table: string, id: OutboxEntryId): Promise<PlatformProcessingRecord | null> {
  const result = await pool.query<PostgreSqlProcessingRow>({ text: `SELECT * FROM ${table} WHERE outbox_entry_id = $1`, values: [String(id)] });
  return result.rows[0] === undefined ? null : processingRecordFromRow(result.rows[0]) ?? null;
}
function invalidLease(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_INVALID_LEASE", "Processing lease duration and acquisition time must be valid.", "platform.persistence.processing.lease.invalid"); }
function invalidStoredProcessing(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", "Stored processing state is invalid.", "platform.persistence.processing.stored.invalid"); }
function notClaimed(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED", "Processing must have an active claim before this operation.", "platform.persistence.processing.not_claimed"); }
function staleFence(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_STALE_FENCE", "Processing operation used a stale fence.", "platform.persistence.processing.stale_fence"); }
function leaseExpired(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_LEASE_EXPIRED", "Processing operation used an expired lease.", "platform.persistence.processing.lease.expired"); }
function failure(code: PlatformPersistenceError["code"], defaultMessage: string, messageKey: string): Result<never, PlatformPersistenceError> { return { ok: false, error: platformPersistenceError({ code, defaultMessage, messageKey }) }; }
