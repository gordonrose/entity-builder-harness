// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-postgresql
//   version: 1
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-23"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Bind the reviewed AWS PostgreSQL adapter to the private core-server persistence acceptance contract.
//   portability:
//     class: internal
//     targets:
//     - kanbien-core-platform
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-main
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts

import type { PostgreSqlConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import type {
  KanbienCorePersistenceRuntime,
  KanbienPersistenceAcceptanceReadResult,
  KanbienPersistenceAcceptanceRecord,
} from "./kanbien-core-server-persistence.app";

export interface KanbienCoreServerPostgreSqlPersistenceOptions {
  readonly pool: PostgreSqlConnectionPool;
  readonly schema: string;
}

/**
 * This capability deliberately supports only the acceptance record used to
 * prove server-mediated persistence. It is neither a general repository nor
 * a verifier-side database client. All values are bound parameters and all
 * provider failures become stable server outcomes at the app boundary.
 */
export function createKanbienCoreServerPostgreSqlPersistenceRuntime(
  options: KanbienCoreServerPostgreSqlPersistenceOptions,
): KanbienCorePersistenceRuntime {
  const table = acceptanceTable(options.schema);
  return {
    readiness: async () => {
      try {
        await options.pool.query({ text: `SELECT 1 FROM ${table} LIMIT 1` });
        return "ready";
      } catch {
        return "not-ready";
      }
    },
    createAcceptanceRecord: async (record) => createRecord(options.pool, table, record),
    readAcceptanceRecord: async (recordId) => readRecord(options.pool, table, recordId),
    deleteAcceptanceRecord: async (recordId) => deleteRecord(options.pool, table, recordId),
    close: async () => options.pool.end(),
  };
}

export function kanbienCoreServerPersistenceAcceptanceMigration(schema: string) {
  const table = acceptanceTable(schema);
  const statements = [{
    text: `CREATE TABLE IF NOT EXISTS ${table} (record_id text PRIMARY KEY, fact_digest char(64) NOT NULL, created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP, CHECK (record_id ~ '^[a-z0-9][a-z0-9-]{7,95}$'), CHECK (fact_digest ~ '^[a-f0-9]{64}$'))`,
  }];
  return { id: "v0002_core_server_persistence_acceptance", statements };
}

async function createRecord(
  pool: PostgreSqlConnectionPool,
  table: string,
  record: KanbienPersistenceAcceptanceRecord,
): Promise<"created" | "already-exists" | "conflict" | "unavailable" | "uncertain"> {
  try {
    const inserted = await pool.query<{ readonly record_id: string }>({
      text: `INSERT INTO ${table} (record_id, fact_digest) VALUES ($1, $2) ON CONFLICT (record_id) DO NOTHING RETURNING record_id`,
      values: [record.id, record.factDigest],
    });
    if (inserted.rows.length === 1) return "created";
    const existing = await readRecord(pool, table, record.id);
    if (existing.outcome === "found") return existing.record.factDigest === record.factDigest ? "already-exists" : "conflict";
    return existing.outcome === "not-found" ? "uncertain" : "unavailable";
  } catch {
    // A failed client call can follow a committed remote insert. Reconcile
    // only by reading the durable record; otherwise keep the outcome unknown.
    try {
      const existing = await readRecord(pool, table, record.id);
      if (existing.outcome === "found") return existing.record.factDigest === record.factDigest ? "already-exists" : "conflict";
      return existing.outcome === "not-found" ? "uncertain" : "unavailable";
    } catch {
      return "unavailable";
    }
  }
}

async function readRecord(
  pool: PostgreSqlConnectionPool,
  table: string,
  recordId: string,
): Promise<KanbienPersistenceAcceptanceReadResult> {
  try {
    const result = await pool.query<{ readonly record_id: string; readonly fact_digest: string }>({
      text: `SELECT record_id, fact_digest FROM ${table} WHERE record_id = $1`,
      values: [recordId],
    });
    const row = result.rows[0];
    return row === undefined
      ? { outcome: "not-found" }
      : { outcome: "found", record: { id: row.record_id, factDigest: row.fact_digest } };
  } catch {
    return { outcome: "unavailable" };
  }
}

async function deleteRecord(
  pool: PostgreSqlConnectionPool,
  table: string,
  recordId: string,
): Promise<"deleted" | "not-found" | "unavailable" | "uncertain"> {
  try {
    const result = await pool.query({
      text: `DELETE FROM ${table} WHERE record_id = $1`,
      values: [recordId],
    });
    return result.rowCount === 1 ? "deleted" : "not-found";
  } catch {
    return "uncertain";
  }
}

function acceptanceTable(schema: string): string {
  if (!/^[a-z][a-z0-9_]{0,62}$/.test(schema)) {
    throw new TypeError("CORE_SERVER_PERSISTENCE_SCHEMA_INVALID");
  }
  return `"${schema}"."core_server_persistence_acceptance"`;
}
