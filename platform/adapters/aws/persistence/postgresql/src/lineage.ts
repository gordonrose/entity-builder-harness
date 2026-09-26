import type { RecordChange, RecordReference } from "@kanbien/core/persistence";
import type { CausationId, Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError, type PlatformRecordChangeStore } from "@kanbien/platform-persistence";
import type { PostgreSqlConnectionPool } from "./connection";
import type { PostgreSqlPersistenceConfiguration } from "./config";
import { isPostgreSqlUniqueViolation, postgreSqlPersistenceOperationError } from "./errors";
import { recordChangeFromRow, recordChangeInsertStatement, relation, type PostgreSqlLineageRow } from "./records";

export interface PostgreSqlPlatformRecordChangeStoreOptions { readonly configuration: PostgreSqlPersistenceConfiguration; readonly pool: PostgreSqlConnectionPool; }

export function createPostgreSqlPlatformRecordChangeStore(options: PostgreSqlPlatformRecordChangeStoreOptions): PlatformRecordChangeStore {
  const table = relation(options.configuration.schema, "platform_record_change");
  return {
    append: async (change) => {
      try {
        const statement = recordChangeInsertStatement(options.configuration.schema, change);
        const inserted = await options.pool.query<PostgreSqlLineageRow>({ ...statement, text: `${statement.text} RETURNING *` });
        const row = inserted.rows[0] === undefined ? undefined : recordChangeFromRow(inserted.rows[0]);
        return row === undefined ? duplicateChange() : { ok: true, value: row };
      } catch (cause) {
        if (isPostgreSqlUniqueViolation(cause)) return duplicateChange();
        return { ok: false, error: postgreSqlPersistenceOperationError("append_lineage", cause) };
      }
    },
    findByRecord: async (record) => findChanges(options.pool, { text: `SELECT * FROM ${table} WHERE record_kind = $1 AND record_id = $2 ORDER BY revision ASC`, values: [String(record.kind), String(record.id)] }),
    findByCause: async (cause) => findChanges(options.pool, { text: `SELECT * FROM ${table} WHERE causation_id = $1 ORDER BY occurred_at ASC, id ASC`, values: [String(cause)] }),
  };
}

async function findChanges(pool: PostgreSqlConnectionPool, statement: { readonly text: string; readonly values: readonly unknown[] }): Promise<readonly RecordChange[]> {
  try {
    return (await pool.query<PostgreSqlLineageRow>(statement)).rows
      .map(recordChangeFromRow)
      .filter((change): change is RecordChange => change !== undefined);
  } catch (cause) {
    throw postgreSqlPersistenceOperationError("read_lineage", cause);
  }
}
function duplicateChange(): Result<never, PlatformPersistenceError> { return { ok: false, error: platformPersistenceError({ code: "PLATFORM_PERSISTENCE_DUPLICATE_RECORD_CHANGE", defaultMessage: "Record change already exists.", messageKey: "platform.persistence.lineage.duplicate" }) }; }
