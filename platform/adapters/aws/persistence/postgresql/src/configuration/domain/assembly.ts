import type { PostgreSqlPersistenceConfigurationPolicy } from "../contract/types";
import { postgreSqlPersistenceConfiguration } from "./validation";

export function assemblePostgreSqlPersistenceConfiguration(values: Readonly<Record<string, string | number>>, policy: PostgreSqlPersistenceConfigurationPolicy) {
  return postgreSqlPersistenceConfiguration({
    host: values["database.host"] as string,
    port: values["database.port"] as number,
    database: values["database.name"] as string,
    schema: values["database.schema"] as string,
    runtimeCredentialSecretReference: values["authentication.reference"] as string,
    maximumPoolSize: policy.maximumPoolSize,
    connectionTimeoutMs: policy.connectionTimeoutMs,
    idleTimeoutMs: policy.idleTimeoutMs,
    statementTimeoutMs: policy.statementTimeoutMs,
    tls: policy.tls,
  });
}
