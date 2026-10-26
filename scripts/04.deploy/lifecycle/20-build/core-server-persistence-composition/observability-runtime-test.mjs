#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.core-server-persistence-observability-runtime
//   version: 1
//   status: draft
//   created_on: "2026-10-26"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [sre, security]
//   kind: script
//   purpose: Prove the packaged server owns an independent PostgreSQL readiness observation and sends its approved metric to a task-local OTLP collector.
//   portability: { class: internal, targets: [] }
//   effects: [writes-files]

import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { createServer as createTcpServer } from "node:net";
import { join, resolve } from "node:path";

const compiled = resolve(process.argv[2] ?? "");
if (compiled.length === 0) throw new Error("Usage: observability-runtime-test.mjs <compiled-output-directory>");

const collector = await startCollector();
const serverPort = await availablePort();
const fakeDriver = join(compiled, "node_modules/pg");
fs.mkdirSync(fakeDriver, { recursive: true });
fs.writeFileSync(join(fakeDriver, "index.js"), `
exports.Pool = class Pool {
  constructor(options) { globalThis.__kanbienPersistencePoolOptions = options; }
  on() { return this; }
  async query() { return { rows: [], rowCount: 1 }; }
  async end() { globalThis.__kanbienPersistencePoolEnded = true; }
};
`);

const actualCertificate = fs.readFileSync("platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt", "utf8");
const originalRead = fs.readFileSync;
const originalLog = console.log;
const originalError = console.error;
const output = [];
fs.readFileSync = (path, ...args) => path === "/app/assets/fixture.crt"
  ? actualCertificate
  : originalRead(path, ...args);
console.log = (...values) => output.push(values.join(" "));
console.error = (...values) => output.push(values.join(" "));

try {
  const require = createRequire(join(compiled, "observability-runtime-test.cjs"));
  const server = require(join(compiled, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.js"));
  await server.runKanbienCoreServerPersistenceMain({
    NODE_ENV: "test",
    HOST: "127.0.0.1",
    PORT: String(serverPort),
    PLATFORM_SERVER_EXIT_AFTER_START: "1",
    PLATFORM_SOURCE_COMMIT_SHA: "a".repeat(40),
    PERSISTENCE_POSTGRES_HOST: "postgres",
    PERSISTENCE_POSTGRES_PORT: "5432",
    PERSISTENCE_POSTGRES_DATABASE: "kanbienpersistence",
    PERSISTENCE_POSTGRES_SCHEMA: "platform",
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
    PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN: "synthetic-test-token",
    PLATFORM_OBSERVABILITY_METRICS_PROVIDER: "cloudwatch-otel",
    PLATFORM_OBSERVABILITY_METRICS_ENDPOINT: "http://127.0.0.1:4318/v1/metrics",
    PLATFORM_OBSERVABILITY_METRICS_REGION: "eu-west-1",
    PLATFORM_OBSERVABILITY_SERVICE_NAME: "kanbien-core-server-persistence",
    PLATFORM_OBSERVABILITY_DEPLOYMENT_ENVIRONMENT: "kanbien-core-platform",
    PLATFORM_OBSERVABILITY_EXPORT_INTERVAL_MS: "30000",
    PLATFORM_OBSERVABILITY_EXPORT_TIMEOUT_MS: "5000",
    PLATFORM_OBSERVABILITY_TARGET: "kanbien-core-platform",
    PLATFORM_OBSERVABILITY_SCOPE: "core-server-persistence",
    PLATFORM_OBSERVABILITY_WORKLOAD: "core-server",
    PLATFORM_OBSERVABILITY_DEPENDENCY: "postgresql",
    PLATFORM_OBSERVABILITY_READINESS_CADENCE_MS: "30000",
    PLATFORM_OBSERVABILITY_READINESS_TIMEOUT_MS: "5000",
    PLATFORM_OBSERVABILITY_READINESS_STALE_AFTER_MS: "180000",
    PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON: '[{"sourceName":"platform.dependency.readiness","sourceKind":"gauge","sourceUnit":"count","instrumentName":"kanbien.core_server.postgresql_readiness","description":"Periodic PostgreSQL readiness from the core server","allowedLabelNames":["target","scope","workload","dependency","readiness"],"cardinalityLimit":16}]',
  });
} finally {
  fs.readFileSync = originalRead;
  console.log = originalLog;
  console.error = originalError;
  await closeServer(collector.server);
}

assert.equal(globalThis.__kanbienPersistencePoolEnded, true, "Server shutdown must close the target-owned PostgreSQL pool.");
assert.match(output.join("\n"), /platform\.dependency\.readiness_observed/, "The independent observer must emit the allowlisted readiness event on startup.");
assert.equal(output.join("\n").includes("synthetic-test-token"), false, "Readiness output must not expose an authentication token.");
assert.equal(output.join("\n").includes("synthetic-administrator"), false, "Readiness output must not expose a credential fixture.");
assert.equal(collector.requests, 1, "The task-local collector must receive the first readiness metric during controlled shutdown.");
console.log("Core-server persistence observability runtime proof passed.");

async function startCollector() {
  let requests = 0;
  const server = createServer((request, response) => {
    if (request.method === "POST" && request.url === "/v1/metrics") requests += 1;
    request.resume();
    response.writeHead(200).end();
  });
  await new Promise((resolvePromise, reject) => server.once("error", reject).listen(4318, "127.0.0.1", resolvePromise));
  return { server, get requests() { return requests; } };
}

async function availablePort() {
  const server = createTcpServer();
  await new Promise((resolvePromise, reject) => server.once("error", reject).listen(0, "127.0.0.1", resolvePromise));
  const address = server.address();
  if (typeof address !== "object" || address === null) throw new Error("Local server port was not allocated.");
  await closeServer(server);
  return address.port;
}

async function closeServer(server) {
  await new Promise((resolvePromise, reject) => server.close((error) => error === undefined ? resolvePromise(undefined) : reject(error)));
}
