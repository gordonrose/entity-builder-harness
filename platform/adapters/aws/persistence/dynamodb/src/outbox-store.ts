import {
  GetItemCommand,
  PutItemCommand,
  QueryCommand,
  UpdateItemCommand,
} from "@aws-sdk/client-dynamodb";
import type { OutboxEntry, OutboxEntryId } from "@kanbien/core/persistence";
import type { ISODateTime, Result } from "@kanbien/core/shared";
import {
  nextPlatformPersistenceLease,
  platformLeaseExpired,
  platformOutboxRecord,
  platformPersistenceError,
  type PlatformOutboxClaimResult,
  type PlatformOutboxRecord,
  type PlatformOutboxStore,
  type PlatformPersistenceError,
  type PlatformPersistenceFence,
  type PlatformPersistenceLeaseOwner,
  type PlatformPersistenceDiagnosticOptions,
} from "@kanbien/platform-persistence";
import type { DynamoDbPersistenceCommandClient } from "./client";
import type { DynamoDbPersistenceConfiguration } from "./configuration/index";
import { isDynamoDbConditionalFailure } from "./errors";
import {
  dueSort,
  itemToOutboxRecord,
  outboxDuePartition,
  outboxKey,
  outboxRecordToItem,
} from "./records";
import { dynamoDbObservation, attributeObservation, responseItem, responseItems, type DynamoDbObservation } from "./observations";

export interface DynamoDbPlatformOutboxStoreOptions extends PlatformPersistenceDiagnosticOptions {
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly client: DynamoDbPersistenceCommandClient;
}

