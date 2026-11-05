// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-relay
//   version: 2
//   status: active
//   created_on: "2026-09-24"
//   updated_on: "2026-10-30"
//   layer: 04.deploy
//   domain: persistence
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Run one bounded Kanbien staging durable-outbox relay pass through the selected DynamoDB and SQS adapters.
//   portability:
//     class: internal
//     targets:
//     - kanbien/staging
//   used_by:
//   - id: platform.server.image-build
//     path: platform/server/tsconfig.image.json

import { createAwsSdkDynamoDbPersistenceCommandClient } from "@kanbien/platform-adapter-aws-persistence-dynamodb";
import { createAwsSdkPlatformSqsQueue } from "@kanbien/platform-adapter-aws-queue-sqs";
import { noopMetrics } from "@kanbien/core/monitoring";
import { systemClock } from "@kanbien/core/shared";
import {
  createKanbienPlatformOutboxRelay,
  createKanbienPlatformPersistenceTransitionObserver,
  reportKanbienPlatformPersistenceStartupDiagnostic,
  dynamoDbPersistenceConfigurationFromTargetEnvironment,
} from "./kanbien-platform-persistence";
import { observabilityFromTargetEnvironment } from "./kanbien-platform-observability";
import { targetTaskLeaseOwnerFromEnvironment } from "./kanbien-platform-task-lease-owner";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { reportTargetConfigurationError, selectTargetConfigurationEvidence, targetEnvironmentConfigurationRecord } from "./kanbien-platform-configuration-diagnostics";
import { reportKanbienPlatformDeliveryFailure, reportKanbienPlatformQueueDiagnostic } from "./kanbien-platform-delivery-diagnostics";

const safeDynamoDbOperations = new Set([
  "create_outbox",
  "read_outbox",
  "list_outbox",
  "claim_outbox",
  "publish_outbox",
  "read_processing",
  "claim_processing",
  "complete_processing",
  "release_processing",
  "append_lineage",
  "read_lineage",
  "write_facts",
  "write_atomic",
]);

const safeDynamoDbProviderFailureClasses = new Set([
  "access_denied",
  "conditional_check_failed",
  "resource_not_found",
  "validation",
  "throttled",
  "transport",
  "unknown",
]);

interface TargetRelayConfiguration {
  readonly relay: ReturnType<typeof createKanbienPlatformOutboxRelay>;
}

interface TargetRelayConfigurationError {
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
  readonly code: "KANBIEN_PLATFORM_TARGET_RELAY_CONFIG_INVALID";
  readonly defaultMessage: string;
  readonly details: Readonly<{ readonly path: string; readonly reason: string }>;
}

/**
 * Run one controlled relay pass. A later scheduler or service may invoke this
 * entrypoint repeatedly, but that topology is deliberately not selected here.
 */
export async function runKanbienPlatformRelayMain(): Promise<void> {
  const observability = observabilityFromTargetEnvironment(process.env);
  if (!observability.ok) {
    writeStartupFailure("kanbien-platform.relay.observability_configuration_invalid", observability.error);
    process.exitCode = 1;
    return;
  }

  const observer = createKanbienPlatformPersistenceTransitionObserver({
    executionContext: "worker",
    metrics: observability.value?.metrics ?? noopMetrics,
  });
  if (!observer.ok) {
    writeStartupFailure("kanbien-platform.relay.persistence_observability_invalid", observer.error);
    await shutdownObservability(observability.value);
    process.exitCode = 1;
    return;
  }

  const configuration = await relayConfigurationFromTargetEnvironment(process.env, observer.value);
  if (!configuration.ok) {
    writeStartupFailure("kanbien-platform.relay.configuration_invalid", configuration.error);
    await shutdownObservability(observability.value);
    process.exitCode = 1;
    return;
  }

  if (process.env["PLATFORM_RELAY_EXIT_AFTER_START"] === "1") {
    await shutdownObservability(observability.value);
    return;
  }

  try {
    const outcome = await configuration.value.relay.runOnce();
    if (!outcome.ok) {
      writeStartupFailure("kanbien-platform.relay.run_failed", outcome.error, false);
      process.exitCode = 1;
      return;
    }

    const status = outcome.value.status;
    const failed = status === "queue-send-failed" || status === "publish-marker-failed";
    console[failed ? "error" : "log"](JSON.stringify({
      level: failed ? "error" : "info",
      message: "kanbien-platform.relay.run_completed",
      fields: { status },
    }));
    if (failed) {
      process.exitCode = 1;
    }
  } catch (error) {
    reportKanbienPlatformDeliveryFailure({ workload: "relay", boundary: "run-once", condition: "threw", effect: "work-outcome-unknown" }, error);
    throw error;
  } finally {
    await flushAndShutdownObservability(observability.value);
  }
}

