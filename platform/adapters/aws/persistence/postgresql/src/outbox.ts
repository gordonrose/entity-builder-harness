import type { OutboxEntryId } from "@kanbien/core/persistence";
import type { Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformOutboxRecord, type PlatformOutboxStore, type PlatformPersistenceError } from "@kanbien/platform-persistence";
import type { PostgreSqlConnectionPool, PostgreSqlQueryClient } from "./connection";
import type { PostgreSqlPersistenceConfiguration } from "./config";
import { isPostgreSqlUniqueViolation, postgreSqlPersistenceOperationError } from "./errors";
import { outboxInsertStatement, outboxRecordFromRow, relation, type PostgreSqlOutboxRow } from "./records";

export interface PostgreSqlPlatformOutboxStoreOptions {
  readonly configuration: PostgreSqlPersistenceConfiguration;
  readonly pool: PostgreSqlConnectionPool;
}

export function createPostgreSqlPlatformOutboxStore(
  options: PostgreSqlPlatformOutboxStoreOptions,
): PlatformOutboxStore {
  const table = relation(options.configuration.schema, "platform_outbox");
  return {
    create: async (entry) => {
      try {
        const statement = outboxInsertStatement(options.configuration.schema, entry);
        const created = await options.pool.query<PostgreSqlOutboxRow>({
          ...statement,
          text: `${statement.text} RETURNING *`,
        });
        const record = created.rows[0] === undefined ? undefined : outboxRecordFromRow(created.rows[0]);
        return record === undefined
          ? invalidStoredOutbox()
          : { ok: true, value: record };
      } catch (cause) {
        if (isPostgreSqlUniqueViolation(cause)) return duplicateOutbox();
        return { ok: false, error: postgreSqlPersistenceOperationError("create_outbox", cause) };
      }
    },
    get: async (id) => {
      try {
        return await findOutbox(options.pool, table, id);
      } catch (cause) {
        throw postgreSqlPersistenceOperationError("read_outbox", cause);
      }
    },
    listDeliverable: async (input) => {
      if (!Number.isInteger(input.limit) || input.limit <= 0 || input.limit > 100) return invalidLimit();
      try {
        const rows = await options.pool.query<PostgreSqlOutboxRow>({
          text: `SELECT * FROM ${table} WHERE state = 'pending' OR (state = 'leased' AND lease_expires_at <= $1) ORDER BY created_at ASC, id ASC LIMIT $2`,
          values: [input.asOf, input.limit],
        });
        const records = rows.rows.map(outboxRecordFromRow);
        if (records.some((record) => record === undefined)) return invalidStoredOutbox();
        return { ok: true, value: records as PlatformOutboxRecord[] };
      } catch (cause) {
        return { ok: false, error: postgreSqlPersistenceOperationError("list_outbox", cause) };
      }
    },
    claim: async (input) => {
      const expiresAt = new Date(Date.parse(input.acquiredAt) + input.leaseDurationMs).toISOString();
      if (!Number.isInteger(input.leaseDurationMs) || input.leaseDurationMs <= 0 || Number.isNaN(Date.parse(input.acquiredAt))) return invalidLease();
      try {
        const claimed = await options.pool.query<PostgreSqlOutboxRow>({
          text: `UPDATE ${table} SET state = 'leased', attempt = attempt + 1, lease_owner = $2, lease_fence = COALESCE(lease_fence, 0) + 1, lease_acquired_at = $3, lease_expires_at = $4, published_at = NULL WHERE id = $1 AND (state = 'pending' OR (state = 'leased' AND lease_expires_at <= $3)) RETURNING *`,
          values: [String(input.id), String(input.owner), input.acquiredAt, expiresAt],
        });
        const updated = claimed.rows[0] === undefined ? undefined : outboxRecordFromRow(claimed.rows[0]);
        if (updated !== undefined) return { ok: true, value: { disposition: "claimed", record: updated } };
        const current = await findOutbox(options.pool, table, input.id);
        if (current === null) return missingOutbox();
        if (current.state === "published") return { ok: true, value: { disposition: "already-published", record: current } };
        return { ok: true, value: { disposition: "lease-active", record: current } };
      } catch (cause) {
        return { ok: false, error: postgreSqlPersistenceOperationError("claim_outbox", cause) };
      }
    },
    markPublished: async (input) => {
      try {
        const published = await options.pool.query<PostgreSqlOutboxRow>({
          text: `UPDATE ${table} SET state = 'published', published_at = $3, lease_owner = NULL, lease_fence = NULL, lease_acquired_at = NULL, lease_expires_at = NULL WHERE id = $1 AND state = 'leased' AND lease_fence = $2 AND lease_expires_at > $3 RETURNING *`,
          values: [String(input.id), Number(input.fence), input.publishedAt],
        });
        const updated = published.rows[0] === undefined ? undefined : outboxRecordFromRow(published.rows[0]);
        if (updated !== undefined) return { ok: true, value: updated };
        const current = await findOutbox(options.pool, table, input.id);
        if (current === null) return missingOutbox();
        if (current.state === "published") return { ok: true, value: current };
        if (current.lease?.fence !== input.fence) return staleFence();
        if (current.lease === undefined) return notLeased();
        return leaseExpired();
      } catch (cause) {
        return { ok: false, error: postgreSqlPersistenceOperationError("publish_outbox", cause) };
      }
    },
  };
}

async function findOutbox(pool: PostgreSqlQueryClient, table: string, id: OutboxEntryId): Promise<PlatformOutboxRecord | null> {
  const rows = await pool.query<PostgreSqlOutboxRow>({ text: `SELECT * FROM ${table} WHERE id = $1`, values: [String(id)] });
  const row = rows.rows[0];
  return row === undefined ? null : outboxRecordFromRow(row) ?? null;
}

function duplicateOutbox(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_DUPLICATE_OUTBOX_ENTRY", "Outbox entry already exists.", "platform.persistence.outbox.duplicate"); }
function missingOutbox(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_OUTBOX_NOT_FOUND", "Outbox entry was not found.", "platform.persistence.outbox.not_found"); }
function invalidLimit(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_INVALID_LIMIT", "Outbox delivery limit must be an integer between 1 and 100.", "platform.persistence.outbox.limit.invalid"); }
function invalidLease(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_INVALID_LEASE", "Outbox lease duration and acquisition time must be valid.", "platform.persistence.outbox.lease.invalid"); }
function invalidStoredOutbox(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", "Stored outbox state is invalid.", "platform.persistence.outbox.stored.invalid"); }
function notLeased(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_OUTBOX_NOT_LEASED", "Outbox entry must be leased before it can be published.", "platform.persistence.outbox.not_leased"); }
function staleFence(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_STALE_FENCE", "Outbox publish used a stale fence.", "platform.persistence.outbox.stale_fence"); }
function leaseExpired(): Result<never, PlatformPersistenceError> { return failure("PLATFORM_PERSISTENCE_LEASE_EXPIRED", "Outbox publish used an expired lease.", "platform.persistence.outbox.lease.expired"); }
function failure(code: PlatformPersistenceError["code"], defaultMessage: string, messageKey: string): Result<never, PlatformPersistenceError> { return { ok: false, error: platformPersistenceError({ code, defaultMessage, messageKey }) }; }
