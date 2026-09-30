// Target-only helper for the bounded relational smoke tasks. It accepts only
// ECS-injected secret/configuration values and never emits any of their fields.

import { readFileSync } from "node:fs";
import {
  createNodePostgreSqlConnectionPool,
  postgreSqlPersistenceConfiguration,
  type PostgreSqlConnectionCredentials,
  type PostgreSqlConnectionPool,
  type PostgreSqlPersistenceConfiguration,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";

export interface RelationalTaskSecret {
  readonly username: string;
  readonly password: string;
  readonly host: string;
  readonly port: number;
}

/** A managed RDS master secret may deliberately contain credentials only. */
export interface RelationalTaskCredentials {
  readonly username: string;
  readonly password: string;
}

export interface RelationalTaskConfiguration {
  readonly database: "platformsmoke";
  readonly schema: "platform_smoke";
  readonly tls: "verify-full";
  readonly runtimeSecretArn: string;
  readonly migrationSecretArn: string;
}

export type BootstrapFailureCategory =
  | "bootstrap-certificate-authority-unavailable"
  | "bootstrap-database-authentication-failure"
  | "bootstrap-database-authorization-failure"
  | "bootstrap-database-connectivity-failure"
  | "bootstrap-database-tls-failure"
  | "bootstrap-input-validation-failure"
  | "bootstrap-password-quotation-failure"
  | "bootstrap-role-provisioning-failure"
  | "bootstrap-database-grant-failure"
  | "bootstrap-schema-provisioning-failure"
  | "bootstrap-schema-grant-failure"
  | "bootstrap-workload-failure-unclassified";

export function secretFromEnvironment(name: string): RelationalTaskSecret {
  const candidate = secretObjectFromEnvironment(name);
  const credentials = credentialsFromSecret(candidate);
  const host = stringField(candidate, "host");
  const port = numberField(candidate, "port");
  if (!/^[A-Za-z0-9.-]{1,253}$/.test(host) || !Number.isInteger(port) || port < 1 || port > 65_535) {
    throw new Error("RELATIONAL_TASK_SECRET_INVALID");
  }
  return { ...credentials, host, port };
}

export function credentialsFromEnvironment(name: string): RelationalTaskCredentials {
  return credentialsFromSecret(secretObjectFromEnvironment(name));
}

export function configurationFromEnvironment(): RelationalTaskConfiguration {
  const raw = process.env["RELATIONAL_CONFIG_JSON"];
  if (raw === undefined) throw new Error("RELATIONAL_TASK_CONFIGURATION_MISSING");
  let candidate: unknown;
  try {
    candidate = JSON.parse(raw);
  } catch {
    throw new Error("RELATIONAL_TASK_CONFIGURATION_INVALID");
  }
  if (!isRecord(candidate)) throw new Error("RELATIONAL_TASK_CONFIGURATION_INVALID");
  const database = stringField(candidate, "database");
  const schema = stringField(candidate, "schema");
  const tls = stringField(candidate, "tls");
  const runtimeSecretArn = stringField(candidate, "runtime_secret_arn");
  const migrationSecretArn = stringField(candidate, "migration_secret_arn");
  if (database !== "platformsmoke" || schema !== "platform_smoke" || tls !== "verify-full" || !secretArn(runtimeSecretArn) || !secretArn(migrationSecretArn)) {
    throw new Error("RELATIONAL_TASK_CONFIGURATION_INVALID");
  }
  return { database, schema, tls, runtimeSecretArn, migrationSecretArn };
}

export function connectionConfiguration(secret: RelationalTaskSecret, reference: string, schema = "platform_smoke"): PostgreSqlPersistenceConfiguration {
  const result = postgreSqlPersistenceConfiguration({
    host: secret.host,
    port: secret.port,
    // The database is a reviewed target configuration, not a credential
    // property. AWS SecretTargetAttachment does not guarantee a dbname field.
    database: "platformsmoke",
    schema,
    runtimeCredentialSecretReference: reference,
    maximumPoolSize: 2,
    connectionTimeoutMs: 10_000,
    idleTimeoutMs: 10_000,
    statementTimeoutMs: 15_000,
    tls: { mode: "verify-full", certificateAuthoritySource: "injected" },
  });
  if (!result.ok) throw new Error("RELATIONAL_TASK_CONFIGURATION_INVALID");
  return result.value;
}

export function connectionPool(secret: RelationalTaskSecret, reference: string, schema = "platform_smoke"): PostgreSqlConnectionPool {
  validateLocalQualificationBinding(secret);
  const credentials: PostgreSqlConnectionCredentials = {
    username: secret.username,
    password: secret.password,
    certificateAuthority: relationalCertificateAuthority(),
  };
  return createNodePostgreSqlConnectionPool(connectionConfiguration(secret, reference, schema), credentials);
}

function relationalCertificateAuthority(): string {
  // The AWS RDS chain is public configuration, not a credential. Keeping the
  // target-region bundle inside the immutable image avoids weakening TLS when
  // a distroless image lacks an operating-system trust-store entry for RDS.
  try {
    if (process.env["RELATIONAL_TLS_CA_MODE"] === "local-qualification-v1") {
      const certificate = readFileSync("/run/release-control/ca.crt", "utf8");
      if (certificate.length > 16_384 || !certificate.startsWith("-----BEGIN CERTIFICATE-----")) {
        throw new Error("RELATIONAL_TASK_CERTIFICATE_AUTHORITY_UNAVAILABLE");
      }
      return certificate;
    }
    return readFileSync("/app/assets/rds-eu-west-1-bundle.crt", "utf8");
  } catch {
    throw new Error("RELATIONAL_TASK_CERTIFICATE_AUTHORITY_UNAVAILABLE");
  }
}

// This explicit local binding changes only the trusted CA input, never TLS
// verification. Target descriptors are checked to forbid these local fields.
// The runner binds the fixed CA mount and isolated dependency to its receipt.
function validateLocalQualificationBinding(secret: RelationalTaskSecret): void {
  const mode = process.env["RELATIONAL_TLS_CA_MODE"];
  const attempt = process.env["RELATIONAL_LOCAL_QUALIFICATION_ID"];
  if (mode === undefined && attempt === undefined) return;
  if (mode !== "local-qualification-v1" || attempt === undefined || !/^[a-f0-9]{32}$/.test(attempt)
      || secret.host !== "release-control-postgresql" || secret.port !== 5432) {
    throw new Error("RELATIONAL_TASK_CONFIGURATION_INVALID");
  }
}

export async function closePool(pool: PostgreSqlConnectionPool | undefined): Promise<void> {
  if (pool === undefined) return;
  try {
    await pool.end();
  } catch {
    // A process is already exiting; diagnostics remain intentionally safe.
  }
}

export function writeOutcome(operation: string, outcome: "succeeded" | "failed", failureCategory?: BootstrapFailureCategory): void {
  const fields = outcome === "failed" && failureCategory !== undefined
    ? { outcome, failure_category: failureCategory }
    : { outcome };
  console.log(JSON.stringify({ level: outcome === "succeeded" ? "info" : "error", message: "kanbien-platform.relational-smoke." + operation, fields }));
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function secretObjectFromEnvironment(name: string): Readonly<Record<string, unknown>> {
  const raw = process.env[name];
  if (raw === undefined) throw new Error("RELATIONAL_TASK_SECRET_MISSING");
  let candidate: unknown;
  try {
    candidate = JSON.parse(raw);
  } catch {
    throw new Error("RELATIONAL_TASK_SECRET_INVALID");
  }
  if (!isRecord(candidate)) throw new Error("RELATIONAL_TASK_SECRET_INVALID");
  return candidate;
}

function credentialsFromSecret(candidate: Readonly<Record<string, unknown>>): RelationalTaskCredentials {
  const username = stringField(candidate, "username");
  const password = stringField(candidate, "password");
  if (!/^[A-Za-z0-9._-]{1,63}$/.test(username) || password.length < 1) {
    throw new Error("RELATIONAL_TASK_SECRET_INVALID");
  }
  return { username, password };
}

function stringField(value: Readonly<Record<string, unknown>>, name: string): string {
  const field = value[name];
  if (typeof field !== "string" || field.length === 0) throw new Error("RELATIONAL_TASK_SECRET_INVALID");
  return field;
}

function numberField(value: Readonly<Record<string, unknown>>, name: string): number {
  const field = value[name];
  if (typeof field !== "number") throw new Error("RELATIONAL_TASK_SECRET_INVALID");
  return field;
}

function secretArn(value: string): boolean {
  return /^arn:aws:secretsmanager:eu-west-1:337159794548:secret:[A-Za-z0-9/_+=.@-]+$/.test(value);
}

export type RelationalTaskOperation = "bootstrap" | "migration" | "relay" | "worker" | "restore-verify";
export type RelationalTaskMode = "execute" | "preflight";

/** Only the existing command or one fixed read-only mode is supported. */
export function relationalTaskMode(): RelationalTaskMode {
  const args = process.argv.slice(2);
  if (args.length === 0) return "execute";
  if (args.length === 1 && args[0] === "--preflight") return "preflight";
  throw new Error("RELATIONAL_TASK_ARGUMENTS_INVALID");
}

/**
 * Check necessary database prerequisites using the actual injected principal.
 * This does not prove a migration's effects, queue action permissions, restore
 * contents, or operation authority. The controller binds this distinct mode to
 * the immutable task/image immediately before its dependent operation.
 */
export async function verifyRelationalTaskPreflight(
  pool: PostgreSqlConnectionPool,
  operation: RelationalTaskOperation,
  expectedUsername: string,
): Promise<void> {
  if (!["bootstrap", "migration", "relay", "worker", "restore-verify"].includes(operation)
      || !/^[A-Za-z0-9._-]{1,63}$/.test(expectedUsername)
      || (operation === "migration" && expectedUsername !== "psmokemigrate")
      || (["relay", "worker", "restore-verify"].includes(operation) && expectedUsername !== "psmokeruntime")) {
    throw new Error("RELATIONAL_TASK_PREFLIGHT_FAILED");
  }
  const client = await pool.connect();
  let checked = false;
  let rolledBack = false;
  try {
    await client.query({ text: "BEGIN READ ONLY" });
    const common = await client.query<{
      readonly identity_ok: boolean;
      readonly database_ok: boolean;
      readonly read_only: boolean;
      readonly engine_ok: boolean;
      readonly tls_active: boolean;
    }>({
      text: "SELECT current_user = $1 AND session_user = $1 AS identity_ok, current_database() = 'platformsmoke' AS database_ok, pg_catalog.current_setting('transaction_read_only') = 'on' AS read_only, pg_catalog.current_setting('server_version_num')::integer BETWEEN 170000 AND 179999 AS engine_ok, COALESCE((SELECT ssl FROM pg_catalog.pg_stat_ssl WHERE pid = pg_catalog.pg_backend_pid()), false) AS tls_active",
      values: [expectedUsername],
    });
    const facts = common.rows[0];
    if (common.rows.length !== 1 || facts?.identity_ok !== true || facts.database_ok !== true
        || facts.read_only !== true || facts.engine_ok !== true || facts.tls_active !== true) {
      throw new Error("RELATIONAL_TASK_PREFLIGHT_FAILED");
    }
    if (operation === "bootstrap") {
      const authority = await client.query<{ readonly principal_authority: boolean; readonly schema_authority: boolean }>({
        text: "SELECT rolcanlogin AND rolcreaterole AS principal_authority, pg_catalog.has_database_privilege(current_user, 'platformsmoke', 'CREATE') AS schema_authority FROM pg_catalog.pg_roles WHERE rolname = current_user",
      });
      if (authority.rows.length !== 1 || authority.rows[0]?.principal_authority !== true || authority.rows[0]?.schema_authority !== true) {
        throw new Error("RELATIONAL_TASK_PREFLIGHT_FAILED");
      }
    } else {
      const identity = await client.query<{ readonly least_privileged: boolean; readonly no_memberships: boolean }>({
        text: "SELECT rolcanlogin AND NOT (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls) AS least_privileged, NOT EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members WHERE member = r.oid OR roleid = r.oid) AS no_memberships FROM pg_catalog.pg_roles r WHERE rolname = current_user",
      });
      if (identity.rows.length !== 1 || identity.rows[0]?.least_privileged !== true || identity.rows[0]?.no_memberships !== true) {
        throw new Error("RELATIONAL_TASK_PREFLIGHT_FAILED");
      }
      const schema = await client.query<{ readonly schema_access: boolean; readonly schema_authority: boolean; readonly database_authority: boolean; readonly schema_owned: boolean }>({
        text: "SELECT pg_catalog.has_schema_privilege(current_user, oid, 'USAGE') AS schema_access, pg_catalog.has_schema_privilege(current_user, oid, 'CREATE') AS schema_authority, pg_catalog.has_database_privilege(current_user, 'platformsmoke', 'CREATE') AS database_authority, pg_catalog.pg_get_userbyid(nspowner) = current_user AS schema_owned FROM pg_catalog.pg_namespace WHERE nspname = 'platform_smoke'",
      });
      const state = schema.rows[0];
      if (schema.rows.length !== 1 || state?.schema_access !== true
          || (operation === "migration" && (state.schema_authority !== true || state.schema_owned !== true))
          || (operation !== "migration" && (state.schema_authority !== false || state.database_authority !== false || state.schema_owned !== false))) {
        throw new Error("RELATIONAL_TASK_PREFLIGHT_FAILED");
      }
      if (operation !== "migration") {
        const tables = operation === "restore-verify"
          ? ["platform_smoke_work_item", "platform_outbox"]
          : ["platform_smoke_work_item", "platform_outbox", "platform_processing", "platform_record_change"];
        const needed = operation === "restore-verify"
          ? "pg_catalog.has_table_privilege(current_user, c.oid, 'SELECT')"
          : "pg_catalog.has_table_privilege(current_user, c.oid, 'SELECT') AND pg_catalog.has_table_privilege(current_user, c.oid, 'INSERT') AND pg_catalog.has_table_privilege(current_user, c.oid, 'UPDATE') AND pg_catalog.has_table_privilege(current_user, c.oid, 'DELETE')";
        const access = await client.query<{ readonly table_count: number; readonly required_access: boolean }>({
          text: "SELECT COUNT(*)::integer AS table_count, COALESCE(bool_and(" + needed + "), false) AS required_access FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'platform_smoke' AND c.relkind = 'r' AND c.relname = ANY($1::text[])",
          values: [tables],
        });
        if (access.rows.length !== 1 || access.rows[0]?.table_count !== tables.length || access.rows[0]?.required_access !== true) {
          throw new Error("RELATIONAL_TASK_PREFLIGHT_FAILED");
        }
      }
    }
    checked = true;
  } finally {
    try {
      await client.query({ text: "ROLLBACK" });
      rolledBack = true;
    } finally {
      client.release();
    }
  }
  if (!checked || !rolledBack) throw new Error("RELATIONAL_TASK_PREFLIGHT_FAILED");
}

/** Fixed, disjoint result shape: an exit-zero preflight is never job success. */
export function writePreflightOutcome(operation: RelationalTaskOperation, verdict: "passed" | "failed"): void {
  console.log(JSON.stringify({
    schema: "relational-task-preflight/v1",
    scope: "read-only-database-prerequisites",
    operation,
    verdict,
    authorized: false,
  }));
}
