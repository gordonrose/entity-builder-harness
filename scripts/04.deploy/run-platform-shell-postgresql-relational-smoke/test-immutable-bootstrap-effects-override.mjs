#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.script.run-platform-shell-postgresql-relational-smoke.test-immutable-bootstrap-effects-override
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: runtime.operations
//   disciplines:
//   - security
//   - sre
//   kind: script
//   purpose: Exercise the exact fixed bootstrap-effect command override in an immutable platform image against disposable TLS PostgreSQL 17.
//   portability:
//     class: internal
//     targets:
//     - kanbien/staging
//   effects:
//   - writes-files
//   - network
//   used_by:
//   - id: deploy.script.run-platform-shell-postgresql-relational-smoke
//     path: scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py

import { randomUUID } from "node:crypto";
import { chmodSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const image = process.argv[2];
if (process.argv.length !== 3 || image === undefined || !/^.+@sha256:[0-9a-f]{64}$/.test(image)) {
  console.error("Usage: test-immutable-bootstrap-effects-override.mjs <immutable-image@sha256:...>");
  process.exitCode = 2;
} else {
  run(image);
}

function run(image) {
  const identifier = randomUUID().replaceAll("-", "").slice(0, 20);
  const network = `pg-effects-${identifier}`;
  const database = `pg-effects-${identifier}`;
  const certificateVolume = `pg-effects-cert-${identifier}`;
  const certificateDirectory = mkdtempSync(join(tmpdir(), "kanbien-pg-effects-tls-"));
  const password = `fixture-${identifier}`;
  let containerStarted = false;
  let networkCreated = false;
  let certificateVolumeCreated = false;
  try {
    createCertificate(certificateDirectory);
    docker(["volume", "create", certificateVolume]);
    certificateVolumeCreated = true;
    docker(["run", "--rm", "--mount", `type=bind,source=${certificateDirectory},target=/source,readonly`, "--mount", `type=volume,source=${certificateVolume},target=/certs`, "--entrypoint", "/bin/sh", "postgres:17.11-bookworm", "-c", "cp /source/server.crt /source/server.key /certs/ && chown 999:999 /certs/server.crt /certs/server.key && chmod 600 /certs/server.key"]);
    docker(["network", "create", network]);
    networkCreated = true;
    docker([
      "run", "--detach", "--name", database, "--network", network, "--network-alias", "postgres",
      "--mount", `type=volume,source=${certificateVolume},target=/certs,readonly`,
      "-e", `POSTGRES_PASSWORD=${password}`,
      "postgres:17.11-bookworm",
      "-c", "ssl=on", "-c", "ssl_cert_file=/certs/server.crt", "-c", "ssl_key_file=/certs/server.key",
    ]);
    containerStarted = true;
    waitForPostgreSql(database);
    provisionFixture(database, password);
    const program = fixedProgram();
    const result = docker([
      "run", "--rm", "--read-only", "--network", network,
      "--mount", `type=bind,source=${join(certificateDirectory, "server.crt")},target=/app/assets/rds-eu-west-1-bundle.crt,readonly`,
      "-e", `RELATIONAL_MASTER_SECRET_JSON=${JSON.stringify({ username: "postgres", password })}`,
      "-e", `RELATIONAL_MIGRATION_SECRET_JSON=${JSON.stringify({ username: "psmokemigrate", password: "fixture-migration-password", host: "postgres", port: 5432 })}`,
      "-e", `RELATIONAL_RUNTIME_SECRET_JSON=${JSON.stringify({ username: "psmokeruntime", password: "fixture-runtime-password", host: "postgres", port: 5432 })}`,
      "--entrypoint", "/nodejs/bin/node", image, "-e", program,
    ], true);
    verifySafeFacts(result.stdout);
    console.log("Immutable PostgreSQL bootstrap-effects override test passed.");
  } finally {
    if (containerStarted) docker(["rm", "--force", database], true);
    if (networkCreated) docker(["network", "rm", network], true);
    if (certificateVolumeCreated) docker(["volume", "rm", certificateVolume], true);
    rmSync(certificateDirectory, { recursive: true, force: true });
  }
}

function createCertificate(directory) {
  const certificate = join(directory, "server.crt");
  const key = join(directory, "server.key");
  command("openssl", ["req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", certificate, "-days", "1", "-subj", "/CN=postgres", "-addext", "subjectAltName=DNS:postgres"]);
  chmodSync(certificate, 0o644);
  chmodSync(key, 0o600);
}

function waitForPostgreSql(container) {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    if (docker(["exec", container, "pg_isready", "-U", "postgres", "-d", "postgres"], true).status === 0) return;
    sleep(1_000);
  }
  throw new Error("Disposable PostgreSQL 17 did not become ready.");
}

function provisionFixture(container, password) {
  sql(container, password, "postgres", "CREATE DATABASE platformsmoke");
  const statements = [
    "CREATE ROLE psmokemigrate LOGIN PASSWORD 'fixture-migration-password'",
    "CREATE ROLE psmokeruntime LOGIN PASSWORD 'fixture-runtime-password'",
    "GRANT CONNECT, CREATE, TEMPORARY ON DATABASE platformsmoke TO psmokemigrate",
    "GRANT CONNECT ON DATABASE platformsmoke TO psmokeruntime",
    "GRANT psmokemigrate TO CURRENT_USER",
    "CREATE SCHEMA platform_smoke AUTHORIZATION psmokemigrate",
    "SET ROLE psmokemigrate; CREATE TABLE platform_smoke.bootstrap_effects_probe (id text); RESET ROLE",
    "GRANT USAGE ON SCHEMA platform_smoke TO psmokeruntime",
    "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA platform_smoke TO psmokeruntime",
  ];
  for (const statement of statements) sql(container, password, "platformsmoke", statement);
}

function sql(container, password, database, statement) {
  docker(["exec", "-e", `PGPASSWORD=${password}`, container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", database, "-c", statement]);
}

function fixedProgram() {
  const controller = readFileSync(resolve("scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py"), "utf8");
  const match = /BOOTSTRAP_EFFECTS_RECONCILIATION_PROGRAM = r"""([\s\S]+?)"""/.exec(controller);
  if (match?.[1] === undefined) throw new Error("The fixed bootstrap-effects program is unavailable.");
  return match[1];
}

function verifySafeFacts(stdout) {
  let event;
  try {
    event = JSON.parse(stdout.trim());
  } catch {
    throw new Error("The immutable bootstrap-effects override emitted no safe result.");
  }
  const factNames = [
    "migration_role_exists", "runtime_role_exists", "bootstrap_has_migration_membership",
    "migration_database_connect", "migration_database_create", "migration_database_temporary",
    "runtime_database_connect", "schema_exists", "schema_owned_by_migration",
    "runtime_schema_usage", "runtime_schema_create_restricted", "runtime_existing_table_dml",
  ];
  const fields = event?.fields;
  if (event?.level !== "info" || event?.message !== "kanbien-platform.relational-smoke.bootstrap_effects_reconciled" || fields?.outcome !== "succeeded" || Object.keys(fields).length !== factNames.length + 1 || factNames.some((name) => fields[name] !== true)) {
    throw new Error("The immutable bootstrap-effects override did not establish the reviewed resumable state.");
  }
}

function docker(commandArguments, allowFailure = false) {
  return command("docker", commandArguments, allowFailure);
}

function command(executable, commandArguments, allowFailure = false) {
  const result = spawnSync(executable, commandArguments, { encoding: "utf8" });
  if (!allowFailure && result.status !== 0) throw new Error(`${executable} execution failed.`);
  return result;
}

function sleep(milliseconds) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, milliseconds);
}
