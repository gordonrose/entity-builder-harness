import type { AttributeValue } from "@aws-sdk/client-dynamodb";
import {
  causationId,
  correlationId,
  isoDateTime,
  type CausationId,
  type CorrelationId,
  type ISODateTime,
} from "@kanbien/core/shared";
import { tenantId } from "@kanbien/core/tenancy";
import {
  outboxDeliveryPolicy,
  outboxEntry,
  outboxEntryId,
  outboxMessageType,
  outboxMessageVersion,
  recordChange,
  recordChangeActor,
  recordChangeFieldName,
  recordChangeId,
  recordId,
  recordKind,
  recordReference,
  recordRevision,
  type OutboxEntry,
  type RecordChange,
  type RecordChangeFieldName,
} from "@kanbien/core/persistence";
import {
  platformOutboxRecord,
  platformPersistenceAttempt,
  platformPersistenceFence,
  platformPersistenceLease,
  platformPersistenceLeaseOwner,
  platformProcessingRecord,
  type PlatformOutboxRecord,
  type PlatformProcessingRecord,
} from "@kanbien/platform-persistence";

export type DynamoDbPersistenceItem = Record<string, AttributeValue>;

const outboxDueIndexPartition = "OUTBOX#DELIVERABLE";

export function outboxKey(id: string): DynamoDbPersistenceItem {
  return { PK: stringValue("OUTBOX#" + id), SK: stringValue("OUTBOX") };
}

export function processingKey(id: string): DynamoDbPersistenceItem {
  return { PK: stringValue("PROCESSING#" + id), SK: stringValue("PROCESSING") };
}

export function lineageKey(kind: string, id: string, revision: number): DynamoDbPersistenceItem {
  return {
    PK: stringValue("LINEAGE#" + kind + "#" + id),
    SK: stringValue("REVISION#" + String(revision).padStart(20, "0")),
  };
}

export function lineageRecordPartition(kind: string, id: string): string {
  return "LINEAGE#" + kind + "#" + id;
}

export function outboxDuePartition(): string {
  return outboxDueIndexPartition;
}

export function dueSort(at: string, id: string): string {
  return "DUE#" + at + "#" + id;
}

export function outboxRecordToItem(record: PlatformOutboxRecord): DynamoDbPersistenceItem {
  const entry = record.entry;
  return {
    ...outboxKey(entry.id),
    recordType: stringValue("outbox"),
    outboxEntryId: stringValue(entry.id),
    subjectKind: stringValue(entry.subject.kind),
    subjectId: stringValue(entry.subject.id),
    messageType: stringValue(entry.messageType),
    messageVersion: numberValue(entry.messageVersion),
    deliveryPolicy: stringValue(entry.deliveryPolicy),
    createdAt: stringValue(entry.createdAt),
    state: stringValue(record.state),
    attempt: numberValue(record.attempt),
    ...(entry.tenantId === undefined ? {} : { tenantId: stringValue(entry.tenantId) }),
    ...(entry.correlationId === undefined ? {} : { correlationId: stringValue(entry.correlationId) }),
    ...(entry.causationId === undefined ? {} : { causationId: stringValue(entry.causationId) }),
    ...(record.lease === undefined ? {} : leaseToItem(record.lease)),
    ...(record.publishedAt === undefined ? {} : { publishedAt: stringValue(record.publishedAt) }),
    ...(record.state === "published" ? {} : {
      DueKey: stringValue(outboxDueIndexPartition),
      DueSort: stringValue(dueSort(record.lease?.expiresAt ?? entry.createdAt, entry.id)),
    }),
  };
}

export function processingRecordToItem(record: PlatformProcessingRecord): DynamoDbPersistenceItem {
  return {
    ...processingKey(record.outboxEntryId),
    recordType: stringValue("processing"),
    outboxEntryId: stringValue(record.outboxEntryId),
    state: stringValue(record.state),
    attempt: numberValue(record.attempt),
    ...(record.lease === undefined ? {} : leaseToItem(record.lease)),
    ...(record.releasedAt === undefined ? {} : { releasedAt: stringValue(record.releasedAt) }),
    ...(record.completion === undefined ? {} : {
      completionOutcome: stringValue(record.completion.outcome),
      completedAt: stringValue(record.completion.completedAt),
    }),
  };
}

