import { createHash } from "node:crypto";
import type { Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError, type PersistenceLocalRejectionDetail } from "@kanbien/platform-persistence";
import type { PostgreSqlStatement, PostgreSqlTransactionalClient } from "./connection";
import { postgreSqlIdentifier, type PostgreSqlPersistenceConfiguration } from "./configuration/index";
import { postgreSqlPersistenceOperationError } from "./errors";
import { withPostgreSqlTransaction, type PostgreSqlTransactionOptions } from "./transactions";
import { localRejection } from "./observations";

export interface PostgreSqlMigration {
  readonly id: string;
  readonly checksum: string;
  readonly statements: readonly PostgreSqlStatement[];
}

export interface PostgreSqlMigrationManifest {
  readonly schema: string;
  /**
   * An administrative bootstrap may own schema creation.  In that mode an
   * ordinary migration identity must not need CREATE on the database merely
   * because the generic runner normally creates its schema defensively.
   */
  readonly schemaPreprovisioned?: boolean;
  readonly migrations: readonly PostgreSqlMigration[];
}

export type PostgreSqlMigrationResult =
  | { readonly status: "applied"; readonly id: string }
  | { readonly status: "already-applied"; readonly id: string };

export interface PostgreSqlMigrationRunner {
  apply(manifest: PostgreSqlMigrationManifest): Promise<Result<readonly PostgreSqlMigrationResult[], PlatformPersistenceError>>;
}

export function createPostgreSqlMigrationRunner(
  configuration: PostgreSqlPersistenceConfiguration,
  options: PostgreSqlTransactionOptions,
  toolVersion: string,
): PostgreSqlMigrationRunner {
  return {
    apply: async (manifest) => {
      if (!toolVersionPattern.test(toolVersion)) return invalidMigration("Migration tool version is invalid.", options, "tool-version", "pattern");
      const schemaMatches = manifest.schema === configuration.schema;
      if (!schemaMatches || postgreSqlIdentifier(manifest.schema) === undefined) {
        return invalidMigration("Migration manifest schema must equal the reviewed adapter configuration schema.", options, "schema", schemaMatches ? "pattern" : "mismatch");
      }
      const rejected = manifestRejection(manifest);
      if (rejected !== undefined) return invalidMigration("Migration manifest identifiers, checksums, or statement list are invalid.", options, rejected.field, rejected.condition, rejected.ordinal);
      return withPostgreSqlTransaction(options, async (client) => {
        // The advisory lock is scoped to this transaction. A stopped or failed
        // migration releases it, while a competing executor waits only for the
        // reviewed bounded lock timeout below. Never replay after a timeout
        // without first observing the migration-history state.
        await client.query({ text: "SET LOCAL lock_timeout = '30000ms'" });
        await client.query({
          text: "SELECT pg_advisory_xact_lock(hashtext($1))",
          values: [`kanbien-postgresql-migration:${manifest.schema}`],
        });
        return applyManifest(client, manifest, toolVersion, options);
      });
    },
  };
}

