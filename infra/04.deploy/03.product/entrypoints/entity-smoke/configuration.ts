// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.configuration
//   version: 1
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Validate isolated feature settings before selecting any database or runtime identity.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { readFileSync } from "node:fs";
import { err, ok } from "@kanbien/core/shared";
import { recordConfigSource, validateConfigSettings } from "@kanbien/core/config";
import { loadPlatformConfiguration } from "@kanbien/platform-config";
import { assemblePostgreSqlPersistenceConfiguration, postgreSqlPersistenceRequirements,
  rdsIamAuthenticationTextRules, rdsIamAuthenticationToken } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { validateCertificateAuthorityContent } from "@kanbien/platform-security";
import { entitySmokeConfigurationError, entitySmokeDatabaseConfigurationError } from "./diagnostics";
import { entitySmokeSchema, entitySmokeRuntimeUsername, entitySmokeMigrationUsername } from "./postgresql";

const bindings = { "database.host": "PERSISTENCE_POSTGRES_HOST", "database.port": "PERSISTENCE_POSTGRES_PORT",
  "database.name": "PERSISTENCE_POSTGRES_DATABASE", "database.schema": "PERSISTENCE_POSTGRES_SCHEMA",
  "authentication.reference": "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE" } as const;
export type EntitySmokeDatabasePurpose = "runtime" | "migration";

/** Fixed schema and role separation cannot be replaced by environment input. */
export function entitySmokeDatabaseSettings(env: NodeJS.ProcessEnv, purpose: EntitySmokeDatabasePurpose,
  readAuthority: (path: string) => string = path => readFileSync(path, "utf8")) {
  const username = purpose === "runtime" ? entitySmokeRuntimeUsername : entitySmokeMigrationUsername;
  const usernameKey = purpose === "runtime" ? "PERSISTENCE_RUNTIME_DATABASE_USERNAME" : "PERSISTENCE_MIGRATION_DATABASE_USERNAME";
  if (env["PERSISTENCE_POSTGRES_SCHEMA"] !== entitySmokeSchema) return err(entitySmokeConfigurationError("schema", "mismatch"));
  if (env[usernameKey] !== username) return err(entitySmokeConfigurationError("identity", "mismatch"));
  if (purpose === "runtime" && env["PLATFORM_DEPLOYMENT_EXPOSURE"] !== "private") return err(entitySmokeConfigurationError("exposure", "mismatch"));
  const parsed = loadPlatformConfiguration({ requirements: postgreSqlPersistenceRequirements, bindings,
    source: recordConfigSource(env), assemble: values => assemblePostgreSqlPersistenceConfiguration(values, {
      maximumPoolSize: purpose === "runtime" ? 4 : 1, connectionTimeoutMs: 5000, idleTimeoutMs: 10000,
      statementTimeoutMs: purpose === "runtime" ? 5000 : 240000,
      tls: { mode: "verify-full", certificateAuthoritySource: "injected" },
    }) });
  if (!parsed.ok) {
    if (parsed.error.code === "CONFIGURATION_INVALID") return err(entitySmokeDatabaseConfigurationError(parsed.error.issues));
    const fields: Record<string, string> = { host: "database.host", port: "database.port", database: "database.name", schema: "database.schema", runtimeCredentialSecretReference: "authentication.reference" };
    return err(entitySmokeDatabaseConfigurationError([{ setting: fields[parsed.error.details.path] ?? "database", reason: parsed.error.details.reasonCode }]));
  }
  const reference = parsed.value.runtimeCredentialSecretReference;
  if (!reference.endsWith("/" + username) || !reference.includes(":rds-db:")) return err(entitySmokeConfigurationError("identity", "mismatch"));
  const region = validateConfigSettings(recordConfigSource(env), [
    { setting: "region", source: "PERSISTENCE_POSTGRES_IAM_REGION", rule: rdsIamAuthenticationTextRules.region },
  ]);
  if (!region.ok) return err(entitySmokeDatabaseConfigurationError(region.error.issues));
  const path = env["PERSISTENCE_POSTGRES_CA_PATH"];
  if (path !== "/app/assets/rds-eu-west-1-bundle.crt") return err(entitySmokeConfigurationError("authority", "mismatch"));
  let certificateAuthority: string;
  try { certificateAuthority = readAuthority(path); }
  catch { return err(entitySmokeConfigurationError("authority", "unavailable")); }
  const authority = validateCertificateAuthorityContent(certificateAuthority);
  if (!authority.ok) return authority;
  const localToken = env["ENTITY_SMOKE_LOCAL_QUALIFICATION_TOKEN"];
  if (localToken !== undefined && (env["NODE_ENV"] !== "test" || localToken !== "entity-smoke-disposable-fixture")) return err(entitySmokeConfigurationError("identity", "invalid"));
  const authenticationToken = localToken === undefined
    ? rdsIamAuthenticationToken({ region: region.value["region"] as string, hostname: parsed.value.host, port: parsed.value.port, username })
    : async () => localToken;
  return ok({ configuration: parsed.value, credentials: { username, certificateAuthority, authenticationToken } });
}

