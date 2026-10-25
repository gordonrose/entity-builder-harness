// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-migration
//   version: 2
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-25"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Apply the reviewed, checksummed persistence migration manifest with the isolated migration credential.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import {
  createNodePostgreSqlTokenConnectionPool,
  createPostgreSqlMigrationRunner,
  postgreSqlMigrationChecksum,
  postgreSqlPersistenceFoundationMigration,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { persistenceConfiguration, persistenceCertificateAuthority } from "./kanbien-core-server-persistence-configuration";
import { persistenceIamAuthentication } from "./kanbien-core-server-persistence-iam-authentication";
import { kanbienCoreServerPersistenceAcceptanceMigration } from "./kanbien-core-server-persistence-postgresql";

export async function runKanbienCoreServerPersistenceMigration(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const configuration = persistenceConfiguration(env, "migration");
  const credentials = configuration === undefined ? undefined : persistenceIamAuthentication(env, configuration, "PERSISTENCE_MIGRATION_DATABASE_USERNAME");
  const certificateAuthority = persistenceCertificateAuthority(env);
  const operation = env["PERSISTENCE_MIGRATION_OPERATION"];
  if (configuration === undefined || credentials === undefined || certificateAuthority === undefined || (operation !== undefined && operation !== "apply")) return rejected("PERSISTENCE_MIGRATION_CONFIGURATION_INVALID");
  const pool = createNodePostgreSqlTokenConnectionPool(configuration, { ...credentials, certificateAuthority });
  const stage = "migration";
  try {
    const acceptance = kanbienCoreServerPersistenceAcceptanceMigration(configuration.schema);
    const result = await createPostgreSqlMigrationRunner(configuration, { pool }, "core-server-persistence-v1").apply({
      schema: configuration.schema,
      // The administrative task owns schema creation and ownership. The
      // ordinary migration identity must never require database-level CREATE.
      schemaPreprovisioned: true,
      migrations: [postgreSqlPersistenceFoundationMigration(configuration.schema), { ...acceptance, checksum: postgreSqlMigrationChecksum(acceptance.statements) }],
    });
    if (!result.ok) return rejected("PERSISTENCE_MIGRATION_NOT_CONFIRMED", stage, migrationFailureClass(result.error));
    console.log(JSON.stringify({ verdict: "accepted", code: "PERSISTENCE_MIGRATION_APPLIED" }));
  } catch { rejected("PERSISTENCE_MIGRATION_NOT_CONFIRMED", stage); } finally { await pool.end(); }
}

function rejected(code: string, stage?: "migration", failureClass?: string): void {
  console.error(JSON.stringify({ verdict: "rejected", code, ...(stage === undefined ? {} : { stage }), ...(failureClass === undefined ? {} : { provider_failure_class: failureClass }) }));
  process.exitCode = 1;
}

function migrationFailureClass(error: { readonly params?: Readonly<Record<string, unknown>> }): string | undefined {
  const value = error.params?.["provider_failure_class"];
  return typeof value === "string" && /^(access_denied|conflict|constraint|resource_not_found|timeout|transaction_rolled_back|transport|validation|unknown)$/.test(value)
    ? value
    : undefined;
}
if (typeof require !== "undefined" && require.main === module) void runKanbienCoreServerPersistenceMigration();
