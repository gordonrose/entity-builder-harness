// One-shot bootstrap only: create the two least-privilege database identities
// from ECS-injected generated credentials, then exit without printing values.

import {
  closePool,
  connectionPool,
  secretFromEnvironment,
  writeOutcome,
} from "./kanbien-platform-postgresql-task";

async function main(): Promise<void> {
  let pool;
  try {
    const master = secretFromEnvironment("RELATIONAL_MASTER_SECRET_JSON");
    const migration = secretFromEnvironment("RELATIONAL_MIGRATION_SECRET_JSON");
    const runtime = secretFromEnvironment("RELATIONAL_RUNTIME_SECRET_JSON");
    pool = connectionPool(master, "arn:aws:secretsmanager:eu-west-1:337159794548:secret:target-managed-master", "platform_smoke");
    const migrationPassword = await quotedLiteral(pool, migration.password);
    const runtimePassword = await quotedLiteral(pool, runtime.password);
    await pool.query({ text: "DO $$ BEGIN CREATE ROLE psmokemigrate LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$" });
    await pool.query({ text: "DO $$ BEGIN CREATE ROLE psmokeruntime LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$" });
    await pool.query({ text: "ALTER ROLE psmokemigrate LOGIN PASSWORD " + migrationPassword });
    await pool.query({ text: "ALTER ROLE psmokeruntime LOGIN PASSWORD " + runtimePassword });
    await pool.query({ text: "GRANT CONNECT, CREATE, TEMPORARY ON DATABASE platformsmoke TO psmokemigrate" });
    await pool.query({ text: "GRANT CONNECT ON DATABASE platformsmoke TO psmokeruntime" });
    await pool.query({ text: "CREATE SCHEMA IF NOT EXISTS platform_smoke AUTHORIZATION psmokemigrate" });
    await pool.query({ text: "GRANT USAGE ON SCHEMA platform_smoke TO psmokeruntime" });
    await pool.query({ text: "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA platform_smoke TO psmokeruntime" });
    writeOutcome("bootstrap_completed", "succeeded");
  } catch {
    writeOutcome("bootstrap_completed", "failed");
    process.exitCode = 1;
  } finally {
    await closePool(pool);
  }
}

async function quotedLiteral(pool: NonNullable<ReturnType<typeof connectionPool>>, value: string): Promise<string> {
  const result = await pool.query<{ readonly literal: string }>({ text: "SELECT quote_literal($1) AS literal", values: [value] });
  const literal = result.rows[0]?.literal;
  if (literal === undefined) throw new Error("RELATIONAL_TASK_QUOTING_FAILED");
  return literal;
}

void main();
