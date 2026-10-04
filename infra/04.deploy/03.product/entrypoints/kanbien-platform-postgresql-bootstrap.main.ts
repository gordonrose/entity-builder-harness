// One-shot bootstrap only: create the two least-privilege database identities
// from ECS-injected generated credentials, then exit without printing values.

import {
  type BootstrapFailureCategory,
  closePool,
  connectionPool,
  credentialsFromEnvironment,
  secretFromEnvironment,
  writeOutcome,
} from "./kanbien-platform-postgresql-task";

async function main(): Promise<void> {
  let pool;
  let phase: BootstrapFailureCategory = "bootstrap-input-validation-failure";
  try {
    const masterCredentials = credentialsFromEnvironment("RELATIONAL_MASTER_SECRET_JSON");
    const migration = secretFromEnvironment("RELATIONAL_MIGRATION_SECRET_JSON");
    const runtime = secretFromEnvironment("RELATIONAL_RUNTIME_SECRET_JSON");
    const master = { ...masterCredentials, host: migration.host, port: migration.port };
    pool = connectionPool(master, "arn:aws:secretsmanager:eu-west-1:337159794548:secret:target-managed-master", "platform_smoke");
    phase = "bootstrap-password-quotation-failure";
    const migrationPassword = await quotedLiteral(pool, migration.password);
    const runtimePassword = await quotedLiteral(pool, runtime.password);
    phase = "bootstrap-role-provisioning-failure";
    await pool.query({ text: "DO $$ BEGIN CREATE ROLE psmokemigrate LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$" });
    await pool.query({ text: "DO $$ BEGIN CREATE ROLE psmokeruntime LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$" });
    await pool.query({ text: "ALTER ROLE psmokemigrate LOGIN PASSWORD " + migrationPassword });
    await pool.query({ text: "ALTER ROLE psmokeruntime LOGIN PASSWORD " + runtimePassword });
    phase = "bootstrap-database-grant-failure";
    await pool.query({ text: "GRANT CONNECT, CREATE, TEMPORARY ON DATABASE platformsmoke TO psmokemigrate" });
    await pool.query({ text: "GRANT CONNECT ON DATABASE platformsmoke TO psmokeruntime" });
    phase = "bootstrap-schema-provisioning-failure";
    // PostgreSQL requires the creator to be able to SET ROLE to assign schema
    // ownership. The managed RDS master created this role, but is not a
    // superuser; grant the exact owned role to the current bootstrap identity.
    await pool.query({ text: "GRANT psmokemigrate TO CURRENT_USER" });
    await pool.query({ text: "CREATE SCHEMA IF NOT EXISTS platform_smoke AUTHORIZATION psmokemigrate" });
    phase = "bootstrap-schema-grant-failure";
    await pool.query({ text: "GRANT USAGE ON SCHEMA platform_smoke TO psmokeruntime" });
    await pool.query({ text: "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA platform_smoke TO psmokeruntime" });
    writeOutcome("bootstrap_completed", "succeeded");
  } catch (error) {
    writeOutcome("bootstrap_completed", "failed", bootstrapFailureCategory(error, phase));
    process.exitCode = 1;
  } finally {
    await closePool(pool);
  }
}

function bootstrapFailureCategory(error: unknown, phase: BootstrapFailureCategory): BootstrapFailureCategory {
  const code = errorProperty(error, "code");
  const message = errorProperty(error, "message");
  if (message === "RELATIONAL_TASK_CERTIFICATE_AUTHORITY_UNAVAILABLE") return "bootstrap-certificate-authority-unavailable";
  if (code === "28P01" || code === "28000") return "bootstrap-database-authentication-failure";
  if (code === "42501") {
    return phase === "bootstrap-input-validation-failure" ? "bootstrap-database-authorization-failure" : phase;
  }
  if (["ECONNREFUSED", "ECONNRESET", "ENETUNREACH", "ENOTFOUND", "ETIMEDOUT"].includes(code ?? "")) return "bootstrap-database-connectivity-failure";
  if (["CERT_HAS_EXPIRED", "ERR_TLS_CERT_ALTNAME_INVALID", "SELF_SIGNED_CERT_IN_CHAIN", "UNABLE_TO_VERIFY_LEAF_SIGNATURE"].includes(code ?? "")) return "bootstrap-database-tls-failure";
  return phase;
}

function errorProperty(error: unknown, property: "code" | "message"): string | undefined {
  if (typeof error !== "object" || error === null) return undefined;
  const value = (error as Readonly<Record<string, unknown>>)[property];
  return typeof value === "string" ? value : undefined;
}

async function quotedLiteral(pool: NonNullable<ReturnType<typeof connectionPool>>, value: string): Promise<string> {
  const result = await pool.query<{ readonly literal: string }>({ text: "SELECT quote_literal($1) AS literal", values: [value] });
  const literal = result.rows[0]?.literal;
  if (literal === undefined) throw new Error("RELATIONAL_TASK_QUOTING_FAILED");
  return literal;
}

void main();
