// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.postgresql
//   version: 2
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Bind app-owned SQL statements to an isolated PostgreSQL schema and retain classified failure evidence.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { relationalTestEntityRepository, testEntityMigration, testEntityCreationConflict, testEntityDiagnosticCatalog, type TestEntityRelationalExecutor, type TestEntityDeletionTransaction } from "@kanbien/app-entity-smoke";
import { ok } from "@kanbien/core/shared";
import { diagnosticRelatedRecordLimit } from "@kanbien/core/diagnostics";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import { postgreSqlFailureDiagnostic, postgreSqlPersistenceOperationError, postgreSqlMigrationChecksum,
  postgreSqlPersistenceFoundationMigration, postgreSqlPlatformScheduleHandoffMigration, postgreSqlPlatformScheduleMigration, postgreSqlSecurityDiagnosticRecords,
  postgreSqlPlatformScheduleSubjectMigration, postgreSqlPlatformProcessingRetryMigration, postgreSqlPlatformScheduleControlMigration,
  createPostgreSqlPlatformScheduleStore, withPostgreSqlTransaction, type PostgreSqlConnectionPool, type PostgreSqlQueryClient, type PostgreSqlPersistenceConfiguration } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { persistenceCrudObservedDiagnosticRecord, platformPersistenceError,
  selectPlatformPersistenceDiagnosticEvidence, platformPersistenceDiagnosticCatalog } from "@kanbien/platform-persistence";

export const entitySmokeSchema = "entity_smoke";
export const entitySmokeRuntimeUsername = "entity_smoke_runtime";
export const entitySmokeMigrationUsername = "entity_smoke_migration";

/** Both the feature SQL and migration share this reviewed, fixed isolation boundary. */
export function entitySmokeSql(text: string): string {
  return text.replaceAll("__SCHEMA__", '"entity_smoke"');
}

export function entitySmokeMigrationManifest(profile: "baseline" | "scheduling" = "scheduling") {
  const foundation = postgreSqlPersistenceFoundationMigration(entitySmokeSchema);
  const migrations = [testEntityMigration, postgreSqlPlatformScheduleMigration(entitySmokeSchema, "v0004_entity_smoke_platform_schedule"),
    { ...foundation, id: "v0005_entity_smoke_platform_outbox_foundation" },
    postgreSqlPlatformScheduleHandoffMigration(entitySmokeSchema, "v0006_entity_smoke_platform_schedule_handoff"),
    ...(profile === "baseline" ? [] : [
    postgreSqlPlatformScheduleSubjectMigration(entitySmokeSchema, "v0007_entity_smoke_schedule_subject"),
    postgreSqlPlatformProcessingRetryMigration(entitySmokeSchema, "v0008_entity_smoke_processing_retry"),
    postgreSqlPlatformScheduleControlMigration(entitySmokeSchema, "v0009_entity_smoke_schedule_control")])];
  return { schema: entitySmokeSchema, schemaPreprovisioned: true, migrations: migrations.map(migration => {
    const statements = migration.statements.map(statement => ({ text: entitySmokeSql(statement.text) }));
    return { id: migration.id, statements, checksum: postgreSqlMigrationChecksum(statements) };
  }) } as const;
}

/** Accepted release98f40c/source19b0fd3 had only the feature migration, not today's four-entry baseline. */
export function entitySmokeSchedulingContinuationManifest() {
  return { ...entitySmokeMigrationManifest("scheduling"), continuation: { minimumAppliedMigrations: 1 } } as const;
}

function entitySmokeExecutor(pool: PostgreSqlQueryClient): TestEntityRelationalExecutor {
  return { async execute(statement, operation) {
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
}

export function createEntitySmokePostgreSqlRuntime(pool: PostgreSqlConnectionPool, configuration?: PostgreSqlPersistenceConfiguration) {
  const executor = entitySmokeExecutor(pool);
  const diagnostics = { diagnosticDefinitions: [...coreDiagnosticCatalog.definitions,
    ...platformPersistenceDiagnosticCatalog.definitions, ...platformSecurityDiagnosticCatalog.definitions, ...testEntityDiagnosticCatalog.definitions] };
  const deletionTransaction: TestEntityDeletionTransaction | undefined = configuration === undefined ? undefined : {
    run: operation => withPostgreSqlTransaction({ pool, ...diagnostics }, async client => {
      const participantPool: PostgreSqlConnectionPool = { query: statement => client.query(statement),
        connect: async () => { throw new TypeError("Nested entity deletion transactions are not supported."); }, end: async () => undefined };
      return operation({ repository: relationalTestEntityRepository(entitySmokeExecutor(client), { lockForMutation: true }),
        schedules: createPostgreSqlPlatformScheduleStore({ configuration, pool: participantPool, ...diagnostics }) });
    }),
  };
  return {
    repository: relationalTestEntityRepository(executor),
    ...(deletionTransaction === undefined ? {} : { deletionTransaction }),
    readiness: async () => {
      const result = await executor.execute({ text: "SELECT id FROM __SCHEMA__.test_entity LIMIT 1", values: [] }, "read");
      return result.ok ? { readiness: "ready" as const } : { readiness: "not-ready" as const,
        ...(result.error.diagnosticRecord === undefined ? {} : { diagnosticRecord: result.error.diagnosticRecord }),
        ...(result.error.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: result.error.relatedDiagnosticRecords }) };
    },
    close: () => pool.end(),
  };
}

