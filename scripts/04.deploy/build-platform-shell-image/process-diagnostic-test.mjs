// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.script.build-platform-shell-image.process-diagnostic-test
//   version: 2
//   status: active
//   created_on: "2026-10-30"
//   updated_on: "2026-11-05"
//   layer: 04.deploy
//   domain: diagnostics
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove compiled ECS selection and actual process-owned startup delivery without provider operations.
//   portability: { class: source-only, targets: [] }
//   effects: [writes-files]
//   used_by:
//   - id: deploy.script.build-platform-shell-image.verify-runtime-payload
//     path: scripts/04.deploy/build-platform-shell-image/verify-runtime-payload.mjs
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join } from "node:path";
import { verifyTargetDeliveryDiagnostics } from "./delivery-diagnostic-test.mjs";

const canary = "synthetic-private-process-canary";
const record = (code, detail) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
const selectedState = record("platform-runtime.state-rejected", { operation: "start", state: "failed", effect: "state-unchanged" });
const failedStep = record("platform-runtime.boundary-failed", { operation: "start", phase: "app.beforeStart", subject: "app", boundary: "invocation", effect: "step-completion-unobserved", ordinal: 0 });
function capture() {
  const output = [], originalLog = console.log, originalError = console.error;
  console.log = console.error = (line) => output.push(JSON.parse(line));
  return { output, restore() { console.log = originalLog; console.error = originalError; } };
}
function environment(values) {
  for (const key of Object.keys(process.env)) if (key.startsWith("PLATFORM_") || key.startsWith("PERSISTENCE_") || key === "ECS_CONTAINER_METADATA_URI_V4") delete process.env[key];
  Object.assign(process.env, values);
}
function diagnostics(output) { return output.filter((entry) => entry.message === "platform.diagnostic.observed").map((entry) => entry.fields.diagnostic); }