export function postgreSqlPersistenceFoundationMigration(schema: string): PostgreSqlMigration {
  const outbox = qualified(schema, "platform_outbox");
  const processing = qualified(schema, "platform_processing");
  const lineage = qualified(schema, "platform_record_change");
  const statements: readonly PostgreSqlStatement[] = [
    { text: `CREATE TABLE IF NOT EXISTS ${outbox} (id text PRIMARY KEY, subject_kind text NOT NULL, subject_id text NOT NULL, message_type text NOT NULL, message_version integer NOT NULL, delivery_policy text NOT NULL, created_at timestamptz NOT NULL, tenant_id text, correlation_id text, causation_id text, state text NOT NULL CHECK (state IN ('pending', 'leased', 'published')), attempt integer NOT NULL CHECK (attempt >= 0), lease_owner text, lease_fence integer, lease_acquired_at timestamptz, lease_expires_at timestamptz, published_at timestamptz)` },
    { text: `CREATE INDEX IF NOT EXISTS "platform_outbox_due" ON ${outbox} (state, lease_expires_at, created_at, id)` },
    { text: `CREATE TABLE IF NOT EXISTS ${processing} (outbox_entry_id text PRIMARY KEY, state text NOT NULL CHECK (state IN ('claimed', 'retry-eligible', 'completed')), attempt integer NOT NULL CHECK (attempt >= 0), lease_owner text, lease_fence integer, lease_acquired_at timestamptz, lease_expires_at timestamptz, released_at timestamptz, completion_outcome text CHECK (completion_outcome IN ('succeeded', 'terminal-failure')), completed_at timestamptz)` },
    { text: `CREATE TABLE IF NOT EXISTS ${lineage} (id text PRIMARY KEY, record_kind text NOT NULL, record_id text NOT NULL, revision integer NOT NULL CHECK (revision > 0), action text NOT NULL CHECK (action IN ('created', 'updated', 'deleted', 'restored')), occurred_at timestamptz NOT NULL, tenant_id text, actor_kind text CHECK (actor_kind IN ('principal', 'system')), actor_id text, correlation_id text, causation_id text, changed_fields text[])` },
    { text: `CREATE UNIQUE INDEX IF NOT EXISTS "platform_record_change_revision" ON ${lineage} (record_kind, record_id, revision)` },
    { text: `CREATE INDEX IF NOT EXISTS "platform_record_change_cause" ON ${lineage} (causation_id, occurred_at, id)` },
  ];
  return {
    id: "v0001_platform_persistence",
    checksum: postgreSqlMigrationChecksum(statements),
    statements,
  };
}

export function postgreSqlMigrationChecksum(statements: readonly PostgreSqlStatement[]): string {
  return createHash("sha256").update(statements.map((statement) => statement.text).join("\n")).digest("hex");
}

async function applyManifest(
  client: PostgreSqlTransactionalClient,
  manifest: PostgreSqlMigrationManifest,
  toolVersion: string,
  options: PostgreSqlTransactionOptions,
): Promise<Result<readonly PostgreSqlMigrationResult[], PlatformPersistenceError>> {
  const historyTable = qualified(manifest.schema, "platform_migration_history");
  try {
    if (manifest.schemaPreprovisioned === true) {
      const existing = await client.query<{ readonly exists: boolean }>({
        text: "SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = $1) AS exists",
        values: [manifest.schema],
      });
      if (existing.rows[0]?.exists !== true) {
        return invalidMigration("Reviewed migration schema is absent; run the governed administrative bootstrap before the ordinary migration task.", options, "schema", "not-found", undefined, "transaction-body");
      }
    } else {
      await client.query({ text: `CREATE SCHEMA IF NOT EXISTS ${quoted(manifest.schema)}` });
    }
    await client.query({
      text: `CREATE TABLE IF NOT EXISTS ${historyTable} (migration_id text PRIMARY KEY, checksum text NOT NULL, tool_version text NOT NULL, applied_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP)`,
    });
    const results: PostgreSqlMigrationResult[] = [];
    let ordinal = 0;
    for (const migration of manifest.migrations) {
      const recorded = await client.query<{ readonly checksum: string }>({
        text: `SELECT checksum FROM ${historyTable} WHERE migration_id = $1`,
        values: [migration.id],
      });
      const prior = recorded.rows[0];
      if (prior !== undefined) {
        if (prior.checksum !== migration.checksum) return checksumMismatch(migration.id, options, ordinal);
        results.push({ status: "already-applied", id: migration.id });
        ordinal++;
        continue;
      }
      for (const statement of migration.statements) await client.query(statement);
      await client.query({
        text: `INSERT INTO ${historyTable} (migration_id, checksum, tool_version) VALUES ($1, $2, $3)`,
        values: [migration.id, migration.checksum, toolVersion],
      });
      results.push({ status: "applied", id: migration.id });
      ordinal++;
    }
    return { ok: true, value: results };
  } catch (cause) {
    return { ok: false, error: postgreSqlPersistenceOperationError("migration", cause, options) };
  }
}

