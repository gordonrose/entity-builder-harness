// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.script.build-platform-shell-image.configuration-diagnostic-test
//   version: 2
//   status: active
//   created_on: "2026-10-30"
//   updated_on: "2026-11-05"
//   layer: 04.deploy
//   domain: diagnostics
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove actual compiled configuration predicates and safe selected diagnostic delivery without provider calls.
//   portability: { class: source-only, targets: [] }
//   effects: [writes-files]
//   used_by:
//   - id: deploy.script.build-platform-shell-image.verify-runtime-payload
//     path: scripts/04.deploy/build-platform-shell-image/verify-runtime-payload.mjs
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

/** Runs only against the actual compiled, package-isolated target payload. */
export async function verifyTargetConfigurationDiagnostics(runtimeRoot, repositoryRoot) {
  const entryRoot = join(runtimeRoot, "infra/04.deploy/03.product/entrypoints");
  const load = async (file) => import(pathToFileURL(join(runtimeRoot, file)).href);
  const target = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.js");
  const task = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-task.js");
  const sqs = await load("platform/adapters/aws/queue/sqs/src/index.js");
  const dynamo = await load("platform/adapters/aws/persistence/dynamodb/src/index.js");
  const owner = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-task-lease-owner.js");
  const require = createRequire(import.meta.url);
  const canary = "synthetic-private-target-canary";
  const expectedRecord = (code, detail) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
  const targetRecord = (setting, reason) => expectedRecord("kanbien-platform.configuration-invalid", { issues: [{ setting, reason }] });
  const workerRecord = (setting, reason) => expectedRecord("platform-worker.configuration-invalid", { issues: [{ setting, reason }] });
  const persistenceRecord = (field, reason) => expectedRecord("persistence.configuration-invalid", { field, reason });
  const sourceRecord = (phase, reason) => expectedRecord("kanbien-platform.lease-owner-source-failed", { phase, reason, effect: "not-assessed" });
  const queueEnv = { PLATFORM_WORKER_SQS_QUEUE_URL: "https://queue.invalid/fixture", PLATFORM_WORKER_SQS_REGION: "fixture-region", PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: "0", PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS: "120" };
  const persistenceEnv = { PLATFORM_PERSISTENCE_PROVIDER: "dynamodb", PLATFORM_PERSISTENCE_DYNAMODB_REGION: "fixture-region", PLATFORM_PERSISTENCE_DYNAMODB_TABLE: "fixture-store", PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX: "fixture-due", PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX: "fixture-cause" };
  const workerEnv = { ...queueEnv, PLATFORM_WORKER_QUEUE_PROVIDER: "sqs", PLATFORM_WORKER_POLL_FAILURE_BACKOFF_MS: "1", PLATFORM_SMOKE_APP_NAME: "fixture", PLATFORM_WORKER_EXIT_AFTER_START: "1", HOSTNAME: "fixture" };
  const relayEnv = { ...persistenceEnv, PLATFORM_RELAY_QUEUE_PROVIDER: "sqs", PLATFORM_RELAY_SQS_QUEUE_URL: "https://queue.invalid/fixture", PLATFORM_RELAY_SQS_REGION: "fixture-region", PLATFORM_RELAY_LEASE_DURATION_MS: "90000", HOSTNAME: "fixture", PLATFORM_RELAY_EXIT_AFTER_START: "1" };
  const serverEnv = { PLATFORM_AUTH_PROVIDER: "none", PLATFORM_DEPLOYMENT_EXPOSURE: "private", PLATFORM_SMOKE_APP_NAME: "fixture", PLATFORM_SERVER_EXIT_AFTER_START: "1", PORT: "0", HOST: "127.0.0.1" };
  function processEnvironment(values) {
    const clean = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith("PLATFORM_") && !key.startsWith("RELATIONAL_") && key !== "ECS_CONTAINER_METADATA_URI_V4"));
    for (const [key, value] of Object.entries(values)) { if (value !== undefined) clean[key] = value; else delete clean[key]; }
    return clean;
  }
  function run(main, values, record, legacyCode) {
    const result = spawnSync(process.execPath, [join(entryRoot, `kanbien-platform-${main}.main.js`)], { cwd: repositoryRoot, env: processEnvironment(values), encoding: "utf8", timeout: 10000 });
    assert.equal(result.error, undefined, `${main} must finish without provider access`);
    assert.equal(result.status, 1, `${main} must preserve rejection exit`);
    const output = result.stdout + result.stderr;
    const entries = output.split("\n").filter((line) => line.startsWith("{")).map((line) => JSON.parse(line));
    const diagnostics = entries.filter((entry) => entry.message === "platform.diagnostic.observed").map((entry) => entry.fields.diagnostic);
    assert.deepEqual(diagnostics, [record], `${main}: exact observed predicate and selected delivery`);
    if (legacyCode) assert(entries.some((entry) => entry.error?.code === legacyCode), `${main}: legacy error retained`);
    assert(!output.includes(canary), `${main}: no supplied value is emitted`);
    assert(!entries.some((entry) => entry.message?.endsWith("started")), `${main}: no workload starts`);
    return result;
  }
  // Real producer proof: preserve all four reads before choosing its original
  // first rejection, including absent/blank and Number's historical grammar.
  for (const [key, setting] of [["PLATFORM_WORKER_SQS_QUEUE_URL", "queue-address"], ["PLATFORM_WORKER_SQS_REGION", "region"]]) {
    for (const [raw, reason] of [[undefined, "missing"], ["", "blank"], [" \t", "blank"]]) {
      const reads = [];
      const env = new Proxy({ ...queueEnv, [key]: raw }, { get(value, name) { reads.push(name); return value[name]; } });
      const result = sqs.createAwsSdkPlatformSqsWorkerQueueFromEnv(env);
      assert.equal(result.ok, false);
      assert.deepEqual(reads, Object.keys(queueEnv));
      assert.deepEqual(result.error.configurationIssue, { setting, reason });
      assert.deepEqual(target.workerQueueConfigurationEvidence(result.error), { diagnosticRecord: workerRecord(setting, reason) });
      run("worker", { ...workerEnv, [key]: raw }, workerRecord(setting, reason), "KANBIEN_PLATFORM_TARGET_WORKER_CONFIG_INVALID");
    }
  }
  for (const [key, setting, maximum] of [["PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS", "receive-wait", 20], ["PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS", "visibility-timeout", 43200]]) {
    for (const [raw, reason] of [[undefined, "missing"], ["1.5", "invalid-integer"], [canary, "invalid-integer"], ["-1", "out-of-range"], [String(maximum + 1), "out-of-range"]]) {
      const reads = [];
      const result = sqs.createAwsSdkPlatformSqsWorkerQueueFromEnv(new Proxy({ ...queueEnv, [key]: raw }, { get(value, name) { reads.push(name); return value[name]; } }));
      assert.deepEqual(reads, Object.keys(queueEnv));
      assert.deepEqual(result.error.configurationIssue, { setting, reason });
      run("worker", { ...workerEnv, [key]: raw }, workerRecord(setting, reason), "KANBIEN_PLATFORM_TARGET_WORKER_CONFIG_INVALID");
    }
    for (const raw of ["", " ", "0", "0x10", `${maximum}`]) assert.equal(sqs.createAwsSdkPlatformSqsWorkerQueueFromEnv({ ...queueEnv, [key]: raw }).ok, true);
  }
  for (const malformed of [{ setting: canary, reason: "missing" }, { setting: "region", reason: canary }, { setting: "region", reason: "missing", value: canary }, Object.defineProperty({ reason: "missing" }, "setting", { get() { throw new Error(canary); }, enumerable: true })]) {
    assert.deepEqual(target.workerQueueConfigurationEvidence({ configurationIssue: malformed }), {});
  }
  let getterCalls = 0;
  assert.deepEqual(target.workerQueueConfigurationEvidence({ configurationIssue: Object.defineProperty({ reason: "missing" }, "setting", { get() { getterCalls++; return "region"; }, enumerable: true }) }), {});
  assert.equal(getterCalls, 0);
  const storeInput = { region: "fixture", tableName: "fixture", outboxDueIndexName: "fixture", lineageCauseIndexName: "fixture" };
  for (const [key, field] of [["region", "region"], ["tableName", "store"], ["outboxDueIndexName", "outbox-index"], ["lineageCauseIndexName", "lineage-index"]]) {
    const blank = dynamo.dynamoDbPersistenceConfiguration({ ...storeInput, [key]: " " });
    assert.deepEqual(blank.error.diagnosticRecord, persistenceRecord(field, "blank"));
    if (key !== "region") {
      const counts = {};
      const input = Object.fromEntries(Object.entries({ ...storeInput, [key]: "x".repeat(256) }).map(([name, value]) => [name, value]));
      const result = dynamo.dynamoDbPersistenceConfiguration(new Proxy(input, { get(value, name) { counts[name] = (counts[name] ?? 0) + 1; return value[name]; } }));
      assert.deepEqual(result.error.diagnosticRecord, persistenceRecord(field, "too-long"));
      assert.equal(result.error.details.path, key);
      const order = ["tableName", "outboxDueIndexName", "lineageCauseIndexName"];
      assert.deepEqual(counts, { region: 1, tableName: 2, outboxDueIndexName: order.indexOf(key) >= 1 ? 2 : 1, lineageCauseIndexName: key === "lineageCauseIndexName" ? 2 : 1 });
    }
  }
  run("server", { ...serverEnv, PLATFORM_AUTH_PROVIDER: canary }, targetRecord("authentication.provider", "unsupported"), "KANBIEN_PLATFORM_TARGET_AUTH_PROVIDER_INVALID");
  run("server", { ...serverEnv, PLATFORM_DEPLOYMENT_EXPOSURE: canary }, targetRecord("deployment.exposure", "unsupported"), "KANBIEN_PLATFORM_TARGET_RUNTIME_CONFIG_INVALID");
  run("server", { ...serverEnv, PLATFORM_DEPLOYMENT_EXPOSURE: "public" }, targetRecord("authentication.provider", "required-provider"), "KANBIEN_PLATFORM_TARGET_RUNTIME_CONFIG_INVALID");
  for (const [key, setting] of [["PLATFORM_RATE_LIMIT_PROVIDER", "rate-limit.provider"], ["PLATFORM_PERSISTENCE_PROVIDER", "persistence.provider"], ["PLATFORM_TRUSTED_INGRESS_MODE", "ingress.mode"]]) run("server", { ...serverEnv, [key]: canary }, targetRecord(setting, "unsupported"), "KANBIEN_PLATFORM_TARGET_RUNTIME_CONFIG_INVALID");
  const transport = [["MAX_REQUEST_BODY_BYTES", "request-body-limit"], ["MAX_HEADER_BYTES", "header-limit"], ["MAX_HEADERS_COUNT", "header-count"], ["HEADERS_TIMEOUT_MS", "headers-timeout"], ["REQUEST_TIMEOUT_MS", "request-timeout"], ["KEEP_ALIVE_TIMEOUT_MS", "keep-alive-timeout"], ["HANDLER_TIMEOUT_MS", "handler-timeout"], ["SHUTDOWN_DRAIN_TIMEOUT_MS", "shutdown-drain-timeout"], ["MAX_CONCURRENT_REQUESTS", "concurrent-requests"], ["MAX_REQUESTS_PER_SOCKET", "requests-per-socket"]];
  for (const [key, setting] of transport) for (const [raw, reason] of [[canary, "invalid-integer"], ["0", "not-positive"]]) run("server", { ...serverEnv, [`PLATFORM_SERVER_${key}`]: raw }, targetRecord(`transport.${setting}`, reason), "KANBIEN_PLATFORM_TARGET_RUNTIME_CONFIG_INVALID");
  run("server", { ...serverEnv, PLATFORM_SERVER_HEADERS_TIMEOUT_MS: "2", PLATFORM_SERVER_REQUEST_TIMEOUT_MS: "1" }, expectedRecord("platform-server.transport-configuration-inconsistent", { relationship: "headers-within-request-timeout", rule: "less-than-or-equal", phase: "configuration", effect: "rejected" }), "KANBIEN_PLATFORM_TARGET_RUNTIME_CONFIG_INVALID");
  const publicEnv = { ...serverEnv, ...persistenceEnv, PLATFORM_DEPLOYMENT_EXPOSURE: "public", PLATFORM_AUTH_PROVIDER: "cognito",
    PLATFORM_AUTH_COGNITO_REGION: "eu-west-1", PLATFORM_AUTH_COGNITO_USER_POOL_ID: "eu-west-1_EQaXioA1n", PLATFORM_AUTH_COGNITO_APP_CLIENT_ID: "4n7kuqstbvb97ur3btbur8afjt",
    PLATFORM_AUTHZ_SCOPE_PERMISSIONS: '{"platform-shell/smoke.read":["platform-smoke.smoke:read"]}',
    PLATFORM_RATE_LIMIT_PROVIDER: "dynamodb", PLATFORM_RATE_LIMIT_DYNAMODB_TABLE: "fixture", PLATFORM_RATE_LIMIT_DYNAMODB_REGION: "eu-west-1", PLATFORM_RATE_LIMIT_LIMIT: "1", PLATFORM_RATE_LIMIT_WINDOW_MS: "1000",
    PLATFORM_TRUSTED_INGRESS_MODE: "alb-security-group-only", ...Object.fromEntries(transport.map(([key]) => [`PLATFORM_SERVER_${key}`, "1"])) };
  for (const [key, setting] of transport) for (const [raw, reason] of [[undefined, "missing"], ["", "empty"]]) run("server", { ...publicEnv, [`PLATFORM_SERVER_${key}`]: raw }, targetRecord(`transport.${setting}`, reason), "KANBIEN_PLATFORM_TARGET_RUNTIME_CONFIG_INVALID");
  for (const [key, setting] of [["PLATFORM_RATE_LIMIT_PROVIDER", "rate-limit.provider"], ["PLATFORM_PERSISTENCE_PROVIDER", "persistence.provider"], ["PLATFORM_TRUSTED_INGRESS_MODE", "ingress.mode"]]) for (const [raw, reason] of [[undefined, "missing"], ["", "empty"]]) run("server", { ...publicEnv, [key]: raw }, targetRecord(setting, reason), "KANBIEN_PLATFORM_TARGET_RUNTIME_CONFIG_INVALID");
  for (const main of ["server", "worker", "relay"]) run(main, { ...(main === "server" ? serverEnv : main === "worker" ? workerEnv : relayEnv), ...persistenceEnv, PLATFORM_PERSISTENCE_DYNAMODB_TABLE: " " }, persistenceRecord("store", "blank"), `KANBIEN_PLATFORM_TARGET_${main === "server" ? "RUNTIME" : main.toUpperCase()}_CONFIG_INVALID`);
  for (const [raw, reason] of [[undefined, "missing"], ["", "empty"], [canary, "unsupported"]]) {
    run("worker", { ...workerEnv, PLATFORM_WORKER_QUEUE_PROVIDER: raw }, targetRecord("worker.queue-provider", reason), "KANBIEN_PLATFORM_TARGET_WORKER_CONFIG_INVALID");
    run("relay", { ...relayEnv, PLATFORM_PERSISTENCE_PROVIDER: raw }, targetRecord("persistence.provider", reason), "KANBIEN_PLATFORM_TARGET_RELAY_CONFIG_INVALID");
    run("relay", { ...relayEnv, PLATFORM_RELAY_QUEUE_PROVIDER: raw }, targetRecord("relay.queue-provider", reason), "KANBIEN_PLATFORM_TARGET_RELAY_CONFIG_INVALID");
  }
  for (const [raw, reason] of [[undefined, "missing"], ["", "empty"], [canary, "invalid-integer"], ["0", "not-positive"]]) run("worker", { ...workerEnv, PLATFORM_WORKER_POLL_FAILURE_BACKOFF_MS: raw }, targetRecord("worker.failure-backoff", reason), "KANBIEN_PLATFORM_TARGET_WORKER_CONFIG_INVALID");
  run("worker", { ...workerEnv, PLATFORM_WORKER_EXIT_AFTER_SUCCESSFUL_DELIVERIES: "01" }, targetRecord("worker.exit-limit", "fixed-value-required"), "KANBIEN_PLATFORM_TARGET_WORKER_CONFIG_INVALID");
  for (const [raw, reason] of [["NaN", "invalid-integer"], ["0", "not-positive"], ["120000", "not-below-visibility"]]) run("worker", { ...workerEnv, ...persistenceEnv, PLATFORM_PERSISTENCE_WORKER_LEASE_DURATION_MS: raw }, workerRecord("durable-lease-duration", reason), "KANBIEN_PLATFORM_TARGET_WORKER_CONFIG_INVALID");
  for (const [key, setting] of [["PLATFORM_RELAY_SQS_QUEUE_URL", "relay.queue-address"], ["PLATFORM_RELAY_SQS_REGION", "relay.region"]]) for (const [raw, reason] of [[undefined, "missing"], [" ", "blank"]]) run("relay", { ...relayEnv, [key]: raw }, targetRecord(setting, reason), "KANBIEN_PLATFORM_TARGET_RELAY_CONFIG_INVALID");
  for (const [raw, reason] of [[undefined, "missing"], ["", "empty"], [canary, "invalid-integer"], ["0", "not-positive"], ["90001", "above-maximum"]]) run("relay", { ...relayEnv, PLATFORM_RELAY_LEASE_DURATION_MS: raw }, targetRecord("relay.lease-duration", reason), "KANBIEN_PLATFORM_TARGET_RELAY_CONFIG_INVALID");

  const originalFetch = globalThis.fetch;
  try {
    let calls = 0;
    globalThis.fetch = async () => { calls++; throw new Error(canary); };
    for (const [value, reason] of [[canary, "malformed-url"], ["https://169.254.170.2/task", "protocol-not-allowed"], ["http://example.invalid/task", "host-not-allowed"], ["http://169.254.170.2:81/task", "port-not-allowed"], ["http://u@169.254.170.2/task", "username-not-allowed"], ["http://:p@169.254.170.2/task", "password-not-allowed"]]) {
      const result = await owner.targetTaskLeaseOwnerFromEnvironment({ ECS_CONTAINER_METADATA_URI_V4: value }, "kanbien.worker.instance-");
      assert.deepEqual(result.error.diagnosticRecord, targetRecord("lease-owner.metadata", reason));
      assert.equal(calls, 0);
    }
    const env = { ECS_CONTAINER_METADATA_URI_V4: "http://169.254.170.2/metadata" };
    assert.deepEqual((await owner.targetTaskLeaseOwnerFromEnvironment(env, "kanbien.worker.instance-")).error.diagnosticRecord, sourceRecord("request", "invocation-failed"));
    assert.equal(calls, 1);
    for (const [response, reason] of [[{ ok: false, json: async () => ({ TaskARN: canary }) }, "response-not-successful"], [{ ok: true, json: async () => ({}) }, "identity-missing"], [{ ok: true, json: async () => ({ TaskARN: 1 }) }, "identity-wrong-type"], [{ ok: true, json: async () => ({ TaskARN: "" }) }, "identity-empty"], [{ ok: true, json: async () => Object.defineProperty({}, "TaskARN", { get() { throw new Error(canary); } }) }, "identity-read-failed"], [{ ok: true, json: async () => { throw new Error(canary); } }, "response-json-failed"]]) {
      globalThis.fetch = async () => { calls++; return response; };
      assert.deepEqual((await owner.targetTaskLeaseOwnerFromEnvironment(env, "kanbien.worker.instance-")).error.diagnosticRecord, sourceRecord(reason === "response-json-failed" ? "response-json" : reason === "response-not-successful" ? "response-status" : "identity-read", reason === "response-json-failed" || reason === "identity-read-failed" ? "invocation-failed" : reason));
    }
    globalThis.fetch = async () => ({ ok: true, json: async () => ({ TaskARN: canary }) });
    assert.equal((await owner.targetTaskLeaseOwnerFromEnvironment(env, "kanbien.worker.instance-")).ok, true);
    assert.equal((await owner.targetTaskLeaseOwnerFromEnvironment({ HOSTNAME: "UPPER-case" }, "kanbien.worker.instance-")).ok, true);
    const leaseTypes = require(join(runtimeRoot, "platform/persistence/src/types.js")); const originalOwner = leaseTypes.platformPersistenceLeaseOwner;
    try { leaseTypes.platformPersistenceLeaseOwner = () => ({ ok: false, error: { code: "PLATFORM_PERSISTENCE_LEASE_OWNER_INVALID" } }); assert.deepEqual((await owner.targetTaskLeaseOwnerFromEnvironment({ HOSTNAME: "fixture" }, "kanbien.worker.instance-")).error.diagnosticRecord, targetRecord("lease-owner.local-hostname", "owner-invalid")); }
    finally { leaseTypes.platformPersistenceLeaseOwner = originalOwner; }
    const crypto = require("node:crypto"); const originalHash = crypto.createHash;
    try { crypto.createHash = () => { throw new Error(canary); }; assert.deepEqual((await owner.targetTaskLeaseOwnerFromEnvironment(env, "kanbien.worker.instance-")).error.diagnosticRecord, sourceRecord("owner-derivation", "invocation-failed")); }
    finally { crypto.createHash = originalHash; }
  } finally { globalThis.fetch = originalFetch; }
  run("worker", { ...workerEnv, ...persistenceEnv, PLATFORM_PERSISTENCE_WORKER_LEASE_DURATION_MS: "90000", HOSTNAME: undefined }, targetRecord("lease-owner.local-hostname", "missing"), "KANBIEN_PLATFORM_TARGET_WORKER_CONFIG_INVALID");
  run("relay", { ...relayEnv, HOSTNAME: canary + "/" }, targetRecord("lease-owner.local-hostname", "invalid-format"), "KANBIEN_PLATFORM_TARGET_RELAY_CONFIG_INVALID");

  const secret = { username: "fixture-user", password: canary, host: "database.invalid", port: 5432 };
  const configuration = { database: "platformsmoke", schema: "platform_smoke", tls: "verify-full", runtime_secret_arn: "arn:aws:secretsmanager:eu-west-1:337159794548:secret:fixture-runtime", migration_secret_arn: "arn:aws:secretsmanager:eu-west-1:337159794548:secret:fixture-migration" };
  const savedEnv = { ...process.env };
  function taskFailure(call, setting, reason, legacyMessage) {
    assert.throws(call, (error) => { assert(error instanceof Error); assert.equal(error.message, legacyMessage); assert.deepEqual(error.diagnosticRecord, targetRecord(setting, reason)); assert(!JSON.stringify(error).includes(canary)); return true; });
  }
  try {
    for (const [name, role] of [["RELATIONAL_MASTER_SECRET_JSON", "master"], ["RELATIONAL_MIGRATION_SECRET_JSON", "migration"], ["RELATIONAL_RUNTIME_SECRET_JSON", "runtime"], [canary, "generic"]]) {
      delete process.env[name]; taskFailure(() => task.secretFromEnvironment(name), `relational.secret.${role}.value`, "missing", "RELATIONAL_TASK_SECRET_MISSING");
      for (const [raw, reason] of [["", "invalid-json"], ["null", "wrong-shape"], ["[]", "wrong-shape"]]) { process.env[name] = raw; taskFailure(() => task.secretFromEnvironment(name), `relational.secret.${role}.value`, reason, "RELATIONAL_TASK_SECRET_INVALID"); }
      for (const field of ["username", "password", "host", "port"]) for (const [value, reason] of [[undefined, "missing"], [false, "wrong-type"], ...(field === "port" ? [[1.5, "invalid-integer"], [0, "out-of-range"], [65536, "out-of-range"]] : [["", "empty"]])]) {
        process.env[name] = JSON.stringify({ ...secret, [field]: value });
        taskFailure(() => task.secretFromEnvironment(name), `relational.secret.${role}.${field}`, reason, "RELATIONAL_TASK_SECRET_INVALID");
      }
      for (const field of ["username", "host"]) { process.env[name] = JSON.stringify({ ...secret, [field]: canary + "/" }); taskFailure(() => task.secretFromEnvironment(name), `relational.secret.${role}.${field}`, "invalid-format", "RELATIONAL_TASK_SECRET_INVALID"); }
      process.env[name] = JSON.stringify(secret); assert.deepEqual(task.secretFromEnvironment(name), secret);
      process.env[name] = JSON.stringify({ ...secret, username: "/", password: undefined }); taskFailure(() => task.secretFromEnvironment(name), `relational.secret.${role}.password`, "missing", "RELATIONAL_TASK_SECRET_INVALID");
      process.env[name] = JSON.stringify({ ...secret, host: "/", port: undefined }); taskFailure(() => task.secretFromEnvironment(name), `relational.secret.${role}.port`, "missing", "RELATIONAL_TASK_SECRET_INVALID");
      process.env[name] = JSON.stringify({ ...secret, password: " ", host: ".", port: 1, extra: canary }); assert.equal(task.secretFromEnvironment(name).password, " ");
    }
    delete process.env.RELATIONAL_CONFIG_JSON;
    taskFailure(task.configurationFromEnvironment, "relational.configuration", "missing", "RELATIONAL_TASK_CONFIGURATION_MISSING");
    for (const [raw, reason] of [["", "invalid-json"], ["null", "wrong-shape"], ["[]", "wrong-shape"]]) { process.env.RELATIONAL_CONFIG_JSON = raw; taskFailure(task.configurationFromEnvironment, "relational.configuration", reason, "RELATIONAL_TASK_CONFIGURATION_INVALID"); }
    for (const [field, setting] of [["database", "relational.database"], ["schema", "relational.schema"], ["tls", "relational.tls"], ["runtime_secret_arn", "relational.runtime-reference"], ["migration_secret_arn", "relational.migration-reference"]]) {
      for (const [value, reason] of [[undefined, "missing"], [false, "wrong-type"], ["", "empty"], [canary, field.endsWith("arn") ? "invalid-format" : "fixed-value-required"]]) {
        process.env.RELATIONAL_CONFIG_JSON = JSON.stringify({ ...configuration, [field]: value });
        taskFailure(task.configurationFromEnvironment, setting, reason, value === canary ? "RELATIONAL_TASK_CONFIGURATION_INVALID" : "RELATIONAL_TASK_SECRET_INVALID");
      }
    }
    process.env.RELATIONAL_CONFIG_JSON = JSON.stringify(configuration); assert.equal(task.configurationFromEnvironment().database, "platformsmoke");
    process.env.RELATIONAL_CONFIG_JSON = JSON.stringify({ ...configuration, database: "wrong", schema: undefined }); taskFailure(task.configurationFromEnvironment, "relational.schema", "missing", "RELATIONAL_TASK_SECRET_INVALID");
    taskFailure(() => task.connectionConfiguration({ ...secret, host: " " }, "reference"), "relational.connection.host", "blank", "RELATIONAL_TASK_CONFIGURATION_INVALID");
    taskFailure(() => task.connectionConfiguration(secret, "reference"), "relational.connection.reference", "invalid-format", "RELATIONAL_TASK_CONFIGURATION_INVALID");
  } finally {
    for (const key of Object.keys(process.env)) if (!(key in savedEnv)) delete process.env[key];
    Object.assign(process.env, savedEnv);
  }
  const taskEnv = { RELATIONAL_CONFIG_JSON: JSON.stringify(configuration), RELATIONAL_RUNTIME_SECRET_JSON: JSON.stringify(secret), RELATIONAL_MIGRATION_SECRET_JSON: JSON.stringify(secret) };
  for (const main of ["postgresql-bootstrap", "postgresql-migration", "postgresql-relay", "postgresql-worker", "postgresql-restore-verify"]) {
    const result = run(main, {}, targetRecord(main === "postgresql-bootstrap" ? "relational.secret.master.value" : "relational.configuration", "missing"));
    assert.equal(result.stdout.trim().split("\n").length, 1, "same single legacy stdout envelope");
    assert.equal(JSON.parse(result.stdout).fields.outcome, "failed");
  }
  for (const main of ["postgresql-relay", "postgresql-worker"]) for (const raw of [undefined, ""]) run(main, { ...taskEnv, RELATIONAL_SMOKE_QUEUE_URL: raw }, targetRecord("relational.queue-address", raw === undefined ? "missing" : "empty"));
  for (const raw of [undefined, canary]) run("postgresql-restore-verify", { ...taskEnv, RELATIONAL_RESTORE_HOST: raw }, targetRecord("relational.restore-host", raw === undefined ? "missing" : "invalid-format"));
  // Reporter and selector boundaries must reject malformed/unselected evidence,
  // preserve selected companions independently and isolate unavailable sinks.
  const good = target.targetConfigurationDiagnosticRecord("authentication.provider", "unsupported");
  assert.deepEqual(target.selectTargetConfigurationEvidence({ diagnosticRecord: { ...good, detail: { issues: [{ setting: canary, reason: "unsupported" }] } }, relatedDiagnosticRecords: [good] }), { relatedDiagnosticRecords: [good] });
  const originalError = console.error;
  try { console.error = () => { throw new Error(canary); }; assert.doesNotThrow(() => target.reportTargetConfigurationError({ diagnosticRecord: good })); }
  finally { console.error = originalError; }
  // Actual wrapper, with injected upstream records. The target must retain
  // valid companions even if the primary is malformed, without serializing
  // the injected native error envelope or invoking any provider operation.
  // Patch the implementation: the public facade forwards a getter-only export.
  const rate = require(join(runtimeRoot, "platform/adapters/aws/security/dynamodb-rate-limiter/src/rate-limiter.js"));
  const publicRate = require(join(runtimeRoot, "platform/adapters/aws/security/dynamodb-rate-limiter/src/index.js"));
  const server = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.js");
  const originalRate = rate.createDynamoDbFixedWindowPlatformRateLimiterFromEnv;
  const savedCode = process.exitCode; const savedProcessEnv = { ...process.env };
  const companion = target.targetConfigurationDiagnosticRecord("persistence.provider", "unsupported");
  try {
    for (const primary of [good, { ...good, detail: { issues: [{ setting: canary, reason: "unsupported" }] } }]) {
      const output = [];
      rate.createDynamoDbFixedWindowPlatformRateLimiterFromEnv = () => ({ ok: false, error: { code: "PLATFORM_ADAPTER_AWS_DYNAMODB_RATE_LIMIT_CONFIG_INVALID", defaultMessage: "Safe failure.", details: { path: "PLATFORM_RATE_LIMIT_DYNAMODB_TABLE", reason: "A non-empty value is required." }, diagnosticRecord: primary, relatedDiagnosticRecords: [companion], cause: { secret: canary } } });
      assert.equal(publicRate.createDynamoDbFixedWindowPlatformRateLimiterFromEnv, rate.createDynamoDbFixedWindowPlatformRateLimiterFromEnv, "actual public startup binding sees the injected implementation");
      for (const key of Object.keys(process.env)) delete process.env[key]; Object.assign(process.env, processEnvironment({ ...serverEnv, PLATFORM_RATE_LIMIT_PROVIDER: "dynamodb" }));
      console.error = (line) => output.push(JSON.parse(line));
      await server.runKanbienPlatformServerMain();
      assert.equal(process.exitCode, 1);
      assert.deepEqual(output.filter((entry) => entry.message === "platform.diagnostic.observed").map((entry) => entry.fields.diagnostic), primary === good ? [good, companion] : [companion]);
      assert(!JSON.stringify(output).includes(canary));
      assert.equal(output.at(-1).error.code, "KANBIEN_PLATFORM_TARGET_RUNTIME_CONFIG_INVALID");
    }
  } finally {
    rate.createDynamoDbFixedWindowPlatformRateLimiterFromEnv = originalRate; console.error = originalError;
    for (const key of Object.keys(process.env)) delete process.env[key]; Object.assign(process.env, savedProcessEnv); process.exitCode = savedCode;
  }
  for (const [main, values] of [["server", { ...serverEnv, PLATFORM_AUTH_PROVIDER: undefined, PLATFORM_DEPLOYMENT_EXPOSURE: undefined }], ["server", { ...serverEnv, PLATFORM_AUTH_PROVIDER: "", PLATFORM_RATE_LIMIT_PROVIDER: "", PLATFORM_PERSISTENCE_PROVIDER: "", PLATFORM_TRUSTED_INGRESS_MODE: "", ...Object.fromEntries(transport.map(([key]) => [`PLATFORM_SERVER_${key}`, "0x10"])) }], ["worker", { ...workerEnv, PLATFORM_WORKER_EXIT_AFTER_SUCCESSFUL_DELIVERIES: "1", PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: "", PLATFORM_PERSISTENCE_PROVIDER: "" }], ["relay", { ...relayEnv, PLATFORM_RELAY_SQS_QUEUE_URL: " https://queue.invalid/fixture ", PLATFORM_RELAY_SQS_REGION: " fixture-region " }]]) {
    const result = spawnSync(process.execPath, [join(entryRoot, `kanbien-platform-${main}.main.js`)], { cwd: repositoryRoot, env: processEnvironment(values), encoding: "utf8", timeout: 10000 });
    assert.equal(result.status, 0, `${main} retains its accepted optional/default/numeric/whitespace alternatives`);
  }
  await verifyLeaseOwnerSourceDiagnostics(runtimeRoot);
  await verifySqsConstructorConfigurationDiagnostics(runtimeRoot);
  await verifyTargetNumericGuardInvocationCounts(runtimeRoot);
  await verifySqsBridgeSelection(runtimeRoot);
}

