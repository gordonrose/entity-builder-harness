// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.script.build-platform-shell-image.delivery-diagnostic-test
//   version: 1
//   status: active
//   created_on: "2026-10-30"
//   updated_on: "2026-11-04"
//   layer: 04.deploy
//   domain: diagnostics
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove actual compiled delivery target boundaries and bindings through local injected ports without provider operations.
//   portability: { class: source-only, targets: [] }
//   effects: [writes-files]
//   used_by:
//   - id: deploy.script.build-platform-shell-image.process-diagnostic-test
//     path: scripts/04.deploy/build-platform-shell-image/process-diagnostic-test.mjs
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join } from "node:path";

const canary = "synthetic-private-target-delivery-canary";
const entry = "infra/04.deploy/03.product/entrypoints/";
const expectedOutbox = "platform-smoke.work-item-accepted.postgresql-stage6-smoke-20260926-a";
const record = (code, detail, definitionVersion = 1) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion, detail });
const own = (workload, boundary, condition, effect, disposition) => record("kanbien-platform.delivery.boundary-observed", {
  workload, boundary, condition, effect, ...(disposition === undefined ? {} : { disposition }),
});
const observed = (output) => output.filter((value) => value.message === "platform.diagnostic.observed");
function scope() {
  const restore = [];
  return {
    patch(object, key, value) { const descriptor = Object.getOwnPropertyDescriptor(object, key); Object.defineProperty(object, key, { configurable: true, writable: true, enumerable: true, value }); restore.push(() => descriptor === undefined ? delete object[key] : Object.defineProperty(object, key, descriptor)); },
    restore() { while (restore.length > 0) restore.pop()(); },
  };
}
function capture(patches) {
  const output = [];
  for (const key of ["log", "warn", "error"]) patches.patch(console, key, (line) => output.push(JSON.parse(line)));
  return output;
}
function environment(values) {
  for (const key of Object.keys(process.env)) if (key.startsWith("PLATFORM_") || key.startsWith("RELATIONAL_") || key === "ECS_CONTAINER_METADATA_URI_V4") delete process.env[key];
  Object.assign(process.env, values);
}
function deferred() { let resolve; const promise = new Promise((done) => { resolve = done; }); return { promise, resolve }; }
async function bounded(promise) {
  let timer;
  try { await Promise.race([promise, new Promise((_, reject) => { timer = setTimeout(() => reject(new Error("Local relational fixture did not close")), 2000); })]); }
  finally { clearTimeout(timer); }
}

/** Called only after the real image compiler/package preparation has stopped. */
export async function verifyTargetDeliveryDiagnostics(runtimeRoot) {
  const require = createRequire(join(runtimeRoot, "target-delivery-diagnostic-test.cjs"));
  const load = (path) => require(join(runtimeRoot, path));
  const savedEnv = { ...process.env }, savedExit = process.exitCode;
  const scopes = [];
  const listeners = new Map(["SIGINT", "SIGTERM"].map((signal) => [signal, process.rawListeners(signal)]));
  const core = load("packages/core/src/index.js");
  const sources = Array.from({ length: 9 }, (_, ordinal) => core.corePersistenceInMemoryBoundaryRecord({ operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal }));
  const cause = Object.freeze(Object.assign(new Error(canary), { diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) }));
  const failure = { code: "FIXTURE_FAILED", defaultMessage: canary, diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) };
  const context = { runtimeRoot, require, load, core, sources, cause, failure,
    scope() { const patches = scope(); scopes.push(patches); return patches; } };
  try {
    await verifySelectedBindings(context);
    await verifyDynamoConstructors(context);
    await verifyDynamoWorker(context);
    await verifyActualSqsReceiveTarget(context);
    await verifyDynamoRelay(context);
    await verifyRelationalTargets(context);
    await verifyPostgreSqlCompositionBindings(context);
    await pgCompositionProducerRegression(context);
    await verifyRelationalMigrationAndCleanup(context);
    await verifyRelationalMigrationInvocations(context);
    await verifyOperationalContractSources(context);
    await new Promise((resolve) => setImmediate(resolve));
    for (const [signal, original] of listeners) assert.deepEqual(process.rawListeners(signal), original, "target fixtures must not leak signal listeners");
  } finally {
    for (const patches of scopes.reverse()) patches.restore();
    for (const key of Object.keys(process.env)) delete process.env[key]; Object.assign(process.env, savedEnv); process.exitCode = savedExit;
  }
}

async function verifySelectedBindings({ load, core, sources, cause, scope }) {
  const target = load(entry + "kanbien-platform-delivery-diagnostics.js");
  const enabledProfile = { name: "fixture.delivery", capability: "fixture.delivery", action: "execute", signals: ["operational_log"] };
  for (const mode of ["default", "injected", "unavailable", "throwing", "rejecting", "shadowed", "opt-out"]) {
    const patches = scope(), output = capture(patches), attempts = [], contexts = [];
    const reporter = { report(value, context) {
      assert.equal(this, reporter); attempts.push(value); contexts.push(context);
      if (mode === "throwing") throw cause;
      if (mode === "rejecting" || mode === "shadowed") {
        const pending = Promise.reject(cause);
        if (mode === "shadowed") Object.defineProperty(pending, "then", { value() { throw new Error("Shadowed promise hook must not run"); } });
        return pending;
      }
      return { status: mode === "unavailable" ? "unavailable" : "written" };
    } };
    try {
      target.reportKanbienPlatformDeliveryFailure({ workload: "worker", boundary: "receive", condition: "threw", effect: "work-not-invoked" }, cause,
        { profile: mode === "opt-out" ? { ...enabledProfile, signals: ["metric"] } : enabledProfile, ...(mode === "default" ? {} : { diagnosticReporter: reporter }) });
      const expected = [own("worker", "receive", "threw", "work-not-invoked"), ...sources];
      assert.deepEqual(observed(output).map((value) => value.fields.diagnostic), mode === "default" ? expected : []);
      assert.deepEqual(attempts, mode === "default" || mode === "opt-out" ? [] : expected);
      assert.deepEqual(contexts, attempts.map(() => ({ capability: "kanbien-platform.delivery", operation: "receive", stage: "runtime" })));
      assert(!JSON.stringify(output).includes(canary));
      let reads = 0;
      const unsafe = Object.defineProperty({ relatedDiagnosticRecords: [sources[1], { ...sources[2], detail: { ordinal: canary } }] }, "diagnosticRecord", { get() { reads++; throw cause; } });
      attempts.length = 0;
      target.reportKanbienPlatformDeliveryFailure({ workload: "worker", boundary: "receive", condition: "threw", effect: "work-not-invoked" }, unsafe, { diagnosticReporter: reporter });
      assert.equal(reads, 0); assert.deepEqual(attempts, [expected[0], sources[1]]);
      const options = { diagnosticReporter: reporter };
      attempts.length = 0;
      for (const companionDiagnosticCatalogs of [[{ owner: "fixture", definitions: [] }], [core.coreDiagnosticCatalog]]) {
        target.reportKanbienPlatformDeliveryFailure({ workload: "worker", boundary: "receive", condition: "threw", effect: "work-not-invoked" }, cause, { ...options, companionDiagnosticCatalogs });
      }
      assert.deepEqual(attempts, [], "injected reporters do not bypass malformed/duplicate catalog validation");
      const result = Object.defineProperty({}, "error", { get() { reads++; throw cause; } });
      assert.equal(target.targetDeliveryErrorSource(result), undefined); assert.equal(reads, 0);
      const queueRecord = core.coreQueueBoundaryDiagnosticRecord({ operation: "receive", boundary: "invocation", reason: "rejected", effect: "unknown" });
      const accessorContext = Object.defineProperty({}, "operation", { get() { reads++; throw cause; } });
      for (const [workload, context] of [["worker", accessorContext], ["worker", { operation: canary }], [canary, { operation: "receive" }]]) {
        target.reportKanbienPlatformQueueDiagnostic(workload, queueRecord, context, options);
      }
      target.reportKanbienPlatformQueueDiagnostic("worker", { ...queueRecord, privateValue: canary }, { operation: "receive" }, options);
      target.reportKanbienPlatformPersistenceDeliveryDiagnostic(sources[0], canary, options);
      assert.deepEqual(attempts, [], "unselected context and extra record fields must not reach a sink"); assert.equal(reads, 0);
      target.reportKanbienPlatformDeliveryFailure({ workload: "worker", boundary: "receive", condition: "threw", effect: "work-not-invoked" }, { diagnosticRecord: { ...sources[0], code: "unselected.source" } }, options);
      assert.deepEqual(attempts, [expected[0]], "unknown sources do not become valid because a reporter was injected");
    } finally { patches.restore(); }
  }
}

