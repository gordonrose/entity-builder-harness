export {
  postgreSqlPersistenceConfiguration,
} from "./config";
export type {
  PostgreSqlPersistenceConfiguration,
  PostgreSqlPersistenceConfigurationError,
} from "./config";

export {
  createNodePostgreSqlConnectionPool,
} from "./connection";
export type {
  PostgreSqlConnectionCredentials,
  PostgreSqlConnectionPool,
  PostgreSqlQueryClient,
  PostgreSqlStatement,
  PostgreSqlTransactionalClient,
} from "./connection";

export {
  createPostgreSqlMigrationRunner,
  postgreSqlMigrationChecksum,
  postgreSqlPersistenceFoundationMigration,
} from "./migrations";
export type {
  PostgreSqlMigration,
  PostgreSqlMigrationManifest,
  PostgreSqlMigrationResult,
  PostgreSqlMigrationRunner,
} from "./migrations";

export {
  createPostgreSqlPlatformOutboxStore,
} from "./outbox";
export type {
  PostgreSqlPlatformOutboxStoreOptions,
} from "./outbox";

export {
  createPostgreSqlPlatformProcessingStore,
} from "./processing";
export type {
  PostgreSqlPlatformProcessingStoreOptions,
} from "./processing";

export {
  createPostgreSqlPlatformRecordChangeStore,
} from "./lineage";
export type {
  PostgreSqlPlatformRecordChangeStoreOptions,
} from "./lineage";

export {
  createPostgreSqlPlatformPersistenceAtomicWriter,
  createPostgreSqlPlatformPersistenceFactWriter,
  stagePostgreSqlTransactionStatement,
  withPostgreSqlTransaction,
} from "./transactions";
export type {
  PostgreSqlPlatformPersistenceAtomicWriter,
  PostgreSqlPlatformPersistenceFactWriter,
  PostgreSqlTransactionOptions,
} from "./transactions";

export {
  postgreSqlPlatformPersistenceObserver,
  recordPostgreSqlPersistenceTelemetry,
} from "./telemetry";
export type {
  PostgreSqlPersistenceTelemetry,
  PostgreSqlPersistenceTelemetrySink,
} from "./telemetry";

export const adapterMetadata = {
  provider: "aws",
  capability: "persistence",
  implementation: "postgresql",
  packageName: "@kanbien/platform-adapter-aws-persistence-postgresql",
} as const;