/** Separately callable, and included in the normal payload dispatcher. This
 * focused proof invokes actual worker/relay startup with an injected source. */
export async function verifyLeaseOwnerSourceDiagnostics(runtimeRoot) {
  const load = async (file) => import(pathToFileURL(join(runtimeRoot, file)).href);
  const owner = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-task-lease-owner.js");
  const target = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.js");
  const worker = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-worker.main.js");
  const relay = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-relay.main.js");
  const canary = "synthetic-private-owner-source-canary";
  const originalFetch = globalThis.fetch; const originalError = console.error; const savedCode = process.exitCode; const savedEnv = { ...process.env };
  const expected = (phase, reason) => ({ schema: "core/diagnostic-record/v1", code: "kanbien-platform.lease-owner-source-failed", definitionVersion: 1, detail: { phase, reason, effect: "not-assessed" } });
  const metadata = { ECS_CONTAINER_METADATA_URI_V4: "http://169.254.170.2/metadata" };
  try {
    assert.equal(target.kanbienPlatformLeaseOwnerSourceDiagnostic.classification.failureKind, "unknown");
    assert.equal(target.kanbienPlatformLeaseOwnerSourceDiagnostic.classification.failureSource, "unknown");
    for (const [response, phase, reason] of [
      [async () => { throw new Error(canary); }, "request", "invocation-failed"],
      [async () => ({ json: async () => { throw new Error(canary); } }), "response-json", "invocation-failed"],
      [async () => ({ ok: true, json: async () => Object.defineProperty({}, "TaskARN", { get() { throw new Error(canary); } }) }), "identity-read", "invocation-failed"],
      [async () => ({ ok: false, json: async () => ({ TaskARN: canary }) }), "response-status", "response-not-successful"],
      [async () => Object.defineProperty({ json: async () => ({ TaskARN: canary }) }, "ok", { get() { throw new Error(canary); } }), "response-status", "invocation-failed"],
      [async () => ({ ok: true, json: async () => ({}) }), "identity-read", "identity-missing"],
      [async () => ({ ok: true, json: async () => ({ TaskARN: false }) }), "identity-read", "identity-wrong-type"],
      [async () => ({ ok: true, json: async () => ({ TaskARN: "" }) }), "identity-read", "identity-empty"],
    ]) {
      let calls = 0; const output = [];
      globalThis.fetch = async (...args) => { calls++; return response(...args); };
      console.error = (line) => output.push(JSON.parse(line));
      const result = await owner.targetTaskLeaseOwnerFromEnvironment(metadata, "kanbien.worker.instance-");
      assert.equal(calls, 1); assert.equal(result.ok, false); assert.deepEqual(result.error.diagnosticRecord, expected(phase, reason));
      target.reportTargetConfigurationError(result.error);
      assert.deepEqual(output.map((record) => record.fields.diagnostic), [expected(phase, reason)]);
      assert(!JSON.stringify(output).includes(canary));
    }
    const reads = [];
    globalThis.fetch = async () => Object.defineProperty({ json: async () => { reads.push("json"); return Object.defineProperty({}, "TaskARN", { get() { reads.push("TaskARN"); return canary; } }); } }, "ok", { get() { reads.push("ok"); throw new Error(canary); } });
    assert.deepEqual((await owner.targetTaskLeaseOwnerFromEnvironment(metadata, "kanbien.worker.instance-")).error.diagnosticRecord, expected("response-status", "invocation-failed"));
    assert.deepEqual(reads, ["json", "TaskARN", "ok"]);
    const crypto = createRequire(import.meta.url)("node:crypto"); const originalHash = crypto.createHash;
    try {
      globalThis.fetch = async () => ({ ok: true, json: async () => ({ TaskARN: canary }) });
      crypto.createHash = () => { throw new Error(canary); };
      assert.deepEqual((await owner.targetTaskLeaseOwnerFromEnvironment(metadata, "kanbien.worker.instance-")).error.diagnosticRecord, expected("owner-derivation", "invocation-failed"));
    } finally { crypto.createHash = originalHash; }
    const persistence = { PLATFORM_PERSISTENCE_PROVIDER: "dynamodb", PLATFORM_PERSISTENCE_DYNAMODB_REGION: "fixture", PLATFORM_PERSISTENCE_DYNAMODB_TABLE: "fixture", PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX: "fixture", PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX: "fixture" };
    for (const [main, values] of [[worker.runKanbienPlatformWorkerMain, { ...persistence, ...metadata, PLATFORM_WORKER_QUEUE_PROVIDER: "sqs", PLATFORM_WORKER_SQS_QUEUE_URL: "https://queue.invalid/fixture", PLATFORM_WORKER_SQS_REGION: "fixture", PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: "0", PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS: "120", PLATFORM_WORKER_POLL_FAILURE_BACKOFF_MS: "1", PLATFORM_PERSISTENCE_WORKER_LEASE_DURATION_MS: "90000" }], [relay.runKanbienPlatformRelayMain, { ...persistence, ...metadata, PLATFORM_RELAY_QUEUE_PROVIDER: "sqs", PLATFORM_RELAY_SQS_QUEUE_URL: "https://queue.invalid/fixture", PLATFORM_RELAY_SQS_REGION: "fixture", PLATFORM_RELAY_LEASE_DURATION_MS: "90000" }]]) {
      const output = []; let calls = 0;
      for (const key of Object.keys(process.env)) delete process.env[key]; Object.assign(process.env, values);
      globalThis.fetch = async () => { calls++; throw new Error(canary); }; console.error = (line) => output.push(JSON.parse(line));
      await main();
      assert.equal(calls, 1); assert.equal(process.exitCode, 1);
      assert.deepEqual(output.filter((record) => record.message === "platform.diagnostic.observed").map((record) => record.fields.diagnostic), [expected("request", "invocation-failed")]);
      assert.equal(output.at(-1).error.code, main === worker.runKanbienPlatformWorkerMain ? "KANBIEN_PLATFORM_TARGET_WORKER_CONFIG_INVALID" : "KANBIEN_PLATFORM_TARGET_RELAY_CONFIG_INVALID");
      assert(!JSON.stringify(output).includes(canary));
    }
  } finally {
    globalThis.fetch = originalFetch; console.error = originalError; process.exitCode = savedCode;
    for (const key of Object.keys(process.env)) delete process.env[key]; Object.assign(process.env, savedEnv);
  }
}