/** Actual Contracts producer -> target's existing selected error/source boundary. */
async function verifyOperationalContractSources({ load, sources, scope }) {
  const contracts = load("platform/contracts/src/index.js"), target = load(entry + "kanbien-platform-delivery-diagnostics.js");
  const checked = contracts.platformReadinessObservationEvent({ type: "dependency.readiness-observed", target: canary.toUpperCase(), scope: "fixture-scope", workload: "fixture-workload", dependency: "fixture-dependency", readiness: "ready", observedAt: "2026-10-31T00:00:00Z" });
  assert.equal(checked.ok, false);
  const contractOwn = record("platform-contracts.operational-event-rejected", { operation: "readiness-event", field: "target", condition: "invalid-format", phase: "validation", effect: "predicate-rejected" });
  assert.deepEqual(checked.error.diagnosticRecord, contractOwn);
  const source = { ...checked.error, relatedDiagnosticRecords: sources.slice(1) };
  for (const mode of ["default", "injected", "opt-out"]) {
    const patches = scope(), output = capture(patches), attempts = [];
    try {
      const reporter = { report(value, context) { assert.equal(this, reporter); attempts.push(value); assert.deepEqual(context, { capability: "kanbien-platform.delivery", operation: "receive", stage: "runtime" }); return { status: "written" }; } };
      target.reportKanbienPlatformDeliveryFailure({ workload: "worker", boundary: "receive", condition: "threw", effect: "work-not-invoked" }, source,
        { ...(mode === "default" ? {} : { diagnosticReporter: reporter }), ...(mode === "opt-out" ? { profile: { name: "fixture", capability: "fixture", action: "execute", signals: ["metric"] } } : {}) });
      const expected = [own("worker", "receive", "threw", "work-not-invoked"), contractOwn, ...sources.slice(1)];
      assert.deepEqual(observed(output).map((value) => value.fields.diagnostic), mode === "default" ? expected : []);
      assert.deepEqual(attempts, mode === "injected" ? expected : []);
      assert(!JSON.stringify(output).includes(canary));
    } finally { patches.restore(); }
  }
}

async function verifyRelationalMigrationAndCleanup({ runtimeRoot, require, load, sources, cause, scope }) {
  const task = load(entry + "kanbien-platform-postgresql-task.js"), migrations = load("platform/adapters/aws/persistence/postgresql/src/migrations.js");
  const cleanupSources = sources.map((value, ordinal) => ({ ...value, detail: { ...value.detail, ordinal: ordinal + 20 } }));
  const cleanup = Object.freeze(Object.assign(new Error(canary), { diagnosticRecord: cleanupSources[0], relatedDiagnosticRecords: cleanupSources.slice(1) }));
  const boundary = (phase, condition) => record("persistence.boundary-observed", { operation: "connection-pool", phase, boundary: "end", condition, effect: "not-assessed" });
  for (const at of ["undefined", "selection", "sync", "rejected"]) {
    const patches = scope(), output = capture(patches);
    let ends = 0, reads = 0;
    const pool = at === "selection" ? Object.defineProperty({}, "end", { get() { reads++; throw cleanup; } }) : { end() { assert.equal(this, pool); ends++; if (at === "sync") throw cleanup; return Promise.reject(cleanup); } };
    try {
      process.exitCode = 73;
      await task.closePool(at === "undefined" ? undefined : pool);
      assert.equal(ends, at === "undefined" || at === "selection" ? 0 : 1); assert.equal(reads, at === "selection" ? 1 : 0); assert.equal(process.exitCode, 73);
      assert.deepEqual(observed(output).map((value) => value.fields.diagnostic), at === "undefined" ? [] : [boundary(at === "rejected" ? "completion" : "invocation", at === "rejected" ? "rejected" : "threw"), ...cleanupSources]);
      assert(observed(output).every((value) => value.fields.operation === "connection-resource" && value.fields.stage === "runtime"));
      assert(!JSON.stringify(output).includes(canary));
    } finally { patches.restore(); }
  }
  for (const resultKind of ["failed", "error-accessor", "wrong-length", "succeeded"]) for (const endFails of [false, true]) {
    const patches = scope(), output = capture(patches), done = deferred(), calls = [], outcomes = [];
    const path = require.resolve(join(runtimeRoot, entry + "kanbien-platform-postgresql-migration.main.js")), cached = require.cache[path];
    let okReads = 0, valueReads = 0, lengthReads = 0, errorReads = 0;
    const result = resultKind === "failed" || resultKind === "error-accessor" ? {
      get ok() { okReads++; return false; },
      ...(resultKind === "failed" ? { error: cause } : {}),
    } : { get ok() { okReads++; return true; }, get value() { valueReads++; return { get length() { lengthReads++; return resultKind === "succeeded" ? 2 : 1; } }; } };
    if (resultKind === "error-accessor") Object.defineProperty(result, "error", { get() { errorReads++; throw cause; } });
    const reference = "arn:aws:secretsmanager:eu-west-1:337159794548:secret:fixture-migration";
    const pool = { async query(statement) { assert.equal(this, pool); calls.push(statement.text); return { rows: [] }; }, async end() { assert.equal(this, pool); calls.push("end"); if (endFails) throw cleanup; } };
    patches.patch(task, "configurationFromEnvironment", () => ({ database: "platformsmoke", schema: "platform_smoke", runtimeSecretArn: reference, migrationSecretArn: reference }));
    patches.patch(task, "secretFromEnvironment", () => ({ username: "psmokemigrate", password: canary, host: "localhost", port: 5432 }));
    patches.patch(task, "connectionPool", () => pool);
    patches.patch(migrations, "createPostgreSqlMigrationRunner", (_configuration, options) => { assert.equal(options.pool, pool); return { async apply(manifest) { calls.push("apply"); assert.equal(manifest.migrations.length, 2); return result; } }; });
    const close = task.closePool, write = task.writeOutcome;
    patches.patch(task, "closePool", async (value) => { try { assert.equal(value, pool); await close(value); } finally { done.resolve(); } });
    patches.patch(task, "writeOutcome", (operation, outcome) => { calls.push("outcome"); outcomes.push({ operation, outcome }); write(operation, outcome); });
    try {
      process.exitCode = 73; delete require.cache[path]; require(path); await bounded(done.promise);
      assert.deepEqual(calls, ["ALTER DEFAULT PRIVILEGES IN SCHEMA platform_smoke GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO psmokeruntime", "apply", "outcome", "end"]);
      assert.deepEqual(outcomes, [{ operation: "migration_completed", outcome: resultKind === "succeeded" ? "succeeded" : "failed" }]);
      assert.equal(process.exitCode, resultKind === "succeeded" ? 73 : 1);
      assert.equal(okReads, 1); assert.equal(valueReads, resultKind === "failed" || resultKind === "error-accessor" ? 0 : 1); assert.equal(lengthReads, valueReads); assert.equal(errorReads, 0);
      const expected = resultKind === "succeeded" ? [] : resultKind === "wrong-length" ? [record("persistence.local-rejected", { operation: "migration", field: "manifest", condition: "predicate-rejected", phase: "after-statements", effect: "unknown" })]
        : [record("persistence.boundary-observed", { operation: "migration", phase: "returned-result", boundary: "body", condition: "returned-failure", effect: "unknown" }), ...(resultKind === "failed" ? sources : [])];
      assert.deepEqual(observed(output).map((value) => value.fields.diagnostic), [...expected, ...(endFails ? [boundary("completion", "rejected"), ...cleanupSources] : [])]);
      assert(!JSON.stringify(output).includes(canary));
    } finally { if (cached === undefined) delete require.cache[path]; else require.cache[path] = cached; patches.restore(); }
  }
  const patches = scope(); let ends = 0;
  patches.patch(console, "error", () => { throw cause; });
  try { await task.closePool({ async end() { ends++; throw cleanup; } }); assert.equal(ends, 1, "an unavailable diagnostic sink cannot replay or reject swallowed cleanup"); }
  finally { patches.restore(); }
}

