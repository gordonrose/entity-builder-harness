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
