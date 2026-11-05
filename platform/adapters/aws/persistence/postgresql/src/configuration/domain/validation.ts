import { destinationPortConstraint, type ConfigIssueReason } from "@kanbien/core/config";
import type { PostgreSqlPersistenceConfiguration } from "../contract/types";
import type { PostgreSqlPersistenceConfigurationError } from "../contract/errors";
import { hostPattern, sqlIdentifierPattern, authenticationReferencePattern } from "../contract/requirements";

export function postgreSqlPersistenceConfiguration(
  input: PostgreSqlPersistenceConfiguration,
): { readonly ok: true; readonly value: PostgreSqlPersistenceConfiguration } | { readonly ok: false; readonly error: PostgreSqlPersistenceConfigurationError } {
  if (typeof input !== "object" || input === null) return invalid("configuration", "A configuration object is required.", "wrong-type");
  const stringFields: ReadonlyArray<readonly [string, string]> = [
    ["host", input.host],
    ["database", input.database],
    ["schema", input.schema],
    ["runtimeCredentialSecretReference", input.runtimeCredentialSecretReference],
  ];
  for (const [path, value] of stringFields) {
    if (value === undefined) return invalid(path, "A non-empty trimmed value is required.", "missing");
    if (typeof value !== "string") return invalid(path, "A non-empty trimmed value is required.", "wrong-type");
    if (value.trim().length === 0) return invalid(path, "A non-empty trimmed value is required.", "blank");
    if (value.trim() !== value) return invalid(path, "A non-empty trimmed value is required.", "surrounding-whitespace");
  }
  if (!hostPattern.test(input.host)) return invalid("host", "Host must be a DNS name, IPv4 address, or IPv6 literal without a scheme.");
  if (!sqlIdentifierPattern.test(input.database)) return invalid("database", "Database must be a reviewed lowercase SQL identifier.");
  if (!sqlIdentifierPattern.test(input.schema)) return invalid("schema", "Schema must be a reviewed lowercase SQL identifier.");
  if (!authenticationReferencePattern.test(input.runtimeCredentialSecretReference)) return invalid("runtimeCredentialSecretReference", "Runtime authentication must use an explicit Secrets Manager or RDS IAM database-user reference.");
  const portIssue = integerIssue(input.port, destinationPortConstraint.minimum, destinationPortConstraint.maximum);
  if (portIssue) return invalid("port", "Port must be an integer between 1 and 65535.", portIssue);
  const poolIssue = integerIssue(input.maximumPoolSize, 1, 10);
  if (poolIssue) return invalid("maximumPoolSize", "Maximum pool size must be an integer between 1 and 10.", poolIssue);
  for (const [path, value] of [
    ["connectionTimeoutMs", input.connectionTimeoutMs],
    ["idleTimeoutMs", input.idleTimeoutMs],
  ] as const) {
    const issue = integerIssue(value, 100, 60_000);
    if (issue) return invalid(path, "Timeout must be an integer between 100 and 60000 milliseconds.", issue);
  }
  // A migration may need longer than an ordinary request, but it must remain
  // bounded. The persistence scope declares a 240-second migration deadline.
  const statementIssue = integerIssue(input.statementTimeoutMs, 100, 300_000);
  if (statementIssue) {
    return invalid("statementTimeoutMs", "Statement timeout must be an integer between 100 and 300000 milliseconds.", statementIssue);
  }
  if (input.tls === undefined) return invalid("tls", "TLS configuration is required.", "missing");
  if (typeof input.tls !== "object" || input.tls === null) return invalid("tls", "TLS configuration must be an object.", "wrong-type");
  if (input.tls.mode !== "verify-full" || input.tls.certificateAuthoritySource !== "injected") {
    return invalid("tls", "TLS must use injected certificate authority material and verify the server identity.");
  }
  return {
    ok: true,
    value: {
      ...input,
      tls: { ...input.tls },
    },
  };
}

export function postgreSqlIdentifier(value: string): string | undefined {
  return sqlIdentifierPattern.test(value) ? value : undefined;
}

function invalid(path: string, reason: string, reasonCode: ConfigIssueReason = "invalid-format"): { readonly ok: false; readonly error: PostgreSqlPersistenceConfigurationError } {
  return {
    ok: false,
    error: {
      code: "PLATFORM_ADAPTER_AWS_POSTGRESQL_PERSISTENCE_CONFIG_INVALID",
      defaultMessage: "PostgreSQL persistence adapter configuration is invalid.",
      details: { path, reason, reasonCode },
    },
  };
}

function integerIssue(value: unknown, minimum: number, maximum: number): ConfigIssueReason | undefined {
  return value === undefined ? "missing" : typeof value !== "number" ? "wrong-type" : !Number.isInteger(value) ? "invalid-integer"
    : value < minimum || value > maximum ? "out-of-range" : undefined;
}
