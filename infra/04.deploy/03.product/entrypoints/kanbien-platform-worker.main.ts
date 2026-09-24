// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-worker
//   version: 2
//   status: active
//   layer: 04.deploy
//   domain: infra.ci-cd
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Run the Kanbien Platform product's declared jobs through the selected staging SQS delivery adapter and optional durable outbox-processing seam.
//   portability:
//     class: target-specific
//     targets:
//     - kanbien/staging
//   used_by:
//   - id: infra.04-deploy.03-product.targets.kanbien.staging.cloudformation.service
//     path: infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml

import { // Compose only the product's public app list and manifest.
  kanbienPlatformApps, // Mount the public Kanbien Platform app composition.
  kanbienPlatformProductManifest, // Obtain the product-declared configuration keys.
} from "@kanbien/product-kanbien-platform"; // Do not import app internals from the target entrypoint.
import { // Select the provider-specific queue delivery translation only at this target boundary.
  createAwsSdkPlatformSqsWorkerQueueFromEnv, // Build the bounded SQS receive/acknowledge/release client from deployment config.
  type PlatformSqsWorkerQueue, // Retain a provider-specific type only in target composition.
} from "@kanbien/platform-adapter-aws-queue-sqs"; // Keep SQS outside generic platform workers.
import { // Select the DynamoDB client only at the target composition boundary.
  createAwsSdkDynamoDbPersistenceCommandClient, // Construct the adapter's narrow command client from reviewed target configuration.
} from "@kanbien/platform-adapter-aws-persistence-dynamodb"; // Keep DynamoDB outside generic platform workers.
import type { // Reuse the target-owned observability lifecycle type.
  CloudWatchOtelMetricsRuntime, // Allow the worker to flush and shut down target metrics safely.
} from "@kanbien/platform-adapter-aws-observability-cloudwatch"; // Keep AWS observability adapter selection at the target boundary.
import { noopMetrics } from "@kanbien/core/monitoring"; // Preserve profile validation and safe logs when a local target deliberately has no metric exporter.
import { // Start only the generic worker process and its declared job shell.
  startPlatformWorkerProcess, // Preserve provider-neutral lifecycle, job validation, and telemetry mechanics.
  type PlatformWorkerProcess, // Hold the started generic worker process for graceful shutdown.
} from "@kanbien/platform-workers/main"; // Import the explicit worker process boundary rather than worker internals.
import { // Construct a validated durable worker owner rather than sharing an unsafe static lease identity.
  platformPersistenceLeaseOwner, // Brand the target-local process identity before it reaches persistence coordination.
  type PlatformPersistenceLeaseOwner, // Name the provider-neutral durable lease identity directly.
} from "@kanbien/platform-persistence"; // Keep leases and fences provider-neutral.
import { // Reuse the shared target metrics composition helper.
  observabilityFromTargetEnvironment, // Build the reviewed target metric runtime from deployment environment configuration.
} from "./kanbien-platform-observability"; // Keep target configuration parsing local to this deploy composition.
import { // Compose the selected DynamoDB processing store only at this target boundary.
  createKanbienPlatformDurableWorkerProcessing, // Supply the generic worker's durable-processing seam.
  createKanbienPlatformPersistenceTransitionObserver, // Bind durable transitions to the app-approved safe telemetry profile.
  dynamoDbPersistenceConfigurationFromTargetEnvironment, // Reconstruct non-secret persistence configuration consistently with the server.
  type KanbienPlatformDurableWorkerProcessing, // Retain the target composition shape without leaking it into generic workers.
} from "./kanbien-platform-persistence"; // Keep target persistence selection separate from worker lifecycle mechanics.

interface TargetWorkerConfiguration { // Describe the deployment-owned worker-specific queue policy.
  readonly queue: PlatformSqsWorkerQueue; // Supply the selected provider queue adapter to the target poll loop.
  readonly failureBackoffMs: number; // Bound retry pressure after a transient provider operation failure.
  readonly durableOutboxProcessing?: KanbienPlatformDurableWorkerProcessing; // Opt into durable duplicate protection only when this target configures its selected persistence provider.
}