function manifestRejection(manifest: PostgreSqlMigrationManifest): Pick<PersistenceLocalRejectionDetail, "field" | "condition" | "ordinal"> | undefined {
  if (manifest.schemaPreprovisioned !== undefined && typeof manifest.schemaPreprovisioned !== "boolean") return { field: "schema-preprovisioned", condition: "wrong-type" };
  const identifiers = new Set<string>();
  let priorIdentifier: string | undefined;
  let rejected: Pick<PersistenceLocalRejectionDetail, "field" | "condition" | "ordinal"> | undefined;
  const accepted = manifest.migrations.every((migration, ordinal) => {
    let local: typeof rejected;
    if (!migrationIdentifierPattern.test(migration.id)) local = { field: "migration-id", condition: "pattern", ordinal };
    else if (!checksumPattern.test(migration.checksum)) local = { field: "checksum", condition: "pattern", ordinal };
    else if (migration.statements.length === 0) local = { field: "statements", condition: "empty", ordinal };
    else if (identifiers.has(migration.id)) local = { field: "migration-id", condition: "duplicate", ordinal };
    else if (priorIdentifier !== undefined && migration.id <= priorIdentifier) local = { field: "migration-id", condition: "out-of-order", ordinal };
    if (local !== undefined) { rejected = local; return false; }
    identifiers.add(migration.id);
    priorIdentifier = migration.id;
    let statementRejection: typeof rejected;
    const statementsAccepted = migration.statements.every((statement, statementOrdinal) => {
      if (statement.text.trim().length === 0) { statementRejection = { field: "statement", condition: "blank", ordinal: statementOrdinal }; return false; }
      if (statement.text.includes("\u0000")) { statementRejection = { field: "statement", condition: "nul", ordinal: statementOrdinal }; return false; }
      return true;
    });
    if (!statementsAccepted) rejected = statementRejection ?? { field: "statements", condition: "predicate-rejected", ordinal };
    return statementsAccepted;
  });
  return accepted ? undefined : rejected ?? { field: "manifest", condition: "predicate-rejected" };
}

function quoted(identifier: string): string {
  if (postgreSqlIdentifier(identifier) === undefined) {
    throw new TypeError("PostgreSQL identifiers must be reviewed lowercase SQL identifiers.");
  }
  return `"${identifier}"`;
}

function qualified(schema: string, relation: string): string {
  return `${quoted(schema)}.${quoted(relation)}`;
}

function invalidMigration(defaultMessage: string, options: PostgreSqlTransactionOptions,
  field: PersistenceLocalRejectionDetail["field"], condition: PersistenceLocalRejectionDetail["condition"], ordinal?: number,
  phase: PersistenceLocalRejectionDetail["phase"] = "preflight"): Result<never, PlatformPersistenceError> {
  return {
    ok: false,
    error: platformPersistenceError({
      code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED",
      messageKey: "platform.persistence.store.operation_failed",
      params: { operation: "migration", provider_failure_class: "unknown" },
      defaultMessage,
      ...localRejection(options, { operation: "migration", field, condition, phase, effect: phase === "preflight" ? "not-started" : "unknown", ...(ordinal === undefined ? {} : { ordinal }) }),
    }),
  };
}

function checksumMismatch(id: string, options: PostgreSqlTransactionOptions, ordinal: number): Result<never, PlatformPersistenceError> {
  return {
    ok: false,
    error: platformPersistenceError({
      code: "PLATFORM_PERSISTENCE_MIGRATION_CHECKSUM_MISMATCH",
      defaultMessage: "Applied migration checksum does not match the reviewed manifest.",
      messageKey: "platform.persistence.migration.checksum_mismatch",
      params: { migration_id: id },
      ...localRejection(options, { operation: "migration", field: "checksum", condition: "checksum-mismatch", phase: "after-statements", effect: "unknown", ordinal }),
    }),
  };
}

const migrationIdentifierPattern = /^v[0-9]{4}_[a-z][a-z0-9_]{0,62}$/;
const checksumPattern = /^[a-f0-9]{64}$/;
const toolVersionPattern = /^[A-Za-z0-9._-]{1,64}$/;