async function verifyRelationalMigrationInvocations({ runtimeRoot, require, load, sources, scope }) {
  const task = load(entry + "kanbien-platform-postgresql-task.js"), migrations = load("platform/adapters/aws/persistence/postgresql/src/migrations.js");
  const connection = load("platform/adapters/aws/persistence/postgresql/src/connection.js"), configurationDiagnostics = load(entry + "kanbien-platform-configuration-diagnostics.js");
  const queryText = "ALTER DEFAULT PRIVILEGES IN SCHEMA platform_smoke GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO psmokeruntime";
  for (const at of ["query-native", "query-native-source", "query-unknown", "query-selection", "query-primitive", "apply-frozen", "apply-primitive", "apply-null", "apply-selection", "failed-sink"]) {
    const patches = scope(), output = [], done = deferred(), calls = [], outcomes = [], caught = [], attempted = [];
    const selected = ["query-native-source", "query-selection", "apply-frozen", "apply-selection", "failed-sink"].includes(at);
    const raw = at === "apply-null" ? null : at.endsWith("primitive") ? canary : Object.freeze(Object.assign(new Error(canary),
      ...(["query-native", "query-native-source", "failed-sink"].includes(at) ? [{ code: "42501" }] : []),
      ...(selected ? [{ diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) }] : [])));
    let queries = 0, querySelections = 0, factories = 0, applies = 0, applySelections = 0, ends = 0, manifests = 0;
    const write = (line) => {
      const value = JSON.parse(line);
      if (at === "failed-sink" && value.message === "platform.diagnostic.observed" && value.fields.operation === "migration") { attempted.push(value); throw raw; }
      output.push(value);
    };
    patches.patch(console, "log", write); patches.patch(console, "error", write);
    const native = { on(event) { assert.equal(this, native); assert.equal(event, "error"); return this; }, async end() { assert.equal(this, native); calls.push("end"); ends++; } };
    Object.defineProperty(native, "query", { get() {
      querySelections++; calls.push("query-selection"); if (at === "query-selection") throw raw;
      return function(text, ...args) { assert.equal(this, native); assert.equal(text, queryText); assert.deepEqual(args, []); queries++; calls.push("query");
        return at.startsWith("query-") || at === "failed-sink" ? Promise.reject(raw) : Promise.resolve({ rows: [] });
      };
    } });
    const pool = connection.nodePoolAdapter(native);
    const reference = "arn:aws:secretsmanager:eu-west-1:337159794548:secret:fixture-migration";
    patches.patch(task, "configurationFromEnvironment", () => ({ database: "platformsmoke", schema: "platform_smoke", runtimeSecretArn: reference, migrationSecretArn: reference }));
    patches.patch(task, "secretFromEnvironment", () => ({ username: "psmokemigrate", password: canary, host: "localhost", port: 5432 }));
    patches.patch(task, "connectionPool", () => pool);
    const foundation = migrations.postgreSqlPersistenceFoundationMigration;
    patches.patch(migrations, "postgreSqlPersistenceFoundationMigration", (schema) => { manifests++; calls.push("manifest"); return foundation(schema); });
    patches.patch(migrations, "createPostgreSqlMigrationRunner", (_configuration, options, tool) => {
      factories++; calls.push("runner"); assert.equal(options.pool, pool); assert.equal(tool, "stage6-staging");
      const runner = {};
      Object.defineProperty(runner, "apply", { get() { applySelections++; calls.push("apply-selection"); if (at === "apply-selection") throw raw;
        return async function(manifest) { assert.equal(this, runner); assert.equal(manifest.migrations.length, 2); applies++; calls.push("apply"); throw raw; };
      } });
      return runner;
    });
    const report = configurationDiagnostics.reportTargetConfigurationError, close = task.closePool, outcome = task.writeOutcome;
    patches.patch(configurationDiagnostics, "reportTargetConfigurationError", function(error, ...args) { caught.push(error); calls.push("catch"); return Reflect.apply(report, this, [error, ...args]); });
    patches.patch(task, "closePool", async (value) => { try { assert.equal(value, pool); await close(value); } finally { done.resolve(); } });
    patches.patch(task, "writeOutcome", (operation, value) => { calls.push("outcome"); outcomes.push({ operation, outcome: value }); outcome(operation, value); });
    const path = require.resolve(join(runtimeRoot, entry + "kanbien-platform-postgresql-migration.main.js")), cached = require.cache[path];
    try {
      process.exitCode = 73; delete require.cache[path]; require(path); await bounded(done.promise);
      assert.equal(caught.length, 1); assert.equal(caught[0], raw, "the narrowly observed expression rethrows the identical frozen/primitive/native value");
      assert.equal(querySelections, 1); assert.equal(queries, at === "query-selection" ? 0 : 1); assert.equal(ends, 1);
      const runnerReached = at.startsWith("apply-");
      assert.equal(factories, runnerReached ? 1 : 0); assert.equal(applySelections, runnerReached ? 1 : 0); assert.equal(applies, runnerReached && at !== "apply-selection" ? 1 : 0); assert.equal(manifests, applies);
      assert.deepEqual(calls.slice(-3), ["catch", "outcome", "end"]);
      assert.deepEqual(outcomes, [{ operation: "migration_completed", outcome: "failed" }]); assert.equal(process.exitCode, 1);
      const hasPoolPhase = at.startsWith("query-") && at !== "query-primitive" || at === "failed-sink";
      const recognized = ["query-native", "query-native-source", "failed-sink"].includes(at);
      const nativeOwn = record(recognized ? "persistence.runtime-permission-denied" : "persistence.unclassified-failure", { phase: "pool_query", classification: recognized ? "permission_denied" : "unknown", codeStatus: recognized ? "recognized" : "absent", operation: "migration", effect: "unknown" }, 2);
      const unknownOwn = record("persistence.boundary-observed", { operation: "migration", phase: "invocation", boundary: "body", condition: "threw", effect: "unknown" });
      const expectedOwn = hasPoolPhase ? nativeOwn : unknownOwn;
      assert.deepEqual(observed(output).map((value) => value.fields.diagnostic), [...(at === "failed-sink" ? [] : [expectedOwn]), ...(selected ? sources : [])], "outer catch delivers source9 once; native-only bridge does not replay it");
      if (at === "failed-sink") { assert.equal(attempted.length, 1); assert.deepEqual(attempted[0].fields.diagnostic, expectedOwn); }
      const summary = output.find((value) => value.message === "kanbien-platform.relational-smoke.migration_completed");
      assert.deepEqual(summary, { level: "error", message: "kanbien-platform.relational-smoke.migration_completed", fields: { outcome: "failed" } });
      assert.equal(output.at(-1), summary, "original failure summary remains after independent observations and before quiet cleanup");
      assert(!JSON.stringify(output).includes(canary));
    } finally { if (cached === undefined) delete require.cache[path]; else require.cache[path] = cached; patches.restore(); }
  }
}