/** The wrapper injects a failing app into the real process, never a fake Result. */
export async function verifyTargetProcessDiagnostics(runtimeRoot) {
  const require = createRequire(join(runtimeRoot, "process-diagnostic-test.cjs"));
  const load = (file) => require(join(runtimeRoot, file));
  const serverProcess = load("platform/server/src/main.js"), workerProcess = load("platform/workers/src/main.js");
  const telemetry = load("infra/04.deploy/03.product/entrypoints/kanbien-platform-observability.js");
  const metrics = load("packages/core/src/monitoring/index.js").noopMetrics;
  const originalServer = serverProcess.startPlatformServerProcess, originalWorker = workerProcess.startPlatformWorkerProcess;
  const originalTelemetry = telemetry.observabilityFromTargetEnvironment;
  const savedEnv = { ...process.env }, savedExit = process.exitCode;
  let starts = 0, shutdowns = 0;
  const app = { id: "startup-fixture", name: "Startup fixture", mount() {}, lifecycle: { beforeStart() { starts++; throw Object.assign(new Error(canary), { diagnosticRecord: selectedState }); } } };
  serverProcess.startPlatformServerProcess = (options) => originalServer({ ...options, installSignalHandlers: false, apps: [app, ...options.apps] });
  workerProcess.startPlatformWorkerProcess = (options) => originalWorker({ ...options, installSignalHandlers: false, apps: [app, ...options.apps] });
  telemetry.observabilityFromTargetEnvironment = () => ({ ok: true, value: { metrics, shutdown: async () => { shutdowns++; } } });
  const cases = [
    ["kanbien-platform-server", "runKanbienPlatformServerMain", "kanbien-platform.server.start_failed", "PLATFORM_SERVER_START_FAILED", {}],
    ["kanbien-platform-worker", "runKanbienPlatformWorkerMain", "kanbien-platform.worker.start_failed", "PLATFORM_WORKER_NOT_READY", { PLATFORM_WORKER_QUEUE_PROVIDER: "sqs", PLATFORM_WORKER_SQS_QUEUE_URL: "https://queue.invalid/fixture", PLATFORM_WORKER_SQS_REGION: "fixture", PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: "0", PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS: "120", PLATFORM_WORKER_POLL_FAILURE_BACKOFF_MS: "1" }],
    ["kanbien-core-server", "runKanbienCoreServerMain", "kanbien-core-server.start_failed", "PLATFORM_SERVER_START_FAILED", {}],
  ];
  try {
    for (const [file, method, summary, code, values] of cases) {
      environment({ PLATFORM_AUTH_PROVIDER: "none", PLATFORM_DEPLOYMENT_EXPOSURE: "private", PLATFORM_SMOKE_APP_NAME: "fixture", ...values });
      const sink = capture(), beforeStarts = starts, beforeShutdowns = shutdowns;
      try {
        await load(`infra/04.deploy/03.product/entrypoints/${file}.main.js`)[method]();
        assert.equal(process.exitCode, 1);
        assert.equal(starts, beforeStarts + 1, "real startup invokes its original lifecycle once");
        const observed = diagnostics(sink.output);
        assert.deepEqual(observed.filter((value) => value.code === failedStep.code), [failedStep]);
        assert.deepEqual(observed.filter((value) => value.code === selectedState.code), [selectedState], "selected upstream evidence is delivered once by the inner producer");
        assert.equal(observed.filter((value) => value.code === (file.includes("worker") ? "platform-worker.delivery-failed" : "platform-server.operation-failed")).length, 0, "retaining already-delivered upstream evidence does not manufacture another failure record");
        assert.deepEqual(sink.output.find((value) => value.message === summary)?.error, { code, message: file.includes("worker") ? "Platform worker lifecycle failed to start." : "Platform server lifecycle failed to start." });
        assert.equal(shutdowns - beforeShutdowns, file === "kanbien-core-server" ? 0 : 1, "target cleanup remains once, after failed startup");
        assert(!JSON.stringify(sink.output).includes(canary));
      } finally { sink.restore(); }
    }
    await verifyCorePersistenceStartup(load);
    await verifyEcsConstructorTarget(load);
    await verifyDynamoConstructorTargets(load);
    await verifyTargetDeliveryDiagnostics(runtimeRoot);
  } finally {
    serverProcess.startPlatformServerProcess = originalServer; workerProcess.startPlatformWorkerProcess = originalWorker;
    telemetry.observabilityFromTargetEnvironment = originalTelemetry;
    for (const key of Object.keys(process.env)) delete process.env[key]; Object.assign(process.env, savedEnv); process.exitCode = savedExit;
  }
}

