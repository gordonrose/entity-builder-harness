// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.migrations
//   version: 1
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Apply the isolated checksummed feature migration without automatic replay; uncertainty uses the administrative observer.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { createNodePostgreSqlTokenConnectionPool, createPostgreSqlMigrationRunner, postgreSqlPersistenceOperationError } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { entitySmokeDatabaseSettings } from "./configuration";
import { entitySmokeConfigurationError, entitySmokeDiagnosticCatalogs, reportEntitySmokeFailure } from "./diagnostics";
import { entitySmokeMigrationManifest, entitySmokeMigrationUsername } from "./postgresql";
import { performEntitySmokeDatabasePreflight } from "./preflight";

export async function runEntitySmokeMigration(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const operation = env["ENTITY_SMOKE_MIGRATION_OPERATION"];
  if (operation !== "apply" && operation !== "preflight") {
    reportEntitySmokeFailure("migration", "not-started", entitySmokeConfigurationError("operation", "invalid")); process.exitCode = 1; return;
  }
  const settings = entitySmokeDatabaseSettings(env, "migration");
  if (!settings.ok) { reportEntitySmokeFailure("migration", "not-started", settings.error); process.exitCode = 1; return; }
  const pool = createNodePostgreSqlTokenConnectionPool(settings.value.configuration, settings.value.credentials);
  const manifest = entitySmokeMigrationManifest();
  let completion: { verdict: "passed"; code: string } | undefined;
  try {
    if (operation === "preflight") {
      const code = await performEntitySmokeDatabasePreflight(pool, { identity: "migration", database: settings.value.configuration.database, username: entitySmokeMigrationUsername });
      completion = { verdict: "passed", code };
    } else {
    const result = await createPostgreSqlMigrationRunner(settings.value.configuration, { pool }, "entity-smoke-v1").apply(manifest);
    if (!result.ok) { reportEntitySmokeFailure("migration", "unknown", result.error); process.exitCode = 1; return; }
    completion = { verdict: "passed", code: result.value[0]?.status === "already-applied" ? "ENTITY_SMOKE_MIGRATION_ALREADY_APPLIED" : "ENTITY_SMOKE_MIGRATION_APPLIED" };
    }
  } catch (cause) { reportEntitySmokeFailure("migration", operation === "preflight" ? "not-started" : "unknown",
    operation === "preflight" ? postgreSqlPersistenceOperationError("readiness", cause, { diagnosticDefinitions: entitySmokeDiagnosticCatalogs.flatMap(catalog => [...catalog.definitions]) }) : cause); process.exitCode = 1; }
  finally { try { await pool.end(); } catch (cause) { completion = undefined; reportEntitySmokeFailure("close", "not-assessed", cause); process.exitCode = 1; } }
  if (completion !== undefined) console.log(JSON.stringify(completion));
}

