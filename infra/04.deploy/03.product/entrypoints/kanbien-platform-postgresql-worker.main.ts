// One fixed relational smoke queue consumer. It completes the durable
// processing record before it acknowledges the one permitted envelope.
import { reportTargetConfigurationError, targetEnvironmentConfigurationRecord } from "./kanbien-platform-configuration-diagnostics";
import { reportKanbienPlatformDeliveryFailure, reportKanbienPlatformQueueDiagnostic, reportKanbienPlatformPersistenceDeliveryDiagnostic, targetDeliveryErrorSource, targetDeliveryDisposition, type KanbienPlatformDeliveryBoundaryDetail } from "./kanbien-platform-delivery-diagnostics";

import { outboxEntryId } from "@kanbien/core/persistence";
import { isoDateTimeFromDate } from "@kanbien/core/shared";
import { createAwsSdkPlatformSqsWorkerQueue } from "@kanbien/platform-adapter-aws-queue-sqs";
import { platformPersistenceLeaseOwner } from "@kanbien/platform-persistence";
import { createPostgreSqlPlatformProcessingStore } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import {
  closePool,
  configurationFromEnvironment,
  connectionPool,
  secretFromEnvironment,
  writeOutcome,
} from "./kanbien-platform-postgresql-task";

const expectedOutboxEntry = "platform-smoke.work-item-accepted.postgresql-stage6-smoke-20260926-a";

