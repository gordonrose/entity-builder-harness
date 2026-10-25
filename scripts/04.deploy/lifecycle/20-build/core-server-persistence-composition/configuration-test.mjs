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
globalThis.poolAttempts = 0;
const require = createRequire(join(compiled, "configuration-test.cjs"));
const entrypoints = join(compiled, "infra/04.deploy/03.product/entrypoints");
const config = require(join(entrypoints, "kanbien-core-server-persistence-configuration.js"));
const server = require(join(entrypoints, "kanbien-core-server-persistence.main.js"));
const migration = require(join(entrypoints, "kanbien-core-server-persistence-migration.main.js"));
const restore = require(join(entrypoints, "kanbien-core-server-persistence-restore-verifier.main.js"));
const valid = {
  PERSISTENCE_POSTGRES_HOST: "postgres", PERSISTENCE_POSTGRES_PORT: "5432",
  PERSISTENCE_POSTGRES_DATABASE: "kanbienpersistence", PERSISTENCE_POSTGRES_SCHEMA: "platform",
  PERSISTENCE_RUNTIME_SECRET_REFERENCE: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-runtime",
  PERSISTENCE_MIGRATION_SECRET_REFERENCE: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-migration",
  PERSISTENCE_RUNTIME_CREDENTIALS: JSON.stringify({ username: "core_runtime", password: "synthetic-runtime" }),
  PERSISTENCE_MIGRATION_CREDENTIALS: JSON.stringify({ username: "core_migration", password: "synthetic-migration" }),
  PERSISTENCE_RUNTIME_BOOTSTRAP_CREDENTIALS: JSON.stringify({ username: "core_runtime", password: "synthetic-runtime" }),
  PERSISTENCE_RESTORE_RUNTIME_CREDENTIALS: JSON.stringify({ username: "core_runtime", password: "synthetic-runtime" }),
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
      for (const run of [server.runKanbienCoreServerPersistenceMain, migration.runKanbienCoreServerPersistenceMigration, restore.runKanbienCoreServerPersistenceRestoreVerifier]) {
        await rejectedBeforePool(run, env); scenarios += 1;
      }
    }
  }
  for (const [run, key] of [
    [server.runKanbienCoreServerPersistenceMain, "PERSISTENCE_RUNTIME_CREDENTIALS"],
    [migration.runKanbienCoreServerPersistenceMigration, "PERSISTENCE_MIGRATION_CREDENTIALS"],
    [migration.runKanbienCoreServerPersistenceMigration, "PERSISTENCE_RUNTIME_BOOTSTRAP_CREDENTIALS"],
    [restore.runKanbienCoreServerPersistenceRestoreVerifier, "PERSISTENCE_RESTORE_RUNTIME_CREDENTIALS"],
  ]) {
    for (const value of ["not-json", "[]", JSON.stringify({ username: "bad role", password: "synthetic-canary" }), JSON.stringify({ username: "core_runtime", password: "synthetic\u0000canary" })]) {
      await rejectedBeforePool(run, { ...valid, [key]: value }); scenarios += 1;
    }
  }
  await rejectedBeforePool(migration.runKanbienCoreServerPersistenceMigration, { ...valid, PERSISTENCE_RUNTIME_BOOTSTRAP_CREDENTIALS: valid.PERSISTENCE_MIGRATION_CREDENTIALS });
  await rejectedBeforePool(migration.runKanbienCoreServerPersistenceMigration, { ...valid, PERSISTENCE_RUNTIME_CREDENTIAL_OPERATION: "unknown" });
  certificateText = "not-a-certificate";
  for (const run of [server.runKanbienCoreServerPersistenceMain, migration.runKanbienCoreServerPersistenceMigration, restore.runKanbienCoreServerPersistenceRestoreVerifier]) await rejectedBeforePool(run, valid);
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
    assert.match(diagnostics, /configuration-invalid|credentials-invalid|CONFIGURATION_INVALID|tls-authority-unavailable/);
    assert.equal(diagnostics.includes("synthetic"), false, "diagnostics must not include credential values");
  } finally { console.error = savedError; process.exitCode = savedCode; }
}
