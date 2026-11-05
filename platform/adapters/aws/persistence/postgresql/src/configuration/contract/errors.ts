import type { ConfigIssueReason } from "@kanbien/core/config";

export interface PostgreSqlPersistenceConfigurationError {
  readonly code: "PLATFORM_ADAPTER_AWS_POSTGRESQL_PERSISTENCE_CONFIG_INVALID";
  readonly defaultMessage: string;
  readonly details: Readonly<{ readonly path: string; readonly reason: string; readonly reasonCode: ConfigIssueReason }>;
}
