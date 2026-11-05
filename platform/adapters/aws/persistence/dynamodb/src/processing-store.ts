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
  type PlatformProcessingClaimResult,
  type PlatformProcessingCompletionResult,
  type PlatformProcessingRecord,
  type PlatformProcessingStore,
  type PlatformPersistenceDiagnosticOptions,
} from "@kanbien/platform-persistence";
import type { DynamoDbPersistenceCommandClient } from "./client";
import type { DynamoDbPersistenceConfiguration } from "./configuration/index";
import { isDynamoDbConditionalFailure } from "./errors";
import {
  itemToProcessingRecord,
  processingKey,
  processingRecordToItem,
} from "./records";
import { dynamoDbObservation, attributeObservation, responseItem, type DynamoDbObservation } from "./observations";

export interface DynamoDbPlatformProcessingStoreOptions extends PlatformPersistenceDiagnosticOptions {
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly client: DynamoDbPersistenceCommandClient;
}

export function createDynamoDbPlatformProcessingStore(
  options: DynamoDbPlatformProcessingStoreOptions,
): PlatformProcessingStore {
  return {
    get: async (outboxEntryId) => readProcessing(options, outboxEntryId),

    claim: async (input) => {
      const observed = dynamoDbObservation(options, "claim_processing");
      const reading = dynamoDbObservation(options, "read_processing");
      let record: PlatformProcessingRecord | null;
      try {
        record = await reading.at("selection", () => readProcessing(options, input.outboxEntryId, reading));
      } catch {
        return { ok: false, error: reading.error("read_processing") };
      }
      if (record?.state === "completed") return success({ disposition: "already-completed", record });
      if (record !== null && record.lease === undefined) {
        observed.reject("lease", "absent");
        return { ok: false, error: observed.error("claim_processing") };
      }
      if (record !== null && observed.at("selection", () => record.state === "claimed" && record.lease !== undefined && !platformLeaseExpired(record.lease, input.acquiredAt))) {
        return success({ disposition: "lease-active", record });
      }
      const leaseResult = observed.at("encoding", () => nextPlatformPersistenceLease({
        owner: input.owner,
        ...(record?.lease === undefined ? {} : { priorLease: record.lease }),
        priorAttempt: record?.attempt ?? initialPlatformPersistenceAttempt,
        acquiredAt: input.acquiredAt,
        durationMs: input.leaseDurationMs,
      }));
      if (!leaseResult.ok) { const error = leaseResult.error; observed.source(error); return { ok: false, error }; }
      const claimed = observed.at("encoding", () => platformProcessingRecord({
        outboxEntryId: input.outboxEntryId,
        state: "claimed",
        attempt: leaseResult.value.attempt,
        lease: leaseResult.value,
      }));
      try {
        if (record === null) {
          await observed.send(options, () => new PutItemCommand({
            TableName: options.configuration.tableName,
            Item: processingRecordToItem(claimed),
            ConditionExpression: "attribute_not_exists(#pk)",
            ExpressionAttributeNames: { "#pk": "PK" },
          }));
        } else {
          await observed.send(options, () => new UpdateItemCommand({
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
          return { ok: false, error: observed.error("claim_processing") };
        }
        return observed.at("selection", () => resolveProcessingClaimRace(options, input.outboxEntryId, input.acquiredAt, observed));
      }
    },

    complete: async (input) => {
      const observed = dynamoDbObservation(options, "complete_processing");
      const reading = dynamoDbObservation(options, "read_processing");
      let record: PlatformProcessingRecord | null;
      try {
        record = await reading.at("selection", () => readProcessing(options, input.outboxEntryId, reading));
      } catch {
        return { ok: false, error: reading.error("read_processing") };
      }
      if (record?.state === "completed") return success({ disposition: "already-completed", record });
      const valid = observed.at("selection", () => validateCompletion(record, input.fence, input.completedAt, observed));
      if (!valid.ok) return valid;
      if (record === null) { observed.reject("record", "absent"); return processingNotClaimedCompletion(observed); }
      const completed = observed.at("encoding", () => platformProcessingRecord({
        outboxEntryId: input.outboxEntryId,
        state: "completed",
        attempt: record.attempt,
        completion: { outcome: input.outcome, completedAt: input.completedAt },
      }));
      try {
        await observed.send(options, () => new UpdateItemCommand({
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
          return { ok: false, error: observed.error("complete_processing") };
        }
        return observed.at("selection", () => resolveCompletionRace(options, input.outboxEntryId, input.fence, input.completedAt, observed));
      }
    },

    release: async (input) => {
      const observed = dynamoDbObservation(options, "release_processing");
      const reading = dynamoDbObservation(options, "read_processing");
      let record: PlatformProcessingRecord | null;
      try {
        record = await reading.at("selection", () => readProcessing(options, input.outboxEntryId, reading));
      } catch {
        return { ok: false, error: reading.error("read_processing") };
      }
      const valid = observed.at("selection", () => validateRelease(record, input.fence, input.releasedAt, observed));
      if (!valid.ok) return valid;
      if (record === null || record.lease === undefined) {
        observed.reject("lease", "predicate-rejected");
        return failure(
          "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
          "Processing must have an active claim before it can be released.",
          "platform.persistence.processing.not_claimed",
          observed.evidence(),
        );
      }
      const released = observed.at("encoding", () => platformProcessingRecord({
        outboxEntryId: input.outboxEntryId,
        state: "retry-eligible",
        attempt: record.attempt,
        lease: record.lease!,
        releasedAt: input.releasedAt,
      }));
      try {
        await observed.send(options, () => new UpdateItemCommand({
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
          return { ok: false, error: observed.error("release_processing") };
        }
        return observed.at("selection", () => resolveReleaseRace(options, input.outboxEntryId, input.fence, input.releasedAt, observed));
      }
    },
  };
}

async function readProcessing(
  options: DynamoDbPlatformProcessingStoreOptions,
  outboxEntryId: OutboxEntryId,
  observed = dynamoDbObservation(options, "read_processing"),
): Promise<PlatformProcessingRecord | null> {
  const attributes = attributeObservation(options, "read_processing", "returned");
  try {
    const response = await observed.send(options, () => new GetItemCommand({
      TableName: options.configuration.tableName,
      Key: processingKey(outboxEntryId),
      ConsistentRead: true,
    }));
    const item = observed.at("response", () => responseItem(response, attributes));
    return item === undefined ? null : observed.decode(attributes, () => itemToProcessingRecord(item, attributes));
  } finally { attributes.flush(); }
}

async function resolveProcessingClaimRace(
  options: DynamoDbPlatformProcessingStoreOptions,
  outboxEntryId: OutboxEntryId,
  asOf: ISODateTime,
  observed: DynamoDbObservation,
): Promise<Result<PlatformProcessingClaimResult, PlatformPersistenceError>> {
  const reading = dynamoDbObservation(options, "read_processing", "reconciliation");
  try {
    const record = await readProcessing(options, outboxEntryId, reading);
    if (record?.state === "completed") { observed.reconcile("already-completed"); return success({ disposition: "already-completed", record }); }
    if (record !== null && observed.at("selection", () => record.state === "claimed" && record.lease !== undefined && !platformLeaseExpired(record.lease, asOf))) {
      observed.reconcile("lease-active"); return success({ disposition: "lease-active", record });
    }
  } catch {
    observed.reconcile("unavailable"); return { ok: false, error: reading.error("read_processing") };
  }
  observed.reconcile("unresolved"); return { ok: false, error: observed.error("claim_processing") };
}

async function resolveCompletionRace(
  options: DynamoDbPlatformProcessingStoreOptions,
  outboxEntryId: OutboxEntryId,
  fence: PlatformPersistenceFence,
  completedAt: ISODateTime,
  observed: DynamoDbObservation,
): Promise<Result<PlatformProcessingCompletionResult, PlatformPersistenceError>> {
  const reading = dynamoDbObservation(options, "read_processing", "reconciliation");
  try {
    const record = await readProcessing(options, outboxEntryId, reading);
    if (record?.state === "completed") { observed.reconcile("already-completed"); return success({ disposition: "already-completed", record }); }
    const valid = observed.at("selection", () => validateCompletion(record, fence, completedAt, observed));
    observed.reconcile(valid.ok ? "valid-current-state" : "unresolved");
    return valid;
  } catch {
    observed.reconcile("unavailable"); return { ok: false, error: reading.error("read_processing") };
  }
}

async function resolveReleaseRace(
  options: DynamoDbPlatformProcessingStoreOptions,
  outboxEntryId: OutboxEntryId,
  fence: PlatformPersistenceFence,
  releasedAt: ISODateTime,
  observed: DynamoDbObservation,
): Promise<Result<PlatformProcessingRecord, PlatformPersistenceError>> {
  const reading = dynamoDbObservation(options, "read_processing", "reconciliation");
  try {
    const record = await readProcessing(options, outboxEntryId, reading);
    const valid = observed.at("selection", () => validateRelease(record, fence, releasedAt, observed));
    observed.reconcile(valid.ok ? "valid-current-state" : "unresolved");
    return valid;
  } catch {
    observed.reconcile("unavailable"); return { ok: false, error: reading.error("read_processing") };
  }
}

function validateCompletion(
  record: PlatformProcessingRecord | null,
  fence: PlatformPersistenceFence,
  completedAt: ISODateTime,
  observed?: DynamoDbObservation,
): Result<PlatformProcessingCompletionResult, PlatformPersistenceError> {
  let field: "record" | "state" | "lease" = "record";
  if (record === null || (field = "state", record.state !== "claimed") || (field = "lease", record.lease === undefined)) {
    observed?.reject(field, field === "state" ? "wrong-state" : "absent");
    return processingNotClaimedCompletion(observed);
  }
  if (record.lease.fence !== fence) { observed?.reject("fence", "stale"); return staleFenceCompletion(observed); }
  if (platformLeaseExpired(record.lease, completedAt)) { observed?.reject("lease", "expired"); return leaseExpiredCompletion(observed); }
  return success({ disposition: "completed", record });
}

function validateRelease(
  record: PlatformProcessingRecord | null,
  fence: PlatformPersistenceFence,
  releasedAt: ISODateTime,
  observed?: DynamoDbObservation,
): Result<PlatformProcessingRecord, PlatformPersistenceError> {
  let field: "record" | "state" | "lease" = "record";
  if (record === null || (field = "state", record.state !== "claimed") || (field = "lease", record.lease === undefined)) {
    return failure(
      "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
      "Processing must have an active claim before it can be released.",
      "platform.persistence.processing.not_claimed",
      observed?.reject(field, field === "state" ? "wrong-state" : "absent"),
    );
  }
  if (record.lease.fence !== fence) {
    return failure(
      "PLATFORM_PERSISTENCE_STALE_FENCE",
      "Processing release used a stale fence.",
      "platform.persistence.processing.stale_fence",
      observed?.reject("fence", "stale"),
    );
  }
  if (platformLeaseExpired(record.lease, releasedAt)) {
    return failure(
      "PLATFORM_PERSISTENCE_LEASE_EXPIRED",
      "Processing release used an expired lease.",
      "platform.persistence.processing.lease.expired",
      observed?.reject("lease", "expired"),
    );
  }
  return success(record);
}

function processingNotClaimedCompletion(observed?: DynamoDbObservation): Result<never, PlatformPersistenceError> {
  return failure(
    "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
    "Processing must be claimed before it can complete.",
    "platform.persistence.processing.not_claimed",
    observed?.evidence(),
  );
}

function staleFenceCompletion(observed?: DynamoDbObservation): Result<never, PlatformPersistenceError> {
  return failure(
    "PLATFORM_PERSISTENCE_STALE_FENCE",
    "Processing completion used a stale fence.",
    "platform.persistence.processing.stale_fence",
    observed?.evidence(),
  );
}

function leaseExpiredCompletion(observed?: DynamoDbObservation): Result<never, PlatformPersistenceError> {
  return failure(
    "PLATFORM_PERSISTENCE_LEASE_EXPIRED",
    "Processing completion used an expired lease.",
    "platform.persistence.processing.lease.expired",
    observed?.evidence(),
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
