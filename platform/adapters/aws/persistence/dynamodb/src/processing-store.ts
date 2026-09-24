import {
  GetItemCommand,
  PutItemCommand,
  UpdateItemCommand,
} from "@aws-sdk/client-dynamodb";
import type { OutboxEntryId } from "@kanbien/core/persistence";
import type { ISODateTime, Result } from "@kanbien/core/shared";
import {
  initialPlatformPersistenceAttempt,
  nextPlatformPersistenceLease,
  platformLeaseExpired,
  platformPersistenceError,
  platformProcessingRecord,
  type PlatformPersistenceError,
  type PlatformPersistenceFence,
  type PlatformPersistenceLeaseOwner,
  type PlatformProcessingClaimResult,
  type PlatformProcessingCompletionResult,
  type PlatformProcessingOutcome,
  type PlatformProcessingRecord,
  type PlatformProcessingStore,
} from "@kanbien/platform-persistence";
import type { DynamoDbPersistenceCommandClient } from "./client";
import type { DynamoDbPersistenceConfiguration } from "./configuration";
import { dynamoDbPersistenceOperationError, isDynamoDbConditionalFailure } from "./errors";
import {
  itemToProcessingRecord,
  processingKey,
  processingRecordToItem,
  type DynamoDbPersistenceItem,
} from "./records";

export interface DynamoDbPlatformProcessingStoreOptions {
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly client: DynamoDbPersistenceCommandClient;
}

