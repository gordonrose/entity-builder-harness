import type { OutboxEntryId } from "@kanbien/core/persistence";
import type { Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError, type PlatformProcessingRecord, type PlatformProcessingStore, type PlatformPersistenceDiagnosticOptions, type PersistenceLocalRejectionDetail } from "@kanbien/platform-persistence";
import type { PostgreSqlConnectionPool, PostgreSqlQueryClient } from "./connection";
import type { PostgreSqlPersistenceConfiguration } from "./configuration/index";
import { postgreSqlPersistenceOperationError } from "./errors";
import { processingRecordFromRow, relation, type PostgreSqlProcessingRow } from "./records";
import { localRejection, observeBoundary, storedObservation, type StoredObservation } from "./observations";

export interface PostgreSqlPlatformProcessingStoreOptions extends PlatformPersistenceDiagnosticOptions { readonly configuration: PostgreSqlPersistenceConfiguration; readonly pool: PostgreSqlConnectionPool; }

export function createPostgreSqlPlatformProcessingStore(options: PostgreSqlPlatformProcessingStoreOptions): PlatformProcessingStore {
  const table = relation(options.configuration.schema, "platform_processing", options);
  return {
    get: async (id) => {
      const observed = storedObservation(options, "read_processing", "null", "not-assessed");
      try {
        return await findProcessing(options.pool, table, id, observed, false);
      } catch (cause) {
        throw postgreSqlPersistenceOperationError("read_processing", cause, options, observed.thrownEvidence().diagnosticRecord);
      } finally { observed.flush(); }
    },
    claim: async (input) => {
      if (!Number.isInteger(input.leaseDurationMs)) return invalidLease(options, "duration", "not-integer");
      if (input.leaseDurationMs <= 0) return invalidLease(options, "duration", "not-positive");
      if (Number.isNaN(Date.parse(input.acquiredAt))) return invalidLease(options, "expiry", "pattern");
      let expiresAt: string;
      try { expiresAt = new Date(Date.parse(input.acquiredAt) + input.leaseDurationMs).toISOString(); }
      catch (cause) { observeBoundary(options, { operation: "claim_processing", boundary: "expiry-normalization", phase: "invocation", condition: "threw", effect: "not-started" }, cause); throw cause; }
      const observed = storedObservation(options, "claim_processing", "reconciled-state", "unknown");
      try {
        const updated = await options.pool.query<PostgreSqlProcessingRow>({
          text: `INSERT INTO ${table} (outbox_entry_id, state, attempt, lease_owner, lease_fence, lease_acquired_at, lease_expires_at) VALUES ($1, 'claimed', 1, $2, 1, $3, $4) ON CONFLICT (outbox_entry_id) DO UPDATE SET state = 'claimed', attempt = ${table}.attempt + 1, lease_owner = EXCLUDED.lease_owner, lease_fence = ${table}.lease_fence + 1, lease_acquired_at = EXCLUDED.lease_acquired_at, lease_expires_at = EXCLUDED.lease_expires_at, released_at = NULL WHERE ${table}.state <> 'completed' AND (${table}.state = 'retry-eligible' OR ${table}.lease_expires_at <= EXCLUDED.lease_acquired_at) RETURNING *`,
          values: [String(input.outboxEntryId), String(input.owner), input.acquiredAt, expiresAt],
        });
        const record = updated.rows[0] === undefined ? undefined : processingRecordFromRow(updated.rows[0], observed);
        if (record !== undefined) return { ok: true, value: { disposition: "claimed", record } };
        const current = await findProcessing(options.pool, table, input.outboxEntryId, observed, false);
        if (current?.state === "completed") return { ok: true, value: { disposition: "already-completed", record: current } };
        if (current !== null) return { ok: true, value: { disposition: "lease-active", record: current } };
        observed.issue("row", "absent");
        return invalidStoredProcessing(observed);
      } catch (cause) { return { ok: false, error: postgreSqlPersistenceOperationError("claim_processing", cause, options, observed.thrownEvidence().diagnosticRecord) }; }
      finally { observed.flush(); }
    },
    complete: async (input) => {
      const observed = storedObservation(options, "complete_processing", "reconciled-state", "unknown");
      try {
        const updated = await options.pool.query<PostgreSqlProcessingRow>({
          text: `UPDATE ${table} SET state = 'completed', completion_outcome = $3, completed_at = $4, lease_owner = NULL, lease_fence = NULL, lease_acquired_at = NULL, lease_expires_at = NULL WHERE outbox_entry_id = $1 AND state = 'claimed' AND lease_fence = $2 AND lease_expires_at > $4 RETURNING *`,
          values: [String(input.outboxEntryId), Number(input.fence), input.outcome, input.completedAt],
        });
        const record = updated.rows[0] === undefined ? undefined : processingRecordFromRow(updated.rows[0], observed);
        if (record !== undefined) return { ok: true, value: { disposition: "completed", record } };
        const current = await findProcessing(options.pool, table, input.outboxEntryId, observed, false);
        if (current?.state === "completed") return { ok: true, value: { disposition: "already-completed", record: current } };
        if (current === null) return notClaimed(options, "complete_processing", "record", "not-found");
        if (current.state !== "claimed") return notClaimed(options, "complete_processing", "state", "wrong-state");
        if (current.lease === undefined) return notClaimed(options, "complete_processing", "lease", "absent");
        if (current.lease.fence !== input.fence) return staleFence(options, "complete_processing");
        return leaseExpired(options, "complete_processing");
      } catch (cause) { return { ok: false, error: postgreSqlPersistenceOperationError("complete_processing", cause, options, observed.thrownEvidence().diagnosticRecord) }; }
      finally { observed.flush(); }
    },
    release: async (input) => {
      const observed = storedObservation(options, "release_processing", "reconciled-state", "unknown");
      try {
        const updated = await options.pool.query<PostgreSqlProcessingRow>({
          text: `UPDATE ${table} SET state = 'retry-eligible', released_at = $3 WHERE outbox_entry_id = $1 AND state = 'claimed' AND lease_fence = $2 AND lease_expires_at > $3 RETURNING *`,
          values: [String(input.outboxEntryId), Number(input.fence), input.releasedAt],
        });
        const record = updated.rows[0] === undefined ? undefined : processingRecordFromRow(updated.rows[0], observed);
        if (record !== undefined) return { ok: true, value: record };
        const current = await findProcessing(options.pool, table, input.outboxEntryId, observed, false);
        if (current === null) return notClaimed(options, "release_processing", "record", "not-found");
        if (current.state !== "claimed") return notClaimed(options, "release_processing", "state", "wrong-state");
        if (current.lease === undefined) return notClaimed(options, "release_processing", "lease", "absent");
        if (current.lease.fence !== input.fence) return staleFence(options, "release_processing");
        return leaseExpired(options, "release_processing");
      } catch (cause) { return { ok: false, error: postgreSqlPersistenceOperationError("release_processing", cause, options, observed.thrownEvidence().diagnosticRecord) }; }
      finally { observed.flush(); }
    },
  };
}

