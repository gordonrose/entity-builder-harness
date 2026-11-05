#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.script.build-platform-shell-image.verify-runtime-payload
//   version: 7
//   status: active
//   created_on: "2026-09-06"
//   updated_on: "2026-10-30"
//   layer: 04.deploy
//   domain: infra.ci-cd
//   disciplines:
//   - agentic
//   - sre
//   kind: script
//   purpose: Prove the compiled platform shell payload starts with its generated package shims rather than workspace TypeScript sources.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - writes-files
//   used_by:
//   - id: package.script.platform-server-image-runtime-check
//     path: package.json

import { deepEqual } from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, renameSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { verifyTargetConfigurationDiagnostics } from "./configuration-diagnostic-test.mjs";
import { verifyTargetProcessDiagnostics, verifyEcsProcessDiagnostics } from "./process-diagnostic-test.mjs";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const runtimeRoot = join(repositoryRoot, ".cache", "platform-shell-image-build");
const serverEntrypoint = join(runtimeRoot, "infra", "04.deploy", "03.product", "entrypoints", "kanbien-platform-server.main.js");
const workerEntrypoint = join(runtimeRoot, "infra", "04.deploy", "03.product", "entrypoints", "kanbien-platform-worker.main.js");
const relayEntrypoint = join(runtimeRoot, "infra", "04.deploy", "03.product", "entrypoints", "kanbien-platform-relay.main.js");
const persistenceCompositionEntrypoint = join(runtimeRoot, "infra", "04.deploy", "03.product", "entrypoints", "kanbien-platform-persistence.js");
const relationalBootstrapEntrypoint = join(runtimeRoot, "infra", "04.deploy", "03.product", "entrypoints", "kanbien-platform-postgresql-bootstrap.main.js");
const relationalRestoreVerificationEntrypoint = join(runtimeRoot, "infra", "04.deploy", "03.product", "entrypoints", "kanbien-platform-postgresql-restore-verify.main.js");
const workspacePackageScope = join(repositoryRoot, "node_modules", "@kanbien");

const requiredPayloadFiles = [
  serverEntrypoint,
  workerEntrypoint,
  relayEntrypoint,
  persistenceCompositionEntrypoint,
  relationalBootstrapEntrypoint,
  relationalRestoreVerificationEntrypoint,
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-auth-cognito", "index.js"),
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-observability-cloudwatch", "index.js"),
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-persistence-dynamodb", "index.js"),
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-persistence-postgresql", "index.js"),
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-queue-sqs", "index.js"),
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-runtime-ecs-fargate", "index.js"),
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-security-dynamodb-rate-limiter", "index.js"),
];

for (const filePath of requiredPayloadFiles) {
  if (!existsSync(filePath)) {
    throw new Error(`Platform shell runtime payload is incomplete: ${filePath}`);
  }
}

if (!existsSync(workspacePackageScope)) {
  throw new Error("Expected local workspace package links are unavailable for runtime-payload isolation.");
}