interface TargetWorkerConfigurationError { // Return safe startup diagnostics without raw environment values.
  readonly code: "KANBIEN_PLATFORM_TARGET_WORKER_CONFIG_INVALID"; // Expose one stable target configuration error category.
  readonly defaultMessage: string; // Give operators a non-sensitive summary.
  readonly details: Readonly<{ // Name the selected deployment key and safe expected form.
    readonly path: string; // Identify the controlled deployment configuration field.
    readonly reason: string; // Explain the acceptable value without echoing it.
  }>;
}

export async function runKanbienPlatformWorkerMain(): Promise<void> { // Start one bounded target worker process.
  const observability = observabilityFromTargetEnvironment(process.env); // Build reviewed target metrics before jobs start.
  if (!observability.ok) { // Stop before polling when telemetry configuration is unsafe or incomplete.
    writeStartupFailure("kanbien-platform.worker.observability_configuration_invalid", observability.error); // Keep raw environment values out of logs.
    process.exitCode = 1; // Make the deployment fault visible to ECS.
    return; // Do not run a configured worker without its selected telemetry path.
  }

  const persistenceObserver = createKanbienPlatformPersistenceTransitionObserver({ // Bind durable processing transitions to the reviewed product profile before polling begins.
    executionContext: "worker", // Record this target process as background worker work rather than a public request.
    metrics: observability.value?.metrics ?? noopMetrics, // Preserve local safe logs while using the selected target metric sink when present.
  }); // Validate profile and telemetry projection before any durable claim can occur.
  if (!persistenceObserver.ok) { // Stop before polling when the registered profile cannot govern persistence evidence.
    writeStartupFailure("kanbien-platform.worker.persistence_observability_invalid", persistenceObserver.error); // Emit only the stable profile-validation error.
    await shutdownObservability(observability.value); // Close any already-created target metric runtime.
    process.exitCode = 1; // Surface the unsafe target composition to ECS.
    return; // Do not process durable work with an incoherent selected profile.
  }

  const workerConfiguration = workerConfigurationFromTargetEnvironment(process.env, persistenceObserver.value); // Validate selected queue and optional durable-processing configuration before lifecycle startup.
  if (!workerConfiguration.ok) { // Stop before polling when target queue or persistence configuration is invalid.
    writeStartupFailure("kanbien-platform.worker.queue_configuration_invalid", workerConfiguration.error); // Emit only safe configuration facts.
    await shutdownObservability(observability.value); // Close any already-created target metric runtime.
    process.exitCode = 1; // Fail container startup so ECS can surface the configuration fault.
    return; // Do not enter a partially configured polling loop.
  }

  const started = await startPlatformWorkerProcess({ // Start provider-neutral lifecycle and registered job execution.
    apps: kanbienPlatformApps, // Mount only public product app contributions.
    configKeys: productConfigKeys(), // Make product-declared worker configuration visible to mounted app schemas.
    ...(observability.value === undefined ? {} : { metrics: observability.value.metrics }), // Pass a provider-neutral Core metrics sink to generic workers.
    ...(workerConfiguration.value.durableOutboxProcessing === undefined ? {} : { durableOutboxProcessing: workerConfiguration.value.durableOutboxProcessing }), // Enable durable claim/fence/completion only when the target has selected and validated it.
    maxAttempts: 1, // Delegate durable retry counting and DLQ redrive to SQS rather than an ephemeral task-local queue.
    installSignalHandlers: false, // Coordinate worker and metrics shutdown together in this composition root.
  }); // Finish provider-neutral worker start.
  if (!started.ok) { // Stop if app mounting, config validation, or lifecycle startup failed.
    writeStartupFailure("kanbien-platform.worker.start_failed", started.error); // Emit only the stable worker failure code and message.
    await shutdownObservability(observability.value); // Flush and close target metrics before the failed task exits.
    process.exitCode = 1; // Surface the startup failure to ECS.
    return; // Never poll with an unready worker shell.
  }

  if (process.env["PLATFORM_WORKER_EXIT_AFTER_START"] === "1") { // Permit compiled-image payload verification without contacting SQS.
    await closeTargetWorker(started.value, observability.value); // Exercise normal lifecycle shutdown in the verification path.
    return; // Leave the validation process successfully.
  }

  const lifecycle = installTargetShutdownHandlers(started.value, observability.value); // Share one stop flag across long polling and graceful shutdown.
  await pollUntilStopped({ // Run the target-owned SQS delivery loop until ECS sends a termination signal.
    queue: workerConfiguration.value.queue, // Poll the selected provider queue.
    worker: started.value, // Adapt successful deliveries into the provider-neutral worker shell.
    observability: observability.value, // Flush metrics at bounded delivery boundaries.
    failureBackoffMs: workerConfiguration.value.failureBackoffMs, // Avoid a hot loop after a transient provider failure.
    isStopping: lifecycle.isStopping, // Stop after an in-flight long poll or delivery completes.
  }); // Complete the long-running worker process.
}

