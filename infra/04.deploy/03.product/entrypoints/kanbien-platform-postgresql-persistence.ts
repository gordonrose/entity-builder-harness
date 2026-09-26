// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-postgresql-persistence
//   version: 1
//   status: draft
//   layer: 04.deploy
//   domain: persistence
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Compose the harmless platform-smoke work-item persistence seam with the PostgreSQL adapter for disposable and later staging reference proofs.
//   portability:
//     class: target-specific
//     targets:
//     - kanbien/staging

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
export function kanbienPlatformSmokePostgreSqlMigration(schema: string): PostgreSqlMigration {
  const table = platformSmokeWorkItemTable(schema);
  const statements = [{
    text: `CREATE TABLE IF NOT EXISTS ${table} (id text PRIMARY KEY, state text NOT NULL CHECK (state = 'accepted'), revision integer NOT NULL CHECK (revision > 0), accepted_at timestamptz NOT NULL)`,
  }];
  return {
    id: "v0002_platform_smoke_work_item",
    checksum: postgreSqlMigrationChecksum(statements),
    statements,
  };
}

/**
 * Select PostgreSQL only at the target composition boundary. The app sees the
 * same provider-neutral repository and atomic-writer contracts it uses with
 * the completed DynamoDB reference.
 */
export function createKanbienPlatformPostgreSqlSmokePersistence(
  options: KanbienPlatformPostgreSqlSmokePersistenceOptions,
): KanbienPlatformPostgreSqlSmokePersistence {
  const table = platformSmokeWorkItemTable(options.configuration.schema);
  return {
    atomicWriter: createPostgreSqlPlatformPersistenceAtomicWriter(
      options.configuration.schema,
      {
        pool: options.pool,
        ...(options.telemetry === undefined ? {} : { telemetry: options.telemetry }),
      },
    ),
    repository: {
      async create({ workItem, transaction }) {
        const staged = stagePostgreSqlTransactionStatement(transaction, platformSmokeWorkItemInsert(table, workItem));
        if (!staged.ok) return staged;
        return ok(workItem);
      },
    },
  };
}

function platformSmokeWorkItemInsert(
  table: string,
  workItem: PlatformSmokeWorkItem,
) {
  return {
    text: `INSERT INTO ${table} (id, state, revision, accepted_at) VALUES ($1, $2, $3, $4)`,
    values: [String(workItem.id), workItem.state, Number(workItem.revision), workItem.acceptedAt],
  };
}

function platformSmokeWorkItemTable(schema: string): string {
  if (!sqlIdentifierPattern.test(schema)) {
    throw new TypeError("The PostgreSQL smoke composition requires a reviewed lowercase schema identifier.");
  }
  return `"${schema}"."platform_smoke_work_item"`;
}

const sqlIdentifierPattern = /^[a-z][a-z0-9_]{0,62}$/;