// Keep the reversible isolation rename on the package scope filesystem.
// A system temporary directory can live on another mount (EXDEV).
const hiddenWorkspaceRoot = mkdtempSync(join(repositoryRoot, "node_modules", ".platform-shell-runtime-payload-"));
const hiddenWorkspaceScope = join(hiddenWorkspaceRoot, "@kanbien");
let workspaceHidden = false;
try {
  renameSync(workspacePackageScope, hiddenWorkspaceScope);
  workspaceHidden = true;
  verifySecurityConfigurationRetention();
  verifyObservabilityConfigurationRetention();
  await verifyTargetConfigurationDiagnostics(runtimeRoot, repositoryRoot);
  await verifyTargetProcessDiagnostics(runtimeRoot);
  await verifyEcsProcessDiagnostics(runtimeRoot);
  await verifyCompiledPersistenceComposition();
  verifyCompiledRelationalBootstrap();
  verifyCompiledRelationalRestoreVerification();

  const serverResult = spawnSync(process.execPath, [serverEntrypoint], {
    cwd: repositoryRoot,
    env: {
      ...process.env,
      HOST: "127.0.0.1",
      PORT: "39455",
      PLATFORM_SERVER_EXIT_AFTER_START: "1",
      PLATFORM_DEPLOYMENT_EXPOSURE: "public",
      PLATFORM_AUTH_PROVIDER: "cognito",
      PLATFORM_AUTH_COGNITO_REGION: "eu-west-1",
      PLATFORM_AUTH_COGNITO_USER_POOL_ID: "eu-west-1_EQaXioA1n",
      PLATFORM_AUTH_COGNITO_APP_CLIENT_ID: "4n7kuqstbvb97ur3btbur8afjt",
      PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS: '["15po9eg4hgknb2pi2d1bdfhdds"]',
      PLATFORM_AUTHZ_SCOPE_PERMISSIONS: '{"platform-shell/smoke.read":["platform-smoke.smoke:read"],"platform-shell/smoke.write":["platform-smoke.persistence.work-item:create"]}',
      PLATFORM_CORS_ORIGIN: "", // Own the omission predicate instead of inheriting the developer shell's value.
      PLATFORM_CORS_ALLOWLIST: "https://staging.platform.kanbien.com",
      PLATFORM_HEALTH_LIVEZ_EXPOSURE: "public",
      PLATFORM_HEALTH_READYZ_EXPOSURE: "synthetic-private-health-setting",
      PLATFORM_RATE_LIMIT_PROVIDER: "dynamodb",
      PLATFORM_RATE_LIMIT_DYNAMODB_TABLE: "kanbien-staging-platform-shell-rate-limits",
      PLATFORM_RATE_LIMIT_DYNAMODB_REGION: "eu-west-1",
      PLATFORM_RATE_LIMIT_LIMIT: "120",
      PLATFORM_RATE_LIMIT_WINDOW_MS: "60000",
      PLATFORM_PERSISTENCE_PROVIDER: "dynamodb",
      PLATFORM_PERSISTENCE_DYNAMODB_TABLE: "kanbien-staging-platform-shell-persistence",
      PLATFORM_PERSISTENCE_DYNAMODB_REGION: "eu-west-1",
      PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX: "OutboxDueIndex",
      PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX: "LineageCauseIndex",
      PLATFORM_TRUSTED_INGRESS_MODE: "alb-security-group-only",
      PLATFORM_SERVER_MAX_REQUEST_BODY_BYTES: "1048576",
      PLATFORM_SERVER_MAX_HEADER_BYTES: "16384",
      PLATFORM_SERVER_MAX_HEADERS_COUNT: "100",
      PLATFORM_SERVER_HEADERS_TIMEOUT_MS: "10000",
      PLATFORM_SERVER_REQUEST_TIMEOUT_MS: "30000",
      PLATFORM_SERVER_KEEP_ALIVE_TIMEOUT_MS: "5000",
      PLATFORM_SERVER_HANDLER_TIMEOUT_MS: "30000",
      PLATFORM_SERVER_SHUTDOWN_DRAIN_TIMEOUT_MS: "30000",
      PLATFORM_SERVER_MAX_CONCURRENT_REQUESTS: "100",
      PLATFORM_SERVER_MAX_REQUESTS_PER_SOCKET: "1000",
      PLATFORM_SMOKE_APP_NAME: "Kanbien Platform Smoke",
      PLATFORM_SOURCE_COMMIT_SHA: "runtime-payload-test",
      PLATFORM_OBSERVABILITY_METRICS_PROVIDER: "cloudwatch-otel",
      PLATFORM_OBSERVABILITY_METRICS_ENDPOINT: "http://127.0.0.1:4318/v1/metrics",
      PLATFORM_OBSERVABILITY_METRICS_REGION: "eu-west-1",
      PLATFORM_OBSERVABILITY_SERVICE_NAME: "kanbien-staging-platform-shell",
      PLATFORM_OBSERVABILITY_DEPLOYMENT_ENVIRONMENT: "staging",
      PLATFORM_OBSERVABILITY_EXPORT_INTERVAL_MS: "60000",
      PLATFORM_OBSERVABILITY_EXPORT_TIMEOUT_MS: "10000",
      PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON: JSON.stringify([
        {
          sourceName: "platform.server.request.outcome",
          sourceKind: "counter",
          sourceUnit: "count",
          instrumentName: "kanbien.platform.server.request.outcome",
          description: "Compiled runtime payload counter fixture.",
          allowedLabelNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
          cardinalityLimit: 32,
        },
        {
          sourceName: "platform.server.request_response_latency",
          sourceKind: "timer",
          sourceUnit: "ms",
          instrumentName: "kanbien.platform.server.request.duration",
          description: "Compiled runtime payload timer fixture.",
          allowedLabelNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
          cardinalityLimit: 32,
          histogramBucketBoundaries: [50, 300, 750],
        },
      ]),
    },
    encoding: "utf8",
  });

  if (serverResult.status !== 0) {
    throw new Error(`Compiled platform shell server runtime failed with exit code ${String(serverResult.status)}.`);
  }
  const serverOutput = serverResult.stdout + serverResult.stderr;
  const startupConfiguration = serverOutput.split("\n").filter((line) => line.startsWith("{")).map((line) => JSON.parse(line))
    .filter((record) => record.message === "platform.diagnostic.observed" && record.fields?.capability === "platform-server"
      && record.fields?.operation === "configure" && record.fields?.stage === "configuration");
  const choiceCodes = new Set(["platform-server.listener-configuration-selected", "platform-server.port-configuration-fallback",
    "platform-server.health-exposure-selected", "platform-server.health-exposure-fallback"]);
  const startupChoices = startupConfiguration.filter((record) => choiceCodes.has(record.fields.diagnostic.code));
  const diagnostic = (code, detail) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
  deepEqual(startupChoices.map((record) => record.fields.diagnostic), [
    diagnostic("platform-server.listener-configuration-selected", { phase: "configuration", setting: "http.host", source: "environment", reason: "provided", effect: "selected" }),
    diagnostic("platform-server.listener-configuration-selected", { phase: "configuration", setting: "http.port", source: "environment", reason: "provided", effect: "selected" }),
    diagnostic("platform-server.health-exposure-selected", { phase: "configuration", setting: "http.health.liveness-exposure", source: "environment", exposure: "public", reason: "provided", effect: "selected" }),
    diagnostic("platform-server.health-exposure-fallback", { phase: "configuration", setting: "http.health.readiness-exposure", source: "authentication-default", exposure: "authenticated", reason: "unsupported", effect: "default-selected" }),
  ], "Compiled shell retains its four exact listener/health choices, including authenticated readiness fallback.");
  deepEqual(startupConfiguration.filter((record) => record.fields.diagnostic.code === "platform-server.configuration-omitted").map((record) => record.fields.diagnostic), [
    diagnostic("platform-server.configuration-omitted", { phase: "configuration", setting: "http.cors-origin", reason: "empty", effect: "omitted" }),
  ], "Only the explicitly empty CORS origin is omitted; the supplied allowlist and release identity remain selected.");
  if (serverOutput.includes("synthetic-private-health-setting")) throw new Error("Compiled shell must not disclose the rejected health setting.");

  const workerResult = spawnSync(process.execPath, [workerEntrypoint], {
    cwd: repositoryRoot,
    env: {
      ...process.env,
      PLATFORM_WORKER_EXIT_AFTER_START: "1",
      PLATFORM_WORKER_QUEUE_PROVIDER: "sqs",
      PLATFORM_WORKER_SQS_QUEUE_URL: "https://sqs.eu-west-1.amazonaws.com/123456789012/kanbien-staging-platform-shell-worker",
      PLATFORM_WORKER_SQS_REGION: "eu-west-1",
      PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: "20",
      PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS: "120",
      PLATFORM_WORKER_POLL_FAILURE_BACKOFF_MS: "1000",
      PLATFORM_PERSISTENCE_PROVIDER: "dynamodb",
      PLATFORM_PERSISTENCE_DYNAMODB_TABLE: "kanbien-staging-platform-shell-persistence",
      PLATFORM_PERSISTENCE_DYNAMODB_REGION: "eu-west-1",
      PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX: "OutboxDueIndex",
      PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX: "LineageCauseIndex",
      PLATFORM_PERSISTENCE_WORKER_LEASE_DURATION_MS: "90000",
      HOSTNAME: "worker-runtime-payload",
      PLATFORM_SMOKE_APP_NAME: "Kanbien Platform Smoke",
      PLATFORM_SOURCE_COMMIT_SHA: "runtime-payload-test",
      PLATFORM_OBSERVABILITY_METRICS_PROVIDER: "cloudwatch-otel",
      PLATFORM_OBSERVABILITY_METRICS_ENDPOINT: "http://127.0.0.1:4318/v1/metrics",
      PLATFORM_OBSERVABILITY_METRICS_REGION: "eu-west-1",
      PLATFORM_OBSERVABILITY_SERVICE_NAME: "kanbien-staging-platform-shell-worker",
      PLATFORM_OBSERVABILITY_DEPLOYMENT_ENVIRONMENT: "staging",
      PLATFORM_OBSERVABILITY_EXPORT_INTERVAL_MS: "60000",
      PLATFORM_OBSERVABILITY_EXPORT_TIMEOUT_MS: "10000",
      PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON: JSON.stringify([
        {
          sourceName: "platform.worker.job.delivery",
          sourceKind: "counter",
          sourceUnit: "count",
          instrumentName: "kanbien.platform.worker.job.delivery",
          description: "Compiled runtime payload worker delivery counter fixture.",
          allowedLabelNames: ["capability", "action", "execution_context", "job_delivery_disposition", "outcome", "error_class"],
          cardinalityLimit: 32,
        },
        {
          sourceName: "platform.worker.job.execution_latency",
          sourceKind: "timer",
          sourceUnit: "ms",
          instrumentName: "kanbien.platform.worker.job.execution.duration",
          description: "Compiled runtime payload worker execution timer fixture.",
          allowedLabelNames: ["capability", "action", "execution_context", "job_delivery_disposition", "outcome", "error_class"],
          cardinalityLimit: 32,
          histogramBucketBoundaries: [50, 300, 750],
        },
      ]),
    },
    stdio: "inherit",
  });

  if (workerResult.status !== 0) {
    throw new Error(`Compiled platform shell worker runtime failed with exit code ${String(workerResult.status)}.`);
  }

  const relayResult = spawnSync(process.execPath, [relayEntrypoint], {
    cwd: repositoryRoot,
    env: {
      ...process.env,
      PLATFORM_RELAY_EXIT_AFTER_START: "1",
      PLATFORM_PERSISTENCE_PROVIDER: "dynamodb",
      PLATFORM_PERSISTENCE_DYNAMODB_TABLE: "kanbien-staging-platform-shell-persistence",
      PLATFORM_PERSISTENCE_DYNAMODB_REGION: "eu-west-1",
      PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX: "OutboxDueIndex",
      PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX: "LineageCauseIndex",
      PLATFORM_RELAY_QUEUE_PROVIDER: "sqs",
      PLATFORM_RELAY_SQS_QUEUE_URL: "https://sqs.eu-west-1.amazonaws.com/123456789012/kanbien-staging-platform-shell-worker",
      PLATFORM_RELAY_SQS_REGION: "eu-west-1",
      PLATFORM_RELAY_LEASE_DURATION_MS: "90000",
      HOSTNAME: "relay-runtime-payload",
    },
    stdio: "inherit",
  });

  if (relayResult.status !== 0) {
    throw new Error(`Compiled platform shell relay runtime failed with exit code ${String(relayResult.status)}.`);
  }
} finally {
  if (workspaceHidden) renameSync(hiddenWorkspaceScope, workspacePackageScope);
  rmSync(hiddenWorkspaceRoot, { force: true, recursive: true });
}