function productConfigKeys(): readonly string[] { // Project the product manifest's declared config requirements once.
  return [...new Set(kanbienPlatformProductManifest.apps.flatMap((app) => app.requiredConfig))]; // Keep target code independent of individual app internals.
}

function workerConfigurationFromTargetEnvironment( // Select and validate the one queue provider supported by this target.
  env: NodeJS.ProcessEnv, // Read only deployment-owned ECS environment values.
  persistenceObserver: import("@kanbien/platform-persistence").PlatformPersistenceObserver, // Supply the already-validated no-payload transition observer to optional durable processing.
): { readonly ok: true; readonly value: TargetWorkerConfiguration } | { readonly ok: false; readonly error: TargetWorkerConfigurationError } {
  if (env["PLATFORM_WORKER_QUEUE_PROVIDER"] !== "sqs") { // Reject absent or unimplemented providers before lifecycle startup.
    return targetWorkerConfigurationError("PLATFORM_WORKER_QUEUE_PROVIDER", "The staging worker requires the selected SQS queue provider."); // Keep provider choice explicit at the target boundary.
  }
  const queue = createAwsSdkPlatformSqsWorkerQueueFromEnv(env); // Let the adapter validate URLs, region, long-poll, and visibility bounds.
  if (!queue.ok) { // Translate adapter validation into a target-owned startup error.
    return targetWorkerConfigurationError(queue.error.details?.path ?? "PLATFORM_WORKER_SQS_*", queue.error.details?.reason ?? queue.error.defaultMessage); // Do not copy raw config values.
  }
  const failureBackoffMs = positiveInteger(env, "PLATFORM_WORKER_POLL_FAILURE_BACKOFF_MS"); // Bound pressure after a transient provider failure.
  if (!failureBackoffMs.ok) return failureBackoffMs; // Fail closed for a missing or unsafe polling backoff.
  const durableOutboxProcessing = durableOutboxProcessingFromTargetEnvironment(env, persistenceObserver); // Select durable processing only when this target explicitly enables the selected persistence provider.
  if (!durableOutboxProcessing.ok) return durableOutboxProcessing; // Stop before polling if durable processing would be partially configured.
  return {
    ok: true,
    value: {
      queue: queue.value,
      failureBackoffMs: failureBackoffMs.value,
      ...(durableOutboxProcessing.value === undefined ? {} : { durableOutboxProcessing: durableOutboxProcessing.value }),
    },
  }; // Return the fully validated target worker configuration.
}

function durableOutboxProcessingFromTargetEnvironment( // Select durable duplicate protection without forcing it onto the already-proven direct-SQS smoke consumer.
  env: NodeJS.ProcessEnv, // Read only reviewed task environment values.
  observer: import("@kanbien/platform-persistence").PlatformPersistenceObserver, // Receive the target-selected safe observer without exposing it to an AWS adapter.
): { readonly ok: true; readonly value: KanbienPlatformDurableWorkerProcessing | undefined } | { readonly ok: false; readonly error: TargetWorkerConfigurationError } {
  const provider = env["PLATFORM_PERSISTENCE_PROVIDER"]; // Read the target's explicit persistence-provider choice.
  if (provider === undefined || provider.length === 0) return { ok: true, value: undefined }; // Keep the pre-existing direct consumer behaviour explicit until the target enables the persistence path.
  if (provider !== "dynamodb") { // Reject a provider that this target composition cannot safely construct.
    return targetWorkerConfigurationError("PLATFORM_PERSISTENCE_PROVIDER", "The staging durable worker supports the selected DynamoDB persistence provider only."); // Prevent accidental provider fallback.
  }
  const configuration = dynamoDbPersistenceConfigurationFromTargetEnvironment(env); // Validate table and index names without logging their raw values.
  if (!configuration.ok) { // Translate the adapter's safe field-level error into target startup vocabulary.
    return targetWorkerConfigurationError(configuration.error.details.path, configuration.error.details.reason); // Stop before SQS polling begins.
  }
  const owner = durableLeaseOwnerFromTargetEnvironment(env); // Derive one process-specific ownership identity for leases and fences.
  if (!owner.ok) return owner; // Require a valid unique process component before claiming durable work.
  const leaseDurationMs = durableLeaseDurationFromTargetEnvironment(env); // Ensure the durable lease ends before SQS visibility expires.
  if (!leaseDurationMs.ok) return leaseDurationMs; // Stop before accepting any delivery when recovery timing is unsafe.
  return {
    ok: true,
    value: createKanbienPlatformDurableWorkerProcessing({ // Keep DynamoDB selection confined to the target composition root.
      client: createAwsSdkDynamoDbPersistenceCommandClient(configuration.value), // Construct no SDK call until the generic worker needs a durable claim.
      configuration: configuration.value, // Supply only validated non-secret adapter configuration.
      owner: owner.value, // Preserve the current process identity for a claim record.
      leaseDurationMs: leaseDurationMs.value, // Preserve the target's bounded recovery window.
      observer, // Emit only approved durable transition evidence outside the persistence control flow.
    }), // Return a provider-neutral structural dependency to the generic worker.
  };
}

