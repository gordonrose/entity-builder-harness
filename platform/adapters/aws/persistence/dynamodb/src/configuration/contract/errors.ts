import type { DiagnosticRecord } from "@kanbien/core/diagnostics";

export interface DynamoDbPersistenceConfigurationError {
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly code: "PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID";
  readonly defaultMessage: string;
  readonly details: Readonly<{ readonly path: string; readonly reason: string }>;
}