async function relayConfigurationFromTargetEnvironment(
  env: NodeJS.ProcessEnv,
  observer: import("@kanbien/platform-persistence").PlatformPersistenceObserver,
): Promise<{ readonly ok: true; readonly value: TargetRelayConfiguration } | { readonly ok: false; readonly error: TargetRelayConfigurationError }> {
  const persistenceProvider = env["PLATFORM_PERSISTENCE_PROVIDER"];
  if (persistenceProvider !== "dynamodb") {
    return relayConfigurationError("PLATFORM_PERSISTENCE_PROVIDER", "The staging relay requires the selected DynamoDB persistence provider.", { diagnosticRecord: targetEnvironmentConfigurationRecord("PLATFORM_PERSISTENCE_PROVIDER", persistenceProvider === undefined ? "missing" : persistenceProvider.length === 0 ? "empty" : "unsupported") });
  }
  const queueProvider = env["PLATFORM_RELAY_QUEUE_PROVIDER"];
  if (queueProvider !== "sqs") {
    return relayConfigurationError("PLATFORM_RELAY_QUEUE_PROVIDER", "The staging relay requires the selected SQS queue provider.", { diagnosticRecord: targetEnvironmentConfigurationRecord("PLATFORM_RELAY_QUEUE_PROVIDER", queueProvider === undefined ? "missing" : queueProvider.length === 0 ? "empty" : "unsupported") });
  }
  const persistence = dynamoDbPersistenceConfigurationFromTargetEnvironment(env);
  if (!persistence.ok) {
    return relayConfigurationError(persistence.error.details.path, persistence.error.details.reason, persistence.error);
  }
  const queueUrl = requiredString(env, "PLATFORM_RELAY_SQS_QUEUE_URL");
  if (!queueUrl.ok) return queueUrl;
  const queueRegion = requiredString(env, "PLATFORM_RELAY_SQS_REGION");
  if (!queueRegion.ok) return queueRegion;
  const owner = await relayLeaseOwnerFromTargetEnvironment(env);
  if (!owner.ok) return owner;
  const leaseDurationMs = boundedPositiveInteger(env, "PLATFORM_RELAY_LEASE_DURATION_MS", 90_000);
  if (!leaseDurationMs.ok) return leaseDurationMs;

  return {
    ok: true,
    value: {
      relay: createKanbienPlatformOutboxRelay({
        client: createAwsSdkDynamoDbPersistenceCommandClient(persistence.value, { onDiagnostic: reportKanbienPlatformPersistenceStartupDiagnostic }),
        configuration: persistence.value,
        queue: createAwsSdkPlatformSqsQueue({ queueUrl: queueUrl.value, region: queueRegion.value,
          onDiagnostic: (record, context) => reportKanbienPlatformQueueDiagnostic("relay", record, context) }),
        owner: owner.value,
        leaseDurationMs: leaseDurationMs.value,
        clock: systemClock,
        observer,
      }),
    },
  };
}

async function flushAndShutdownObservability(
  observability: import("@kanbien/platform-adapter-aws-observability-cloudwatch").CloudWatchOtelMetricsRuntime | undefined,
): Promise<void> {
  if (observability === undefined) return;
  try {
    await observability.forceFlush();
  } catch {
    console.warn(JSON.stringify({ level: "warn", message: "kanbien-platform.relay.observability_flush_failed" }));
  }
  await shutdownObservability(observability);
}

