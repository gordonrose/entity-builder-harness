// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-main
//   version: 1
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-23"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Start the persistence-capable core server with the reviewed PostgreSQL adapter and injected runtime credentials.
//   portability:
//     class: internal
//     targets:
//     - kanbien-core-platform
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import { readFileSync } from "node:fs";
import {
  createNodePostgreSqlConnectionPool,
  postgreSqlPersistenceConfiguration,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { resolvePlatformReleaseIdentity } from "@kanbien/platform-server";
import { startPlatformServerProcess } from "@kanbien/platform-server/main";
import { createKanbienCoreServerPersistenceApp } from "./kanbien-core-server-persistence.app";
import { createKanbienCoreServerPostgreSqlPersistenceRuntime } from "./kanbien-core-server-persistence-postgresql";

export async function runKanbienCoreServerPersistenceMain(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const configuration = configurationFromEnvironment(env);
  if (configuration === undefined) return startupFailed("configuration-invalid");
  const credentials = runtimeCredentialsFromEnvironment(env);
  if (credentials === undefined) return startupFailed("runtime-credentials-invalid");
  const certificateAuthority = certificateAuthorityFromEnvironment(env);
  if (certificateAuthority === undefined) return startupFailed("tls-authority-unavailable");

  const pool = createNodePostgreSqlConnectionPool(configuration, { ...credentials, certificateAuthority });
  const persistence = createKanbienCoreServerPostgreSqlPersistenceRuntime({ pool, schema: configuration.schema });
  const started = await startPlatformServerProcess({
    apps: [createKanbienCoreServerPersistenceApp(resolvePlatformReleaseIdentity(env["PLATFORM_SOURCE_COMMIT_SHA"]), persistence)],
    env,
  });
  if (!started.ok) {
    await persistence.close();
    return startupFailed(started.error.code);
  }
  if (env["PLATFORM_SERVER_EXIT_AFTER_START"] === "1") await started.value.close();
}

function configurationFromEnvironment(env: NodeJS.ProcessEnv) {
  const host = requiredEnvironment(env, "PERSISTENCE_POSTGRES_HOST");
  const port = requiredIntegerEnvironment(env, "PERSISTENCE_POSTGRES_PORT");
  const database = requiredEnvironment(env, "PERSISTENCE_POSTGRES_DATABASE");
  const schema = requiredEnvironment(env, "PERSISTENCE_POSTGRES_SCHEMA");
  const runtimeCredentialSecretReference = requiredEnvironment(env, "PERSISTENCE_RUNTIME_SECRET_REFERENCE");
  if (host === undefined || port === undefined || database === undefined || schema === undefined || runtimeCredentialSecretReference === undefined) return undefined;
  const checked = postgreSqlPersistenceConfiguration({
    host,
    port,
    database,
    schema,
    runtimeCredentialSecretReference,
    maximumPoolSize: 4,
    connectionTimeoutMs: 5_000,
    idleTimeoutMs: 10_000,
    statementTimeoutMs: 5_000,
    tls: { mode: "verify-full", certificateAuthoritySource: "injected" },
  });
  return checked.ok ? checked.value : undefined;
}

function runtimeCredentialsFromEnvironment(env: NodeJS.ProcessEnv) {
  return credentialObject(env["PERSISTENCE_RUNTIME_CREDENTIALS"]);
}

function credentialObject(value: unknown): { readonly username: string; readonly password: string } | undefined {
  if (typeof value !== "string") return undefined;
  try {
    const parsed: unknown = JSON.parse(value);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return undefined;
    const username = (parsed as { readonly username?: unknown }).username;
    const password = (parsed as { readonly password?: unknown }).password;
    return typeof username === "string" && username.trim() !== "" && typeof password === "string" && password.length > 0 ? { username, password } : undefined;
  } catch { return undefined; }
}

function certificateAuthorityFromEnvironment(env: NodeJS.ProcessEnv): string | undefined {
  const path = requiredEnvironment(env, "PERSISTENCE_POSTGRES_CA_PATH");
  if (path === undefined || !path.startsWith("/app/assets/") || !path.endsWith(".crt")) return undefined;
  try {
    const value = readFileSync(path, "utf8");
    return value.includes("BEGIN CERTIFICATE") ? value : undefined;
  } catch {
    return undefined;
  }
}

function requiredEnvironment(env: NodeJS.ProcessEnv, key: string): string | undefined {
  const value = env[key];
  return typeof value === "string" && value.trim().length > 0 && value.trim() === value ? value : undefined;
}

function requiredIntegerEnvironment(env: NodeJS.ProcessEnv, key: string): number | undefined {
  const value = requiredEnvironment(env, key);
  return value === undefined || !/^\d+$/.test(value) ? undefined : Number(value);
}

function startupFailed(code: string): void {
  console.error(JSON.stringify({
    level: "error",
    message: "kanbien-core-server-persistence.start_failed",
    error: { code, message: "The persistence-capable core server could not start safely." },
  }));
  process.exitCode = 1;
}

if (typeof require !== "undefined" && require.main === module) {
  void runKanbienCoreServerPersistenceMain();
}
