// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.database-verification
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: code
//   purpose: Prove effective runtime SQL denials or independently read original restored feature facts without recreating them.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { createHash } from "node:crypto";
import { createDiagnosticRecord } from "@kanbien/core/diagnostics";
import { systemClock } from "@kanbien/core/shared";
import { postgreSqlFailureDiagnostic, postgreSqlPersistenceOperationError, type PostgreSqlConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { entitySmokeDatabaseProofDiagnostic, reportEntitySmokeFailure } from "./diagnostics";
import { createEntitySmokePostgreSqlRuntime, entitySmokeRuntimeUsername } from "./postgresql";
import { entitySmokeRecordDigest } from "./proof-facts";

export interface EntitySmokeDatabaseProofOptions {
  readonly operation: "permissions" | "collision" | "restore-read";
  readonly label: string;
  readonly expectedDigest?: string;
}
type Step = "configuration" | "identity" | "read" | "collision" | "delete" | "truncate" | "create-table" | "alter-table" | "drop-table" | "history-write" | "rollback";
type Condition = "invalid-input" | "not-confirmed" | "unexpectedly-allowed" | "unexpected-failure" | "missing-record" | "multiple-records" | "digest-mismatch";

/** This task uses the runtime login, never an administrator selecting SET ROLE.
 * The controller binds its endpoint and resource incarnation. Restore reads
 * cannot bootstrap, migrate, grant access or recreate a missing record. */
export async function verifyEntitySmokeDatabase(pool: PostgreSqlConnectionPool, options: EntitySmokeDatabaseProofOptions) {
  let step: Step = "configuration";
  const rejected = (condition: Condition, effect: "not-started" | "not-assessed" | "unknown" = step === "configuration" ? "not-started" : "not-assessed") => {
    const record = createDiagnosticRecord(entitySmokeDatabaseProofDiagnostic, { operation: options.operation, step, condition, effect });
    return { code: "ENTITY_SMOKE_DATABASE_PROOF_NOT_CONFIRMED", defaultMessage: "The isolated database proof was not confirmed.", ...(record.ok ? { diagnosticRecord: record.value } : {}) };
  };
  if (!["permissions", "collision", "restore-read"].includes(options.operation) || !/^entity-smoke-[a-f0-9]{24}$/.test(options.label) || options.operation !== "permissions" && !/^[a-f0-9]{64}$/.test(options.expectedDigest ?? "")) throw rejected("invalid-input");
  step = "identity";
  const identity = await pool.query<{ username: string; superuser: boolean; create_role: boolean; create_database: boolean; replication: boolean; bypass_rls: boolean; inherit: boolean }>({
    text: "SELECT current_user AS username, rolsuper AS superuser, rolcreaterole AS create_role, rolcreatedb AS create_database, rolreplication AS replication, rolbypassrls AS bypass_rls, rolinherit AS inherit FROM pg_roles WHERE rolname = current_user",
  });
  const role = identity.rows[0];
  if (identity.rows.length !== 1 || !role || role.username !== entitySmokeRuntimeUsername || [role.superuser, role.create_role, role.create_database, role.replication, role.bypass_rls, role.inherit].some(value => value !== false)) throw rejected("not-confirmed");
  const steps: Step[] = [step];
  if (options.operation === "restore-read" || options.operation === "collision") {
    step = "read";
    const client = await pool.connect();
    let bodyFailed = false;
    try {
      await client.query({ text: options.operation === "restore-read" ? "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY" : "BEGIN" });
      await client.query({ text: "SET LOCAL statement_timeout = '5000ms'" });
      const readPool: PostgreSqlConnectionPool = { query: statement => client.query(statement), connect: async () => client, end: async () => undefined };
      const repository = createEntitySmokePostgreSqlRuntime(readPool).repository;
      const matches = (await repository.listByStatus("draft")).filter(entity => entity.label === options.label);
      if (matches.length === 0) throw rejected("missing-record");
      if (matches.length !== 1) throw rejected("multiple-records");
      const original = await repository.get(matches[0]!.id);
      if (!original || original.label !== options.label || original.lifecycle.state !== "active") throw rejected("missing-record");
      const digest = entitySmokeRecordDigest(original);
      if (digest !== options.expectedDigest) throw rejected("digest-mismatch");
      steps.push(step);
      if (options.operation === "collision") {
        step = "collision";
        await client.query({ text: "SAVEPOINT entity_smoke_duplicate_probe" });
        const duplicate = await repository.create({ ...original, integerValue: original.integerValue === 7 ? -42 : 7, label: original.label + "-collision" });
        // Undo even an incorrectly allowed upsert before reporting failure;
        // the correct insert-only repository receives a real PostgreSQL 23505.
        await client.query({ text: "ROLLBACK TO SAVEPOINT entity_smoke_duplicate_probe" });
        if (duplicate.ok) throw rejected("unexpectedly-allowed");
        if (duplicate.error.code !== "TEST_ENTITY_ID_CONFLICT") throw duplicate.error;
        steps.push(step); step = "read";
        const preserved = await repository.get(original.id);
        if (!preserved || entitySmokeRecordDigest(preserved) !== digest) throw rejected("digest-mismatch");
        steps.push(step);
      }
      return receipt(options.operation === "collision" ? "ENTITY_SMOKE_IDENTIFIER_COLLISION_PROVEN" : "ENTITY_SMOKE_RESTORED_RECORD_RETRIEVED", digest);
    } catch (cause) {
      bodyFailed = true; throw cause;
    } finally {
      try { await client.query({ text: "ROLLBACK" }); }
      catch {
        step = "rollback";
        const rollback = rejected("unexpected-failure", options.operation === "collision" ? "unknown" : "not-assessed");
        if (!bodyFailed) throw rollback;
        reportEntitySmokeFailure("verification", "unknown", rollback);
      }
      finally { client.release(); }
    }
  }
  const probes: readonly [Step, string][] = [
    ["delete", 'DELETE FROM "entity_smoke".test_entity WHERE false'],
    ["truncate", 'TRUNCATE "entity_smoke".test_entity'],
    ["create-table", 'CREATE TABLE "entity_smoke".__privilege_probe (id integer)'],
    ["alter-table", 'ALTER TABLE "entity_smoke".test_entity ADD COLUMN __privilege_probe integer'],
    ["drop-table", 'DROP TABLE "entity_smoke".test_entity'],
    ["history-write", 'UPDATE "entity_smoke".platform_migration_history SET checksum = checksum WHERE false'],
  ];
  const client = await pool.connect();
  try {
    for (const [name, text] of probes) {
      step = name;
      let denied = false;
      await client.query({ text: "BEGIN" });
      let failure: unknown, bodyFailed = false;
      try {
        await client.query({ text: "SET LOCAL statement_timeout = '5000ms'" });
        await client.query({ text: "SET LOCAL lock_timeout = '1000ms'" });
        try { await client.query({ text }); }
        catch (cause) {
          if (postgreSqlFailureDiagnostic(cause).facts.classification === "permission_denied") denied = true;
          else {
            const provider = postgreSqlPersistenceOperationError("administration", cause);
            failure = { ...rejected("unexpected-failure"), relatedDiagnosticRecords: [provider.diagnosticRecord, ...(provider.relatedDiagnosticRecords ?? [])].filter(value => value !== undefined) };
          }
        }
        if (!denied && failure === undefined) failure = rejected("unexpectedly-allowed");
      } catch (cause) { bodyFailed = true; throw cause; }
      finally {
        // Even an unexpectedly allowed DDL/TRUNCATE is rolled back. Failure to
        // confirm rollback is never accepted or followed by another probe.
        try { await client.query({ text: "ROLLBACK" }); }
        catch {
          step = "rollback";
          const rollback = rejected("unexpected-failure", "unknown");
          if (!bodyFailed && failure === undefined) throw rollback;
          reportEntitySmokeFailure("verification", "unknown", rollback);
        }
      }
      if (failure !== undefined) throw failure;
      steps.push(name);
    }
  } finally { client.release(); }
  return receipt("ENTITY_SMOKE_EFFECTIVE_PRIVILEGES_PROVEN");

  function receipt(code: string, digest?: string) {
    return { schema: "deploy/entity-smoke-database-proof/v1", verdict: "passed", operation: options.operation, code,
      proof_label_sha256: createHash("sha256").update(options.label).digest("hex"),
      ...(digest === undefined ? {} : { record_digest: digest }), steps, checked_at: systemClock.now().toISOString() };
  }
}