async function shutdownObservability(
  observability: import("@kanbien/platform-adapter-aws-observability-cloudwatch").CloudWatchOtelMetricsRuntime | undefined,
): Promise<void> {
  if (observability === undefined) return;
  try {
    await observability.shutdown();
  } catch {
    console.warn(JSON.stringify({ level: "warn", message: "kanbien-platform.relay.observability_shutdown_failed" }));
  }
}

async function relayLeaseOwnerFromTargetEnvironment(
  env: NodeJS.ProcessEnv,
): Promise<{ readonly ok: true; readonly value: import("@kanbien/platform-persistence").PlatformPersistenceLeaseOwner } | { readonly ok: false; readonly error: TargetRelayConfigurationError }> {
  const owner = await targetTaskLeaseOwnerFromEnvironment(env, "kanbien.relay.instance-");
  if (!owner.ok) return relayConfigurationError(owner.error.path, owner.error.reason, owner.error);
  return owner;
}

function requiredString(
  env: NodeJS.ProcessEnv,
  path: "PLATFORM_RELAY_SQS_QUEUE_URL" | "PLATFORM_RELAY_SQS_REGION",
): { readonly ok: true; readonly value: string } | { readonly ok: false; readonly error: TargetRelayConfigurationError } {
  const value = env[path];
  if (value === undefined || value.trim().length === 0) {
    return relayConfigurationError(path, "A non-empty value is required.", { diagnosticRecord: targetEnvironmentConfigurationRecord(path, value === undefined ? "missing" : "blank") });
  }
  return { ok: true, value };
}

function boundedPositiveInteger(
  env: NodeJS.ProcessEnv,
  path: "PLATFORM_RELAY_LEASE_DURATION_MS",
  maximum: number,
): { readonly ok: true; readonly value: number } | { readonly ok: false; readonly error: TargetRelayConfigurationError } {
  const raw = env[path];
  const value = Number(raw);
  const integer = Number.isInteger(value);
  if (!integer || value <= 0 || value > maximum) {
    return relayConfigurationError(path, `A positive integer no greater than ${maximum} is required.`, { diagnosticRecord: targetEnvironmentConfigurationRecord(path, raw === undefined ? "missing" : raw.length === 0 ? "empty" : !integer ? "invalid-integer" : value <= 0 ? "not-positive" : "above-maximum") });
  }
  return { ok: true, value };
}

function relayConfigurationError(
  path: string,
  reason: string,
  evidence?: unknown,
): { readonly ok: false; readonly error: TargetRelayConfigurationError } {
  return {
    ok: false,
    error: {
      code: "KANBIEN_PLATFORM_TARGET_RELAY_CONFIG_INVALID",
      defaultMessage: "Kanbien platform target relay configuration is invalid.",
      details: { path, reason },
      ...selectTargetConfigurationEvidence(evidence),
    },
  };
}

function writeStartupFailure(
  message: string,
  error: { readonly code: string; readonly defaultMessage: string; readonly details?: Readonly<Record<string, unknown>>; readonly params?: Readonly<Record<string, unknown>> },
  reportConfiguration: boolean = true,
): void {
  if (reportConfiguration) reportTargetConfigurationError(error);
  const path = error.details?.["path"];
  const operation = error.params?.["operation"];
  const providerFailureClass = error.params?.["provider_failure_class"];
  console.error(JSON.stringify({
    level: "error",
    message,
    error: {
      code: error.code,
      message: error.defaultMessage,
      ...(typeof path === "string" ? { path } : {}),
      ...(typeof operation === "string" && safeDynamoDbOperations.has(operation) ? { operation } : {}),
      ...(typeof providerFailureClass === "string" && safeDynamoDbProviderFailureClasses.has(providerFailureClass) ? { providerFailureClass } : {}),
    },
  }));
}

if (typeof require !== "undefined" && require.main === module) {
  void runKanbienPlatformRelayMain();
}
