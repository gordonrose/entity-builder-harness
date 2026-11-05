import type { OutboxEntryId } from "@kanbien/core/persistence";
import type { Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformOutboxRecord, type PlatformOutboxStore, type PlatformPersistenceError, type PlatformPersistenceDiagnosticOptions, type PersistenceLocalRejectionDetail } from "@kanbien/platform-persistence";
import type { PostgreSqlConnectionPool, PostgreSqlQueryClient } from "./connection";
import type { PostgreSqlPersistenceConfiguration } from "./configuration/index";
import { isPostgreSqlUniqueViolation, postgreSqlPersistenceOperationError } from "./errors";
import { outboxInsertStatement, outboxRecordFromRow, relation, type PostgreSqlOutboxRow } from "./records";
import { localRejection, observeBoundary, storedObservation, type StoredObservation } from "./observations";

export interface PostgreSqlPlatformOutboxStoreOptions extends PlatformPersistenceDiagnosticOptions {
  readonly configuration: PostgreSqlPersistenceConfiguration;
  readonly pool: PostgreSqlConnectionPool;
}

export function createPostgreSqlPlatformOutboxStore(
  options: PostgreSqlPlatformOutboxStoreOptions,
): PlatformOutboxStore {
  const table = relation(options.configuration.schema, "platform_outbox", options);
  return {
    create: async (entry) => {
      const observed = storedObservation(options, "create_outbox", "returned", "unknown");
      try {
        const statement = outboxInsertStatement(options.configuration.schema, entry);
        const created = await options.pool.query<PostgreSqlOutboxRow>({
          ...statement,
          text: `${statement.text} RETURNING *`,
        });
        const record = created.rows[0] === undefined ? (observed.issue("row", "absent"), undefined) : outboxRecordFromRow(created.rows[0], observed);
        return record === undefined
          ? invalidStoredOutbox(observed)
          : { ok: true, value: record };
      } catch (cause) {
        if (isPostgreSqlUniqueViolation(cause)) return duplicateOutbox(options);
        return { ok: false, error: postgreSqlPersistenceOperationError("create_outbox", cause, options, observed.thrownEvidence().diagnosticRecord) };
      } finally { observed.flush(); }
    },
    get: async (id) => {
      const observed = storedObservation(options, "read_outbox", "null", "not-assessed");
      try {
        return await findOutbox(options.pool, table, id, observed, false);
      } catch (cause) {
        throw postgreSqlPersistenceOperationError("read_outbox", cause, options, observed.thrownEvidence().diagnosticRecord);
      } finally { observed.flush(); }
    },
    listDeliverable: async (input) => {
      if (!Number.isInteger(input.limit)) return invalidLimit(options, "not-integer");
      if (input.limit <= 0) return invalidLimit(options, "not-positive");
      if (input.limit > 100) return invalidLimit(options, "too-large");
      const observed = storedObservation(options, "list_outbox", "returned", "not-assessed");
      try {
        const rows = await options.pool.query<PostgreSqlOutboxRow>({
          text: `SELECT * FROM ${table} WHERE state = 'pending' OR (state = 'leased' AND lease_expires_at <= $1) ORDER BY created_at ASC, id ASC LIMIT $2`,
          values: [input.asOf, input.limit],
        });
        const records = rows.rows.map((row, ordinal) => outboxRecordFromRow(row, observed, ordinal));
        if (records.some((record) => record === undefined)) return invalidStoredOutbox(observed);
        return { ok: true, value: records as PlatformOutboxRecord[] };
      } catch (cause) {
        return { ok: false, error: postgreSqlPersistenceOperationError("list_outbox", cause, options, observed.thrownEvidence().diagnosticRecord) };
      } finally { observed.flush(); }
    },
    claim: async (input) => {
      let expiresAt: string;
      try { expiresAt = new Date(Date.parse(input.acquiredAt) + input.leaseDurationMs).toISOString(); }
      catch (cause) { observeBoundary(options, { operation: "claim_outbox", boundary: "expiry-normalization", phase: "invocation", condition: "threw", effect: "not-started" }, cause); throw cause; }
      if (!Number.isInteger(input.leaseDurationMs)) return invalidLease(options, "duration", "not-integer");
      if (input.leaseDurationMs <= 0) return invalidLease(options, "duration", "not-positive");
      if (Number.isNaN(Date.parse(input.acquiredAt))) return invalidLease(options, "expiry", "pattern");
      const observed = storedObservation(options, "claim_outbox", "reconciled-state", "unknown");
      try {
        const claimed = await options.pool.query<PostgreSqlOutboxRow>({
          text: `UPDATE ${table} SET state = 'leased', attempt = attempt + 1, lease_owner = $2, lease_fence = COALESCE(lease_fence, 0) + 1, lease_acquired_at = $3, lease_expires_at = $4, published_at = NULL WHERE id = $1 AND (state = 'pending' OR (state = 'leased' AND lease_expires_at <= $3)) RETURNING *`,
          values: [String(input.id), String(input.owner), input.acquiredAt, expiresAt],
        });
        const updated = claimed.rows[0] === undefined ? undefined : outboxRecordFromRow(claimed.rows[0], observed);
        if (updated !== undefined) return { ok: true, value: { disposition: "claimed", record: updated } };
        const current = await findOutbox(options.pool, table, input.id, observed, false);
        if (current === null) return missingOutbox(options, "claim_outbox");
        if (current.state === "published") return { ok: true, value: { disposition: "already-published", record: current } };
        return { ok: true, value: { disposition: "lease-active", record: current } };
      } catch (cause) {
        return { ok: false, error: postgreSqlPersistenceOperationError("claim_outbox", cause, options, observed.thrownEvidence().diagnosticRecord) };
      } finally { observed.flush(); }
    },
    markPublished: async (input) => {
      const observed = storedObservation(options, "publish_outbox", "reconciled-state", "unknown");
      try {
        const published = await options.pool.query<PostgreSqlOutboxRow>({
          text: `UPDATE ${table} SET state = 'published', published_at = $3, lease_owner = NULL, lease_fence = NULL, lease_acquired_at = NULL, lease_expires_at = NULL WHERE id = $1 AND state = 'leased' AND lease_fence = $2 AND lease_expires_at > $3 RETURNING *`,
          values: [String(input.id), Number(input.fence), input.publishedAt],
        });
        const updated = published.rows[0] === undefined ? undefined : outboxRecordFromRow(published.rows[0], observed);
        if (updated !== undefined) return { ok: true, value: updated };
        const current = await findOutbox(options.pool, table, input.id, observed, false);
        if (current === null) return missingOutbox(options, "publish_outbox");
        if (current.state === "published") return { ok: true, value: current };
        if (current.lease?.fence !== input.fence) return staleFence(options);
        if (current.lease === undefined) return notLeased(options);
        return leaseExpired(options);
      } catch (cause) {
        return { ok: false, error: postgreSqlPersistenceOperationError("publish_outbox", cause, options, observed.thrownEvidence().diagnosticRecord) };
      } finally { observed.flush(); }
    },
  };
}

