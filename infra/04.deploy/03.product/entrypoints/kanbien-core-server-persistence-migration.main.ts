// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-migration
//   version: 3
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-11-04"
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
import { persistenceConfigurationResult, persistenceCertificateAuthorityResult, persistenceTaskDiagnosticFields, persistenceMigrationInstructionsResult } from "./kanbien-core-server-persistence-configuration";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { persistenceIamAuthenticationResult } from "./kanbien-core-server-persistence-iam-authentication";
import { kanbienCoreServerPersistenceAcceptanceMigration } from "./kanbien-core-server-persistence-postgresql";
import { reportCoreServerPersistenceBoundary } from "./kanbien-core-server-persistence-operation-diagnostics";

export async function runKanbienCoreServerPersistenceMigration(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const parsed = persistenceConfigurationResult(env, "migration");
  if (!parsed.ok) return rejected("PERSISTENCE_MIGRATION_CONFIGURATION_INVALID", undefined, undefined, parsed.error.diagnostic);
  const configuration = parsed.value;
  const authentication = persistenceIamAuthenticationResult(env, configuration, "PERSISTENCE_MIGRATION_DATABASE_USERNAME");
  if (!authentication.ok) return rejected("PERSISTENCE_MIGRATION_CONFIGURATION_INVALID", undefined, undefined, authentication.error.diagnostic);
  const credentials = authentication.value;
  const authority = persistenceCertificateAuthorityResult(env);
  if (!authority.ok) return rejected("PERSISTENCE_MIGRATION_CONFIGURATION_INVALID", undefined, undefined, authority.error.diagnostic);
  const certificateAuthority = authority.value;
  const instructions = persistenceMigrationInstructionsResult(env);
  if (configuration === undefined || credentials === undefined || certificateAuthority === undefined) return rejected("PERSISTENCE_MIGRATION_CONFIGURATION_INVALID");
  if (!instructions.ok) return rejected("PERSISTENCE_MIGRATION_CONFIGURATION_INVALID", undefined, undefined, instructions.error.diagnostic);
  const pool = createNodePostgreSqlTokenConnectionPool(configuration, { ...credentials, certificateAuthority });
  const stage = "migration";
  try {
    const acceptance = kanbienCoreServerPersistenceAcceptanceMigration(configuration.schema);
    const result = await createPostgreSqlMigrationRunner(configuration, { pool }, "core-server-persistence-v1")[instructions.value.operation]({
      schema: configuration.schema,
      // The administrative task owns schema creation and ownership. The
      // ordinary migration identity must never require database-level CREATE.
      schemaPreprovisioned: true,
      migrations: [postgreSqlPersistenceFoundationMigration(configuration.schema), { ...acceptance, checksum: postgreSqlMigrationChecksum(acceptance.statements) }],
    });
    if (!result.ok) return rejected("PERSISTENCE_MIGRATION_NOT_CONFIRMED", stage, migrationFailureClass(result.error), result.error.diagnosticRecord, result.error.relatedDiagnosticRecords);
    console.log(JSON.stringify({ verdict: "accepted", code: "PERSISTENCE_MIGRATION_APPLIED" }));
  } catch (cause) {
    rejected("PERSISTENCE_MIGRATION_NOT_CONFIRMED", stage);
    reportCoreServerPersistenceBoundary("migration", { operation: "migration", phase: "invocation", boundary: "body", condition: "threw", effect: "unknown" }, cause);
  } finally {
    let pending: Promise<void>;
    try { pending = pool.end(); }
    catch (cause) { reportCoreServerPersistenceBoundary("migration", { operation: "connection-pool", phase: "invocation", boundary: "end", condition: "threw", effect: "not-assessed" }, cause); throw cause; }
    try { await pending; }
    catch (cause) { reportCoreServerPersistenceBoundary("migration", { operation: "connection-pool", phase: "completion", boundary: "end", condition: "rejected", effect: "not-assessed" }, cause); throw cause; }
  }
}

function rejected(code: string, stage?: "migration", failureClass?: string, diagnostic?: DiagnosticRecord, relatedDiagnosticRecords?: readonly DiagnosticRecord[]): void {
  console.error(JSON.stringify({ verdict: "rejected", code, ...(stage === undefined ? {} : { stage }), ...(failureClass === undefined ? {} : { provider_failure_class: failureClass }), ...persistenceTaskDiagnosticFields(diagnostic, relatedDiagnosticRecords) }));
  process.exitCode = 1;
}

function migrationFailureClass(error: { readonly params?: Readonly<Record<string, unknown>> }): string | undefined {
  const value = error.params?.["provider_failure_class"];
  return typeof value === "string" && /^(access_denied|conflict|constraint|resource_not_found|timeout|transaction_rolled_back|transport|validation|unknown)$/.test(value)
    ? value
    : undefined;
}
if (typeof require !== "undefined" && require.main === module) void runKanbienCoreServerPersistenceMigration();
