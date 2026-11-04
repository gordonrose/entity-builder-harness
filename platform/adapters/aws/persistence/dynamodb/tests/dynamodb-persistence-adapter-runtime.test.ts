import { deepEqual, equal, match, rejects, throws } from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
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
  corePersistenceValidationRecord,
} from "@kanbien/core/persistence";
import {
  platformOutboxRecord,
  platformPersistenceLeaseOwner,
  platformPersistenceFence,
  type PlatformPersistenceTransactionScope,
} from "@kanbien/platform-persistence";
import {
  createDynamoDbPlatformOutboxStore,
  createAwsSdkDynamoDbPersistenceCommandClient,
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
  processingRecordToItem,
  itemToOutboxRecord,
  type DynamoDbPersistenceItem,
} from "../src/records";
import { attributeObservation, dynamoDbObservation } from "../src/observations";
import { dynamoDbPersistenceConfiguration as publicConfiguration, type DynamoDbPersistenceConfiguration as PublicConfiguration, type DynamoDbPersistenceConfigurationError as PublicConfigurationError } from "../src/index";
import { dynamoDbPersistenceConfiguration as groupedConfiguration, type DynamoDbPersistenceConfiguration as GroupedConfiguration, type DynamoDbPersistenceConfigurationError as GroupedConfigurationError } from "../src/configuration/index";

function configurationSafety(): void {
  equal(dynamoDbPersistenceConfiguration, publicConfiguration);
  equal(publicConfiguration, groupedConfiguration, "public root and grouped index expose one checker");
  const base: PublicConfiguration = { region: "region", tableName: "records", outboxDueIndexName: "due", lineageCauseIndexName: "cause" };
  const sameType: GroupedConfiguration = base;
  deepEqual(groupedConfiguration(sameType), { ok: true, value: base });
  const canary = "synthetic-private-config-canary";
  const fields = [["region", "region"], ["tableName", "store"], ["outboxDueIndexName", "outbox-index"], ["lineageCauseIndexName", "lineage-index"]] as const;
  const check = (input: unknown) => dynamoDbPersistenceConfiguration(input as GroupedConfiguration);
  const expected = (path: string, field: string, reason: "missing" | "wrong-type" | "wrong-shape") => ({ ok: false, error: {
    code: "PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID",
    defaultMessage: "DynamoDB persistence adapter configuration is invalid.",
    details: { path, reason: reason === "missing" ? "A required value is missing." : reason === "wrong-type" ? "A text value is required." : "A configuration object is required." },
    diagnosticRecord: { schema: "core/diagnostic-record/v1", code: "persistence.configuration-input-invalid", definitionVersion: 1, detail: { field, reason } },
  } });
  for (const [path, field] of fields) {
    const omitted = { ...base } as Record<string, unknown>;
    delete omitted[path];
    deepEqual(check(omitted), expected(path, field, "missing"));
    deepEqual(check({ ...base, [path]: undefined }), expected(path, field, "missing"));
    for (const value of [null, 1, NaN, Infinity, false, [], { privateValue: canary }, Symbol(canary), 1n, () => canary]) {
      const result = check({ ...base, [path]: value });
      deepEqual(result, expected(path, field, "wrong-type"));
      equal(JSON.stringify(result).includes(canary), false);
    }
    for (const value of ["", " ", "\t\n"]) {
      deepEqual(check({ ...base, [path]: value }), { ok: false, error: {
        code: "PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID",
        defaultMessage: "DynamoDB persistence adapter configuration is invalid.",
        details: { path, reason: "A non-empty value is required." },
        diagnosticRecord: { schema: "core/diagnostic-record/v1", code: "persistence.configuration-invalid", definitionVersion: 1, detail: { field, reason: "blank" } },
      } });
    }
  }
  for (const input of [undefined, null, false, 2, canary, [], Symbol(canary), 1n, () => base]) {
    const result = check(input);
    deepEqual(result, expected("configuration", "configuration", "wrong-shape"));
    equal(JSON.stringify(result).includes(canary), false);
  }
  deepEqual(check({}), expected("region", "region", "missing"));
  deepEqual(check({ ...base, lineageCauseIndexName: null, tableName: null, region: null }), expected("region", "region", "wrong-type"));
  const failure = check({ ...base, region: 1 });
  if (failure.ok) throw new Error("Expected configuration failure.");
  const publicError: PublicConfigurationError = failure.error;
  const newError: GroupedConfigurationError = publicError;
  equal(newError.code, "PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID");

  const padded = { region: " region ", tableName: " records ", outboxDueIndexName: " due ", lineageCauseIndexName: " cause " };
  deepEqual(check(padded), { ok: true, value: padded }, "accepted strings are not silently trimmed");
  const extra = { ...base, extra: "retained" };
  const copied = check(extra);
  deepEqual(copied, { ok: true, value: extra });
  if (copied.ok) equal(copied.value === extra, false, "success retains copy semantics");
  const extraBlank = check({ ...base, extra: " " });
  equal(extraBlank.ok, false);
  if (!extraBlank.ok) {
    equal(extraBlank.error.details.path, "extra");
    deepEqual(extraBlank.error.diagnosticRecord?.detail, { field: "configuration", reason: "blank" });
  }
  throws(() => check({ ...base, extra: 1 }), TypeError, "extra-property hardening remains deferred");
  const orderedBlank = check({ tableName: "", region: "", outboxDueIndexName: "due", lineageCauseIndexName: "cause" });
  equal(orderedBlank.ok, false);
  if (!orderedBlank.ok) equal(orderedBlank.error.details.path, "tableName", "existing blank rejection follows supplied entry order");

  const reads: string[] = [];
  const getters = Object.fromEntries(Object.entries(base).map(([key, value]) => [key, value]));
  for (const [key, value] of Object.entries(base)) Object.defineProperty(getters, key, { enumerable: true, get() { reads.push(key); return value; } });
  deepEqual(check(getters), { ok: true, value: base });
  deepEqual(reads, ["region", "tableName", "outboxDueIndexName", "lineageCauseIndexName", "tableName", "outboxDueIndexName", "lineageCauseIndexName", "region", "tableName", "outboxDueIndexName", "lineageCauseIndexName"], "Core checking must not reread the supplied accessors");
  const original = new Error(canary);
  throws(() => check({ ...base, get region() { throw original; } }), (error) => error === original);
  let conversions = 0;
  const nonText = { toString() { conversions++; throw original; }, valueOf() { conversions++; throw original; } };
  deepEqual(check({ ...base, region: nonText }), expected("region", "region", "wrong-type"));
  equal(conversions, 0, "wrong-type diagnostics must not coerce or inspect submitted content");

  const filename = require.resolve("../src/configuration/domain/validation");
  const localRequire = createRequire(filename);
  const shared = localRequire("@kanbien/core/config") as typeof import("@kanbien/core/config");
  const fixture = { exports: {} as typeof import("../src/configuration/domain/validation") };
  const calls: string[] = [];
  let forced: "none" | "missing" | "blank" = "none";
  new Function("require", "module", "exports", readFileSync(filename, "utf8"))(
    (name: string) => name === "@kanbien/core/config" ? { ...shared,
      stringConfigValue(source: Parameters<typeof shared.stringConfigValue>[0], key: string) {
        calls.push(key);
        if (forced === "missing" && key === "tableName") return shared.stringConfigValue({ get: () => undefined }, key);
        if (forced === "blank" && key === "region") return { ok: true, value: "" };
        return shared.stringConfigValue(source, key);
      },
    } : localRequire(name), fixture, fixture.exports,
  );
  deepEqual(fixture.exports.dynamoDbPersistenceConfiguration(base), { ok: true, value: base });
  deepEqual(calls, ["region", "tableName", "outboxDueIndexName", "lineageCauseIndexName"], "actual checker must use the shared Core reader for every required field");
  forced = "missing";
  deepEqual(fixture.exports.dynamoDbPersistenceConfiguration(base), expected("tableName", "store", "missing"), "shared rejection cannot be ignored");
  forced = "blank";
  const transformed = fixture.exports.dynamoDbPersistenceConfiguration(base);
  equal(transformed.ok, false, "subsequent checking must use the returned checked text");
  if (!transformed.ok) deepEqual(transformed.error.diagnosticRecord?.detail, { field: "region", reason: "blank" });
}