/** Actual local constructor guards, including their existing exception type,
 * message, acceptance and property-read order; no SDK invocation is permitted. */
export async function verifySqsConstructorConfigurationDiagnostics(runtimeRoot) {
  const load = async (file) => import(pathToFileURL(join(runtimeRoot, file)).href);
  const sqs = await load("platform/adapters/aws/queue/sqs/src/index.js");
  const target = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.js");
  let sends = 0;
  const sdk = createRequire(join(runtimeRoot, "runtime-fixture.cjs"))("@aws-sdk/client-sqs"); const originalSend = sdk.SQSClient.prototype.send;
  sdk.SQSClient.prototype.send = async () => { sends++; throw new Error("synthetic-private-sqs-constructor-canary"); };
  try {
  const client = { send: async () => { sends++; throw new Error("synthetic-private-sqs-constructor-canary"); } };
  const expected = (setting, reason) => ({ diagnosticRecord: { schema: "core/diagnostic-record/v1", code: "platform-worker.configuration-invalid", definitionVersion: 1, detail: { issues: [{ setting, reason }] } } });
  const valid = { queueUrl: "fixture", waitTimeSeconds: 0, visibilityTimeoutSeconds: 0, client };
  function rejected(call, setting, reason, ErrorType, message) {
    assert.throws(call, (error) => { assert(error instanceof ErrorType); assert.equal(error.message, message); assert.deepEqual(target.workerQueueConfigurationEvidence(error), expected(setting, reason)); return true; });
  }
  for (const [value, reason, ErrorType, message] of [["", "empty", RangeError, "queueUrl must not be empty."], [undefined, "missing", TypeError, "Cannot read properties of undefined (reading 'length')"], [null, "wrong-type", TypeError, "Cannot read properties of null (reading 'length')"]]) {
    const reads = [];
    rejected(() => sqs.createPlatformSqsWorkerQueue(new Proxy({ ...valid, queueUrl: value }, { get(value, name) { reads.push(name); return value[name]; } })), "queue-address", reason, ErrorType, message);
    // Original configuration reads still precede the new optional diagnostic
    // selection/delivery reads; later configuration fields remain untouched.
    assert.deepEqual(reads, ["queueUrl", "diagnosticDefinitions", "onDiagnostic"]);
  }
  for (const [key, setting, maximum] of [["waitTimeSeconds", "receive-wait", 20], ["visibilityTimeoutSeconds", "visibility-timeout", 43200]]) {
    for (const [value, reason] of [[undefined, "missing"], [null, "wrong-type"], ["1", "wrong-type"], [NaN, "not-finite"], [Infinity, "not-finite"], [-Infinity, "not-finite"], [1.5, "invalid-integer"], [-1, "out-of-range"], [maximum + 1, "out-of-range"]]) {
      const reads = [];
      rejected(() => sqs.createPlatformSqsWorkerQueue(new Proxy({ ...valid, [key]: value }, { get(value, name) { reads.push(name); return value[name]; } })), setting, reason, RangeError, `${key} must be an integer from 0 to ${maximum}.`);
      assert.deepEqual(reads, [...(key === "waitTimeSeconds" ? ["queueUrl", "waitTimeSeconds"] : ["queueUrl", "waitTimeSeconds", "visibilityTimeoutSeconds"]),
        "diagnosticDefinitions", "onDiagnostic"]);
    }
    for (const value of [0, maximum]) assert(sqs.createPlatformSqsWorkerQueue({ ...valid, [key]: value }));
  }
  rejected(() => sqs.createAwsSdkPlatformSqsWorkerQueue({ queueUrl: "fixture", region: "", waitTimeSeconds: 0, visibilityTimeoutSeconds: 0 }), "region", "empty", RangeError, "region must not be empty.");
  for (const construct of [sqs.createPlatformSqsQueue, (options) => sqs.createAwsSdkPlatformSqsQueue({ ...options, region: "fixture" })]) {
    rejected(() => construct({ queueUrl: "", client }), "queue-address", "empty", RangeError, "queueUrl must not be empty.");
    assert(construct({ queueUrl: " ", client }));
    const marker = new Error("synthetic-private-getter-canary"); let calls = 0;
    assert.throws(() => construct({ queueUrl: { get length() { calls++; throw marker; } }, client }), (error) => { assert.equal(error, marker); assert.equal(error.configurationIssue, undefined); return true; });
    assert.equal(calls, 1);
  }
  rejected(() => sqs.createAwsSdkPlatformSqsQueue({ queueUrl: "fixture", region: "" }), "region", "empty", RangeError, "region must not be empty.");
  assert(sqs.createPlatformSqsWorkerQueue({ ...valid, queueUrl: " " }));
  assert(sqs.createPlatformSqsWorkerQueue({ ...valid, queueUrl: 1 }), "historically accepted .length-undefined primitive remains accepted");
  assert.equal(sends, 0);
  const queue = sqs.createPlatformSqsWorkerQueue(valid);
  await assert.rejects(queue.acknowledge(""), (error) => { assert.equal(error.message, "receiptHandle must not be empty."); assert.equal(error.configurationIssue, undefined); return true; });
  assert.equal(sends, 0);
  } finally { sdk.SQSClient.prototype.send = originalSend; }
}