console.log("Platform shell compiled runtime payload check passed.");

async function verifyCompiledPersistenceComposition() {
  const persistenceModule = await import(pathToFileURL(persistenceCompositionEntrypoint).href);
  const smokeModule = await import(pathToFileURL(join(runtimeRoot, "apps", "platform-smoke", "src", "index.js")).href);
  const sharedModule = await import(pathToFileURL(join(runtimeRoot, "packages", "core", "src", "shared", "index.js")).href);
  const commands = [];
  const persistence = persistenceModule.createKanbienPlatformSmokePersistence({
    client: {
      send: async (command) => {
        commands.push(command);
        return {};
      },
    },
    configuration: {
      region: "eu-west-1",
      tableName: "platform-shell-persistence-proof",
      outboxDueIndexName: "due-index",
      lineageCauseIndexName: "cause-index",
    },
  });
  const workItemId = smokeModule.platformSmokeWorkItemId("compiled-persistence-proof");
  if (!workItemId.ok) {
    throw new Error("Compiled persistence proof could not construct a work-item identity.");
  }
  const result = await smokeModule.acceptPlatformSmokeWorkItem({
    id: workItemId.value,
    acceptedAt: sharedModule.isoDateTimeFromDate(new Date("2026-09-24T12:00:00.000Z")),
    causationId: sharedModule.causationId("compiled-persistence-proof"),
  }, persistence);
  if (!result.ok) {
    throw new Error(`Compiled persistence proof failed: ${result.error.code}.`);
  }
  if (commands.length !== 1) {
    throw new Error("Compiled persistence proof must submit exactly one DynamoDB request.");
  }
  const transactItems = commands[0]?.input?.TransactItems;
  if (!Array.isArray(transactItems) || transactItems.length !== 3) {
    throw new Error("Compiled persistence proof must submit work-item, lineage, and outbox writes together.");
  }
  if (
    transactItems[0]?.Put?.Item?.recordType?.S !== "platform-smoke-work-item"
    || transactItems[1]?.Put?.Item?.recordType?.S !== "lineage"
    || transactItems[2]?.Put?.Item?.recordType?.S !== "outbox"
  ) {
    throw new Error("Compiled persistence proof must preserve the reviewed three-write record order.");
  }

  const corePersistence = await import(pathToFileURL(join(runtimeRoot, "packages/core/src/persistence/index.js")).href);
  const sources = Array.from({ length: 9 }, (_, ordinal) => corePersistence.corePersistenceInMemoryBoundaryRecord({
    operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal,
  }));
  const failure = Object.assign(new Error("private-compiled-persistence-canary"), {
    name: "AccessDeniedException", diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1),
  });
  const observed = [], defaults = [];
  let failedCalls = 0;
  const failing = persistenceModule.createKanbienPlatformSmokePersistence({
    client: { async send() { failedCalls++; throw failure; } },
    configuration: { region: "eu-west-1", tableName: "platform-shell-persistence-proof", outboxDueIndexName: "due-index", lineageCauseIndexName: "cause-index" },
    onDiagnostic(record) { defaults.push(record); },
  });
  const input = { id: workItemId.value, acceptedAt: sharedModule.isoDateTimeFromDate(new Date("2026-09-24T12:00:00.000Z")),
    causationId: sharedModule.causationId("compiled-persistence-proof") };
  const failed = await smokeModule.acceptPlatformSmokeWorkItem(input, failing, { onDiagnostic(record) { observed.push(record); } });
  if (failed.ok || failed.error.code !== "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED") throw new Error("Compiled adapter failure changed the existing feature result.");
  deepEqual(observed.filter((record) => record.code.startsWith("core.")), sources);
  deepEqual(observed.filter((record) => !record.code.startsWith("core.")), [{ schema: "core/diagnostic-record/v1",
    code: "persistence.runtime-permission-denied", definitionVersion: 4,
    detail: { operation: "write_atomic", boundary: "invocation", role: "primary", condition: "access-rejected", codeStatus: "recognized", effect: "unknown" } }]);
  deepEqual(defaults, [], "Invocation observer replaces, rather than duplicates, default delivery");
  await smokeModule.acceptPlatformSmokeWorkItem(input, failing, {});
  deepEqual(defaults, [], "Explicit opt-out does not fall back to the default observer");
  if (failedCalls !== 2 || JSON.stringify(observed).includes("canary")) throw new Error("Compiled diagnostics retried work or exposed a private value.");
  await verifyCompiledStoreObserverBridges(persistenceModule, sources, failure);
}