export function createDynamoDbPlatformOutboxStore(
  options: DynamoDbPlatformOutboxStoreOptions,
): PlatformOutboxStore {
  return {
    create: async (entry) => {
      const observed = dynamoDbObservation(options, "create_outbox");
      const record = observed.at("encoding", () => platformOutboxRecord({ entry }));
      try {
        await observed.send(options, () => new PutItemCommand({
          TableName: options.configuration.tableName,
          Item: outboxRecordToItem(record),
          ConditionExpression: "attribute_not_exists(#pk)",
          ExpressionAttributeNames: { "#pk": "PK" },
        }));
        return success(record);
      } catch (error) {
        if (isDynamoDbConditionalFailure(error)) {
          return failure(
            "PLATFORM_PERSISTENCE_DUPLICATE_OUTBOX_ENTRY",
            "Outbox entry already exists.",
            "platform.persistence.outbox.duplicate",
            observed.evidence(),
          );
        }
        return { ok: false, error: observed.error("create_outbox") };
      }
    },

    get: async (id) => readOutbox(options, id),

    listDeliverable: async (input) => {
      const observed = dynamoDbObservation(options, "list_outbox");
      let limitCondition: "not-integer" | "not-positive" = "not-integer";
      if (observed.at("selection", () => !Number.isInteger(input.limit) || (limitCondition = "not-positive", input.limit <= 0))) {
        return failure(
          "PLATFORM_PERSISTENCE_INVALID_LIMIT",
          "Outbox delivery limit must be a positive integer.",
          "platform.persistence.outbox.limit.invalid",
          observed.reject("limit", limitCondition, "validation", "not-started"),
        );
      }
      const attributes = attributeObservation(options, "list_outbox", "returned");
      try {
        const response = await observed.send(options, () => new QueryCommand({
          TableName: options.configuration.tableName,
          IndexName: options.configuration.outboxDueIndexName,
          KeyConditionExpression: "#dueKey = :dueKey AND #dueSort <= :dueSort",
          ExpressionAttributeNames: {
            "#dueKey": "DueKey",
            "#dueSort": "DueSort",
          },
          ExpressionAttributeValues: {
            ":dueKey": stringAttribute(outboxDuePartition()),
            ":dueSort": stringAttribute(dueSort(input.asOf, "\uffff")),
          },
          Limit: input.limit,
          ScanIndexForward: true,
        }));
        const items = observed.at("response", () => responseItems(response, attributes));
        return success(observed.decode(attributes, () => items.map((item, ordinal) => { attributes.row(ordinal); return itemToOutboxRecord(item, attributes); })));
      } catch (error) {
        return { ok: false, error: observed.error("list_outbox", error) };
      } finally { attributes.flush(); }
    },

    claim: async (input) => {
      const observed = dynamoDbObservation(options, "claim_outbox");
      const reading = dynamoDbObservation(options, "read_outbox");
      let record: PlatformOutboxRecord | null;
      try {
        record = await reading.at("selection", () => readOutbox(options, input.id, reading));
      } catch (error) {
        return { ok: false, error: reading.error("read_outbox", error) };
      }
      if (record === null) return outboxNotFound(observed);
      if (record.state === "published") return success({ disposition: "already-published", record });
      if (record.state === "leased" && record.lease === undefined) {
        observed.reject("lease", "absent");
        return { ok: false, error: observed.error("claim_outbox") };
      }
      if (observed.at("selection", () => record.lease !== undefined && !platformLeaseExpired(record.lease, input.acquiredAt))) {
        return success({ disposition: "lease-active", record });
      }
      const leaseResult = observed.at("encoding", () => nextPlatformPersistenceLease({
        owner: input.owner,
        ...(record.lease === undefined ? {} : { priorLease: record.lease }),
        priorAttempt: record.attempt,
        acquiredAt: input.acquiredAt,
        durationMs: input.leaseDurationMs,
      }));
      if (!leaseResult.ok) { const error = leaseResult.error; observed.source(error); return { ok: false, error }; }
      const claimed = observed.at("encoding", () => platformOutboxRecord({
        entry: record.entry,
        state: "leased",
        attempt: leaseResult.value.attempt,
        lease: leaseResult.value,
      }));
      try {
        await observed.send(options, () => new UpdateItemCommand({
          TableName: options.configuration.tableName,
          Key: outboxKey(input.id),
          UpdateExpression: "SET #state = :leased, #attempt = :attempt, #leaseOwner = :leaseOwner, #leaseFence = :leaseFence, #leaseAcquiredAt = :leaseAcquiredAt, #leaseExpiresAt = :leaseExpiresAt, #dueKey = :dueKey, #dueSort = :dueSort REMOVE #publishedAt",
          ConditionExpression: claimCondition(record),
          ExpressionAttributeNames: claimAttributeNames(),
          ExpressionAttributeValues: {
            ":leased": stringAttribute("leased"),
            ":priorAttempt": numberAttribute(record.attempt),
            ":attempt": numberAttribute(leaseResult.value.attempt),
            ":leaseOwner": stringAttribute(leaseResult.value.owner),
            ":leaseFence": numberAttribute(leaseResult.value.fence),
            ":leaseAcquiredAt": stringAttribute(leaseResult.value.acquiredAt),
            ":leaseExpiresAt": stringAttribute(leaseResult.value.expiresAt),
            ":dueKey": stringAttribute(outboxDuePartition()),
            ":dueSort": stringAttribute(dueSort(leaseResult.value.expiresAt, input.id)),
            ...(record.lease === undefined
              ? { ":pending": stringAttribute("pending") }
              : {
                ":priorFence": numberAttribute(record.lease.fence),
                ":asOf": stringAttribute(input.acquiredAt),
              }),
          },
        }));
        return success({ disposition: "claimed", record: claimed });
      } catch (error) {
        if (!isDynamoDbConditionalFailure(error)) {
          return { ok: false, error: observed.error("claim_outbox", error) };
        }
        return observed.at("selection", () => resolveOutboxClaimRace(options, input.id, input.acquiredAt, observed));
      }
    },

    markPublished: async (input) => {
      const observed = dynamoDbObservation(options, "publish_outbox");
      const reading = dynamoDbObservation(options, "read_outbox");
      let record: PlatformOutboxRecord | null;
      try {
        record = await reading.at("selection", () => readOutbox(options, input.id, reading));
      } catch (error) {
        return { ok: false, error: reading.error("read_outbox", error) };
      }
      if (record === null) return outboxNotFound(observed);
      if (record.state === "published") return success(record);
      const valid = observed.at("selection", () => validatePublish(record, input.fence, input.publishedAt, observed));
      if (!valid.ok) return valid;
      const published = observed.at("encoding", () => platformOutboxRecord({
        entry: record.entry,
        state: "published",
        attempt: record.attempt,
        publishedAt: input.publishedAt,
      }));
      try {
        await observed.send(options, () => new UpdateItemCommand({
          TableName: options.configuration.tableName,
          Key: outboxKey(input.id),
          UpdateExpression: "SET #state = :published, #publishedAt = :publishedAt REMOVE #leaseOwner, #leaseFence, #leaseAcquiredAt, #leaseExpiresAt, #dueKey, #dueSort",
          ConditionExpression: "#state = :leased AND #leaseFence = :fence AND #leaseExpiresAt > :publishedAt",
          ExpressionAttributeNames: {
            "#state": "state",
            "#publishedAt": "publishedAt",
            "#leaseOwner": "leaseOwner",
            "#leaseFence": "leaseFence",
            "#leaseAcquiredAt": "leaseAcquiredAt",
            "#leaseExpiresAt": "leaseExpiresAt",
            "#dueKey": "DueKey",
            "#dueSort": "DueSort",
          },
          ExpressionAttributeValues: {
            ":leased": stringAttribute("leased"),
            ":published": stringAttribute("published"),
            ":fence": numberAttribute(input.fence),
            ":publishedAt": stringAttribute(input.publishedAt),
          },
        }));
        return success(published);
      } catch (error) {
        if (!isDynamoDbConditionalFailure(error)) {
          return { ok: false, error: observed.error("publish_outbox", error) };
        }
        return observed.at("selection", () => resolvePublishRace(options, input.id, input.fence, input.publishedAt, observed));
      }
    },
  };
}