async function main(): Promise<void> {
  let pool;
  let boundary: KanbienPlatformDeliveryBoundaryDetail["boundary"] | undefined;
  let effect: KanbienPlatformDeliveryBoundaryDetail["effect"] = "work-not-invoked";
  let preciseFailure: { readonly error: Error } | undefined;
  function fail(message: string, condition: KanbienPlatformDeliveryBoundaryDetail["condition"], source?: unknown, disposition?: KanbienPlatformDeliveryBoundaryDetail["disposition"]): never {
    const error = new Error(message);
    preciseFailure = { error };
    reportKanbienPlatformDeliveryFailure({ workload: "relational-worker", boundary: boundary ?? "delivery-selection", condition, effect,
      ...(disposition === undefined ? {} : { disposition }) }, source);
    throw error;
  }
  try {
    const configuration = configurationFromEnvironment();
    const runtime = secretFromEnvironment("RELATIONAL_RUNTIME_SECRET_JSON");
    const queueUrl = requiredEnvironment("RELATIONAL_SMOKE_QUEUE_URL");
    pool = connectionPool(runtime, configuration.runtimeSecretArn, configuration.schema);
    const queue = createAwsSdkPlatformSqsWorkerQueue({ queueUrl, region: "eu-west-1", waitTimeSeconds: 20, visibilityTimeoutSeconds: 120,
      onDiagnostic: (record, context) => reportKanbienPlatformQueueDiagnostic("relational-worker", record, context) });
    boundary = "receive";
    const delivery = await queue.receive();
    boundary = "delivery-selection";
    const deliveryKind = delivery.kind;
    if (deliveryKind !== "delivery") fail("RELATIONAL_TASK_WORKER_DELIVERY_INVALID", "not-delivery", targetDeliveryErrorSource(delivery), targetDeliveryDisposition(deliveryKind));
    boundary = "identity-check";
    let payloadIssue: KanbienPlatformDeliveryBoundaryDetail["condition"] | undefined;
    const deliveredOutboxEntryId = payloadOutboxEntryId(delivery.message.payload, (issue) => { payloadIssue = issue; });
    if (deliveredOutboxEntryId !== expectedOutboxEntry) fail("RELATIONAL_TASK_WORKER_DELIVERY_INVALID", payloadIssue ?? "payload-id-mismatch");
    boundary = "owner-validation";
    const owner = platformPersistenceLeaseOwner("kanbien-postgresql-worker-a");
    if (!owner.ok) fail("RELATIONAL_TASK_OWNER_INVALID", "invalid-owner", targetDeliveryErrorSource(owner));
    const store = createPostgreSqlPlatformProcessingStore({ configuration: {
      host: runtime.host, port: runtime.port, database: configuration.database, schema: configuration.schema,
      runtimeCredentialSecretReference: configuration.runtimeSecretArn, maximumPoolSize: 2, connectionTimeoutMs: 10_000,
      idleTimeoutMs: 10_000, statementTimeoutMs: 15_000,
      tls: { mode: "verify-full", certificateAuthoritySource: "injected" },
    }, pool, onDiagnostic: (record) => reportKanbienPlatformPersistenceDeliveryDiagnostic(record, boundary === "complete" || boundary === "completion-result" ? "complete" : "claim") });
    const entryId = outboxEntryId(expectedOutboxEntry);
    boundary = "claim";
    effect = "work-outcome-unknown";
    const claimed = await store.claim({ outboxEntryId: entryId, owner: owner.value, acquiredAt: isoDateTimeFromDate(new Date()), leaseDurationMs: 90_000 });
    boundary = "claim-result";
    if (!claimed.ok) fail("RELATIONAL_TASK_PROCESSING_CLAIM_FAILED", "returned-failure", targetDeliveryErrorSource(claimed));
    const claimDisposition = claimed.value.disposition;
    if (claimDisposition !== "claimed") fail("RELATIONAL_TASK_PROCESSING_CLAIM_FAILED", "unexpected-disposition", undefined, targetDeliveryDisposition(claimDisposition));
    if (claimed.value.record.lease === undefined) fail("RELATIONAL_TASK_PROCESSING_CLAIM_FAILED", "missing-lease");
    boundary = "complete";
    const completedAt = isoDateTimeFromDate(new Date());
    const complete = await store.complete({ outboxEntryId: entryId, fence: claimed.value.record.lease.fence, outcome: "succeeded", completedAt });
    boundary = "completion-result";
    if (!complete.ok) fail("RELATIONAL_TASK_PROCESSING_COMPLETION_FAILED", "returned-failure", targetDeliveryErrorSource(complete));
    const completionDisposition = complete.value.disposition;
    if (completionDisposition !== "completed") fail("RELATIONAL_TASK_PROCESSING_COMPLETION_FAILED", "unexpected-disposition", undefined, targetDeliveryDisposition(completionDisposition));
    boundary = "acknowledge";
    effect = "work-success-acknowledgement-unknown";
    await queue.acknowledge(delivery.receiptHandle);
    effect = "work-success-acknowledgement-returned";
    boundary = "summary";
    writeOutcome("worker_completed", "succeeded");
  } catch (error) {
    if (boundary !== undefined && (preciseFailure === undefined || preciseFailure.error !== error)) reportKanbienPlatformDeliveryFailure({ workload: "relational-worker", boundary, condition: "threw", effect }, error);
    reportTargetConfigurationError(error);
    writeOutcome("worker_completed", "failed");
    process.exitCode = 1;
  } finally {
    await closePool(pool);
  }
}

function payloadOutboxEntryId(value: unknown, rejected: (condition: KanbienPlatformDeliveryBoundaryDetail["condition"]) => void): string | undefined {
  if (typeof value !== "object") { rejected("payload-not-record"); return undefined; }
  if (value === null) { rejected("payload-null"); return undefined; }
  if (Array.isArray(value)) { rejected("payload-array"); return undefined; }
  const candidate = (value as Record<string, unknown>).outboxEntryId;
  if (typeof candidate !== "string") rejected(candidate === undefined ? "payload-id-missing" : "payload-id-wrong-type");
  return typeof candidate === "string" ? candidate : undefined;
}

function requiredEnvironment(name: string): string {
  const value = process.env[name];
  if (value === undefined || value.length === 0) throw Object.assign(new Error("RELATIONAL_TASK_QUEUE_CONFIGURATION_INVALID"), { diagnosticRecord: targetEnvironmentConfigurationRecord("RELATIONAL_SMOKE_QUEUE_URL", value === undefined ? "missing" : "empty") });
  return value;
}

void main();
