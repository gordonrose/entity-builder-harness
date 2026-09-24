#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.script.build-platform-shell-image.verify-runtime-payload
//   version: 5
//   status: active
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

import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, renameSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const runtimeRoot = join(repositoryRoot, ".cache", "platform-shell-image-build");
const serverEntrypoint = join(runtimeRoot, "infra", "04.deploy", "03.product", "entrypoints", "kanbien-platform-server.main.js");
const workerEntrypoint = join(runtimeRoot, "infra", "04.deploy", "03.product", "entrypoints", "kanbien-platform-worker.main.js");
const relayEntrypoint = join(runtimeRoot, "infra", "04.deploy", "03.product", "entrypoints", "kanbien-platform-relay.main.js");
const persistenceCompositionEntrypoint = join(runtimeRoot, "infra", "04.deploy", "03.product", "entrypoints", "kanbien-platform-persistence.js");
const workspacePackageScope = join(repositoryRoot, "node_modules", "@kanbien");
const hiddenWorkspaceRoot = mkdtempSync(join(tmpdir(), "platform-shell-runtime-payload-"));
const hiddenWorkspaceScope = join(hiddenWorkspaceRoot, "@kanbien");

const requiredPayloadFiles = [
  serverEntrypoint,
  workerEntrypoint,
  relayEntrypoint,
  persistenceCompositionEntrypoint,
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-auth-cognito", "index.js"),
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-observability-cloudwatch", "index.js"),
  join(runtimeRoot, "node_modules", "@kanbien", "platform-adapter-aws-persistence-dynamodb", "index.js"),
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

renameSync(workspacePackageScope, hiddenWorkspaceScope);

try {
  await verifyCompiledPersistenceComposition();

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
      PLATFORM_CORS_ALLOWLIST: "https://staging.platform.kanbien.com",
      PLATFORM_HEALTH_LIVEZ_EXPOSURE: "public",
      PLATFORM_HEALTH_READYZ_EXPOSURE: "authenticated",
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
    stdio: "inherit",
  });

  if (serverResult.status !== 0) {
    throw new Error(`Compiled platform shell server runtime failed with exit code ${String(serverResult.status)}.`);
  }

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
  renameSync(hiddenWorkspaceScope, workspacePackageScope);
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
}
