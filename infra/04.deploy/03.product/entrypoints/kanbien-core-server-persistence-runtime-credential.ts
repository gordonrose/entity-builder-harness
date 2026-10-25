// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-runtime-credential
//   version: 1
//   status: draft
//   created_on: "2026-10-24"
//   updated_on: "2026-10-25"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Revoke and restore bounded PostgreSQL IAM database identity access without altering a password or verifier.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-administration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts

import type { PostgreSqlConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { requireBoundedExistingRole } from "./kanbien-core-server-persistence-role-credential";

/**
 * Urgent revocation removes the IAM-authentication membership, disables new
 * database logins, then terminates sessions held by the runtime identity.
 * It deliberately never changes a password or writes a verifier.  Recovery
 * is a separate, explicit identity restoration followed by a replacement
 * workload; a completed task is never replayed automatically.
 */
export async function revokeRuntimeAccess(pool: PostgreSqlConnectionPool, runtimeUsername: string): Promise<void> {
  const role = quotedIdentifier(runtimeUsername);
  let terminated: { readonly rows: readonly { readonly terminated: boolean }[] };
  try {
    await pool.query({ text: `REVOKE rds_iam FROM ${role}` });
  } catch {
    throw new Error("PERSISTENCE_RUNTIME_REVOCATION_IAM_MEMBERSHIP_NOT_CONFIRMED");
  }
  try {
    await pool.query({ text: `ALTER ROLE ${role} NOLOGIN` });
  } catch {
    throw new Error("PERSISTENCE_RUNTIME_REVOCATION_LOGIN_DISABLED_NOT_CONFIRMED");
  }
  try {
    terminated = await pool.query<{ readonly terminated: boolean }>({
      text: "SELECT pg_terminate_backend(pid) AS terminated FROM pg_stat_activity WHERE usename = $1 AND pid <> pg_backend_pid()",
      values: [runtimeUsername],
    });
  } catch {
    throw new Error("PERSISTENCE_RUNTIME_REVOCATION_SESSION_TERMINATION_NOT_CONFIRMED");
  }
  // Revocation is not established merely because PostgreSQL accepted the
  // statement. Every returned session must have been terminated. A zero-row
  // result is valid when no runtime session exists at that exact instant;
  // the governed replacement and not-ready proof then establish that new
  // runtime access is denied without inventing a session to terminate.
  if (terminated.rows.some((row) => row.terminated !== true)) {
    throw new Error("PERSISTENCE_RUNTIME_SESSION_TERMINATION_NOT_CONFIRMED");
  }
}

/** Restore only the already-verified identity's login state and IAM membership. */
export async function restoreRuntimeIamAccess(pool: PostgreSqlConnectionPool, runtimeUsername: string): Promise<void> {
  const role = quotedIdentifier(runtimeUsername);
  // A bounded RDS administrator must not attempt to rewrite attributes such
  // as CREATEDB during recovery. PostgreSQL reserves those changes for roles
  // with broader powers. Verify the fixed identity before enabling it instead.
  await requireBoundedExistingRole(pool, { username: runtimeUsername });
  try {
    await pool.query({ text: `ALTER ROLE ${role} LOGIN` });
  } catch {
    throw new Error("PERSISTENCE_RUNTIME_RECOVERY_LOGIN_RESTORED_NOT_CONFIRMED");
  }
  await requireBoundedExistingRole(pool, { username: runtimeUsername }, { requireLogin: true });
  try {
    await pool.query({ text: `GRANT rds_iam TO ${role}` });
  } catch {
    throw new Error("PERSISTENCE_RUNTIME_RECOVERY_IAM_MEMBERSHIP_NOT_CONFIRMED");
  }
  const result = await pool.query<{ readonly member: boolean }>({ text: "SELECT pg_has_role($1, 'rds_iam', 'member') AS member", values: [runtimeUsername] });
  if (result.rows[0]?.member !== true) throw new Error("PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED");
}

function quotedIdentifier(value: string): string {
  if (!/^[a-z_][a-z0-9_]{0,62}$/.test(value)) throw new TypeError("PERSISTENCE_ROLE_IDENTIFIER_INVALID");
  return `"${value}"`;
}
