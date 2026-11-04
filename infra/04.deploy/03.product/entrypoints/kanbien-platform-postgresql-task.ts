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
import { relationalSecretSetting, targetConfigurationDiagnosticRecord, type TargetConfigurationReason } from "./kanbien-platform-configuration-diagnostics";
import { persistenceBoundaryDiagnosticRecord } from "@kanbien/platform-persistence";
import { reportKanbienPlatformPostgreSqlTaskDiagnostic } from "./kanbien-platform-postgresql-operation-diagnostics";

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

/** Fixed, non-sensitive classifications for the isolated restore proof. */
export type RestoreVerificationFailureCategory =
  | "restore-input-validation-failure"
  | "restore-certificate-authority-unavailable"
  | "restore-database-authentication-failure"
  | "restore-database-authorization-failure"
  | "restore-database-connectivity-failure"
  | "restore-database-tls-failure"
  | "restore-database-query-failure"
  | "restore-migration-checksum-mismatch"
  | "restore-missing-proof-data"
  | "restore-processing-state-mismatch";

export type RestoreVerificationPhase =
  | "input-validation"
  | "connection"
  | "migration-checksum-verification"
  | "work-item-verification"
  | "outbox-verification"
  | "processing-state-verification";

export type RestoreVerificationObserved = "not-queried" | "zero" | "one" | "two" | "other";

export interface RestoreVerificationFailureDetails {
  readonly failure_phase: RestoreVerificationPhase;
  readonly failure_category: RestoreVerificationFailureCategory;
  readonly database_error_code?: string;
  readonly expected: Readonly<Record<"migration_checksums" | "accepted_work_item" | "published_outbox" | "completed_processing", "two" | "one">>;
  readonly observed: Readonly<Record<"migration_checksums" | "accepted_work_item" | "published_outbox" | "completed_processing", RestoreVerificationObserved>>;
}

export function secretFromEnvironment(name: string): RelationalTaskSecret {
  const candidate = secretObjectFromEnvironment(name);
  const credentials = credentialsFromSecret(candidate, name);
  const host = stringField(candidate, "host", relationalSecretSetting(name, "host"));
  const port = numberField(candidate, "port", relationalSecretSetting(name, "port"));
  if (!/^[A-Za-z0-9.-]{1,253}$/.test(host)) throw relationalConfigurationError("RELATIONAL_TASK_SECRET_INVALID", relationalSecretSetting(name, "host"), "invalid-format");
  if (!Number.isInteger(port)) throw relationalConfigurationError("RELATIONAL_TASK_SECRET_INVALID", relationalSecretSetting(name, "port"), "invalid-integer");
  if (port < 1 || port > 65_535) throw relationalConfigurationError("RELATIONAL_TASK_SECRET_INVALID", relationalSecretSetting(name, "port"), "out-of-range");
  return { ...credentials, host, port };
}

export function credentialsFromEnvironment(name: string): RelationalTaskCredentials {
  return credentialsFromSecret(secretObjectFromEnvironment(name), name);
}

export function configurationFromEnvironment(): RelationalTaskConfiguration {
  const raw = process.env["RELATIONAL_CONFIG_JSON"];
  if (raw === undefined) throw relationalConfigurationError("RELATIONAL_TASK_CONFIGURATION_MISSING", "relational.configuration", "missing");
  let candidate: unknown;
  try {
    candidate = JSON.parse(raw);
  } catch {
    throw relationalConfigurationError("RELATIONAL_TASK_CONFIGURATION_INVALID", "relational.configuration", "invalid-json");
  }
  if (!isRecord(candidate)) throw relationalConfigurationError("RELATIONAL_TASK_CONFIGURATION_INVALID", "relational.configuration", "wrong-shape");
  const database = stringField(candidate, "database", "relational.database");
  const schema = stringField(candidate, "schema", "relational.schema");
  const tls = stringField(candidate, "tls", "relational.tls");
  const runtimeSecretArn = stringField(candidate, "runtime_secret_arn", "relational.runtime-reference");
  const migrationSecretArn = stringField(candidate, "migration_secret_arn", "relational.migration-reference");
  if (database !== "platformsmoke") throw relationalConfigurationError("RELATIONAL_TASK_CONFIGURATION_INVALID", "relational.database", "fixed-value-required");
  if (schema !== "platform_smoke") throw relationalConfigurationError("RELATIONAL_TASK_CONFIGURATION_INVALID", "relational.schema", "fixed-value-required");
  if (tls !== "verify-full") throw relationalConfigurationError("RELATIONAL_TASK_CONFIGURATION_INVALID", "relational.tls", "fixed-value-required");
  if (!secretArn(runtimeSecretArn)) throw relationalConfigurationError("RELATIONAL_TASK_CONFIGURATION_INVALID", "relational.runtime-reference", "invalid-format");
  if (!secretArn(migrationSecretArn)) throw relationalConfigurationError("RELATIONAL_TASK_CONFIGURATION_INVALID", "relational.migration-reference", "invalid-format");
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
  if (!result.ok) {
    const path = result.error.details.path;
    const setting = path === "host" ? "relational.connection.host" : path === "port" ? "relational.connection.port" : path === "schema" ? "relational.connection.schema" : path === "runtimeCredentialSecretReference" ? "relational.connection.reference" : "relational.connection.configuration";
    // reasonCode is adapter-owned typed evidence; never inspect its message.
    throw relationalConfigurationError("RELATIONAL_TASK_CONFIGURATION_INVALID", setting, result.error.details.reasonCode as TargetConfigurationReason);
  }
  return result.value;
}

