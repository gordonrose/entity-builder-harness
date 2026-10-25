#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.core-server-persistence-configuration
//   version: 1
//   status: draft
//   created_on: "2026-10-24"
//   updated_on: "2026-10-25"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: script
//   purpose: Prove configuration failures stop all persistence entrypoints before pool creation, without database or target access.
//   portability: { class: internal, targets: [] }
//   effects: [writes-files]
//   used_by:
//   - id: deploy.test.core-server-persistence-composition
//     path: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh

import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";

const compiled = resolve(process.argv[2]);
// No real driver is loaded. Any attempt to create a pool is a test failure.
const fakeDriver = join(compiled, "node_modules/pg");
fs.mkdirSync(fakeDriver, { recursive: true });
fs.writeFileSync(join(fakeDriver, "index.js"), 'exports.Pool = class { constructor() { globalThis.poolAttempts += 1; throw new Error("database-access-before-validation"); } };');
const fakeSigner = join(compiled, "node_modules/@aws-sdk/rds-signer");
fs.mkdirSync(fakeSigner, { recursive: true });
fs.writeFileSync(join(fakeSigner, "index.js"), 'exports.Signer = class { async getAuthToken() { return "synthetic-token"; } };');
globalThis.poolAttempts = 0;
const require = createRequire(join(compiled, "configuration-test.cjs"));
const entrypoints = join(compiled, "infra/04.deploy/03.product/entrypoints");
const config = require(join(entrypoints, "kanbien-core-server-persistence-configuration.js"));
const server = require(join(entrypoints, "kanbien-core-server-persistence.main.js"));
const migration = require(join(entrypoints, "kanbien-core-server-persistence-migration.main.js"));
const administration = require(join(entrypoints, "kanbien-core-server-persistence-administration.main.js"));
const roleCredential = require(join(entrypoints, "kanbien-core-server-persistence-role-credential.js"));
const iamAuthentication = require(join(entrypoints, "kanbien-core-server-persistence-iam-authentication.js"));
const restore = require(join(entrypoints, "kanbien-core-server-persistence-restore-verifier.main.js"));
const valid = {
  PERSISTENCE_POSTGRES_HOST: "postgres", PERSISTENCE_POSTGRES_PORT: "5432",
  PERSISTENCE_POSTGRES_DATABASE: "kanbienpersistence", PERSISTENCE_POSTGRES_SCHEMA: "platform",
  PERSISTENCE_POSTGRES_IAM_REGION: "eu-west-1",
  PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: "arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-ABCDEFGHIJKLMNOP/core_runtime",
  PERSISTENCE_RUNTIME_DATABASE_USERNAME: "core_runtime",
  PERSISTENCE_MIGRATION_DATABASE_USERNAME: "core_schema_migration",
  PERSISTENCE_ADMINISTRATOR_CREDENTIALS: JSON.stringify({ username: "core_administrator", password: "synthetic-administrator" }),
  PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-administrator",
  PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME: "core_runtime",
  PERSISTENCE_POSTGRES_CA_PATH: "/app/assets/fixture.crt",
  PERSISTENCE_ACCEPTANCE_RECORD_ID: "core-persistence-config-fixture",
  PERSISTENCE_ACCEPTANCE_FACT_DIGEST: "a".repeat(64),
};
for (const [purpose, timeout] of [["server", 5000], ["migration", 240000], ["restore", 30000]]) {
  assert.equal(config.persistenceConfiguration(valid, purpose).statementTimeoutMs, timeout);
}
const certificate = fs.readFileSync("platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt", "utf8");
const originalRead = fs.readFileSync;
let certificateText = certificate;
let reads = 0;
fs.readFileSync = (path, ...args) => {
  if (path === "/app/assets/fixture.crt") { reads += 1; return certificateText; }
  throw new Error("unexpected-certificate-path");
};
try {
  assert.equal(config.persistenceCertificateAuthority(valid), certificate);
  const before = reads;
  assert.equal(config.persistenceCertificateAuthority({ ...valid, PERSISTENCE_POSTGRES_CA_PATH: "/app/assets/../outside.crt" }), undefined);
  assert.equal(reads, before, "traversal must fail before filesystem access");
  certificateText = "-----BEGIN CERTIFICATE-----broken-----END CERTIFICATE-----";
  assert.equal(config.persistenceCertificateAuthority(valid), undefined);
  certificateText = certificate;
  let scenarios = 0;
  for (const [key, values] of Object.entries({
    PERSISTENCE_POSTGRES_HOST: ["", " postgres", "https://postgres"],
    PERSISTENCE_POSTGRES_PORT: ["", "0", "65536", "5432.5", " 5432", "5e3"],
    PERSISTENCE_POSTGRES_DATABASE: ["", "bad-name"],
    PERSISTENCE_POSTGRES_SCHEMA: ["", "BadSchema"],
  })) {
    for (const value of values) {
      const env = { ...valid, [key]: value };
      for (const run of [server.runKanbienCoreServerPersistenceMain, migration.runKanbienCoreServerPersistenceMigration, administration.runKanbienCoreServerPersistenceAdministration, restore.runKanbienCoreServerPersistenceRestoreVerifier]) {
        await rejectedBeforePool(run, env); scenarios += 1;
      }
    }
  }
  for (const [run, key] of [
    [server.runKanbienCoreServerPersistenceMain, "PERSISTENCE_RUNTIME_DATABASE_USERNAME"],
    [migration.runKanbienCoreServerPersistenceMigration, "PERSISTENCE_MIGRATION_DATABASE_USERNAME"],
    [administration.runKanbienCoreServerPersistenceAdministration, "PERSISTENCE_ADMINISTRATOR_CREDENTIALS"],
    [administration.runKanbienCoreServerPersistenceAdministration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME"],
    [administration.runKanbienCoreServerPersistenceAdministration, "PERSISTENCE_MIGRATION_DATABASE_USERNAME"],
    [restore.runKanbienCoreServerPersistenceRestoreVerifier, "PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME"],
  ]) {
    for (const value of ["", "bad role", "core_runtime\u0000canary"]) {
      await rejectedBeforePool(run, { ...valid, [key]: value }); scenarios += 1;
    }
  }
  await rejectedBeforePool(migration.runKanbienCoreServerPersistenceMigration, { ...valid, PERSISTENCE_MIGRATION_OPERATION: "unknown" });
  await rejectedBeforePool(administration.runKanbienCoreServerPersistenceAdministration, { ...valid, PERSISTENCE_RUNTIME_DATABASE_USERNAME: valid.PERSISTENCE_MIGRATION_DATABASE_USERNAME });
  certificateText = "not-a-certificate";
  for (const run of [server.runKanbienCoreServerPersistenceMain, migration.runKanbienCoreServerPersistenceMigration, administration.runKanbienCoreServerPersistenceAdministration, restore.runKanbienCoreServerPersistenceRestoreVerifier]) await rejectedBeforePool(run, valid);
  await roleCredentialRegression();
  await iamAuthenticationRegression();
  targetTemplateRegression();
  assert.equal(globalThis.poolAttempts, 0);
  console.log(`Persistence configuration regression passed (${scenarios + 5} entrypoint failures before pool creation; migration deadline and TLS authority validated).`);
} finally { fs.readFileSync = originalRead; }

async function rejectedBeforePool(run, env) {
  const savedError = console.error, savedCode = process.exitCode;
  const errors = [];
  console.error = (value) => errors.push(String(value));
  process.exitCode = undefined;
  try {
    await run(env);
    assert.equal(process.exitCode, 1, "invalid input must fail closed");
    assert.equal(globalThis.poolAttempts, 0, "invalid input must not construct a driver pool");
    const diagnostics = errors.join("\n");
    assert.match(diagnostics, /configuration-invalid|iam-authentication-invalid|credentials-invalid|CONFIGURATION_INVALID|tls-authority-unavailable|ADMINISTRATION_CONFIGURATION_INVALID/);
    assert.equal(diagnostics.includes("synthetic"), false, "diagnostics must not include credential values");
  } finally { console.error = savedError; process.exitCode = savedCode; }
}

async function roleCredentialRegression() {
  const absent = { exists: false, can_login: false, superuser: false, create_role: false, create_database: false, replication: false, bypass_rls: false, inherit: false };
  const bounded = { ...absent, exists: true, can_login: true };
  const statements = [];
  const pool = { query: async (statement) => {
    statements.push(statement);
    const text = statement.text;
    if (text.startsWith("SELECT EXISTS")) return { rows: [statements.filter((item) => item.text.startsWith("SELECT EXISTS")).length === 1 ? absent : bounded] };
    return { rows: [] };
  } };
  await roleCredential.ensureBoundedLoginRole(pool, { username: "core_runtime" });
  const ddl = statements.map((statement) => statement.text).join("\n");
  assert.equal(ddl.includes("PASSWORD"), false, "role identity DDL must not carry a credential or verifier");
  assert.equal(ddl.includes("SCRAM-SHA-256"), false, "a verifier is sensitive credential material too");
  const elevatedPool = { query: async () => ({ rows: [{ ...bounded, create_role: true }] }) };
  await assert.rejects(() => roleCredential.ensureBoundedLoginRole(elevatedPool, { username: "core_runtime" }), /PERSISTENCE_ROLE_PRIVILEGE_BOUNDARY_NOT_CONFIRMED/);
}

async function iamAuthenticationRegression() {
  const configuration = config.persistenceConfiguration(valid, "server");
  assert.ok(configuration);
  const local = iamAuthentication.persistenceIamAuthentication({ ...valid, NODE_ENV: "test", PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN: "synthetic-test-token" }, configuration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME");
  assert.equal(await local.authenticationToken(), "synthetic-test-token", "The disposable route must be explicit and test-only.");
  const production = iamAuthentication.persistenceIamAuthentication({ ...valid, NODE_ENV: "production", PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN: "synthetic-test-token" }, configuration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME");
  assert.notEqual(await production.authenticationToken(), "synthetic-test-token", "A local qualification token must never override the production signer.");
}

function targetTemplateRegression() {
  const template = originalRead("infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml", "utf8");
  assert.equal(template.includes("PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN"), false, "The target realization must reject the local-token test escape by never declaring it.");
  assert.equal(/Name:\s*NODE_ENV,\s*Value:\s*test/.test(template), false, "The target realization must never deploy a test runtime marker.");
  assert.equal(template.includes("PERSISTENCE_RUNTIME_CREDENTIALS"), false, "The deployed server must not receive the retired runtime password secret.");
  assert.equal(template.includes("PERSISTENCE_MIGRATION_CREDENTIALS"), false, "The deployed migration task must not receive the retired migration password secret.");
}