export function recordChangeToItem(change: RecordChange): DynamoDbPersistenceItem {
  return {
    ...lineageKey(change.record.kind, change.record.id, Number(change.revision)),
    recordType: stringValue("lineage"),
    recordChangeId: stringValue(change.id),
    recordKind: stringValue(change.record.kind),
    recordId: stringValue(change.record.id),
    revision: numberValue(change.revision),
    action: stringValue(change.action),
    occurredAt: stringValue(change.occurredAt),
    ...(change.tenantId === undefined ? {} : { tenantId: stringValue(change.tenantId) }),
    ...(change.actor === undefined ? {} : {
      actorKind: stringValue(change.actor.kind),
      actorId: stringValue(change.actor.id),
    }),
    ...(change.correlationId === undefined ? {} : { correlationId: stringValue(change.correlationId) }),
    ...(change.causationId === undefined ? {} : {
      causationId: stringValue(change.causationId),
      CauseKey: stringValue("CAUSE#" + change.causationId),
      CauseSort: stringValue(change.occurredAt + "#" + change.id),
    }),
    ...(change.changedFields === undefined || change.changedFields.length === 0 ? {} : {
      changedFields: { L: change.changedFields.map((field) => stringValue(field)) },
    }),
  };
}

export function itemToOutboxRecord(item: DynamoDbPersistenceItem): PlatformOutboxRecord {
  const entry = outboxEntry({
    id: outboxEntryId(requiredString(item, "outboxEntryId")),
    subject: recordReference({
      kind: requiredResult(recordKind(requiredString(item, "subjectKind"))),
      id: requiredResult(recordId(requiredString(item, "subjectId"))),
    }),
    messageType: requiredResult(outboxMessageType(requiredString(item, "messageType"))),
    messageVersion: requiredResult(outboxMessageVersion(requiredNumber(item, "messageVersion"))),
    deliveryPolicy: requiredResult(outboxDeliveryPolicy(requiredString(item, "deliveryPolicy"))),
    createdAt: requiredIso(item, "createdAt"),
    ...(optionalString(item, "tenantId") === undefined ? {} : { tenantId: tenantId(optionalString(item, "tenantId") as string) }),
    ...(optionalString(item, "correlationId") === undefined ? {} : { correlationId: correlationId(optionalString(item, "correlationId") as string) }),
    ...(optionalString(item, "causationId") === undefined ? {} : { causationId: causationId(optionalString(item, "causationId") as string) }),
  });
  const state = requiredOutboxState(requiredString(item, "state"));
  const lease = item.leaseOwner === undefined ? undefined : itemToLease(item);
  return platformOutboxRecord({
    entry,
    state,
    attempt: requiredResult(platformPersistenceAttempt(requiredNumber(item, "attempt"))),
    ...(lease === undefined ? {} : { lease }),
    ...(optionalString(item, "publishedAt") === undefined ? {} : { publishedAt: requiredIso(item, "publishedAt") }),
  });
}

export function itemToProcessingRecord(item: DynamoDbPersistenceItem): PlatformProcessingRecord {
  const state = requiredProcessingState(requiredString(item, "state"));
  const lease = item.leaseOwner === undefined ? undefined : itemToLease(item);
  const completionOutcome = optionalString(item, "completionOutcome");
  return platformProcessingRecord({
    outboxEntryId: outboxEntryId(requiredString(item, "outboxEntryId")),
    state,
    attempt: requiredResult(platformPersistenceAttempt(requiredNumber(item, "attempt"))),
    ...(lease === undefined ? {} : { lease }),
    ...(optionalString(item, "releasedAt") === undefined ? {} : { releasedAt: requiredIso(item, "releasedAt") }),
    ...(completionOutcome === undefined ? {} : {
      completion: {
        outcome: requiredProcessingOutcome(completionOutcome),
        completedAt: requiredIso(item, "completedAt"),
      },
    }),
  });
}

