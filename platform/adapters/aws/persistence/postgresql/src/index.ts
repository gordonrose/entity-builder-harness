export { postgreSqlPersistenceConfigurationTextRules, postgreSqlLoginNameRule } from "./configuration/index";
export { postgreSqlPasswordCredentials } from "./credentials";
export type { PostgreSqlPasswordCredentials, PostgreSqlCredentialIssue } from "./credentials";
export {
  postgreSqlPersistenceConfiguration,
} from "./configuration/index";
export type {
  PostgreSqlPersistenceConfiguration,
  PostgreSqlPersistenceConfigurationError,
} from "./configuration/index";

export {
  createNodePostgreSqlConnectionPool,
  createNodePostgreSqlTokenConnectionPool,
} from "./connection";
export type {
  PostgreSqlConnectionCredentials,
  PostgreSqlTokenConnectionCredentials,
  PostgreSqlConnectionPool,
  PostgreSqlQueryClient,
  PostgreSqlStatement,
  PostgreSqlTransactionalClient,
} from "./connection";
export { rdsIamAuthenticationToken, rdsIamAuthenticationTextRules } from "./rds-iam-authentication";
export type { RdsIamAuthenticationTokenOptions } from "./rds-iam-authentication";

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

export { adapterMetadata } from "./metadata";

export { observePostgreSqlOperation, postgreSqlFailureDiagnostic, postgreSqlFailureClassifications, postgreSqlPersistenceOperationError } from "./errors";
export type { PostgreSqlFailureDiagnostic, PostgreSqlFailureFacts, PostgreSqlFailureClassification, PostgreSqlObservedPhase } from "./errors";
export { postgreSqlSecurityDiagnosticRecords } from "./errors";

export { postgreSqlPersistenceRequirements, assemblePostgreSqlPersistenceConfiguration } from "./configuration/index";
export type { PostgreSqlPersistenceConfigurationPolicy } from "./configuration/index";