async function verifyCompiledStoreObserverBridges(target, sources, failure) {
  const persistence = await import(pathToFileURL(join(runtimeRoot, "platform/persistence/src/index.js")).href);
  const monitoring = await import(pathToFileURL(join(runtimeRoot, "packages/core/src/monitoring/index.js")).href);
  const product = await import(pathToFileURL(join(runtimeRoot, "products/kanbien-platform/src/index.js")).href);
  const owner = persistence.platformPersistenceLeaseOwner("compiled-observer-proof");
  if (!owner.ok) throw new Error("Compiled observer owner fixture invalid.");
  const clock = { now: () => new Date("2026-09-24T12:00:00.000Z") };
  const configuration = { region: "eu-west-1", tableName: "private-bridge-table-canary", outboxDueIndexName: "due-index", lineageCauseIndexName: "cause-index" };
  for (const enabled of [true, false]) {
    const logs = [], attempts = [];
    const profile = product.kanbienPlatformSmokeWorkItemDeliveryObservabilityProfile;
    const selected = persistence.createPlatformPersistenceTransitionObserver({
      profile: enabled ? profile : { name: profile.name, capability: profile.capability, action: profile.action,
        signals: ["metric"], metricDimensionFieldNames: profile.metricDimensionFieldNames },
      executionContext: "worker", metrics: monitoring.noopMetrics, clock,
      logger: { write(log) { logs.push(log); } },
    });
    if (!selected.ok) throw new Error("Compiled observer profile fixture invalid.");
    const observer = { record(observation) { selected.value.record(observation); }, onDiagnostic(record) {
      if (this !== observer) throw new Error("Observer bridge lost its receiver.");
      attempts.push(record); selected.value.onDiagnostic(record);
    } };
    let sends = 0, queueSends = 0;
    const client = { async send() { sends++; throw failure; } };
    const relay = target.createKanbienPlatformOutboxRelay({ client, configuration, observer, owner: owner.value,
      leaseDurationMs: 1_000, clock, queue: { async send() { queueSends++; throw new Error("Unexpected queue send"); } } });
    const relayed = await relay.runOnce();
    if (relayed.ok) throw new Error("Failed store read unexpectedly relayed work.");
    const worker = target.createKanbienPlatformDurableWorkerProcessing({ client, configuration, observer, owner: owner.value, leaseDurationMs: 1_000 });
    try { await worker.processingStore.get("private-processing-id-canary"); throw new Error("Failed get unexpectedly succeeded"); }
    catch (cause) { if (cause !== failure) throw cause; }
    if (sends !== 2 || queueSends !== 0) throw new Error("Store diagnostics changed send/retry behavior.");
    const expected = ["list_outbox", "read_processing"].flatMap((operation) => [{ schema: "core/diagnostic-record/v1",
      code: "persistence.runtime-permission-denied", definitionVersion: 4,
      detail: { operation, boundary: "invocation", role: "primary", condition: "access-rejected", codeStatus: "recognized", effect: "not-assessed" } }, ...sources]);
    deepEqual(attempts, expected, "Both real target store bridges preserve own plus source9 and observer receiver");
    const delivered = logs.filter((log) => log.message === "platform.diagnostic.observed" && log.fields.operation === "store-observation");
    deepEqual(delivered.map((log) => log.fields.diagnostic), enabled ? expected : [], "Actual selected reporter honors profile opt-out");
    if (delivered.some((log) => log.fields.stage !== "runtime" || log.correlationId !== undefined)
      || JSON.stringify(logs).includes("canary")) throw new Error("Background store evidence invented request context or exposed private values.");
  }
}