async function verifyDynamoConstructorTargets(load) {
  const client = load("platform/adapters/aws/persistence/dynamodb/src/client.js");
  const original = client.createAwsSdkDynamoDbPersistenceCommandClient;
  const core = load("packages/core/src/persistence/index.js");
  const sources = Array.from({ length: 9 }, (_, ordinal) => core.corePersistenceInMemoryBoundaryRecord({
    operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal,
  }));
  const cause = Object.freeze(Object.assign(new Error(canary), { diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) }));
  let calls = 0;
  client.createAwsSdkDynamoDbPersistenceCommandClient = (configuration, diagnostics) => {
    calls++;
    // Exercise the actual adapter's construction guard and actual target callback,
    // without replacing its Result, logging directly, or invoking the provider.
    return original(Object.defineProperty({ ...configuration }, "region", { get() { throw cause; } }), diagnostics);
  };
  const base = { PLATFORM_AUTH_PROVIDER: "none", PLATFORM_DEPLOYMENT_EXPOSURE: "private", PLATFORM_SMOKE_APP_NAME: "fixture",
    PLATFORM_PERSISTENCE_PROVIDER: "dynamodb", PLATFORM_PERSISTENCE_DYNAMODB_REGION: "eu-west-1",
    PLATFORM_PERSISTENCE_DYNAMODB_TABLE: "private-dynamodb-target-canary", PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX: "due-index",
    PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX: "cause-index", HOSTNAME: "fixture", PLATFORM_PERSISTENCE_WORKER_LEASE_DURATION_MS: "1000" };
  try {
    for (const [file, method, env] of [
      ["server", "runKanbienPlatformServerMain", {}],
      ["worker", "runKanbienPlatformWorkerMain", { PLATFORM_WORKER_QUEUE_PROVIDER: "sqs", PLATFORM_WORKER_SQS_QUEUE_URL: "https://queue.invalid/fixture",
        PLATFORM_WORKER_SQS_REGION: "eu-west-1", PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: "0", PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS: "120", PLATFORM_WORKER_POLL_FAILURE_BACKOFF_MS: "1" }],
      ["relay", "runKanbienPlatformRelayMain", { PLATFORM_RELAY_QUEUE_PROVIDER: "sqs", PLATFORM_RELAY_SQS_QUEUE_URL: "https://queue.invalid/fixture",
        PLATFORM_RELAY_SQS_REGION: "eu-west-1", PLATFORM_RELAY_LEASE_DURATION_MS: "1000" }],
    ]) {
      environment({ ...base, ...env });
      const sink = capture(), before = calls;
      try {
        await assert.rejects(load(`infra/04.deploy/03.product/entrypoints/kanbien-platform-${file}.main.js`)[method](), (error) => error === cause);
        assert.equal(calls, before + 1);
        assert.deepEqual(diagnostics(sink.output), [{ schema: "core/diagnostic-record/v1", code: "persistence.unclassified-failure", definitionVersion: 4,
          detail: { operation: "client-initialization", boundary: "client-construction", role: "primary", condition: "unclassified", codeStatus: "not-inspected", effect: "not-invoked" } }, ...sources]);
        for (const log of sink.output.filter((entry) => entry.message === "platform.diagnostic.observed")) {
          assert.equal(log.fields.capability, "persistence"); assert.equal(log.fields.operation, "client-initialization");
          assert.equal(log.fields.stage, "startup"); assert.equal(log.correlationId, undefined);
        }
        assert(!JSON.stringify(sink.output).includes(canary));
      } finally { sink.restore(); }
    }
  } finally { client.createAwsSdkDynamoDbPersistenceCommandClient = original; }
}