async function main(): Promise<void> {
  configurationSafety();
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

  // Own command facts and a complete source primary/eight travel independently.
  const seen: DiagnosticRecord[] = [];
  const onDiagnostic = (record: DiagnosticRecord) => { seen.push(record); };
  const details = (record: DiagnosticRecord) => record.detail as Readonly<Record<string, unknown>>;
  const commandsSeen = () => seen.filter((record) => record.definitionVersion === 4 || record.code === "persistence.command-condition-observed");
  const issuesSeen = () => seen.filter((record) => record.code === "persistence.stored-attribute-observed");
  const mutation = { recordChange: change, outboxEntry: entry };
  const nativeCases = [
    ["AccessDeniedException", "access-rejected", "persistence.runtime-permission-denied"],
    ["UnrecognizedClientException", "identity-unrecognized", "persistence.credential-rejected"],
    ["ExpiredTokenException", "credential-expired", "persistence.credential-rejected"],
    ["ConditionalCheckFailedException", "condition-rejected", "persistence.command-condition-observed"],
    ["TransactionCanceledException", "transaction-canceled", "persistence.unclassified-failure"],
    ["ResourceNotFoundException", "resource-unavailable", "persistence.unclassified-failure"],
    ["ValidationException", "input-rejected", "persistence.unclassified-failure"],
    ["ProvisionedThroughputExceededException", "throughput-exceeded", "persistence.unclassified-failure"],
    ["RequestLimitExceeded", "request-limit-exceeded", "persistence.unclassified-failure"],
    ["ThrottlingException", "throttled", "persistence.unclassified-failure"],
    ["TimeoutError", "timeout", "persistence.operation-timed-out"],
    ["NetworkingError", "network-failure", "persistence.transport-unavailable"],
  ] as const;
  for (const [name, condition, code] of nativeCases) {
    seen.length = 0;
    const result = await createDynamoDbPlatformPersistenceFactWriter({ configuration, onDiagnostic,
      client: { send: async () => { throw Object.freeze({ name, message: "PRIVATE_NATIVE_CANARY" }); } },
    }).write(mutation);
    equal(result.ok, false);
    equal(seen.length, 1);
    equal(seen[0]!.code, code);
    equal(seen[0]!.definitionVersion, condition === "condition-rejected" ? 1 : 4);
    deepEqual(details(seen[0]!), { operation: "write_facts", boundary: "invocation", role: "primary", condition, codeStatus: "recognized", effect: "unknown",
      ...(condition === "transaction-canceled" ? { cancellation: { availability: "absent", truncated: false, reasons: [] } } : {}) });
    if (!result.ok) deepEqual(result.error.params, { operation: "write_facts", provider_failure_class: "unknown" });
    equal(JSON.stringify(seen).includes("PRIVATE_NATIVE_CANARY"), false);
  }
  const sourceRecords = (["empty", "untrimmed", "duplicate", "too-many", "not-positive", "negative", "required", "invalid-format", "unsupported"] as const).map((reason) =>
    corePersistenceValidationRecord({ operation: "record-id", field: "id", reason }));
  const fullSource = Object.freeze({ name: "NetworkingError", diagnosticRecord: sourceRecords[0], relatedDiagnosticRecords: sourceRecords.slice(1) });
  seen.length = 0;
  const sourceFailure = await createDynamoDbPlatformPersistenceFactWriter({ configuration, onDiagnostic, client: { send: async () => { throw fullSource; } } }).write(mutation);
  equal(sourceFailure.ok, false);
  equal(seen.length, 10);
  deepEqual(seen.slice(1), sourceRecords);
  if (!sourceFailure.ok) { deepEqual(sourceFailure.error.diagnosticRecord, sourceRecords[0]); deepEqual(sourceFailure.error.relatedDiagnosticRecords, sourceRecords.slice(1)); }

  for (const [cause, status] of [[17, "absent"], [null, "absent"], [{ name: 1 }, "wrong-type"], [{ name: "PRIVATE_UNKNOWN_CANARY" }, "unrecognized"], [Object.defineProperty({}, "name", { get() { throw new Error("must not inspect accessor"); } }), "unavailable"]] as const) {
    seen.length = 0;
    await createDynamoDbPlatformPersistenceFactWriter({ configuration, onDiagnostic, client: { send: async () => { throw cause; } } }).write(mutation);
    equal(details(seen[0]!).codeStatus, status);
    equal(seen[0]!.code, "persistence.unclassified-failure");
    equal(JSON.stringify(seen).includes("PRIVATE_UNKNOWN_CANARY"), false);
  }
  seen.length = 0;
  let cancellationAccessorReads = 0;
  const canceled = { name: "TransactionCanceledException", CancellationReasons: Array.from({ length: 70 }, (_, ordinal) => ordinal === 1
    ? Object.defineProperty({}, "Code", { get() { cancellationAccessorReads++; return "ConditionalCheckFailed"; } })
    : { Code: ordinal === 0 ? "ConditionalCheckFailed" : "PRIVATE_REASON_CANARY", Message: "PRIVATE_NATIVE_CANARY" }) };
  await createDynamoDbPlatformPersistenceFactWriter({ configuration, onDiagnostic, client: { send: async () => { throw canceled; } } }).write(mutation);
  const cancellation = details(seen[0]!).cancellation as { reasons: readonly { ordinal: number; condition: string; codeStatus: string }[]; truncated: boolean };
  equal(cancellation.reasons.length, 64); equal(cancellation.truncated, true); equal(cancellationAccessorReads, 0);
  deepEqual(cancellation.reasons[0], { ordinal: 0, condition: "condition-rejected", codeStatus: "recognized" });
  deepEqual(cancellation.reasons[1], { ordinal: 1, condition: "unclassified", codeStatus: "unavailable" });
  equal(JSON.stringify(seen).includes("PRIVATE_REASON_CANARY"), false);

  // Method selection precedes argument construction and retains the SDK receiver.
  seen.length = 0;
  const order: string[] = [];
  const receiverClient = { get send() { order.push("select"); return async function(this: unknown) { equal(this, receiverClient); order.push("invoke"); return {}; }; } };
  const orderedConfiguration = { ...configuration, get tableName() { order.push("encode"); return configuration.tableName; } };
  equal((await createDynamoDbPlatformOutboxStore({ configuration: orderedConfiguration, client: receiverClient, onDiagnostic }).create(entry)).ok, true);
  deepEqual(order, ["select", "encode", "invoke"]);
  const original = new Error("PRIVATE_THROW_CANARY");
  const throwingClient = Object.defineProperty({}, "send", { get() { throw original; } }) as DynamoDbPersistenceCommandClient;
  order.length = 0;
  equal((await createDynamoDbPlatformOutboxStore({ configuration: orderedConfiguration, client: throwingClient, onDiagnostic }).create(entry)).ok, false);
  deepEqual(order, []); equal(details(commandsSeen().at(-1)!).boundary, "selection"); equal(details(commandsSeen().at(-1)!).effect, "not-invoked");
  await rejects(createDynamoDbPlatformOutboxStore({ configuration, client: throwingClient, onDiagnostic }).get(entry.id), (error) => error === original);
  seen.length = 0;
  throws(() => createAwsSdkDynamoDbPersistenceCommandClient({ ...configuration, get region(): string { throw original; } }, { onDiagnostic }), (error) => error === original);
  deepEqual(details(seen[0]!), { operation: "client-initialization", boundary: "client-construction", role: "primary", condition: "unclassified", codeStatus: "not-inspected", effect: "not-invoked" });

  // Rejecting guards must not add getter reads or persistence calls.
  let limitReads = 0;
  let sends = 0;
  const guards = createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: { send: async () => { sends++; return {}; } } });
  seen.length = 0;
  const badLimit = await guards.listDeliverable({ asOf: at(0), get limit() { if (++limitReads > 1) throw original; return 0.5; } });
  equal(badLimit.ok, false); equal(limitReads, 1); equal(sends, 0); equal(details(seen[0]!).condition, "not-integer");
  seen.length = 0; limitReads = 0;
  const zeroLimit = await guards.listDeliverable({ asOf: at(0), get limit() { if (++limitReads > 2) throw original; return 0; } });
  equal(zeroLimit.ok, false); equal(limitReads, 2); equal(details(seen[0]!).condition, "not-positive");
  for (const sink of [() => { throw original; }, async () => { throw original; }]) {
    equal((await createDynamoDbPlatformOutboxStore({ configuration, client: { send: async () => { throw { name: "ValidationException" }; } }, onDiagnostic: sink }).create(entry)).ok, false);
  }
  const unsafeOptions = Object.defineProperty({ configuration, client: { send: async () => { throw original; } } }, "diagnosticDefinitions", { get() { throw original; } });
  equal((await createDynamoDbPlatformPersistenceFactWriter(unsafeOptions).write(mutation)).ok, false);

  // Malformed envelope reductions remain unchanged; missing item is ordinary.
  for (const response of [null, 5, { Item: [] }, { Item: null }]) {
    seen.length = 0;
    equal(await createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: { send: async () => response } }).get(entry.id), null);
    equal(issuesSeen().length, 1); equal(details(issuesSeen()[0]!).reduction, "null");
  }
  seen.length = 0;
  equal(await guards.get(entry.id), null); equal(seen.length, 0);
  for (const response of [{ Items: null }, { Items: "PRIVATE_ITEM_CANARY" }, null]) {
    seen.length = 0;
    const result = await createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: { send: async () => response } }).listDeliverable({ asOf: at(0), limit: 1 });
    equal(result.ok, true); if (result.ok) deepEqual(result.value, []);
    equal(details(issuesSeen()[0]!).reduction, "empty-list");
  }
  seen.length = 0;
  const mixed = await createDynamoDbPlatformRecordChangeStore({ configuration, onDiagnostic, client: { send: async () => ({ Items: [null, 7, recordChangeToItem(change), null] }) } }).findByRecord(subject);
  equal(mixed.length, 1);
  const mixedIssues = details(issuesSeen()[0]!).issues as readonly { field: string; condition: string; rowOrdinal: number; count?: number }[];
  deepEqual(mixedIssues, [{ field: "item", condition: "null", rowOrdinal: 0, count: 2 }, { field: "item", condition: "not-object", rowOrdinal: 1 }]);
  // A custom filter can return rows despite its predicate: don't infer a reduction.
  const customItems: unknown[] = [null];
  Object.defineProperty(customItems, "filter", { value(predicate: (value: unknown, ordinal: number) => boolean) { predicate(null, 0); return [recordChangeToItem(change)]; } });
  seen.length = 0;
  equal((await createDynamoDbPlatformRecordChangeStore({ configuration, onDiagnostic, client: { send: async () => ({ Items: customItems }) } }).findByCause(causationId("request-1"))).length, 1);
  equal(details(issuesSeen()[0]!).reduction, "returned");

  const goodOutbox = outboxRecordToItem(platformOutboxRecord({ entry }));
  const decodeCases: readonly [DynamoDbPersistenceItem, string, string][] = [
    [{ ...goodOutbox, subjectKind: {} } as unknown as DynamoDbPersistenceItem, "subjectKind", "string-component-absent"],
    [{ ...goodOutbox, messageVersion: {} } as unknown as DynamoDbPersistenceItem, "messageVersion", "number-component-absent"],
    [{ ...goodOutbox, messageVersion: { N: "1.5" } }, "messageVersion", "not-safe-integer"],
    [{ ...goodOutbox, subjectKind: { S: "BAD_KIND" } }, "subjectKind", "invalid-format"],
    [{ ...goodOutbox, state: { S: "PRIVATE_STATE_CANARY" } }, "state", "closed-value-rejected"],
    [{ ...goodOutbox, createdAt: { S: "bad-date" } }, "createdAt", "invalid-format"],
  ];
  for (const [item, field, condition] of decodeCases) {
    seen.length = 0;
    await rejects(createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: { send: async () => ({ Item: item }) } }).get(entry.id), TypeError);
    const issues = details(issuesSeen().at(-1)!).issues as readonly { field: string; condition: string }[];
    equal(issues[0]!.field, field); equal(issues[0]!.condition, condition);
    equal(details(issuesSeen().at(-1)!).reduction, "thrown");
  }
  equal(itemToOutboxRecord({ ...goodOutbox, messageVersion: { N: "01" } }).entry.messageVersion, 1);
  const goodProcessing = processingRecordToItem(processingClaim.value.record);
  const processingDecodeCases: readonly [DynamoDbPersistenceItem, string, string][] = [
    [{ ...goodProcessing, state: { S: "PRIVATE_STATE_CANARY" } }, "state", "closed-value-rejected"],
    [{ ...goodProcessing, completionOutcome: { S: "PRIVATE_OUTCOME_CANARY" } }, "completionOutcome", "closed-value-rejected"],
    [{ ...goodProcessing, completionOutcome: { S: "succeeded" } }, "completedAt", "string-component-absent"],
    [{ ...goodProcessing, leaseFence: { N: "1.5" } }, "leaseFence", "not-safe-integer"],
    [{ ...goodProcessing, leaseExpiresAt: { S: "bad-date" } }, "leaseExpiresAt", "invalid-format"],
  ];
  for (const [item, field, condition] of processingDecodeCases) {
    seen.length = 0;
    await rejects(createDynamoDbPlatformProcessingStore({ configuration, onDiagnostic, client: { send: async () => ({ Item: item }) } }).get(entry.id), TypeError);
    const issues = details(issuesSeen()[0]!).issues as readonly { field: string; condition: string }[];
    equal(issuesSeen().length, 1); equal(issues[0]!.field, field); equal(issues[0]!.condition, condition);
    equal(commandsSeen().length, 0, "Known processing guard rejection is not an unknown command failure");
  }
  let optionalReads = 0;
  itemToOutboxRecord({ ...goodOutbox, get tenantId() { optionalReads++; return { S: "tenant-1" }; } }); equal(optionalReads, 2);
  seen.length = 0;
  const getterItem = { ...goodOutbox, get subjectKind(): never { throw original; } };
  await rejects(createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: { send: async () => ({ Item: getterItem }) } }).get(entry.id), (error) => error === original);
  equal(issuesSeen().length, 0); equal(details(commandsSeen()[0]!).boundary, "decoding"); equal(commandsSeen()[0]!.code, "persistence.unclassified-failure");
  const lineageCases: readonly [DynamoDbPersistenceItem, string, string][] = [
    [{ ...recordChangeToItem(change), actorKind: { S: "system" } }, "actor", "incomplete"],
    [{ ...recordChangeToItem(change), action: { S: "bad" } }, "action", "closed-value-rejected"],
    [{ ...recordChangeToItem(change), actorKind: { S: "bad" }, actorId: { S: "safe" } }, "actorKind", "closed-value-rejected"],
    [{ ...recordChangeToItem(change), changedFields: { S: "bad" } }, "changedFields", "not-array"],
    [{ ...recordChangeToItem(change), changedFields: { L: [{ N: "1" }] } }, "changedFields", "string-component-absent"],
    [{ ...recordChangeToItem(change), changedFields: { L: [{ S: "" }] } }, "changedFields", "invalid-format"],
    [{ ...recordChangeToItem(change), changedFields: { L: [{ S: "safe" }, { S: "safe" }] } }, "changedFields", "duplicate"],
    [{ ...recordChangeToItem(change), changedFields: { L: Array.from({ length: 33 }, (_, ordinal) => ({ S: "field" + ordinal })) } }, "changedFields", "too-many"],
  ];
  for (const [item, field, condition] of lineageCases) {
    seen.length = 0;
    await rejects(createDynamoDbPlatformRecordChangeStore({ configuration, onDiagnostic, client: { send: async () => ({ Items: [item] }) } }).findByRecord(subject));
    const issues = details(issuesSeen().at(-1)!).issues as readonly { field: string; condition: string }[];
    equal(issues[0]!.field, field); equal(issues[0]!.condition, condition);
  }
  seen.length = 0;
  const bounded = attributeObservation({ onDiagnostic }, "read_lineage", "returned");
  const fields = ["response", "item", "items", "attribute", "outboxEntryId", "subjectKind", "subjectId", "messageType", "messageVersion", "deliveryPolicy", "createdAt", "tenantId", "correlationId", "causationId", "state", "attempt", "leaseOwner"] as const;
  fields.forEach((field) => bounded.issue(field, "absent")); bounded.flush();
  equal((details(seen[0]!).issues as unknown[]).length, 16); equal(details(seen[0]!).truncated, true);

  // Conditional races preserve successful validation without a second write.
  const leasedOutbox = claim.value.record;
  const claimedProcessing = processingClaim.value.record;
  for (const kind of ["publish", "complete", "release"] as const) {
    seen.length = 0; let calls = 0;
    const raceClient: DynamoDbPersistenceCommandClient = { send: async (command) => { calls++;
      if (command instanceof GetItemCommand) return { Item: kind === "publish" ? outboxRecordToItem(leasedOutbox) : processingRecordToItem(claimedProcessing) };
      throw { name: "ConditionalCheckFailedException" };
    } };
    const result = kind === "publish" ? await createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: raceClient }).markPublished({ id: entry.id, fence: leasedOutbox.lease!.fence, publishedAt: at(1) })
      : kind === "complete" ? await createDynamoDbPlatformProcessingStore({ configuration, onDiagnostic, client: raceClient }).complete({ outboxEntryId: entry.id, fence: claimedProcessing.lease!.fence, completedAt: at(1), outcome: "succeeded" })
      : await createDynamoDbPlatformProcessingStore({ configuration, onDiagnostic, client: raceClient }).release({ outboxEntryId: entry.id, fence: claimedProcessing.lease!.fence, releasedAt: at(1) });
    equal(result.ok, true); equal(calls, 3);
    equal(details(commandsSeen()[0]!).condition, "condition-rejected");
    const reconciled = seen.find((record) => record.code === "persistence.reconciliation-observed")!;
    equal(reconciled.definitionVersion, 2); equal(details(reconciled).observed, "valid-current-state"); equal(details(reconciled).effect, "read-result-observed");
  }
  for (const [kind, outcome] of [["outbox", "missing"], ["outbox", "already-published"], ["outbox", "lease-active"], ["outbox", "unresolved"], ["outbox", "unavailable"],
    ["processing", "already-completed"], ["processing", "lease-active"], ["processing", "unresolved"], ["processing", "unavailable"]] as const) {
    seen.length = 0; let reads = 0; let writes = 0;
    const raceClient: DynamoDbPersistenceCommandClient = { send: async (command) => {
      if (!(command instanceof GetItemCommand)) { writes++; throw { name: "ConditionalCheckFailedException" }; }
      reads++;
      if (reads === 1) return kind === "outbox" ? { Item: goodOutbox } : {};
      if (outcome === "unavailable") throw Object.freeze({ ...fullSource, name: "NetworkingError" });
      if (outcome === "missing" || (kind === "processing" && outcome === "unresolved")) return {};
      if (kind === "outbox") return { Item: outboxRecordToItem(outcome === "already-published" ? platformOutboxRecord({ entry, state: "published", publishedAt: at(1) }) : outcome === "lease-active" ? leasedOutbox : platformOutboxRecord({ entry })) };
      return { Item: processingRecordToItem(outcome === "already-completed" ? { ...claimedProcessing, state: "completed", completion: { outcome: "succeeded", completedAt: at(1) } } : claimedProcessing) };
    } };
    const result = kind === "outbox" ? await createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: raceClient }).claim({ id: entry.id, owner, acquiredAt: at(1), leaseDurationMs: 60_000 })
      : await createDynamoDbPlatformProcessingStore({ configuration, onDiagnostic, client: raceClient }).claim({ outboxEntryId: entry.id, owner, acquiredAt: at(1), leaseDurationMs: 60_000 });
    equal(reads, 2); equal(writes, 1);
    equal(result.ok, outcome === "already-published" || outcome === "already-completed" || outcome === "lease-active");
    equal(details(seen.find((record) => record.code === "persistence.reconciliation-observed")!).observed, outcome);
    if (outcome === "unavailable") {
      deepEqual(seen.filter((record) => record.code === "core.persistence.validation-rejected"), sourceRecords);
      equal(details(commandsSeen().at(-1)!).role, "reconciliation");
    }
  }
  // State/fence/expiry local predicates are independent of legacy result codes.
  for (const [kind, item, fence, time, field, condition] of [
    ["publish", undefined, leasedOutbox.lease!.fence, at(1), "record", "not-found"],
    ["publish", goodOutbox, leasedOutbox.lease!.fence, at(1), "state", "wrong-state"],
    ["publish", { ...goodOutbox, state: { S: "leased" } }, leasedOutbox.lease!.fence, at(1), "lease", "absent"],
    ["publish", outboxRecordToItem(leasedOutbox), accepted(platformPersistenceFence(2)), at(1), "fence", "stale"],
    ["publish", outboxRecordToItem(leasedOutbox), leasedOutbox.lease!.fence, at(60), "lease", "expired"],
    ["complete", undefined, claimedProcessing.lease!.fence, at(1), "record", "absent"],
    ["release", { ...processingRecordToItem(claimedProcessing), state: { S: "retry-eligible" } }, claimedProcessing.lease!.fence, at(1), "state", "wrong-state"],
    ["complete", { outboxEntryId: { S: entry.id }, state: { S: "claimed" }, attempt: { N: "1" } }, claimedProcessing.lease!.fence, at(1), "lease", "absent"],
    ["release", processingRecordToItem(claimedProcessing), claimedProcessing.lease!.fence, at(60), "lease", "expired"],
  ] as const) {
    seen.length = 0; let calls = 0;
    const localClient: DynamoDbPersistenceCommandClient = { send: async () => { calls++; return item === undefined ? {} : { Item: item }; } };
    const result = kind === "publish" ? await createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: localClient }).markPublished({ id: entry.id, fence, publishedAt: time })
      : kind === "complete" ? await createDynamoDbPlatformProcessingStore({ configuration, onDiagnostic, client: localClient }).complete({ outboxEntryId: entry.id, fence, completedAt: time, outcome: "succeeded" })
      : await createDynamoDbPlatformProcessingStore({ configuration, onDiagnostic, client: localClient }).release({ outboxEntryId: entry.id, fence, releasedAt: time });
    equal(result.ok, false); equal(calls, 1); equal(details(seen.at(-1)!).field, field); equal(details(seen.at(-1)!).condition, condition);
  }

  let nativeNameReads = 0;
  const nameGetter = Object.defineProperty({}, "name", { get() { nativeNameReads++; return "ValidationException"; } });
  seen.length = 0;
  await createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: { send: async () => { throw nameGetter; } } }).create(entry);
  equal(nativeNameReads, 1); equal(details(seen[0]!).codeStatus, "unavailable");
  nativeNameReads = 0;
  await createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: { send: async () => { throw nameGetter; } } }).listDeliverable({ asOf: at(0), limit: 1 });
  equal(nativeNameReads, 2);

  // Atomic guards, original participant-slot reads and invocation-local sinks.
  seen.length = 0;
  let atomicSends = 0;
  const observedWriter = createDynamoDbPlatformPersistenceAtomicWriter({ configuration, onDiagnostic, client: { send: async () => { atomicSends++; throw original; } } });
  const participant = { Put: { TableName: configuration.tableName, Item: {} } };
  let escapedScope: PlatformPersistenceTransactionScope | undefined;
  await observedWriter.run(async (scope) => { escapedScope = scope; return ok(undefined); });
  equal(details(seen.at(-1)!).field, "participant"); equal(details(seen.at(-1)!).condition, "missing");
  const closed = await escapedScope!.stage(mutation); equal(closed.ok, false); equal(details(seen.at(-1)!).condition, "closed");
  const unsupported = stageDynamoDbTransactionWrite({ afterCommit() {} }, {}); equal(unsupported.ok, false);
  for (const [write, condition] of [[{}, "absent"], [{ Put: participant.Put, Delete: { TableName: configuration.tableName, Key: {} } }, "too-large"]] as const) {
    seen.length = 0;
    await observedWriter.run((scope) => stageDynamoDbTransactionWrite(scope.transaction, write));
    equal(details(seen[0]!).field, "participant"); equal(details(seen[0]!).condition, condition);
  }
  const slotReads: string[] = [];
  await observedWriter.run((scope) => { const write = Object.fromEntries(["Put", "Update", "Delete", "ConditionCheck"].map((slot) => [slot, undefined]));
    for (const slot of Object.keys(write)) Object.defineProperty(write, slot, { get() { slotReads.push(slot); return slot === "Put" ? null : undefined; } });
    equal(stageDynamoDbTransactionWrite(scope.transaction, write).ok, true); return ok(undefined);
  });
  deepEqual(slotReads, ["Put", "Update", "Delete", "ConditionCheck"]);
  seen.length = 0;
  await observedWriter.run((scope) => { stageDynamoDbTransactionWrite(scope.transaction, participant); return ok(undefined); });
  equal(details(seen.at(-1)!).field, "mutation"); equal(atomicSends, 0);
  seen.length = 0;
  await observedWriter.run((scope) => { throws(() => scope.transaction.afterCommit(() => {}), TypeError); return ok(undefined); });
  equal(details(seen[0]!).field, "after-commit"); equal(details(seen[0]!).condition, "unsupported");
  seen.length = 0;
  await observedWriter.run(async (scope) => { stageDynamoDbTransactionWrite(scope.transaction, participant); for (let index = 0; index < 49; index++) equal((await scope.stage(mutation)).ok, true);
    equal((await scope.stage(mutation)).ok, false); return { ok: false as const, error: original }; });
  equal(details(seen[0]!).field, "mutation"); equal(details(seen[0]!).condition, "too-large"); equal(atomicSends, 0);
  seen.length = 0;
  await observedWriter.run((scope) => { for (let index = 0; index < 100; index++) equal(stageDynamoDbTransactionWrite(scope.transaction, participant).ok, true);
    equal(stageDynamoDbTransactionWrite(scope.transaction, participant).ok, false); return { ok: false as const, error: original }; });
  equal(details(seen[0]!).field, "participant"); equal(details(seen[0]!).condition, "too-large");
  seen.length = 0;
  await observedWriter.run(() => { throw original; }, {}); equal(seen.length, 0);
  const left: DiagnosticRecord[] = []; const right: DiagnosticRecord[] = [];
  await Promise.all([observedWriter.run(async () => { await Promise.resolve(); throw fullSource; }, { onDiagnostic: (record) => left.push(record) }),
    observedWriter.run(async () => { await Promise.resolve(); throw 0; }, { onDiagnostic: (record) => right.push(record) })]);
  equal(seen.length, 0); equal(left.length, 10); equal(right.length, 1); equal(details(left[0]!).boundary, "callback");
  equal(JSON.stringify([...left, ...right, ...seen]).includes("PRIVATE_THROW_CANARY"), false);

  // Review regressions: pre-send synchronous boundaries retain their original scope.
  const assertPreSend = async (action: () => Promise<unknown>, boundary: "selection" | "encoding", calls: () => number, expectedCalls: number): Promise<void> => {
    seen.length = 0;
    await rejects(action(), (error) => error === fullSource);
    equal(calls(), expectedCalls);
    equal(seen.length, 10);
    deepEqual(details(seen[0]!), { operation: details(seen[0]!).operation, boundary, role: "primary", condition: "unclassified", codeStatus: "not-inspected", effect: "not-invoked" });
    deepEqual(seen.slice(1), sourceRecords);
  };
  let preSendCalls = 0;
  const preSendClient: DynamoDbPersistenceCommandClient = { send: async () => { preSendCalls++; return {}; } };
  await assertPreSend(() => createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: preSendClient }).create({ ...entry, get subject(): never { throw fullSource; } }), "encoding", () => preSendCalls, 0);
  let throwingLimitReads = 0;
  await assertPreSend(() => createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: preSendClient }).listDeliverable({ asOf: at(0), get limit(): never { throwingLimitReads++; throw fullSource; } }), "selection", () => preSendCalls, 0);
  equal(throwingLimitReads, 1);

  for (const operation of ["claim-outbox", "publish-outbox", "claim-processing", "complete-processing", "release-processing"] as const) {
    seen.length = 0; preSendCalls = 0;
    let idReads = 0;
    const failId = (): never => { idReads++; throw fullSource; };
    const options = { configuration, onDiagnostic, client: preSendClient };
    const result = operation === "claim-outbox" ? await createDynamoDbPlatformOutboxStore(options).claim({ get id() { return failId(); }, owner, acquiredAt: at(0), leaseDurationMs: 60_000 })
      : operation === "publish-outbox" ? await createDynamoDbPlatformOutboxStore(options).markPublished({ get id() { return failId(); }, fence: leasedOutbox.lease!.fence, publishedAt: at(1) })
      : operation === "claim-processing" ? await createDynamoDbPlatformProcessingStore(options).claim({ get outboxEntryId() { return failId(); }, owner, acquiredAt: at(0), leaseDurationMs: 60_000 })
      : operation === "complete-processing" ? await createDynamoDbPlatformProcessingStore(options).complete({ get outboxEntryId() { return failId(); }, fence: claimedProcessing.lease!.fence, completedAt: at(1), outcome: "succeeded" })
      : await createDynamoDbPlatformProcessingStore(options).release({ get outboxEntryId() { return failId(); }, fence: claimedProcessing.lease!.fence, releasedAt: at(1) });
    const readOperation = operation.endsWith("outbox") ? "read_outbox" : "read_processing";
    equal(result.ok, false); equal(idReads, 1); equal(preSendCalls, 0);
    if (!result.ok) {
      equal(result.error.code, "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED");
      deepEqual(result.error.params, { operation: readOperation, provider_failure_class: readOperation === "read_outbox" ? "transport" : "unknown" });
      deepEqual(result.error.diagnosticRecord, sourceRecords[0]); deepEqual(result.error.relatedDiagnosticRecords, sourceRecords.slice(1));
    }
    equal(seen.length, 10); equal(commandsSeen().length, 1); equal(seen[0]!.code, "persistence.unclassified-failure");
    deepEqual(details(seen[0]!), { operation: readOperation, boundary: "selection", role: "primary", condition: "unclassified", codeStatus: "not-inspected", effect: "not-invoked" });
    deepEqual(seen.slice(1), sourceRecords);
  }

  for (const kind of ["publish-arguments", "publish-record", "complete-arguments", "complete-record", "release-arguments", "release-record", "claim-record"] as const) {
    preSendCalls = 0;
    let fieldReads = 0;
    const selectedClient: DynamoDbPersistenceCommandClient = { send: async (command) => { preSendCalls++;
      if (!(command instanceof GetItemCommand)) throw new Error("Preflight must not send a mutation.");
      if (kind === "claim-record") return {};
      return { Item: kind.startsWith("publish") ? outboxRecordToItem(leasedOutbox) : processingRecordToItem(claimedProcessing) };
    } };
    const observationOptions = { configuration, onDiagnostic, client: selectedClient };
    if (kind.startsWith("publish")) {
      await assertPreSend(() => createDynamoDbPlatformOutboxStore(observationOptions).markPublished({ id: entry.id, fence: leasedOutbox.lease!.fence,
        get publishedAt() { fieldReads++; if (kind === "publish-arguments" || fieldReads === 2) throw fullSource; return at(1); } }),
      kind === "publish-arguments" ? "selection" : "encoding", () => preSendCalls, 1);
    } else if (kind.startsWith("complete")) {
      await assertPreSend(() => createDynamoDbPlatformProcessingStore(observationOptions).complete({ outboxEntryId: entry.id, fence: claimedProcessing.lease!.fence, outcome: "succeeded",
        get completedAt() { fieldReads++; if (kind === "complete-arguments" || fieldReads === 2) throw fullSource; return at(1); } }),
      kind === "complete-arguments" ? "selection" : "encoding", () => preSendCalls, 1);
    } else if (kind.startsWith("release")) {
      await assertPreSend(() => createDynamoDbPlatformProcessingStore(observationOptions).release({ outboxEntryId: entry.id, fence: claimedProcessing.lease!.fence,
        get releasedAt() { fieldReads++; if (kind === "release-arguments" || fieldReads === 2) throw fullSource; return at(1); } }),
      kind === "release-arguments" ? "selection" : "encoding", () => preSendCalls, 1);
    } else {
      await assertPreSend(() => createDynamoDbPlatformProcessingStore(observationOptions).claim({ owner, acquiredAt: at(0), leaseDurationMs: 60_000,
        get outboxEntryId() { fieldReads++; if (fieldReads === 2) throw fullSource; return entry.id; } }), "encoding", () => preSendCalls, 1);
    }
    equal(fieldReads, kind.endsWith("arguments") ? 1 : 2);
  }

  // A current known guard emits one coalesced own record, not a command failure.
  seen.length = 0;
  let oldGuardError: unknown;
  await rejects(createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: { send: async () => ({ Item: { ...goodOutbox, subjectKind: {} } }) } }).get(entry.id), (error) => {
    oldGuardError = error; return error instanceof TypeError && error.message === "Stored persistence item is missing subjectKind.";
  });
  equal(seen.length, 1); equal(issuesSeen().length, 1); equal(commandsSeen().length, 0);
  seen.length = 0;
  await rejects(createDynamoDbPlatformOutboxStore({ configuration, onDiagnostic, client: { send: async () => ({ Item: { ...goodOutbox, get subjectKind(): never { throw oldGuardError; } } }) } }).get(entry.id), (error) => error === oldGuardError);
  equal(seen.length, 2); equal(commandsSeen().length, 1); equal(details(seen[0]!).boundary, "decoding");
  equal(issuesSeen().length, 1, "Only the old error's selected source survives; no new invalid-row observation is created.");
  seen.length = 0;
  const currentAttributes = attributeObservation({ onDiagnostic }, "read_outbox", "returned");
  const currentDecode = dynamoDbObservation({ onDiagnostic }, "read_outbox");
  throws(() => currentDecode.decode(currentAttributes, () => { throw currentAttributes.failure("Guard fixture.", "subjectKind", "contract-rejected", fullSource); }), TypeError);
  currentAttributes.flush();
  equal(seen.length, 10); equal(issuesSeen().length, 1); equal(commandsSeen().length, 0); deepEqual(seen.slice(1), sourceRecords);

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
