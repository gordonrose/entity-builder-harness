// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.preflight
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-11"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: code
//   purpose: Observe the actual database identity and prerequisites through the selected connection in one read-only transaction without preparing business state.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { createDiagnosticRecord } from "@kanbien/core/diagnostics";
import type { PostgreSqlConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { requireBoundedExistingRole } from "../kanbien-core-server-persistence-role-credential";
import { entitySmokeMigrationUsername, entitySmokeRuntimeUsername, entitySmokeSchema } from "./postgresql";
import { entitySmokePreflightDiagnostic, reportEntitySmokeFailure } from "./diagnostics";

type Identity = "administration" | "migration" | "runtime";
type Field = "configuration" | "identity" | "database" | "authority" | "schema" | "rollback";
type Condition = "invalid-input" | "count-mismatch" | "wrong-type" | "mismatch" | "not-confirmed";

// Authentication follows explicit membership grants, including NOINHERIT.
// pg_has_role also treats superusers as implicit members of every role, which
// is a privilege rule, not an authentication membership observation.
export const entitySmokePasswordAuthenticationPredicate = "NOT EXISTS (WITH RECURSIVE memberships(roleid) AS (SELECT oid FROM pg_roles WHERE rolname = session_user UNION SELECT m.roleid FROM pg_auth_members AS m JOIN memberships AS parent ON m.member = parent.roleid) SELECT 1 FROM memberships JOIN pg_roles AS role ON role.oid = memberships.roleid WHERE role.rolname = 'rds_iam')";

/** TLS/authentication and destination selection are owned by the same real
 * pool/configuration constructors as the later operation. This observes that
 * connection; it never claims all eventual mutation permissions are proven. */
export async function performEntitySmokeDatabasePreflight(pool: PostgreSqlConnectionPool,
  options: { readonly identity: Identity; readonly database: string; readonly username: string },
): Promise<"ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED"> {
  const rejected = (field: Field, condition: Condition) => {
    const checked = createDiagnosticRecord(entitySmokePreflightDiagnostic, { identity: options.identity, field, condition, effect: "not-started" });
    if (!checked.ok) throw new TypeError("ENTITY_SMOKE_DIAGNOSTIC_INVALID");
    return { code: "ENTITY_SMOKE_PREFLIGHT_NOT_CONFIRMED", defaultMessage: "The read-only database preflight was not confirmed.", diagnosticRecord: checked.value };
  };
  // The typed owning callers select identity; even runtime misuse must fail
  // before a connection, without copying supplied identity text into a record.
  if (!["administration", "migration", "runtime"].includes(options.identity)) throw new TypeError("ENTITY_SMOKE_PREFLIGHT_IDENTITY_INVALID");
  if (!/^[a-z][a-z0-9_]{0,62}$/.test(options.database) || !/^[a-z_][a-z0-9_]{0,62}$/.test(options.username)
      || options.identity === "administration" && [entitySmokeMigrationUsername, entitySmokeRuntimeUsername].includes(options.username)
      || options.identity === "migration" && options.username !== entitySmokeMigrationUsername
      || options.identity === "runtime" && options.username !== entitySmokeRuntimeUsername) throw rejected("configuration", "invalid-input");
  const client = await pool.connect();
  let failed = false;
  try {
    await client.query({ text: "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY" });
    await client.query({ text: "SET LOCAL statement_timeout = '5000ms'" });
    const connection = await client.query<{ username: unknown; database: unknown }>({ text: "SELECT current_user AS username, current_database() AS database" });
    if (connection.rows.length !== 1) throw rejected("identity", "count-mismatch");
    const current = connection.rows[0]!;
    if (typeof current.username !== "string") throw rejected("identity", "wrong-type");
    if (current.username !== options.username) throw rejected("identity", "mismatch");
    if (typeof current.database !== "string") throw rejected("database", "wrong-type");
    if (current.database !== options.database) throw rejected("database", "mismatch");
    const boolean = (rows: readonly { allowed: unknown }[], field: Field) => {
      if (rows.length !== 1) throw rejected(field, "count-mismatch");
      if (typeof rows[0]!.allowed !== "boolean") throw rejected(field, "wrong-type");
      if (rows[0]!.allowed !== true) throw rejected(field, "not-confirmed");
    };
    if (options.identity === "administration") {
      const authority = await client.query<{ allowed: unknown }>({
        text: `SELECT has_database_privilege(current_user, $1, 'CREATE WITH GRANT OPTION') AND has_database_privilege(current_user, $1, 'CONNECT WITH GRANT OPTION') AND (SELECT rolcreaterole FROM pg_roles WHERE rolname = current_user) AND ${entitySmokePasswordAuthenticationPredicate} AS allowed`,
        values: [options.database],
      });
      boolean(authority.rows, "authority");
    } else {
      const connected: PostgreSqlConnectionPool = { query: statement => client.query(statement), connect: async () => client, end: async () => undefined };
      await requireBoundedExistingRole(connected, { username: options.username }, { requireLogin: true });
      const authority = await client.query<{ allowed: unknown }>({
        text: "SELECT pg_has_role(current_user, 'rds_iam', 'member') AND has_database_privilege(current_user, $1, 'CONNECT') AS allowed",
        values: [options.database],
      });
      boolean(authority.rows, "authority");
      const schema = await client.query<{ allowed: unknown }>({
        text: options.identity === "migration"
          ? "SELECT pg_get_userbyid(nspowner) = current_user AND has_schema_privilege(current_user, $1, 'USAGE') AND has_schema_privilege(current_user, $1, 'CREATE') AS allowed FROM pg_namespace WHERE nspname = $1"
          : "SELECT has_schema_privilege(current_user, $1, 'USAGE') AND NOT has_schema_privilege(current_user, $1, 'CREATE') AND has_table_privilege(current_user, 'entity_smoke.test_entity', 'SELECT') AS allowed",
        values: [entitySmokeSchema],
      });
      boolean(schema.rows, "schema");
    }
  } catch (cause) { failed = true; throw cause; }
  finally {
    try { await client.query({ text: "ROLLBACK" }); }
    catch {
      const rollback = rejected("rollback", "not-confirmed");
      if (!failed) { failed = true; throw rollback; }
      reportEntitySmokeFailure("verification", "not-started", rollback);
    } finally {
      try { client.release(); }
      catch (cause) {
        if (!failed) throw cause;
        reportEntitySmokeFailure("close", "not-assessed", cause);
      }
    }
  }
  // A success is returned only after rollback and release have completed.
  return "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED";
}
