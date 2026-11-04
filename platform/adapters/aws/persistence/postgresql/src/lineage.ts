import type { RecordChange, RecordReference } from "@kanbien/core/persistence";
import type { CausationId, Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError, type PlatformRecordChangeStore, type PlatformPersistenceDiagnosticOptions } from "@kanbien/platform-persistence";
import type { PostgreSqlConnectionPool } from "./connection";
import type { PostgreSqlPersistenceConfiguration } from "./configuration/index";
import { isPostgreSqlUniqueViolation, postgreSqlPersistenceOperationError } from "./errors";
import { recordChangeFromRow, recordChangeInsertStatement, relation, type PostgreSqlLineageRow } from "./records";
import { localRejection, storedObservation, type StoredObservation } from "./observations";

export interface PostgreSqlPlatformRecordChangeStoreOptions extends PlatformPersistenceDiagnosticOptions { readonly configuration: PostgreSqlPersistenceConfiguration; readonly pool: PostgreSqlConnectionPool; }

export function createPostgreSqlPlatformRecordChangeStore(options: PostgreSqlPlatformRecordChangeStoreOptions): PlatformRecordChangeStore {
  const table = relation(options.configuration.schema, "platform_record_change", options);
  return {
    append: async (change) => {
      const observed = storedObservation(options, "append_lineage", "duplicate", "unknown");
      try {
        const statement = recordChangeInsertStatement(options.configuration.schema, change);
        const inserted = await options.pool.query<PostgreSqlLineageRow>({ ...statement, text: `${statement.text} RETURNING *` });
        const row = inserted.rows[0] === undefined ? (observed.issue("row", "absent"), undefined) : recordChangeFromRow(inserted.rows[0], observed);
        return row === undefined ? duplicateChange(options, observed) : { ok: true, value: row };
      } catch (cause) {
        if (isPostgreSqlUniqueViolation(cause)) return duplicateChange(options);
        return { ok: false, error: postgreSqlPersistenceOperationError("append_lineage", cause, options, observed.thrownEvidence().diagnosticRecord) };
      } finally { observed.flush(); }
    },
    findByRecord: async (record) => findChanges(options, { text: `SELECT * FROM ${table} WHERE record_kind = $1 AND record_id = $2 ORDER BY revision ASC`, values: [String(record.kind), String(record.id)] }),
    findByCause: async (cause) => findChanges(options, { text: `SELECT * FROM ${table} WHERE causation_id = $1 ORDER BY occurred_at ASC, id ASC`, values: [String(cause)] }),
  };
}

async function findChanges(options: PostgreSqlPlatformRecordChangeStoreOptions, statement: { readonly text: string; readonly values: readonly unknown[] }): Promise<readonly RecordChange[]> {
  const observed = storedObservation(options, "read_lineage", "filtered", "not-assessed");
  try {
    return (await options.pool.query<PostgreSqlLineageRow>(statement)).rows
      .map((row, ordinal) => recordChangeFromRow(row, observed, ordinal))
      .filter((change): change is RecordChange => change !== undefined);
  } catch (cause) {
    throw postgreSqlPersistenceOperationError("read_lineage", cause, options, observed.thrownEvidence().diagnosticRecord);
  } finally { observed.flush(); }
}
function duplicateChange(options: PostgreSqlPlatformRecordChangeStoreOptions, observed?: StoredObservation): Result<never, PlatformPersistenceError> { return { ok: false, error: platformPersistenceError({ code: "PLATFORM_PERSISTENCE_DUPLICATE_RECORD_CHANGE", defaultMessage: "Record change already exists.", messageKey: "platform.persistence.lineage.duplicate",
  ...(observed === undefined ? localRejection(options, { operation: "append_lineage", field: "record", condition: "duplicate", phase: "state-check", effect: "unknown" }) : observed.evidence()) }) }; }