async function readOutbox(
  options: DynamoDbPlatformOutboxStoreOptions,
  id: OutboxEntryId,
  observed = dynamoDbObservation(options, "read_outbox"),
): Promise<PlatformOutboxRecord | null> {
  const attributes = attributeObservation(options, "read_outbox", "returned");
  try {
    const response = await observed.send(options, () => new GetItemCommand({
      TableName: options.configuration.tableName,
      Key: outboxKey(id),
      ConsistentRead: true,
    }));
    const item = observed.at("response", () => responseItem(response, attributes));
    return item === undefined ? null : observed.decode(attributes, () => itemToOutboxRecord(item, attributes));
  } finally { attributes.flush(); }
}

async function resolveOutboxClaimRace(
  options: DynamoDbPlatformOutboxStoreOptions,
  id: OutboxEntryId,
  asOf: ISODateTime,
  observed: DynamoDbObservation,
): Promise<Result<PlatformOutboxClaimResult, PlatformPersistenceError>> {
  const reading = dynamoDbObservation(options, "read_outbox", "reconciliation");
  try {
    const record = await readOutbox(options, id, reading);
    if (record === null) { observed.reconcile("missing"); return outboxNotFound(observed); }
    if (record.state === "published") { observed.reconcile("already-published"); return success({ disposition: "already-published", record }); }
    if (observed.at("selection", () => record.lease !== undefined && !platformLeaseExpired(record.lease, asOf))) {
      observed.reconcile("lease-active"); return success({ disposition: "lease-active", record });
    }
  } catch {
    observed.reconcile("unavailable"); return { ok: false, error: reading.error("read_outbox") };
  }
  observed.reconcile("unresolved"); return { ok: false, error: observed.error("claim_outbox") };
}