export function createDynamoDbPlatformProcessingStore(
  options: DynamoDbPlatformProcessingStoreOptions,
): PlatformProcessingStore {
  return {
    get: async (outboxEntryId) => readProcessing(options, outboxEntryId),

    claim: async (input) => {
      let record: PlatformProcessingRecord | null;
      try {
        record = await readProcessing(options, input.outboxEntryId);
      } catch {
        return { ok: false, error: dynamoDbPersistenceOperationError("read_processing") };
      }
      if (record?.state === "completed") return success({ disposition: "already-completed", record });
      if (record !== null && record.lease === undefined) {
        return { ok: false, error: dynamoDbPersistenceOperationError("claim_processing") };
      }
      if (record?.state === "claimed" && record.lease !== undefined && !platformLeaseExpired(record.lease, input.acquiredAt)) {
        return success({ disposition: "lease-active", record });
      }
      const leaseResult = nextPlatformPersistenceLease({
        owner: input.owner,
        ...(record?.lease === undefined ? {} : { priorLease: record.lease }),
        priorAttempt: record?.attempt ?? initialPlatformPersistenceAttempt,
        acquiredAt: input.acquiredAt,
        durationMs: input.leaseDurationMs,
      });
      if (!leaseResult.ok) return { ok: false, error: leaseResult.error };
      const claimed = platformProcessingRecord({
        outboxEntryId: input.outboxEntryId,
        state: "claimed",
        attempt: leaseResult.value.attempt,
        lease: leaseResult.value,
      });
      try {
        if (record === null) {
          await options.client.send(new PutItemCommand({
            TableName: options.configuration.tableName,
            Item: processingRecordToItem(claimed),
            ConditionExpression: "attribute_not_exists(#pk)",
            ExpressionAttributeNames: { "#pk": "PK" },
          }));
        } else {
          await options.client.send(new UpdateItemCommand({
            TableName: options.configuration.tableName,
            Key: processingKey(input.outboxEntryId),
            UpdateExpression: "SET #state = :claimed, #attempt = :attempt, #leaseOwner = :leaseOwner, #leaseFence = :leaseFence, #leaseAcquiredAt = :leaseAcquiredAt, #leaseExpiresAt = :leaseExpiresAt REMOVE #releasedAt, #completionOutcome, #completedAt",
            ConditionExpression: claimCondition(record),
            ExpressionAttributeNames: claimAttributeNames(),
            ExpressionAttributeValues: {
              ":claimed": stringAttribute("claimed"),
              ":retryEligible": stringAttribute("retry-eligible"),
              ":priorAttempt": numberAttribute(record.attempt),
              ":attempt": numberAttribute(leaseResult.value.attempt),
              ":leaseOwner": stringAttribute(leaseResult.value.owner),
              ":leaseFence": numberAttribute(leaseResult.value.fence),
              ":leaseAcquiredAt": stringAttribute(leaseResult.value.acquiredAt),
              ":leaseExpiresAt": stringAttribute(leaseResult.value.expiresAt),
              ":asOf": stringAttribute(input.acquiredAt),
              ...(record.lease === undefined ? {} : { ":priorFence": numberAttribute(record.lease.fence) }),
            },
          }));
        }
        return success({ disposition: "claimed", record: claimed });
      } catch (error) {
        if (!isDynamoDbConditionalFailure(error)) {
          return { ok: false, error: dynamoDbPersistenceOperationError("claim_processing") };
        }
        return resolveProcessingClaimRace(options, input.outboxEntryId, input.acquiredAt);
      }
    },

    complete: async (input) => {
      let record: PlatformProcessingRecord | null;
      try {
        record = await readProcessing(options, input.outboxEntryId);
      } catch {
        return { ok: false, error: dynamoDbPersistenceOperationError("read_processing") };
      }
      if (record?.state === "completed") return success({ disposition: "already-completed", record });
      const valid = validateCompletion(record, input.fence, input.completedAt);
      if (!valid.ok) return valid;
      if (record === null) return processingNotClaimedCompletion();
      const completed = platformProcessingRecord({
        outboxEntryId: input.outboxEntryId,
        state: "completed",
        attempt: record.attempt,
        completion: { outcome: input.outcome, completedAt: input.completedAt },
      });
      try {
        await options.client.send(new UpdateItemCommand({
          TableName: options.configuration.tableName,
          Key: processingKey(input.outboxEntryId),
          UpdateExpression: "SET #state = :completed, #completionOutcome = :outcome, #completedAt = :completedAt REMOVE #leaseOwner, #leaseFence, #leaseAcquiredAt, #leaseExpiresAt, #releasedAt",
          ConditionExpression: "#state = :claimed AND #leaseFence = :fence AND #leaseExpiresAt > :completedAt",
          ExpressionAttributeNames: {
            "#state": "state",
            "#completionOutcome": "completionOutcome",
            "#completedAt": "completedAt",
            "#leaseOwner": "leaseOwner",
            "#leaseFence": "leaseFence",
            "#leaseAcquiredAt": "leaseAcquiredAt",
            "#leaseExpiresAt": "leaseExpiresAt",
            "#releasedAt": "releasedAt",
          },
          ExpressionAttributeValues: {
            ":claimed": stringAttribute("claimed"),
            ":completed": stringAttribute("completed"),
            ":outcome": stringAttribute(input.outcome),
            ":fence": numberAttribute(input.fence),
            ":completedAt": stringAttribute(input.completedAt),
          },
        }));
        return success({ disposition: "completed", record: completed });
      } catch (error) {
        if (!isDynamoDbConditionalFailure(error)) {
          return { ok: false, error: dynamoDbPersistenceOperationError("complete_processing") };
        }
        return resolveCompletionRace(options, input.outboxEntryId, input.fence, input.completedAt);
      }
    },

    release: async (input) => {
      let record: PlatformProcessingRecord | null;
      try {
        record = await readProcessing(options, input.outboxEntryId);
      } catch {
        return { ok: false, error: dynamoDbPersistenceOperationError("read_processing") };
      }
      const valid = validateRelease(record, input.fence, input.releasedAt);
      if (!valid.ok) return valid;
      if (record === null || record.lease === undefined) {
        return failure(
          "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
          "Processing must have an active claim before it can be released.",
          "platform.persistence.processing.not_claimed",
        );
      }
      const released = platformProcessingRecord({
        outboxEntryId: input.outboxEntryId,
        state: "retry-eligible",
        attempt: record.attempt,
        lease: record.lease,
        releasedAt: input.releasedAt,
      });
      try {
        await options.client.send(new UpdateItemCommand({
          TableName: options.configuration.tableName,
          Key: processingKey(input.outboxEntryId),
          UpdateExpression: "SET #state = :retryEligible, #releasedAt = :releasedAt",
          ConditionExpression: "#state = :claimed AND #leaseFence = :fence AND #leaseExpiresAt > :releasedAt",
          ExpressionAttributeNames: {
            "#state": "state",
            "#releasedAt": "releasedAt",
            "#leaseFence": "leaseFence",
            "#leaseExpiresAt": "leaseExpiresAt",
          },
          ExpressionAttributeValues: {
            ":claimed": stringAttribute("claimed"),
            ":retryEligible": stringAttribute("retry-eligible"),
            ":fence": numberAttribute(input.fence),
            ":releasedAt": stringAttribute(input.releasedAt),
          },
        }));
        return success(released);
      } catch (error) {
        if (!isDynamoDbConditionalFailure(error)) {
          return { ok: false, error: dynamoDbPersistenceOperationError("release_processing") };
        }
        return resolveReleaseRace(options, input.outboxEntryId, input.fence, input.releasedAt);
      }
    },
  };
}

async function readProcessing(
  options: DynamoDbPlatformProcessingStoreOptions,
  outboxEntryId: OutboxEntryId,
): Promise<PlatformProcessingRecord | null> {
  const response = await options.client.send(new GetItemCommand({
    TableName: options.configuration.tableName,
    Key: processingKey(outboxEntryId),
    ConsistentRead: true,
  }));
  const item = responseItem(response);
  return item === undefined ? null : itemToProcessingRecord(item);
}