const workerEnvironment = { PLATFORM_SMOKE_APP_NAME: "fixture", PLATFORM_WORKER_QUEUE_PROVIDER: "sqs", PLATFORM_WORKER_SQS_QUEUE_URL: "https://queue.invalid/fixture", PLATFORM_WORKER_SQS_REGION: "eu-west-1", PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: "0", PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS: "120", PLATFORM_WORKER_POLL_FAILURE_BACKOFF_MS: "1", PLATFORM_WORKER_EXIT_AFTER_SUCCESSFUL_DELIVERIES: "1", HOSTNAME: "fixture" };
const relayEnvironment = { PLATFORM_PERSISTENCE_PROVIDER: "dynamodb", PLATFORM_PERSISTENCE_DYNAMODB_REGION: "eu-west-1", PLATFORM_PERSISTENCE_DYNAMODB_TABLE: "fixture-store", PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX: "fixture-due", PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX: "fixture-cause", PLATFORM_RELAY_QUEUE_PROVIDER: "sqs", PLATFORM_RELAY_SQS_QUEUE_URL: "https://queue.invalid/fixture", PLATFORM_RELAY_SQS_REGION: "eu-west-1", PLATFORM_RELAY_LEASE_DURATION_MS: "1000", HOSTNAME: "fixture" };
async function verifyDynamoConstructors({ load, sources, cause, scope }) {
  const sqsWorker = load("platform/adapters/aws/queue/sqs/src/worker.js"), sqsQueue = load("platform/adapters/aws/queue/sqs/src/queue.js");
  for (const workload of ["worker", "relay"]) {
    const patches = scope(), output = capture(patches);
    patches.patch(load(entry + "kanbien-platform-observability.js"), "observabilityFromTargetEnvironment", () => ({ ok: true, value: undefined }));
    patches.patch(load("platform/adapters/aws/persistence/dynamodb/src/client.js"), "createAwsSdkDynamoDbPersistenceCommandClient", () => ({ send() { throw new Error("Unexpected provider call"); } }));
    let calls = 0;
    try {
      environment(workload === "worker" ? workerEnvironment : relayEnvironment);
      if (workload === "worker") {
        const original = sqsWorker.createAwsSdkPlatformSqsWorkerQueueFromEnv;
        patches.patch(sqsWorker, "createAwsSdkPlatformSqsWorkerQueueFromEnv", (env, diagnostics) => { calls++; return original(new Proxy(env, { get(target, key) { if (key === "PLATFORM_WORKER_SQS_REGION") throw cause; return target[key]; } }), diagnostics); });
      } else {
        const original = sqsQueue.createAwsSdkPlatformSqsQueue;
        patches.patch(sqsQueue, "createAwsSdkPlatformSqsQueue", (options) => { calls++; return original(Object.defineProperty({ ...options }, "region", { get() { throw cause; } })); });
      }
      await assert.rejects(load(entry + `kanbien-platform-${workload}.main.js`)[workload === "worker" ? "runKanbienPlatformWorkerMain" : "runKanbienPlatformRelayMain"](), (error) => error === cause);
      assert.equal(calls, 1);
      const diagnostic = record("core.queue.boundary-failed", { operation: "client-initialization", boundary: "selection", reason: "threw", effect: "not-invoked" });
      assert.deepEqual(observed(output).map((value) => value.fields.diagnostic), [diagnostic, ...sources]);
      for (const value of observed(output)) { assert.equal(value.fields.capability, "queue"); assert.equal(value.fields.operation, `${workload}.client-initialization`); assert.equal(value.fields.stage, "startup"); assert.equal(value.correlationId, undefined); }
      assert(!JSON.stringify(output).includes(canary));
    } finally { patches.restore(); }
  }
}

/** Poll policy plus explicit callback wiring; actual adapter production is proved separately below. */
async function verifyDynamoWorker({ load, core, sources, cause, failure, scope }) {
  for (const at of ["receive", "enqueue", "enqueue-return", "run-next", "run-return", "acknowledge", "release", "shutdown"]) {
    const patches = scope(), output = capture(patches), calls = [], handlers = new Map(), delays = [];
    let receive = 0, enqueue = 0, run = 0, ack = 0, release = 0, close = 0, shutdown = 0, flush = 0;
    const closed = deferred();
    const message = { id: canary, type: "fixture.execute", version: 1, payload: {} };
    const queue = {
      async receive() { assert.equal(this, queue); calls.push("receive"); receive++;
        if (at === "receive" && receive === 1) throw cause;
        if (at === "shutdown") { handlers.get("SIGTERM")(); await closed.promise; return { kind: "empty" }; }
        if (receive > 2) { handlers.get("SIGTERM")(); await closed.promise; return { kind: "empty" }; }
        return at === "release" && receive === 1 ? { kind: "invalid", receiptHandle: canary, error: failure } : { kind: "delivery", receiptHandle: canary, message };
      },
      async acknowledge(value) { assert.equal(this, queue); assert.equal(value, canary); calls.push("acknowledge"); ack++; if (at === "acknowledge" && ack === 1) throw cause; },
      async release(value) { assert.equal(this, queue); assert.equal(value, canary); calls.push("release"); release++; if (at === "release" && release === 1) throw cause; },
    };
    const shell = {
      enqueue(value) { assert.equal(this, shell); assert.equal(value, message); calls.push("enqueue"); enqueue++; if (enqueue === 1 && at === "enqueue") throw cause; return enqueue === 1 && at === "enqueue-return" ? { ok: false, error: failure } : { ok: true }; },
      async runNext() { assert.equal(this, shell); calls.push("run-next"); run++; if (run === 1 && at === "run-next") throw cause; return run === 1 && at === "run-return" ? { ok: false, error: failure } : { ok: true, value: { status: "succeeded" } }; },
    };
    const worker = { shell, async close() { assert.equal(this, worker); calls.push("close"); close++; } };
    const telemetry = { metrics: core.noopMetrics, async forceFlush() { flush++; }, async shutdown() { shutdown++; closed.resolve(); } };
    patches.patch(load(entry + "kanbien-platform-observability.js"), "observabilityFromTargetEnvironment", () => ({ ok: true, value: telemetry }));
    patches.patch(load("platform/adapters/aws/queue/sqs/src/worker.js"), "createAwsSdkPlatformSqsWorkerQueueFromEnv", (_env, diagnostics) => {
      core.observeCoreQueueDiagnostic(diagnostics, core.coreQueueBoundaryDiagnosticRecord({ operation: "receive", boundary: "invocation", reason: "rejected", effect: "unknown" }), cause);
      return { ok: true, value: queue };
    });
    patches.patch(load("platform/workers/src/main.js"), "startPlatformWorkerProcess", async (options) => { assert.equal(options.maxAttempts, 1); assert.equal(options.installSignalHandlers, false); return { ok: true, value: worker }; });
    patches.patch(process, "once", function(signal, handler) { handlers.set(signal, handler); return this; });
    patches.patch(globalThis, "setTimeout", (callback, milliseconds) => { delays.push(milliseconds); queueMicrotask(callback); return 0; });
    try {
      environment(workerEnvironment); process.exitCode = undefined;
      await load(entry + "kanbien-platform-worker.main.js").runKanbienPlatformWorkerMain();
      assert.equal(close, 1); assert.equal(shutdown, 1); assert.equal(process.exitCode, undefined);
      assert.deepEqual([...handlers.keys()], ["SIGTERM", "SIGINT"]);
      const queueRecords = observed(output).filter((value) => value.fields.capability === "queue");
      assert.deepEqual(queueRecords.map((value) => value.fields.diagnostic), [core.coreQueueBoundaryDiagnosticRecord({ operation: "receive", boundary: "invocation", reason: "rejected", effect: "unknown" }), ...sources]);
      assert(queueRecords.every((value) => value.fields.operation === "worker.receive" && value.fields.stage === "runtime"));
      const targetRecords = observed(output).filter((value) => value.fields.capability === "kanbien-platform.delivery").map((value) => value.fields.diagnostic);
      if (at === "shutdown" || at === "run-return") assert.deepEqual(targetRecords, []);
      else assert.deepEqual(targetRecords, [own("worker", at === "enqueue-return" ? "enqueue" : at, at === "enqueue-return" ? "returned-failure" : "threw",
        at === "acknowledge" ? "work-success-acknowledgement-unknown" : at === "run-next" ? "work-outcome-unknown" : "work-not-invoked"), ...sources]);
      assert.deepEqual(delays, ["enqueue-return", "run-return", "shutdown"].includes(at) ? [] : [1]);
      if (at === "acknowledge") { assert.equal(receive, 2, "failed ack must not increment the one-success exit counter"); assert.equal(run, 2); assert.equal(ack, 2); assert.equal(release, 0); }
      else if (at === "shutdown") { assert.equal(receive, 1); assert.equal(enqueue, 0); assert.equal(run, 0); assert.equal(ack, 0); }
      else { assert.equal(receive, 2); assert.equal(ack, 1); }
      if (at === "enqueue-return" || at === "run-return" || at === "release") assert.equal(release, 1);
      assert.equal(calls.at(-1), "close"); assert.equal(flush, at === "shutdown" ? 0 : at === "enqueue-return" || at === "run-return" ? 2 : 1);
      assert(!JSON.stringify(output).includes(canary));
    } finally { patches.restore(); }
  }
}