function durableLeaseOwnerFromTargetEnvironment( // Convert the ECS-provided container hostname into a valid non-sensitive lease identity.
  env: NodeJS.ProcessEnv, // Read the process-local hostname only at composition time.
): { readonly ok: true; readonly value: PlatformPersistenceLeaseOwner } | { readonly ok: false; readonly error: TargetWorkerConfigurationError } {
  const hostname = env["HOSTNAME"]; // Read the container-local instance discriminator.
  if (hostname === undefined || !/^[a-z0-9-]+$/i.test(hostname)) { // Reject a missing or unsafe hostname rather than falling back to one shared owner.
    return targetWorkerConfigurationError("HOSTNAME", "A lowercase alphanumeric or hyphenated container hostname is required for durable worker leases."); // Do not expose the hostname itself.
  }
  const owner = platformPersistenceLeaseOwner("kanbien.worker.instance-" + hostname.toLowerCase()); // Prefix the hostname so every dot-separated segment begins with a letter.
  if (!owner.ok) return targetWorkerConfigurationError("HOSTNAME", "The container hostname could not form a valid durable worker lease owner."); // Preserve a bounded configuration error.
  return owner; // Return the branded provider-neutral owner.
}

function durableLeaseDurationFromTargetEnvironment( // Validate a lease that leaves recovery headroom inside the selected SQS visibility window.
  env: NodeJS.ProcessEnv, // Read target-owned queue and persistence policy values.
): { readonly ok: true; readonly value: number } | { readonly ok: false; readonly error: TargetWorkerConfigurationError } {
  const visibilitySeconds = Number(env["PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS"]); // Reuse the worker delivery policy already validated by the SQS adapter.
  const leaseDurationMs = Number(env["PLATFORM_PERSISTENCE_WORKER_LEASE_DURATION_MS"]); // Parse the durable coordination lease once.
  if (!Number.isInteger(leaseDurationMs) || leaseDurationMs <= 0 || !Number.isInteger(visibilitySeconds) || leaseDurationMs >= visibilitySeconds * 1000) { // Require positive milliseconds strictly below visibility so a redelivery never sees a still-active crashed claim.
    return targetWorkerConfigurationError("PLATFORM_PERSISTENCE_WORKER_LEASE_DURATION_MS", "A positive integer strictly below the configured SQS visibility timeout in milliseconds is required."); // Explain the safe relationship without returning values.
  }
  return { ok: true, value: leaseDurationMs }; // Return the bounded target-controlled duration.
}

