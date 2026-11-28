// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.shared-scheduling-composition
//   version: 2
//   status: draft
//   created_on: "2026-11-27"
//   updated_on: "2026-11-28"
//   layer: 04.deploy
//   domain: deployment.scheduling
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Compose bounded due dispatch and durable externally delivered work from public runtime capabilities.
//   portability: { class: internal, targets: [kanbien-core-platform, entity-smoke] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.shared-scheduling-invocation
//     path: infra/04.deploy/03.product/entrypoints/shared/scheduling/invocation.ts

import { createHash } from "node:crypto";
import { outboxDeliveryPolicy } from "@kanbien/core/persistence";
import { isoDateTime, type Clock, type UuidGenerator } from "@kanbien/core/shared";
import type { Logger } from "@kanbien/core/logging";
import type { PlatformApp, PlatformDiagnosticCatalog, PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { createPlatformRuntimeContextDeps, mountPlatformRuntimeApps } from "@kanbien/platform-runtime";
import { createPlatformWorkerShell } from "@kanbien/platform-workers";
import { createPlatformOutboxRelay, createPlatformScheduleDelivery, createPlatformScheduleDispatcher,
  createPlatformScheduleJobOutboxFactory, platformPersistenceLeaseOwner,
  type PlatformOutboxQueuePayload, type PlatformOutboxStore, type PlatformProcessingStore, type PlatformScheduleStore,
  type PlatformPersistenceDiagnosticOptions } from "@kanbien/platform-persistence";
import { createPlatformSqsQueue, createPlatformSqsWorkerQueue, createPlatformSqsLambdaBatchHandler,
  type PlatformSqsCommandClient } from "@kanbien/platform-adapter-aws-queue-sqs";
import { createPlatformLambdaContinuation, createPlatformLambdaDispatcherHandler, type PlatformLambdaContext } from "@kanbien/platform-adapter-aws-runtime-lambda";
import { reportPlatformDiagnostic, reportPlatformErrorDiagnostic } from "@kanbien/platform-observability";
import type { PostgreSqlConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { schedulingRequired, type SchedulingConfiguration, type SchedulingPurpose } from "./configuration";

export interface SchedulingAppResources extends PlatformPersistenceDiagnosticOptions {
  readonly pool: PostgreSqlConnectionPool;
  readonly outbox: PlatformOutboxStore;
  readonly schedules: PlatformScheduleStore;
  readonly clock: Clock;
  readonly close: () => Promise<void>;
}
export interface SchedulingCompositionOptions extends SchedulingAppResources {
  readonly configuration: SchedulingConfiguration;
  readonly processing: PlatformProcessingStore;
  readonly client: PlatformSqsCommandClient;
  readonly uuidGenerator: UuidGenerator;
  readonly reporter: PlatformDiagnosticReporter;
  readonly logger: Logger;
  /** Dependencies beyond the worker's built-ins; app catalogues come from its public mount. */
  readonly extraCatalogs: readonly PlatformDiagnosticCatalog[];
  readonly app: PlatformApp;
  readonly purpose: SchedulingPurpose;
  /** Actual provider metadata, projected by the invocation owner; never event input. */
  readonly observationIdentity?: { readonly source_revision: string; readonly request_id: string; readonly function_arn: string };
}
export interface SchedulingComposedRuntime {
  run(event: unknown, context: PlatformLambdaContext): Promise<unknown>;
  close(): Promise<void>;
}

/** Target-owned policy; dependency factories still validate these checked values. */
export const schedulingRuntimeBudgets = Object.freeze({ workerMinimumRemainingMs: 45_000,
  dispatchMinimumRemainingMs: 35_000, dueMinimumRemainingMs: 45_000,
  queueConnectionTimeoutMs: 2_000, queueRequestTimeoutMs: 5_000 });

export async function createSchedulingComposition(options: SchedulingCompositionOptions): Promise<SchedulingComposedRuntime> {
  const { clock, reporter, logger, app, purpose } = options;
  const observeRuntime = (facts: () => Record<string, unknown>): void => {
    // Missing metadata or a failed evidence sink cannot turn durable completion
    // into another delivery. The provider reader treats missing logs as unknown.
    try {
      if (options.observationIdentity === undefined) return;
      logger.write({ level: "info", message: "Scheduling runtime observation.", fields: { scheduling_runtime: {
        schema: "kanbien/scheduling-runtime-observation/v1", ...options.observationIdentity,
        purpose, observed_at: clock.now().toISOString(), ...facts(),
      } } });
    } catch { /* Evidence is best effort, not execution authority. */ }
  };
  const context = { capability: "scheduling", operation: purpose, stage: "request" } as const;
  const diagnostics = { diagnosticDefinitions: options.diagnosticDefinitions ?? [],
    onDiagnostic: (record: Parameters<typeof reportPlatformDiagnostic>[1]) => reportPlatformDiagnostic(reporter, record, context) };
  const deps = { ...createPlatformRuntimeContextDeps({ clock, logger }), diagnostics: reporter };
  const owner = schedulingRequired(platformPersistenceLeaseOwner(`scheduling.${purpose}-${schedulingRequired(options.uuidGenerator.generate())}`));
  const observer = {
    record(observation: import("@kanbien/platform-persistence").PlatformPersistenceObservation) {
      if (observation.diagnosticRecord !== undefined) diagnostics.onDiagnostic(observation.diagnosticRecord);
      if (observation.error !== undefined) reportPlatformErrorDiagnostic(reporter, observation.error, context);
    },
    onDiagnostic: diagnostics.onDiagnostic,
  };
  if (purpose === "dispatch") {
    const mounted = schedulingRequired(await mountPlatformRuntimeApps({ apps: [app], deps, ...diagnostics }));
    const delivery = createPlatformScheduleDelivery({ clock, scheduleStore: options.schedules, maximumSchedules: 20,
      createOutboxEntry: createPlatformScheduleJobOutboxFactory({ jobs: mounted.jobs, clock,
        deliveryPolicy: schedulingRequired(outboxDeliveryPolicy("scheduling.sqs.standard.v1")), ...diagnostics }), ...diagnostics });
    const relay = createPlatformOutboxRelay({ outbox: options.outbox,
      queue: createPlatformSqsQueue<PlatformOutboxQueuePayload>({ queueUrl: options.configuration.queue.queueUrl, client: options.client, ...diagnostics }),
      owner, leaseDurationMs: 90_000, clock, observer, diagnosticDefinitions: diagnostics.diagnosticDefinitions });
    const dispatcher = createPlatformScheduleDispatcher({ delivery, relay, maximumRelayAttempts: 20, ...diagnostics });
    const run = createPlatformLambdaDispatcherHandler({ dispatcher, minimumRemainingMs: schedulingRuntimeBudgets.dispatchMinimumRemainingMs,
      minimumDeliveryRemainingMs: schedulingRuntimeBudgets.dueMinimumRemainingMs });
    return { async run(event, invocation) {
      const result = await run(event, invocation);
      observeRuntime(() => ({ kind: "dispatch-completed", result, trigger: schedulerTrigger(event) }));
      return result;
    },
      close: async () => undefined };
  }
  const worker = schedulingRequired(await createPlatformWorkerShell({ apps: [app], deps, diagnosticCatalogs: options.extraCatalogs,
    durableOutboxProcessing: { outbox: options.outbox, processingStore: options.processing, owner, leaseDurationMs: 90_000, observer },
    maxAttempts: 3, retryBackoffMs: () => 5_000 }));
  const batch = createPlatformSqsLambdaBatchHandler({ expectedSourceArn: options.configuration.queue.queueArn, maximumBatchSize: 1,
    visibility: createPlatformSqsWorkerQueue({ queueUrl: options.configuration.queue.queueUrl, client: options.client,
      waitTimeSeconds: 0, visibilityTimeoutSeconds: 360, ...diagnostics }),
    async processMessage(message) {
      const delivered = await worker.runDelivery(message);
      if (!delivered.ok) { reportPlatformErrorDiagnostic(reporter, delivered.error, context); return { disposition: "retry" }; }
      if (delivered.value.status === "succeeded") {
        // External durable processing has already checked message/outbox identity
        // equality and the authoritative stored envelope. Only its digest leaves
        // this boundary; application subject and payload are never logged.
        const completed = delivered.value;
        observeRuntime(() => ({ kind: "delivery-completed", outbox_sha256: createHash("sha256").update(completed.message.id).digest("hex"),
          attempt: completed.attempt, idempotency: completed.idempotency }));
        return { disposition: "acknowledge" };
      }
      reportPlatformErrorDiagnostic(reporter, delivered.value.error, context);
      return delivered.value.status === "retry" ? { disposition: "retry", delayMs: delivered.value.delayMs } : { disposition: "retry" };
    }, ...diagnostics });
  return {
    async run(event, invocation) {
      schedulingRequired(await worker.start());
      return batch.run(event, { shouldContinue: createPlatformLambdaContinuation(invocation, schedulingRuntimeBudgets.workerMinimumRemainingMs) });
    },
    async close() { schedulingRequired(await worker.shutdown()); },
  };
}

/** Observation only. The event never selects jobs or grants execution authority. */
function schedulerTrigger(event: unknown) {
  try {
    if (typeof event !== "object" || event === null || Array.isArray(event) || Object.keys(event).join() !== "scheduler") return null;
    const property = Object.getOwnPropertyDescriptor(event, "scheduler");
    const value: unknown = property !== undefined && "value" in property ? property.value : undefined;
    if (typeof value !== "object" || value === null || Array.isArray(value)
      || Object.keys(value).sort().join() !== "attempt,execution_id,schedule_arn,scheduled_at") return null;
    const fields = Object.getOwnPropertyDescriptors(value);
    if (Object.values(fields).some(field => !("value" in field) || typeof field.value !== "string")) return null;
    const arn = fields.schedule_arn!.value as string, at = fields.scheduled_at!.value as string;
    const execution = fields.execution_id!.value as string, attempt = fields.attempt!.value as string;
    if (!/^arn:aws:scheduler:[a-z0-9-]+:[0-9]{12}:schedule\/[A-Za-z0-9_.-]{1,64}\/[A-Za-z0-9_.-]{1,64}$/.test(arn)
      || !at.endsWith("Z") || !isoDateTime(at).ok || execution.length === 0 || execution.length > 256 || !/^[1-9][0-9]?$/.test(attempt)) return null;
    return { schedule_arn: arn, scheduled_at: at, execution_sha256: createHash("sha256").update(execution).digest("hex"), attempt: Number(attempt) };
  } catch { return null; }
}
