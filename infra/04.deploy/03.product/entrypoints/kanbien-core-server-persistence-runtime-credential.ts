// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-runtime-credential
//   version: 1
//   status: draft
//   created_on: "2026-10-24"
//   updated_on: "2026-10-31"
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
import { AdministrationObservation, type PersistenceTaskDiagnosticOptions } from "./kanbien-core-server-persistence-operation-diagnostics";

/**
 * Urgent revocation removes the IAM-authentication membership, disables new
 * database logins, then terminates sessions held by the runtime identity.
 * It deliberately never changes a password or writes a verifier.  Recovery
 * is a separate, explicit identity restoration followed by a replacement
 * workload; a completed task is never replayed automatically.
 */
export async function revokeRuntimeAccess(pool: PostgreSqlConnectionPool, runtimeUsername: string, diagnostics?: PersistenceTaskDiagnosticOptions): Promise<void> {
  const observation = new AdministrationObservation("revoke-runtime", diagnostics);
  return observation.runAsync(async () => {
  const role = quotedIdentifier(runtimeUsername, diagnostics);
  let terminated: { readonly rows: readonly { readonly terminated: boolean }[] };
  try {
    observation.location("revoke-iam");
    await pool.query({ text: `REVOKE rds_iam FROM ${role}` });
  } catch (cause) {
    observation.failed(cause);
    throw observation.retained(new Error("PERSISTENCE_RUNTIME_REVOCATION_IAM_MEMBERSHIP_NOT_CONFIRMED"));
  }
  try {
    observation.location("disable-login");
    await pool.query({ text: `ALTER ROLE ${role} NOLOGIN` });
  } catch (cause) {
    observation.failed(cause);
    throw observation.retained(new Error("PERSISTENCE_RUNTIME_REVOCATION_LOGIN_DISABLED_NOT_CONFIRMED"));
  }
  try {
    observation.location("terminate-sessions");
    terminated = await pool.query<{ readonly terminated: boolean }>({
      text: "SELECT pg_terminate_backend(pid) AS terminated FROM pg_stat_activity WHERE usename = $1 AND pid <> pg_backend_pid()",
      values: [runtimeUsername],
    });
  } catch (cause) {
    observation.failed(cause);
    throw observation.retained(new Error("PERSISTENCE_RUNTIME_REVOCATION_SESSION_TERMINATION_NOT_CONFIRMED"));
  }
  // Revocation is not established merely because PostgreSQL accepted the
  // statement. Every returned session must have been terminated. A zero-row
  // result is valid when no runtime session exists at that exact instant;
  // the governed replacement and not-ready proof then establish that new
  // runtime access is denied without inventing a session to terminate.
  let visits = 0, firstRejected: number | undefined;
  observation.location("termination-traversal", "termination-result");
  if (terminated.rows.some((row) => {
    const ordinal = visits++;
    observation.location("termination-traversal", "terminated", ordinal);
    const rejected = row.terminated !== true;
    if (rejected && firstRejected === undefined) firstRejected = ordinal;
    return rejected;
  })) {
    throw observation.rejected(new Error("PERSISTENCE_RUNTIME_SESSION_TERMINATION_NOT_CONFIRMED"), firstRejected === undefined ? "termination-result" : "terminated", firstRejected === undefined ? "predicate-rejected" : "not-true", firstRejected);
  }
  });
}

/** Restore only the already-verified identity's login state and IAM membership. */
export async function restoreRuntimeIamAccess(pool: PostgreSqlConnectionPool, runtimeUsername: string, diagnostics?: PersistenceTaskDiagnosticOptions): Promise<void> {
  const observation = new AdministrationObservation("restore-runtime", diagnostics);
  return observation.runAsync(async () => {
  const role = quotedIdentifier(runtimeUsername, diagnostics);
  // A bounded RDS administrator must not attempt to rewrite attributes such
  // as CREATEDB during recovery. PostgreSQL reserves those changes for roles
  // with broader powers. Verify the fixed identity before enabling it instead.
  await observation.at("bounded-role", undefined, () => requireBoundedExistingRole(pool, { username: runtimeUsername }, {}, diagnostics));
  try {
    observation.location("enable-login");
    await pool.query({ text: `ALTER ROLE ${role} LOGIN` });
  } catch (cause) {
    observation.failed(cause);
    throw observation.retained(new Error("PERSISTENCE_RUNTIME_RECOVERY_LOGIN_RESTORED_NOT_CONFIRMED"));
  }
  await observation.at("bounded-role", undefined, () => requireBoundedExistingRole(pool, { username: runtimeUsername }, { requireLogin: true }, diagnostics));
  try {
    observation.location("grant-iam");
    await pool.query({ text: `GRANT rds_iam TO ${role}` });
  } catch (cause) {
    observation.failed(cause);
    throw observation.retained(new Error("PERSISTENCE_RUNTIME_RECOVERY_IAM_MEMBERSHIP_NOT_CONFIRMED"));
  }
  observation.location("iam-membership-query");
  const result = await pool.query<{ readonly member: boolean }>({ text: "SELECT pg_has_role($1, 'rds_iam', 'member') AS member", values: [runtimeUsername] });
  observation.location("iam-membership-projection", "member");
  if (result.rows[0]?.member !== true) throw observation.rejected(new Error("PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED"), "member", "not-true");
  });
}

function quotedIdentifier(value: string, diagnostics?: PersistenceTaskDiagnosticOptions): string {
  const observation = new AdministrationObservation("role-identifier", diagnostics);
  return observation.run(() => {
    observation.location("identifier-predicate", "identifier");
    if (!/^[a-z_][a-z0-9_]{0,62}$/.test(value)) throw observation.rejected(new TypeError("PERSISTENCE_ROLE_IDENTIFIER_INVALID"), "identifier", "pattern");
    return `"${value}"`;
  });
}