async function pollUntilStopped(input: { // Keep provider polling coordination local to this target entrypoint.
  readonly queue: PlatformSqsWorkerQueue; // Receive and settle SQS deliveries.
  readonly worker: PlatformWorkerProcess; // Execute registered jobs through provider-neutral mechanics.
  readonly observability: CloudWatchOtelMetricsRuntime | undefined; // Flush target metrics after each settled outcome.
  readonly failureBackoffMs: number; // Wait safely after a provider operation failure.
  readonly isStopping: () => boolean; // Observe target lifecycle shutdown without global state.
}): Promise<void> {
  while (!input.isStopping()) { // Keep one delivery in flight until ECS requests shutdown.
    try { // Treat provider failures as retryable operational conditions, not process crashes.
      const received = await input.queue.receive(); // Long poll for at most one provider delivery.
      if (input.isStopping() || received.kind === "empty") continue; // Do not begin a new job after shutdown or for an empty long poll.
      if (received.kind === "invalid") { // SQS delivered a body that is not a valid platform queue envelope.
        await input.queue.release(received.receiptHandle); // Let infrastructure redrive the malformed delivery to the configured DLQ after bounded receives.
        console.warn(JSON.stringify({ level: "warn", message: "kanbien-platform.worker.invalid_delivery_released", fields: { code: received.error.code } })); // Exclude provider body, receipt, message ID, and error payload.
        await flushObservability(input.observability); // Flush any preceding worker metric batch before the next poll.
        continue; // Poll the next delivery without acknowledging invalid work.
      }

      const enqueued = input.worker.shell.enqueue(received.message); // Add the validated provider delivery to generic worker execution.
      if (!enqueued.ok) { // The local worker queue may be closed during shutdown or otherwise unavailable.
        await input.queue.release(received.receiptHandle); // Preserve at-least-once delivery instead of dropping the provider message.
        console.warn(JSON.stringify({ level: "warn", message: "kanbien-platform.worker.delivery_released", fields: { code: enqueued.error.code } })); // Keep provider data out of logs.
        await flushObservability(input.observability); // Flush pending safe worker telemetry.
        continue; // Resume polling only after the provider delivery is safely released.
      }

      const outcome = await input.worker.shell.runNext(); // Execute exactly the delivery just enqueued.
      if (!outcome.ok || outcome.value.status !== "succeeded") { // Failed, rejected, unknown, or retried work stays owned by SQS redrive policy.
        await input.queue.release(received.receiptHandle); // Make the delivery immediately available for a bounded SQS retry/DLQ cycle.
        const code = outcome.ok ? outcome.value.status : outcome.error.code; // Retain one safe operational outcome only.
        console.warn(JSON.stringify({ level: "warn", message: "kanbien-platform.worker.delivery_released", fields: { code } })); // Do not log queue payload, ID, receipt, tenant, or provider error.
      } else { // The generic worker completed the declared app job successfully.
        await input.queue.acknowledge(received.receiptHandle); // Delete only after successful job handling.
      }
      await flushObservability(input.observability); // Bound metric-loss exposure at every settled delivery outcome.
    } catch { // Keep raw AWS/provider failures out of operational logs and the task's public evidence.
      if (input.isStopping()) break; // Finish cleanly when the failed call raced with ECS shutdown.
      console.warn(JSON.stringify({ level: "warn", message: "kanbien-platform.worker.poll_failed" })); // Emit a safe diagnostic without provider error content.
      await delay(input.failureBackoffMs); // Prevent an unavailable provider from causing a hot error loop.
    }
  }
}

function installTargetShutdownHandlers( // Coordinate the generic worker and target metrics runtime under ECS signals.
  worker: PlatformWorkerProcess, // Close provider-neutral lifecycle after the current delivery boundary.
  observability: CloudWatchOtelMetricsRuntime | undefined, // Flush and shut down target-owned metric delivery.
): { readonly isStopping: () => boolean } {
  let stopping = false; // Retain target-local shutdown state without exposing it globally.
  const shutdown = async (signal: NodeJS.Signals) => { // Execute one idempotent shutdown path for ECS SIGTERM or local SIGINT.
    if (stopping) return; // Prevent duplicated signal handlers from closing the shell twice.
    stopping = true; // Tell the long-poll loop not to start another delivery.
    console.log(JSON.stringify({ level: "info", message: "kanbien-platform.worker.shutdown", fields: { signal } })); // Record only the safe lifecycle signal.
    await closeTargetWorker(worker, observability); // Finish worker and metrics lifecycle in order.
  };
  process.once("SIGTERM", () => { void shutdown("SIGTERM"); }); // Handle normal ECS task termination.
  process.once("SIGINT", () => { void shutdown("SIGINT"); }); // Handle local controlled termination.
  return { isStopping: () => stopping }; // Give the long-poll loop a read-only lifecycle signal.
}

