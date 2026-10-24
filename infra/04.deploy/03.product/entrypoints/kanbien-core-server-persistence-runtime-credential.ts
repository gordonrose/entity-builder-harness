// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-runtime-credential
//   version: 1
//   status: draft
//   created_on: "2026-10-24"
//   updated_on: "2026-10-24"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Define the bounded runtime PostgreSQL credential operation used by the migration executor.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-migration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.ts

import type { PostgreSqlConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";

export type RuntimeCredentialOperation = "apply" | "rotate" | "revoke" | "prove-effective-privilege";

export function runtimeCredentialOperation(value: unknown): RuntimeCredentialOperation | undefined {
  return value === undefined || value === "apply"
    ? "apply"
    : value === "rotate" || value === "revoke" || value === "prove-effective-privilege"
      ? value
      : undefined;
}

/**
 * Urgent revocation prevents new logins before it terminates sessions held by
 * the runtime role.  A separate migration-credential recovery operation must
 * later install a fresh password and a fresh server task; completed tasks are
 * never replayed automatically.
 */
export async function revokeRuntimeAccess(pool: PostgreSqlConnectionPool, runtimeUsername: string): Promise<void> {
  const role = quotedIdentifier(runtimeUsername);
  await pool.query({ text: `ALTER ROLE ${role} NOLOGIN` });
  const terminated = await pool.query<{ readonly terminated: boolean }>({
    text: "SELECT pg_terminate_backend(pid) AS terminated FROM pg_stat_activity WHERE usename = $1 AND pid <> pg_backend_pid()",
    values: [runtimeUsername],
  });
  // Revocation is not established merely because PostgreSQL accepted the
  // statement. Every returned session must have been terminated. A zero-row
  // result is valid when no runtime session exists at that exact instant;
  // the governed replacement and not-ready proof then establish that new
  // runtime access is denied without inventing a session to terminate.
  if (terminated.rows.some((row) => row.terminated !== true)) {
    throw new Error("PERSISTENCE_RUNTIME_SESSION_TERMINATION_NOT_CONFIRMED");
  }
}

function quotedIdentifier(value: string): string {
  if (!/^[a-z_][a-z0-9_]{0,62}$/.test(value)) throw new TypeError("PERSISTENCE_ROLE_IDENTIFIER_INVALID");
  return `"${value}"`;
}