/** Watch a unique numeric input so record/schema validation cannot conceal an
 * extra coercion or repeated call to the actual configuration predicate. */
export async function verifyTargetNumericGuardInvocationCounts(runtimeRoot) {
  const load = async (file) => import(pathToFileURL(join(runtimeRoot, file)).href);
  const sqs = await load("platform/adapters/aws/queue/sqs/src/index.js");
  const server = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.js");
  const worker = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-worker.main.js");
  const relay = await load("infra/04.deploy/03.product/entrypoints/kanbien-platform-relay.main.js");
  const intrinsicNumber = Number; const integer = Number.isInteger; const finite = Number.isFinite;
  const savedEnv = { ...process.env }; const originalError = console.error; const savedCode = process.exitCode;
  const raw = "997.25"; const watched = 997.25;
  let coercions = 0; let integerCalls = 0; let finiteCalls = 0;
  const valid = { PLATFORM_AUTH_PROVIDER: "none", PLATFORM_DEPLOYMENT_EXPOSURE: "private", PLATFORM_PERSISTENCE_PROVIDER: "dynamodb", PLATFORM_PERSISTENCE_DYNAMODB_REGION: "fixture", PLATFORM_PERSISTENCE_DYNAMODB_TABLE: "fixture", PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX: "fixture", PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX: "fixture", PLATFORM_WORKER_QUEUE_PROVIDER: "sqs", PLATFORM_WORKER_SQS_QUEUE_URL: "https://queue.invalid/fixture", PLATFORM_WORKER_SQS_REGION: "fixture", PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: "0", PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS: "120", PLATFORM_WORKER_POLL_FAILURE_BACKOFF_MS: "1", PLATFORM_RELAY_QUEUE_PROVIDER: "sqs", PLATFORM_RELAY_SQS_QUEUE_URL: "https://queue.invalid/fixture", PLATFORM_RELAY_SQS_REGION: "fixture", PLATFORM_RELAY_LEASE_DURATION_MS: "90000", HOSTNAME: "fixture" };
  try {
    intrinsicNumber.isInteger = (value) => { if (Object.is(value, watched)) integerCalls++; return Reflect.apply(integer, intrinsicNumber, [value]); };
    intrinsicNumber.isFinite = (value) => { if (Object.is(value, watched)) finiteCalls++; return Reflect.apply(finite, intrinsicNumber, [value]); };
    globalThis.Number = new Proxy(intrinsicNumber, { apply(target, receiver, args) { if (args[0] === raw) coercions++; return Reflect.apply(target, receiver, args); } });
    const fromEnv = sqs.createAwsSdkPlatformSqsWorkerQueueFromEnv({ ...valid, PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: raw });
    assert.equal(fromEnv.ok, false); assert.deepEqual([coercions, integerCalls, finiteCalls], [1, 1, 0]);
    coercions = 0; integerCalls = 0; finiteCalls = 0;
    assert.throws(() => sqs.createPlatformSqsWorkerQueue({ queueUrl: "fixture", waitTimeSeconds: watched, visibilityTimeoutSeconds: 0, client: { send: async () => { throw new Error("No SDK call permitted"); } } }), RangeError);
    assert.deepEqual([coercions, integerCalls, finiteCalls], [0, 1, 0]);
    for (const [main, key] of [[server.runKanbienPlatformServerMain, "PLATFORM_SERVER_MAX_REQUEST_BODY_BYTES"], [worker.runKanbienPlatformWorkerMain, "PLATFORM_WORKER_POLL_FAILURE_BACKOFF_MS"], [relay.runKanbienPlatformRelayMain, "PLATFORM_RELAY_LEASE_DURATION_MS"]]) {
      coercions = 0; integerCalls = 0; finiteCalls = 0;
      for (const key of Object.keys(process.env)) delete process.env[key]; Object.assign(process.env, valid, { [key]: raw });
      console.error = () => {};
      await main();
      assert.equal(process.exitCode, 1); assert.deepEqual([coercions, integerCalls, finiteCalls], [1, 1, 0], key);
    }
  } finally {
    intrinsicNumber.isInteger = integer; intrinsicNumber.isFinite = finite; globalThis.Number = intrinsicNumber;
    console.error = originalError; process.exitCode = savedCode;
    for (const key of Object.keys(process.env)) delete process.env[key]; Object.assign(process.env, savedEnv);
  }
}

