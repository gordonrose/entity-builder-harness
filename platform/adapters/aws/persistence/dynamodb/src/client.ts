import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import type { DynamoDbPersistenceConfiguration } from "./configuration";

/** The smallest AWS SDK surface required by deterministic adapter tests. */
export interface DynamoDbPersistenceCommandClient {
  send(command: unknown): Promise<unknown>;
}

export function createAwsSdkDynamoDbPersistenceCommandClient(
  configuration: DynamoDbPersistenceConfiguration,
): DynamoDbPersistenceCommandClient {
  return new DynamoDBClient({ region: configuration.region }) as unknown as DynamoDbPersistenceCommandClient;
}