/** Actual SQS producer -> retained adapter wrapper -> actual target poll catch. */
async function verifyActualSqsReceiveTarget({ load, core, sources, cause, scope }) {
  const patches = scope(), output = capture(patches), handlers = new Map(), delays = [];
  const sqs = load("platform/adapters/aws/queue/sqs/src/worker.js");
  const sdkCause = Object.assign(new Error(canary), { name: "RequestThrottled", diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) });
  let sends = 0, closes = 0, shutdowns = 0, jobs = 0;
  const closed = deferred();
  const client = { async send(command) {
    assert.equal(this, client); assert.equal(command.constructor.name, "ReceiveMessageCommand");
    assert.deepEqual(command.input, { QueueUrl: workerEnvironment.PLATFORM_WORKER_SQS_QUEUE_URL, MaxNumberOfMessages: 1,
      WaitTimeSeconds: 0, VisibilityTimeout: 120, MessageSystemAttributeNames: ["ApproximateReceiveCount"] });
    sends++;
    if (sends === 1) throw sdkCause;
    handlers.get("SIGTERM")(); await closed.promise; return { Messages: [] };
  } };
  patches.patch(sqs, "createAwsSdkPlatformSqsWorkerQueueFromEnv", (env, diagnostics) => ({ ok: true, value: sqs.createPlatformSqsWorkerQueue({
    queueUrl: env.PLATFORM_WORKER_SQS_QUEUE_URL, waitTimeSeconds: Number(env.PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS),
    visibilityTimeoutSeconds: Number(env.PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS), client, ...diagnostics,
  }) }));
  const worker = { shell: { enqueue() { jobs++; throw new Error("Unexpected work"); }, runNext() { jobs++; throw new Error("Unexpected work"); } }, async close() { closes++; } };
  patches.patch(load("platform/workers/src/main.js"), "startPlatformWorkerProcess", async () => ({ ok: true, value: worker }));
  patches.patch(load(entry + "kanbien-platform-observability.js"), "observabilityFromTargetEnvironment", () => ({ ok: true, value: { metrics: core.noopMetrics, async shutdown() { shutdowns++; closed.resolve(); } } }));
  patches.patch(process, "once", function(signal, handler) { handlers.set(signal, handler); return this; });
  patches.patch(globalThis, "setTimeout", (callback, milliseconds) => { delays.push(milliseconds); queueMicrotask(callback); return 0; });
  try {
    environment(workerEnvironment); process.exitCode = undefined;
    await load(entry + "kanbien-platform-worker.main.js").runKanbienPlatformWorkerMain();
    assert.equal(sends, 2); assert.equal(jobs, 0); assert.equal(closes, 1); assert.equal(shutdowns, 1); assert.deepEqual(delays, [1]);
    const records = observed(output);
    const queueOwn = record("core.queue.boundary-failed", { operation: "receive", boundary: "invocation", reason: "rejected", effect: "unknown",
      native: { codeAvailability: "recognized", condition: "request-throttled" } });
    assert.deepEqual(records.map((value) => value.fields.diagnostic), [queueOwn, ...sources, own("worker", "receive", "threw", "work-not-invoked"), ...sources]);
    for (const value of records.slice(0, 10)) { assert.equal(value.fields.capability, "queue"); assert.equal(value.fields.operation, "worker.receive"); assert.equal(value.fields.stage, "runtime"); }
    for (const value of records.slice(10)) { assert.equal(value.fields.capability, "kanbien-platform.delivery"); assert.equal(value.fields.operation, "receive"); assert.equal(value.fields.stage, "runtime"); }
    assert(!JSON.stringify(output).includes(canary));
  } finally { patches.restore(); }
}

/** Target run-once outcomes and explicit callback wiring, not an SDK send qualification. */
async function verifyDynamoRelay({ load, core, sources, cause, scope }) {
  for (const status of ["threw", "published", "queue-send-failed", "publish-marker-failed"]) {
    const patches = scope(), output = capture(patches), calls = [];
    const telemetry = { metrics: core.noopMetrics, async forceFlush() { calls.push("flush"); }, async shutdown() { calls.push("shutdown"); } };
    patches.patch(load(entry + "kanbien-platform-observability.js"), "observabilityFromTargetEnvironment", () => ({ ok: true, value: telemetry }));
    patches.patch(load("platform/adapters/aws/persistence/dynamodb/src/client.js"), "createAwsSdkDynamoDbPersistenceCommandClient", () => ({ send() { throw new Error("Unexpected provider call"); } }));
    patches.patch(load("platform/adapters/aws/queue/sqs/src/queue.js"), "createAwsSdkPlatformSqsQueue", (options) => {
      core.observeCoreQueueDiagnostic(options, core.coreQueueBoundaryDiagnosticRecord({ operation: "send", boundary: "invocation", reason: "rejected", effect: "unknown" }), cause);
      return { send() { throw new Error("Unexpected queue send"); } };
    });
    const relay = { async runOnce() { assert.equal(this, relay); calls.push("run-once"); if (status === "threw") throw cause; return { ok: true, value: { status } }; } };
    patches.patch(load(entry + "kanbien-platform-persistence.js"), "createKanbienPlatformOutboxRelay", () => relay);
    try {
      environment(relayEnvironment); process.exitCode = undefined;
      const run = load(entry + "kanbien-platform-relay.main.js").runKanbienPlatformRelayMain;
      if (status === "threw") await assert.rejects(run(), (error) => error === cause); else await run();
      assert.deepEqual(calls, ["run-once", "flush", "shutdown"]);
      const records = observed(output);
      assert.deepEqual(records.filter((value) => value.fields.capability === "queue").map((value) => value.fields.diagnostic), [core.coreQueueBoundaryDiagnosticRecord({ operation: "send", boundary: "invocation", reason: "rejected", effect: "unknown" }), ...sources]);
      assert.deepEqual(records.filter((value) => value.fields.capability === "kanbien-platform.delivery").map((value) => value.fields.diagnostic), status === "threw" ? [own("relay", "run-once", "threw", "work-outcome-unknown"), ...sources] : []);
      if (status !== "threw") { assert.deepEqual(output.find((value) => value.message === "kanbien-platform.relay.run_completed")?.fields, { status }); assert.equal(process.exitCode, status === "published" ? undefined : 1); }
      assert(!JSON.stringify(output).includes(canary));
    } finally { patches.restore(); }
  }
}

