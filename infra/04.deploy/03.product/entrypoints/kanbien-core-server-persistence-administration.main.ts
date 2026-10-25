// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-administration
//   version: 1
//   status: draft
//   created_on: "2026-10-25"
//   updated_on: "2026-10-25"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Execute the explicitly administrative PostgreSQL role, grant, rotation, revocation, and effective-access operations outside ordinary migrations.
//   portability: { class: internal, targets: [kanbien-core-platform] }

import { readFileSync } from "node:fs";
import {
  createNodePostgreSqlConnectionPool,
  postgreSqlPersistenceConfiguration,
  type PostgreSqlConnectionPool,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { revokeRuntimeAccess } from "./kanbien-core-server-persistence-runtime-credential";

type Credentials = { readonly username: string; readonly password: string };
type AdministrationOperation = "bootstrap-identities" | "grant-runtime-application-access" | "rotate-runtime" | "revoke-runtime" | "prove-effective-privilege";

/**
 * This entrypoint is deliberately the only core-persistence program that may
 * create roles, alter passwords, transfer ownership, or grant/revoke the
 * runtime role's database access. Ordinary migrations receive only the
 * bounded schema-owner identity and cannot invoke these operations.
 */
export async function runKanbienCoreServerPersistenceAdministration(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const configuration = configurationFromEnvironment(env);
  const administrator = credentialObject(env["PERSISTENCE_ADMINISTRATOR_CREDENTIALS"]);
  const migration = credentialObject(env["PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS"]);
  const runtime = credentialObject(env["PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS"]);
  const certificateAuthority = certificateAuthorityFromEnvironment(env);
  const operation = administrationOperation(env["PERSISTENCE_ADMINISTRATION_OPERATION"]);
  if (configuration === undefined || administrator === undefined || migration === undefined || runtime === undefined || certificateAuthority === undefined || operation === undefined) {
    return rejected("PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID");
  }
  const pool = createNodePostgreSqlConnectionPool(configuration, { ...administrator, certificateAuthority });
  try {
    if (operation === "bootstrap-identities") {
      await bootstrapIdentities(pool, configuration.database, configuration.schema, migration, runtime);
      return accepted("PERSISTENCE_ADMINISTRATION_IDENTITIES_BOOTSTRAPPED");
    }
    if (operation === "grant-runtime-application-access") {
      await grantRuntimeApplicationAccess(pool, configuration.schema, runtime.username);
      return accepted("PERSISTENCE_RUNTIME_APPLICATION_ACCESS_GRANTED");
    }
    if (operation === "rotate-runtime") {
      await rotateRuntimePassword(pool, runtime);
      return accepted("PERSISTENCE_RUNTIME_CREDENTIAL_ROTATED");
    }
    if (operation === "revoke-runtime") {
      await revokeRuntimeAccess(pool, runtime.username);
      return accepted("PERSISTENCE_RUNTIME_CREDENTIAL_REVOKED");
    }
    await proveRuntimePrivilege(configuration, runtime, certificateAuthority);
    return accepted("PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN");
  } catch {
    return rejected("PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED");
  } finally {
    await pool.end();
  }
}

async function bootstrapIdentities(
  pool: PostgreSqlConnectionPool,
  databaseName: string,
  schemaName: string,
  migration: Credentials,
  runtime: Credentials,
): Promise<void> {
  const database = quotedIdentifier(databaseName);
  const schema = quotedIdentifier(schemaName);
  const migrationRole = quotedIdentifier(migration.username);
  const runtimeRole = quotedIdentifier(runtime.username);
  await ensureLoginRole(pool, migration);
  await ensureLoginRole(pool, runtime);
  await pool.query({ text: `REVOKE ALL PRIVILEGES ON DATABASE ${database} FROM ${runtimeRole}` });
  await pool.query({ text: `GRANT CONNECT ON DATABASE ${database} TO ${migrationRole}, ${runtimeRole}` });
  await pool.query({ text: `CREATE SCHEMA IF NOT EXISTS ${schema} AUTHORIZATION ${migrationRole}` });
  await pool.query({ text: `ALTER SCHEMA ${schema} OWNER TO ${migrationRole}` });
  await pool.query({ text: `GRANT USAGE, CREATE ON SCHEMA ${schema} TO ${migrationRole}` });
  await pool.query({ text: `REVOKE ALL ON SCHEMA ${schema} FROM ${runtimeRole}` });
  await pool.query({ text: `GRANT USAGE ON SCHEMA ${schema} TO ${runtimeRole}` });
  await pool.query({ text: `CREATE TABLE IF NOT EXISTS ${schema}."platform_migration_history" (migration_id text PRIMARY KEY, checksum text NOT NULL, tool_version text NOT NULL, applied_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP)` });
  await transferRelationOwnership(pool, schemaName, migration.username);
  await pool.query({ text: `REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA ${schema} FROM ${runtimeRole}` });
  await pool.query({ text: `REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ${schema} FROM ${runtimeRole}` });
  await pool.query({ text: `REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA ${schema} FROM ${runtimeRole}` });
  // Do not set broad runtime default privileges. Each future migration must
  // grant only the operations needed by the object it introduces; this keeps
  // migration history and future administrative relations non-writable.
  await pool.query({ text: `ALTER DEFAULT PRIVILEGES FOR ROLE ${migrationRole} IN SCHEMA ${schema} REVOKE ALL ON TABLES FROM ${runtimeRole}` });
  await pool.query({ text: `ALTER DEFAULT PRIVILEGES FOR ROLE ${migrationRole} IN SCHEMA ${schema} REVOKE ALL ON SEQUENCES FROM ${runtimeRole}` });
  await pool.query({ text: `ALTER DEFAULT PRIVILEGES FOR ROLE ${migrationRole} IN SCHEMA ${schema} REVOKE EXECUTE ON FUNCTIONS FROM ${runtimeRole}` });
}

async function ensureLoginRole(pool: PostgreSqlConnectionPool, credentials: Credentials): Promise<void> {
  const role = quotedIdentifier(credentials.username);
  const exists = await pool.query<{ readonly exists: boolean }>({ text: "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = $1) AS exists", values: [credentials.username] });
  const password = quotedLiteral(credentials.password);
  await pool.query({ text: exists.rows[0]?.exists === true
    ? `ALTER ROLE ${role} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT PASSWORD ${password}`
    : `CREATE ROLE ${role} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT PASSWORD ${password}` });
}

async function transferRelationOwnership(pool: PostgreSqlConnectionPool, schemaName: string, owner: string): Promise<void> {
  const schema = quotedIdentifier(schemaName);
  const ownerRole = quotedIdentifier(owner);
  const relations = await pool.query<{ readonly name: string; readonly kind: string }>({
    text: "SELECT c.relname AS name, c.relkind AS kind FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = $1 AND c.relkind IN ('r', 'p', 'v', 'm', 'S')",
    values: [schemaName],
  });
  for (const relation of relations.rows) {
    const name = quotedIdentifier(relation.name);
    const command = relation.kind === "S" ? "ALTER SEQUENCE" : relation.kind === "v" ? "ALTER VIEW" : relation.kind === "m" ? "ALTER MATERIALIZED VIEW" : "ALTER TABLE";
    await pool.query({ text: `${command} ${schema}.${name} OWNER TO ${ownerRole}` });
  }
  const functions = await pool.query<{ readonly count: string }>({ text: "SELECT COUNT(*)::text AS count FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = $1", values: [schemaName] });
  if (functions.rows[0]?.count !== "0") throw new Error("PERSISTENCE_ADMINISTRATION_FUNCTION_OWNERSHIP_REVIEW_REQUIRED");
}

async function grantRuntimeApplicationAccess(pool: PostgreSqlConnectionPool, schemaName: string, runtimeUsername: string): Promise<void> {
  const schema = quotedIdentifier(schemaName);
  const runtime = quotedIdentifier(runtimeUsername);
  const applicationTable = `${schema}."core_server_persistence_acceptance"`;
  await pool.query({ text: `REVOKE ALL PRIVILEGES ON ${schema}."platform_migration_history" FROM ${runtime}` });
  await pool.query({ text: `REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ${schema} FROM ${runtime}` });
  await pool.query({ text: `REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA ${schema} FROM ${runtime}` });
  await pool.query({ text: `GRANT SELECT, INSERT, UPDATE, DELETE ON ${applicationTable} TO ${runtime}` });
}

async function rotateRuntimePassword(pool: PostgreSqlConnectionPool, credentials: Credentials): Promise<void> {
  await pool.query({ text: `ALTER ROLE ${quotedIdentifier(credentials.username)} LOGIN PASSWORD ${quotedLiteral(credentials.password)}` });
}

async function proveRuntimePrivilege(
  configuration: ReturnType<typeof configurationFromEnvironment> & {},
  credentials: Credentials,
  certificateAuthority: string,
): Promise<void> {
  const pool = createNodePostgreSqlConnectionPool(configuration, { ...credentials, certificateAuthority });
  const table = `"${configuration.schema}"."core_server_persistence_acceptance"`;
  const history = `"${configuration.schema}"."platform_migration_history"`;
  const client = await pool.connect();
  try {
    await client.query({ text: "BEGIN" });
    await client.query({ text: `INSERT INTO ${table} (record_id, fact_digest) VALUES ($1, $2) ON CONFLICT (record_id) DO NOTHING`, values: ["core-persistence-privilege-probe", "0".repeat(64)] });
    const read = await client.query<{ readonly record_id: string }>({ text: `SELECT record_id FROM ${table} WHERE record_id = $1`, values: ["core-persistence-privilege-probe"] });
    if (read.rows.length !== 1) throw new Error("PERSISTENCE_RUNTIME_DML_NOT_CONFIRMED");
    await client.query({ text: "ROLLBACK" });
    await expectPermissionDenied(client, `INSERT INTO ${history} (migration_id, checksum, tool_version) VALUES ('runtime-must-not-write-history', '0', 'probe')`);
    await expectPermissionDenied(client, `CREATE TABLE "${configuration.schema}"."runtime_privilege_probe_must_reject" (id text)`);
    const roleFacts = await client.query<{ readonly createrole: boolean; readonly createdb: boolean; readonly superuser: boolean }>({ text: "SELECT rolcreaterole AS createrole, rolcreatedb AS createdb, rolsuper AS superuser FROM pg_roles WHERE rolname = current_user" });
    const facts = roleFacts.rows[0];
    if (facts === undefined || facts.createrole || facts.createdb || facts.superuser) throw new Error("PERSISTENCE_RUNTIME_ADMINISTRATION_UNEXPECTEDLY_PERMITTED");
  } finally {
    client.release();
    await pool.end();
  }
}

async function expectPermissionDenied(client: { query(statement: { readonly text: string; readonly values?: readonly unknown[] }): Promise<unknown> }, text: string): Promise<void> {
  try { await client.query({ text }); }
  catch (error) { if (providerCode(error) === "42501") return; throw new Error("PERSISTENCE_RUNTIME_PERMISSION_DENIAL_NOT_CONFIRMED"); }
  throw new Error("PERSISTENCE_RUNTIME_PERMISSION_UNEXPECTEDLY_PERMITTED");
}

function configurationFromEnvironment(env: NodeJS.ProcessEnv) {
  const host = text(env, "PERSISTENCE_POSTGRES_HOST"), database = text(env, "PERSISTENCE_POSTGRES_DATABASE"), schema = text(env, "PERSISTENCE_POSTGRES_SCHEMA"), reference = text(env, "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE"), port = text(env, "PERSISTENCE_POSTGRES_PORT");
  if (host === undefined || database === undefined || schema === undefined || reference === undefined || port === undefined || !/^\d+$/.test(port)) return undefined;
  const checked = postgreSqlPersistenceConfiguration({ host, database, schema, runtimeCredentialSecretReference: reference, port: Number(port), maximumPoolSize: 1, connectionTimeoutMs: 5_000, idleTimeoutMs: 10_000, statementTimeoutMs: 240_000, tls: { mode: "verify-full", certificateAuthoritySource: "injected" } });
  return checked.ok ? checked.value : undefined;
}
function administrationOperation(value: unknown): AdministrationOperation | undefined {
  return value === undefined || value === "bootstrap-identities" ? "bootstrap-identities" : value === "grant-runtime-application-access" || value === "rotate-runtime" || value === "revoke-runtime" || value === "prove-effective-privilege" ? value : undefined;
}
function certificateAuthorityFromEnvironment(env: NodeJS.ProcessEnv): string | undefined { const path = text(env, "PERSISTENCE_POSTGRES_CA_PATH"); try { return path?.startsWith("/app/assets/") ? readFileSync(path, "utf8") : undefined; } catch { return undefined; } }
function text(env: NodeJS.ProcessEnv, key: string): string | undefined { const value = env[key]; return typeof value === "string" && value.trim() !== "" && value.trim() === value ? value : undefined; }
function credentialObject(value: unknown): Credentials | undefined { try { const parsed: unknown = typeof value === "string" ? JSON.parse(value) : undefined; if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return undefined; const username = (parsed as { username?: unknown }).username, password = (parsed as { password?: unknown }).password; return typeof username === "string" && /^[a-z_][a-z0-9_]{0,62}$/.test(username) && typeof password === "string" && password.length > 0 ? { username, password } : undefined; } catch { return undefined; } }
function quotedIdentifier(value: string): string { if (!/^[a-z_][a-z0-9_]{0,62}$/.test(value)) throw new TypeError("PERSISTENCE_ROLE_IDENTIFIER_INVALID"); return `"${value}"`; }
function quotedLiteral(value: string): string { if (value.length === 0 || value.includes("\u0000")) throw new TypeError("PERSISTENCE_CREDENTIAL_INVALID"); return `'${value.replaceAll("'", "''")}'`; }
function providerCode(value: unknown): string | undefined { return typeof value === "object" && value !== null && typeof (value as { readonly code?: unknown }).code === "string" ? (value as { readonly code: string }).code : undefined; }
function accepted(code: string): void { console.log(JSON.stringify({ verdict: "accepted", code })); }
function rejected(code: string): void { console.error(JSON.stringify({ verdict: "rejected", code })); process.exitCode = 1; }
if (typeof require !== "undefined" && require.main === module) void runKanbienCoreServerPersistenceAdministration();