function verifyCompiledRelationalBootstrap() {
  const fixtureSecret = JSON.stringify({ username: "fixture-user", password: "fixture-password", host: "127.0.0.1", port: 1 });
  const result = spawnSync(process.execPath, [relationalBootstrapEntrypoint], {
    cwd: repositoryRoot,
    env: {
      ...process.env,
      RELATIONAL_MASTER_SECRET_JSON: fixtureSecret,
      RELATIONAL_MIGRATION_SECRET_JSON: fixtureSecret,
      RELATIONAL_RUNTIME_SECRET_JSON: fixtureSecret,
    },
    encoding: "utf8",
  });
  const expected = JSON.stringify({ level: "error", message: "kanbien-platform.relational-smoke.bootstrap_completed", fields: { outcome: "failed", failure_category: "bootstrap-certificate-authority-unavailable" } });
  if (result.status !== 1 || result.stdout.trim() !== expected) {
    throw new Error("Compiled relational bootstrap payload must load its PostgreSQL adapter and emit only the reviewed safe failure event.");
  }
}

function verifyCompiledRelationalRestoreVerification() {
  const result = spawnSync(process.execPath, [relationalRestoreVerificationEntrypoint], {
    cwd: repositoryRoot,
    env: { ...process.env },
    encoding: "utf8",
  });
  const expected = JSON.stringify({
    level: "error",
    message: "kanbien-platform.relational-smoke.restore_verified",
    fields: {
      outcome: "failed",
      failure_phase: "input-validation",
      failure_category: "restore-input-validation-failure",
      expected: { migration_checksums: "two", accepted_work_item: "one", published_outbox: "one", completed_processing: "one" },
      observed: { migration_checksums: "not-queried", accepted_work_item: "not-queried", published_outbox: "not-queried", completed_processing: "not-queried" },
    },
  });
  if (result.status !== 1 || result.stdout.trim() !== expected) {
    throw new Error("Compiled relational restore verification payload must load and retain its reviewed safe failure outcome.");
  }
}

