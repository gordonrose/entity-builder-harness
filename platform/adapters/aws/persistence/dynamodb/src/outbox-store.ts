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
} from "@kanbien/platform-persistence";
import type { DynamoDbPersistenceCommandClient } from "./client";
import type { DynamoDbPersistenceConfiguration } from "./configuration";
import { dynamoDbPersistenceOperationError, isDynamoDbConditionalFailure } from "./errors";
import {
  dueSort,
  itemToOutboxRecord,
  outboxDuePartition,
  outboxKey,
  outboxRecordToItem,
  type DynamoDbPersistenceItem,
} from "./records";

export interface DynamoDbPlatformOutboxStoreOptions {
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly client: DynamoDbPersistenceCommandClient;
}

export function createDynamoDbPlatformOutboxStore(
  options: DynamoDbPlatformOutboxStoreOptions,
): PlatformOutboxStore {
  return {
    create: async (entry) => {
      const record = platformOutboxRecord({ entry });
      try {
        await options.client.send(new PutItemCommand({
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
          );
        }
        return { ok: false, error: dynamoDbPersistenceOperationError("create_outbox") };
      }
    },

    get: async (id) => readOutbox(options, id),

    listDeliverable: async (input) => {
      if (!Number.isInteger(input.limit) || input.limit <= 0) {
        return failure(
          "PLATFORM_PERSISTENCE_INVALID_LIMIT",
          "Outbox delivery limit must be a positive integer.",
          "platform.persistence.outbox.limit.invalid",
        );
      }
      try {
        const response = await options.client.send(new QueryCommand({
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
        return success(responseItems(response).map(itemToOutboxRecord));
      } catch (error) {
        return { ok: false, error: dynamoDbPersistenceOperationError("list_outbox", error) };
      }
    },

    claim: async (input) => {
      let record: PlatformOutboxRecord | null;
      try {
        record = await readOutbox(options, input.id);
      } catch (error) {
        return { ok: false, error: dynamoDbPersistenceOperationError("read_outbox", error) };
      }
      if (record === null) return outboxNotFound();
      if (record.state === "published") return success({ disposition: "already-published", record });
      if (record.state === "leased" && record.lease === undefined) {
        return { ok: false, error: dynamoDbPersistenceOperationError("claim_outbox") };
      }
      if (record.lease !== undefined && !platformLeaseExpired(record.lease, input.acquiredAt)) {
        return success({ disposition: "lease-active", record });
      }
      const leaseResult = nextPlatformPersistenceLease({
        owner: input.owner,
        ...(record.lease === undefined ? {} : { priorLease: record.lease }),
        priorAttempt: record.attempt,
        acquiredAt: input.acquiredAt,
        durationMs: input.leaseDurationMs,
      });
      if (!leaseResult.ok) return { ok: false, error: leaseResult.error };
      const claimed = platformOutboxRecord({
        entry: record.entry,
        state: "leased",
        attempt: leaseResult.value.attempt,
        lease: leaseResult.value,
      });
      try {
        await options.client.send(new UpdateItemCommand({
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
          return { ok: false, error: dynamoDbPersistenceOperationError("claim_outbox", error) };
        }
        return resolveOutboxClaimRace(options, input.id, input.acquiredAt);
      }
    },

    markPublished: async (input) => {
      let record: PlatformOutboxRecord | null;
      try {
        record = await readOutbox(options, input.id);
      } catch (error) {
        return { ok: false, error: dynamoDbPersistenceOperationError("read_outbox", error) };
      }
      if (record === null) return outboxNotFound();
      if (record.state === "published") return success(record);
      const valid = validatePublish(record, input.fence, input.publishedAt);
      if (!valid.ok) return valid;
      const published = platformOutboxRecord({
        entry: record.entry,
        state: "published",
        attempt: record.attempt,
        publishedAt: input.publishedAt,
      });
      try {
        await options.client.send(new UpdateItemCommand({
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
          return { ok: false, error: dynamoDbPersistenceOperationError("publish_outbox", error) };
        }
        return resolvePublishRace(options, input.id, input.fence, input.publishedAt);
      }
    },
  };
}

async function readOutbox(
  options: DynamoDbPlatformOutboxStoreOptions,
  id: OutboxEntryId,
): Promise<PlatformOutboxRecord | null> {
  const response = await options.client.send(new GetItemCommand({
    TableName: options.configuration.tableName,
    Key: outboxKey(id),
    ConsistentRead: true,
  }));
  const item = responseItem(response);
  return item === undefined ? null : itemToOutboxRecord(item);
}

async function resolveOutboxClaimRace(
  options: DynamoDbPlatformOutboxStoreOptions,
  id: OutboxEntryId,
  asOf: ISODateTime,
): Promise<Result<PlatformOutboxClaimResult, PlatformPersistenceError>> {
  try {
    const record = await readOutbox(options, id);
    if (record === null) return outboxNotFound();
    if (record.state === "published") return success({ disposition: "already-published", record });
    if (record.lease !== undefined && !platformLeaseExpired(record.lease, asOf)) {
      return success({ disposition: "lease-active", record });
    }
  } catch {
    return { ok: false, error: dynamoDbPersistenceOperationError("read_outbox") };
  }
  return { ok: false, error: dynamoDbPersistenceOperationError("claim_outbox") };
}

async function resolvePublishRace(
  options: DynamoDbPlatformOutboxStoreOptions,
  id: OutboxEntryId,
  fence: PlatformPersistenceFence,
  publishedAt: ISODateTime,
): Promise<Result<PlatformOutboxRecord, PlatformPersistenceError>> {
  try {
    const record = await readOutbox(options, id);
    if (record === null) return outboxNotFound();
    if (record.state === "published") return success(record);
    return validatePublish(record, fence, publishedAt);
  } catch {
    return { ok: false, error: dynamoDbPersistenceOperationError("read_outbox") };
  }
}

function validatePublish(
  record: PlatformOutboxRecord,
  fence: PlatformPersistenceFence,
  publishedAt: ISODateTime,
): Result<PlatformOutboxRecord, PlatformPersistenceError> {
  if (record.state !== "leased" || record.lease === undefined) {
    return failure(
      "PLATFORM_PERSISTENCE_OUTBOX_NOT_LEASED",
      "Outbox entry must be leased before it can be published.",
      "platform.persistence.outbox.not_leased",
    );
  }
  if (record.lease.fence !== fence) {
    return failure(
      "PLATFORM_PERSISTENCE_STALE_FENCE",
      "Outbox publish used a stale fence.",
      "platform.persistence.outbox.stale_fence",
    );
  }
  if (platformLeaseExpired(record.lease, publishedAt)) {
    return failure(
      "PLATFORM_PERSISTENCE_LEASE_EXPIRED",
      "Outbox publish used an expired lease.",
      "platform.persistence.outbox.lease.expired",
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

function outboxNotFound(): Result<never, PlatformPersistenceError> {
  return failure(
    "PLATFORM_PERSISTENCE_OUTBOX_NOT_FOUND",
    "Outbox entry was not found.",
    "platform.persistence.outbox.not_found",
  );
}

function responseItem(response: unknown): DynamoDbPersistenceItem | undefined {
  if (typeof response !== "object" || response === null || !("Item" in response)) return undefined;
  const item = (response as { readonly Item?: unknown }).Item;
  return isItem(item) ? item : undefined;
}

function responseItems(response: unknown): readonly DynamoDbPersistenceItem[] {
  if (typeof response !== "object" || response === null || !("Items" in response)) return [];
  const items = (response as { readonly Items?: unknown }).Items;
  return Array.isArray(items) ? items.filter(isItem) : [];
}

function isItem(value: unknown): value is DynamoDbPersistenceItem {
  return typeof value === "object" && value !== null && !Array.isArray(value);
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
): Result<never, PlatformPersistenceError> {
  return { ok: false, error: platformPersistenceError({ code, defaultMessage, messageKey }) };
}