async function findOutbox(pool: PostgreSqlQueryClient, table: string, id: OutboxEntryId, observed: StoredObservation, flush = true): Promise<PlatformOutboxRecord | null> {
  try {
  const rows = await pool.query<PostgreSqlOutboxRow>({ text: `SELECT * FROM ${table} WHERE id = $1`, values: [String(id)] });
  const row = rows.rows[0];
  return row === undefined ? null : outboxRecordFromRow(row, observed) ?? null;
  } finally { if (flush) observed.flush(); }
}

function duplicateOutbox(options: PostgreSqlPlatformOutboxStoreOptions) { return failure(options, "PLATFORM_PERSISTENCE_DUPLICATE_OUTBOX_ENTRY", "Outbox entry already exists.", "platform.persistence.outbox.duplicate", "create_outbox", "record", "duplicate"); }
function missingOutbox(options: PostgreSqlPlatformOutboxStoreOptions, operation: "claim_outbox" | "publish_outbox") { return failure(options, "PLATFORM_PERSISTENCE_OUTBOX_NOT_FOUND", "Outbox entry was not found.", "platform.persistence.outbox.not_found", operation, "record", "not-found"); }
function invalidLimit(options: PostgreSqlPlatformOutboxStoreOptions, condition: PersistenceLocalRejectionDetail["condition"]) { return failure(options, "PLATFORM_PERSISTENCE_INVALID_LIMIT", "Outbox delivery limit must be an integer between 1 and 100.", "platform.persistence.outbox.limit.invalid", "list_outbox", "limit", condition, true); }
function invalidLease(options: PostgreSqlPlatformOutboxStoreOptions, field: "duration" | "expiry", condition: PersistenceLocalRejectionDetail["condition"]) { return failure(options, "PLATFORM_PERSISTENCE_INVALID_LEASE", "Outbox lease duration and acquisition time must be valid.", "platform.persistence.outbox.lease.invalid", "claim_outbox", field, condition, true); }
function invalidStoredOutbox(observed: StoredObservation): Result<never, PlatformPersistenceError> { return { ok: false, error: platformPersistenceError({ code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: "Stored outbox state is invalid.", messageKey: "platform.persistence.outbox.stored.invalid", ...observed.evidence() }) }; }
function notLeased(options: PostgreSqlPlatformOutboxStoreOptions) { return failure(options, "PLATFORM_PERSISTENCE_OUTBOX_NOT_LEASED", "Outbox entry must be leased before it can be published.", "platform.persistence.outbox.not_leased", "publish_outbox", "lease", "absent"); }
function staleFence(options: PostgreSqlPlatformOutboxStoreOptions) { return failure(options, "PLATFORM_PERSISTENCE_STALE_FENCE", "Outbox publish used a stale fence.", "platform.persistence.outbox.stale_fence", "publish_outbox", "fence", "stale"); }
function leaseExpired(options: PostgreSqlPlatformOutboxStoreOptions): Result<never, PlatformPersistenceError> { return { ok: false, error: platformPersistenceError({ code: "PLATFORM_PERSISTENCE_LEASE_EXPIRED", defaultMessage: "Outbox publish used an expired lease.", messageKey: "platform.persistence.outbox.lease.expired",
  ...observeBoundary(options, { operation: "publish_outbox", phase: "returned-result", boundary: "reconciliation", condition: "returned-failure", effect: "unknown", reconciliation: "lease-present-fence-matched" }) }) }; }
function failure(options: PostgreSqlPlatformOutboxStoreOptions, code: PlatformPersistenceError["code"], defaultMessage: string, messageKey: string,
  operation: PersistenceLocalRejectionDetail["operation"], field: PersistenceLocalRejectionDetail["field"], condition: PersistenceLocalRejectionDetail["condition"], preflight = false): Result<never, PlatformPersistenceError> {
  return { ok: false, error: platformPersistenceError({ code, defaultMessage, messageKey,
    ...localRejection(options, { operation, field, condition, phase: preflight ? "validation" : "state-check", effect: preflight ? "not-started" : operation === "list_outbox" ? "not-assessed" : "unknown" }) }) };
}
