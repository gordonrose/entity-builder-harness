// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.library.entity-smoke.administrator-recovery
//   version: 1
//   status: draft
//   created_on: "2026-11-11"
//   updated_on: "2026-11-11"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: script
//   purpose: Remove only the observed feature membership and prove fresh administrator password authentication without data writes.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   effects: [network, aws-mutation]
//   used_by:
//   - id: aws.standard.operational-realization-applicability
//     path: .agentic/aws/standards/operational-realization-applicability.md
"use strict";
const { Client } = require("/app/artifacts/node_modules/pg");
const { Signer } = require("/app/artifacts/node_modules/@aws-sdk/rds-signer");
const { readFileSync } = require("node:fs");
const host = "kanbien-core-platform-persistence.cl62wkc0w898.eu-west-1.rds.amazonaws.com";
const edgesSql = "SELECT r.rolname AS role, m.rolname AS member, g.rolname AS grantor, a.admin_option, a.inherit_option, a.set_option FROM pg_auth_members a JOIN pg_roles r ON r.oid = a.roleid JOIN pg_roles m ON m.oid = a.member JOIN pg_roles g ON g.oid = a.grantor WHERE m.rolname IN ('core_migration','entity_smoke_migration','entity_smoke_runtime') ORDER BY r.rolname, m.rolname, g.rolname";
const stateSql = "SELECT current_user = 'core_migration' AND current_database() = 'kanbienpersistence' AND NOT (SELECT rolsuper FROM pg_roles WHERE rolname = current_user) AND pg_has_role(current_user,'rds_superuser','MEMBER') AS administrator, pg_has_role(current_user,'rds_iam','MEMBER') AS iam";
const historySql = "SELECT md5(string_agg(migration_id || checksum || tool_version || applied_at::text, ',' ORDER BY migration_id)) AS digest FROM entity_smoke.platform_migration_history";
let phase = "configuration", effect = "not-started", client, passwordClient, transaction = false;
function requireFact(value) { if (!value) throw new Error("recovery-not-confirmed"); }
(async () => {
  requireFact(process.env.PERSISTENCE_POSTGRES_HOST === host && process.env.PERSISTENCE_POSTGRES_DATABASE === "kanbienpersistence" && process.env.PERSISTENCE_POSTGRES_SCHEMA === "entity_smoke");
  const credentials = JSON.parse(process.env.PERSISTENCE_ADMINISTRATOR_CREDENTIALS);
  requireFact(credentials.username === "core_migration" && typeof credentials.password === "string" && credentials.password.length > 0);
  const settings = { host, port: 5432, database: "kanbienpersistence", user: "core_migration", ssl: { rejectUnauthorized: true, ca: readFileSync("/app/assets/rds-eu-west-1-bundle.crt", "utf8") }, connectionTimeoutMillis: 15000, statement_timeout: 15000 };
  phase = "iam-connection";
  const token = await new Signer({ region: "eu-west-1", hostname: host, port: 5432, username: "core_migration" }).getAuthToken();
  client = new Client({ ...settings, password: token }); await client.connect();
  phase = "original-state";
  await client.query("BEGIN"); transaction = true;
  await client.query("SET LOCAL lock_timeout = '5000ms'");
  await client.query("SELECT pg_advisory_xact_lock(hashtext('entity-smoke-identity-bootstrap'))");
  const state = (await client.query(stateSql)).rows;
  requireFact(state.length === 1 && state[0].administrator === true && state[0].iam === true);
  const before = (await client.query(edgesSql)).rows;
  const expected = [
    { role: "entity_smoke_migration", member: "core_migration", grantor: "rdsadmin", admin_option: false, inherit_option: false, set_option: true },
    { role: "rds_iam", member: "entity_smoke_migration", grantor: "rdsadmin", admin_option: false, inherit_option: false, set_option: true },
    { role: "rds_iam", member: "entity_smoke_runtime", grantor: "rdsadmin", admin_option: false, inherit_option: false, set_option: true },
    { role: "rds_superuser", member: "core_migration", grantor: "rdsadmin", admin_option: false, inherit_option: true, set_option: true }
  ];
  requireFact(JSON.stringify(before) === JSON.stringify(expected));
  await client.query("SET LOCAL ROLE entity_smoke_migration");
  const history = (await client.query(historySql)).rows;
  requireFact(history.length === 1 && /^[a-f0-9]{32}$/.test(history[0].digest));
  await client.query("RESET ROLE");
  phase = "remove-feature-membership"; effect = "transaction-uncommitted";
  await client.query("REVOKE entity_smoke_migration FROM core_migration");
  requireFact(JSON.stringify((await client.query(edgesSql)).rows) === JSON.stringify(expected.slice(1)));
  requireFact((await client.query(stateSql)).rows[0]?.iam === false);
  phase = "owner-authority-observation";
  await client.query("SAVEPOINT owner_authority");
  let ownerSelection = false;
  try {
    await client.query("SET LOCAL ROLE entity_smoke_migration");
    requireFact(JSON.stringify((await client.query(historySql)).rows) === JSON.stringify(history));
    ownerSelection = true;
  } catch (cause) {
    if (cause?.code !== "42501") throw cause;
  }
  await client.query("ROLLBACK TO SAVEPOINT owner_authority");
  phase = "commit"; effect = "commit-uncertain";
  await client.query("COMMIT"); transaction = false; effect = "membership-removed";
  phase = "password-reconnection";
  passwordClient = new Client({ ...settings, password: credentials.password }); await passwordClient.connect();
  const restored = (await passwordClient.query(stateSql)).rows;
  requireFact(restored.length === 1 && restored[0].administrator === true && restored[0].iam === false);
  requireFact(JSON.stringify((await passwordClient.query(edgesSql)).rows) === JSON.stringify(expected.slice(1)));
  phase = "close";
  await passwordClient.end(); passwordClient = undefined; await client.end(); client = undefined;
  console.log(JSON.stringify({ schema: "deploy/entity-smoke-administrator-recovery/v1", verdict: "recovered", password_reconnected: true, feature_membership_removed: true, other_memberships_preserved: true, owner_selection_without_membership: ownerSelection, history_unchanged: ownerSelection, business_writes: false }));
})().catch(async () => {
  if (client && transaction && effect !== "commit-uncertain") {
    try { await client.query("ROLLBACK"); effect = "rolled-back"; } catch { effect = "rollback-unconfirmed"; }
  }
  for (const connection of [passwordClient, client]) if (connection) { try { await connection.end(); } catch {} }
  console.error(JSON.stringify({ schema: "deploy/entity-smoke-administrator-recovery/v1", verdict: "failed", phase, effect }));
  process.exitCode = 1;
});
