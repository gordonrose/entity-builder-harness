import { createHash } from "node:crypto";
import type { Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError } from "@kanbien/platform-persistence";
import type { PostgreSqlStatement, PostgreSqlTransactionalClient } from "./connection";
import { postgreSqlIdentifier, type PostgreSqlPersistenceConfiguration } from "./config";
import { postgreSqlPersistenceOperationError } from "./errors";
import { withPostgreSqlTransaction, type PostgreSqlTransactionOptions } from "./transactions";

export interface PostgreSqlMigration {
  readonly id: string;
  readonly checksum: string;
  readonly statements: readonly PostgreSqlStatement[];
}

export interface PostgreSqlMigrationManifest {
  readonly schema: string;
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
      if (!toolVersionPattern.test(toolVersion)) return invalidMigration("Migration tool version is invalid.");
      if (manifest.schema !== configuration.schema || postgreSqlIdentifier(manifest.schema) === undefined) {
        return invalidMigration("Migration manifest schema must equal the reviewed adapter configuration schema.");
      }
      if (!validManifest(manifest)) return invalidMigration("Migration manifest identifiers, checksums, or statement list are invalid.");
      return withPostgreSqlTransaction(options, async (client) => applyManifest(client, manifest, toolVersion));
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
): Promise<Result<readonly PostgreSqlMigrationResult[], PlatformPersistenceError>> {
  const historyTable = qualified(manifest.schema, "platform_migration_history");
  try {
    await client.query({ text: `CREATE SCHEMA IF NOT EXISTS ${quoted(manifest.schema)}` });
    await client.query({
      text: `CREATE TABLE IF NOT EXISTS ${historyTable} (migration_id text PRIMARY KEY, checksum text NOT NULL, tool_version text NOT NULL, applied_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP)`,
    });
    const results: PostgreSqlMigrationResult[] = [];
    for (const migration of manifest.migrations) {
      const recorded = await client.query<{ readonly checksum: string }>({
        text: `SELECT checksum FROM ${historyTable} WHERE migration_id = $1`,
        values: [migration.id],
      });
      const prior = recorded.rows[0];
      if (prior !== undefined) {
        if (prior.checksum !== migration.checksum) return checksumMismatch(migration.id);
        results.push({ status: "already-applied", id: migration.id });
        continue;
      }
      for (const statement of migration.statements) await client.query(statement);
      await client.query({
        text: `INSERT INTO ${historyTable} (migration_id, checksum, tool_version) VALUES ($1, $2, $3)`,
        values: [migration.id, migration.checksum, toolVersion],
      });
      results.push({ status: "applied", id: migration.id });
    }
    return { ok: true, value: results };
  } catch (cause) {
    return { ok: false, error: postgreSqlPersistenceOperationError("migration", cause) };
  }
}

function validManifest(manifest: PostgreSqlMigrationManifest): boolean {
  const identifiers = new Set<string>();
  let priorIdentifier: string | undefined;
  return manifest.migrations.every((migration) => {
    if (
      !migrationIdentifierPattern.test(migration.id)
      || !checksumPattern.test(migration.checksum)
      || migration.statements.length === 0
      || identifiers.has(migration.id)
      || (priorIdentifier !== undefined && migration.id <= priorIdentifier)
    ) return false;
    identifiers.add(migration.id);
    priorIdentifier = migration.id;
    return migration.statements.every((statement) => statement.text.trim().length > 0 && !statement.text.includes("\u0000"));
  });
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

function invalidMigration(defaultMessage: string): Result<never, PlatformPersistenceError> {
  return {
    ok: false,
    error: {
      ...postgreSqlPersistenceOperationError("migration"),
      defaultMessage,
    },
  };
}

function checksumMismatch(id: string): Result<never, PlatformPersistenceError> {
  return {
    ok: false,
    error: platformPersistenceError({
      code: "PLATFORM_PERSISTENCE_MIGRATION_CHECKSUM_MISMATCH",
      defaultMessage: "Applied migration checksum does not match the reviewed manifest.",
      messageKey: "platform.persistence.migration.checksum_mismatch",
      params: { migration_id: id },
    }),
  };
}

const migrationIdentifierPattern = /^v[0-9]{4}_[a-z][a-z0-9_]{0,62}$/;
const checksumPattern = /^[a-f0-9]{64}$/;
const toolVersionPattern = /^[A-Za-z0-9._-]{1,64}$/;