async function verifyCorePersistenceStartup(load) {
  const connection = load("platform/adapters/aws/persistence/postgresql/src/connection.js");
  const composition = load("infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-composition.js");
  const config = load("infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.js");
  const telemetry = load("infra/04.deploy/03.product/entrypoints/kanbien-platform-observability.js");
  const originalPool = connection.createNodePostgreSqlTokenConnectionPool, originalAuthority = config.persistenceCertificateAuthorityResult;
  const originalConfiguration = telemetry.observabilityConfigurationFromTargetEnvironment;
  const originalSelection = composition.selectPersistenceImplementation;
  // The real selector retains a frozen factory; inject at its selected boundary.
  composition.selectPersistenceImplementation = (value) => {
    const selected = originalSelection(value);
    return selected.ok ? { ...selected, value: { ...selected.value,
      createPool: (...args) => connection.createNodePostgreSqlTokenConnectionPool(...args),
    } } : selected;
  };
  let pools = 0, closes = 0, queries = 0;
  connection.createNodePostgreSqlTokenConnectionPool = () => { pools++; return { query: async () => { queries++; throw new Error(canary); }, connect: async () => { throw new Error(canary); }, end: async () => { closes++; } }; };
  config.persistenceCertificateAuthorityResult = () => ({ ok: true, value: "fixture-certificate" });
  telemetry.observabilityConfigurationFromTargetEnvironment = () => ({ ok: true, value: { options: undefined } });
  const sink = capture();
  try {
    const env = {
      NODE_ENV: "test", HOST: "127.0.0.1", PORT: "0", PLATFORM_SOURCE_COMMIT_SHA: "a".repeat(40),
      PERSISTENCE_POSTGRES_HOST: "postgres", PERSISTENCE_POSTGRES_PORT: "5432", PERSISTENCE_POSTGRES_DATABASE: "kanbienpersistence", PERSISTENCE_POSTGRES_SCHEMA: "platform",
      PERSISTENCE_POSTGRES_IAM_REGION: "eu-west-1", PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: "arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-ABCDEFGHIJKLMNOP/core_runtime",
      PERSISTENCE_RUNTIME_DATABASE_USERNAME: "core_runtime", PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN: "synthetic-test-token", PERSISTENCE_POSTGRES_CA_PATH: "/app/assets/fixture.crt",
    };
    const run = load("infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.js").runKanbienCoreServerPersistenceMain;
    await run(env);
    assert.equal(process.exitCode, 1); assert.equal(pools, 1); assert.equal(closes, 1); assert.equal(queries, 0, "startup failure never invokes SQL or provider operations");
    const observed = diagnostics(sink.output);
    assert.deepEqual(observed.filter((value) => value.code === failedStep.code), [failedStep]);
    assert.deepEqual(observed.filter((value) => value.code === selectedState.code), [selectedState]);
    assert.equal(observed.filter((value) => value.code === "platform-server.operation-failed").length, 0);
    const summary = sink.output.find((value) => value.message === "kanbien-core-server-persistence.start_failed");
    assert(summary, "original persistence task summary remains after cleanup");
    assert(!JSON.stringify(sink.output).includes(canary));
    const core = load("packages/core/src/persistence/index.js");
    const sources = Array.from({ length: 9 }, (_, ordinal) => core.corePersistenceInMemoryBoundaryRecord({
      operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal,
    }));
    const cause = Object.assign(new Error(canary), { diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) });
    const boundary = (name) => record("persistence.boundary-observed", {
      operation: "connection-pool", phase: name === "idle-pool" ? "event" : "invocation",
      boundary: name, condition: "rejected", effect: "not-assessed",
    });
    for (const endFails of [false, true]) {
      sink.output.length = 0;
      const beforePools = pools, beforeCloses = closes, beforeQueries = queries;
      connection.createNodePostgreSqlTokenConnectionPool = (_configuration, _credentials, options) => {
        pools++;
        let idleError;
        const native = {
          on(event, listener) { assert.equal(event, "error"); idleError = listener; },
          async query() { queries++; throw cause; },
          async connect() { throw new Error("Unexpected connection acquisition"); },
          async end() { closes++; if (endFails) throw cause; },
        };
        const adapted = connection.nodePoolAdapter(native, options);
        idleError(cause);
        return adapted;
      };
      if (endFails) await assert.rejects(run(env), (error) => error === cause, "cleanup preserves the original rejection identity");
      else await run(env);
      assert.equal(pools - beforePools, 1); assert.equal(closes - beforeCloses, 1); assert.equal(queries - beforeQueries, 0);
      const resource = sink.output.filter((entry) => entry.message === "platform.diagnostic.observed" && entry.fields.operation === "connection-resource");
      assert.deepEqual(resource.map((entry) => entry.fields.diagnostic), [boundary("idle-pool"), ...sources,
        ...(endFails ? [boundary("end"), ...sources] : [])], "actual target wiring delivers own boundary plus all nine selected source records");
      for (const entry of resource) {
        assert.equal(entry.fields.capability, "persistence"); assert.equal(entry.fields.stage, "runtime");
        assert.equal(entry.correlationId, undefined, "process observations do not invent request identity");
      }
      assert(!JSON.stringify(sink.output).includes(canary));
    }
    sink.output.length = 0;
    const primary = { schema: "core/diagnostic-record/v1", code: "persistence.credential-rejected", definitionVersion: 2,
      detail: { phase: "unknown", classification: "authentication_rejected", codeStatus: "recognized", operation: "migration", effect: "unknown" } };
    const migrationCause = Object.assign(new Error(canary), { code: "28P01", diagnosticRecord: primary, relatedDiagnosticRecords: sources.slice(1) });
    let connects = 0, releases = 0;
    const beforeQueries = queries, beforeCloses = closes;
    connection.createNodePostgreSqlTokenConnectionPool = () => ({
      async query() { throw new Error("Unexpected pool query"); },
      async connect() { connects++; return {
        async query(statement) { queries++; assert.equal(statement.text, "BEGIN"); throw migrationCause; },
        release() { releases++; },
      }; },
      async end() { closes++; },
    });
    await load("infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.js").runKanbienCoreServerPersistenceMigration({
      ...env, PERSISTENCE_MIGRATION_DATABASE_USERNAME: "core_schema_migration",
    });
    assert.equal(connects, 1); assert.equal(releases, 1); assert.equal(queries - beforeQueries, 1); assert.equal(closes - beforeCloses, 1);
    assert.deepEqual(sink.output, [{ verdict: "rejected", code: "PERSISTENCE_MIGRATION_NOT_CONFIRMED", stage: "migration",
      provider_failure_class: "access_denied", diagnostic: primary, related_diagnostics: sources.slice(1) }],
    "actual migration task projection retains its selected primary/eight through runner and task serializer");
    assert(!JSON.stringify(sink.output).includes(canary));
  } finally {
    composition.selectPersistenceImplementation = originalSelection;
    connection.createNodePostgreSqlTokenConnectionPool = originalPool; config.persistenceCertificateAuthorityResult = originalAuthority;
    telemetry.observabilityConfigurationFromTargetEnvironment = originalConfiguration; sink.restore();
  }
}