export function itemToRecordChange(item: DynamoDbPersistenceItem): RecordChange {
  const actorKind = optionalString(item, "actorKind");
  const actorId = optionalString(item, "actorId");
  if ((actorKind === undefined) !== (actorId === undefined)) {
    throw new TypeError("Stored lineage actor is incomplete.");
  }
  const action = requiredString(item, "action");
  if (action !== "created" && action !== "updated" && action !== "deleted" && action !== "restored") {
    throw new TypeError("Stored lineage action is invalid.");
  }
  return requiredResult(recordChange({
    id: recordChangeId(requiredString(item, "recordChangeId")),
    record: recordReference({
      kind: requiredResult(recordKind(requiredString(item, "recordKind"))),
      id: requiredResult(recordId(requiredString(item, "recordId"))),
    }),
    revision: requiredResult(recordRevision(requiredNumber(item, "revision"))),
    action,
    occurredAt: requiredIso(item, "occurredAt"),
    ...(optionalString(item, "tenantId") === undefined ? {} : { tenantId: tenantId(optionalString(item, "tenantId") as string) }),
    ...(actorKind === undefined || actorId === undefined ? {} : {
      actor: requiredResult(recordChangeActor({
        kind: requiredActorKind(actorKind),
        id: actorId,
      })),
    }),
    ...(optionalString(item, "correlationId") === undefined ? {} : { correlationId: correlationId(optionalString(item, "correlationId") as string) }),
    ...(optionalString(item, "causationId") === undefined ? {} : { causationId: causationId(optionalString(item, "causationId") as string) }),
    ...(item.changedFields === undefined ? {} : { changedFields: itemToChangedFields(item.changedFields) }),
  }));
}

function leaseToItem(lease: {
  readonly owner: string;
  readonly fence: number;
  readonly acquiredAt: string;
  readonly expiresAt: string;
}): DynamoDbPersistenceItem {
  return {
    leaseOwner: stringValue(lease.owner),
    leaseFence: numberValue(lease.fence),
    leaseAcquiredAt: stringValue(lease.acquiredAt),
    leaseExpiresAt: stringValue(lease.expiresAt),
  };
}

function itemToLease(item: DynamoDbPersistenceItem) {
  return requiredResult(platformPersistenceLease({
    owner: requiredResult(platformPersistenceLeaseOwner(requiredString(item, "leaseOwner"))),
    fence: requiredResult(platformPersistenceFence(requiredNumber(item, "leaseFence"))),
    attempt: requiredResult(platformPersistenceAttempt(requiredNumber(item, "attempt"))),
    acquiredAt: requiredIso(item, "leaseAcquiredAt"),
    expiresAt: requiredIso(item, "leaseExpiresAt"),
  }));
}

function itemToChangedFields(value: AttributeValue): readonly RecordChangeFieldName[] {
  if (!Array.isArray(value.L)) {
    throw new TypeError("Stored lineage changed fields are invalid.");
  }
  return value.L.map((field) => requiredResult(recordChangeFieldName(requiredAttributeString(field, "changedFields"))));
}

function requiredString(item: DynamoDbPersistenceItem, name: string): string {
  const value = optionalString(item, name);
  if (value === undefined) {
    throw new TypeError("Stored persistence item is missing " + name + ".");
  }
  return value;
}

function optionalString(item: DynamoDbPersistenceItem, name: string): string | undefined {
  const value = item[name];
  return value?.S;
}

function requiredAttributeString(value: AttributeValue, name: string): string {
  if (value.S === undefined) {
    throw new TypeError("Stored persistence item has invalid " + name + ".");
  }
  return value.S;
}

function requiredNumber(item: DynamoDbPersistenceItem, name: string): number {
  const raw = item[name]?.N;
  const value = raw === undefined ? Number.NaN : Number(raw);
  if (!Number.isSafeInteger(value)) {
    throw new TypeError("Stored persistence item has invalid " + name + ".");
  }
  return value;
}

function requiredIso(item: DynamoDbPersistenceItem, name: string): ISODateTime {
  return requiredResult(isoDateTime(requiredString(item, name)));
}

function requiredOutboxState(value: string): "pending" | "leased" | "published" {
  if (value === "pending" || value === "leased" || value === "published") return value;
  throw new TypeError("Stored outbox state is invalid.");
}

function requiredProcessingState(value: string): "claimed" | "retry-eligible" | "completed" {
  if (value === "claimed" || value === "retry-eligible" || value === "completed") return value;
  throw new TypeError("Stored processing state is invalid.");
}

function requiredProcessingOutcome(value: string): "succeeded" | "terminal-failure" {
  if (value === "succeeded" || value === "terminal-failure") return value;
  throw new TypeError("Stored processing outcome is invalid.");
}

function requiredActorKind(value: string): "principal" | "system" {
  if (value === "principal" || value === "system") return value;
  throw new TypeError("Stored lineage actor kind is invalid.");
}

function stringValue(value: string): AttributeValue {
  return { S: value };
}

function numberValue(value: number): AttributeValue {
  return { N: String(value) };
}

function requiredResult<TValue>(result: { readonly ok: true; readonly value: TValue } | { readonly ok: false }): TValue {
  if (!result.ok) {
    throw new TypeError("Stored persistence item violated a Core or platform contract.");
  }
  return result.value;
}