/** Real composition predicate -> actual one-shot binding -> selected reporter. */
async function verifyPostgreSqlCompositionBindings({ runtimeRoot, require, load, scope }) {
  const task = load(entry + "kanbien-platform-postgresql-task.js");
  const migrations = load("platform/adapters/aws/persistence/postgresql/src/migrations.js");
  for (const workload of ["relay", "migration", "restore-verify"]) {
    const patches = scope(), output = capture(patches), done = deferred(), calls = [], outcomes = [];
    const path = require.resolve(join(runtimeRoot, entry + `kanbien-platform-postgresql-${workload}.main.js`));
    const cached = require.cache[path];
    let pool;
    const reference = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:fixture";
    patches.patch(task, "configurationFromEnvironment", () => ({ database: "platformsmoke", schema: canary,
      runtimeSecretArn: reference, migrationSecretArn: reference }));
    patches.patch(task, "secretFromEnvironment", () => ({ username: canary, password: canary, host: canary, port: 5432 }));
    const connectionConfiguration = task.connectionConfiguration;
    // The adapter connection-schema guard is independent of this target guard.
    // Keep a genuinely validated sibling configuration to reach the latter.
    patches.patch(task, "connectionConfiguration", (secret, reference) => connectionConfiguration(secret, reference, "platform_smoke"));
    patches.patch(task, "connectionPool", () => {
      calls.push("pool");
      pool = { async query(statement) { calls.push(statement.text); return { rows: [] }; }, async end() { calls.push("end"); } };
      return pool;
    });
    const closePool = task.closePool, writeOutcome = task.writeOutcome, writeRestoreFailure = task.writeRestoreVerificationFailure;
    patches.patch(task, "closePool", async (value) => {
      try { assert.equal(value, pool); await closePool(value); } finally { done.resolve(); }
    });
    patches.patch(task, "writeOutcome", (operation, outcome) => { outcomes.push({ operation, outcome }); writeOutcome(operation, outcome); });
    patches.patch(task, "writeRestoreVerificationFailure", (details) => { outcomes.push(details); writeRestoreFailure(details); });
    // The preceding foundation migration is a separate adapter-owned predicate.
    // Bypass only that sibling to reach this real target-owned schema guard.
    patches.patch(migrations, "postgreSqlPersistenceFoundationMigration", () => ({ id: "foundation", checksum: "fixture", statements: [] }));
    try {
      environment({ RELATIONAL_SMOKE_QUEUE_URL: "https://queue.invalid/fixture",
        RELATIONAL_RESTORE_HOST: "kanbien-staging-platform-relational-restore-proof-fixture.a.eu-west-1.rds.amazonaws.com" });
      process.exitCode = undefined;
      delete require.cache[path]; require(path); await bounded(done.promise);
      const operation = workload === "relay" ? "compose" : "migration";
      assert.deepEqual(observed(output).map((value) => value.fields.diagnostic), [record("kanbien-platform.postgresql.composition-boundary-failed", {
        operation, phase: "schema-predicate", condition: "predicate-rejected", effect: "not-started",
      }), ...(workload === "migration" ? [record("persistence.boundary-observed", {
        operation: "migration", phase: "invocation", boundary: "body", condition: "threw", effect: "unknown",
      })] : [])], `${workload}: composition predicate and actual invocation boundary remain independent, without inferred native cause`);
      assert.equal(process.exitCode, 1);
      assert.deepEqual(calls, workload === "relay" ? ["pool", "end"] : workload === "migration"
        ? ["pool", "ALTER DEFAULT PRIVILEGES IN SCHEMA platform_smoke GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO psmokeruntime", "end"]
        : ["pool", "SELECT 1", "end"], `${workload}: original query/cleanup order and count`);
      if (workload === "restore-verify") {
        assert.equal(outcomes.length, 1);
        assert.equal(outcomes[0].failure_phase, "migration-checksum-verification");
        assert.equal(outcomes[0].failure_category, "restore-database-query-failure");
        assert.deepEqual(outcomes[0].observed, { migration_checksums: "not-queried", accepted_work_item: "not-queried",
          published_outbox: "not-queried", completed_processing: "not-queried" });
        const details = require(path).restoreVerificationFailureDetails;
        const unknown = details({ code: "CANRY" }, "connection", outcomes[0].observed);
        assert.equal(unknown.database_error_code, undefined, "an arbitrary five-character error value is not a selected provider code");
        assert.equal(unknown.failure_category, "restore-database-query-failure");
        const known = details({ code: "42501" }, "connection", outcomes[0].observed);
        assert.equal(known.database_error_code, "42501");
        assert.equal(known.failure_category, "restore-database-authorization-failure");
      } else assert.deepEqual(outcomes, [{ operation: workload === "relay" ? "relay_completed" : "migration_completed", outcome: "failed" }]);
      assert(!JSON.stringify(output).includes(canary));
    } finally {
      if (cached === undefined) delete require.cache[path]; else require.cache[path] = cached;
      patches.restore();
    }
  }
}