/** A catalog-selected worker fact may still be outside the SQS producer's
 * actual vocabulary. The target binding must reject that injected evidence. */
export async function verifySqsBridgeSelection(runtimeRoot) {
  const target = await import(pathToFileURL(join(runtimeRoot, "infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.js")).href);
  for (const setting of ["queue-address", "region", "receive-wait", "visibility-timeout"]) {
    for (const reason of ["missing", "empty", "blank", "wrong-type", "not-finite", "invalid-integer", "out-of-range"]) {
      assert.deepEqual(target.workerQueueConfigurationEvidence({ configurationIssue: { setting, reason } }), { diagnosticRecord: {
        schema: "core/diagnostic-record/v1", code: "platform-worker.configuration-invalid", definitionVersion: 1, detail: { issues: [{ setting, reason }] },
      } });
    }
    for (const reason of ["not-below-visibility", "not-positive"]) assert.deepEqual(target.workerQueueConfigurationEvidence({ configurationIssue: { setting, reason } }), {});
  }
  for (const reason of ["missing", "empty", "blank", "wrong-type", "not-finite", "invalid-integer", "out-of-range", "not-below-visibility", "not-positive"]) {
    assert.deepEqual(target.workerQueueConfigurationEvidence({ configurationIssue: { setting: "durable-lease-duration", reason } }), {});
  }
}
