// One-shot migration only: apply the reviewed immutable two-entry manifest,
// then exit. The runtime identity never executes this path.

import {
  createPostgreSqlMigrationRunner,
  postgreSqlPersistenceFoundationMigration,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { kanbienPlatformSmokePostgreSqlMigration } from "./kanbien-platform-postgresql-persistence";
import {
  closePool,
  configurationFromEnvironment,
  connectionConfiguration,
  connectionPool,
  secretFromEnvironment,
  writeOutcome,
} from "./kanbien-platform-postgresql-task";

async function main(): Promise<void> {
  let pool;
  try {
    const configuration = configurationFromEnvironment();
    const migration = secretFromEnvironment("RELATIONAL_MIGRATION_SECRET_JSON");
    pool = connectionPool(migration, configuration.migrationSecretArn, configuration.schema);
    const adapterConfiguration = connectionConfiguration(migration, configuration.migrationSecretArn, configuration.schema);
    // PostgreSQL default privileges belong to the role that will create later
    // tables. The bootstrap identity deliberately does not impersonate this
    // migration identity or retain membership in it.
    await pool.query({ text: "ALTER DEFAULT PRIVILEGES IN SCHEMA platform_smoke GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO psmokeruntime" });
    const result = await createPostgreSqlMigrationRunner(adapterConfiguration, { pool }, "stage6-staging").apply({
      schema: configuration.schema,
      migrations: [postgreSqlPersistenceFoundationMigration(configuration.schema), kanbienPlatformSmokePostgreSqlMigration(configuration.schema)],
    });
    if (!result.ok || result.value.length !== 2) throw new Error("RELATIONAL_TASK_MIGRATION_FAILED");
    writeOutcome("migration_completed", "succeeded");
  } catch {
    writeOutcome("migration_completed", "failed");
    process.exitCode = 1;
  } finally {
    await closePool(pool);
  }
}

void main();