async function pgCompositionProducerRegression({ runtimeRoot, require, load }) {
  const pgCompositionDiagnostics = load(entry + "kanbien-platform-postgresql-operation-diagnostics.js");
  const composition = load(entry + "kanbien-platform-postgresql-persistence.js");
  const literal = record("kanbien-platform.postgresql.composition-boundary-failed", { operation: "create", phase: "work-item-revision", condition: "threw", effect: "not-staged" });
  assert.deepEqual(pgCompositionDiagnostics.compositionBoundaryRecord(literal.detail), literal);
  const definitions = pgCompositionDiagnostics.kanbienPlatformPostgreSqlOperationDiagnosticCatalog.definitions;
  assert.deepEqual(definitions.map(({ code }) => code), [literal.code]);
  const { parseDiagnosticRecord } = load("packages/core/src/diagnostics/index.js");
  assert.equal(parseDiagnosticRecord(definitions[0], literal).ok, true);
  for (const bad of [{ ...literal, definitionVersion: 2 }, { ...literal, detail: { ...literal.detail, raw: "PRIVATE-canary" } }, { ...literal, detail: { ...literal.detail, effect: "definitely-rolled-back" } }]) assert.equal(parseDiagnosticRecord(definitions[0], bad).ok, false);
  const records = [], contexts = [];
  const source = Array.from({ length: 9 }, (_, ordinal) => ({ schema: "core/diagnostic-record/v1", code: "core.persistence.in-memory-boundary-failed", definitionVersion: 1,
    detail: { operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal } }));
  const native = Object.freeze(Object.assign(new Error("PRIVATE-PG-canary"), { diagnosticRecord: source[0], relatedDiagnosticRecords: source.slice(1) }));
  const options = { onDiagnostic(record, context) { records.push(record); contexts.push(context); } };
  assert.throws(() => composition.kanbienPlatformSmokePostgreSqlMigration("_valid-role-not-smoke", options), /reviewed lowercase schema/);
  assert.deepEqual(records[0].detail, { operation: "migration", phase: "schema-predicate", condition: "predicate-rejected", effect: "not-started" });
  records.length = contexts.length = 0;
  assert.throws(() => composition.createKanbienPlatformPostgreSqlSmokePersistence({ get configuration() { throw native; } }, options), (error) => error === native);
  assert.equal(records.length, 10); assert.deepEqual(records.slice(1), source); assert.equal(contexts.every((context) => context.operation === "compose" && context.phase === "configuration"), true);
  records.length = contexts.length = 0;
  const schemaReads = [];
  assert.throws(() => composition.createKanbienPlatformPostgreSqlSmokePersistence({ get configuration() { schemaReads.push("configuration"); return { get schema() { schemaReads.push("schema"); return { toString() { schemaReads.push("coercion"); throw native; } }; } }; } }, options), (error) => error === native);
  assert.deepEqual(schemaReads, ["configuration", "schema", "coercion"]); assert.equal(records[0].detail.phase, "schema-predicate");
  const configuration = load(entry + "kanbien-platform-postgresql-task.js").connectionConfiguration({ host: "localhost", port: 5432 }, "arn:aws:secretsmanager:eu-west-1:123456789012:secret:fixture", "platform_smoke"), pool = { query: async () => ({ rows: [] }) };
  const repository = composition.createKanbienPlatformPostgreSqlSmokePersistence({ configuration, pool }, options).repository;
  for (const property of ["workItem", "transaction"]) {
    records.length = 0; let reads = 0;
    await assert.rejects(() => repository.create(Object.defineProperty({ workItem: {}, transaction: {} }, property, { get() { reads++; throw native; } })), (error) => error === native);
    assert.equal(reads, 1); assert.equal(records.length, 10); assert.equal(records[0].detail.phase, "input-projection");
  }
  for (const [property, phase] of [["id", "work-item-id"], ["state", "work-item-state"], ["revision", "work-item-revision"], ["acceptedAt", "work-item-accepted-at"]]) {
    records.length = 0;
    await assert.rejects(() => repository.create({ workItem: Object.defineProperty({ id: "id", state: "accepted", revision: 1, acceptedAt: "now" }, property, { get() { throw native; } }), transaction: {} }), (error) => error === native);
    assert.deepEqual(records[0].detail, { operation: "create", phase, condition: "threw", effect: "not-staged" }); assert.deepEqual(records.slice(1), source);
  }
  const calls = [], delivered = [];
  records.length = 0;
  const failed = await repository.create({ workItem: { get id() { calls.push("id"); return { toString() { calls.push("String"); return "id"; } }; }, get state() { calls.push("state"); return "accepted"; }, get revision() { calls.push("revision"); return { valueOf() { calls.push("Number"); return 1; } }; }, get acceptedAt() { calls.push("accepted"); return "now"; } }, transaction: {} });
  assert.equal(failed.ok, false); assert.deepEqual(calls, ["id", "String", "state", "revision", "Number", "accepted"]);
  assert.equal(records[0].detail.phase, "staging-result");
  const transactions = require(join(runtimeRoot, "platform/adapters/aws/persistence/postgresql/src/transactions.js"));
  const originalStage = transactions.stagePostgreSqlTransactionStatement;
  try {
    let errorReads = 0;
    const returned = { ok: false, get error() { errorReads++; throw native; } };
    transactions.stagePostgreSqlTransactionStatement = () => returned;
    records.length = 0;
    assert.equal(await repository.create({ workItem: { id: "id", state: "accepted", revision: 1, acceptedAt: "now" }, transaction: {} }), returned);
    assert.equal(errorReads, 0, "new evidence must not invoke returned error accessors"); assert.equal(records.length, 1);
    transactions.stagePostgreSqlTransactionStatement = () => { throw native; };
    records.length = 0;
    await assert.rejects(() => repository.create({ workItem: { id: "id", state: "accepted", revision: 1, acceptedAt: "now" }, transaction: {} }), (error) => error === native);
    assert.equal(records[0].detail.phase, "statement-staging"); assert.equal(records[0].detail.effect, "unknown"); assert.deepEqual(records.slice(1), source);
  } finally { transactions.stagePostgreSqlTransactionStatement = originalStage; }
  for (const [operation, phase, stage] of [["migration", "schema-predicate", "migration"], ["compose", "writer-construction", "configuration"], ["create", "statement-staging", "runtime"]]) {
    delivered.length = 0;
    const own = pgCompositionDiagnostics.compositionBoundaryRecord({ operation, phase, condition: "threw", effect: "unknown" });
    for (const record of [own, ...source]) pgCompositionDiagnostics.reportKanbienPlatformPostgreSqlDiagnostic(record, { operation, phase }, { diagnosticReporter: { report(record, context) { delivered.push({ record, context }); return { status: "written" }; } } });
    assert.equal(delivered.length, 10); assert.deepEqual(delivered.slice(1).map(({ record }) => record), source);
    assert.equal(delivered[0].record.detail.phase, phase);
    assert.equal(delivered.every(({ context }) => context.operation === operation && context.stage === stage), true);
  }
  for (const sink of [() => { throw native; }, () => Promise.reject(native), () => Object.assign(Promise.reject(native), { then() { throw native; } })]) {
    assert.throws(() => composition.kanbienPlatformSmokePostgreSqlMigration("_", { onDiagnostic: sink }), /reviewed lowercase schema/);
    pgCompositionDiagnostics.reportKanbienPlatformPostgreSqlDiagnostic(records[0], undefined, { diagnosticReporter: { report: sink } });
  }
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(JSON.stringify(delivered).includes("PRIVATE-"), false);
}