function verifySecurityConfigurationRetention() {
  for (const [env, reference, publicCode] of [
    [{ PLATFORM_AUTH_PROVIDER: "cognito", PLATFORM_AUTH_COGNITO_REGION: "" }, "region", "PLATFORM_ADAPTER_AWS_COGNITO_CONFIG_INVALID"],
    [{ PLATFORM_AUTH_PROVIDER: "none", PLATFORM_DEPLOYMENT_EXPOSURE: "private", PLATFORM_RATE_LIMIT_PROVIDER: "dynamodb", PLATFORM_RATE_LIMIT_DYNAMODB_TABLE: "", PLATFORM_RATE_LIMIT_DYNAMODB_REGION: "synthetic-private-canary", PLATFORM_RATE_LIMIT_LIMIT: "1", PLATFORM_RATE_LIMIT_WINDOW_MS: "1000" }, "table", "KANBIEN_PLATFORM_TARGET_RUNTIME_CONFIG_INVALID"],
  ]) {
    const result = spawnSync(process.execPath, [serverEntrypoint], { cwd: repositoryRoot, env: { ...process.env, ...env }, encoding: "utf8" });
    const output = result.stdout + result.stderr;
    const entries = output.trim().split("\n").filter(Boolean).map((line) => JSON.parse(line));
    const diagnostic = entries.find((entry) => entry.message === "platform.diagnostic.observed")?.fields?.diagnostic;
    const legacy = entries.find((entry) => entry.error?.code === publicCode);
    if (result.status !== 1 || !legacy || diagnostic?.code !== "security.adapter-configuration.empty"
      || JSON.stringify(diagnostic.detail) !== JSON.stringify({ phase: "adapter-configuration", reason: "empty", effect: "not-assessed", reference })
      || output.includes("synthetic-private-canary")) throw new Error("Compiled target must preserve the exact safe adapter configuration observation without changing the original startup code or disclosing configuration values.");
  }
}

