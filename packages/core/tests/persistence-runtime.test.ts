import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import {
  concurrencyToken,
  inMemoryRepository,
  inMemoryUnitOfWork,
  isRecordLifecycleActive,
  logicallyDeleteRecord,
  outboxDeliveryPolicy,
  outboxEntry,
  outboxEntryId,
  outboxMessageType,
  outboxMessageVersion,
  page,
  pageRequest,
  pageTotal,
  pageTotals,
  persistenceError,
  recordChange,
  recordChangeActor,
  recordChangeFieldName,
  recordChangeId,
  recordId,
  recordKind,
  recordReference,
  recordRevision,
  recordLifecyclePolicy,
  recordPurgeEligibility,
  recordRetentionPolicyReference,
  restoreLogicallyDeletedRecord,
  activeRecordLifecycle,
  type ConcurrencyToken,
  type Transaction,
  type InMemoryRepositoryOptions,
  corePersistenceValidationDiagnostic,
} from "../src/persistence/index";
import { createDiagnosticRecord, defineDiagnostic, diagnosticDescriptor, diagnosticRelatedRecordLimit, type DiagnosticRecord } from "../src/diagnostics/index";
import { coreDiagnosticCatalog } from "../src/diagnostic-catalog";
import { brand, causationId, entityId, isErr, isOk, isoDateTimeFromDate, type EntityId } from "../src/shared/index";
import { permission } from "../src/authz/index";

type DealId = EntityId<"DealId">;

interface DealRecord {
  readonly id: DealId;
  readonly name: string;
  readonly concurrencyToken: ConcurrencyToken;
  readonly tags: string[];
}

const dealId = entityId<"DealId">("deal-123");
const firstVersion = concurrencyToken("deal-123:v1");
const secondVersion = concurrencyToken("deal-123:v2");
const thirdVersion = concurrencyToken("deal-123:v3");

