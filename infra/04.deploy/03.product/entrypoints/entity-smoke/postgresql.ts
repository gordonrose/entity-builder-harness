// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.postgresql
//   version: 1
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Bind app-owned SQL statements to an isolated PostgreSQL schema and retain classified failure evidence.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { relationalTestEntityRepository, testEntityMigration, testEntityCreationConflict, type TestEntityRelationalExecutor } from "@kanbien/app-entity-smoke";
import { ok } from "@kanbien/core/shared";
import { diagnosticRelatedRecordLimit } from "@kanbien/core/diagnostics";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import { postgreSqlFailureDiagnostic, postgreSqlPersistenceOperationError, postgreSqlMigrationChecksum,
  postgreSqlSecurityDiagnosticRecords, type PostgreSqlConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { persistenceCrudObservedDiagnosticRecord, platformPersistenceError,
  selectPlatformPersistenceDiagnosticEvidence, platformPersistenceDiagnosticCatalog } from "@kanbien/platform-persistence";

export const entitySmokeSchema = "entity_smoke";
export const entitySmokeRuntimeUsername = "entity_smoke_runtime";
export const entitySmokeMigrationUsername = "entity_smoke_migration";

/** Both the feature SQL and migration share this reviewed, fixed isolation boundary. */
export function entitySmokeSql(text: string): string {
  return text.replaceAll("__SCHEMA__", '"entity_smoke"');
}

export function entitySmokeMigrationManifest() {
  const statements = testEntityMigration.statements.map(statement => ({ text: entitySmokeSql(statement.text) }));
  return { schema: entitySmokeSchema, schemaPreprovisioned: true, migrations: [
    { id: testEntityMigration.id, statements, checksum: postgreSqlMigrationChecksum(statements) },
  ] } as const;
}

export function createEntitySmokePostgreSqlRuntime(pool: PostgreSqlConnectionPool) {
  const executor: TestEntityRelationalExecutor = { async execute(statement, operation) {
    try { return ok(await pool.query({ ...statement, text: entitySmokeSql(statement.text) })); }
    catch (cause) {
      if (operation !== "read") {
        const error = postgreSqlPersistenceOperationError("write_facts", cause, {
          diagnosticDefinitions: [...coreDiagnosticCatalog.definitions, ...platformPersistenceDiagnosticCatalog.definitions, ...platformSecurityDiagnosticCatalog.definitions],
        });
        return { ok: false, error: operation === "create" && postgreSqlFailureDiagnostic(cause).facts.classification === "conflict" ? testEntityCreationConflict(error) : error };
      }
      const selected = selectPlatformPersistenceDiagnosticEvidence({}, cause);
      const facts = postgreSqlFailureDiagnostic(cause);
      const related = [...(selected.relatedDiagnosticRecords ?? [])];
      if (facts.facts.classification === "tls_trust_invalid") for (const record of postgreSqlSecurityDiagnosticRecords(cause)) {
        if (related.length < diagnosticRelatedRecordLimit && ![selected.diagnosticRecord, ...related].some(existing => existing?.code === record.code && existing.definitionVersion === record.definitionVersion && JSON.stringify(existing.detail) === JSON.stringify(record.detail))) related.push(record);
      }
      return { ok: false, error: platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: "The persistence read could not complete.",
        diagnostic: facts,
        diagnosticRecord: selected.diagnosticRecord ?? persistenceCrudObservedDiagnosticRecord(facts.facts, "read", "primary"),
        ...(related.length === 0 ? {} : { relatedDiagnosticRecords: related }),
        relatedDiagnosticDefinitions: [...coreDiagnosticCatalog.definitions, ...platformPersistenceDiagnosticCatalog.definitions, ...platformSecurityDiagnosticCatalog.definitions],
      }) };
    }
  } };
  return {
    repository: relationalTestEntityRepository(executor),
    readiness: async () => {
      const result = await executor.execute({ text: "SELECT id FROM __SCHEMA__.test_entity LIMIT 1", values: [] }, "read");
      return result.ok ? { readiness: "ready" as const } : { readiness: "not-ready" as const,
        ...(result.error.diagnosticRecord === undefined ? {} : { diagnosticRecord: result.error.diagnosticRecord }),
        ...(result.error.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: result.error.relatedDiagnosticRecords }) };
    },
    close: () => pool.end(),
  };
}

