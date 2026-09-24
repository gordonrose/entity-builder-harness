import { deepEqual, equal } from "node:assert/strict";
import {
  outboxDeliveryPolicy,
  outboxEntry,
  outboxEntryId,
  outboxMessageType,
  recordChange,
  recordChangeFieldName,
  recordChangeId,
  recordId,
  recordKind,
  recordReference,
  recordRevision,
} from "@kanbien/core/persistence";
import { inMemoryQueue, queueError, type Queue } from "@kanbien/core/queues";
import { causationId, isoDateTimeFromDate } from "@kanbien/core/shared";
import {
  createInMemoryPlatformOutboxStore,
  createInMemoryPlatformProcessingStore,
  createInMemoryPlatformRecordChangeStore,
  createPlatformOutboxRelay,
  platformPersistenceFence,
  platformPersistenceLeaseOwner,
  platformPersistenceMutation,
  type PlatformOutboxQueuePayload,
  type PlatformPersistenceObservation,
} from "../src/index";

async function main(): Promise<void> {
  const baseTime = new Date("2026-09-23T12:00:00.000Z");
  const at = (milliseconds: number) => isoDateTimeFromDate(new Date(baseTime.getTime() + milliseconds));
  const record = recordReference({
    kind: accepted(recordKind("platform-smoke.work-item")),
    id: accepted(recordId("work-1")),
  });
  const entry = outboxEntry({
    id: outboxEntryId("outbox-1"),
    subject: record,
    messageType: accepted(outboxMessageType("platform-smoke.work.accepted")),
    deliveryPolicy: accepted(outboxDeliveryPolicy("platform-short-idempotent-work.v1")),
    createdAt: at(0),
    causationId: causationId("request-1"),
  });
  const relayA = accepted(platformPersistenceLeaseOwner("relay-a"));
  const relayB = accepted(platformPersistenceLeaseOwner("relay-b"));
  const workerA = accepted(platformPersistenceLeaseOwner("worker-a"));
  const workerB = accepted(platformPersistenceLeaseOwner("worker-b"));

  const outbox = createInMemoryPlatformOutboxStore();
  const created = await outbox.create(entry);
  equal(created.ok, true);
  if (!created.ok) {
    throw new Error("Expected outbox entry to be created.");
  }
  equal(created.value.state, "pending");
  equal(created.value.attempt, 0);

  const duplicate = await outbox.create(entry);
  equal(duplicate.ok, false);
  if (!duplicate.ok) {
    equal(duplicate.error.code, "PLATFORM_PERSISTENCE_DUPLICATE_OUTBOX_ENTRY");
  }

  const due = await outbox.listDeliverable({ asOf: at(0), limit: 1 });
  equal(due.ok, true);
  if (!due.ok) {
    throw new Error("Expected pending outbox entry to be deliverable.");
  }
  deepEqual(due.value.map((record) => record.entry.id), [entry.id]);

  const firstClaim = await outbox.claim({
    id: entry.id,
    owner: relayA,
    acquiredAt: at(0),
    leaseDurationMs: 1_000,
  });
  equal(firstClaim.ok, true);
  if (!firstClaim.ok || firstClaim.value.disposition !== "claimed") {
    throw new Error("Expected first relay claim.");
  }
  equal(firstClaim.value.record.lease?.fence, 1);
  equal(firstClaim.value.record.attempt, 1);

  const activeLease = await outbox.claim({
    id: entry.id,
    owner: relayB,
    acquiredAt: at(500),
    leaseDurationMs: 1_000,
  });
  equal(activeLease.ok, true);
  if (!activeLease.ok) {
    throw new Error("Expected active lease result.");
  }
  equal(activeLease.value.disposition, "lease-active");

  const secondClaim = await outbox.claim({
    id: entry.id,
    owner: relayB,
    acquiredAt: at(1_001),
    leaseDurationMs: 1_000,
  });
  equal(secondClaim.ok, true);
  if (!secondClaim.ok || secondClaim.value.disposition !== "claimed") {
    throw new Error("Expected expired relay lease to be reclaimable.");
  }
  equal(secondClaim.value.record.lease?.fence, 2);
  equal(secondClaim.value.record.attempt, 2);

  const stalePublish = await outbox.markPublished({
    id: entry.id,
    fence: firstClaim.value.record.lease!.fence,
    publishedAt: at(1_002),
  });
  equal(stalePublish.ok, false);
  if (!stalePublish.ok) {
    equal(stalePublish.error.code, "PLATFORM_PERSISTENCE_STALE_FENCE");
  }

  const published = await outbox.markPublished({
    id: entry.id,
    fence: secondClaim.value.record.lease!.fence,
    publishedAt: at(1_002),
  });
  equal(published.ok, true);
  if (!published.ok) {
    throw new Error("Expected current relay fence to publish.");
  }
  equal(published.value.state, "published");

  const expiringEntry = outboxEntry({
    id: outboxEntryId("outbox-2"),
    subject: record,
    messageType: accepted(outboxMessageType("platform-smoke.work.accepted")),
    deliveryPolicy: accepted(outboxDeliveryPolicy("platform-short-idempotent-work.v1")),
    createdAt: at(5_000),
  });
  await outbox.create(expiringEntry);
  const expiringRelayClaim = await outbox.claim({
    id: expiringEntry.id,
    owner: relayA,
    acquiredAt: at(5_000),
    leaseDurationMs: 1_000,
  });
  if (!expiringRelayClaim.ok || expiringRelayClaim.value.disposition !== "claimed") {
    throw new Error("Expected relay claim for expiry test.");
  }
  const expiredPublish = await outbox.markPublished({
    id: expiringEntry.id,
    fence: expiringRelayClaim.value.record.lease!.fence,
    publishedAt: at(6_000),
  });
  equal(expiredPublish.ok, false);
  if (!expiredPublish.ok) {
    equal(expiredPublish.error.code, "PLATFORM_PERSISTENCE_LEASE_EXPIRED");
  }

  const processing = createInMemoryPlatformProcessingStore();
  const firstProcessingClaim = await processing.claim({
    outboxEntryId: entry.id,
    owner: workerA,
    acquiredAt: at(2_000),
    leaseDurationMs: 1_000,
  });
  equal(firstProcessingClaim.ok, true);
  if (!firstProcessingClaim.ok || firstProcessingClaim.value.disposition !== "claimed") {
    throw new Error("Expected first worker claim.");
  }
  equal(firstProcessingClaim.value.record.lease?.fence, 1);

  const secondProcessingClaim = await processing.claim({
    outboxEntryId: entry.id,
    owner: workerB,
    acquiredAt: at(3_001),
    leaseDurationMs: 1_000,
  });
  equal(secondProcessingClaim.ok, true);
  if (!secondProcessingClaim.ok || secondProcessingClaim.value.disposition !== "claimed") {
    throw new Error("Expected expired worker lease to be reclaimable.");
  }
  equal(secondProcessingClaim.value.record.lease?.fence, 2);

  const staleCompletion = await processing.complete({
    outboxEntryId: entry.id,
    fence: firstProcessingClaim.value.record.lease!.fence,
    outcome: "succeeded",
    completedAt: at(3_002),
  });
  equal(staleCompletion.ok, false);
  if (!staleCompletion.ok) {
    equal(staleCompletion.error.code, "PLATFORM_PERSISTENCE_STALE_FENCE");
  }

  const completion = await processing.complete({
    outboxEntryId: entry.id,
    fence: secondProcessingClaim.value.record.lease!.fence,
    outcome: "succeeded",
    completedAt: at(3_002),
  });
  equal(completion.ok, true);
  if (!completion.ok) {
    throw new Error("Expected current worker claim to complete.");
  }
  equal(completion.value.disposition, "completed");
  equal(completion.value.record.completion?.outcome, "succeeded");

  const retryEligibleEntryId = outboxEntryId("outbox-processing-retry");
  const retryEligibleClaim = await processing.claim({
    outboxEntryId: retryEligibleEntryId,
    owner: workerA,
    acquiredAt: at(4_000),
    leaseDurationMs: 1_000,
  });
  if (!retryEligibleClaim.ok || retryEligibleClaim.value.disposition !== "claimed") {
    throw new Error("Expected processing claim for release test.");
  }
  const releasedForRetry = await processing.release({
    outboxEntryId: retryEligibleEntryId,
    fence: retryEligibleClaim.value.record.lease!.fence,
    releasedAt: at(4_001),
  });
  equal(releasedForRetry.ok, true);
  if (!releasedForRetry.ok) {
    throw new Error("Expected current worker claim to become retry eligible.");
  }
  equal(releasedForRetry.value.state, "retry-eligible");
  const completionAfterRelease = await processing.complete({
    outboxEntryId: retryEligibleEntryId,
    fence: retryEligibleClaim.value.record.lease!.fence,
    outcome: "succeeded",
    completedAt: at(4_001),
  });
  equal(completionAfterRelease.ok, false);
  if (!completionAfterRelease.ok) {
    equal(completionAfterRelease.error.code, "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED");
  }
  const reclaimedAfterRelease = await processing.claim({
    outboxEntryId: retryEligibleEntryId,
    owner: workerB,
    acquiredAt: at(4_001),
    leaseDurationMs: 1_000,
  });
  equal(reclaimedAfterRelease.ok, true);
  if (!reclaimedAfterRelease.ok || reclaimedAfterRelease.value.disposition !== "claimed") {
    throw new Error("Expected released processing to be reclaimable without waiting for lease expiry.");
  }
  equal(reclaimedAfterRelease.value.record.attempt, 2);
  equal(reclaimedAfterRelease.value.record.lease?.fence, 2);

  const expiringProcessingEntryId = outboxEntryId("outbox-3");
  const expiringProcessingClaim = await processing.claim({
    outboxEntryId: expiringProcessingEntryId,
    owner: workerA,
    acquiredAt: at(5_000),
    leaseDurationMs: 1_000,
  });
  if (!expiringProcessingClaim.ok || expiringProcessingClaim.value.disposition !== "claimed") {
    throw new Error("Expected worker claim for expiry test.");
  }
  const expiredCompletion = await processing.complete({
    outboxEntryId: expiringProcessingEntryId,
    fence: expiringProcessingClaim.value.record.lease!.fence,
    outcome: "succeeded",
    completedAt: at(6_000),
  });
  equal(expiredCompletion.ok, false);
  if (!expiredCompletion.ok) {
    equal(expiredCompletion.error.code, "PLATFORM_PERSISTENCE_LEASE_EXPIRED");
  }

  const duplicateProcessing = await processing.claim({
    outboxEntryId: entry.id,
    owner: workerA,
    acquiredAt: at(4_000),
    leaseDurationMs: 1_000,
  });
  equal(duplicateProcessing.ok, true);
  if (!duplicateProcessing.ok) {
    throw new Error("Expected duplicate processing result.");
  }
  equal(duplicateProcessing.value.disposition, "already-completed");

  const lineage = createInMemoryPlatformRecordChangeStore();
  const change = accepted(recordChange({
    id: recordChangeId("change-1"),
    record,
    revision: accepted(recordRevision(1)),
    action: "created",
    occurredAt: at(0),
    causationId: causationId("request-1"),
    changedFields: [accepted(recordChangeFieldName("state"))],
  }));
  const appended = await lineage.append(change);
  equal(appended.ok, true);
  deepEqual(await lineage.findByRecord(record), [change]);
  deepEqual(await lineage.findByCause(causationId("request-1")), [change]);

  const mutation = platformPersistenceMutation({ recordChange: change, outboxEntry: entry });
  equal(mutation.ok, true);
  if (!mutation.ok) {
    throw new Error("Expected matching lineage and outbox facts to form a mutation.");
  }
  equal(mutation.value.outboxEntry.subject.id, mutation.value.recordChange.record.id);

  const unrelatedCauseEntry = outboxEntry({
    id: outboxEntryId("outbox-4"),
    subject: record,
    messageType: accepted(outboxMessageType("platform-smoke.work.accepted")),
    deliveryPolicy: accepted(outboxDeliveryPolicy("platform-short-idempotent-work.v1")),
    createdAt: at(0),
    causationId: causationId("request-2"),
  });
  const invalidMutation = platformPersistenceMutation({
    recordChange: change,
    outboxEntry: unrelatedCauseEntry,
  });
  equal(invalidMutation.ok, false);
  if (!invalidMutation.ok) {
    equal(invalidMutation.error.code, "PLATFORM_PERSISTENCE_INVALID_MUTATION");
  }

  const duplicateChange = await lineage.append(change);
  equal(duplicateChange.ok, false);
  if (!duplicateChange.ok) {
    equal(duplicateChange.error.code, "PLATFORM_PERSISTENCE_DUPLICATE_RECORD_CHANGE");
  }

  const invalidFence = platformPersistenceFence(0);
  equal(invalidFence.ok, false);

  let relayNow = new Date(baseTime.getTime() + 10_000);
  const relayClock = { now: () => relayNow };
  const relayOutbox = createInMemoryPlatformOutboxStore();
  const relayEntry = outboxEntry({
    id: outboxEntryId("outbox-5"),
    subject: record,
    messageType: accepted(outboxMessageType("platform-smoke.work.accepted")),
    deliveryPolicy: accepted(outboxDeliveryPolicy("platform-short-idempotent-work.v1")),
    createdAt: at(10_000),
    causationId: causationId("request-1"),
  });
  await relayOutbox.create(relayEntry);
  const acceptedQueue = inMemoryQueue<PlatformOutboxQueuePayload>();
  const relayObservations: PlatformPersistenceObservation[] = [];
  const relay = createPlatformOutboxRelay({
    outbox: relayOutbox,
    queue: acceptedQueue,
    owner: relayA,
    leaseDurationMs: 1_000,
    clock: relayClock,
    observer: { record: (observation) => relayObservations.push(observation) },
  });
  const relayed = await relay.runOnce();
  equal(relayed.ok, true);
  if (!relayed.ok || relayed.value.status !== "published") {
    throw new Error("Expected relay to publish its claimed entry after the queue accepts it.");
  }
  equal(relayed.value.outboxEntryId, relayEntry.id);
  equal(relayed.value.attempt, 1);
  equal(relayed.value.fence, 1);
  deepEqual(acceptedQueue.acceptedMessages().map((message) => ({
    id: String(message.id),
    type: String(message.type),
    version: Number(message.version),
    causationId: message.causationId === undefined ? undefined : String(message.causationId),
    idempotencyKey: message.idempotencyKey === undefined ? undefined : String(message.idempotencyKey),
    payload: message.payload,
  })), [{
    id: "outbox-5",
    type: "platform-smoke.work.accepted",
    version: 1,
    causationId: "request-1",
    idempotencyKey: "outbox-5",
    payload: { outboxEntryId: "outbox-5" },
  }]);
  const relayPublishedRecord = await relayOutbox.get(relayEntry.id);
  if (relayPublishedRecord === null) {
    throw new Error("Expected relayed outbox entry to remain available.");
  }
  equal(relayPublishedRecord.state, "published");
  deepEqual(relayObservations.map((observation) => ({
    transition: observation.transition,
    outcome: observation.outcome,
    fields: Object.keys(observation).sort(),
  })), [
    { transition: "outbox.claimed", outcome: "succeeded", fields: ["outcome", "transition"] },
    { transition: "outbox.published", outcome: "succeeded", fields: ["outcome", "transition"] },
  ]);

  const relayIdle = await relay.runOnce();
  equal(relayIdle.ok, true);
  if (!relayIdle.ok) {
    throw new Error("Expected a successful idle relay cycle.");
  }
  equal(relayIdle.value.status, "idle");

  const recoverableOutbox = createInMemoryPlatformOutboxStore();
  const recoverableEntry = outboxEntry({
    id: outboxEntryId("outbox-6"),
    subject: record,
    messageType: accepted(outboxMessageType("platform-smoke.work.accepted")),
    deliveryPolicy: accepted(outboxDeliveryPolicy("platform-short-idempotent-work.v1")),
    createdAt: at(11_000),
  });
  await recoverableOutbox.create(recoverableEntry);
  relayNow = new Date(baseTime.getTime() + 11_000);
  const unavailableQueue: Queue<PlatformOutboxQueuePayload> = {
    async send() {
      return {
        ok: false,
        error: queueError({
          code: "QUEUE_UNAVAILABLE",
          defaultMessage: "Queue is temporarily unavailable for the relay test.",
          messageKey: "queues.test.unavailable",
        }),
      };
    },
  };
  const failedRelayObservations: PlatformPersistenceObservation[] = [];
  const failedRelay = createPlatformOutboxRelay({
    outbox: recoverableOutbox,
    queue: unavailableQueue,
    owner: relayA,
    leaseDurationMs: 1_000,
    clock: relayClock,
    observer: { record: (observation) => failedRelayObservations.push(observation) },
  });
  const failedSend = await failedRelay.runOnce();
  equal(failedSend.ok, true);
  if (!failedSend.ok || failedSend.value.status !== "queue-send-failed") {
    throw new Error("Expected queue failure to leave the durable entry recoverable.");
  }
  const leasedAfterFailure = await recoverableOutbox.get(recoverableEntry.id);
  if (leasedAfterFailure === null) {
    throw new Error("Expected failed relay entry to remain available.");
  }
  equal(leasedAfterFailure.state, "leased");
  equal(leasedAfterFailure.attempt, 1);
  deepEqual(failedRelayObservations.map((observation) => ({
    transition: observation.transition,
    outcome: observation.outcome,
    errorCode: observation.error !== undefined && typeof observation.error === "object" && observation.error !== null && "code" in observation.error
      ? (observation.error as { readonly code: string }).code
      : undefined,
  })), [
    { transition: "outbox.claimed", outcome: "succeeded", errorCode: undefined },
    { transition: "outbox.queue_send_failed", outcome: "failed", errorCode: "QUEUE_UNAVAILABLE" },
  ]);

  relayNow = new Date(baseTime.getTime() + 12_001);
  const recoveryQueue = inMemoryQueue<PlatformOutboxQueuePayload>();
  const recoveryRelay = createPlatformOutboxRelay({
    outbox: recoverableOutbox,
    queue: recoveryQueue,
    owner: relayB,
    leaseDurationMs: 1_000,
    clock: relayClock,
  });
  const recovered = await recoveryRelay.runOnce();
  equal(recovered.ok, true);
  if (!recovered.ok || recovered.value.status !== "published") {
    throw new Error("Expected a later relay to reclaim and publish after lease expiry.");
  }
  equal(recovered.value.attempt, 2);
  equal(recovered.value.fence, 2);
  equal(recoveryQueue.acceptedMessages().length, 1);

  const telemetryFailureOutbox = createInMemoryPlatformOutboxStore();
  const telemetryFailureEntry = outboxEntry({
    id: outboxEntryId("outbox-7"),
    subject: record,
    messageType: accepted(outboxMessageType("platform-smoke.work.accepted")),
    deliveryPolicy: accepted(outboxDeliveryPolicy("platform-short-idempotent-work.v1")),
    createdAt: at(13_000),
  });
  await telemetryFailureOutbox.create(telemetryFailureEntry);
  relayNow = new Date(baseTime.getTime() + 13_000);
  const telemetryFailureRelay = createPlatformOutboxRelay({
    outbox: telemetryFailureOutbox,
    queue: inMemoryQueue<PlatformOutboxQueuePayload>(),
    owner: relayA,
    leaseDurationMs: 1_000,
    clock: relayClock,
    observer: { record: () => { throw new Error("Observer must be best effort."); } },
  });
  const telemetryFailureResult = await telemetryFailureRelay.runOnce();
  equal(telemetryFailureResult.ok, true);
  if (!telemetryFailureResult.ok) {
    throw new Error("Expected a telemetry observer failure not to alter relay delivery.");
  }
  equal(telemetryFailureResult.value.status, "published");
}

function accepted<TValue, TError>(result: { readonly ok: true; readonly value: TValue } | { readonly ok: false; readonly error: TError }): TValue {
  if (!result.ok) {
    throw new Error("Expected valid test fixture value.");
  }

  return result.value;
}

main()
  .then(() => {
    console.log("platform/persistence runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
