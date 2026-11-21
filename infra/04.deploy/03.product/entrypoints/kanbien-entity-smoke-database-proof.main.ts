// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.database-proof-main
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: code
//   purpose: Run one explicit database proof with only the isolated runtime identity and safe task output.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { createNodePostgreSqlTokenConnectionPool, postgreSqlPersistenceOperationError } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { entitySmokeDatabaseSettings } from "./entity-smoke/configuration";
import { entitySmokeConfigurationError, entitySmokeDiagnosticCatalogs, reportEntitySmokeFailure } from "./entity-smoke/diagnostics";
import { verifyEntitySmokeDatabase } from "./entity-smoke/database-verification";
import { performEntitySmokeDatabasePreflight } from "./entity-smoke/preflight";
import { entitySmokeRuntimeUsername } from "./entity-smoke/postgresql";

export async function runEntitySmokeDatabaseProof(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const operation = env["ENTITY_SMOKE_DATABASE_PROOF_OPERATION"];
  const label = env["ENTITY_SMOKE_PROOF_LABEL"] ?? "";
  const digest = env["ENTITY_SMOKE_EXPECTED_DIGEST"];
  if ((operation !== "preflight" && operation !== "permissions" && operation !== "collision" && operation !== "restore-read") || !/^entity-smoke-[a-f0-9]{24}$/.test(label) ||
      (operation === "collision" || operation === "restore-read") && !/^[a-f0-9]{64}$/.test(digest ?? "")) {
    reportEntitySmokeFailure("verification", "not-started", entitySmokeConfigurationError("operation", "invalid")); process.exitCode = 1; return;
  }
  // An administrative credential must never be delivered to this workload.
  if (Object.keys(env).some(key => key.startsWith("PERSISTENCE_ADMINISTRATOR_"))) {
    reportEntitySmokeFailure("verification", "not-started", entitySmokeConfigurationError("identity", "mismatch")); process.exitCode = 1; return;
  }
  const settings = entitySmokeDatabaseSettings(env, "runtime");
  if (!settings.ok) { reportEntitySmokeFailure("verification", "not-started", settings.error); process.exitCode = 1; return; }
  const pool = createNodePostgreSqlTokenConnectionPool(settings.value.configuration, settings.value.credentials);
  let completion: Awaited<ReturnType<typeof verifyEntitySmokeDatabase>> | { verdict: "passed"; code: "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED" } | undefined;
  try {
    if (operation === "preflight") {
      const code = await performEntitySmokeDatabasePreflight(pool, { identity: "runtime", database: settings.value.configuration.database, username: entitySmokeRuntimeUsername });
      completion = { verdict: "passed", code };
    } else completion = await verifyEntitySmokeDatabase(pool, { operation, label,
      ...(digest === undefined ? {} : { expectedDigest: digest }) });
  } catch (cause) {
    reportEntitySmokeFailure("verification", operation === "preflight" ? "not-started" : operation === "permissions" ? "unknown" : "not-assessed",
      postgreSqlPersistenceOperationError(operation === "preflight" ? "readiness" : operation === "restore-read" ? "restore_verification" : "administration", cause, { diagnosticDefinitions: entitySmokeDiagnosticCatalogs.flatMap(catalog => [...catalog.definitions]) }));
    process.exitCode = 1;
  } finally {
    try { await pool.end(); }
    catch (cause) { completion = undefined; reportEntitySmokeFailure("close", "not-assessed", cause); process.exitCode = 1; }
  }
  if (completion !== undefined) console.log(JSON.stringify(completion));
}
if (typeof require !== "undefined" && require.main === module) void runEntitySmokeDatabaseProof().catch(cause => {
  reportEntitySmokeFailure("verification", "unknown", cause); process.exitCode = 1;
});
