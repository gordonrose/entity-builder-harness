import { deepEqual, equal, match } from "node:assert/strict";
import {
  GetItemCommand,
  PutItemCommand,
  QueryCommand,
  TransactWriteItemsCommand,
  UpdateItemCommand,
} from "@aws-sdk/client-dynamodb";
import {
  causationId,
  isoDateTimeFromDate,
  ok,
} from "@kanbien/core/shared";
import {
  outboxDeliveryPolicy,
  outboxEntry,
  outboxEntryId,
  outboxMessageType,
  recordChange,
  recordChangeId,
  recordId,
  recordKind,
  recordReference,
  recordRevision,
} from "@kanbien/core/persistence";
import {
  platformOutboxRecord,
  platformPersistenceLeaseOwner,
} from "@kanbien/platform-persistence";
import {
  createDynamoDbPlatformOutboxStore,
  createDynamoDbPlatformPersistenceAtomicWriter,
  createDynamoDbPlatformPersistenceFactWriter,
  createDynamoDbPlatformProcessingStore,
  createDynamoDbPlatformRecordChangeStore,
  dynamoDbPersistenceConfiguration,
  stageDynamoDbTransactionWrite,
  type DynamoDbPersistenceCommandClient,
} from "../src/index";
import {
  dynamoDbPersistenceOperationError,
  dynamoDbPersistenceProviderFailureClass,
} from "../src/errors";
import {
  outboxRecordToItem,
  recordChangeToItem,
} from "../src/records";

