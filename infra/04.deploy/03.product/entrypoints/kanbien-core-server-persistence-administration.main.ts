// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-administration
//   version: 2
//   status: draft
//   created_on: "2026-10-25"
//   updated_on: "2026-10-31"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Execute the explicitly administrative PostgreSQL role, grant, rotation, revocation, and effective-access operations outside ordinary migrations.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import {
  createNodePostgreSqlConnectionPool,
  postgreSqlMigrationChecksum,
  postgreSqlPersistenceFoundationMigration,
  postgreSqlPersistenceConfiguration,
  type PostgreSqlConnectionPool,
  postgreSqlPersistenceOperationError,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { restoreRuntimeIamAccess, revokeRuntimeAccess } from "./kanbien-core-server-persistence-runtime-credential";
import { ensureBoundedLoginRole, ensureRdsIamAuthentication, type PostgreSqlLoginIdentity } from "./kanbien-core-server-persistence-role-credential";
import { persistenceAdministrationConfigurationResult, persistenceAdministratorCredentialBindings, persistenceCertificateAuthorityResult, persistenceTaskDiagnosticFields, persistenceConfigurationResult, persistenceCredentialsResult } from "./kanbien-core-server-persistence-configuration";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { persistenceIamAuthenticationResult, type PersistenceIamAuthentication } from "./kanbien-core-server-persistence-iam-authentication";
import { kanbienCoreServerPersistenceAcceptanceMigration } from "./kanbien-core-server-persistence-postgresql";
import { AdministrationObservation, PersistenceTaskObservations, type AdministrationPredicateDetail, type PersistenceTaskDiagnosticOptions } from "./kanbien-core-server-persistence-operation-diagnostics";

type Identity = PostgreSqlLoginIdentity;
type MigrationStateObservation = "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED" | "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED";

/**
 * This entrypoint is deliberately the only core-persistence program that may
 * create roles, transfer ownership, or grant/revoke the
 * runtime role's database access. Ordinary migrations receive only the
 * bounded schema-owner identity and cannot invoke these operations.
 */
