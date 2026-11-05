// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-postgresql-persistence
//   version: 1
//   status: draft
//   created_on: "2026-09-26"
//   updated_on: "2026-10-31"
//   layer: 04.deploy
//   domain: persistence
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Compose the harmless platform-smoke work-item persistence seam with the PostgreSQL adapter for disposable and later staging reference proofs.
//   portability:
//     class: internal
//     targets:
//     - kanbien/staging
//   used_by:
//   - id: aws.plan.kanbien-staging-postgresql-relational-reference-v1
//     path: docs/aws/kanbien-staging-postgresql-relational-reference-v1-deployment-plan.md

import type {
  PlatformSmokeWorkItem,
  PlatformSmokeWorkItemRepository,
} from "../../../../apps/platform-smoke/src/persistence/types";
import { ok } from "@kanbien/core/shared";
import {
  createPostgreSqlPlatformPersistenceAtomicWriter,
  postgreSqlMigrationChecksum,
  stagePostgreSqlTransactionStatement,
  type PostgreSqlConnectionPool,
  type PostgreSqlMigration,
  type PostgreSqlPersistenceConfiguration,
  type PostgreSqlPersistenceTelemetrySink,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";
import type { PlatformPersistenceAtomicWriter } from "@kanbien/platform-persistence";
import { observeKanbienPlatformPostgreSql, type CompositionBoundaryDetail, type KanbienPlatformPostgreSqlDiagnosticOptions } from "./kanbien-platform-postgresql-operation-diagnostics";

export interface KanbienPlatformPostgreSqlSmokePersistence {
  readonly atomicWriter: PlatformPersistenceAtomicWriter;
  readonly repository: PlatformSmokeWorkItemRepository;
}

export interface KanbienPlatformPostgreSqlSmokePersistenceOptions {
  readonly configuration: PostgreSqlPersistenceConfiguration;
  readonly pool: PostgreSqlConnectionPool;
  readonly telemetry?: PostgreSqlPersistenceTelemetrySink;
}

/**
 * This migration describes only the harmless smoke capability's state. The
 * reusable adapter owns platform tables and migration mechanics; it never
 * learns what a smoke work item means.
 */
export function kanbienPlatformSmokePostgreSqlMigration(schema: string, diagnostics?: KanbienPlatformPostgreSqlDiagnosticOptions): PostgreSqlMigration {
  let phase: CompositionBoundaryDetail["phase"] = "schema-predicate";
  let rejected = false;
  try {
  const table = platformSmokeWorkItemTable(schema, () => { rejected = true; observeKanbienPlatformPostgreSql(diagnostics, { operation: "migration", phase, condition: "predicate-rejected", effect: "not-started" }); });
  const statements = [{
    text: `CREATE TABLE IF NOT EXISTS ${table} (id text PRIMARY KEY, state text NOT NULL CHECK (state = 'accepted'), revision integer NOT NULL CHECK (revision > 0), accepted_at timestamptz NOT NULL)`,
  }];
  phase = "configuration";
  return {
    id: "v0002_platform_smoke_work_item",
    checksum: postgreSqlMigrationChecksum(statements),
    statements,
  };
  } catch (cause) {
    if (!rejected) observeKanbienPlatformPostgreSql(diagnostics, { operation: "migration", phase, condition: "threw", effect: "not-started" }, cause);
    throw cause;
  }
}

/**
 * Select PostgreSQL only at the target composition boundary. The app sees the
 * same provider-neutral repository and atomic-writer contracts it uses with
 * the completed DynamoDB reference.
 */
export function createKanbienPlatformPostgreSqlSmokePersistence(
  options: KanbienPlatformPostgreSqlSmokePersistenceOptions,
  diagnostics?: KanbienPlatformPostgreSqlDiagnosticOptions,
): KanbienPlatformPostgreSqlSmokePersistence {
  let phase: CompositionBoundaryDetail["phase"] = "configuration";
  let rejected = false;
  try {
  const table = platformSmokeWorkItemTable(options.configuration.schema, () => { rejected = true; observeKanbienPlatformPostgreSql(diagnostics, { operation: "compose", phase: "schema-predicate", condition: "predicate-rejected", effect: "not-started" }); }, () => { phase = "schema-predicate"; });
  phase = "writer-construction";
  return {
    atomicWriter: createPostgreSqlPlatformPersistenceAtomicWriter(
      options.configuration.schema,
      {
        pool: options.pool,
        ...(options.telemetry === undefined ? {} : { telemetry: options.telemetry }),
      },
    ),
    repository: {
      async create(input) {
        let phase: CompositionBoundaryDetail["phase"] = "input-projection";
        let stagedSuccessfully = false;
        try {
          const { workItem, transaction } = input;
          phase = "statement-staging";
          const staged = stagePostgreSqlTransactionStatement(transaction, stagingArgument(platformSmokeWorkItemInsert(table, workItem, (at) => { phase = at; })));
          phase = "staging-result";
          if (!staged.ok) {
            let source: unknown;
            try { const descriptor = Object.getOwnPropertyDescriptor(staged, "error"); if (descriptor !== undefined && "value" in descriptor) source = descriptor.value; } catch { /* Optional evidence unavailable. */ }
            observeKanbienPlatformPostgreSql(diagnostics, { operation: "create", phase, condition: "returned-failure", effect: "not-staged" }, source);
            return staged;
          }
          stagedSuccessfully = true;
          return ok(workItem);
        } catch (cause) {
          observeKanbienPlatformPostgreSql(diagnostics, { operation: "create", phase, condition: "threw", effect: stagedSuccessfully || phase === "statement-staging" || phase === "staging-result" ? "unknown" : "not-staged" }, cause);
          throw cause;
        }
        function stagingArgument<T>(statement: T): T { phase = "statement-staging"; return statement; }
      },
    },
  };
  } catch (cause) {
    if (!rejected) observeKanbienPlatformPostgreSql(diagnostics, { operation: "compose", phase, condition: "threw", effect: "not-started" }, cause);
    throw cause;
  }
}

function platformSmokeWorkItemInsert(
  table: string,
  workItem: PlatformSmokeWorkItem,
  location: (phase: CompositionBoundaryDetail["phase"]) => void,
) {
  return {
    text: `INSERT INTO ${table} (id, state, revision, accepted_at) VALUES ($1, $2, $3, $4)`,
    values: [(location("work-item-id"), String(workItem.id)), (location("work-item-state"), workItem.state), (location("work-item-revision"), Number(workItem.revision)), (location("work-item-accepted-at"), workItem.acceptedAt)],
  };
}

function platformSmokeWorkItemTable(schema: string, rejected: () => void, entered?: () => void): string {
  entered?.();
  if (!sqlIdentifierPattern.test(schema)) {
    rejected();
    throw new TypeError("The PostgreSQL smoke composition requires a reviewed lowercase schema identifier.");
  }
  return `"${schema}"."platform_smoke_work_item"`;
}

const sqlIdentifierPattern = /^[a-z][a-z0-9_]{0,62}$/;