async function verifyEcsConstructorTarget(load) {
  const ecs = load("platform/adapters/aws/runtime/ecs-fargate/src/index.js"), original = ecs.createAlbTrustedClientAddressResolver;
  let rejection;
  try { original({ ingressMode: canary }); } catch (error) { rejection = error; }
  assert(rejection instanceof RangeError);
  ecs.createAlbTrustedClientAddressResolver = () => { throw rejection; };
  environment({ PLATFORM_AUTH_PROVIDER: "none", PLATFORM_DEPLOYMENT_EXPOSURE: "private", PLATFORM_TRUSTED_INGRESS_MODE: "alb-security-group-only" });
  const sink = capture();
  try {
    await assert.rejects(load("infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.js").runKanbienPlatformServerMain(), (error) => error === rejection);
    assert.deepEqual(diagnostics(sink.output), [record("platform-server.client-address-trust-invalid", { phase: "configuration", setting: "http.client-address-trust", reason: "unsupported", effect: "rejected" })]);
    assert(!JSON.stringify(sink.output).includes(canary));
  } finally { ecs.createAlbTrustedClientAddressResolver = original; sink.restore(); }
}

/** Opt-in is an exported process option, deliberately not a new target CLI flag. */
export async function verifyEcsProcessDiagnostics(runtimeRoot) {
  const require = createRequire(join(runtimeRoot, "ecs-process-diagnostic-test.cjs"));
  const load = (file) => require(join(runtimeRoot, file));
  const { startPlatformServerProcess } = load("platform/server/src/main.js");
  const { createAlbTrustedClientAddressResolver } = load("platform/adapters/aws/runtime/ecs-fargate/src/index.js");
  let releaseLate;
  const app = { id: "ecs-fixture", name: "ECS process fixture", mount(registry) {
    registry.registerObservabilityProfile({ name: "ecs-fixture.request", capability: "ecs-fixture.request", action: "execute", signals: ["operational_log"], logFieldNames: ["capability", "action", "execution_context", "outcome", "error_class"] });
    for (const [name, method, path, enabled] of [["public", "GET", "/public", true], ["opt-out", "GET", "/opt-out", false], ["mixed-profile", "GET", "/mixed", true], ["mixed-opt-out", "POST", "/mixed", false], ["slow", "GET", "/slow", true]]) registry.registerRoute({ name: `ecs-fixture.${name}`, method, path, auth: { kind: "public" }, observability: enabled ? { kind: "profile", profile: "ecs-fixture.request" } : { kind: "opt_out", reason: "non_user_workload_path", justification: "Keep ECS selection observations inside the route policy." }, handler: { handle: () => name === "slow" ? new Promise((resolve) => { releaseLate = () => resolve({ status: 200, body: { ok: true } }); }) : ({ status: 200, body: { ok: true } }) } });
  } };
  const fallback = record("platform-server.client-address-fallback-selected", { phase: "client-address-selection", reason: "forwarded-header-missing", source: "socket-peer", effect: "fallback-selected" });
  for (const enabled of [false, true]) {
    const output = []; let resolverCalls = 0, quotaCalls = 0;
    const resolver = createAlbTrustedClientAddressResolver({ ingressMode: "alb-security-group-only" });
    const started = await startPlatformServerProcess({ apps: [app], env: { HOST: "127.0.0.1" }, port: 0, transport: { handlerTimeoutMs: 10 }, installSignalHandlers: false, securityDecisionDiagnostics: enabled, logger: { write(value) { output.push(value); } }, clientAddressResolver: { resolve(input) { resolverCalls++; return resolver.resolve(input); } }, rateLimiter: { check() { quotaCalls++; return { allowed: true }; } } });
    assert.equal(started.ok, true);
    try {
      const url = `http://127.0.0.1:${started.value.handle.port}`;
      for (const [method, path, expected] of [["GET", "/public", 200], ["GET", "/opt-out", 200], ["OPTIONS", "/mixed", 204], ["OPTIONS", "/opt-out", 204]]) {
        const before = diagnostics(output).filter((value) => value.code === fallback.code).length;
        const response = await fetch(url + path, { method }); assert.equal(response.status, expected); await response.text();
        const delivered = diagnostics(output).filter((value) => value.code === fallback.code).slice(before);
        assert.deepEqual(delivered, enabled && path === "/public" ? [fallback] : [], "default quiet and route/preflight opt-outs apply before admission");
      }
      for (const [forwarded, reason] of [[canary, "forwarded-final-address-invalid"], ["203.0.113.3", undefined]]) {
        const before = diagnostics(output).filter((value) => value.code === fallback.code).length;
        const response = await fetch(url + "/public", { headers: { "x-forwarded-for": forwarded } }); assert.equal(response.status, 200);
        const body = await response.text(); assert(!body.includes("diagnostic")); assert(!body.includes(canary));
        assert.deepEqual(diagnostics(output).filter((value) => value.code === fallback.code).slice(before), enabled && reason ? [record(fallback.code, { ...fallback.detail, reason })] : []);
      }
      const beforeDeadline = diagnostics(output).filter((value) => value.code === fallback.code).length;
      const timedOut = await fetch(url + "/slow"); assert.equal(timedOut.status, 504); await timedOut.text();
      assert.equal(typeof releaseLate, "function"); releaseLate(); await new Promise((resolve) => setImmediate(resolve));
      assert.deepEqual(diagnostics(output).filter((value) => value.code === fallback.code).slice(beforeDeadline), enabled ? [fallback] : [], "deadline and late completion do not replay selection observations");
      assert.equal(resolverCalls, 7); assert.equal(quotaCalls, 7, "observation does not add resolver or quota calls");
      assert(!JSON.stringify(output).includes("127.0.0.1"));
      assert(!JSON.stringify(output).includes(canary));
    } finally { releaseLate?.(); await started.value.close(); }
  }
}
