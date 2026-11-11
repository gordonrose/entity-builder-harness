// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.library.entity-smoke.administrator-observation
//   version: 1
//   status: draft
//   created_on: "2026-11-11"
//   updated_on: "2026-11-11"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: script
//   purpose: Observe fixed role edges through the existing restricted migration identity without business or permission writes.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   effects: [network]
//   used_by:
//   - id: aws.standard.operational-realization-applicability
//     path: .agentic/aws/standards/operational-realization-applicability.md
"use strict";
const { Client } = require("/app/artifacts/node_modules/pg");
const { Signer } = require("/app/artifacts/node_modules/@aws-sdk/rds-signer");
const { readFileSync } = require("node:fs");
const host = "kanbien-core-platform-persistence.cl62wkc0w898.eu-west-1.rds.amazonaws.com";
const names = ["core_migration", "entity_smoke_migration", "entity_smoke_runtime", "rds_iam", "rds_superuser", "rdsadmin"];
let phase = "configuration", client;
function requireFact(value) { if (!value) throw new Error("observation-not-confirmed"); }
(async () => {
  requireFact(process.env.PERSISTENCE_POSTGRES_HOST === host && process.env.PERSISTENCE_POSTGRES_DATABASE === "kanbienpersistence" && process.env.PERSISTENCE_MIGRATION_DATABASE_USERNAME === "entity_smoke_migration");
  phase = "credential";
  const password = await new Signer({ region: "eu-west-1", hostname: host, port: 5432, username: "entity_smoke_migration" }).getAuthToken();
  phase = "connection";
  client = new Client({ host, port: 5432, database: "kanbienpersistence", user: "entity_smoke_migration", password,
    ssl: { rejectUnauthorized: true, ca: readFileSync("/app/assets/rds-eu-west-1-bundle.crt", "utf8") }, connectionTimeoutMillis: 15000, statement_timeout: 15000 });
  await client.connect();
  phase = "observation";
  await client.query("BEGIN READ ONLY");
  const identity = await client.query("SELECT current_user = 'entity_smoke_migration' AS allowed");
  requireFact(identity.rows.length === 1 && identity.rows[0].allowed === true);
  const memberships = await client.query({ text: "SELECT r.rolname AS role, m.rolname AS member, g.rolname AS grantor, a.admin_option, a.inherit_option, a.set_option FROM pg_auth_members a JOIN pg_roles r ON r.oid = a.roleid JOIN pg_roles m ON m.oid = a.member JOIN pg_roles g ON g.oid = a.grantor WHERE m.rolname = ANY($1::text[]) ORDER BY r.rolname, m.rolname, g.rolname", values: [names.slice(0, 3)] });
  const authentication = await client.query("SELECT pg_has_role('core_migration','rds_iam','MEMBER') AS member, pg_has_role('core_migration','rds_iam','USAGE') AS usage, pg_has_role('core_migration','rds_iam','SET') AS selectable");
  requireFact(memberships.rows.length <= 30 && authentication.rows.length === 1 && Object.values(authentication.rows[0]).every(value => typeof value === "boolean"));
  const edges = memberships.rows.map(row => {
    requireFact([row.admin_option, row.inherit_option, row.set_option].every(value => typeof value === "boolean"));
    requireFact([row.role, row.member, row.grantor].every(value => typeof value === "string"));
    return { role: names.includes(row.role) ? row.role : "other", member: names.includes(row.member) ? row.member : "other", grantor: names.includes(row.grantor) ? row.grantor : "other", admin: row.admin_option, inherit: row.inherit_option, set: row.set_option };
  });
  await client.query("ROLLBACK");
  phase = "close"; await client.end(); client = undefined;
  console.log(JSON.stringify({ schema: "deploy/entity-smoke-administrator-observation/v1", verdict: "observed", edges, authentication: authentication.rows[0], writes: false }));
})().catch(async () => {
  if (client) { try { await client.end(); } catch {} }
  console.error(JSON.stringify({ schema: "deploy/entity-smoke-administrator-observation/v1", verdict: "failed", phase, effect: "read-only" }));
  process.exitCode = 1;
});
