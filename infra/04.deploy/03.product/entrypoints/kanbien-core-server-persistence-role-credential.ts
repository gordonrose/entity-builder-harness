// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-role-credential
//   version: 2
//   status: draft
//   created_on: "2026-10-25"
//   updated_on: "2026-10-31"
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
import { AdministrationObservation, type AdministrationPredicateDetail, type PersistenceTaskDiagnosticOptions } from "./kanbien-core-server-persistence-operation-diagnostics";

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
export async function ensureBoundedLoginRole(pool: PostgreSqlConnectionPool, identity: PostgreSqlLoginIdentity, diagnostics?: PersistenceTaskDiagnosticOptions): Promise<void> {
  const observation = new AdministrationObservation("ensure-login-role", diagnostics);
  return observation.runAsync(async () => {
  const before = await observation.at("role-facts-query", "identifier", () => roleFacts(pool, identity.username, diagnostics));
  observation.location("role-facts-projection", "exists");
  if (!before.exists) {
    observation.location("create-role", "identifier");
    await pool.query({ text: `CREATE ROLE ${quotedIdentifier(identity.username, diagnostics)} LOGIN NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT` });
  } else {
    // A role from the password-era bootstrap may exist with PostgreSQL's
    // default INHERIT attribute.  It is safe to converge that *reducing*
    // setting only after rejecting every privilege that could broaden the
    // role.  Refusing all legacy attributes here made the IAM migration
    // non-idempotent; blindly altering the role would be worse.
    observation.at("bounded-role", undefined, () => requireNoElevatedRole(before, diagnostics));
    // NOLOGIN is the explicit urgent-revocation state. Bootstrap is not a
    // recovery path and must never silently re-enable it; only restore-runtime
    // may do so after proving that existing sessions were terminated.
    observation.location("role-facts-projection", "can-login");
    if (!before.can_login) throw observation.rejected(new Error("PERSISTENCE_ROLE_REACTIVATION_REQUIRES_EXPLICIT_RECOVERY"), "can-login", "falsy");
    // Leave an already bounded role untouched.  A constrained administrator
    // can validate it but may not be permitted to rewrite all role attributes;
    // only the legacy INHERIT setting needs convergence.
    observation.location("role-facts-projection", "inherit");
    if (before.inherit) {
      observation.location("set-noinherit", "identifier");
      await pool.query({ text: `ALTER ROLE ${quotedIdentifier(identity.username, diagnostics)} NOINHERIT` });
    }
  }
  await observation.at("bounded-role", undefined, () => requireBoundedExistingRole(pool, identity, { requireLogin: true }, diagnostics));
  });
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
  diagnostics?: PersistenceTaskDiagnosticOptions,
): Promise<void> {
  const observation = new AdministrationObservation("bounded-role", diagnostics);
  return observation.runAsync(async () => {
    const facts = await observation.at("role-facts-query", "identifier", () => roleFacts(pool, identity.username, diagnostics));
    observation.at("bounded-role", undefined, () => requireBoundedRole(facts, options, diagnostics));
  });
}

/** RDS owns this predefined role; membership selects IAM authentication. */
export async function ensureRdsIamAuthentication(pool: PostgreSqlConnectionPool, identity: PostgreSqlLoginIdentity, diagnostics?: PersistenceTaskDiagnosticOptions): Promise<void> {
  const observation = new AdministrationObservation("iam-membership", diagnostics);
  return observation.runAsync(async () => {
  observation.location("grant-iam", "identifier");
  await pool.query({ text: `GRANT rds_iam TO ${quotedIdentifier(identity.username, diagnostics)}` });
  observation.location("iam-membership-query", "member");
  const result = await pool.query<{ readonly member: boolean }>({ text: "SELECT pg_has_role($1, 'rds_iam', 'member') AS member", values: [identity.username] });
  observation.location("iam-membership-projection", "member");
  if (result.rows[0]?.member !== true) throw observation.rejected(new Error("PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED"), "member", "not-true");
  });
}