async function main(): Promise<void> {
  const validPageRequest = pageRequest({ limit: 25, cursor: "cursor-1" });
  equal(isOk(validPageRequest), true);
  if (!isOk(validPageRequest)) {
    throw new Error("Expected valid page request.");
  }
  deepEqual(validPageRequest.value, { limit: 25, cursor: "cursor-1" });

  const invalidLimit = pageRequest({ limit: 0 });
  equal(isErr(invalidLimit), true);
  if (!isErr(invalidLimit)) {
    throw new Error("Expected invalid page request.");
  }
  equal(invalidLimit.error.code, "PERSISTENCE_INVALID_PAGE_REQUEST");
  equal(invalidLimit.error.messageKey, "persistence.page_request.invalid_limit");

  const invalidCursor = pageRequest({ limit: 10, cursor: "" });
  equal(isErr(invalidCursor), true);
  if (!isErr(invalidCursor)) {
    throw new Error("Expected invalid cursor.");
  }
  equal(invalidCursor.error.code, "PERSISTENCE_INVALID_PAGE_REQUEST");
  equal(invalidCursor.error.messageKey, "persistence.page_request.invalid_cursor");

  const firstPage = page({ items: ["deal-1", "deal-2"], nextCursor: "cursor-2" });
  deepEqual(firstPage, { items: ["deal-1", "deal-2"], nextCursor: "cursor-2" });

  const totalItems = pageTotal(100);
  equal(isOk(totalItems), true);
  if (!isOk(totalItems)) {
    throw new Error("Expected page total to be valid.");
  }
  equal(totalItems.value, 100);

  const invalidTotal = pageTotal(-1);
  equal(isErr(invalidTotal), true);
  if (!isErr(invalidTotal)) {
    throw new Error("Expected negative page total to fail.");
  }
  equal(invalidTotal.error.code, "PERSISTENCE_INVALID_PAGE");

  const totals = pageTotals({ totalItems: 100, totalMatchingItems: 12 });
  equal(isOk(totals), true);
  if (!isOk(totals)) {
    throw new Error("Expected page totals to be valid.");
  }
  deepEqual(totals.value, { totalItems: 100, totalMatchingItems: 12 });

  const invalidTotals = pageTotals({ totalItems: 10, totalMatchingItems: 11 });
  equal(isErr(invalidTotals), true);
  if (!isErr(invalidTotals)) {
    throw new Error("Expected invalid page totals to fail.");
  }
  equal(invalidTotals.error.messageKey, "persistence.page.invalid_total_relationship");

  const pageWithTotals = page({ items: ["deal-1"], totals: totals.value });
  deepEqual(pageWithTotals, {
    items: ["deal-1"],
    totals: { totalItems: 100, totalMatchingItems: 12 },
  });

  const items = ["deal-1"];
  const copiedPage = page({ items });
  items.push("deal-2");
  deepEqual(copiedPage.items, ["deal-1"]);

  const explicitError = persistenceError({
    code: "PERSISTENCE_TIMEOUT",
    defaultMessage: "Storage operation timed out.",
    messageKey: "persistence.timeout",
    diagnostic: diagnosticDescriptor({
      failureKind: "timeout",
      failureSource: "provider",
      severity: "error",
      recovery: "automation_retryable",
      action: "retry",
    }),
  });
  equal(explicitError.code, "PERSISTENCE_TIMEOUT");
  equal(explicitError.messageKey, "persistence.timeout");
  equal(explicitError.diagnostic?.retryable, true);

  const recordedAt = isoDateTimeFromDate(new Date("2026-09-23T12:00:00.000Z"));
  const retentionReference = recordRetentionPolicyReference("platform-smoke.work-item-retention.v1");
  equal(isOk(retentionReference), true);
  if (!isOk(retentionReference)) {
    throw new Error("Expected a valid logical-record retention reference.");
  }
  const lifecyclePolicy = recordLifecyclePolicy({
    recoveryWindowMs: 60_000,
    retentionPolicy: retentionReference.value,
    legalHoldCheckRequired: true,
  });
  equal(isOk(lifecyclePolicy), true);
  if (!isOk(lifecyclePolicy)) {
    throw new Error("Expected a valid logical-record lifecycle policy.");
  }
  const deletedLifecycle = logicallyDeleteRecord({
    current: activeRecordLifecycle(),
    deletedAt: recordedAt,
    policy: lifecyclePolicy.value,
  });
  equal(isOk(deletedLifecycle), true);
  if (!isOk(deletedLifecycle)) {
    throw new Error("Expected logical deletion to succeed for an active record.");
  }
  equal(isRecordLifecycleActive(deletedLifecycle.value), false);
  equal(deletedLifecycle.value.state, "deleted");
  if (deletedLifecycle.value.state !== "deleted") {
    throw new Error("Expected logical deletion to retain deletion facts.");
  }
  equal(deletedLifecycle.value.retentionPolicy, retentionReference.value);
  const repeatedDeletion = logicallyDeleteRecord({
    current: deletedLifecycle.value,
    deletedAt: recordedAt,
    policy: lifecyclePolicy.value,
  });
  equal(isErr(repeatedDeletion), true);
  if (!isErr(repeatedDeletion)) {
    throw new Error("Expected repeated logical deletion to fail.");
  }
  equal(repeatedDeletion.error.code, "PERSISTENCE_INVALID_RECORD_LIFECYCLE");
  equal(recordPurgeEligibility({
    current: deletedLifecycle.value,
    asOf: isoDateTimeFromDate(new Date("2026-09-23T12:00:30.000Z")),
    retentionSatisfied: true,
    legalHold: false,
  }), "within-recovery-window");
  equal(recordPurgeEligibility({
    current: deletedLifecycle.value,
    asOf: isoDateTimeFromDate(new Date("2026-09-23T12:01:01.000Z")),
    retentionSatisfied: true,
    legalHold: true,
  }), "legal-hold");
  equal(recordPurgeEligibility({
    current: deletedLifecycle.value,
    asOf: isoDateTimeFromDate(new Date("2026-09-23T12:01:01.000Z")),
    retentionSatisfied: false,
    legalHold: false,
  }), "retention-not-met");
  equal(recordPurgeEligibility({
    current: deletedLifecycle.value,
    asOf: isoDateTimeFromDate(new Date("2026-09-23T12:01:01.000Z")),
    retentionSatisfied: true,
    legalHold: false,
  }), "eligible");
  const restoredLifecycle = restoreLogicallyDeletedRecord({
    current: deletedLifecycle.value,
    restoredAt: isoDateTimeFromDate(new Date("2026-09-23T12:00:59.000Z")),
  });
  equal(isOk(restoredLifecycle), true);
  if (!isOk(restoredLifecycle)) {
    throw new Error("Expected restoration inside the recovery window to succeed.");
  }
  equal(isRecordLifecycleActive(restoredLifecycle.value), true);
  const expiredRestore = restoreLogicallyDeletedRecord({
    current: deletedLifecycle.value,
    restoredAt: isoDateTimeFromDate(new Date("2026-09-23T12:01:01.000Z")),
  });
  equal(isErr(expiredRestore), true);
  if (!isErr(expiredRestore)) {
    throw new Error("Expected restoration after the recovery window to fail.");
  }
  equal(expiredRestore.error.code, "PERSISTENCE_RESTORE_WINDOW_EXPIRED");
  const restoreActive = restoreLogicallyDeletedRecord({
    current: activeRecordLifecycle(),
    restoredAt: recordedAt,
  });
  equal(isErr(restoreActive), true);
  if (!isErr(restoreActive)) {
    throw new Error("Expected restoration of an active record to fail.");
  }
  equal(restoreActive.error.code, "PERSISTENCE_RECORD_NOT_DELETED");
  equal(recordPurgeEligibility({
    current: activeRecordLifecycle(),
    asOf: recordedAt,
    retentionSatisfied: true,
    legalHold: false,
  }), "not-deleted");
  const messageType = outboxMessageType("platform-smoke.work.accepted");
  const deliveryPolicy = outboxDeliveryPolicy("platform-short-idempotent-work.v1");
  const messageVersion = outboxMessageVersion(2);
  const lineageKind = recordKind("platform-smoke.work-item");
  const lineageId = recordId("work-1");
  const lineageRevision = recordRevision(1);
  const stateField = recordChangeFieldName("state");
  equal(isOk(messageType), true);
  equal(isOk(deliveryPolicy), true);
  equal(isOk(messageVersion), true);
  if (!isOk(messageType) || !isOk(deliveryPolicy) || !isOk(messageVersion) || !isOk(lineageKind) || !isOk(lineageId) || !isOk(lineageRevision) || !isOk(stateField)) {
    throw new Error("Expected valid durable-delivery facts.");
  }
  const durableEntry = outboxEntry({
    id: outboxEntryId("outbox-1"),
    subject: recordReference({ kind: lineageKind.value, id: lineageId.value }),
    messageType: messageType.value,
    messageVersion: messageVersion.value,
    deliveryPolicy: deliveryPolicy.value,
    createdAt: recordedAt,
    causationId: causationId("request-1"),
  });
  equal(durableEntry.messageVersion, 2);
  equal(durableEntry.messageType, "platform-smoke.work.accepted");
  equal(isErr(outboxMessageType("Platform Smoke")), true);
  equal(isErr(outboxDeliveryPolicy("no-space policy")), true);
  equal(isErr(outboxMessageVersion(0)), true);

  const lineage = recordChange({
    id: recordChangeId("change-1"),
    record: recordReference({ kind: lineageKind.value, id: lineageId.value }),
    revision: lineageRevision.value,
    action: "updated",
    occurredAt: recordedAt,
    causationId: causationId("request-1"),
    changedFields: [stateField.value],
  });
  equal(isOk(lineage), true);
  if (!isOk(lineage)) {
    throw new Error("Expected valid record change.");
  }
  deepEqual(lineage.value.changedFields, ["state"]);
  const duplicateFields = recordChange({
    id: recordChangeId("change-2"),
    record: recordReference({ kind: lineageKind.value, id: lineageId.value }),
    revision: lineageRevision.value,
    action: "updated",
    occurredAt: recordedAt,
    changedFields: [stateField.value, stateField.value],
  });
  equal(isErr(duplicateFields), true);
  if (!isErr(duplicateFields)) {
    throw new Error("Expected duplicate lineage fields to fail.");
  }
  equal(duplicateFields.error.code, "PERSISTENCE_INVALID_LINEAGE");
  const deletedLineage = recordChange({
    id: recordChangeId("change-3"),
    record: recordReference({ kind: lineageKind.value, id: lineageId.value }),
    revision: lineageRevision.value,
    action: "deleted",
    occurredAt: recordedAt,
    changedFields: [stateField.value],
  });
  const restoredLineage = recordChange({
    id: recordChangeId("change-4"),
    record: recordReference({ kind: lineageKind.value, id: lineageId.value }),
    revision: lineageRevision.value,
    action: "restored",
    occurredAt: recordedAt,
    changedFields: [stateField.value],
  });
  equal(isOk(deletedLineage), true);
  equal(isOk(restoredLineage), true);
  if (!isOk(deletedLineage) || !isOk(restoredLineage)) {
    throw new Error("Expected deletion and restoration to use the bounded lineage vocabulary.");
  }
  equal(deletedLineage.value.action, "deleted");
  equal(restoredLineage.value.action, "restored");

  const repository = inMemoryRepository<DealRecord, DealId>({
    getId: (deal) => deal.id,
    getConcurrencyToken: (deal) => deal.concurrencyToken,
    clone: (deal) => ({ ...deal, tags: [...deal.tags] }),
    initialEntities: [
      {
        id: dealId,
        name: "Initial deal",
        concurrencyToken: firstVersion,
        tags: ["seed"],
      },
    ],
  });

  const loaded = await repository.get(dealId);
  if (loaded === null) {
    throw new Error("Expected seeded deal.");
  }
  deepEqual(loaded, {
    id: "deal-123",
    name: "Initial deal",
    concurrencyToken: "deal-123:v1",
    tags: ["seed"],
  });

  loaded.tags.push("mutated");
  const reloaded = await repository.get(dealId);
  deepEqual(reloaded?.tags, ["seed"]);

  const saved = await repository.save(
    {
      id: dealId,
      name: "Updated deal",
      concurrencyToken: secondVersion,
      tags: ["updated"],
    },
    { expectedConcurrencyToken: firstVersion },
  );
  equal(isOk(saved), true);
  if (!isOk(saved)) {
    throw new Error("Expected save to succeed.");
  }
  equal(saved.value.name, "Updated deal");

  const staleSave = await repository.save(
    {
      id: dealId,
      name: "Stale update",
      concurrencyToken: thirdVersion,
      tags: ["stale"],
    },
    { expectedConcurrencyToken: firstVersion },
  );
  equal(isErr(staleSave), true);
  if (!isErr(staleSave)) {
    throw new Error("Expected stale save to fail.");
  }
  equal(staleSave.error.code, "PERSISTENCE_CONFLICT");

  const missing = await repository.get(entityId<"DealId">("missing-deal"));
  equal(missing, null);

  const unitOfWork = inMemoryUnitOfWork();
  const unsupportedTransactionalSave = await unitOfWork.run((transaction) =>
    repository.save(
      {
        id: dealId,
        name: "Transaction attempt",
        concurrencyToken: thirdVersion,
        tags: ["transaction"],
      },
      { transaction },
    ),
  );
  equal(isErr(unsupportedTransactionalSave), true);
  if (!isErr(unsupportedTransactionalSave)) {
    throw new Error("Expected in-memory repository to reject a transaction handle.");
  }
  equal(unsupportedTransactionalSave.error.code, "PERSISTENCE_TRANSACTION_UNSUPPORTED");

  const events: string[] = [];
  const value = await unitOfWork.run((transaction) => {
    transaction.afterCommit(() => {
      events.push("first-after-commit");
    });
    transaction.afterCommit(async () => {
      events.push("second-after-commit");
    });
    events.push("inside-transaction");
    return "done";
  });
  equal(value, "done");
  deepEqual(events, ["inside-transaction", "first-after-commit", "second-after-commit"]);

  const rolledBackEvents: string[] = [];
  await rejects(
    unitOfWork.run(async (transaction) => {
      transaction.afterCommit(() => {
        rolledBackEvents.push("should-not-run");
      });
      throw new Error("operation failed");
    }),
    (error: unknown) =>
      isPersistenceTransactionError(error) &&
      error.cause instanceof Error &&
      error.cause.message === "operation failed",
  );
  deepEqual(rolledBackEvents, []);

  let capturedTransaction: Transaction | undefined;
  await unitOfWork.run((transaction) => {
    capturedTransaction = transaction;
  });
  if (capturedTransaction === undefined) {
    throw new Error("Expected transaction to be captured.");
  }
  const closedTransaction = capturedTransaction;
  throws(() => closedTransaction.afterCommit(() => undefined), /transaction is closed/);
  await diagnosticCoverage();
}

