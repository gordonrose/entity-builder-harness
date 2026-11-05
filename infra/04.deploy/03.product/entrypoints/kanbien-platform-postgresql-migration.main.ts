// One-shot migration only: apply the reviewed immutable two-entry manifest,
// then exit. The runtime identity never executes this path.
import { reportTargetConfigurationError } from "./kanbien-platform-configuration-diagnostics";

import {
  createPostgreSqlMigrationRunner,
  postgreSqlPersistenceFoundationMigration,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { kanbienPlatformSmokePostgreSqlMigration } from "./kanbien-platform-postgresql-persistence";
import { reportKanbienPlatformPostgreSqlDiagnostic, reportKanbienPlatformPostgreSqlTaskDiagnostic, reportKanbienPlatformPostgreSqlMigrationInvocationFailure } from "./kanbien-platform-postgresql-operation-diagnostics";
import { persistenceBoundaryDiagnosticRecord, persistenceLocalRejectionDiagnosticRecord } from "@kanbien/platform-persistence";
import { targetDeliveryErrorSource } from "./kanbien-platform-delivery-diagnostics";
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
    try {
      await pool.query({ text: "ALTER DEFAULT PRIVILEGES IN SCHEMA platform_smoke GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO psmokeruntime" });
    } catch (cause) { reportKanbienPlatformPostgreSqlMigrationInvocationFailure(cause); throw cause; }
    let result: Awaited<ReturnType<ReturnType<typeof createPostgreSqlMigrationRunner>["apply"]>>;
    try {
      result = await createPostgreSqlMigrationRunner(adapterConfiguration, { pool }, "stage6-staging").apply({
        schema: configuration.schema,
        migrations: [postgreSqlPersistenceFoundationMigration(configuration.schema), kanbienPlatformSmokePostgreSqlMigration(configuration.schema, { onDiagnostic: reportKanbienPlatformPostgreSqlDiagnostic })],
      });
    } catch (cause) { reportKanbienPlatformPostgreSqlMigrationInvocationFailure(cause); throw cause; }
    let returnedFailure = false;
    if ((returnedFailure = !result.ok) || (result as Extract<typeof result, { readonly ok: true }>).value.length !== 2) {
      if (returnedFailure) reportKanbienPlatformPostgreSqlTaskDiagnostic("migration", persistenceBoundaryDiagnosticRecord({ operation: "migration", phase: "returned-result", boundary: "body", condition: "returned-failure", effect: "unknown" }), targetDeliveryErrorSource(result));
      else reportKanbienPlatformPostgreSqlTaskDiagnostic("migration", persistenceLocalRejectionDiagnosticRecord({ operation: "migration", field: "manifest", condition: "predicate-rejected", phase: "after-statements", effect: "unknown" }));
      throw new Error("RELATIONAL_TASK_MIGRATION_FAILED");
    }
    writeOutcome("migration_completed", "succeeded");
  } catch (error) {
    reportTargetConfigurationError(error);
    writeOutcome("migration_completed", "failed");
    process.exitCode = 1;
  } finally {
    await closePool(pool);
  }
}

void main();
