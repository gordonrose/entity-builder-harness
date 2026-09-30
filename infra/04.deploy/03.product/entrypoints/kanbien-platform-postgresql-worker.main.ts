// One fixed relational smoke queue consumer. It completes the durable
// processing record before it acknowledges the one permitted envelope.

import { outboxEntryId } from "@kanbien/core/persistence";
import { isoDateTimeFromDate } from "@kanbien/core/shared";
import { createAwsSdkPlatformSqsWorkerQueue } from "@kanbien/platform-adapter-aws-queue-sqs";
import { platformPersistenceLeaseOwner } from "@kanbien/platform-persistence";
import { createPostgreSqlPlatformProcessingStore } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import {
  closePool,
  relationalTaskMode,
  verifyRelationalTaskPreflight,
  writePreflightOutcome,
  configurationFromEnvironment,
  connectionPool,
  secretFromEnvironment,
  writeOutcome,
} from "./kanbien-platform-postgresql-task";

const expectedOutboxEntry = "platform-smoke.work-item-accepted.postgresql-stage6-smoke-20260926-a";

async function main(): Promise<void> {
  let pool;
  let preflight = process.argv.slice(2).includes("--preflight");
  try {
    preflight = relationalTaskMode() === "preflight";
    const configuration = configurationFromEnvironment();
    const runtime = secretFromEnvironment("RELATIONAL_RUNTIME_SECRET_JSON");
    const queueUrl = requiredEnvironment("RELATIONAL_SMOKE_QUEUE_URL");
    pool = connectionPool(runtime, configuration.runtimeSecretArn, configuration.schema);
    if (preflight) {
      await verifyRelationalTaskPreflight(pool, "worker", runtime.username);
      writePreflightOutcome("worker", "passed");
      return;
    }
    const queue = createAwsSdkPlatformSqsWorkerQueue({ queueUrl, region: "eu-west-1", waitTimeSeconds: 20, visibilityTimeoutSeconds: 120 });
    const delivery = await queue.receive();
    if (delivery.kind !== "delivery") throw new Error("RELATIONAL_TASK_WORKER_DELIVERY_INVALID");
    const deliveredOutboxEntryId = payloadOutboxEntryId(delivery.message.payload);
    if (deliveredOutboxEntryId !== expectedOutboxEntry) throw new Error("RELATIONAL_TASK_WORKER_DELIVERY_INVALID");
    const owner = platformPersistenceLeaseOwner("kanbien-postgresql-worker-a");
    if (!owner.ok) throw new Error("RELATIONAL_TASK_OWNER_INVALID");
    const store = createPostgreSqlPlatformProcessingStore({ configuration: {
      host: runtime.host, port: runtime.port, database: configuration.database, schema: configuration.schema,
      runtimeCredentialSecretReference: configuration.runtimeSecretArn, maximumPoolSize: 2, connectionTimeoutMs: 10_000,
      idleTimeoutMs: 10_000, statementTimeoutMs: 15_000,
      tls: { mode: "verify-full", certificateAuthoritySource: "injected" },
    }, pool });
    const entryId = outboxEntryId(expectedOutboxEntry);
    const claimed = await store.claim({ outboxEntryId: entryId, owner: owner.value, acquiredAt: isoDateTimeFromDate(new Date()), leaseDurationMs: 90_000 });
    if (!claimed.ok || claimed.value.disposition !== "claimed" || claimed.value.record.lease === undefined) throw new Error("RELATIONAL_TASK_PROCESSING_CLAIM_FAILED");
    const completedAt = isoDateTimeFromDate(new Date());
    const complete = await store.complete({ outboxEntryId: entryId, fence: claimed.value.record.lease.fence, outcome: "succeeded", completedAt });
    if (!complete.ok || complete.value.disposition !== "completed") throw new Error("RELATIONAL_TASK_PROCESSING_COMPLETION_FAILED");
    await queue.acknowledge(delivery.receiptHandle);
    writeOutcome("worker_completed", "succeeded");
  } catch {
    if (preflight) writePreflightOutcome("worker", "failed");
    else writeOutcome("worker_completed", "failed");
    process.exitCode = 1;
  } finally {
    await closePool(pool);
  }
}

function payloadOutboxEntryId(value: unknown): string | undefined {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return undefined;
  const candidate = (value as Record<string, unknown>).outboxEntryId;
  return typeof candidate === "string" ? candidate : undefined;
}

function requiredEnvironment(name: string): string {
  const value = process.env[name];
  if (value === undefined || value.length === 0) throw new Error("RELATIONAL_TASK_QUEUE_CONFIGURATION_INVALID");
  return value;
}

void main();