async function main(): Promise<void> {
  const configuration = accepted(dynamoDbPersistenceConfiguration({
    region: "eu-west-1",
    tableName: "platform-smoke-persistence",
    outboxDueIndexName: "due-index",
    lineageCauseIndexName: "cause-index",
  }));
  const invalid = dynamoDbPersistenceConfiguration({
    region: "",
    tableName: "table",
    outboxDueIndexName: "due",
    lineageCauseIndexName: "cause",
  });
  equal(invalid.ok, false);

  // Provider diagnostics are deliberately reduced to a finite, safe category.
  equal(
    dynamoDbPersistenceProviderFailureClass({ name: "AccessDeniedException" }),
    "access_denied",
  );
  equal(
    dynamoDbPersistenceProviderFailureClass({ name: "ValidationException" }),
    "validation",
  );
  equal(dynamoDbPersistenceProviderFailureClass({ name: "UnexpectedProviderError" }), "unknown");
  deepEqual(
    dynamoDbPersistenceOperationError("claim_outbox", { name: "ConditionalCheckFailedException" }).params,
    { operation: "claim_outbox", provider_failure_class: "conditional_check_failed" },
  );

  const at = (seconds: number) => isoDateTimeFromDate(new Date(Date.parse("2026-09-24T12:00:00.000Z") + (seconds * 1_000)));
  const subject = recordReference({
    kind: accepted(recordKind("platform-smoke.work-item")),
    id: accepted(recordId("work-1")),
  });
  const entry = outboxEntry({
    id: outboxEntryId("outbox-1"),
    subject,
    messageType: accepted(outboxMessageType("platform-smoke.work.accepted")),
    deliveryPolicy: accepted(outboxDeliveryPolicy("platform-short-idempotent-work.v1")),
    createdAt: at(0),
    causationId: causationId("request-1"),
  });
  const change = accepted(recordChange({
    id: recordChangeId("change-1"),
    record: subject,
    revision: accepted(recordRevision(1)),
    action: "created",
    occurredAt: at(0),
    causationId: causationId("request-1"),
  }));
  const owner = accepted(platformPersistenceLeaseOwner("relay-a"));
  const commands: unknown[] = [];
  let storedOutbox = platformOutboxRecord({ entry });
  const client: DynamoDbPersistenceCommandClient = {
    send: async (command) => {
      commands.push(command);
      if (command instanceof GetItemCommand) {
        return { Item: outboxRecordToItem(storedOutbox) };
      }
      if (command instanceof QueryCommand) {
        if (command.input.IndexName === "due-index") {
          return { Items: [outboxRecordToItem(storedOutbox)] };
        }
        return { Items: [recordChangeToItem(change)] };
      }
      return {};
    },
  };

  const outbox = createDynamoDbPlatformOutboxStore({ configuration, client });
  const created = await outbox.create(entry);
  equal(created.ok, true);
  const createCommand = commands[0];
  equal(createCommand instanceof PutItemCommand, true);
  if (createCommand instanceof PutItemCommand) {
    equal(createCommand.input.TableName, configuration.tableName);
    equal(createCommand.input.Item?.PK?.S, "OUTBOX#outbox-1");
    equal(createCommand.input.Item?.DueSort?.S, "DUE#2026-09-24T12:00:00.000Z#outbox-1");
    equal(createCommand.input.Item?.causationId?.S, "request-1");
  }

  const claim = await outbox.claim({
    id: entry.id,
    owner,
    acquiredAt: at(0),
    leaseDurationMs: 60_000,
  });
  equal(claim.ok, true);
  if (!claim.ok || claim.value.disposition !== "claimed") throw new Error("Expected a relay claim.");
  const claimCommand = commands.at(-1);
  equal(claimCommand instanceof UpdateItemCommand, true);
  if (claimCommand instanceof UpdateItemCommand) {
    match(claimCommand.input.ConditionExpression ?? "", /#state = :pending/);
    equal(claimCommand.input.ExpressionAttributeValues?.[":leaseFence"]?.N, "1");
    equal(claimCommand.input.ExpressionAttributeValues?.[":dueSort"]?.S, "DUE#2026-09-24T12:01:00.000Z#outbox-1");
    equal(claimCommand.input.ExpressionAttributeValues?.[":asOf"], undefined);
    equal(claimCommand.input.ExpressionAttributeValues?.[":priorFence"], undefined);
    assertExpressionValuesAreUsed(claimCommand);
  }
  storedOutbox = claim.value.record;

  const reclaimed = await outbox.claim({
    id: entry.id,
    owner,
    acquiredAt: at(61),
    leaseDurationMs: 60_000,
  });
  equal(reclaimed.ok, true);
  if (!reclaimed.ok || reclaimed.value.disposition !== "claimed") throw new Error("Expected an expired relay lease to be reclaimed.");
  const reclaimCommand = commands.at(-1);
  equal(reclaimCommand instanceof UpdateItemCommand, true);
  if (reclaimCommand instanceof UpdateItemCommand) {
    match(reclaimCommand.input.ConditionExpression ?? "", /#state = :leased/);
    equal(reclaimCommand.input.ExpressionAttributeValues?.[":pending"], undefined);
    equal(reclaimCommand.input.ExpressionAttributeValues?.[":priorFence"]?.N, "1");
    equal(reclaimCommand.input.ExpressionAttributeValues?.[":asOf"]?.S, at(61));
    assertExpressionValuesAreUsed(reclaimCommand);
  }
  storedOutbox = reclaimed.value.record;

  const published = await outbox.markPublished({
    id: entry.id,
    fence: reclaimed.value.record.lease!.fence,
    publishedAt: at(62),
  });
  equal(published.ok, true);
  const publishCommand = commands.at(-1);
  equal(publishCommand instanceof UpdateItemCommand, true);
  if (publishCommand instanceof UpdateItemCommand) {
    match(publishCommand.input.ConditionExpression ?? "", /#leaseFence = :fence/);
    match(publishCommand.input.ConditionExpression ?? "", /#leaseExpiresAt > :publishedAt/);
    equal(publishCommand.input.ExpressionAttributeValues?.[":fence"]?.N, "2");
  }

  const deliverable = await outbox.listDeliverable({ asOf: at(0), limit: 2 });
  equal(deliverable.ok, true);
  const dueQuery = commands.at(-1);
  equal(dueQuery instanceof QueryCommand, true);
  if (dueQuery instanceof QueryCommand) {
    equal(dueQuery.input.IndexName, "due-index");
    equal(dueQuery.input.ExpressionAttributeValues?.[":dueKey"]?.S, "OUTBOX#DELIVERABLE");
    equal(dueQuery.input.ExpressionAttributeValues?.[":dueSort"]?.S, "DUE#2026-09-24T12:00:00.000Z#￿");
  }

  const lineage = createDynamoDbPlatformRecordChangeStore({ configuration, client });
  const appended = await lineage.append(change);
  equal(appended.ok, true);
  const lineagePut = commands.at(-1);
  equal(lineagePut instanceof PutItemCommand, true);
  if (lineagePut instanceof PutItemCommand) {
    equal(lineagePut.input.Item?.PK?.S, "LINEAGE#platform-smoke.work-item#work-1");
    equal(lineagePut.input.Item?.CauseKey?.S, "CAUSE#request-1");
  }
  const foundByCause = await lineage.findByCause(causationId("request-1"));
  deepEqual(foundByCause.map((found) => found.id), [change.id]);

  const processingCommands: unknown[] = [];
  let storedProcessing: Record<string, unknown> | undefined;
  const processingClient: DynamoDbPersistenceCommandClient = {
    send: async (command) => {
      processingCommands.push(command);
      if (command instanceof GetItemCommand) return storedProcessing === undefined ? {} : { Item: storedProcessing };
      if (command instanceof PutItemCommand) storedProcessing = command.input.Item as Record<string, unknown>;
      return {};
    },
  };
  const processing = createDynamoDbPlatformProcessingStore({ configuration, client: processingClient });
  const processingClaim = await processing.claim({
    outboxEntryId: entry.id,
    owner: accepted(platformPersistenceLeaseOwner("worker-a")),
    acquiredAt: at(0),
    leaseDurationMs: 60_000,
  });
  equal(processingClaim.ok, true);
  equal(processingCommands.at(-1) instanceof PutItemCommand, true);
  const processingPut = processingCommands.at(-1);
  if (processingPut instanceof PutItemCommand) {
    equal(processingPut.input.Item?.PK?.S, "PROCESSING#outbox-1");
    equal(processingPut.input.Item?.leaseFence?.N, "1");
  }
  if (!processingClaim.ok || processingClaim.value.disposition !== "claimed") {
    throw new Error("Expected a durable processing claim.");
  }
  const completed = await processing.complete({
    outboxEntryId: entry.id,
    fence: processingClaim.value.record.lease!.fence,
    outcome: "succeeded",
    completedAt: at(1),
  });
  equal(completed.ok, true);
  const completionCommand = processingCommands.at(-1);
  equal(completionCommand instanceof UpdateItemCommand, true);
  if (completionCommand instanceof UpdateItemCommand) {
    match(completionCommand.input.ConditionExpression ?? "", /#leaseFence = :fence/);
    match(completionCommand.input.ConditionExpression ?? "", /#leaseExpiresAt > :completedAt/);
    equal(completionCommand.input.ExpressionAttributeValues?.[":outcome"]?.S, "succeeded");
  }

  const writerCommands: unknown[] = [];
  const writer = createDynamoDbPlatformPersistenceFactWriter({
    configuration,
    client: { send: async (command) => { writerCommands.push(command); return {}; } },
  });
  const written = await writer.write({ recordChange: change, outboxEntry: entry });
  equal(written.ok, true);
  const transaction = writerCommands[0];
  equal(transaction instanceof TransactWriteItemsCommand, true);
  if (transaction instanceof TransactWriteItemsCommand) {
    equal(transaction.input.TransactItems?.length, 2);
    equal(transaction.input.TransactItems?.[0]?.Put?.Item?.recordType?.S, "lineage");
    equal(transaction.input.TransactItems?.[1]?.Put?.Item?.recordType?.S, "outbox");
  }

  const atomicCommands: unknown[] = [];
  const atomicWriter = createDynamoDbPlatformPersistenceAtomicWriter({
    configuration,
    client: { send: async (command) => { atomicCommands.push(command); return {}; } },
  });
  const atomic = await atomicWriter.run(async (scope) => {
    const participant = stageDynamoDbTransactionWrite(scope.transaction, {
      Put: {
        TableName: configuration.tableName,
        Item: {
          PK: { S: "SMOKE-WORK-ITEM#work-1" },
          SK: { S: "SMOKE-WORK-ITEM" },
          recordType: { S: "platform-smoke-work-item" },
          state: { S: "accepted" },
          revision: { N: "1" },
        },
        ConditionExpression: "attribute_not_exists(#pk)",
        ExpressionAttributeNames: { "#pk": "PK" },
      },
    });
    if (!participant.ok) return participant;
    const staged = await scope.stage({ recordChange: change, outboxEntry: entry });
    if (!staged.ok) return staged;
    return ok("committed");
  });
  equal(atomic.ok, true);
  if (!atomic.ok) throw new Error("Expected a complete three-record atomic transaction.");
  equal(atomic.value, "committed");
  const atomicCommand = atomicCommands[0];
  equal(atomicCommand instanceof TransactWriteItemsCommand, true);
  if (atomicCommand instanceof TransactWriteItemsCommand) {
    equal(atomicCommand.input.TransactItems?.length, 3);
    equal(atomicCommand.input.TransactItems?.[0]?.Put?.Item?.recordType?.S, "platform-smoke-work-item");
    equal(atomicCommand.input.TransactItems?.[1]?.Put?.Item?.recordType?.S, "lineage");
    equal(atomicCommand.input.TransactItems?.[2]?.Put?.Item?.recordType?.S, "outbox");
  }

  const missingParticipant = await atomicWriter.run(async (scope) => {
    const staged = await scope.stage({ recordChange: change, outboxEntry: entry });
    if (!staged.ok) return staged;
    return ok("not-committed");
  });
  equal(missingParticipant.ok, false);
  equal(atomicCommands.length, 1);

  const conditional = createDynamoDbPlatformOutboxStore({
    configuration,
    client: { send: async () => { throw { name: "ConditionalCheckFailedException" }; } },
  });
  const duplicate = await conditional.create(entry);
  equal(duplicate.ok, false);
  if (!duplicate.ok) equal(duplicate.error.code, "PLATFORM_PERSISTENCE_DUPLICATE_OUTBOX_ENTRY");

  const claimFailure = createDynamoDbPlatformOutboxStore({
    configuration,
    client: {
      send: async (command) => {
        if (command instanceof GetItemCommand) return { Item: outboxRecordToItem(platformOutboxRecord({ entry })) };
        throw { name: "ValidationException" };
      },
    },
  });
  const failedClaim = await claimFailure.claim({
    id: entry.id,
    owner,
    acquiredAt: at(0),
    leaseDurationMs: 60_000,
  });
  equal(failedClaim.ok, false);
  if (!failedClaim.ok) {
    equal(failedClaim.error.code, "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED");
    deepEqual(failedClaim.error.params, {
      operation: "claim_outbox",
      provider_failure_class: "validation",
    });
  }

  console.log("DynamoDB persistence adapter runtime test passed.");
}

function accepted<TValue>(result: { readonly ok: true; readonly value: TValue } | { readonly ok: false }): TValue {
  if (!result.ok) throw new Error("Expected a valid test fixture.");
  return result.value;
}

function assertExpressionValuesAreUsed(command: UpdateItemCommand): void {
  const expression = `${command.input.UpdateExpression ?? ""} ${command.input.ConditionExpression ?? ""}`;
  for (const placeholder of Object.keys(command.input.ExpressionAttributeValues ?? {})) {
    equal(expression.includes(placeholder), true, `Expression value ${placeholder} must be referenced by this DynamoDB request.`);
  }
}

main()
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
