import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import type { DynamoDbPersistenceConfiguration } from "./configuration/index";
import type { PlatformPersistenceDiagnosticOptions } from "@kanbien/platform-persistence";
import { dynamoDbObservation } from "./observations";

/** The smallest AWS SDK surface required by deterministic adapter tests. */
export interface DynamoDbPersistenceCommandClient {
  send(command: unknown): Promise<unknown>;
}

export function createAwsSdkDynamoDbPersistenceCommandClient(
  configuration: DynamoDbPersistenceConfiguration,
  diagnostics?: PlatformPersistenceDiagnosticOptions,
): DynamoDbPersistenceCommandClient {
  return dynamoDbObservation(diagnostics, "client-initialization").at("client-construction", () => new DynamoDBClient({ region: configuration.region }) as unknown as DynamoDbPersistenceCommandClient);
}