function positiveInteger( // Parse one required positive deployment integer without returning its raw value.
  env: NodeJS.ProcessEnv, // Read target-owned ECS configuration.
  path: string, // Name the reviewed configuration key.
): { readonly ok: true; readonly value: number } | { readonly ok: false; readonly error: TargetWorkerConfigurationError } {
  const value = Number(env[path]); // Convert exactly once so invalid values fail consistently.
  if (!Number.isInteger(value) || value <= 0) { // Reject missing, non-numeric, zero, negative, and fractional values.
    return targetWorkerConfigurationError(path, "A positive integer is required."); // Explain the expected shape without disclosing the configured value.
  }
  return { ok: true, value }; // Return the bounded parsed configuration to the target poll loop.
}

function targetWorkerConfigurationError( // Construct a stable non-sensitive target worker configuration error.
  path: string, // Identify the reviewed configuration field that failed validation.
  reason: string, // Describe the expected safe shape.
): { readonly ok: false; readonly error: TargetWorkerConfigurationError } {
  return { // Preserve the same result shape used by other target configuration parsers.
    ok: false, // Mark target worker configuration unavailable.
    error: { // Keep diagnostic detail bounded to path and safe reason.
      code: "KANBIEN_PLATFORM_TARGET_WORKER_CONFIG_INVALID", // Provide one stable startup failure code.
      defaultMessage: "Kanbien platform target worker configuration is invalid.", // Avoid including environment values.
      details: { path, reason }, // Give operators a direct configuration location and expected form.
    }, // Finish safe configuration error construction.
  };
}

function writeStartupFailure( // Emit a safe target-worker startup diagnostic.
  message: string, // Name the startup stage without exposing runtime configuration.
  error: { readonly code: string; readonly defaultMessage: string }, // Restrict output to stable safe error vocabulary.
): void {
  console.error(JSON.stringify({ level: "error", message, error: { code: error.code, message: error.defaultMessage } })); // Do not log raw provider/config errors.
}

async function closeTargetWorker( // Close worker lifecycle before target metrics lifecycle.
  worker: PlatformWorkerProcess, // Shut down app lifecycle and generic worker resources.
  observability: CloudWatchOtelMetricsRuntime | undefined, // Flush metric export after worker work is complete.
): Promise<void> {
  try { // Ensure observability still closes when worker shutdown throws.
    await worker.close(); // Stop worker lifecycle and reject any newly enqueued local work.
  } finally { // Preserve target telemetry shutdown on every closure path.
    await shutdownObservability(observability); // Close the target-owned metrics runtime.
  }
}

async function flushObservability( // Flush at a settled delivery boundary without changing job outcome when telemetry is unavailable.
  observability: CloudWatchOtelMetricsRuntime | undefined, // Permit local targets without an exporter runtime.
): Promise<void> {
  if (observability === undefined) return; // Skip when this target intentionally has no metric provider.
  try { // Keep exporter failure observational rather than business-control flow.
    await observability.forceFlush(); // Request a bounded immediate metric export.
  } catch { // Do not expose exporter details or turn successful work into failure.
    console.warn(JSON.stringify({ level: "warn", message: "kanbien-platform.worker.observability_flush_failed" })); // Emit only a safe operational signal.
  }
}

async function shutdownObservability( // Close the target-owned metrics provider safely.
  observability: CloudWatchOtelMetricsRuntime | undefined, // Permit the generic/local no-provider path.
): Promise<void> {
  if (observability === undefined) return; // Avoid invoking a missing optional runtime.
  try { // Keep exporter shutdown independent from generic worker lifecycle.
    await observability.shutdown(); // Flush and close OTel metric resources.
  } catch { // Preserve an orderly process exit without leaking provider details.
    console.error(JSON.stringify({ level: "warn", message: "kanbien-platform.worker.observability_shutdown_failed" })); // Retain only the safe event name.
  }
}

function delay(milliseconds: number): Promise<void> { // Provide a small target-configured backoff after a provider failure.
  return new Promise((resolve) => { setTimeout(resolve, milliseconds); }); // Avoid a busy retry loop while keeping the task alive.
}

if (typeof require !== "undefined" && require.main === module) { // Execute only when ECS invokes this compiled target entrypoint directly.
  void runKanbienPlatformWorkerMain(); // Start the target worker without exporting side effects to test imports.
}