async function verifyRelationalTargets({ runtimeRoot, require, load, core, sources, cause, failure, scope }) {
  const task = load(entry + "kanbien-platform-postgresql-task.js");
  const processing = load("platform/adapters/aws/persistence/postgresql/src/processing.js");
  const outbox = load("platform/adapters/aws/persistence/postgresql/src/outbox.js");
  const sqsWorker = load("platform/adapters/aws/queue/sqs/src/worker.js"), sqsQueue = load("platform/adapters/aws/queue/sqs/src/queue.js");
  const persistence = load("platform/persistence/src/relay.js");
  const appAcceptance = load("apps/platform-smoke/src/persistence/acceptance.js");
  const expectedWorker = ["success", "receive", "not-delivery", "null", "array", "nonobject", "missing-id", "wrong-id-type", "mismatch", "payload-getter", "owner", "claim-return", "claim-throw", "claim-disposition", "missing-lease", "complete-return", "complete-throw", "complete-disposition", "acknowledge"];
  for (const workload of ["worker", "relay"]) for (const at of workload === "worker" ? expectedWorker : ["success", "identifier", "owner", "acceptance-return", "acceptance-throw", "relay-return", "relay-throw", "relay-disposition"]) {
    const patches = scope(), output = capture(patches), done = deferred(), calls = [], outcomes = [];
    let pool;
    let payloadReads = 0;
    const queue = { async receive() { assert.equal(this, queue); calls.push("receive"); if (at === "receive") throw cause;
      if (at === "not-delivery") return { kind: "invalid", error: failure, receiptHandle: canary };
      const payload = at === "null" ? null : at === "array" ? [] : at === "nonobject" ? false : at === "missing-id" ? {} : at === "wrong-id-type" ? { outboxEntryId: 1 } :
        { get outboxEntryId() { payloadReads++; if (at === "payload-getter") throw cause; return at === "mismatch" ? canary : expectedOutbox; } };
      return { kind: "delivery", receiptHandle: canary, message: { payload } };
    }, async acknowledge(value) { assert.equal(this, queue); assert.equal(value, canary); calls.push("acknowledge"); if (at === "acknowledge") throw cause; } };
    const store = { async claim() { assert.equal(this, store); calls.push("claim"); if (at === "claim-throw") throw cause;
      if (at === "claim-return") return { ok: false, error: failure };
      return { ok: true, value: { disposition: at === "claim-disposition" ? "lease-active" : "claimed", record: at === "missing-lease" ? {} : { lease: { fence: 1 } } } };
    }, async complete() { assert.equal(this, store); calls.push("complete"); if (at === "complete-throw") throw cause;
      if (at === "complete-return") return { ok: false, error: failure };
      return { ok: true, value: { disposition: at === "complete-disposition" ? "already-completed" : "completed" } };
    } };
    patches.patch(task, "configurationFromEnvironment", () => ({ database: "platformsmoke", schema: "platform_smoke", runtimeSecretArn: "fixture", migrationSecretArn: "fixture" }));
    patches.patch(task, "secretFromEnvironment", () => ({ username: canary, password: canary, host: canary, port: 5432 }));
    patches.patch(task, "connectionPool", () => { calls.push("pool"); pool = { async end() { calls.push("end"); } }; return pool; });
    const closePool = task.closePool, writeOutcome = task.writeOutcome;
    patches.patch(task, "closePool", async (value) => { try { assert.equal(value, pool); await closePool(value); } finally { done.resolve(); } });
    patches.patch(task, "writeOutcome", (operation, outcome) => { outcomes.push({ operation, outcome }); writeOutcome(operation, outcome); });
    patches.patch(sqsWorker, "createAwsSdkPlatformSqsWorkerQueue", (options) => {
      core.observeCoreQueueDiagnostic(options, core.coreQueueBoundaryDiagnosticRecord({ operation: "receive", boundary: "invocation", reason: "rejected", effect: "unknown" }), cause);
      return queue;
    });
    patches.patch(processing, "createPostgreSqlPlatformProcessingStore", (options) => {
      const bound = {};
      for (const method of ["claim", "complete"]) bound[method] = async function(...args) { for (const source of sources) options.onDiagnostic(source); return Reflect.apply(store[method], store, args); };
      return bound;
    });
    patches.patch(load(entry + "kanbien-platform-postgresql-persistence.js"), "createKanbienPlatformPostgreSqlSmokePersistence", () => ({}));
    const ownerType = load("platform/persistence/src/types.js"), originalOwner = ownerType.platformPersistenceLeaseOwner;
    patches.patch(ownerType, "platformPersistenceLeaseOwner", (value) => at === "owner" ? { ok: false, error: failure } : originalOwner(value));
    const workItemType = load("apps/platform-smoke/src/persistence/types.js"), originalIdentifier = workItemType.platformSmokeWorkItemId;
    patches.patch(workItemType, "platformSmokeWorkItemId", (value) => at === "identifier" ? { ok: false, error: failure } : originalIdentifier(value));
    patches.patch(appAcceptance, "acceptPlatformSmokeWorkItem", async (_input, _dependencies, options) => { calls.push("acceptance"); for (const source of sources) options.onDiagnostic(source); if (at === "acceptance-throw") throw cause; return at === "acceptance-return" ? { ok: false, error: failure } : { ok: true, value: {} }; });
    patches.patch(outbox, "createPostgreSqlPlatformOutboxStore", (options) => { for (const source of sources) options.onDiagnostic(source); return {}; });
    patches.patch(sqsQueue, "createAwsSdkPlatformSqsQueue", (options) => { core.observeCoreQueueDiagnostic(options, core.coreQueueBoundaryDiagnosticRecord({ operation: "send", boundary: "invocation", reason: "rejected", effect: "unknown" }), cause); return {}; });
    patches.patch(persistence, "createPlatformOutboxRelay", () => ({ async runOnce() { calls.push("run-once"); if (at === "relay-throw") throw cause; return at === "relay-return" ? { ok: false, error: failure } : { ok: true, value: { status: at === "relay-disposition" ? "idle" : "published" } }; } }));
    const path = require.resolve(join(runtimeRoot, entry + `kanbien-platform-postgresql-${workload}.main.js`));
    const cached = require.cache[path];
    try {
      environment({ RELATIONAL_SMOKE_QUEUE_URL: "https://queue.invalid/fixture" }); process.exitCode = undefined;
      delete require.cache[path]; require(path); await bounded(done.promise);
      assert.deepEqual(outcomes, [{ operation: workload === "worker" ? "worker_completed" : "relay_completed", outcome: at === "success" ? "succeeded" : "failed" }]);
      assert.equal(process.exitCode, at === "success" ? undefined : 1); assert.equal(calls.at(-1), "end"); assert.equal(calls.filter((value) => value === "end").length, 1);
      const precise = observed(output).filter((value) => value.fields.capability === "kanbien-platform.delivery").map((value) => value.fields.diagnostic);
      let boundary, condition, disposition;
      if (at !== "success") {
        boundary = at === "receive" ? "receive" : at === "not-delivery" ? "delivery-selection" : at === "owner" ? "owner-validation" : at === "identifier" || ["null", "array", "nonobject", "missing-id", "wrong-id-type", "mismatch", "payload-getter"].includes(at) ? "identity-check" : at.startsWith("claim") || at === "missing-lease" ? at === "claim-throw" ? "claim" : "claim-result" : at.startsWith("complete") ? at === "complete-throw" ? "complete" : "completion-result" : at === "acknowledge" ? "acknowledge" : at.startsWith("acceptance") ? "acceptance" : "run-once";
        condition = at === "not-delivery" ? "not-delivery" : at === "owner" ? "invalid-owner" : at === "identifier" ? "returned-failure" : at === "null" ? "payload-null" : at === "array" ? "payload-array" : at === "nonobject" ? "payload-not-record" : at === "missing-id" ? "payload-id-missing" : at === "wrong-id-type" ? "payload-id-wrong-type" : at === "mismatch" ? "payload-id-mismatch" : at === "missing-lease" ? "missing-lease" : at.endsWith("disposition") ? "unexpected-disposition" : at.endsWith("return") ? "returned-failure" : "threw";
        disposition = at === "not-delivery" ? "invalid" : at === "claim-disposition" ? "lease-active" : at === "complete-disposition" ? "already-completed" : at === "relay-disposition" ? "idle" : undefined;
        const hasSource = ["receive", "not-delivery", "payload-getter", "owner", "identifier", "claim-return", "claim-throw", "complete-return", "complete-throw", "acknowledge", "acceptance-return", "acceptance-throw", "relay-return", "relay-throw"].includes(at);
        const effect = workload === "relay" ? "work-outcome-unknown" : at === "acknowledge" ? "work-success-acknowledgement-unknown" : boundary === "claim" || boundary === "claim-result" || boundary === "complete" || boundary === "completion-result" ? "work-outcome-unknown" : "work-not-invoked";
        assert.deepEqual(precise, [own(`relational-${workload}`, boundary, condition, effect, disposition), ...(hasSource ? sources : [])], `${workload}:${at} exact task location/source9`);
      } else assert.deepEqual(precise, []);
      if (workload === "worker") {
        if (["success", "claim-return", "claim-throw", "claim-disposition", "missing-lease", "complete-return", "complete-throw", "complete-disposition", "acknowledge"].includes(at)) assert.equal(payloadReads, 1);
        assert.deepEqual(calls, at === "success" || at === "acknowledge" ? ["pool", "receive", "claim", "complete", "acknowledge", "end"]
          : at.startsWith("complete") ? ["pool", "receive", "claim", "complete", "end"]
          : at.startsWith("claim") || at === "missing-lease" ? ["pool", "receive", "claim", "end"] : ["pool", "receive", "end"], `${at}: exact task call count/order`);
        assert.equal(calls.includes("acknowledge"), at === "success" || at === "acknowledge");
        for (const operation of ["claim", "complete"]) {
          const records = observed(output).filter((value) => value.fields.capability === "persistence" && value.fields.operation === operation);
          assert.deepEqual(records.map((value) => value.fields.diagnostic), calls.includes(operation) ? sources : []);
          assert(records.every((value) => value.fields.stage === "runtime" && value.correlationId === undefined));
        }
      } else {
        assert.deepEqual(calls, at === "identifier" ? ["pool", "end"] : at === "owner" || at.startsWith("acceptance") ? ["pool", "acceptance", "end"] : ["pool", "acceptance", "run-once", "end"], `${at}: exact task call count/order`);
        assert.deepEqual(observed(output).filter((value) => value.fields.capability === "persistence" && value.fields.operation === "acceptance").map((value) => value.fields.diagnostic), at === "identifier" ? [] : sources);
      }
      assert(!JSON.stringify(output).includes(canary));
    } finally { if (cached === undefined) delete require.cache[path]; else require.cache[path] = cached; patches.restore(); }
  }
}
