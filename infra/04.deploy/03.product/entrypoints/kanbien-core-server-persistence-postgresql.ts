// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-postgresql
//   version: 2
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-30"
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
import { postgreSqlFailureDiagnostic, postgreSqlPersistenceOperationError, postgreSqlSecurityDiagnosticRecords } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { attachCoreDiagnosticRecord } from "@kanbien/core/shared";
import { observePlatformPersistenceDiagnostic, persistenceCrudObservedDiagnosticRecord, persistenceLocalRejectionDiagnosticRecord, persistenceReconciliationDiagnosticRecord,
  type PlatformPersistenceDiagnosticOptions } from "@kanbien/platform-persistence";
import { platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import type {
  KanbienCorePersistenceRuntime,
  KanbienPersistenceAcceptanceReadResult,
  KanbienPersistenceAcceptanceRecord,
} from "./kanbien-core-server-persistence.app";

export interface KanbienCoreServerPostgreSqlPersistenceOptions {
  readonly pool: PostgreSqlConnectionPool;
  readonly schema: string;
  /** Additional explicitly selected source definitions, never provider values. */
  readonly diagnosticDefinitions?: PlatformPersistenceDiagnosticOptions["diagnosticDefinitions"];
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
  const readinessObservation = async () => {
    try {
      await options.pool.query({ text: `SELECT 1 FROM ${table} LIMIT 1` });
      return { readiness: "ready" as const };
    } catch (cause) {
      const error = postgreSqlPersistenceOperationError("readiness", cause);
      return { readiness: "not-ready" as const,
        ...(error.diagnosticRecord === undefined ? {} : { diagnosticRecord: error.diagnosticRecord, diagnosticCode: error.diagnosticRecord.code }),
        ...(error.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: error.relatedDiagnosticRecords }) };
    }
  };
  return {
    readinessObservation,
    readiness: async () => (await readinessObservation()).readiness,
    createAcceptanceRecord: async (record, onDiagnostic) => createRecord(options.pool, table, record, options, onDiagnostic),
    readAcceptanceRecord: async (recordId, onDiagnostic) => readRecord(options.pool, table, recordId, options, onDiagnostic),
    deleteAcceptanceRecord: async (recordId, onDiagnostic) => deleteRecord(options.pool, table, recordId, options, onDiagnostic),
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
  options: KanbienCoreServerPostgreSqlPersistenceOptions,
  onDiagnostic?: PlatformPersistenceDiagnosticOptions["onDiagnostic"],
): Promise<"created" | "already-exists" | "conflict" | "unavailable" | "uncertain"> {
  try {
    const inserted = await pool.query<{ readonly record_id: string }>({
      text: `INSERT INTO ${table} (record_id, fact_digest) VALUES ($1, $2) ON CONFLICT (record_id) DO NOTHING RETURNING record_id`,
      values: [record.id, record.factDigest],
    });
    if (inserted.rows.length === 1) return "created";
    const existing = await readRecord(pool, table, record.id, options, onDiagnostic, "reconciliation");
    return reconciledAcceptanceOutcome(existing, record, onDiagnostic, "no-row-returned");
  } catch (cause) {
    observeAcceptanceFailure(options, onDiagnostic, "create", "primary", cause);
    // A failed client call can follow a committed remote insert. Reconcile
    // only by reading the durable record; otherwise keep the outcome unknown.
    try {
      const existing = await readRecord(pool, table, record.id, options, onDiagnostic, "reconciliation");
      return reconciledAcceptanceOutcome(existing, record, onDiagnostic, "call-threw");
    } catch {
      return "unavailable";
    }
  }
}

function reconciledAcceptanceOutcome(
  existing: KanbienPersistenceAcceptanceReadResult,
  record: KanbienPersistenceAcceptanceRecord,
  onDiagnostic: PlatformPersistenceDiagnosticOptions["onDiagnostic"],
  primaryOutcome: "no-row-returned" | "call-threw",
): "already-exists" | "conflict" | "uncertain" | "unavailable" {
  // Select the original result before the optional observer can run. A matching
  // durable row proves its current content, not which invocation created it.
  const matching = existing.outcome === "found" ? existing.record.factDigest === record.factDigest : undefined;
  const outcome = matching === true ? "already-exists" : matching === false ? "conflict"
    : existing.outcome === "not-found" ? "uncertain" : "unavailable";
  if (onDiagnostic !== undefined) try {
    observePlatformPersistenceDiagnostic({ onDiagnostic }, persistenceReconciliationDiagnosticRecord({
      operation: "create", primaryOutcome,
      observed: matching === true ? "matching" : matching === false ? "different" : existing.outcome === "not-found" ? "absent" : "unavailable",
      effect: "read-result-observed",
    }));
  } catch { /* Preserve the already selected result. */ }
  return outcome;
}

async function readRecord(
  pool: PostgreSqlConnectionPool,
  table: string,
  recordId: string,
  options: KanbienCoreServerPostgreSqlPersistenceOptions,
  onDiagnostic?: PlatformPersistenceDiagnosticOptions["onDiagnostic"],
  boundary: "primary" | "reconciliation" = "primary",
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
  } catch (cause) {
    observeAcceptanceFailure(options, onDiagnostic, "read", boundary, cause);
    return { outcome: "unavailable" };
  }
}

