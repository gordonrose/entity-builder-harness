// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-migration
//   version: 1
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-23"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Apply the reviewed, checksummed persistence migration manifest with the isolated migration credential.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import { readFileSync } from "node:fs";
import {
  createNodePostgreSqlConnectionPool,
  createPostgreSqlMigrationRunner,
  postgreSqlMigrationChecksum,
  postgreSqlPersistenceConfiguration,
  postgreSqlPersistenceFoundationMigration,
  type PostgreSqlConnectionPool,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { kanbienCoreServerPersistenceAcceptanceMigration } from "./kanbien-core-server-persistence-postgresql";

export async function runKanbienCoreServerPersistenceMigration(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const configuration = configurationFromEnvironment(env);
  const credentials = credentialObject(env["PERSISTENCE_MIGRATION_CREDENTIALS"]);
  const runtimeCredentials = credentialObject(env["PERSISTENCE_RUNTIME_BOOTSTRAP_CREDENTIALS"]);
  const certificateAuthority = certificateAuthorityFromEnvironment(env);
  if (configuration === undefined || credentials === undefined || runtimeCredentials === undefined || certificateAuthority === undefined) return rejected("PERSISTENCE_MIGRATION_CONFIGURATION_INVALID");
  const pool = createNodePostgreSqlConnectionPool(configuration, { ...credentials, certificateAuthority });
  let stage: "migration" | "runtime-access" = "migration";
  try {
    const acceptance = kanbienCoreServerPersistenceAcceptanceMigration(configuration.schema);
    const result = await createPostgreSqlMigrationRunner(configuration, { pool }, "core-server-persistence-v1").apply({
      schema: configuration.schema,
      migrations: [postgreSqlPersistenceFoundationMigration(configuration.schema), { ...acceptance, checksum: postgreSqlMigrationChecksum(acceptance.statements) }],
    });
    if (!result.ok) return rejected("PERSISTENCE_MIGRATION_NOT_CONFIRMED", stage, migrationFailureClass(result.error));
    stage = "runtime-access";
    await provisionRuntimeAccess(pool, {
      database: configuration.database,
      schema: configuration.schema,
      migrationUsername: credentials.username,
      runtimeCredentials,
    });
    console.log(JSON.stringify({ verdict: "accepted", code: "PERSISTENCE_MIGRATION_APPLIED" }));
  } catch { rejected("PERSISTENCE_MIGRATION_NOT_CONFIRMED", stage); } finally { await pool.end(); }
}
function configurationFromEnvironment(env: NodeJS.ProcessEnv) {
  const host = text(env, "PERSISTENCE_POSTGRES_HOST"), database = text(env, "PERSISTENCE_POSTGRES_DATABASE"), schema = text(env, "PERSISTENCE_POSTGRES_SCHEMA"), reference = text(env, "PERSISTENCE_MIGRATION_SECRET_REFERENCE"), port = text(env, "PERSISTENCE_POSTGRES_PORT");
  if (host === undefined || database === undefined || schema === undefined || reference === undefined || port === undefined || !/^\d+$/.test(port)) return undefined;
  const checked = postgreSqlPersistenceConfiguration({ host, database, schema, runtimeCredentialSecretReference: reference, port: Number(port), maximumPoolSize: 1, connectionTimeoutMs: 5_000, idleTimeoutMs: 10_000, statementTimeoutMs: 240_000, tls: { mode: "verify-full", certificateAuthoritySource: "injected" } });
  return checked.ok ? checked.value : undefined;
}
function certificateAuthorityFromEnvironment(env: NodeJS.ProcessEnv): string | undefined { const path = text(env, "PERSISTENCE_POSTGRES_CA_PATH"); try { return path?.startsWith("/app/assets/") ? readFileSync(path, "utf8") : undefined; } catch { return undefined; } }
function text(env: NodeJS.ProcessEnv, key: string): string | undefined { const value = env[key]; return typeof value === "string" && value.trim() !== "" && value.trim() === value ? value : undefined; }
function credentialObject(value: unknown): { readonly username: string; readonly password: string } | undefined { try { const parsed: unknown = typeof value === "string" ? JSON.parse(value) : undefined; if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return undefined; const username = (parsed as { username?: unknown }).username, password = (parsed as { password?: unknown }).password; return typeof username === "string" && username.trim() !== "" && typeof password === "string" && password.length > 0 ? { username, password } : undefined; } catch { return undefined; } }

/**
 * The migration credential owns database structure. It deliberately creates
 * and maintains a separate, minimally-granted runtime principal after the
 * schema is known. This also makes a later coordinated runtime-secret
 * rotation effective only after this task has applied the matching role
 * password and grants; completed tasks are never replayed automatically.
 */
async function provisionRuntimeAccess(
  pool: PostgreSqlConnectionPool,
  input: {
    readonly database: string;
    readonly schema: string;
    readonly migrationUsername: string;
    readonly runtimeCredentials: { readonly username: string; readonly password: string };
  },
): Promise<void> {
  const database = quotedIdentifier(input.database);
  const schema = quotedIdentifier(input.schema);
  const migrationUsername = quotedIdentifier(input.migrationUsername);
  const runtimeUsername = quotedIdentifier(input.runtimeCredentials.username);
  const role = await pool.query<{ readonly exists: boolean }>({
    text: "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = $1) AS exists",
    values: [input.runtimeCredentials.username],
  });
  const password = quotedLiteral(input.runtimeCredentials.password);
  await pool.query({ text: role.rows[0]?.exists ? `ALTER ROLE ${runtimeUsername} LOGIN PASSWORD ${password}` : `CREATE ROLE ${runtimeUsername} LOGIN PASSWORD ${password}` });
  await pool.query({ text: `GRANT CONNECT ON DATABASE ${database} TO ${runtimeUsername}` });
  await pool.query({ text: `GRANT USAGE ON SCHEMA ${schema} TO ${runtimeUsername}` });
  await pool.query({ text: `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ${schema} TO ${runtimeUsername}` });
  await pool.query({ text: `GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ${schema} TO ${runtimeUsername}` });
  await pool.query({ text: `GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA ${schema} TO ${runtimeUsername}` });
  await pool.query({ text: `ALTER DEFAULT PRIVILEGES FOR ROLE ${migrationUsername} IN SCHEMA ${schema} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${runtimeUsername}` });
  await pool.query({ text: `ALTER DEFAULT PRIVILEGES FOR ROLE ${migrationUsername} IN SCHEMA ${schema} GRANT USAGE, SELECT ON SEQUENCES TO ${runtimeUsername}` });
  await pool.query({ text: `ALTER DEFAULT PRIVILEGES FOR ROLE ${migrationUsername} IN SCHEMA ${schema} GRANT EXECUTE ON FUNCTIONS TO ${runtimeUsername}` });
}

function quotedIdentifier(value: string): string {
  if (!/^[a-z_][a-z0-9_]{0,62}$/.test(value)) throw new TypeError("PERSISTENCE_ROLE_IDENTIFIER_INVALID");
  return `"${value}"`;
}

function quotedLiteral(value: string): string {
  if (value.length === 0 || value.includes("\u0000")) throw new TypeError("PERSISTENCE_CREDENTIAL_INVALID");
  return `'${value.replaceAll("'", "''")}'`;
}
function rejected(code: string, stage?: "migration" | "runtime-access", failureClass?: string): void {
  console.error(JSON.stringify({ verdict: "rejected", code, ...(stage === undefined ? {} : { stage }), ...(failureClass === undefined ? {} : { provider_failure_class: failureClass }) }));
  process.exitCode = 1;
}

function migrationFailureClass(error: { readonly params?: Readonly<Record<string, unknown>> }): string | undefined {
  const value = error.params?.["provider_failure_class"];
  return typeof value === "string" && /^(access_denied|conflict|constraint|resource_not_found|timeout|transaction_rolled_back|transport|validation|unknown)$/.test(value)
    ? value
    : undefined;
}
if (typeof require !== "undefined" && require.main === module) void runKanbienCoreServerPersistenceMigration();
