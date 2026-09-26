export interface PostgreSqlPersistenceConfiguration {
  readonly host: string;
  readonly port: number;
  readonly database: string;
  readonly schema: string;
  readonly runtimeCredentialSecretReference: string;
  readonly maximumPoolSize: number;
  readonly connectionTimeoutMs: number;
  readonly idleTimeoutMs: number;
  readonly statementTimeoutMs: number;
  readonly tls: {
    readonly mode: "verify-full";
    readonly certificateAuthoritySource: "injected";
  };
}

export interface PostgreSqlPersistenceConfigurationError {
  readonly code: "PLATFORM_ADAPTER_AWS_POSTGRESQL_PERSISTENCE_CONFIG_INVALID";
  readonly defaultMessage: string;
  readonly details: Readonly<{ readonly path: string; readonly reason: string }>;
}

export function postgreSqlPersistenceConfiguration(
  input: PostgreSqlPersistenceConfiguration,
): { readonly ok: true; readonly value: PostgreSqlPersistenceConfiguration } | { readonly ok: false; readonly error: PostgreSqlPersistenceConfigurationError } {
  const stringFields: ReadonlyArray<readonly [string, string]> = [
    ["host", input.host],
    ["database", input.database],
    ["schema", input.schema],
    ["runtimeCredentialSecretReference", input.runtimeCredentialSecretReference],
  ];
  for (const [path, value] of stringFields) {
    if (value.trim().length === 0 || value.trim() !== value) return invalid(path, "A non-empty trimmed value is required.");
  }
  if (!hostPattern.test(input.host)) return invalid("host", "Host must be a DNS name, IPv4 address, or IPv6 literal without a scheme.");
  if (!sqlIdentifierPattern.test(input.database)) return invalid("database", "Database must be a reviewed lowercase SQL identifier.");
  if (!sqlIdentifierPattern.test(input.schema)) return invalid("schema", "Schema must be a reviewed lowercase SQL identifier.");
  if (!secretReferencePattern.test(input.runtimeCredentialSecretReference)) return invalid("runtimeCredentialSecretReference", "Runtime credentials must use an explicit Secrets Manager reference.");
  if (!Number.isInteger(input.port) || input.port < 1 || input.port > 65_535) return invalid("port", "Port must be an integer between 1 and 65535.");
  if (!Number.isInteger(input.maximumPoolSize) || input.maximumPoolSize < 1 || input.maximumPoolSize > 10) return invalid("maximumPoolSize", "Maximum pool size must be an integer between 1 and 10.");
  for (const [path, value] of [
    ["connectionTimeoutMs", input.connectionTimeoutMs],
    ["idleTimeoutMs", input.idleTimeoutMs],
    ["statementTimeoutMs", input.statementTimeoutMs],
  ] as const) {
    if (!Number.isInteger(value) || value < 100 || value > 60_000) return invalid(path, "Timeout must be an integer between 100 and 60000 milliseconds.");
  }
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

function invalid(path: string, reason: string): { readonly ok: false; readonly error: PostgreSqlPersistenceConfigurationError } {
  return {
    ok: false,
    error: {
      code: "PLATFORM_ADAPTER_AWS_POSTGRESQL_PERSISTENCE_CONFIG_INVALID",
      defaultMessage: "PostgreSQL persistence adapter configuration is invalid.",
      details: { path, reason },
    },
  };
}

const sqlIdentifierPattern = /^[a-z][a-z0-9_]{0,62}$/;
const hostPattern = /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?|\[[0-9a-fA-F:]+\])$/;
const secretReferencePattern = /^arn:aws(?:-[a-z]+)?:secretsmanager:[a-z0-9-]+:\d{12}:secret:[A-Za-z0-9/_+=.@-]+$/;