function assertValidation(result: { readonly ok: boolean; readonly error?: { readonly diagnosticRecord?: DiagnosticRecord } }, operation: string, field: string, reason: string): void {
  equal(result.ok, false);
  deepEqual(result.error?.diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "core.persistence.validation-rejected", definitionVersion: 1,
    detail: { operation, field, reason, effect: "rejected" } });
}
function boundary(operation: string, phase: string, effect: string, ordinal?: number, reason = "boundary-threw") {
  return { schema: "core/diagnostic-record/v1", code: "core.persistence.in-memory-boundary-failed", definitionVersion: 1,
    detail: { operation, phase, reason, effect, ...(ordinal === undefined ? {} : { ordinal }) } };
}
function caught(operation: () => unknown): unknown {
  try { operation(); } catch (error) { return error; }
  throw new Error("Expected original synchronous failure.");
}
async function rejected(operation: () => Promise<unknown>): Promise<unknown> {
  try { await operation(); } catch (error) { return error; }
  throw new Error("Expected original asynchronous failure.");
}

async function diagnosticCoverage(): Promise<void> {
  const privateValue = "synthetic-private-persistence-canary";
  const when = isoDateTimeFromDate(new Date("2026-09-23T12:00:00Z"));
  const retention = recordRetentionPolicyReference("reviewed.policy");
  if (!retention.ok) throw new Error("Expected retention fixture.");
  const policy = { recoveryWindowMs: 1_000, retentionPolicy: retention.value, legalHoldCheckRequired: true as const };
  for (const value of [0.5, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1]) {
    assertValidation(recordLifecyclePolicy({ ...policy, recoveryWindowMs: value }), "lifecycle-policy", "recovery-window", "not-safe-integer");
  }
  for (const value of [0, -1]) assertValidation(recordLifecyclePolicy({ ...policy, recoveryWindowMs: value }), "lifecycle-policy", "recovery-window", "not-positive");
  assertValidation(recordLifecyclePolicy({ ...policy, legalHoldCheckRequired: false as unknown as true }), "lifecycle-policy", "legal-hold-check", "required");
  assertValidation(recordRetentionPolicyReference(privateValue.toUpperCase()), "retention-reference", "retention-policy", "invalid-format");
  const deleted = logicallyDeleteRecord({ current: activeRecordLifecycle(), deletedAt: when, policy });
  if (!deleted.ok) throw new Error("Expected deleted fixture.");
  assertValidation(logicallyDeleteRecord({ current: deleted.value, deletedAt: when, policy }), "delete", "state", "already-deleted");
  assertValidation(logicallyDeleteRecord({ current: activeRecordLifecycle(), deletedAt: brand<string, "ISODateTime">(privateValue), policy }), "delete", "deleted-at", "invalid-time");
  assertValidation(logicallyDeleteRecord({ current: activeRecordLifecycle(), deletedAt: when, policy: { ...policy, recoveryWindowMs: Number.MAX_VALUE } }), "delete", "restore-boundary", "unrepresentable-boundary");
  assertValidation(restoreLogicallyDeletedRecord({ current: activeRecordLifecycle(), restoredAt: when }), "restore", "state", "not-deleted");
  assertValidation(restoreLogicallyDeletedRecord({ current: deleted.value, restoredAt: isoDateTimeFromDate(new Date(Date.parse(when) + 1_001)) }), "restore", "restore-time", "window-expired");
  equal(restoreLogicallyDeletedRecord({ current: deleted.value, restoredAt: isoDateTimeFromDate(new Date(Date.parse(when) + 1_000)) }).ok, true, "restore equality stays accepted");
  equal(restoreLogicallyDeletedRecord({ current: deleted.value, restoredAt: brand<string, "ISODateTime">(privateValue) }).ok, true, "diagnostics do not add timestamp validation");
  assertValidation(recordKind(privateValue.toUpperCase()), "record-kind", "kind", "invalid-format");
  assertValidation(recordId(""), "record-id", "id", "empty");
  assertValidation(recordId(` ${privateValue}`), "record-id", "id", "untrimmed");
  assertValidation(recordChangeActor({ kind: "principal", id: "" }), "change-actor", "actor-id", "empty");
  assertValidation(recordChangeActor({ kind: "system", id: `${privateValue} ` }), "change-actor", "actor-id", "untrimmed");
  assertValidation(recordChangeFieldName(privateValue.toUpperCase()), "change-field", "field-name", "invalid-format");
  for (const value of [0.5, NaN, Infinity]) {
    assertValidation(recordRevision(value), "record-revision", "revision", "not-integer");
    assertValidation(outboxMessageVersion(value), "outbox-version", "message-version", "not-integer");
    assertValidation(pageTotal(value), "page-total", "total", "not-integer");
    assertValidation(pageTotals({ totalItems: value }), "page-totals", "totalItems", "not-integer");
    assertValidation(pageTotals({ totalMatchingItems: value }), "page-totals", "totalMatchingItems", "not-integer");
    assertValidation(pageRequest({ limit: value }), "page-request", "limit", "not-integer");
  }
  for (const value of [0, -1]) {
    assertValidation(recordRevision(value), "record-revision", "revision", "not-positive");
    assertValidation(outboxMessageVersion(value), "outbox-version", "message-version", "not-positive");
    assertValidation(pageRequest({ limit: value }), "page-request", "limit", "not-positive");
  }
  assertValidation(pageTotal(-1), "page-total", "total", "negative");
  assertValidation(pageTotals({ totalItems: -1 }), "page-totals", "totalItems", "negative");
  assertValidation(pageTotals({ totalMatchingItems: -1 }), "page-totals", "totalMatchingItems", "negative");
  assertValidation(pageTotals({ totalItems: 0, totalMatchingItems: 1 }), "page-totals", "totals", "matching-exceeds-total");
  assertValidation(pageRequest({ limit: 1, cursor: "" }), "page-request", "cursor", "empty");
  assertValidation(outboxMessageType(privateValue.toUpperCase()), "outbox-type", "message-type", "invalid-format");
  assertValidation(outboxDeliveryPolicy(privateValue.toUpperCase()), "outbox-policy", "delivery-policy", "invalid-format");
  const kind = recordKind("reviewed.record");
  const id = recordId(privateValue);
  const revision = recordRevision(1);
  const field = recordChangeFieldName("reviewed_field");
  if (!kind.ok || !id.ok || !revision.ok || !field.ok) throw new Error("Expected lineage fixture.");
  const change = { id: recordChangeId(privateValue), record: recordReference({ kind: kind.value, id: id.value }), revision: revision.value, action: "created" as const, occurredAt: when };
  assertValidation(recordChange({ ...change, changedFields: Array(33).fill(field.value) }), "record-change", "changed-fields", "too-many");
  assertValidation(recordChange({ ...change, changedFields: [field.value, field.value] }), "record-change", "changed-fields", "duplicate");
  equal(recordChange({ ...change, changedFields: [] }).ok, true);
  equal(pageRequest({ limit: 1, cursor: " " }).ok, true, "existing cursor grammar remains");
  equal(pageTotal(0).ok, true);
  equal(outboxMessageVersion(Number.MAX_SAFE_INTEGER + 1).ok, true, "integer is not silently strengthened to safe integer");
  let reads = 0;
  assertValidation(pageRequest({ get limit() { reads++; return 0.5; }, get cursor(): string { throw new Error("unreached cursor"); } }), "page-request", "limit", "not-integer");
  equal(reads, 2, "existing limit read plus legacy params read remain");
  reads = 0;
  assertValidation(recordLifecyclePolicy({ ...policy, get recoveryWindowMs() { reads++; return 0.5; }, get legalHoldCheckRequired(): true { throw new Error("unreached hold"); } }), "lifecycle-policy", "recovery-window", "not-safe-integer");
  equal(reads, 1);
  for (const definition of coreDiagnosticCatalog.definitions.filter((definition) => definition.code.startsWith("core.persistence."))) {
    equal(definition.version, 1);
    equal(JSON.stringify(definition).includes(privateValue), false);
  }
  equal(createDiagnosticRecord(corePersistenceValidationDiagnostic, { operation: "save", field: "id", reason: privateValue, effect: "rejected" } as never).ok, false);

  const sourceDefinition = defineDiagnostic({ code: "fixture.persistence-source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } } } as const);
  const sources = Array.from({ length: 9 }, (_, ordinal) => {
    const result = createDiagnosticRecord(sourceDefinition, { ordinal });
    if (!result.ok) throw new Error("Expected source fixture.");
    return result.value;
  });
  const sourcePrimary = sources[0]!;
  const companions = sources.slice(1);
  const makeSource = () => Object.assign(new Error(privateValue), { diagnosticRecord: sourcePrimary, relatedDiagnosticRecords: companions });
  const explicit = persistenceError({ code: "PERSISTENCE_TIMEOUT", defaultMessage: "Safe", diagnosticRecord: sourcePrimary });
  equal(explicit.diagnosticRecord, sourcePrimary, "old custom-app primary requires no definitions");
  const retained = persistenceError({ code: "PERSISTENCE_TIMEOUT", defaultMessage: "Safe", diagnosticRecord: sourcePrimary,
    relatedDiagnosticRecords: companions, relatedDiagnosticDefinitions: [sourceDefinition] });
  equal(retained.diagnosticRecord, sourcePrimary);
  deepEqual(retained.relatedDiagnosticRecords, companions);
  equal(Object.isFrozen(retained.relatedDiagnosticRecords), true);
  equal("relatedDiagnosticDefinitions" in retained, false);
  for (const invalid of [Array(1), Array(diagnosticRelatedRecordLimit + 1).fill(sourcePrimary), [{ ...sourcePrimary, detail: { ordinal: privateValue } }]]) {
    const result = persistenceError({ code: "PERSISTENCE_TIMEOUT", defaultMessage: "Safe", diagnosticRecord: sourcePrimary,
      relatedDiagnosticRecords: invalid, relatedDiagnosticDefinitions: [sourceDefinition] });
    equal(result.diagnosticRecord, sourcePrimary);
    equal(result.relatedDiagnosticRecords, undefined);
  }
  equal(persistenceError({ code: "PERSISTENCE_TIMEOUT", defaultMessage: "Safe", relatedDiagnosticRecords: companions }).relatedDiagnosticRecords, undefined);

  type Entity = { readonly id: string; readonly value: number; readonly token?: ConcurrencyToken };
  const seed: Entity = { id: privateValue, value: 1, token: firstVersion };
  for (const phase of ["get-id", "clone-initial"] as const) {
    const failure = makeSource();
    const observations: DiagnosticRecord[] = [];
    const events: string[] = [];
    const options: InMemoryRepositoryOptions<Entity, string> = {
      initialEntities: [seed, { ...seed, value: 2 }], diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => observations.push(record),
      getId(entity) { equal(this, options); events.push(`id:${entity.value}`); if (phase === "get-id" && entity.value === 2) throw failure; return entity.id; },
      clone(this: void, entity) { equal(this, undefined); events.push(`clone:${entity.value}`); if (phase === "clone-initial" && entity.value === 2) throw failure; return { ...entity }; },
    };
    equal(caught(() => inMemoryRepository(options)), failure);
    deepEqual(events, phase === "get-id" ? ["id:1", "clone:1", "id:2"] : ["id:1", "clone:1", "id:2", "clone:2"]);
    deepEqual(observations, [boundary("initialize", phase, "write-not-reached", 1), ...sources]);
  }
  for (const phase of ["clone-read", "get-id", "get-concurrency-token", "clone-before-write", "clone-after-write"] as const) {
    const failure = makeSource();
    const observations: DiagnosticRecord[] = [];
    const events: string[] = [];
    let active = false;
    let cloneCalls = 0;
    const options: InMemoryRepositoryOptions<Entity, string> = {
      initialEntities: [seed], diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => observations.push(record),
      getId(entity) { equal(this, options); events.push("id"); if (active && phase === "get-id") throw failure; return entity.id; },
      getConcurrencyToken(entity) { equal(this, options); events.push("token"); if (active && phase === "get-concurrency-token") throw failure; return entity.token; },
      clone(this: void, entity) {
        equal(this, undefined); events.push("clone"); cloneCalls++;
        if (active && (phase === "clone-read" || phase === "clone-before-write" || (phase === "clone-after-write" && cloneCalls === 2))) throw failure;
        return { ...entity };
      },
    };
    const repository = inMemoryRepository(options);
    events.length = 0; cloneCalls = 0; active = true;
    equal(await rejected(() => phase === "clone-read" ? repository.get(seed.id) : repository.save({ ...seed, value: 2 }, { expectedConcurrencyToken: firstVersion })), failure);
    deepEqual(events, phase === "clone-read" ? ["clone"] : phase === "get-id" ? ["id"] : phase === "get-concurrency-token" ? ["id", "token"]
      : phase === "clone-before-write" ? ["id", "token", "clone"] : ["id", "token", "clone", "clone"]);
    deepEqual(observations, [boundary(phase === "clone-read" ? "get" : "save", phase, phase === "clone-read" ? "read-only" : phase === "clone-after-write" ? "write-completed" : "write-not-reached"), ...sources]);
    active = false;
    equal((await repository.get(seed.id))?.value, phase === "clone-after-write" ? 2 : 1, "postwrite response failure must retain applied update");
    equal(failure.diagnosticRecord, sourcePrimary);
    deepEqual(failure.relatedDiagnosticRecords, companions);
    equal(JSON.stringify(observations).includes(privateValue), false);
  }
  const conflictRepository = inMemoryRepository<Entity, string>({ getId: (entity) => entity.id, initialEntities: [seed] });
  assertValidation(await conflictRepository.save(seed, { expectedConcurrencyToken: firstVersion }), "save", "concurrency-token", "token-unavailable");
  assertValidation(await conflictRepository.save({ ...seed, id: "missing" }, { expectedConcurrencyToken: firstVersion }), "save", "concurrency-token", "record-absent");
  const tokenRepository = inMemoryRepository<Entity, string>({ getId: (entity) => entity.id, getConcurrencyToken: (entity) => entity.token, initialEntities: [seed] });
  assertValidation(await tokenRepository.save(seed, { expectedConcurrencyToken: secondVersion }), "save", "concurrency-token", "token-mismatch");
  let forbiddenCalls = 0;
  const rejectTransaction = inMemoryRepository<Entity, string>({ getId() { forbiddenCalls++; throw new Error("unreached"); }, clone() { forbiddenCalls++; throw new Error("unreached"); }, getConcurrencyToken() { forbiddenCalls++; throw new Error("unreached"); } });
  assertValidation(await rejectTransaction.save(seed, { transaction: { afterCommit() {} }, expectedConcurrencyToken: firstVersion }), "save", "transaction", "unsupported");
  equal(forbiddenCalls, 0);

  for (const failure of [undefined, null, 7, privateValue, Object.freeze(new Error(privateValue))]) {
    for (const observerMode of ["absent", "throwing", "rejecting"] as const) {
      const observations: DiagnosticRecord[] = [];
      const onDiagnostic = observerMode === "absent" ? undefined : (record: DiagnosticRecord) => {
        observations.push(record);
        if (observerMode === "throwing") throw new Error(privateValue);
        return Promise.reject(new Error(privateValue));
      };
      const repository = inMemoryRepository<Entity, string>({ getId() { throw failure; }, ...(onDiagnostic === undefined ? {} : { onDiagnostic }) });
      equal(await rejected(() => repository.save(seed)), failure);
      deepEqual(observations, observerMode === "absent" ? [] : [boundary("save", "get-id", "write-not-reached")]);
      const unit = inMemoryUnitOfWork(onDiagnostic === undefined ? {} : { onDiagnostic });
      observations.length = 0;
      const wrapped = await rejected(() => unit.run(() => { throw failure; })) as { readonly code: string; readonly cause?: unknown; readonly diagnosticRecord?: DiagnosticRecord };
      equal(wrapped.code, "PERSISTENCE_TRANSACTION_FAILED");
      equal(wrapped.cause, failure);
      deepEqual(wrapped.diagnosticRecord, boundary("unit-of-work", "operation", "operation-not-returned"));
      deepEqual(observations, observerMode === "absent" ? [] : [boundary("unit-of-work", "operation", "operation-not-returned")]);
    }
  }
  const ownOnly: DiagnosticRecord[] = [];
  const ordinaryFailure = new Error(privateValue);
  const ordinaryRepository = inMemoryRepository<Entity, string>({ getId() { throw ordinaryFailure; }, onDiagnostic: (record) => ownOnly.push(record) });
  equal(await rejected(() => ordinaryRepository.save(seed)), ordinaryFailure);
  deepEqual(Object.getOwnPropertyDescriptor(ordinaryFailure, "diagnosticRecord")?.value, boundary("save", "get-id", "write-not-reached"));
  const selected: DiagnosticRecord[] = [];
  const unitFailure = makeSource();
  const actions: string[] = [];
  const unit = inMemoryUnitOfWork({ diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => selected.push(record) });
  const wrapped = await rejected(() => unit.run((transaction) => {
    actions.push("operation");
    transaction.afterCommit(() => { actions.push("first"); });
    transaction.afterCommit(function (this: void) { equal(this, undefined); actions.push("second"); throw unitFailure; });
    transaction.afterCommit(() => { actions.push("unreached-third"); });
    return "operation-returned";
  })) as { readonly code: string; readonly defaultMessage: string; readonly messageKey: string; readonly cause: unknown; readonly diagnosticRecord: DiagnosticRecord; readonly relatedDiagnosticRecords: readonly DiagnosticRecord[] };
  deepEqual(actions, ["operation", "first", "second"]);
  equal(wrapped.code, "PERSISTENCE_TRANSACTION_FAILED");
  equal(wrapped.defaultMessage, "Transaction failed before it could complete.");
  equal(wrapped.messageKey, "persistence.transaction.failed");
  equal(wrapped.cause, unitFailure);
  deepEqual(wrapped.diagnosticRecord, sourcePrimary);
  deepEqual(wrapped.relatedDiagnosticRecords, companions);
  deepEqual(selected, [boundary("unit-of-work", "after-commit", "operation-returned", 1), ...sources]);
  let captured: Transaction | undefined;
  selected.length = 0;
  await unit.run((transaction) => { captured = transaction; });
  const closed = caught(() => captured!.afterCommit(() => { throw new Error("unreached"); }));
  equal(closed instanceof TypeError, true);
  equal((closed as TypeError).message, "Cannot register after-commit actions after the transaction is closed.");
  deepEqual(selected, [boundary("after-commit-registration", "closed-registration", "registration-rejected", undefined, "transaction-closed")]);

  // Source selection is data-only, independently preserves companions and defaults to built-in Core definitions.
  const malformed = Object.assign(new Error(privateValue), { relatedDiagnosticRecords: companions });
  let accessorReads = 0;
  Object.defineProperty(malformed, "diagnosticRecord", { get() { accessorReads++; throw new Error(privateValue); } });
  selected.length = 0;
  const malformedWrapped = await rejected(() => unit.run(() => { throw malformed; })) as { readonly diagnosticRecord: DiagnosticRecord; readonly relatedDiagnosticRecords: readonly DiagnosticRecord[] };
  equal(accessorReads, 0);
  deepEqual(malformedWrapped.diagnosticRecord, boundary("unit-of-work", "operation", "operation-not-returned"));
  deepEqual(malformedWrapped.relatedDiagnosticRecords, companions);
  deepEqual(selected, [boundary("unit-of-work", "operation", "operation-not-returned"), ...companions]);
  const accessorCompanions: DiagnosticRecord[] = [];
  Object.defineProperty(accessorCompanions, "0", { enumerable: true, get() { accessorReads++; throw new Error(privateValue); } });
  selected.length = 0;
  const accessorFailure = Object.assign(new Error(privateValue), { diagnosticRecord: sourcePrimary, relatedDiagnosticRecords: accessorCompanions });
  const accessorWrapped = await rejected(() => unit.run(() => { throw accessorFailure; })) as { readonly diagnosticRecord: DiagnosticRecord; readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[] };
  equal(accessorReads, 0);
  deepEqual(accessorWrapped.diagnosticRecord, sourcePrimary);
  equal(accessorWrapped.relatedDiagnosticRecords, undefined);
  deepEqual(selected, [boundary("unit-of-work", "operation", "operation-not-returned"), sourcePrimary]);
  for (const failure of [makeSource(), Object.assign(new Error(privateValue), { diagnosticRecord: { ...sourcePrimary, detail: { ordinal: privateValue } }, relatedDiagnosticRecords: Array(9).fill(sourcePrimary) })]) {
    const records: DiagnosticRecord[] = [];
    const noAppDefinitions = inMemoryUnitOfWork({ onDiagnostic: (record) => records.push(record) });
    const result = await rejected(() => noAppDefinitions.run(() => { throw failure; })) as { readonly diagnosticRecord: DiagnosticRecord; readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[] };
    deepEqual(result.diagnosticRecord, boundary("unit-of-work", "operation", "operation-not-returned"));
    deepEqual(records, [boundary("unit-of-work", "operation", "operation-not-returned")]);
    equal(JSON.stringify(records).includes(privateValue), false);
  }
  const builtIn = pageRequest({ limit: 0 });
  if (builtIn.ok) throw new Error("Expected built-in diagnostic fixture.");
  const builtInRecords: DiagnosticRecord[] = [];
  const builtInWrapped = await rejected(() => inMemoryUnitOfWork({ onDiagnostic: (record) => builtInRecords.push(record) }).run(() => { throw builtIn.error; })) as { readonly diagnosticRecord: DiagnosticRecord };
  deepEqual(builtInWrapped.diagnosticRecord, builtIn.error.diagnosticRecord);
  deepEqual(builtInRecords, [boundary("unit-of-work", "operation", "operation-not-returned"), builtIn.error.diagnosticRecord]);
  const otherCoreFailure = caught(() => permission("", "view"));
  builtInRecords.length = 0;
  const otherCoreWrapped = await rejected(() => inMemoryUnitOfWork({ onDiagnostic: (record) => builtInRecords.push(record) }).run(() => { throw otherCoreFailure; })) as { readonly diagnosticRecord: DiagnosticRecord };
  const expectedOtherCore = { schema: "core/diagnostic-record/v1", code: "core.authz.permission-invalid", definitionVersion: 1, detail: { field: "resource", reason: "empty" } };
  deepEqual(otherCoreWrapped.diagnosticRecord, expectedOtherCore);
  deepEqual(builtInRecords, [boundary("unit-of-work", "operation", "operation-not-returned"), expectedOtherCore]);
  await new Promise<void>((resolve) => setImmediate(resolve));
}

function isPersistenceTransactionError(error: unknown): error is {
  readonly code: "PERSISTENCE_TRANSACTION_FAILED";
  readonly cause?: unknown;
} {
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    error.code === "PERSISTENCE_TRANSACTION_FAILED"
  );
}

main()
  .then(() => {
    console.log("packages/core persistence runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
