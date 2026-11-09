// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.administration
//   version: 1
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Provision only the isolated schema and bounded identities, then grant and observe exact feature privileges.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { createNodePostgreSqlConnectionPool, postgreSqlPersistenceOperationError, type PostgreSqlConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { persistenceConfigurationResult, persistenceCertificateAuthorityResult, persistenceCredentialsResult } from "../kanbien-core-server-persistence-configuration";
import { ensureBoundedLoginRole, ensureRdsIamAuthentication, requireBoundedExistingRole } from "../kanbien-core-server-persistence-role-credential";
import { entitySmokeSchema, entitySmokeRuntimeUsername, entitySmokeMigrationUsername, entitySmokeMigrationManifest } from "./postgresql";
import { entitySmokeConfigurationError, entitySmokeDependencyStateError, entitySmokeDiagnosticCatalogs, reportEntitySmokeFailure } from "./diagnostics";
import { performEntitySmokeDatabasePreflight } from "./preflight";

export type EntitySmokeAdministrationOperation = "bootstrap" | "grant-runtime" | "observe-permissions" | "observe-migration-state" | "revoke-runtime" | "restore-runtime";
const operations = new Set(["preflight", "bootstrap", "grant-runtime", "observe-permissions", "observe-migration-state", "revoke-runtime", "restore-runtime"]);
type AdministrationResult = "ENTITY_SMOKE_ADMINISTRATION_CONFIRMED" | "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED" | "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED";

export async function runEntitySmokeAdministration(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const operation = env["ENTITY_SMOKE_ADMINISTRATION_OPERATION"];
  if (!operation || !operations.has(operation)) { reject(entitySmokeConfigurationError("operation", "invalid")); return; }
  if (env["PERSISTENCE_POSTGRES_SCHEMA"] !== entitySmokeSchema ||
      env["PERSISTENCE_RUNTIME_DATABASE_USERNAME"] !== entitySmokeRuntimeUsername ||
      env["PERSISTENCE_MIGRATION_DATABASE_USERNAME"] !== entitySmokeMigrationUsername) {
    reject(entitySmokeConfigurationError("identity", "mismatch")); return;
  }
  if (env["PERSISTENCE_POSTGRES_CA_PATH"] !== "/app/assets/rds-eu-west-1-bundle.crt") { reject(entitySmokeConfigurationError("authority", "mismatch")); return; }
  const settings = persistenceConfigurationResult(env, "administration");
  if (!settings.ok) { reject({ diagnosticRecord: settings.error.diagnostic }); return; }
  const credentials = persistenceCredentialsResult(env["PERSISTENCE_ADMINISTRATOR_CREDENTIALS"]);
  if (!credentials.ok) { reject({ diagnosticRecord: credentials.error.diagnostic }); return; }
  const authority = persistenceCertificateAuthorityResult(env);
  if (!authority.ok) { reject({ diagnosticRecord: authority.error.diagnostic }); return; }
  if ([entitySmokeRuntimeUsername, entitySmokeMigrationUsername].includes(credentials.value.username)) {
    reject(entitySmokeConfigurationError("identity", "mismatch")); return;
  }
  const pool = createNodePostgreSqlConnectionPool(settings.value, { ...credentials.value, certificateAuthority: authority.value });
  let completion: { verdict: "passed"; code: string; operation: string } | undefined;
  try {
    const code = operation === "preflight"
      ? await performEntitySmokeDatabasePreflight(pool, { identity: "administration", database: settings.value.database, username: credentials.value.username })
      : await performEntitySmokeAdministration(pool, operation as EntitySmokeAdministrationOperation, settings.value.database);
    completion = { verdict: "passed", code, operation };
  } catch (cause) { reportEntitySmokeFailure("administration", operation === "preflight" ? "not-started" : "unknown",
    postgreSqlPersistenceOperationError(operation === "preflight" ? "readiness" : "administration", cause, { diagnosticDefinitions: entitySmokeDiagnosticCatalogs.flatMap(catalog => [...catalog.definitions]) })); process.exitCode = 1; }
  finally { try { await pool.end(); } catch (cause) { completion = undefined; reportEntitySmokeFailure("close", "not-assessed", cause); process.exitCode = 1; } }
  if (completion !== undefined) console.log(JSON.stringify(completion));
}
function reject(cause: unknown): void { reportEntitySmokeFailure("administration", "not-started", cause); process.exitCode = 1; }

/** The database name was checked by the existing PostgreSQL configuration owner.
 * Role/schema/table names below are fixed by this scope, never caller input. */
export async function performEntitySmokeAdministration(pool: PostgreSqlConnectionPool, operation: EntitySmokeAdministrationOperation, database: string): Promise<AdministrationResult> {
  if (!operations.has(operation) || (operation as string) === "preflight") throw entitySmokeConfigurationError("operation", "invalid");
  if (!/^[a-z][a-z0-9_]{0,62}$/.test(database)) throw entitySmokeConfigurationError("database", "invalid");
  if (operation === "observe-permissions") { await observePermissions(pool, database); return "ENTITY_SMOKE_ADMINISTRATION_CONFIRMED"; }
  if (operation === "observe-migration-state") return observeMigrationState(pool);
  if (operation === "revoke-runtime" || operation === "restore-runtime") {
    await changeRuntimeAccess(pool, operation);
    return "ENTITY_SMOKE_ADMINISTRATION_CONFIRMED";
  }
  const client = await pool.connect();
  try {
    await client.query({ text: "BEGIN" });
    await client.query({ text: "SET LOCAL lock_timeout = '30000ms'" });
    await client.query({ text: "SELECT pg_advisory_xact_lock(hashtext($1))", values: ["entity-smoke-identity-bootstrap"] });
    if (operation === "bootstrap") {
      const authority = await client.query<{ allowed: boolean }>({
        text: "SELECT has_database_privilege(current_user, $1, 'CREATE WITH GRANT OPTION') AND has_database_privilege(current_user, $1, 'CONNECT WITH GRANT OPTION') AS allowed",
        values: [database],
      });
      if (authority.rows.length !== 1 || authority.rows[0]?.allowed !== true) throw entitySmokeDependencyStateError(operation, "privileges", "not-confirmed");
      // Existing bounded-role primitives reject elevated or revoked identities;
      // this operation never silently re-enables a NOLOGIN role.
      const connection: PostgreSqlConnectionPool = { query: statement => client.query(statement), connect: async () => client, end: async () => undefined };
      await ensureBoundedLoginRole(connection, { username: entitySmokeMigrationUsername });
      await ensureBoundedLoginRole(connection, { username: entitySmokeRuntimeUsername });
      await ensureRdsIamAuthentication(connection, { username: entitySmokeMigrationUsername });
      await ensureRdsIamAuthentication(connection, { username: entitySmokeRuntimeUsername });
      // PostgreSQL 16 gives CREATEROLE creators ADMIN but not SET by default.
      // Select only this scope's migration-owner authority, without inheritance.
      // Regranting ADMIN to ourself would create a forbidden grantor cycle.
      await client.query({ text: 'GRANT entity_smoke_migration TO CURRENT_USER WITH INHERIT FALSE, SET TRUE' });
      const schema = await client.query<{ owner: string }>({ text: "SELECT pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname = $1", values: [entitySmokeSchema] });
      if (schema.rows.length > 0 && (schema.rows.length !== 1 || schema.rows[0]?.owner !== entitySmokeMigrationUsername)) throw entitySmokeDependencyStateError(operation, "schema-owner", schema.rows.length !== 1 ? "count-mismatch" : "mismatch");
      if (schema.rows.length === 0) {
        await client.query({ text: `GRANT CREATE ON DATABASE "${database}" TO entity_smoke_migration` });
        await client.query({ text: 'CREATE SCHEMA "entity_smoke"' });
        await client.query({ text: 'ALTER SCHEMA "entity_smoke" OWNER TO entity_smoke_migration' });
        await client.query({ text: `REVOKE CREATE ON DATABASE "${database}" FROM entity_smoke_migration` });
      }
      await client.query({ text: `GRANT CONNECT ON DATABASE "${database}" TO entity_smoke_migration, entity_smoke_runtime` });
      await client.query({ text: 'SET LOCAL ROLE entity_smoke_migration' });
      await client.query({ text: 'REVOKE ALL ON SCHEMA "entity_smoke" FROM entity_smoke_runtime' });
      await client.query({ text: 'GRANT USAGE ON SCHEMA "entity_smoke" TO entity_smoke_runtime' });
    } else {
      await client.query({ text: 'SET LOCAL ROLE entity_smoke_migration' });
      const manifest = entitySmokeMigrationManifest();
      const history = await client.query<{ checksum: string }>({ text: 'SELECT checksum FROM "entity_smoke".platform_migration_history WHERE migration_id = $1', values: [manifest.migrations[0].id] });
      if (history.rows.length !== 1) throw entitySmokeDependencyStateError(operation, "history-count", "count-mismatch");
      if (history.rows[0]?.checksum !== manifest.migrations[0].checksum) throw entitySmokeDependencyStateError(operation, "history-checksum", "mismatch");
      await client.query({ text: 'REVOKE ALL ON "entity_smoke".platform_migration_history FROM entity_smoke_runtime' });
      await client.query({ text: 'REVOKE ALL ON "entity_smoke".test_entity FROM entity_smoke_runtime' });
      await client.query({ text: 'GRANT SELECT, INSERT, UPDATE ON "entity_smoke".test_entity TO entity_smoke_runtime' });
    }
    await client.query({ text: "COMMIT" });
    return "ENTITY_SMOKE_ADMINISTRATION_CONFIRMED";
  } catch (cause) {
    try { await client.query({ text: "ROLLBACK" }); }
    catch (rollbackCause) { reportEntitySmokeFailure("administration", "unknown", rollbackCause); }
    throw cause;
  } finally { client.release(); }
}

/** These are explicit, non-transactional access controls. Disabling LOGIN is
 * committed before terminating sessions; a failed observation cannot undo it.
 * Only the feature's fixed identity is ever selected. No table grants, role
 * attributes, passwords, records or migration history are repaired here. */
async function changeRuntimeAccess(pool: PostgreSqlConnectionPool, operation: "revoke-runtime" | "restore-runtime"): Promise<void> {
  await requireBoundedExistingRole(pool, { username: entitySmokeRuntimeUsername });
  if (operation === "revoke-runtime") {
    await pool.query({ text: 'REVOKE rds_iam FROM entity_smoke_runtime' });
    await pool.query({ text: 'ALTER ROLE entity_smoke_runtime NOLOGIN' });
    const terminated = await pool.query<{ terminated: boolean }>({
      text: "SELECT pg_terminate_backend(pid) AS terminated FROM pg_stat_activity WHERE usename = $1 AND pid <> pg_backend_pid()",
      values: [entitySmokeRuntimeUsername],
    });
    if (terminated.rows.some(row => row.terminated !== true)) throw entitySmokeDependencyStateError(operation, "sessions", "not-confirmed");
  } else {
    // Do not restore while an old session remains. The controller separately
    // proves replacement after this access-only operation.
    await requireNoRuntimeSessions(pool, operation);
    await pool.query({ text: 'ALTER ROLE entity_smoke_runtime LOGIN' });
    await pool.query({ text: 'GRANT rds_iam TO entity_smoke_runtime' });
  }
  if (operation === "revoke-runtime") await requireNoRuntimeSessions(pool, operation);
  const state = await pool.query<{ can_login: boolean; iam_member: boolean }>({
    text: "SELECT rolcanlogin AS can_login, pg_has_role(rolname, 'rds_iam', 'member') AS iam_member FROM pg_roles WHERE rolname = $1",
    values: [entitySmokeRuntimeUsername],
  });
  const expected = operation === "restore-runtime";
  if (state.rows.length !== 1 || state.rows[0]?.can_login !== expected || state.rows[0]?.iam_member !== expected) {
    throw entitySmokeDependencyStateError(operation, "access-state", "not-confirmed");
  }
}

async function requireNoRuntimeSessions(pool: PostgreSqlConnectionPool, operation: "revoke-runtime" | "restore-runtime"): Promise<void> {
  const sessions = await pool.query({ text: "SELECT 1 FROM pg_stat_activity WHERE usename = $1 AND pid <> pg_backend_pid()", values: [entitySmokeRuntimeUsername] });
  if (sessions.rows.length !== 0) throw entitySmokeDependencyStateError(operation, "sessions", "not-confirmed");
}

async function observePermissions(pool: PostgreSqlConnectionPool, database: string): Promise<void> {
  await requireBoundedExistingRole(pool, { username: entitySmokeRuntimeUsername }, { requireLogin: true });
  await requireBoundedExistingRole(pool, { username: entitySmokeMigrationUsername }, { requireLogin: true });
  const client = await pool.connect();
  let failed = false;
  try {
    await client.query({ text: "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY" });
    await client.query({ text: "SET LOCAL statement_timeout = '30000ms'" });
    // Resolving the fixed table names requires owner-schema access. Observe
    // explicit runtime privileges as the owner, never by inheriting its rights.
    await client.query({ text: 'SET LOCAL ROLE entity_smoke_migration' });
    const observed = await client.query<{ allowed: boolean }>({
      text: "SELECT has_schema_privilege($1, $2, 'USAGE') AND NOT has_schema_privilege($1, $2, 'CREATE') AND NOT has_database_privilege($1, $3, 'CREATE') AND has_table_privilege($1, 'entity_smoke.test_entity', 'SELECT') AND has_table_privilege($1, 'entity_smoke.test_entity', 'INSERT') AND has_table_privilege($1, 'entity_smoke.test_entity', 'UPDATE') AND NOT has_table_privilege($1, 'entity_smoke.test_entity', 'DELETE') AND NOT has_table_privilege($1, 'entity_smoke.test_entity', 'TRUNCATE') AND NOT has_table_privilege($1, 'entity_smoke.platform_migration_history', 'INSERT, UPDATE, DELETE') AS allowed",
      values: [entitySmokeRuntimeUsername, entitySmokeSchema, database],
    });
    const memberships = await client.query({ text: "SELECT 1 FROM pg_auth_members m JOIN pg_roles member ON member.oid = m.member JOIN pg_roles role ON role.oid = m.roleid WHERE member.rolname = ANY($1::text[]) AND role.rolname <> 'rds_iam'", values: [[entitySmokeRuntimeUsername, entitySmokeMigrationUsername]] });
    if (observed.rows.length !== 1) throw entitySmokeDependencyStateError("observe-permissions", "privileges", "count-mismatch");
    if (observed.rows[0]?.allowed !== true) throw entitySmokeDependencyStateError("observe-permissions", "privileges", "not-confirmed");
    if (memberships.rows.length !== 0) throw entitySmokeDependencyStateError("observe-permissions", "memberships", "not-confirmed");
  } catch (cause) { failed = true; throw cause; }
  finally {
    try { await client.query({ text: "ROLLBACK" }); }
    catch (cause) {
      if (!failed) throw cause;
      reportEntitySmokeFailure("administration", "not-assessed", cause);
    } finally { client.release(); }
  }
}

/** A separate administrative observer, never a migration replay. The caller
 * must first establish that its earlier migration task has stopped and retain
 * this fresh task's receipt before deciding whether a new submission is safe. */
async function observeMigrationState(pool: PostgreSqlConnectionPool): Promise<AdministrationResult> {
  const client = await pool.connect();
  let failed = false;
  const rejected = (field: Parameters<typeof entitySmokeDependencyStateError>[1], condition: Parameters<typeof entitySmokeDependencyStateError>[2]) => entitySmokeDependencyStateError("observe-migration-state", field, condition);
  try {
    await client.query({ text: "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY" });
    await client.query({ text: "SET LOCAL statement_timeout = '30000ms'" });
    // Use the actual adapter migration-lock key, not a target-local imitation.
    const lock = await client.query<{ acquired: boolean }>({ text: "SELECT pg_try_advisory_xact_lock(hashtext($1)) AS acquired", values: ["kanbien-postgresql-migration:entity_smoke"] });
    if (lock.rows.length !== 1) throw rejected("migration-lock", "count-mismatch");
    if (lock.rows[0]?.acquired === false) throw rejected("migration-lock", "already-running");
    if (lock.rows[0]?.acquired !== true) throw rejected("migration-lock", "not-confirmed");
    await client.query({ text: 'SET LOCAL ROLE entity_smoke_migration' });
    const tables = await client.query<{ history: string | null; entity: string | null; index: string | null }>({
      text: "SELECT to_regclass($1)::text AS history, to_regclass($2)::text AS entity, to_regclass($3)::text AS index",
      values: ["entity_smoke.platform_migration_history", "entity_smoke.test_entity", "entity_smoke.test_entity_status_created_at_idx"],
    });
    const state = tables.rows[0];
    if (tables.rows.length !== 1 || state === undefined || [state.history, state.entity, state.index].some(value => value !== null && typeof value !== "string")) throw rejected("table-state", "not-confirmed");
    if (state.history === null) {
      if (state.entity !== null || state.index !== null) throw rejected("table-state", "mismatch");
      return "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED";
    }
    const history = await client.query<{ migration_id: string; checksum: string }>({ text: 'SELECT migration_id, checksum FROM "entity_smoke".platform_migration_history ORDER BY migration_id ASC' });
    if (history.rows.length === 0) {
      if (state.entity !== null || state.index !== null) throw rejected("table-state", "mismatch");
      return "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED";
    }
    if (history.rows.length !== 1) throw rejected("history-count", "count-mismatch");
    const migration = entitySmokeMigrationManifest().migrations[0];
    if (history.rows[0]?.migration_id !== migration.id) throw rejected("history-id", "mismatch");
    if (history.rows[0]?.checksum !== migration.checksum) throw rejected("history-checksum", "mismatch");
    if (state.entity === null || state.index === null) throw rejected("table-state", "missing");
    return "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED";
  } catch (cause) {
    failed = true;
    throw cause;
  } finally {
    // Always close the read-only snapshot and release its advisory lock. A
    // failed rollback is an observation failure, not an accepted receipt.
    try { await client.query({ text: "ROLLBACK" }); }
    catch (cause) {
      if (!failed) throw cause;
      reportEntitySmokeFailure("administration", "not-assessed", cause);
    }
    finally { client.release(); }
  }
}

