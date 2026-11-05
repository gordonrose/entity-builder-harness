import { deepEqual, equal, rejects, throws } from "node:assert/strict";
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
  type OutboxEntry,
} from "@kanbien/core/persistence";
import * as coreQueue from "@kanbien/core/queues";
import { inMemoryQueue, queueError, type Queue } from "@kanbien/core/queues";
import { causationId, correlationId, isoDateTimeFromDate, ok, type ISODateTime } from "@kanbien/core/shared";
import { tenantId } from "@kanbien/core/tenancy";
import { createDiagnosticRecord, defineDiagnostic, parseDiagnosticRecord, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import {
  createInMemoryPlatformOutboxStore,
  createInMemoryPlatformProcessingStore,
  createInMemoryPlatformRecordChangeStore,
  createPlatformOutboxRelay,
  platformPersistenceFence,
  platformPersistenceLeaseOwner,
  platformPersistenceMutation,
  platformPersistenceAttempt, platformPersistenceLease, nextPlatformPersistenceLease,
  persistenceLocalRejectionDiagnostic, persistenceLocalRejectionDiagnosticRecord,
  persistenceStoredRecordDiagnostic, persistenceStoredRecordDiagnosticRecord,
  persistenceBoundaryDiagnostic, persistenceBoundaryDiagnosticRecord, persistenceCrudObservedDiagnosticRecord,
  persistenceObservedDiagnosticRecord, persistenceDiagnosticDefinitions, persistenceCurrentDiagnosticDefinitions,
  persistenceCrudDiagnosticDefinitions,
  persistenceReconciliationDiagnostic, persistenceReconciliationDiagnosticRecord,
  persistenceCommandDiagnosticDefinitions, persistenceCommandConditionDiagnostic, persistenceCommandDiagnosticRecord,
  persistenceStoredAttributeDiagnostic, persistenceStoredAttributeDiagnosticRecord,
  persistenceStateReconciliationDiagnostic, persistenceStateReconciliationDiagnosticRecord,
  resolvePlatformPersistenceDiagnosticOptions, observePlatformPersistenceDiagnostic,
  platformOutboxRecord, platformOutboxQueueMessage, persistenceRelayBoundaryDiagnostic, platformPersistenceError,
  persistenceRelayBoundaryDiagnosticRecord, type PlatformOutboxStore, type PlatformPersistenceObserver, type PlatformPersistenceLeaseOwner,
  persistenceConfigurationInputDiagnostic, persistenceConfigurationInputDiagnosticRecord,
  persistenceConfigurationDiagnostic, persistenceConfigurationDiagnosticRecord, platformPersistenceDiagnosticCatalog,
  type PlatformOutboxQueuePayload,
  type PlatformPersistenceObservation,
} from "../src/index";

async function main(): Promise<void> {
  const inputDefinition = persistenceConfigurationInputDiagnostic;
  equal(platformPersistenceDiagnosticCatalog.definitions.filter((definition) => definition.code === inputDefinition.code && definition.version === 1).length, 1);
  for (const field of ["region", "store", "outbox-index", "lineage-index"] as const) for (const reason of ["missing", "wrong-type"] as const) {
    const record = persistenceConfigurationInputDiagnosticRecord(field, reason);
    deepEqual(record, { schema: "core/diagnostic-record/v1", code: "persistence.configuration-input-invalid", definitionVersion: 1, detail: { field, reason } });
    equal(parseDiagnosticRecord(inputDefinition, record).ok, true);
  }
  const shape = persistenceConfigurationInputDiagnosticRecord("configuration", "wrong-shape");
  deepEqual(shape.detail, { field: "configuration", reason: "wrong-shape" });
  for (const detail of [
    { field: "private-canary", reason: "missing" }, { field: "region", reason: "private-canary" },
    { field: "region", reason: "missing", value: "private-canary" },
    { field: "region", reason: "missing", message: "private-canary" },
  ]) equal(parseDiagnosticRecord(inputDefinition, { ...shape, detail }).ok, false);
  equal(parseDiagnosticRecord(inputDefinition, { ...shape, definitionVersion: 2 }).ok, false);
  deepEqual(persistenceConfigurationDiagnostic.detail, { type: "object", properties: {
    field: { type: "enum", values: ["region", "store", "outbox-index", "lineage-index", "configuration"] },
    reason: { type: "enum", values: ["blank", "too-long"] },
  } });
  const historical = persistenceConfigurationDiagnosticRecord("region", "blank");
  equal(parseDiagnosticRecord(persistenceConfigurationDiagnostic, historical).ok, true);
  equal(parseDiagnosticRecord(persistenceConfigurationDiagnostic, { ...historical, detail: { field: "region", reason: "missing" } }).ok, false);
  equal(parseDiagnosticRecord(inputDefinition, historical).ok, false);
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

  const diagnostic = (operation: string, field: string, condition: string, phase = "validation", effect = "not-started") => ({
    schema: "core/diagnostic-record/v1", code: "persistence.local-rejected", definitionVersion: 1,
    detail: { operation, field, condition, phase, effect },
  });
  const rejection = (result: { readonly ok: boolean; readonly error?: { readonly diagnosticRecord?: unknown } }, expected: unknown) => {
    equal(result.ok, false); deepEqual(result.error?.diagnosticRecord, expected);
  };
  for (const [value, condition] of [[1.5, "not-integer"], [0, "not-positive"], [-1, "not-positive"]] as const) {
    rejection(platformPersistenceFence(value), diagnostic("validate-lease", "fence", condition));
  }
  for (const [value, condition] of [[NaN, "not-integer"], [1.5, "not-integer"], [-1, "negative"]] as const) {
    rejection(platformPersistenceAttempt(value), diagnostic("validate-lease", "attempt", condition));
  }
  rejection(platformPersistenceLeaseOwner("PRIVATE OWNER CANARY"), diagnostic("validate-lease", "owner", "pattern"));
  const validLease = { owner: relayA, fence: accepted(platformPersistenceFence(1)), attempt: accepted(platformPersistenceAttempt(0)), acquiredAt: at(0), expiresAt: at(1) };
  rejection(platformPersistenceLease({ ...validLease, expiresAt: at(0) }), diagnostic("validate-lease", "expiry", "not-after-acquisition"));
  equal(platformPersistenceLease({ ...validLease, expiresAt: "invalid-date" as typeof validLease.expiresAt }).ok, true, "do not add date validation absent from the original guard");
  for (const [durationMs, condition] of [[0, "not-positive"], [1.5, "not-integer"]] as const) {
    rejection(nextPlatformPersistenceLease({ owner: relayA, priorAttempt: validLease.attempt, acquiredAt: at(0), durationMs }), diagnostic("validate-lease", "duration", condition));
  }
  for (const first of [0, 1.5, 1]) {
    let reads = 0;
    const result = nextPlatformPersistenceLease({ owner: relayA, priorAttempt: validLease.attempt, acquiredAt: at(0), get durationMs() {
      if (++reads > 1) throw new Error("Duration must be read only once");
      return first;
    } });
    equal(reads, 1);
    if (first === 1) {
      equal(result.ok, true);
      if (result.ok) equal(result.value.expiresAt, at(1));
    } else {
      rejection(result, diagnostic("validate-lease", "duration", first === 0 ? "not-positive" : "not-integer"));
      if (!result.ok) deepEqual(result.error.params, { durationMs: String(first) });
    }
  }
  const rawGetterThrow = Object.freeze(new Error("getter-private-canary"));
  throws(() => nextPlatformPersistenceLease({ owner: relayA, priorAttempt: validLease.attempt, acquiredAt: at(0), get durationMs(): never { throw rawGetterThrow; } }), error => error === rawGetterThrow);
  const getterOutbox = createInMemoryPlatformOutboxStore();
  accepted(await getterOutbox.create(entry));
  for (const [values, condition] of [[[1.5], "not-integer"], [[1, 0], "not-positive"]] as const) {
    const reads: number[] = [];
    rejection(await getterOutbox.listDeliverable({ asOf: at(0), get limit() {
      const ordinal = reads.length; reads.push(ordinal);
      if (ordinal >= values.length) throw new Error("Unexpected diagnostic limit getter read");
      return values[ordinal]!;
    } }), diagnostic("list_outbox", "limit", condition, "state-check", "local-state-unchanged"));
    deepEqual(reads, values.map((_value, ordinal) => ordinal));
  }
  for (const values of [[rawGetterThrow], [1, rawGetterThrow]] as const) {
    const reads: number[] = [];
    await rejects(getterOutbox.listDeliverable({ asOf: at(0), get limit() {
      const ordinal = reads.length; reads.push(ordinal); const value = values[ordinal]!;
      if (typeof value !== "number") throw value;
      return value;
    } }), (error: unknown) => error === rawGetterThrow);
    deepEqual(reads, values.map((_value, ordinal) => ordinal));
  }
  let acceptedLimitReads = 0;
  deepEqual(accepted(await getterOutbox.listDeliverable({ asOf: at(0), get limit() { acceptedLimitReads++; return 1; } })).map((item) => item.entry.id), [entry.id]);
  equal(acceptedLimitReads, 3, "integer guard, range guard and existing slice each retain their read");
  const sequence = nextPlatformPersistenceLease({ owner: relayA, priorLease: { ...validLease, fence: NaN as typeof validLease.fence },
    priorAttempt: NaN as typeof validLease.attempt, acquiredAt: at(0), durationMs: 1 });
  rejection(sequence, diagnostic("validate-lease", "sequence", "cannot-advance"));
  if (sequence.ok) throw new Error("Expected invalid sequence");
  deepEqual(sequence.error.relatedDiagnosticRecords, [diagnostic("validate-lease", "fence", "not-integer"), diagnostic("validate-lease", "attempt", "not-integer")]);
  const { causationId: omittedChangeCause, ...changeWithoutCause } = change;
  const { causationId: omittedEntryCause, ...entryWithoutCause } = entry;
  void omittedChangeCause; void omittedEntryCause;
  for (const [recordChangeInput, outboxEntryInput, field, condition] of [
    [{ ...change, record: { ...record, kind: accepted(recordKind("other.kind")) } }, entry, "subject-kind", "mismatch"],
    [{ ...change, record: { ...record, id: accepted(recordId("other-id")) } }, entry, "subject-id", "mismatch"],
    [changeWithoutCause, entry, "causation", "left-absent"],
    [change, entryWithoutCause, "causation", "right-absent"],
    [change, unrelatedCauseEntry, "causation", "mismatch"],
    [{ ...change, tenantId: tenantId("tenant-a") }, { ...entry, tenantId: tenantId("tenant-b") }, "tenant", "mismatch"],
    [{ ...change, correlationId: correlationId("a") }, { ...entry, correlationId: correlationId("b") }, "correlation", "mismatch"],
  ] as const) {
    const result = platformPersistenceMutation({ recordChange: recordChangeInput, outboxEntry: outboxEntryInput });
    rejection(result, diagnostic("validate-mutation", field, condition));
  }
  equal(platformPersistenceMutation({ recordChange: { ...change, tenantId: tenantId("a"), correlationId: correlationId("a") }, outboxEntry: entry }).ok, true);
  equal(platformPersistenceMutation({ recordChange: change, outboxEntry: { ...entry, tenantId: tenantId("b"), correlationId: correlationId("b") } }).ok, true);
  const observations: DiagnosticRecord[] = [];
  const observedOutbox = createInMemoryPlatformOutboxStore({ onDiagnostic(record) { observations.push(record); return Promise.reject("sink-canary"); } });
  const stateDiagnostic = (operation: string, field: string, condition: string) => diagnostic(operation, field, condition, "state-check", "local-state-unchanged");
  rejection(await observedOutbox.claim({ id: entry.id, owner: relayA, acquiredAt: at(0), leaseDurationMs: 0 }), stateDiagnostic("claim_outbox", "record", "not-found"));
  rejection(await observedOutbox.markPublished({ id: entry.id, fence: validLease.fence, publishedAt: at(0) }), stateDiagnostic("publish_outbox", "record", "not-found"));
  accepted(await observedOutbox.create(entry));
  rejection(await observedOutbox.create(entry), stateDiagnostic("create_outbox", "record", "duplicate"));
  rejection(await observedOutbox.listDeliverable({ asOf: at(0), limit: 0 }), stateDiagnostic("list_outbox", "limit", "not-positive"));
  rejection(await observedOutbox.listDeliverable({ asOf: at(0), limit: 1.5 }), stateDiagnostic("list_outbox", "limit", "not-integer"));
  rejection(await observedOutbox.markPublished({ id: entry.id, fence: validLease.fence, publishedAt: at(0) }), stateDiagnostic("publish_outbox", "state", "wrong-state"));
  accepted(await observedOutbox.claim({ id: entry.id, owner: relayA, acquiredAt: at(0), leaseDurationMs: 10 }));
  rejection(await observedOutbox.markPublished({ id: entry.id, fence: accepted(platformPersistenceFence(2)), publishedAt: at(10) }), stateDiagnostic("publish_outbox", "fence", "stale"));
  rejection(await observedOutbox.markPublished({ id: entry.id, fence: validLease.fence, publishedAt: at(10) }), stateDiagnostic("publish_outbox", "lease", "expired"));
  accepted(await observedOutbox.markPublished({ id: entry.id, fence: validLease.fence, publishedAt: at(1) }));
  const beforeDuplicates = observations.length;
  equal(accepted(await observedOutbox.claim({ id: entry.id, owner: relayA, acquiredAt: at(0), leaseDurationMs: 0 })).disposition, "already-published");
  accepted(await observedOutbox.markPublished({ id: entry.id, fence: accepted(platformPersistenceFence(2)), publishedAt: at(99) }));
  equal(observations.length, beforeDuplicates, "successful duplicate dispositions must remain quiet and precede validation");
  const observedProcessing = createInMemoryPlatformProcessingStore({ onDiagnostic(record) { observations.push(record); } });
  const processingInput = { outboxEntryId: entry.id, fence: validLease.fence, outcome: "succeeded" as const, completedAt: at(1), releasedAt: at(1) };
  rejection(await observedProcessing.complete(processingInput), stateDiagnostic("complete_processing", "record", "not-found"));
  rejection(await observedProcessing.release(processingInput), stateDiagnostic("release_processing", "record", "not-found"));
  accepted(await observedProcessing.claim({ outboxEntryId: entry.id, owner: relayA, acquiredAt: at(0), leaseDurationMs: 10 }));
  for (const [method, operation] of [["complete", "complete_processing"], ["release", "release_processing"]] as const) {
    rejection(await observedProcessing[method]({ ...processingInput, fence: accepted(platformPersistenceFence(2)), completedAt: at(10), releasedAt: at(10) }), stateDiagnostic(operation, "fence", "stale"));
    rejection(await observedProcessing[method]({ ...processingInput, completedAt: at(10), releasedAt: at(10) }), stateDiagnostic(operation, "lease", "expired"));
  }
  accepted(await observedProcessing.release(processingInput));
  rejection(await observedProcessing.complete(processingInput), stateDiagnostic("complete_processing", "state", "wrong-state"));
  rejection(await observedProcessing.release(processingInput), stateDiagnostic("release_processing", "state", "wrong-state"));
  deepEqual(observations[0], stateDiagnostic("claim_outbox", "record", "not-found"));
  await new Promise<void>((resolve) => setImmediate(resolve));
  equal(JSON.stringify(observations).includes("CANARY"), false);
  const storedDetail = { operation: "read_outbox", reduction: "null", effect: "not-assessed", issues: [{ field: "lease", condition: "partial", ordinal: 0 }], truncated: false } as const;
  deepEqual(persistenceStoredRecordDiagnosticRecord(storedDetail), { schema: "core/diagnostic-record/v1", code: "persistence.stored-record-observed", definitionVersion: 1, detail: storedDetail });
  equal(createDiagnosticRecord(persistenceStoredRecordDiagnostic, { ...storedDetail, issues: Array(17).fill(storedDetail.issues[0]) }).ok, false);
  equal(createDiagnosticRecord<unknown>(persistenceStoredRecordDiagnostic, { ...storedDetail, truncated: undefined }).ok, false);
  equal(createDiagnosticRecord<unknown>(persistenceLocalRejectionDiagnostic, { operation: "validate-lease", field: "owner", condition: "PRIVATE CANARY", phase: "validation", effect: "not-started" }).ok, false);
  const boundaryDetail = { operation: "transaction", phase: "completion", boundary: "release", condition: "threw", effect: "commit-completed" } as const;
  deepEqual(persistenceBoundaryDiagnosticRecord(boundaryDetail), { schema: "core/diagnostic-record/v1", code: "persistence.boundary-observed", definitionVersion: 1, detail: boundaryDetail });
  const manifestDetail = { operation: "migration", field: "manifest", condition: "predicate-rejected", phase: "preflight", effect: "not-started" } as const;
  deepEqual(persistenceLocalRejectionDiagnosticRecord(manifestDetail), { schema: "core/diagnostic-record/v1", code: "persistence.local-rejected", definitionVersion: 1, detail: manifestDetail });
  const decodeDetail = { operation: "read_outbox", phase: "invocation", boundary: "decode", condition: "threw", effect: "not-assessed" } as const;
  deepEqual(persistenceBoundaryDiagnosticRecord(decodeDetail), { schema: "core/diagnostic-record/v1", code: "persistence.boundary-observed", definitionVersion: 1, detail: decodeDetail });
  const fallbackDetail = { operation: "publish_outbox", phase: "returned-result", boundary: "reconciliation", condition: "returned-failure", effect: "unknown", reconciliation: "lease-present-fence-matched" } as const;
  deepEqual(persistenceBoundaryDiagnosticRecord(fallbackDetail), { schema: "core/diagnostic-record/v1", code: "persistence.boundary-observed", definitionVersion: 1, detail: fallbackDetail });
  deepEqual(persistenceBoundaryDiagnostic.classification, { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false });
  for (const invalid of [{ ...fallbackDetail, reconciliation: "lease-expired" }, { ...fallbackDetail, condition: "expired" }, { ...fallbackDetail, effect: "lease-expired" }, { ...fallbackDetail, expiresAt: "private-expiry-canary" }]) {
    equal(createDiagnosticRecord<unknown>(persistenceBoundaryDiagnostic, invalid).ok, false);
  }
  for (const operation of ["create", "read", "delete"] as const) for (const boundary of ["primary", "reconciliation"] as const) {
    deepEqual(persistenceCrudObservedDiagnosticRecord({ classification: "timeout", phase: "query", code_status: "recognized" }, operation, boundary), {
      schema: "core/diagnostic-record/v1", code: "persistence.operation-timed-out", definitionVersion: 3,
      detail: { phase: "query", classification: "timeout", codeStatus: "recognized", operation, boundary, effect: operation === "read" ? "not-assessed" : "unknown" },
    });
  }
  equal(persistenceObservedDiagnosticRecord({ classification: "timeout", phase: "query", code_status: "recognized" }, "write_facts").definitionVersion, 2);
  for (const definition of persistenceDiagnosticDefinitions) equal(definition.version, 1);
  for (const definition of persistenceCurrentDiagnosticDefinitions) equal(definition.version, 2);
  const historicalOperations = ["connect", "readiness", "transaction", "migration", "create_outbox", "write_facts", "write_atomic", "read_outbox", "list_outbox", "claim_outbox", "publish_outbox", "read_processing", "claim_processing", "complete_processing", "release_processing", "append_lineage", "read_lineage"];
  for (const [definitions, expectedOperations] of [[persistenceDiagnosticDefinitions, historicalOperations], [persistenceCurrentDiagnosticDefinitions, [...historicalOperations, "administration", "restore_verification"]]] as const) {
    for (const definition of definitions) {
      if (definition.detail.type !== "object" || definition.detail.properties["operation"]?.type !== "enum") throw new Error("Expected operation enum");
      deepEqual(definition.detail.properties["operation"].values, expectedOperations);
    }
  }
  for (const definition of persistenceCrudDiagnosticDefinitions) {
    equal(createDiagnosticRecord<unknown>(definition, { phase: "query", classification: "timeout", codeStatus: "recognized", operation: "create", boundary: "primary", effect: "not-started" }).ok, false);
  }
  deepEqual(persistenceCrudDiagnosticDefinitions.find((definition) => definition.code === "persistence.unclassified-failure")?.classification,
    { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false });
  deepEqual(persistenceReconciliationDiagnostic.classification, { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none", retryable: false, userCorrectable: false });
  for (const primaryOutcome of ["no-row-returned", "call-threw"] as const) for (const observed of ["matching", "different", "absent", "unavailable"] as const) {
    const detail = { operation: "create", primaryOutcome, observed, effect: "read-result-observed" } as const;
    deepEqual(persistenceReconciliationDiagnosticRecord(detail), { schema: "core/diagnostic-record/v1", code: "persistence.reconciliation-observed", definitionVersion: 1, detail });
    for (const invalid of [{ ...detail, effect: "created" }, { ...detail, observed: "rejected" }, { ...detail, operation: "write_facts" }, { ...detail, id: "private-record-canary" }, { ...detail, primaryOutcome: "provider-rejected" }]) {
      equal(createDiagnosticRecord<unknown>(persistenceReconciliationDiagnostic, invalid).ok, false);
    }
  }
  for (const [condition, specificCode] of [
    ["access-rejected", "persistence.runtime-permission-denied"], ["identity-unrecognized", "persistence.credential-rejected"],
    ["credential-expired", "persistence.credential-rejected"], ["network-failure", "persistence.transport-unavailable"],
    ["timeout", "persistence.operation-timed-out"], ["condition-rejected", "persistence.command-condition-observed"],
    ["transaction-canceled", "persistence.unclassified-failure"], ["resource-unavailable", "persistence.unclassified-failure"],
    ["input-rejected", "persistence.unclassified-failure"], ["throughput-exceeded", "persistence.unclassified-failure"],
    ["request-limit-exceeded", "persistence.unclassified-failure"], ["throttled", "persistence.unclassified-failure"], ["unclassified", "persistence.unclassified-failure"],
  ] as const) for (const boundary of ["client-construction", "selection", "encoding", "invocation", "response", "decoding", "callback"] as const) {
    const detail = { operation: "write_atomic", boundary, role: "primary", condition, codeStatus: "recognized", effect: "unknown" } as const;
    deepEqual(persistenceCommandDiagnosticRecord(detail), { schema: "core/diagnostic-record/v1", code: boundary === "invocation" ? specificCode : "persistence.unclassified-failure",
      definitionVersion: boundary === "invocation" && condition === "condition-rejected" ? 1 : 4, detail });
  }
  for (const codeStatus of ["not-inspected", "absent", "wrong-type", "unavailable", "unrecognized"] as const) {
    equal(persistenceCommandDiagnosticRecord({ operation: "read_outbox", boundary: "invocation", role: "reconciliation", condition: "access-rejected", codeStatus, effect: "not-assessed" }).code, "persistence.unclassified-failure");
    equal(persistenceCommandDiagnosticRecord({ operation: "claim_outbox", boundary: "invocation", role: "primary", condition: "condition-rejected", codeStatus, effect: "unknown" }).code, "persistence.unclassified-failure");
  }
  deepEqual(persistenceCommandConditionDiagnostic.classification, { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none", retryable: false, userCorrectable: false });
  for (const role of ["primary", "reconciliation"] as const) {
    const detail = { operation: "create_outbox", boundary: "invocation", role, condition: "condition-rejected", codeStatus: "recognized", effect: "unknown" } as const;
    deepEqual(persistenceCommandDiagnosticRecord(detail), { schema: "core/diagnostic-record/v1", code: "persistence.command-condition-observed", definitionVersion: 1, detail });
    equal(createDiagnosticRecord<unknown>(persistenceCommandConditionDiagnostic, { ...detail, nativeMessage: "conditional-native-canary" }).ok, false);
  }
  deepEqual(persistenceCommandDiagnosticDefinitions.map((definition) => [definition.code, definition.version]), [
    ["persistence.credential-rejected", 4], ["persistence.runtime-permission-denied", 4], ["persistence.transport-unavailable", 4], ["persistence.operation-timed-out", 4], ["persistence.unclassified-failure", 4],
  ]);
  const commandDefinition = persistenceCommandDiagnosticDefinitions.find((definition) => definition.code === "persistence.unclassified-failure")!;
  equal(commandDefinition.classification.failureSource, "unknown");
  const cancellationDetail = { operation: "write_atomic", boundary: "invocation", role: "primary", condition: "transaction-canceled", codeStatus: "recognized", effect: "unknown",
    cancellation: { availability: "available", truncated: true, reasons: Array.from({ length: 64 }, (_value, ordinal) => ({ ordinal, codeStatus: "recognized", condition: "condition-rejected" } as const)) } } as const;
  deepEqual(persistenceCommandDiagnosticRecord(cancellationDetail), { schema: "core/diagnostic-record/v1", code: "persistence.unclassified-failure", definitionVersion: 4, detail: cancellationDetail });
  for (const invalid of [{ ...cancellationDetail, cancellation: { ...cancellationDetail.cancellation, reasons: Array(65).fill(cancellationDetail.cancellation.reasons[0]) } },
    { ...cancellationDetail, cancellation: { ...cancellationDetail.cancellation, truncated: undefined } }, { ...cancellationDetail, nativeMessage: "private-native-canary" }, { ...cancellationDetail, operation: "target-acceptance" }]) {
    equal(createDiagnosticRecord<unknown>(commandDefinition, invalid).ok, false);
  }
  const attributeDetail = { operation: "read_lineage", reduction: "filtered", effect: "not-assessed", issues: [{ field: "actor", condition: "incomplete", rowOrdinal: 1, attributeOrdinal: 0, count: 2 }], truncated: true } as const;
  deepEqual(persistenceStoredAttributeDiagnosticRecord(attributeDetail), { schema: "core/diagnostic-record/v1", code: "persistence.stored-attribute-observed", definitionVersion: 1, detail: attributeDetail });
  for (const invalid of [{ ...attributeDetail, issues: Array(17).fill(attributeDetail.issues[0]) }, { ...attributeDetail, truncated: undefined },
    { ...attributeDetail, issues: [{ field: "tableName", condition: "absent" }] }, { ...attributeDetail, issues: [{ ...attributeDetail.issues[0], value: "private-attribute-canary" }] }]) {
    equal(createDiagnosticRecord<unknown>(persistenceStoredAttributeDiagnostic, invalid).ok, false);
  }
  for (const operation of ["claim_outbox", "publish_outbox", "claim_processing", "complete_processing", "release_processing"] as const) {
    for (const observed of ["missing", "already-published", "lease-active", "already-completed", "valid-current-state", "unresolved", "unavailable"] as const) {
      const detail = { operation, primaryOutcome: "condition-rejected", observed, effect: "read-result-observed" } as const;
      deepEqual(persistenceStateReconciliationDiagnosticRecord(detail), { schema: "core/diagnostic-record/v1", code: "persistence.reconciliation-observed", definitionVersion: 2, detail });
      equal(createDiagnosticRecord<unknown>(persistenceStateReconciliationDiagnostic, { ...detail, effect: "write-confirmed" }).ok, false);
    }
  }
  const defaultRecords: DiagnosticRecord[] = []; const invocationRecords: DiagnosticRecord[] = [];
  const defaults = { get pool(): never { throw new Error("Do not spread legacy options"); }, diagnosticDefinitions: [persistenceLocalRejectionDiagnostic],
    onDiagnostic(this: unknown, record: DiagnosticRecord) { equal(this, defaults); defaultRecords.push(record); return Promise.reject("default-sink-canary"); } };
  const invocation = { diagnosticDefinitions: [persistenceStoredAttributeDiagnostic], onDiagnostic(this: unknown, record: DiagnosticRecord) { equal(this, invocation); invocationRecords.push(record); return "written"; } };
  const omitted = resolvePlatformPersistenceDiagnosticOptions(defaults);
  equal(omitted, defaults, "omission preserves the original defaults identity without reading diagnostic properties");
  let omittedGetterReads = 0;
  const untouchedDefaults = { get diagnosticDefinitions(): never { omittedGetterReads++; throw "default-getter-canary"; }, get onDiagnostic(): never { omittedGetterReads++; throw "default-observer-canary"; } };
  equal(resolvePlatformPersistenceDiagnosticOptions(untouchedDefaults), untouchedDefaults);
  equal(omittedGetterReads, 0);
  const silenced = resolvePlatformPersistenceDiagnosticOptions(defaults, {});
  const replaced = resolvePlatformPersistenceDiagnosticOptions(defaults, invocation);
  const ownLocation = persistenceBoundaryDiagnosticRecord(boundaryDetail);
  observePlatformPersistenceDiagnostic(omitted, ownLocation);
  observePlatformPersistenceDiagnostic(silenced, ownLocation);
  observePlatformPersistenceDiagnostic(replaced, ownLocation);
  deepEqual(defaultRecords, [ownLocation]); deepEqual(invocationRecords, [ownLocation]);
  deepEqual(replaced.diagnosticDefinitions, [persistenceLocalRejectionDiagnostic, persistenceStoredAttributeDiagnostic]);
  const unavailableDefinitions = { get diagnosticDefinitions(): never { throw "definitions-canary"; }, get onDiagnostic(): never { throw "callback-getter-canary"; } };
  const unavailable = resolvePlatformPersistenceDiagnosticOptions(unavailableDefinitions, unavailableDefinitions);
  deepEqual(unavailable.diagnosticDefinitions, []);
  unavailable.onDiagnostic?.(ownLocation);
  await new Promise<void>((resolve) => setImmediate(resolve));
  await relayDiagnosticProof(entry, at, relayA);
}

async function relayDiagnosticProof(entry: OutboxEntry, at: (milliseconds: number) => ISODateTime, owner: PlatformPersistenceLeaseOwner): Promise<void> {
  const own = (boundary: string, effect: string, reason = "threw", operation = "run-once") => ({ schema: "core/diagnostic-record/v1", code: "persistence.relay-boundary-observed", definitionVersion: 1,
    detail: { operation, boundary, reason, effect } });
  const sourceDefinition = defineDiagnostic({ code: "fixture.relay-source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } },
  } as const);
  const sources = Array.from({ length: 9 }, (_value, ordinal) => accepted(createDiagnosticRecord(sourceDefinition, { ordinal })));
  const raw = Object.freeze(Object.assign(new Error("private-relay-boundary-canary"), { diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) }));
  const lease = accepted(nextPlatformPersistenceLease({ owner, priorAttempt: accepted(platformPersistenceAttempt(0)), acquiredAt: at(0), durationMs: 1000 }));
  for (const [phase, expectedEffect, expectedCalls] of [
    ["claim-clock", "relay-send-not-invoked", ["claim-clock"]],
    ["claim-time-normalization", "relay-send-not-invoked", ["claim-clock", "claim-time-normalization"]],
    ["list-deliverable", "relay-send-not-invoked", ["claim-clock", "list-deliverable"]],
    ["candidate-selection", "relay-send-not-invoked", ["claim-clock", "list-deliverable", "candidate-selection"]],
    ["claim", "relay-send-not-invoked", ["claim-clock", "list-deliverable", "claim"]],
    ["envelope-construction", "relay-send-not-invoked", ["claim-clock", "list-deliverable", "claim", "envelope-construction"]],
    ["queue-send", "send-outcome-unknown", ["claim-clock", "list-deliverable", "claim", "queue-send"]],
    ["publication-clock", "send-success-marker-not-invoked", ["claim-clock", "list-deliverable", "claim", "queue-send", "publication-clock"]],
    ["publication-time-normalization", "send-success-marker-not-invoked", ["claim-clock", "list-deliverable", "claim", "queue-send", "publication-clock", "publication-time-normalization"]],
    ["publish-marker", "send-success-marker-outcome-unknown", ["claim-clock", "list-deliverable", "claim", "queue-send", "publication-clock", "publish-marker"]],
    ["result-projection", "marker-success-returned", ["claim-clock", "list-deliverable", "claim", "queue-send", "publication-clock", "publish-marker", "result-projection"]],
  ] as const) {
    const calls: string[] = [], delivered: DiagnosticRecord[] = [], roles: unknown[] = [];
    let clocks = 0, markerReturned = false;
    const step = (name: string): void => { calls.push(name); if (phase === name) throw raw; };
    const record = platformOutboxRecord({ entry, state: "leased", lease, attempt: lease.attempt });
    if (phase === "envelope-construction") Object.defineProperty(record.entry, "messageType", { get() { step("envelope-construction"); return entry.messageType; } });
    if (phase === "result-projection") Object.defineProperty(record, "attempt", { get() { step("result-projection"); return lease.attempt; } });
    const outbox: PlatformOutboxStore = {
      async create() { throw new Error("Unexpected create"); }, async get() { throw new Error("Unexpected get"); },
      async listDeliverable() { equal(this, outbox); step("list-deliverable"); const records = [record];
        if (phase === "candidate-selection") Object.defineProperty(records, "0", { get() { step("candidate-selection"); return record; } });
        return ok(records); },
      async claim() { equal(this, outbox); step("claim"); return ok({ disposition: "claimed", record }); },
      async markPublished() { equal(this, outbox); step("publish-marker"); markerReturned = true; return ok(record); },
    };
    const queue: Queue<PlatformOutboxQueuePayload> = { async send() { equal(this, queue); step("queue-send"); return ok(undefined); } };
    const clock = { now() { equal(this, clock); const prefix = ++clocks === 1 ? "claim" : "publication"; step(`${prefix}-clock`);
      const date = new Date("2026-09-23T12:00:00.000Z");
      if (phase === `${prefix}-time-normalization`) Object.defineProperty(date, "toISOString", { value() { equal(this, date); step(`${prefix}-time-normalization`); return at(0); } });
      return date; } };
    const observer: PlatformPersistenceObserver = { record() { equal(this, observer); }, onDiagnostic(record, operation) { equal(this, observer); delivered.push(record); roles.push(operation); } };
    await rejects(createPlatformOutboxRelay({ outbox, queue, clock, owner, leaseDurationMs: 1000, observer, diagnosticDefinitions: [sourceDefinition] }).runOnce(), (error: unknown) => error === raw);
    deepEqual(delivered, [own(phase, expectedEffect), ...sources]);
    deepEqual(roles, Array(10).fill("relay")); deepEqual(calls, expectedCalls);
    equal(markerReturned, phase === "result-projection");
    equal(JSON.stringify(delivered).includes("canary"), false);
  }
  for (const failed of ["list-deliverable", "claim", "queue-send", "publish-marker"] as const) {
    const observations: PlatformPersistenceObservation[] = [], rawObservations: DiagnosticRecord[] = [], calls: string[] = [];
    const sourceError = platformPersistenceError({ code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: "Original returned failure", diagnosticRecord: sources[0]!, relatedDiagnosticRecords: sources.slice(1), relatedDiagnosticDefinitions: [sourceDefinition] });
    const failure = { ok: false as const, error: sourceError };
    const queueSource = queueError({ code: "QUEUE_UNAVAILABLE", defaultMessage: "Original send failure", diagnosticRecord: sources[0]!, relatedDiagnosticRecords: sources.slice(1) });
    const record = platformOutboxRecord({ entry, state: "leased", lease, attempt: lease.attempt });
    const outbox: PlatformOutboxStore = {
      async create() { throw new Error("Unexpected create"); }, async get() { throw new Error("Unexpected get"); },
      async listDeliverable() { calls.push("list"); return failed === "list-deliverable" ? failure : ok([record]); },
      async claim() { calls.push("claim"); return failed === "claim" ? failure : ok({ disposition: "claimed", record }); },
      async markPublished() { calls.push("marker"); return failed === "publish-marker" ? failure : ok(record); },
    };
    const queue: Queue<PlatformOutboxQueuePayload> = { async send() { calls.push("send"); return failed === "queue-send" ? { ok: false, error: queueSource } : ok(undefined); } };
    const result = await createPlatformOutboxRelay({ outbox, queue, owner, leaseDurationMs: 1000, clock: { now: () => new Date(at(0)) },
      observer: { record(observation) { observations.push(observation); }, onDiagnostic(record) { rawObservations.push(record); } } }).runOnce();
    const expectedEffect = failed === "queue-send" ? "send-outcome-unknown" : failed === "publish-marker" ? "send-success-marker-outcome-unknown" : "relay-send-not-invoked";
    deepEqual(observations.at(-1)?.diagnosticRecord, own(failed, expectedEffect, "returned-failure"));
    equal(observations.at(-1)?.error, failed === "queue-send" ? queueSource : sourceError); deepEqual(rawObservations, []);
    if (failed === "list-deliverable" || failed === "claim") equal(result, failure);
    else { equal(result.ok, true); if (!result.ok) throw new Error("Expected retained relay status"); equal(result.value.status, failed === "queue-send" ? "queue-send-failed" : "publish-marker-failed"); }
    deepEqual(calls, failed === "list-deliverable" ? ["list"] : failed === "claim" ? ["list", "claim"] : failed === "queue-send" ? ["list", "claim", "send"] : ["list", "claim", "send", "marker"]);
  }
  for (const disposition of ["claimed", "already-published", "lease-active", "empty"] as const) {
    const observations: PlatformPersistenceObservation[] = [], rawObservations: DiagnosticRecord[] = [];
    let sends = 0;
    const record = platformOutboxRecord({ entry, state: "leased", attempt: lease.attempt });
    const outbox: PlatformOutboxStore = { async create() { throw new Error("Unexpected create"); }, async get() { throw new Error("Unexpected get"); },
      async listDeliverable() { return ok(disposition === "empty" ? [] : [record]); }, async claim() { return ok({ disposition: disposition === "empty" ? "claimed" : disposition, record }); },
      async markPublished() { throw new Error("Unexpected marker"); } };
    const result = await createPlatformOutboxRelay({ outbox, queue: { async send() { sends++; return ok(undefined); } }, owner, leaseDurationMs: 1000,
      clock: { now: () => new Date(at(0)) }, observer: { record(observation) { observations.push(observation); }, onDiagnostic(record) { rawObservations.push(record); } } }).runOnce();
    equal(sends, 0); deepEqual(rawObservations, []);
    if (disposition === "claimed") {
      equal(result.ok, false); if (result.ok) throw new Error("Expected missing lease rejection");
      equal(result.error.code, "PLATFORM_PERSISTENCE_OUTBOX_NOT_LEASED");
      deepEqual(result.error.diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "persistence.local-rejected", definitionVersion: 1,
        detail: { operation: "claim_outbox", field: "lease", condition: "absent", phase: "state-check", effect: "unknown" } });
      deepEqual(observations.at(-1)?.diagnosticRecord, result.error.diagnosticRecord);
      equal(observations.at(-1)?.error, undefined, "Missing lease must not change legacy transition error-class population");
    } else {
      equal(result.ok, true); if (!result.ok) throw new Error("Expected ordinary coordination result");
      equal(result.value.status, disposition === "lease-active" ? "contended" : "idle");
      equal(observations.every((observation) => observation.diagnosticRecord === undefined && observation.error === undefined), true);
    }
  }
  const reads: string[] = [];
  const record = platformOutboxRecord({ entry, state: "leased", lease, attempt: lease.attempt });
  const outbox: PlatformOutboxStore = { async create() { throw new Error("Unexpected create"); }, async get() { throw new Error("Unexpected get"); },
    async listDeliverable() { equal(this, outbox); reads.push("invoke-list"); return ok([record]); },
    async claim() { equal(this, outbox); reads.push("invoke-claim"); return ok({ disposition: "claimed", record }); },
    async markPublished() { equal(this, outbox); reads.push("invoke-marker"); return ok(record); } };
  for (const method of ["listDeliverable", "claim", "markPublished"] as const) {
    const original = outbox[method]; Object.defineProperty(outbox, method, { get() { reads.push(`select-${method}`); return original; } });
  }
  const queue: Queue<PlatformOutboxQueuePayload> = { async send() { equal(this, queue); reads.push("invoke-send"); return ok(undefined); } };
  const originalSend = queue.send; Object.defineProperty(queue, "send", { get() { reads.push("select-send"); return originalSend; } });
  const clock = { now() { equal(this, clock); reads.push("invoke-clock"); return new Date(at(0)); } };
  equal(accepted(await createPlatformOutboxRelay({ get outbox() { reads.push("select-outbox"); return outbox; },
    get queue() { reads.push("select-queue"); return queue; }, get clock() { reads.push("select-clock"); return clock; },
    get owner() { reads.push("owner"); return owner; }, get leaseDurationMs() { reads.push("duration"); return 1000; } }).runOnce()).status, "published");
  deepEqual(reads, ["duration", "select-clock", "invoke-clock", "select-outbox", "select-listDeliverable", "invoke-list", "select-outbox", "select-claim", "owner", "invoke-claim",
    "select-queue", "select-send", "invoke-send", "select-clock", "invoke-clock", "select-outbox", "select-markPublished", "invoke-marker"]);
  for (const thrown of [undefined, "primitive-relay-canary", Object.freeze(new Error("frozen-relay-canary"))]) {
    const delivered: DiagnosticRecord[] = [];
    const failing = { ...outbox, async listDeliverable() { throw thrown; } };
    await rejects(createPlatformOutboxRelay({ outbox: failing, queue, clock, owner, leaseDurationMs: 1000,
      observer: { record() { throw new Error("No synthetic transition for raw failure"); }, onDiagnostic(record) { delivered.push(record); throw "sink-private-canary"; } } }).runOnce(), (error: unknown) => error === thrown);
    deepEqual(delivered, [own("list-deliverable", "relay-send-not-invoked")]);
  }
  const mappingRecords: DiagnosticRecord[] = [], validatorCalls: string[] = [];
  const typeDescriptor = Object.getOwnPropertyDescriptor(coreQueue, "queueMessageType")!, versionDescriptor = Object.getOwnPropertyDescriptor(coreQueue, "queueMessageVersion")!;
  const originalType = coreQueue.queueMessageType, originalVersion = coreQueue.queueMessageVersion;
  try {
    Object.defineProperty(coreQueue, "queueMessageType", { ...typeDescriptor, value(value: string) { validatorCalls.push("type"); return originalType(value); } });
    Object.defineProperty(coreQueue, "queueMessageVersion", { ...versionDescriptor, value(value: number) { validatorCalls.push("version"); return originalVersion(value); } });
    const invalid = platformOutboxQueueMessage({ ...entry, messageType: "INVALID" as typeof entry.messageType, messageVersion: 1.5 as typeof entry.messageVersion }, at(0), { onDiagnostic(record) { mappingRecords.push(record); } });
    equal(invalid.ok, false); if (invalid.ok) throw new Error("Expected mapping rejection");
    equal(invalid.error.code, "PLATFORM_PERSISTENCE_QUEUE_MAPPING_INVALID");
    const first = { schema: "core/diagnostic-record/v1", code: "core.queue.validation-rejected", definitionVersion: 1, detail: { operation: "validate", field: "message-type", reason: "invalid-format", effect: "rejected" } };
    const second = { schema: "core/diagnostic-record/v1", code: "core.queue.validation-rejected", definitionVersion: 1, detail: { operation: "validate", field: "message-version", reason: "not-integer", effect: "rejected" } };
    deepEqual(invalid.error.diagnosticRecord, first); deepEqual(invalid.error.relatedDiagnosticRecords, [second]);
    deepEqual(mappingRecords, [own("envelope-construction", "relay-send-not-invoked", "returned-failure", "queue-message"), first, second]);
    deepEqual(validatorCalls, ["type", "version"]);
    validatorCalls.length = 0;
    equal(platformOutboxQueueMessage(entry, at(0)).ok, true); deepEqual(validatorCalls, ["type", "version"]);
  } finally {
    Object.defineProperty(coreQueue, "queueMessageType", typeDescriptor); Object.defineProperty(coreQueue, "queueMessageVersion", versionDescriptor);
  }
  const direct: DiagnosticRecord[] = [];
  throws(() => platformOutboxQueueMessage({ ...entry, get messageType(): typeof entry.messageType { throw raw; } }, at(0), { diagnosticDefinitions: [sourceDefinition], onDiagnostic(record) { direct.push(record); } }), (error: unknown) => error === raw);
  deepEqual(direct, [own("envelope-construction", "relay-send-not-invoked", "threw", "queue-message"), ...sources]);
  const detail = { operation: "run-once", boundary: "publish-marker", reason: "returned-failure", effect: "send-success-marker-outcome-unknown" } as const;
  deepEqual(persistenceRelayBoundaryDiagnosticRecord(detail), own("publish-marker", "send-success-marker-outcome-unknown", "returned-failure"));
  for (const invalid of [{ ...detail, effect: "queue-not-accepted" }, { ...detail, provider: "native-canary" }, { ...detail, reason: "duplicate" }]) {
    equal(createDiagnosticRecord<unknown>(persistenceRelayBoundaryDiagnostic, invalid).ok, false);
  }
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
