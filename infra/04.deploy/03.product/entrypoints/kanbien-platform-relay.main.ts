// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-relay
//   version: 2
//   status: active
//   layer: 04.deploy
//   domain: persistence
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Run one bounded Kanbien staging durable-outbox relay pass through the selected DynamoDB and SQS adapters.
//   portability:
//     class: target-specific
//     targets:
//     - kanbien/staging
//   used_by:
//   - id: platform.server.image-build
//     path: platform/server/tsconfig.image.json

import { createAwsSdkDynamoDbPersistenceCommandClient } from "@kanbien/platform-adapter-aws-persistence-dynamodb";
import { createAwsSdkPlatformSqsQueue } from "@kanbien/platform-adapter-aws-queue-sqs";
import { noopMetrics } from "@kanbien/core/monitoring";
import {
  platformPersistenceLeaseOwner,
  type PlatformPersistenceLeaseOwner,
} from "@kanbien/platform-persistence";
import { systemClock } from "@kanbien/core/shared";
import {
  createKanbienPlatformOutboxRelay,
  createKanbienPlatformPersistenceTransitionObserver,
  dynamoDbPersistenceConfigurationFromTargetEnvironment,
} from "./kanbien-platform-persistence";
import { observabilityFromTargetEnvironment } from "./kanbien-platform-observability";

interface TargetRelayConfiguration {
  readonly relay: ReturnType<typeof createKanbienPlatformOutboxRelay>;
}

interface TargetRelayConfigurationError {
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

  const configuration = relayConfigurationFromTargetEnvironment(process.env, observer.value);
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
      writeStartupFailure("kanbien-platform.relay.run_failed", outcome.error);
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
  } finally {
    await flushAndShutdownObservability(observability.value);
  }
}

function relayConfigurationFromTargetEnvironment(
  env: NodeJS.ProcessEnv,
  observer: import("@kanbien/platform-persistence").PlatformPersistenceObserver,
): { readonly ok: true; readonly value: TargetRelayConfiguration } | { readonly ok: false; readonly error: TargetRelayConfigurationError } {
  if (env["PLATFORM_PERSISTENCE_PROVIDER"] !== "dynamodb") {
    return relayConfigurationError("PLATFORM_PERSISTENCE_PROVIDER", "The staging relay requires the selected DynamoDB persistence provider.");
  }
  if (env["PLATFORM_RELAY_QUEUE_PROVIDER"] !== "sqs") {
    return relayConfigurationError("PLATFORM_RELAY_QUEUE_PROVIDER", "The staging relay requires the selected SQS queue provider.");
  }
  const persistence = dynamoDbPersistenceConfigurationFromTargetEnvironment(env);
  if (!persistence.ok) {
    return relayConfigurationError(persistence.error.details.path, persistence.error.details.reason);
  }
  const queueUrl = requiredString(env, "PLATFORM_RELAY_SQS_QUEUE_URL");
  if (!queueUrl.ok) return queueUrl;
  const queueRegion = requiredString(env, "PLATFORM_RELAY_SQS_REGION");
  if (!queueRegion.ok) return queueRegion;
  const owner = relayLeaseOwnerFromTargetEnvironment(env);
  if (!owner.ok) return owner;
  const leaseDurationMs = boundedPositiveInteger(env, "PLATFORM_RELAY_LEASE_DURATION_MS", 90_000);
  if (!leaseDurationMs.ok) return leaseDurationMs;

  return {
    ok: true,
    value: {
      relay: createKanbienPlatformOutboxRelay({
        client: createAwsSdkDynamoDbPersistenceCommandClient(persistence.value),
        configuration: persistence.value,
        queue: createAwsSdkPlatformSqsQueue({ queueUrl: queueUrl.value, region: queueRegion.value }),
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

function relayLeaseOwnerFromTargetEnvironment(
  env: NodeJS.ProcessEnv,
): { readonly ok: true; readonly value: PlatformPersistenceLeaseOwner } | { readonly ok: false; readonly error: TargetRelayConfigurationError } {
  const hostname = env["HOSTNAME"];
  if (hostname === undefined || !/^[a-z0-9-]+$/i.test(hostname)) {
    return relayConfigurationError("HOSTNAME", "A lowercase alphanumeric or hyphenated container hostname is required for durable relay leases.");
  }
  const owner = platformPersistenceLeaseOwner("kanbien.relay.instance-" + hostname.toLowerCase());
  if (!owner.ok) {
    return relayConfigurationError("HOSTNAME", "The container hostname could not form a valid durable relay lease owner.");
  }
  return owner;
}

function requiredString(
  env: NodeJS.ProcessEnv,
  path: string,
): { readonly ok: true; readonly value: string } | { readonly ok: false; readonly error: TargetRelayConfigurationError } {
  const value = env[path];
  if (value === undefined || value.trim().length === 0) {
    return relayConfigurationError(path, "A non-empty value is required.");
  }
  return { ok: true, value };
}

function boundedPositiveInteger(
  env: NodeJS.ProcessEnv,
  path: string,
  maximum: number,
): { readonly ok: true; readonly value: number } | { readonly ok: false; readonly error: TargetRelayConfigurationError } {
  const value = Number(env[path]);
  if (!Number.isInteger(value) || value <= 0 || value > maximum) {
    return relayConfigurationError(path, `A positive integer no greater than ${maximum} is required.`);
  }
  return { ok: true, value };
}

function relayConfigurationError(
  path: string,
  reason: string,
): { readonly ok: false; readonly error: TargetRelayConfigurationError } {
  return {
    ok: false,
    error: {
      code: "KANBIEN_PLATFORM_TARGET_RELAY_CONFIG_INVALID",
      defaultMessage: "Kanbien platform target relay configuration is invalid.",
      details: { path, reason },
    },
  };
}

function writeStartupFailure(
  message: string,
  error: { readonly code: string; readonly defaultMessage: string },
): void {
  console.error(JSON.stringify({ level: "error", message, error: { code: error.code, message: error.defaultMessage } }));
}

if (typeof require !== "undefined" && require.main === module) {
  void runKanbienPlatformRelayMain();
}