async function deleteRecord(
  pool: PostgreSqlConnectionPool,
  table: string,
  recordId: string,
  options: KanbienCoreServerPostgreSqlPersistenceOptions,
  onDiagnostic?: PlatformPersistenceDiagnosticOptions["onDiagnostic"],
): Promise<"deleted" | "not-found" | "unavailable" | "uncertain"> {
  try {
    const result = await pool.query({
      text: `DELETE FROM ${table} WHERE record_id = $1`,
      values: [recordId],
    });
    return result.rowCount === 1 ? "deleted" : "not-found";
  } catch (cause) {
    observeAcceptanceFailure(options, onDiagnostic, "delete", "primary", cause);
    return "uncertain";
  }
}

function acceptanceTable(schema: string): string {
  if (!/^[a-z][a-z0-9_]{0,62}$/.test(schema)) {
    throw attachCoreDiagnosticRecord(new TypeError("CORE_SERVER_PERSISTENCE_SCHEMA_INVALID"), persistenceLocalRejectionDiagnosticRecord({
      operation: "validate-identifier", field: "schema", condition: "pattern", phase: "preflight", effect: "not-started",
    }));
  }
  return `"${schema}"."core_server_persistence_acceptance"`;
}

/** Failed client work does not prove a write was rejected. Each failed call
 * owns one location record alongside the complete selected source envelope.
 */
function observeAcceptanceFailure(
  options: KanbienCoreServerPostgreSqlPersistenceOptions,
  onDiagnostic: PlatformPersistenceDiagnosticOptions["onDiagnostic"],
  operation: "create" | "read" | "delete",
  boundary: "primary" | "reconciliation",
  cause: unknown,
): void {
  if (onDiagnostic === undefined) return;
  try {
    const diagnostics = { onDiagnostic, diagnosticDefinitions: [
      ...platformSecurityDiagnosticCatalog.definitions, ...(options.diagnosticDefinitions ?? []),
    ] };
    const facts = postgreSqlFailureDiagnostic(cause).facts;
    const source = observePlatformPersistenceDiagnostic(diagnostics, persistenceCrudObservedDiagnosticRecord(facts, operation, boundary), cause);
    if (facts.classification === "tls_trust_invalid") {
      const retained = [source.diagnosticRecord, ...(source.relatedDiagnosticRecords ?? [])];
      for (const peer of postgreSqlSecurityDiagnosticRecords(cause)) {
        if (!retained.some((record) => record?.code === peer.code && record.definitionVersion === peer.definitionVersion && JSON.stringify(record.detail) === JSON.stringify(peer.detail))) {
          observePlatformPersistenceDiagnostic(diagnostics, peer);
        }
      }
    }
  } catch { /* Diagnostics do not change reconciliation, result or query count. */ }
}