async function resolveProcessingClaimRace(
  options: DynamoDbPlatformProcessingStoreOptions,
  outboxEntryId: OutboxEntryId,
  asOf: ISODateTime,
): Promise<Result<PlatformProcessingClaimResult, PlatformPersistenceError>> {
  try {
    const record = await readProcessing(options, outboxEntryId);
    if (record?.state === "completed") return success({ disposition: "already-completed", record });
    if (record?.state === "claimed" && record.lease !== undefined && !platformLeaseExpired(record.lease, asOf)) {
      return success({ disposition: "lease-active", record });
    }
  } catch {
    return { ok: false, error: dynamoDbPersistenceOperationError("read_processing") };
  }
  return { ok: false, error: dynamoDbPersistenceOperationError("claim_processing") };
}

async function resolveCompletionRace(
  options: DynamoDbPlatformProcessingStoreOptions,
  outboxEntryId: OutboxEntryId,
  fence: PlatformPersistenceFence,
  completedAt: ISODateTime,
): Promise<Result<PlatformProcessingCompletionResult, PlatformPersistenceError>> {
  try {
    const record = await readProcessing(options, outboxEntryId);
    if (record?.state === "completed") return success({ disposition: "already-completed", record });
    return validateCompletion(record, fence, completedAt);
  } catch {
    return { ok: false, error: dynamoDbPersistenceOperationError("read_processing") };
  }
}

async function resolveReleaseRace(
  options: DynamoDbPlatformProcessingStoreOptions,
  outboxEntryId: OutboxEntryId,
  fence: PlatformPersistenceFence,
  releasedAt: ISODateTime,
): Promise<Result<PlatformProcessingRecord, PlatformPersistenceError>> {
  try {
    return validateRelease(await readProcessing(options, outboxEntryId), fence, releasedAt);
  } catch {
    return { ok: false, error: dynamoDbPersistenceOperationError("read_processing") };
  }
}

function validateCompletion(
  record: PlatformProcessingRecord | null,
  fence: PlatformPersistenceFence,
  completedAt: ISODateTime,
): Result<PlatformProcessingCompletionResult, PlatformPersistenceError> {
  if (record === null || record.state !== "claimed" || record.lease === undefined) {
    return processingNotClaimedCompletion();
  }
  if (record.lease.fence !== fence) return staleFenceCompletion();
  if (platformLeaseExpired(record.lease, completedAt)) return leaseExpiredCompletion();
  return success({ disposition: "completed", record });
}

function validateRelease(
  record: PlatformProcessingRecord | null,
  fence: PlatformPersistenceFence,
  releasedAt: ISODateTime,
): Result<PlatformProcessingRecord, PlatformPersistenceError> {
  if (record === null || record.state !== "claimed" || record.lease === undefined) {
    return failure(
      "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
      "Processing must have an active claim before it can be released.",
      "platform.persistence.processing.not_claimed",
    );
  }
  if (record.lease.fence !== fence) {
    return failure(
      "PLATFORM_PERSISTENCE_STALE_FENCE",
      "Processing release used a stale fence.",
      "platform.persistence.processing.stale_fence",
    );
  }
  if (platformLeaseExpired(record.lease, releasedAt)) {
    return failure(
      "PLATFORM_PERSISTENCE_LEASE_EXPIRED",
      "Processing release used an expired lease.",
      "platform.persistence.processing.lease.expired",
    );
  }
  return success(record);
}

function processingNotClaimedCompletion(): Result<never, PlatformPersistenceError> {
  return failure(
    "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
    "Processing must be claimed before it can complete.",
    "platform.persistence.processing.not_claimed",
  );
}

function staleFenceCompletion(): Result<never, PlatformPersistenceError> {
  return failure(
    "PLATFORM_PERSISTENCE_STALE_FENCE",
    "Processing completion used a stale fence.",
    "platform.persistence.processing.stale_fence",
  );
}

function leaseExpiredCompletion(): Result<never, PlatformPersistenceError> {
  return failure(
    "PLATFORM_PERSISTENCE_LEASE_EXPIRED",
    "Processing completion used an expired lease.",
    "platform.persistence.processing.lease.expired",
  );
}

function claimCondition(record: PlatformProcessingRecord): string {
  if (record.state === "retry-eligible") {
    return "#state = :retryEligible AND #attempt = :priorAttempt AND #leaseFence = :priorFence";
  }
  return "#state = :claimed AND #attempt = :priorAttempt AND #leaseFence = :priorFence AND #leaseExpiresAt <= :asOf";
}

function claimAttributeNames(): Record<string, string> {
  return {
    "#state": "state",
    "#attempt": "attempt",
    "#leaseOwner": "leaseOwner",
    "#leaseFence": "leaseFence",
    "#leaseAcquiredAt": "leaseAcquiredAt",
    "#leaseExpiresAt": "leaseExpiresAt",
    "#releasedAt": "releasedAt",
    "#completionOutcome": "completionOutcome",
    "#completedAt": "completedAt",
  };
}

function responseItem(response: unknown): DynamoDbPersistenceItem | undefined {
  if (typeof response !== "object" || response === null || !("Item" in response)) return undefined;
  const item = (response as { readonly Item?: unknown }).Item;
  return isItem(item) ? item : undefined;
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
