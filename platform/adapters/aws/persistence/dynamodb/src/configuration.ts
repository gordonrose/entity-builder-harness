export interface DynamoDbPersistenceConfiguration {
  readonly region: string;
  readonly tableName: string;
  readonly outboxDueIndexName: string;
  readonly lineageCauseIndexName: string;
}

export interface DynamoDbPersistenceConfigurationError {
  readonly code: "PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID";
  readonly defaultMessage: string;
  readonly details: Readonly<{ readonly path: string; readonly reason: string }>;
}

export function dynamoDbPersistenceConfiguration(
  input: DynamoDbPersistenceConfiguration,
): { readonly ok: true; readonly value: DynamoDbPersistenceConfiguration } | { readonly ok: false; readonly error: DynamoDbPersistenceConfigurationError } {
  for (const [path, value] of Object.entries(input)) {
    if (value.trim().length === 0) {
      return {
        ok: false,
        error: {
          code: "PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID",
          defaultMessage: "DynamoDB persistence adapter configuration is invalid.",
          details: { path, reason: "A non-empty value is required." },
        },
      };
    }
  }

  if (input.tableName.length > 255 || input.outboxDueIndexName.length > 255 || input.lineageCauseIndexName.length > 255) {
    return {
      ok: false,
      error: {
        code: "PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID",
        defaultMessage: "DynamoDB persistence adapter configuration is invalid.",
        details: { path: "tableName", reason: "Table and index names must be at most 255 characters." },
      },
    };
  }

  return { ok: true, value: { ...input } };
}