async function resolvePublishRace(
  options: DynamoDbPlatformOutboxStoreOptions,
  id: OutboxEntryId,
  fence: PlatformPersistenceFence,
  publishedAt: ISODateTime,
  observed: DynamoDbObservation,
): Promise<Result<PlatformOutboxRecord, PlatformPersistenceError>> {
  const reading = dynamoDbObservation(options, "read_outbox", "reconciliation");
  try {
    const record = await readOutbox(options, id, reading);
    if (record === null) { observed.reconcile("missing"); return outboxNotFound(observed); }
    if (record.state === "published") { observed.reconcile("already-published"); return success(record); }
    const valid = observed.at("selection", () => validatePublish(record, fence, publishedAt, observed));
    observed.reconcile(valid.ok ? "valid-current-state" : "unresolved");
    return valid;
  } catch {
    observed.reconcile("unavailable"); return { ok: false, error: reading.error("read_outbox") };
  }
}

function validatePublish(
  record: PlatformOutboxRecord,
  fence: PlatformPersistenceFence,
  publishedAt: ISODateTime,
  observed?: DynamoDbObservation,
): Result<PlatformOutboxRecord, PlatformPersistenceError> {
  let rejectedField: "state" | "lease" = "state";
  if (record.state !== "leased" || (rejectedField = "lease", record.lease === undefined)) {
    return failure(
      "PLATFORM_PERSISTENCE_OUTBOX_NOT_LEASED",
      "Outbox entry must be leased before it can be published.",
      "platform.persistence.outbox.not_leased",
      observed?.reject(rejectedField, rejectedField === "state" ? "wrong-state" : "absent"),
    );
  }
  if (record.lease.fence !== fence) {
    return failure(
      "PLATFORM_PERSISTENCE_STALE_FENCE",
      "Outbox publish used a stale fence.",
      "platform.persistence.outbox.stale_fence",
      observed?.reject("fence", "stale"),
    );
  }
  if (platformLeaseExpired(record.lease, publishedAt)) {
    return failure(
      "PLATFORM_PERSISTENCE_LEASE_EXPIRED",
      "Outbox publish used an expired lease.",
      "platform.persistence.outbox.lease.expired",
      observed?.reject("lease", "expired"),
    );
  }
  return success(record);
}

function claimCondition(record: PlatformOutboxRecord): string {
  if (record.lease === undefined) {
    return "#state = :pending AND #attempt = :priorAttempt AND attribute_not_exists(#leaseFence)";
  }
  return "#state = :leased AND #leaseFence = :priorFence AND #leaseExpiresAt <= :asOf AND #attempt = :priorAttempt";
}

function claimAttributeNames(): Record<string, string> {
  return {
    "#state": "state",
    "#attempt": "attempt",
    "#leaseOwner": "leaseOwner",
    "#leaseFence": "leaseFence",
    "#leaseAcquiredAt": "leaseAcquiredAt",
    "#leaseExpiresAt": "leaseExpiresAt",
    "#publishedAt": "publishedAt",
    "#dueKey": "DueKey",
    "#dueSort": "DueSort",
  };
}

function outboxNotFound(observed?: DynamoDbObservation): Result<never, PlatformPersistenceError> {
  return failure(
    "PLATFORM_PERSISTENCE_OUTBOX_NOT_FOUND",
    "Outbox entry was not found.",
    "platform.persistence.outbox.not_found",
    observed?.reject("record", "not-found"),
  );
}

function stringAttribute(value: string): { readonly S: string } {
  return { S: value };
}

function numberAttribute(value: number): { readonly N: string } {
  return { N: String(value) };
}

function success<TValue>(value: TValue): Result<TValue, PlatformPersistenceError> {
  return { ok: true, value };
}

function failure(
  code: PlatformPersistenceError["code"],
  defaultMessage: string,
  messageKey: string,
  evidence: ReturnType<DynamoDbObservation["evidence"]> = {},
): Result<never, PlatformPersistenceError> {
  return { ok: false, error: platformPersistenceError({ code, defaultMessage, messageKey, ...evidence }) };
}