export function connectionPool(secret: RelationalTaskSecret, reference: string, schema = "platform_smoke"): PostgreSqlConnectionPool {
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
    return readFileSync("/app/assets/rds-eu-west-1-bundle.crt", "utf8");
  } catch {
    throw new Error("RELATIONAL_TASK_CERTIFICATE_AUTHORITY_UNAVAILABLE");
  }
}

export async function closePool(pool: PostgreSqlConnectionPool | undefined): Promise<void> {
  if (pool === undefined) return;
  let pending: Promise<void>;
  try { pending = pool.end(); }
  catch (cause) {
    reportKanbienPlatformPostgreSqlTaskDiagnostic("connection-resource", persistenceBoundaryDiagnosticRecord({ operation: "connection-pool", phase: "invocation", boundary: "end", condition: "threw", effect: "not-assessed" }), cause);
    return;
  }
  try {
    await pending;
  } catch (cause) {
    reportKanbienPlatformPostgreSqlTaskDiagnostic("connection-resource", persistenceBoundaryDiagnosticRecord({ operation: "connection-pool", phase: "completion", boundary: "end", condition: "rejected", effect: "not-assessed" }), cause);
  }
}

export function writeOutcome(operation: string, outcome: "succeeded" | "failed", failureCategory?: BootstrapFailureCategory | RestoreVerificationFailureCategory): void {
  const fields = outcome === "failed" && failureCategory !== undefined
    ? { outcome, failure_category: failureCategory }
    : { outcome };
  console.log(JSON.stringify({ level: outcome === "succeeded" ? "info" : "error", message: "kanbien-platform.relational-smoke." + operation, fields }));
}

/** Emit only the reviewed, count-bucketed restore failure facts. */
export function writeRestoreVerificationFailure(details: RestoreVerificationFailureDetails): void {
  console.log(JSON.stringify({
    level: "error",
    message: "kanbien-platform.relational-smoke.restore_verified",
    fields: { outcome: "failed", ...details },
  }));
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function secretObjectFromEnvironment(name: string): Readonly<Record<string, unknown>> {
  const raw = process.env[name];
  if (raw === undefined) throw relationalConfigurationError("RELATIONAL_TASK_SECRET_MISSING", relationalSecretSetting(name, "value"), "missing");
  let candidate: unknown;
  try {
    candidate = JSON.parse(raw);
  } catch {
    throw relationalConfigurationError("RELATIONAL_TASK_SECRET_INVALID", relationalSecretSetting(name, "value"), "invalid-json");
  }
  if (!isRecord(candidate)) throw relationalConfigurationError("RELATIONAL_TASK_SECRET_INVALID", relationalSecretSetting(name, "value"), "wrong-shape");
  return candidate;
}

function credentialsFromSecret(candidate: Readonly<Record<string, unknown>>, name: string): RelationalTaskCredentials {
  const username = stringField(candidate, "username", relationalSecretSetting(name, "username"));
  const password = stringField(candidate, "password", relationalSecretSetting(name, "password"));
  if (!/^[A-Za-z0-9._-]{1,63}$/.test(username)) throw relationalConfigurationError("RELATIONAL_TASK_SECRET_INVALID", relationalSecretSetting(name, "username"), "invalid-format");
  if (password.length < 1) throw relationalConfigurationError("RELATIONAL_TASK_SECRET_INVALID", relationalSecretSetting(name, "password"), "empty");
  return { username, password };
}

function stringField(value: Readonly<Record<string, unknown>>, name: string, setting: string): string {
  const field = value[name];
  if (typeof field !== "string" || field.length === 0) throw relationalConfigurationError("RELATIONAL_TASK_SECRET_INVALID", setting, field === undefined ? "missing" : typeof field !== "string" ? "wrong-type" : "empty");
  return field;
}

function numberField(value: Readonly<Record<string, unknown>>, name: string, setting: string): number {
  const field = value[name];
  if (typeof field !== "number") throw relationalConfigurationError("RELATIONAL_TASK_SECRET_INVALID", setting, field === undefined ? "missing" : "wrong-type");
  return field;
}

function secretArn(value: string): boolean {
  return /^arn:aws:secretsmanager:eu-west-1:337159794548:secret:[A-Za-z0-9/_+=.@-]+$/.test(value);
}

/** Keep the historical Error and message, attaching only a checked safe fact. */
export function relationalConfigurationError(message: string, setting: string, reason: TargetConfigurationReason): Error {
  return Object.assign(new Error(message), { diagnosticRecord: targetConfigurationDiagnosticRecord(setting, reason) });
}
