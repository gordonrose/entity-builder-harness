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

export type PostgreSqlPersistenceConfigurationPolicy = Pick<PostgreSqlPersistenceConfiguration,
  "maximumPoolSize" | "connectionTimeoutMs" | "idleTimeoutMs" | "statementTimeoutMs" | "tls">;
