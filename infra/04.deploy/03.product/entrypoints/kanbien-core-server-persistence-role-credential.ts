// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-role-credential
//   version: 2
//   status: draft
//   created_on: "2026-10-25"
//   updated_on: "2026-10-25"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Establish bounded PostgreSQL IAM database identities without sending passwords or password verifiers in SQL.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-administration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-runtime-credential
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-runtime-credential.ts

import type { PostgreSqlConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";

export type PostgreSqlLoginIdentity = { readonly username: string };

type RoleFacts = {
  readonly exists: boolean;
  readonly can_login: boolean;
  readonly superuser: boolean;
  readonly create_role: boolean;
  readonly create_database: boolean;
  readonly replication: boolean;
  readonly bypass_rls: boolean;
  readonly inherit: boolean;
};

/** This boundary never sets a password or passes a verifier to SQL. */
export async function ensureBoundedLoginRole(pool: PostgreSqlConnectionPool, identity: PostgreSqlLoginIdentity): Promise<void> {
  const before = await roleFacts(pool, identity.username);
  if (!before.exists) {
    await pool.query({ text: `CREATE ROLE ${quotedIdentifier(identity.username)} LOGIN NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT` });
  } else {
    // A role from the password-era bootstrap may exist with PostgreSQL's
    // default INHERIT attribute.  It is safe to converge that *reducing*
    // setting only after rejecting every privilege that could broaden the
    // role.  Refusing all legacy attributes here made the IAM migration
    // non-idempotent; blindly altering the role would be worse.
    requireNoElevatedRole(before);
    // NOLOGIN is the explicit urgent-revocation state. Bootstrap is not a
    // recovery path and must never silently re-enable it; only restore-runtime
    // may do so after proving that existing sessions were terminated.
    if (!before.can_login) throw new Error("PERSISTENCE_ROLE_REACTIVATION_REQUIRES_EXPLICIT_RECOVERY");
    // Leave an already bounded role untouched.  A constrained administrator
    // can validate it but may not be permitted to rewrite all role attributes;
    // only the legacy INHERIT setting needs convergence.
    if (before.inherit) await pool.query({ text: `ALTER ROLE ${quotedIdentifier(identity.username)} NOINHERIT` });
  }
  await requireBoundedExistingRole(pool, identity, { requireLogin: true });
}

/**
 * Check an existing identity before changing whether it can log in. Recovery
 * uses this to reject a role whose non-login privileges were widened while it
 * was disabled, instead of enabling it again and assuming historical setup.
 */
export async function requireBoundedExistingRole(
  pool: PostgreSqlConnectionPool,
  identity: PostgreSqlLoginIdentity,
  options: { readonly requireLogin?: boolean } = {},
): Promise<void> {
  requireBoundedRole(await roleFacts(pool, identity.username), options);
}

/** RDS owns this predefined role; membership selects IAM authentication. */
export async function ensureRdsIamAuthentication(pool: PostgreSqlConnectionPool, identity: PostgreSqlLoginIdentity): Promise<void> {
  await pool.query({ text: `GRANT rds_iam TO ${quotedIdentifier(identity.username)}` });
  const result = await pool.query<{ readonly member: boolean }>({ text: "SELECT pg_has_role($1, 'rds_iam', 'member') AS member", values: [identity.username] });
  if (result.rows[0]?.member !== true) throw new Error("PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED");
}

async function roleFacts(pool: PostgreSqlConnectionPool, username: string): Promise<RoleFacts> {
  const result = await pool.query<RoleFacts>({
    text: "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = $1) AS exists, COALESCE((SELECT rolcanlogin FROM pg_roles WHERE rolname = $1), false) AS can_login, COALESCE((SELECT rolsuper FROM pg_roles WHERE rolname = $1), false) AS superuser, COALESCE((SELECT rolcreaterole FROM pg_roles WHERE rolname = $1), false) AS create_role, COALESCE((SELECT rolcreatedb FROM pg_roles WHERE rolname = $1), false) AS create_database, COALESCE((SELECT rolreplication FROM pg_roles WHERE rolname = $1), false) AS replication, COALESCE((SELECT rolbypassrls FROM pg_roles WHERE rolname = $1), false) AS bypass_rls, COALESCE((SELECT rolinherit FROM pg_roles WHERE rolname = $1), false) AS inherit",
    values: [username],
  });
  const facts = result.rows[0];
  if (facts === undefined || typeof facts.exists !== "boolean" || typeof facts.can_login !== "boolean" || typeof facts.superuser !== "boolean" || typeof facts.create_role !== "boolean" || typeof facts.create_database !== "boolean" || typeof facts.replication !== "boolean" || typeof facts.bypass_rls !== "boolean" || typeof facts.inherit !== "boolean") throw new Error("PERSISTENCE_ROLE_STATE_UNAVAILABLE");
  return facts;
}

function requireBoundedRole(facts: RoleFacts, options: { readonly requireLogin?: boolean } = {}): void {
  if (!facts.exists || facts.inherit || (options.requireLogin === true && !facts.can_login)) throw new Error("PERSISTENCE_ROLE_PRIVILEGE_BOUNDARY_NOT_CONFIRMED");
  requireNoElevatedRole(facts);
}

function requireNoElevatedRole(facts: RoleFacts): void {
  if (!facts.exists || facts.superuser || facts.create_role || facts.create_database || facts.replication || facts.bypass_rls) throw new Error("PERSISTENCE_ROLE_PRIVILEGE_BOUNDARY_NOT_CONFIRMED");
}

function quotedIdentifier(value: string): string {
  if (!/^[a-z_][a-z0-9_]{0,62}$/.test(value)) throw new TypeError("PERSISTENCE_ROLE_IDENTIFIER_INVALID");
  return `"${value}"`;
}