export async function runKanbienCoreServerPersistenceAdministration(env: NodeJS.ProcessEnv = process.env, diagnostics?: PersistenceTaskDiagnosticOptions): Promise<void> {
  const observations = new PersistenceTaskObservations("administration", diagnostics);
  const observer = observations.options;
  const observation = new AdministrationObservation("administration", observer);
  return observation.runAsync(async () => {
  observation.location("configuration", "configuration");
  const parsed = persistenceConfigurationResult(env, "administration");
  if (!parsed.ok) return rejected("PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID", parsed.error.diagnostic, undefined, observations, observation);
  const configuration = parsed.value;
  const credentials = persistenceCredentialsResult(env[persistenceAdministratorCredentialBindings["administrator.credentials"]]);
  if (!credentials.ok) return rejected("PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID", credentials.error.diagnostic, undefined, observations, observation);
  const administrator = credentials.value;
  const preflight = persistenceAdministrationConfigurationResult(env, administrator.username);
  const authority = persistenceCertificateAuthorityResult(env);
  if (!preflight.ok || !authority.ok) {
    // An invalid runtime identity is already a generic configuration failure.
    // Retain that precedence while explaining its IAM predicates (which cannot
    // construct a signer on this rejected identity).
    const authentication = env["PERSISTENCE_ADMINISTRATION_OPERATION"] === "prove-effective-privilege" && !preflight.ok
      && preflight.error.issues.some(({ setting }) => setting === "runtime.username")
      ? persistenceIamAuthenticationResult(env, configuration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME") : undefined;
    return rejected("PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID", authentication?.ok === false ? authentication.error.diagnostic
      : !authority.ok ? authority.error.diagnostic : !preflight.ok ? preflight.error.diagnostic : undefined, undefined, observations, observation);
  }
  const { migration, runtime, operation } = preflight.value;
  const certificateAuthority = authority.value;
  // Only this operation authenticates as the runtime identity. Validate before
  // either pool, without requiring IAM for administrator-only operations.
  observation.location("authentication-preflight");
  const authentication = operation === "prove-effective-privilege"
    ? persistenceIamAuthenticationResult(env, configuration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME") : undefined;
  if (authentication?.ok === false) return rejected("PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED", authentication.error.diagnostic, undefined, observations, observation);
  observation.location("pool-construction");
  const pool = createNodePostgreSqlConnectionPool(configuration, { ...administrator, certificateAuthority });
  try {
    observation.location("task-body");
    if (operation === "bootstrap-identities") {
      await bootstrapIdentities(pool, configuration.database, configuration.schema, migration, runtime, observer);
      return accepted("PERSISTENCE_ADMINISTRATION_IDENTITIES_BOOTSTRAPPED", observations, observation);
    }
    if (operation === "grant-runtime-application-access") {
      await grantRuntimeApplicationAccess(pool, configuration.schema, migration.username, runtime.username, observer);
      return accepted("PERSISTENCE_RUNTIME_APPLICATION_ACCESS_GRANTED", observations, observation);
    }
    if (operation === "confirm-runtime-iam-access") {
      await ensureBoundedLoginRole(pool, runtime, observer);
      await ensureRdsIamAuthentication(pool, runtime, observer);
      return accepted("PERSISTENCE_RUNTIME_IAM_ACCESS_CONFIRMED", observations, observation);
    }
    if (operation === "revoke-runtime") {
      await revokeRuntimeAccess(pool, runtime.username, observer);
      return accepted("PERSISTENCE_RUNTIME_IAM_ACCESS_REVOKED", observations, observation);
    }
    if (operation === "restore-runtime") {
      await restoreRuntimeIamAccess(pool, runtime.username, observer);
      return accepted("PERSISTENCE_RUNTIME_IAM_ACCESS_RESTORED", observations, observation);
    }
    if (operation === "observe-migration-state") {
      return accepted(await observeMigrationState(pool, configuration.schema, migration.username, observer), observations, observation);
    }
    if (authentication?.ok !== true) throw observation.rejected(new Error("PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED"), "member", "not-true");
    await proveRuntimePrivilege(configuration, authentication.value, certificateAuthority, observer);
    return accepted("PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN", observations, observation);
  } catch (error) {
    observation.failed(error);
    observation.location("failure-projection");
    const observed = postgreSqlPersistenceOperationError("administration", error);
    return rejected(administrationFailureCode(error), observed.diagnosticRecord, observed.relatedDiagnosticRecords, observations, observation);
  } finally {
    const restore = observation.checkpoint();
    observation.location("pool-end");
    await pool.end();
    restore();
  }
  }).catch((cause: unknown) => { observations.publishUncaught(); throw cause; });
}

async function bootstrapIdentities(
  pool: PostgreSqlConnectionPool,
  databaseName: string,
  schemaName: string,
  migration: Identity,
  runtime: Identity,
  diagnostics?: PersistenceTaskDiagnosticOptions,
): Promise<void> {
  const observation = new AdministrationObservation("bootstrap-identities", diagnostics);
  return observation.runAsync(async () => {
  const database = quotedIdentifier(databaseName, diagnostics);
  const schema = quotedIdentifier(schemaName, diagnostics);
  const migrationRole = quotedIdentifier(migration.username, diagnostics);
  const runtimeRole = quotedIdentifier(runtime.username, diagnostics);
  let stage = "identity-boundary";
  try {
    observation.location("identity-boundary");
    await ensureBoundedLoginRole(pool, migration, diagnostics);
    await ensureBoundedLoginRole(pool, runtime, diagnostics);
    stage = "iam-membership";
    observation.location("iam-membership");
    await ensureRdsIamAuthentication(pool, migration, diagnostics);
    await ensureRdsIamAuthentication(pool, runtime, diagnostics);
    stage = "database-access";
    observation.location("database-access", undefined, 0);
    await pool.query({ text: `REVOKE ALL PRIVILEGES ON DATABASE ${database} FROM ${runtimeRole}` });
    observation.location("database-access", undefined, 1);
    await pool.query({ text: `GRANT CONNECT ON DATABASE ${database} TO ${migrationRole}, ${runtimeRole}` });
    observation.location("database-access", undefined, 2);
    await pool.query({ text: `GRANT CREATE ON DATABASE ${database} TO ${migrationRole}` });
    stage = "schema-ownership";
    observation.location("schema-ownership");
    await bootstrapMigrationOwnedSchema(pool, schemaName, migration.username, runtime.username, diagnostics);
  } catch (error) {
    observation.failed(error);
    observation.location("failure-projection", "provider-code");
    if (error instanceof Error && error.message.startsWith("PERSISTENCE_ADMINISTRATION_BOOTSTRAP_")) throw observation.retained(error);
    throw observation.retained(new Error(`PERSISTENCE_ADMINISTRATION_BOOTSTRAP_${stage.toUpperCase().replace(/-/g, "_")}_${providerCode(error) ?? "NOT_CONFIRMED"}`, { cause: error }));
  }
  });
}

async function bootstrapMigrationOwnedSchema(pool: PostgreSqlConnectionPool, schemaName: string, migrationUsername: string, runtimeUsername: string, diagnostics?: PersistenceTaskDiagnosticOptions): Promise<void> {
  const observation = new AdministrationObservation("schema-bootstrap", diagnostics);
  return observation.runAsync(async () => {
  const schema = quotedIdentifier(schemaName, diagnostics);
  const migration = quotedIdentifier(migrationUsername, diagnostics);
  const runtime = quotedIdentifier(runtimeUsername, diagnostics);
  let stage = "transaction";
  observation.location("begin");
  await pool.query({ text: "BEGIN" });
  try {
    stage = "create-schema";
    observation.location("create-schema");
    await pool.query({ text: `CREATE SCHEMA IF NOT EXISTS ${schema}` });
    stage = "migration-history";
    observation.location("migration-history");
    await pool.query({ text: `CREATE TABLE IF NOT EXISTS ${schema}."platform_migration_history" (migration_id text PRIMARY KEY, checksum text NOT NULL, tool_version text NOT NULL, applied_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP)` });
    stage = "relation-ownership";
    observation.location("relation-ownership");
    await pool.query({ text: `GRANT USAGE, CREATE ON SCHEMA ${schema} TO ${migration}` });
    await transferRelationOwnership(pool, schemaName, migrationUsername, diagnostics);
    await pool.query({ text: `ALTER SCHEMA ${schema} OWNER TO ${migration}` });
    // The administrator explicitly assumes only the bounded schema-owner role
    // for post-bootstrap object policy. The server never receives structural
    // ownership or database-wide administration privileges.
    observation.location("set-local-role");
    await pool.query({ text: `SET LOCAL ROLE ${migration}` });
    stage = "runtime-boundary";
    observation.location("runtime-boundary", undefined, 0);
    await pool.query({ text: `REVOKE ALL ON SCHEMA ${schema} FROM ${runtime}` });
    observation.location("runtime-boundary", undefined, 1);
    await pool.query({ text: `GRANT USAGE ON SCHEMA ${schema} TO ${runtime}` });
    observation.location("runtime-boundary", undefined, 2);
    await pool.query({ text: `REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA ${schema} FROM ${runtime}` });
    observation.location("runtime-boundary", undefined, 3);
    await pool.query({ text: `REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ${schema} FROM ${runtime}` });
    observation.location("runtime-boundary", undefined, 4);
    await pool.query({ text: `REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA ${schema} FROM ${runtime}` });
    // Do not set broad runtime default privileges. Each future migration must
    // grant only the operations needed by the object it introduces; this keeps
    // migration history and future administrative relations non-writable.
    observation.location("runtime-boundary", undefined, 5);
    await pool.query({ text: `ALTER DEFAULT PRIVILEGES IN SCHEMA ${schema} REVOKE ALL ON TABLES FROM ${runtime}` });
    observation.location("runtime-boundary", undefined, 6);
    await pool.query({ text: `ALTER DEFAULT PRIVILEGES IN SCHEMA ${schema} REVOKE ALL ON SEQUENCES FROM ${runtime}` });
    observation.location("runtime-boundary", undefined, 7);
    await pool.query({ text: `ALTER DEFAULT PRIVILEGES IN SCHEMA ${schema} REVOKE EXECUTE ON FUNCTIONS FROM ${runtime}` });
    observation.location("commit");
    await pool.query({ text: "COMMIT" });
  } catch (error) {
    observation.failed(error);
    try { await pool.query({ text: "ROLLBACK" }); } catch (cause) { observeAdministrationRollback(diagnostics, "schema-bootstrap", cause); }
    observation.location("failure-projection", "provider-code");
    throw observation.retained(new Error(`PERSISTENCE_ADMINISTRATION_BOOTSTRAP_SCHEMA_${stage.toUpperCase().replace(/-/g, "_")}_${providerCode(error) ?? "NOT_CONFIRMED"}`, { cause: error }));
  }
  });
}

async function transferRelationOwnership(pool: PostgreSqlConnectionPool, schemaName: string, owner: string, diagnostics?: PersistenceTaskDiagnosticOptions): Promise<void> {
  const observation = new AdministrationObservation("relation-ownership", diagnostics);
  return observation.runAsync(async () => {
  const schema = quotedIdentifier(schemaName, diagnostics);
  const ownerRole = quotedIdentifier(owner, diagnostics);
  observation.location("relation-query");
  const relations = await pool.query<{ readonly name: string; readonly kind: string }>({
    text: "SELECT c.relname AS name, c.relkind AS kind FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = $1 AND c.relkind IN ('r', 'p', 'v', 'm', 'S')",
    values: [schemaName],
  });
  let ordinal = 0;
  observation.location("relation-traversal");
  for (const relation of relations.rows) {
    const name = observation.at("relation-traversal", "relation-name", () => quotedIdentifier(relation.name, diagnostics), ordinal);
    const command = observation.at("relation-traversal", "relation-kind", () => relation.kind === "S" ? "ALTER SEQUENCE" : relation.kind === "v" ? "ALTER VIEW" : relation.kind === "m" ? "ALTER MATERIALIZED VIEW" : "ALTER TABLE", ordinal);
    observation.location("relation-ownership", undefined, ordinal++);
    await pool.query({ text: `${command} ${schema}.${name} OWNER TO ${ownerRole}` });
  }
  observation.location("function-count-query");
  const functions = await pool.query<{ readonly count: string }>({ text: "SELECT COUNT(*)::text AS count FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = $1", values: [schemaName] });
  observation.location("function-count-projection", "function-count");
  if (functions.rows[0]?.count !== "0") throw observation.rejected(new Error("PERSISTENCE_ADMINISTRATION_FUNCTION_OWNERSHIP_REVIEW_REQUIRED"), "function-count", "not-zero");
  });
}

async function grantRuntimeApplicationAccess(pool: PostgreSqlConnectionPool, schemaName: string, migrationUsername: string, runtimeUsername: string, diagnostics?: PersistenceTaskDiagnosticOptions): Promise<void> {
  const observation = new AdministrationObservation("application-access", diagnostics);
  return observation.runAsync(async () => {
  const schema = quotedIdentifier(schemaName, diagnostics);
  const migration = quotedIdentifier(migrationUsername, diagnostics);
  const runtime = quotedIdentifier(runtimeUsername, diagnostics);
  const applicationTable = `${schema}."core_server_persistence_acceptance"`;
  observation.location("begin");
  await pool.query({ text: "BEGIN" });
  try {
    observation.location("set-local-role");
    await pool.query({ text: `SET LOCAL ROLE ${migration}` });
    observation.location("grant-runtime", undefined, 0);
    await pool.query({ text: `REVOKE ALL PRIVILEGES ON ${schema}."platform_migration_history" FROM ${runtime}` });
    observation.location("grant-runtime", undefined, 1);
    await pool.query({ text: `REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ${schema} FROM ${runtime}` });
    observation.location("grant-runtime", undefined, 2);
    await pool.query({ text: `REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA ${schema} FROM ${runtime}` });
    observation.location("grant-runtime", undefined, 3);
    await pool.query({ text: `GRANT SELECT, INSERT, UPDATE, DELETE ON ${applicationTable} TO ${runtime}` });
    observation.location("commit");
    await pool.query({ text: "COMMIT" });
  } catch (error) {
    observation.failed(error);
    try { await pool.query({ text: "ROLLBACK" }); } catch (cause) { observeAdministrationRollback(diagnostics, "application-access", cause); }
    throw observation.retained(error);
  }
  });
}

/**
 * Observe, but never repair, migration history after an unsuccessful or
 * interrupted controller. The migration runner is transaction-bound, so an
 * empty reviewed manifest is the sole state that permits a new submission.
 * A complete checksum-matching history is accepted only as evidence that the
 * prior migration already took effect; it never authorises a replay.
 */
async function observeMigrationState(pool: PostgreSqlConnectionPool, schemaName: string, migrationUsername: string, diagnostics?: PersistenceTaskDiagnosticOptions): Promise<MigrationStateObservation> {
  const observation = new AdministrationObservation("migration-state", diagnostics);
  return observation.runAsync(async () => {
  const history = `${quotedIdentifier(schemaName, diagnostics)}."platform_migration_history"`;
  const migration = quotedIdentifier(migrationUsername, diagnostics);
  observation.location("configuration", "schema");
  const foundation = postgreSqlPersistenceFoundationMigration(schemaName);
  const acceptance = kanbienCoreServerPersistenceAcceptanceMigration(schemaName);
  const expected = [
    { id: foundation.id, checksum: foundation.checksum },
    { id: acceptance.id, checksum: postgreSqlMigrationChecksum(acceptance.statements) },
  ];
  observation.location("begin");
  await pool.query({ text: "BEGIN READ ONLY" });
  let observed: { readonly rows: readonly { readonly migration_id: string; readonly checksum: string }[] };
  try {
    // The history is owned by the constrained migration identity. The
    // administrative task assumes that already-governed role only inside a
    // read-only transaction; it neither reuses migration credentials nor gains
    // authority to alter schema state through this observation path.
    observation.location("set-local-role");
    await pool.query({ text: `SET LOCAL ROLE ${migration}` });
    observation.location("history-read");
    observed = await pool.query<{ readonly migration_id: string; readonly checksum: string }>({
      text: `SELECT migration_id, checksum FROM ${history} ORDER BY migration_id ASC`,
    });
    observation.location("rollback");
    await pool.query({ text: "ROLLBACK" });
  } catch (error) {
    observation.failed(error);
    try { await pool.query({ text: "ROLLBACK" }); } catch (cause) { observeAdministrationRollback(diagnostics, "migration-state", cause); }
    throw observation.retained(error);
  }
  observation.location("history-traversal", "migration-count");
  if (observed.rows.length === 0) return "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED";
  let field: AdministrationPredicateDetail["field"] = "migration-count";
  let condition: AdministrationPredicateDetail["condition"] = "count-mismatch";
  let firstRejected: number | undefined, visits = 0;
  const matches = (at: AdministrationPredicateDetail["field"], matched: boolean, ordinal: number): boolean => {
    if (!matched && firstRejected === undefined) { field = at; condition = at === "migration-id" ? "id-mismatch" : "checksum-mismatch"; firstRejected = ordinal; }
    return matched;
  };
  let countMatched = false;
  if (
    (countMatched = observed.rows.length === expected.length)
    && observed.rows.every((row, index) => {
      const ordinal = visits++;
      return matches("migration-id", observation.at("history-traversal", "migration-id", () => row.migration_id === expected[index]?.id, ordinal), ordinal)
        && matches("migration-checksum", observation.at("history-traversal", "migration-checksum", () => row.checksum === expected[index]?.checksum, ordinal), ordinal);
    })
  ) return "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED";
  if (countMatched && firstRejected === undefined) condition = "predicate-rejected";
  throw observation.rejected(new Error("PERSISTENCE_MIGRATION_STATE_REVIEW_REQUIRED"), field, condition, firstRejected);
  });
}

async function proveRuntimePrivilege(
  configuration: ReturnType<typeof configurationFromEnvironment> & {},
  credentials: PersistenceIamAuthentication,
  certificateAuthority: string,
  diagnostics?: PersistenceTaskDiagnosticOptions,
): Promise<void> {
  const observation = new AdministrationObservation("runtime-privilege", diagnostics);
  return observation.runAsync(async () => {
  observation.location("pool-import");
  const { createNodePostgreSqlTokenConnectionPool } = await import("@kanbien/platform-adapter-aws-persistence-postgresql");
  observation.location("pool-construction");
  const pool = createNodePostgreSqlTokenConnectionPool(configuration, { ...credentials, certificateAuthority });
  observation.location("input-projection", "schema");
  const table = `"${configuration.schema}"."core_server_persistence_acceptance"`;
  const history = `"${configuration.schema}"."platform_migration_history"`;
  observation.location("pool-connect");
  const client = await pool.connect();
  try {
    observation.location("begin");
    await client.query({ text: "BEGIN" });
    observation.location("runtime-insert");
    await client.query({ text: `INSERT INTO ${table} (record_id, fact_digest) VALUES ($1, $2) ON CONFLICT (record_id) DO NOTHING`, values: ["core-persistence-privilege-probe", "0".repeat(64)] });
    observation.location("runtime-read");
    const read = await client.query<{ readonly record_id: string }>({ text: `SELECT record_id FROM ${table} WHERE record_id = $1`, values: ["core-persistence-privilege-probe"] });
    observation.location("runtime-read-projection", "read-count");
    if (read.rows.length !== 1) throw observation.rejected(new Error("PERSISTENCE_RUNTIME_DML_NOT_CONFIRMED"), "read-count", "not-one");
    observation.location("rollback");
    await client.query({ text: "ROLLBACK" });
    observation.location("permission-history");
    await expectPermissionDenied(client, `INSERT INTO ${history} (migration_id, checksum, tool_version) VALUES ('runtime-must-not-write-history', '0', 'probe')`, "permission-history", diagnostics);
    observation.location("permission-schema");
    await expectPermissionDenied(client, `CREATE TABLE "${configuration.schema}"."runtime_privilege_probe_must_reject" (id text)`, "permission-schema", diagnostics);
    observation.location("runtime-role-query");
    const roleFacts = await client.query<{ readonly createrole: boolean; readonly createdb: boolean; readonly superuser: boolean }>({ text: "SELECT rolcreaterole AS createrole, rolcreatedb AS createdb, rolsuper AS superuser FROM pg_roles WHERE rolname = current_user" });
    observation.location("runtime-role-projection", "row");
    const facts = roleFacts.rows[0];
    let field: AdministrationPredicateDetail["field"] = "row";
    const readFact = <T>(at: AdministrationPredicateDetail["field"], action: () => T): T => { field = at; return observation.at("runtime-role-projection", at, action); };
    if (facts === undefined || readFact("create-role", () => facts.createrole) || readFact("create-database", () => facts.createdb) || readFact("superuser", () => facts.superuser)) throw observation.rejected(new Error("PERSISTENCE_RUNTIME_ADMINISTRATION_UNEXPECTEDLY_PERMITTED"), field, field === "row" ? "missing" : "truthy");
  } catch (cause) {
    observation.failed(cause);
    throw observation.retained(cause);
  } finally {
    const restore = observation.checkpoint();
    observation.location("client-release");
    client.release();
    observation.location("pool-end");
    await pool.end();
    restore();
  }
  });
}

async function expectPermissionDenied(client: { query(statement: { readonly text: string; readonly values?: readonly unknown[] }): Promise<unknown> }, text: string, phase: "permission-history" | "permission-schema", diagnostics?: PersistenceTaskDiagnosticOptions): Promise<void> {
  const observation = new AdministrationObservation("permission-probe", diagnostics);
  return observation.runAsync(async () => {
  observation.location(phase);
  try { await client.query({ text }); }
  catch (error) {
    observation.location("permission-code", "provider-code");
    try { if (providerCode(error) === "42501") return; }
    catch (cause) {
      const query = new AdministrationObservation("permission-probe", diagnostics);
      query.location(phase); query.failed(error);
      throw cause;
    }
    throw observation.rejected(new Error("PERSISTENCE_RUNTIME_PERMISSION_DENIAL_NOT_CONFIRMED"), "provider-code", "denial-code-mismatch", undefined, error);
  }
  throw observation.rejected(new Error("PERSISTENCE_RUNTIME_PERMISSION_UNEXPECTEDLY_PERMITTED"), "provider-code", "permission-permitted");
  });
}

function configurationFromEnvironment(env: NodeJS.ProcessEnv) {
  const checked = persistenceConfigurationResult(env, "administration");
  return checked.ok ? checked.value : undefined;
}
function text(env: NodeJS.ProcessEnv, key: string): string | undefined { const value = env[key]; return typeof value === "string" && value.trim() !== "" && value.trim() === value ? value : undefined; }
function quotedIdentifier(value: string, diagnostics?: PersistenceTaskDiagnosticOptions): string {
  const observation = new AdministrationObservation("role-identifier", diagnostics);
  return observation.run(() => {
    observation.location("identifier-predicate", "identifier");
    if (!/^[a-z_][a-z0-9_]{0,62}$/.test(value)) throw observation.rejected(new TypeError("PERSISTENCE_ROLE_IDENTIFIER_INVALID"), "identifier", "pattern");
    return `"${value}"`;
  });
}
function providerCode(value: unknown): string | undefined { return typeof value === "object" && value !== null && typeof (value as { readonly code?: unknown }).code === "string" ? (value as { readonly code: string }).code : undefined; }
export function administrationFailureCode(error: unknown): string {
  const message = error instanceof Error ? error.message : undefined;
  if (typeof message === "string" && /^PERSISTENCE_ADMINISTRATION_BOOTSTRAP_[A-Z_]+_(?:[0-9A-Z_]+)$/.test(message)) return message;
  if (
    message === "PERSISTENCE_ROLE_PRIVILEGE_BOUNDARY_NOT_CONFIRMED"
    || message === "PERSISTENCE_RUNTIME_ROLE_MISSING"
    || message === "PERSISTENCE_ROLE_STATE_UNAVAILABLE"
    || message === "PERSISTENCE_ROLE_REACTIVATION_REQUIRES_EXPLICIT_RECOVERY"
    || message === "PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED"
    || message === "PERSISTENCE_RUNTIME_DML_NOT_CONFIRMED"
    || message === "PERSISTENCE_RUNTIME_PERMISSION_DENIAL_NOT_CONFIRMED"
    || message === "PERSISTENCE_RUNTIME_PERMISSION_UNEXPECTEDLY_PERMITTED"
    || message === "PERSISTENCE_RUNTIME_ADMINISTRATION_UNEXPECTEDLY_PERMITTED"
    || message === "PERSISTENCE_MIGRATION_STATE_ALREADY_APPLIED"
    || message === "PERSISTENCE_MIGRATION_STATE_REVIEW_REQUIRED"
    || (typeof message === "string" && /^PERSISTENCE_RUNTIME_(?:REVOCATION|RECOVERY)_[A-Z_]+_NOT_CONFIRMED$/.test(message))
  ) return message;
  const code = providerCode(error);
  return code === "42501" ? "PERSISTENCE_ADMINISTRATION_ACCESS_DENIED" : code === "28P01" ? "PERSISTENCE_ADMINISTRATION_CREDENTIAL_REJECTED" : "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED";
}
function observeAdministrationRollback(diagnostics: PersistenceTaskDiagnosticOptions | undefined, operation: "schema-bootstrap" | "application-access" | "migration-state", cause: unknown): void {
  const observation = new AdministrationObservation(operation, diagnostics);
  observation.location("rollback"); observation.failed(cause);
}
function accepted(code: string, observations: PersistenceTaskObservations, observation?: AdministrationObservation): void { observation?.location("result-projection"); console.log((observations.markSerializationReached(), JSON.stringify({ verdict: "accepted", code }))); observations.markPublished(); }
function rejected(code: string, diagnostic: DiagnosticRecord | undefined, relatedDiagnosticRecords: readonly DiagnosticRecord[] | undefined, observations: PersistenceTaskObservations, observation?: AdministrationObservation): void { observation?.location("result-projection"); console.error((observations.markSerializationReached(), JSON.stringify(observations.failure(code, { ...(diagnostic === undefined ? {} : { diagnosticRecord: diagnostic }), ...(relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords }) })))); observations.markPublished(); process.exitCode = 1; }
if (typeof require !== "undefined" && require.main === module) void runKanbienCoreServerPersistenceAdministration();

