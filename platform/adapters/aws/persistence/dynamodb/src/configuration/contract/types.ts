export interface DynamoDbPersistenceConfiguration {
  readonly region: string;
  readonly tableName: string;
  readonly outboxDueIndexName: string;
  readonly lineageCauseIndexName: string;
}