async function findProcessing(pool: PostgreSqlQueryClient, table: string, id: OutboxEntryId, observed: StoredObservation, flush = true): Promise<PlatformProcessingRecord | null> {
  try {
  const result = await pool.query<PostgreSqlProcessingRow>({ text: `SELECT * FROM ${table} WHERE outbox_entry_id = $1`, values: [String(id)] });
  return result.rows[0] === undefined ? null : processingRecordFromRow(result.rows[0], observed) ?? null;
  } finally { if (flush) observed.flush(); }
}
function invalidLease(options: PostgreSqlPlatformProcessingStoreOptions, field: "duration" | "expiry", condition: PersistenceLocalRejectionDetail["condition"]) { return failure(options, "PLATFORM_PERSISTENCE_INVALID_LEASE", "Processing lease duration and acquisition time must be valid.", "platform.persistence.processing.lease.invalid", "claim_processing", field, condition, true); }
function invalidStoredProcessing(observed: StoredObservation): Result<never, PlatformPersistenceError> { return { ok: false, error: platformPersistenceError({ code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: "Stored processing state is invalid.", messageKey: "platform.persistence.processing.stored.invalid", ...observed.evidence() }) }; }
function notClaimed(options: PostgreSqlPlatformProcessingStoreOptions, operation: "complete_processing" | "release_processing", field: "record" | "state" | "lease", condition: PersistenceLocalRejectionDetail["condition"]) { return failure(options, "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED", "Processing must have an active claim before this operation.", "platform.persistence.processing.not_claimed", operation, field, condition); }
function staleFence(options: PostgreSqlPlatformProcessingStoreOptions, operation: "complete_processing" | "release_processing") { return failure(options, "PLATFORM_PERSISTENCE_STALE_FENCE", "Processing operation used a stale fence.", "platform.persistence.processing.stale_fence", operation, "fence", "stale"); }
function leaseExpired(options: PostgreSqlPlatformProcessingStoreOptions, operation: "complete_processing" | "release_processing"): Result<never, PlatformPersistenceError> { return { ok: false, error: platformPersistenceError({ code: "PLATFORM_PERSISTENCE_LEASE_EXPIRED", defaultMessage: "Processing operation used an expired lease.", messageKey: "platform.persistence.processing.lease.expired",
  ...observeBoundary(options, { operation, phase: "returned-result", boundary: "reconciliation", condition: "returned-failure", effect: "unknown", reconciliation: "lease-present-fence-matched" }) }) }; }
function failure(options: PostgreSqlPlatformProcessingStoreOptions, code: PlatformPersistenceError["code"], defaultMessage: string, messageKey: string,
  operation: PersistenceLocalRejectionDetail["operation"], field: PersistenceLocalRejectionDetail["field"], condition: PersistenceLocalRejectionDetail["condition"], preflight = false): Result<never, PlatformPersistenceError> {
  return { ok: false, error: platformPersistenceError({ code, defaultMessage, messageKey,
    ...localRejection(options, { operation, field, condition, phase: preflight ? "validation" : "state-check", effect: preflight ? "not-started" : "unknown" }) }) };
}
