// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-configuration
//   version: 1
//   status: draft
//   created_on: "2026-10-24"
//   updated_on: "2026-10-25"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Validate the persistence target configuration before opening a connection or performing migration work.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-main
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-migration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.ts
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-restore-verifier
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts

import { X509Certificate } from "node:crypto";
import { readFileSync } from "node:fs";
import { posix } from "node:path";
import { postgreSqlPersistenceConfiguration } from "@kanbien/platform-adapter-aws-persistence-postgresql";

export function persistenceConfiguration(env: NodeJS.ProcessEnv, purpose: "server" | "migration" | "restore") {
  const host = environmentText(env, "PERSISTENCE_POSTGRES_HOST");
  const database = environmentText(env, "PERSISTENCE_POSTGRES_DATABASE");
  const schema = environmentText(env, "PERSISTENCE_POSTGRES_SCHEMA");
  const reference = environmentText(env, "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE");
  const port = environmentText(env, "PERSISTENCE_POSTGRES_PORT");
  if (host === undefined || database === undefined || schema === undefined || reference === undefined || port === undefined || !/^\d+$/.test(port)) return undefined;
  const checked = postgreSqlPersistenceConfiguration({
    host, database, schema, runtimeCredentialSecretReference: reference, port: Number(port),
    maximumPoolSize: purpose === "server" ? 4 : 1,
    connectionTimeoutMs: 5_000, idleTimeoutMs: 10_000,
    statementTimeoutMs: purpose === "migration" ? 240_000 : purpose === "restore" ? 30_000 : 5_000,
    tls: { mode: "verify-full", certificateAuthoritySource: "injected" },
  });
  return checked.ok ? checked.value : undefined;
}

export function persistenceCredentials(value: unknown): { readonly username: string; readonly password: string } | undefined {
  try {
    const parsed: unknown = typeof value === "string" ? JSON.parse(value) : undefined;
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return undefined;
    const { username, password } = parsed as { readonly username?: unknown; readonly password?: unknown };
    // The migration executor must be able to quote both principals before
    // any schema change, and a NUL password cannot be sent to PostgreSQL.
    return typeof username === "string" && /^[a-z_][a-z0-9_]{0,62}$/.test(username)
      && typeof password === "string" && password.length > 0 && !password.includes("\u0000")
      ? { username, password } : undefined;
  } catch { return undefined; }
}

export function persistenceCertificateAuthority(env: NodeJS.ProcessEnv): string | undefined {
  const path = environmentText(env, "PERSISTENCE_POSTGRES_CA_PATH");
  if (path === undefined || !path.startsWith("/app/assets/") || posix.normalize(path) !== path || !path.endsWith(".crt")) return undefined;
  try {
    const value = readFileSync(path, "utf8");
    const certificates = value.match(/-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----/g);
    if (certificates === null || certificates.length === 0) return undefined;
    for (const certificate of certificates) new X509Certificate(certificate);
    return value;
  } catch { return undefined; }
}

export function environmentText(env: NodeJS.ProcessEnv, key: string): string | undefined {
  const value = env[key];
  return typeof value === "string" && value.trim() !== "" && value.trim() === value ? value : undefined;
}