async function roleFacts(pool: PostgreSqlConnectionPool, username: string, diagnostics?: PersistenceTaskDiagnosticOptions): Promise<RoleFacts> {
  const observation = new AdministrationObservation("role-facts", diagnostics);
  return observation.runAsync(async () => {
  observation.location("role-facts-query");
  const result = await pool.query<RoleFacts>({
    text: "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = $1) AS exists, COALESCE((SELECT rolcanlogin FROM pg_roles WHERE rolname = $1), false) AS can_login, COALESCE((SELECT rolsuper FROM pg_roles WHERE rolname = $1), false) AS superuser, COALESCE((SELECT rolcreaterole FROM pg_roles WHERE rolname = $1), false) AS create_role, COALESCE((SELECT rolcreatedb FROM pg_roles WHERE rolname = $1), false) AS create_database, COALESCE((SELECT rolreplication FROM pg_roles WHERE rolname = $1), false) AS replication, COALESCE((SELECT rolbypassrls FROM pg_roles WHERE rolname = $1), false) AS bypass_rls, COALESCE((SELECT rolinherit FROM pg_roles WHERE rolname = $1), false) AS inherit",
    values: [username],
  });
  observation.location("role-facts-projection", "row");
  const facts = result.rows[0];
  let field: AdministrationPredicateDetail["field"] = "row";
  const invalid = (at: AdministrationPredicateDetail["field"], rejected: boolean): boolean => { field = at; return rejected; };
  if (facts === undefined || invalid("exists", typeof observation.at("role-facts-projection", "exists", () => facts.exists) !== "boolean") || invalid("can-login", typeof observation.at("role-facts-projection", "can-login", () => facts.can_login) !== "boolean") || invalid("superuser", typeof observation.at("role-facts-projection", "superuser", () => facts.superuser) !== "boolean") || invalid("create-role", typeof observation.at("role-facts-projection", "create-role", () => facts.create_role) !== "boolean") || invalid("create-database", typeof observation.at("role-facts-projection", "create-database", () => facts.create_database) !== "boolean") || invalid("replication", typeof observation.at("role-facts-projection", "replication", () => facts.replication) !== "boolean") || invalid("bypass-rls", typeof observation.at("role-facts-projection", "bypass-rls", () => facts.bypass_rls) !== "boolean") || invalid("inherit", typeof observation.at("role-facts-projection", "inherit", () => facts.inherit) !== "boolean")) throw observation.rejected(new Error("PERSISTENCE_ROLE_STATE_UNAVAILABLE"), field, field === "row" ? "missing" : "wrong-type");
  return facts;
  });
}

function requireBoundedRole(facts: RoleFacts, options: { readonly requireLogin?: boolean } = {}, diagnostics?: PersistenceTaskDiagnosticOptions): void {
  const observation = new AdministrationObservation("bounded-role", diagnostics);
  observation.run(() => {
    let field: AdministrationPredicateDetail["field"] = "exists";
    const rejects = (at: AdministrationPredicateDetail["field"], result: boolean): boolean => { field = at; return result; };
    if (rejects("exists", !observation.at("role-facts-projection", "exists", () => facts.exists)) || rejects("inherit", !!observation.at("role-facts-projection", "inherit", () => facts.inherit)) || (observation.at("bounded-role", "require-login", () => options.requireLogin) === true && rejects("can-login", !observation.at("role-facts-projection", "can-login", () => facts.can_login)))) throw observation.rejected(new Error("PERSISTENCE_ROLE_PRIVILEGE_BOUNDARY_NOT_CONFIRMED"), field, (field as AdministrationPredicateDetail["field"]) === "inherit" ? "truthy" : "falsy");
    observation.at("bounded-role", undefined, () => requireNoElevatedRole(facts, diagnostics));
  });
}

function requireNoElevatedRole(facts: RoleFacts, diagnostics?: PersistenceTaskDiagnosticOptions): void {
  const observation = new AdministrationObservation("elevated-role", diagnostics);
  observation.run(() => {
    let field: AdministrationPredicateDetail["field"] = "exists";
    const read = <T>(at: AdministrationPredicateDetail["field"], action: () => T): T => { field = at; return observation.at("role-facts-projection", at, action); };
    if (!read("exists", () => facts.exists) || read("superuser", () => facts.superuser) || read("create-role", () => facts.create_role) || read("create-database", () => facts.create_database) || read("replication", () => facts.replication) || read("bypass-rls", () => facts.bypass_rls)) throw observation.rejected(new Error("PERSISTENCE_ROLE_PRIVILEGE_BOUNDARY_NOT_CONFIRMED"), field, field === "exists" ? "falsy" : "truthy");
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