function verifyObservabilityConfigurationRetention() {
  for (const entrypoint of [serverEntrypoint, workerEntrypoint]) {
    const result = spawnSync(process.execPath, [entrypoint], { cwd: repositoryRoot, encoding: "utf8", env: {
      ...process.env, PLATFORM_AUTH_PROVIDER: "none", PLATFORM_DEPLOYMENT_EXPOSURE: "private",
      PLATFORM_RATE_LIMIT_PROVIDER: "", PLATFORM_OBSERVABILITY_METRICS_PROVIDER: "cloudwatch-otel",
      PLATFORM_OBSERVABILITY_METRICS_ENDPOINT: "https://synthetic-private-canary:4318/v1/metrics",
      PLATFORM_OBSERVABILITY_METRICS_REGION: "eu-west-1", PLATFORM_OBSERVABILITY_SERVICE_NAME: "fixture-service",
      PLATFORM_SOURCE_COMMIT_SHA: "fixture-version", PLATFORM_OBSERVABILITY_DEPLOYMENT_ENVIRONMENT: "fixture",
      PLATFORM_OBSERVABILITY_EXPORT_INTERVAL_MS: "1000", PLATFORM_OBSERVABILITY_EXPORT_TIMEOUT_MS: "1001",
      PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON: "[]",
    } });
    const output = result.stdout + result.stderr;
    const entries = output.trim().split("\n").filter(Boolean).map((line) => JSON.parse(line));
    const record = entries.find((entry) => entry.message === "platform.diagnostic.observed")?.fields?.diagnostic;
    const legacy = entries.find((entry) => entry.error?.code === "KANBIEN_PLATFORM_TARGET_OBSERVABILITY_CONFIG_INVALID");
    if (result.status !== 1 || !legacy || record?.code !== "observability.configuration-invalid"
      || record.detail.effect !== "not-started" || record.detail.truncated !== false
      || !record.detail.issues.some((issue) => issue.setting === "metrics.endpoint" && issue.reason === "protocol-not-allowed")
      || !record.detail.issues.some((issue) => issue.setting === "metrics.export-timeout" && issue.reason === "timeout-exceeds-interval")
      || !record.detail.issues.some((issue) => issue.setting === "metrics.series" && issue.reason === "empty")
      || output.includes("synthetic-private-canary")) throw new Error("Compiled server and worker must retain safe, granular telemetry diagnostics and the existing startup code before starting work.");
  }
}
