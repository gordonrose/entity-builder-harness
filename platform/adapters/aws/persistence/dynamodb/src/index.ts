export {
  dynamoDbPersistenceConfiguration,
} from "./configuration";
export type {
  DynamoDbPersistenceConfiguration,
  DynamoDbPersistenceConfigurationError,
} from "./configuration";

export {
  createAwsSdkDynamoDbPersistenceCommandClient,
} from "./client";
export type {
  DynamoDbPersistenceCommandClient,
} from "./client";

export {
  createDynamoDbPlatformOutboxStore,
} from "./outbox-store";
export type {
  DynamoDbPlatformOutboxStoreOptions,
} from "./outbox-store";

export {
  createDynamoDbPlatformProcessingStore,
} from "./processing-store";
export type {
  DynamoDbPlatformProcessingStoreOptions,
} from "./processing-store";

export {
  createDynamoDbPlatformRecordChangeStore,
} from "./lineage-store";
export type {
  DynamoDbPlatformRecordChangeStoreOptions,
} from "./lineage-store";

export {
  createDynamoDbPlatformPersistenceAtomicWriter,
  createDynamoDbPlatformPersistenceFactWriter,
  dynamoDbPlatformPersistenceAtomicTransaction,
  dynamoDbPlatformPersistenceFactTransaction,
  stageDynamoDbTransactionWrite,
} from "./transactions";
export type {
  DynamoDbPlatformPersistenceAtomicWriter,
  DynamoDbPlatformPersistenceAtomicWriterOptions,
  DynamoDbPlatformPersistenceFactWriter,
  DynamoDbPlatformPersistenceFactWriterOptions,
} from "./transactions";

export const adapterMetadata = {
  provider: "aws",
  capability: "persistence",
  implementation: "dynamodb",
  packageName: "@kanbien/platform-adapter-aws-persistence-dynamodb",
} as const;
