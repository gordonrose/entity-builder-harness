import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import * as sqsSdk from "@aws-sdk/client-sqs";
import {
  ChangeMessageVisibilityCommand,
  DeleteMessageCommand,
  ReceiveMessageCommand,
  SendMessageCommand,
} from "@aws-sdk/client-sqs";
import {
  causationId,
  correlationId,
  isoDateTime,
  queueDelaySeconds,
  queueIdempotencyKey,
  queueMessage,
  queueMessageId,
  queueMessageType,
  type QueueMessageType,
  coreQueueValidationDiagnosticRecord,
  coreQueueBoundaryDiagnosticRecord,
  type DiagnosticRecord,
  type CoreQueueDiagnosticContext,
} from "@kanbien/core";
import {
  createAwsSdkPlatformSqsWorkerQueueFromEnv,
  createAwsSdkPlatformSqsQueue,
  createAwsSdkPlatformSqsWorkerQueue,
  createPlatformSqsQueue,
  createPlatformSqsWorkerQueue,
  type PlatformSqsCommandClient,
} from "../src/index";
import { decodePlatformQueueMessage } from "../src/messages";
import { receiveReductions, sqsObservation } from "../src/observations";

const queueUrl = "https://sqs.eu-west-1.amazonaws.com/123456789012/worker";

async function main(): Promise<void> {
  const durableMessage = platformQueueMessage();
  const commands: unknown[] = [];
  const client: PlatformSqsCommandClient = {
    send: async (command) => {
      commands.push(command);
      if (command instanceof ReceiveMessageCommand) {
        return {
          Messages: [{
            MessageId: "provider-delivery-1",
            ReceiptHandle: "receipt-1",
            Attributes: { ApproximateReceiveCount: "2" },
            Body: JSON.stringify({
              id: durableMessage.id,
              type: durableMessage.type,
              version: durableMessage.version,
              enqueuedAt: durableMessage.enqueuedAt,
              correlationId: durableMessage.correlationId,
              causationId: durableMessage.causationId,
              idempotencyKey: durableMessage.idempotencyKey,
              payload: durableMessage.payload,
            }),
          }],
        };
      }
      return {};
    },
  };

  const producer = createPlatformSqsQueue<{ readonly outboxEntryId: string }>({ queueUrl, client });
  const sendResult = await producer.send(durableMessage, {
    delaySeconds: accepted(queueDelaySeconds(30)),
  });
  equal(sendResult.ok, true);
  const sent = commands[0];
  equal(sent instanceof SendMessageCommand, true);
  if (!(sent instanceof SendMessageCommand)) throw new Error("Expected SQS send command.");
  deepEqual(sent.input, {
    QueueUrl: queueUrl,
    DelaySeconds: 30,
    MessageBody: JSON.stringify({
      id: "outbox-1",
      type: "platform-smoke.rebuild",
      version: 1,
      enqueuedAt: "2026-09-23T12:00:00.000Z",
      correlationId: "correlation-1",
      causationId: "request-1",
      idempotencyKey: "outbox-1",
      payload: { outboxEntryId: "outbox-1" },
    }),
  });

  const worker = createPlatformSqsWorkerQueue({
    queueUrl,
    waitTimeSeconds: 20,
    visibilityTimeoutSeconds: 120,
    client,
  });
  const delivery = await worker.receive();
  equal(delivery.kind, "delivery");
  if (delivery.kind !== "delivery") throw new Error("Expected SQS delivery.");
  equal(delivery.receiveCount, 2);
  deepEqual(delivery.message, durableMessage);
  equal(String(delivery.message.id), "outbox-1");
  equal(String(delivery.message.causationId), "request-1");
  const receive = commands[1];
  equal(receive instanceof ReceiveMessageCommand, true);
  if (!(receive instanceof ReceiveMessageCommand)) throw new Error("Expected SQS receive command.");
  deepEqual(receive.input, {
    QueueUrl: queueUrl,
    MaxNumberOfMessages: 1,
    WaitTimeSeconds: 20,
    VisibilityTimeout: 120,
    MessageSystemAttributeNames: ["ApproximateReceiveCount"],
  });

  await worker.acknowledge(delivery.receiptHandle);
  await worker.release(delivery.receiptHandle);
  const acknowledge = commands[2];
  const release = commands[3];
  equal(acknowledge instanceof DeleteMessageCommand, true);
  equal(release instanceof ChangeMessageVisibilityCommand, true);
  if (!(acknowledge instanceof DeleteMessageCommand) || !(release instanceof ChangeMessageVisibilityCommand)) {
    throw new Error("Expected acknowledgement and release commands.");
  }
  deepEqual(acknowledge.input, { QueueUrl: queueUrl, ReceiptHandle: "receipt-1" });
  deepEqual(release.input, { QueueUrl: queueUrl, ReceiptHandle: "receipt-1", VisibilityTimeout: 0 });

  const empty = createPlatformSqsWorkerQueue({
    queueUrl,
    waitTimeSeconds: 1,
    visibilityTimeoutSeconds: 120,
    client: { send: async () => ({ Messages: [] }) },
  });
  deepEqual(await empty.receive(), { kind: "empty" });

  const invalid = createPlatformSqsWorkerQueue({
    queueUrl,
    waitTimeSeconds: 1,
    visibilityTimeoutSeconds: 120,
    client: {
      send: async () => ({
        Messages: [{
          MessageId: "provider-delivery-invalid",
          ReceiptHandle: "receipt-invalid",
          Body: '{"payload":"must-not-appear-in-error"}',
        }],
      }),
    },
  });
  const invalidResult = await invalid.receive();
  equal(invalidResult.kind, "invalid");
  if (invalidResult.kind !== "invalid") throw new Error("Expected invalid SQS delivery.");
  equal(invalidResult.error.code, "PLATFORM_ADAPTER_AWS_SQS_MESSAGE_INVALID");
  equal(JSON.stringify(invalidResult.error).includes("must-not-appear-in-error"), false);

  const failedProducer = createPlatformSqsQueue({
    queueUrl,
    client: { send: async () => { throw new Error("provider detail must not escape"); } },
  });
  const failedSend = await failedProducer.send(durableMessage);
  equal(failedSend.ok, false);
  if (!failedSend.ok) {
    equal(failedSend.error.code, "QUEUE_SEND_FAILED");
    equal(JSON.stringify(failedSend.error).includes("provider detail must not escape"), false);
  }

  const missingConfig = createAwsSdkPlatformSqsWorkerQueueFromEnv({});
  equal(missingConfig.ok, false);
  if (!missingConfig.ok) {
    equal(missingConfig.error.code, "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID");
    equal(missingConfig.error.details?.path, "PLATFORM_WORKER_SQS_QUEUE_URL");
  }

  const records: DiagnosticRecord[] = [];
  const contexts: CoreQueueDiagnosticContext[] = [];
  const onDiagnostic = (record: DiagnosticRecord, context: CoreQueueDiagnosticContext) => { records.push(record); contexts.push(context); };
  const clear = () => { records.length = 0; contexts.length = 0; };
  const detail = (record: DiagnosticRecord) => record.detail as Record<string, unknown>;
  const issues = () => records.filter((record) => record.code === "core.queue.receive-reduced");
  const boundaries = () => records.filter((record) => record.code === "core.queue.boundary-failed");
  const sourceRecords = Array.from({ length: 9 }, () => coreQueueValidationDiagnosticRecord({ operation: "validate", field: "attempt", reason: "not-positive", effect: "rejected" }));
  const source = Object.freeze({ diagnosticRecord: sourceRecords[0], relatedDiagnosticRecords: sourceRecords.slice(1), message: "PRIVATE_SQS_CANARY" });
  const baseWorker = { queueUrl, waitTimeSeconds: 0, visibilityTimeoutSeconds: 120 };
  for (const operation of ["send", "receive", "acknowledge", "release"] as const) {
    for (const rejected of [false, true]) {
      clear(); let calls = 0;
      const failing: PlatformSqsCommandClient = { send() { calls++; if (rejected) return Promise.reject(source); throw source; } };
      const queue = createPlatformSqsWorkerQueue({ ...baseWorker, client: failing, onDiagnostic });
      if (operation === "send") {
        const result = await createPlatformSqsQueue({ queueUrl, client: failing, onDiagnostic }).send(durableMessage);
        equal(result.ok, false); if (!result.ok) { equal(result.error.defaultMessage, "AWS SQS did not accept the queue message."); deepEqual(result.error.relatedDiagnosticRecords, sourceRecords.slice(1)); }
      } else await rejects(operation === "receive" ? queue.receive() : queue[operation]("PRIVATE_RECEIPT"), (error: unknown) => {
        equal((error as { defaultMessage: string }).defaultMessage, `AWS SQS ${operation} operation failed.`); return true;
      });
      equal(calls, 1); equal(records.length, 10); deepEqual(records.slice(1), sourceRecords);
      deepEqual(detail(records[0]!), { operation, boundary: "invocation", reason: rejected ? "rejected" : "threw", effect: "unknown", native: { codeAvailability: "absent", condition: "unknown" } });
      contexts.forEach((context) => { equal(context, contexts[0]); deepEqual(context, { operation, boundary: "invocation" }); });
      equal(JSON.stringify(records).includes("PRIVATE_SQS_CANARY"), false);
      equal(JSON.stringify(records).includes("PRIVATE_RECEIPT"), false);
    }
  }
  for (const cause of [0, "PRIVATE_SQS_CANARY", Object.freeze(new Error("PRIVATE_SQS_CANARY")), Object.defineProperty({}, "diagnosticRecord", { get() { throw new Error("Do not read source accessor"); } })]) {
    clear(); await createPlatformSqsQueue({ queueUrl, onDiagnostic, client: { send: async () => { throw cause; } } }).send(durableMessage);
    equal(records.length, 1); equal(detail(records[0]!).effect, "unknown");
  }
  let sends = 0;
  const quietClient: PlatformSqsCommandClient = { send: async () => { sends++; return {}; } };
  const observedProducer = createPlatformSqsQueue({ queueUrl, client: quietClient, onDiagnostic });
  clear(); equal((await observedProducer.send({ ...durableMessage, messageGroupKey: "PRIVATE_GROUP" as never })).ok, false);
  equal(sends, 0); deepEqual(detail(records[0]!), { operation: "send", field: "message-group-key", reason: "unsupported", effect: "rejected" });
  for (const [value, reason] of [[0.5, "not-integer"], [-1, "negative"], [901, "above-maximum"]] as const) {
    clear(); equal((await observedProducer.send(durableMessage, { delaySeconds: value as never })).ok, false); equal(detail(records[0]!).reason, reason); equal(sends, 0);
  }
  clear(); let groupReads = 0;
  await rejects(observedProducer.send({ ...durableMessage, get messageGroupKey(): never { groupReads++; throw source; } }), (error) => error === source);
  equal(groupReads, 1); equal(records.length, 10); equal(detail(records[0]!).boundary, "selection"); equal(sends, 0);
  clear(); let delayReads = 0;
  await rejects(observedProducer.send(durableMessage, { get delaySeconds(): never { delayReads++; throw source; } }), (error) => error === source);
  equal(delayReads, 1); equal(sends, 0); equal(detail(records[0]!).boundary, "selection");

  const order: string[] = [];
  const receiverClient = { get send() { order.push("selection"); return async function(this: unknown) { equal(this, receiverClient); order.push("invocation"); return {}; }; } };
  const ordered = createPlatformSqsQueue({ get queueUrl() { order.push("encoding"); return queueUrl; }, client: receiverClient, onDiagnostic });
  order.length = 0; equal((await ordered.send(durableMessage)).ok, true); deepEqual(order, ["selection", "encoding", "invocation"]);
  clear(); order.length = 0;
  const selectionClient = Object.defineProperty({}, "send", { get() { order.push("selection"); throw source; } }) as PlatformSqsCommandClient;
  const selectionQueue = createPlatformSqsQueue({ get queueUrl() { order.push("encoding"); return queueUrl; }, client: selectionClient, onDiagnostic });
  order.length = 0; equal((await selectionQueue.send(durableMessage)).ok, false); deepEqual(order, ["selection"]); equal(detail(records[0]!).effect, "not-invoked");
  const handles = createPlatformSqsWorkerQueue({ ...baseWorker, client: quietClient, onDiagnostic });
  for (const operation of ["acknowledge", "release"] as const) {
    clear(); await rejects(handles[operation](""), (error: unknown) => { equal((error as Error).message, "receiptHandle must not be empty."); return error instanceof RangeError; });
    equal(records.length, 1); equal(detail(records[0]!).field, "receipt-handle"); equal(sends, 0);
    clear(); await rejects(handles[operation](Object.defineProperty({}, "length", { get() { throw source; } }) as never), (error) => error === source);
    equal(records.length, 10); equal(detail(records[0]!).boundary, "selection");
  }

  for (const response of [{}, { Messages: [] }]) {
    clear(); deepEqual(await createPlatformSqsWorkerQueue({ ...baseWorker, onDiagnostic, client: { send: async () => response } }).receive(), { kind: "empty" }); equal(records.length, 0);
  }
  for (const [response, field] of [[null, "response"], [{ Messages: "PRIVATE_BODY" }, "messages"], [{ Messages: [null] }, "message"]] as const) {
    clear(); deepEqual(await createPlatformSqsWorkerQueue({ ...baseWorker, onDiagnostic, client: { send: async () => response } }).receive(), { kind: "empty" });
    equal(records.length, 1); equal(issues().length, 1); equal((detail(records[0]!).issues as { field: string }[])[0]!.field, field);
  }
  for (const [count, expected] of [[undefined, 1], ["", 1], ["0", 1], ["-1", 1], ["1.5", 1], ["0x10", 16], ["1e3", 1000], ["9007199254740992", 9007199254740992]] as const) {
    clear(); const result = await createPlatformSqsWorkerQueue({ ...baseWorker, onDiagnostic, client: { send: async (): Promise<unknown> => ({ Messages: [{ ReceiptHandle: "safe", Body: sent.input.MessageBody, Attributes: { ApproximateReceiveCount: count } }] }) } }).receive();
    equal(result.kind, "delivery"); if (result.kind === "delivery") equal(result.receiveCount, expected);
    equal(issues().length, expected === 1 ? 1 : 0);
  }
  clear(); await rejects(createPlatformSqsWorkerQueue({ ...baseWorker, onDiagnostic, client: { send: async () => ({ Messages: [{ Body: sent.input.MessageBody }] }) } }).receive());
  equal(boundaries().length, 0); equal(records[0]!.code, "core.queue.validation-rejected"); equal(detail(records[0]!).field, "receipt-handle");
  clear(); const emptyReceipt = await createPlatformSqsWorkerQueue({ ...baseWorker, onDiagnostic, client: { send: async () => ({ Messages: [{ ReceiptHandle: "", Body: "bad", Attributes: { ApproximateReceiveCount: "1" } }] }) } }).receive();
  equal(emptyReceipt.kind, "invalid"); if (emptyReceipt.kind === "invalid") equal(emptyReceipt.receiptHandle, "");
  equal(detail(boundaries()[0]!).boundary, "json-parse");

  const envelope = JSON.parse(sent.input.MessageBody!) as Record<string, unknown>;
  for (const [body, field, reason] of [[undefined, "body", "missing"], ["", "body", "empty"], ["null", "envelope", "not-record"], [JSON.stringify({ ...envelope, id: "" }), "id", "empty"],
    [JSON.stringify({ ...envelope, type: 2 }), "message-type", "wrong-type"], [JSON.stringify({ ...envelope, version: "1" }), "message-version", "wrong-type"],
    [JSON.stringify({ ...envelope, enqueuedAt: "" }), "enqueued-at", "empty"], [JSON.stringify({ ...envelope, payload: [] }), "payload", "predicate-rejected"],
    [JSON.stringify({ ...envelope, traceParent: [] }), "trace-parent", "not-record"], [JSON.stringify({ ...envelope, traceParent: { traceId: "safe" } }), "span-id", "missing"]] as const) {
    clear(); const result = decodePlatformQueueMessage(body, { onDiagnostic }); equal(result.ok, false); equal(detail(records[0]!).field, field); equal(detail(records[0]!).reason, reason); equal(boundaries().length, 0);
  }
  clear(); decodePlatformQueueMessage(JSON.stringify({ ...envelope, type: "BAD", version: 0, enqueuedAt: "BAD" }), { onDiagnostic });
  equal(records.length, 4); equal(detail(records[0]!).operation, "decode"); deepEqual(records.slice(1).map((record) => record.code), ["core.queue.validation-rejected", "core.queue.validation-rejected", "core.shared.date-invalid"]);
  clear(); decodePlatformQueueMessage("bad json", { onDiagnostic }); equal(detail(records[0]!).boundary, "json-parse"); equal(records.length, 1);

  const originalParse = JSON.parse;
  try {
    clear(); let requiredReads = 0;
    JSON.parse = () => ({ ...envelope, get id(): never { requiredReads++; throw source; } });
    const getterResult = decodePlatformQueueMessage("fixture", { onDiagnostic }); equal(getterResult.ok, false); equal(requiredReads, 1); equal(records.length, 10); equal(detail(records[0]!).boundary, "envelope");
    clear(); let optionalReads = 0; let messagesReads = 0; let attributeReads = 0;
    JSON.parse = () => ({ ...envelope, get tenantId() { optionalReads++; return "tenant"; } });
    equal(decodePlatformQueueMessage("fixture", { onDiagnostic }).ok, true); equal(optionalReads, 2); equal(records.length, 0);
    const response = { get Messages() { messagesReads++; return [{ ReceiptHandle: "safe", Body: "fixture", get Attributes() { attributeReads++; return { ApproximateReceiveCount: "2" }; } }]; } };
    equal((await createPlatformSqsWorkerQueue({ ...baseWorker, onDiagnostic, client: { send: async () => response } }).receive()).kind, "delivery"); equal(messagesReads, 2); equal(attributeReads, 2);
    clear(); JSON.parse = () => ({ ...envelope, payload: { get nested(): never { throw source; } } });
    equal(decodePlatformQueueMessage("fixture", { onDiagnostic }).ok, false); equal(detail(records[0]!).boundary, "envelope"); equal(records.length, 10);
    clear(); JSON.parse = () => ({ ...envelope, payload: { score: NaN } });
    equal(decodePlatformQueueMessage("fixture", { onDiagnostic }).ok, false); equal(detail(records[0]!).boundary, "payload-copy"); equal(records[1]!.code, "core.shared.json-invalid");
    clear(); JSON.parse = () => ({ ...envelope, get traceParent(): never { throw source; } });
    equal(decodePlatformQueueMessage("fixture", { onDiagnostic }).ok, false); equal(detail(records[0]!).boundary, "trace-parent"); equal(records.length, 10);
    clear(); JSON.parse = () => ({ ...envelope, traceParent: { traceId: "bad", spanId: "bad" } });
    equal(decodePlatformQueueMessage("fixture", { onDiagnostic }).ok, true); equal(records.length, 0, "Legacy trace identifiers require nonempty text, not a new formatting policy.");
    clear(); const old = Object.assign(new TypeError("Old guard"), { diagnosticRecord: coreQueueValidationDiagnosticRecord({ operation: "decode", field: "id", reason: "empty", effect: "rejected" }) });
    JSON.parse = () => ({ ...envelope, get id(): never { throw old; } });
    equal(decodePlatformQueueMessage("fixture", { onDiagnostic }).ok, false); equal(records.length, 2); equal(records[0]!.code, "core.queue.boundary-failed"); equal(detail(records[0]!).boundary, "envelope");
  } finally { JSON.parse = originalParse; }
  clear(); await rejects(createPlatformSqsWorkerQueue({ ...baseWorker, onDiagnostic, client: { send: async () => ({ Messages: [{ ReceiptHandle: "safe", Attributes: { ApproximateReceiveCount: "1" }, get Body(): never { throw source; } }] }) } }).receive());
  equal(records.length, 10); equal(detail(records[0]!).boundary, "response");
  clear(); const reductions = receiveReductions({ onDiagnostic });
  for (const field of ["response", "messages", "message", "attributes", "receipt-handle", "body", "receive-count"] as const) for (const reason of ["absent", "empty", "wrong-type"] as const) reductions.add(field, reason, "field-unavailable");
  reductions.flush(); equal((detail(records[0]!).issues as unknown[]).length, 16); equal(detail(records[0]!).truncated, true);

  for (const sink of [() => { throw source; }, async () => { throw source; }, () => Object.defineProperty(Promise.reject(source), "then", { value: () => { throw source; } })]) {
    equal((await createPlatformSqsQueue({ queueUrl, client: { send: async () => { throw source; } }, onDiagnostic: sink }).send(durableMessage)).ok, false);
  }
  clear(); let regionReads = 0;
  throws(() => createAwsSdkPlatformSqsQueue({ queueUrl, get region() { if (++regionReads === 2) throw source; return "fixture"; }, onDiagnostic }), (error) => error === source);
  equal(regionReads, 2); equal(records.length, 10); contexts.forEach((context) => deepEqual(context, { operation: "client-initialization", boundary: "construction" }));
  clear(); throws(() => createAwsSdkPlatformSqsWorkerQueue({ ...baseWorker, get region(): never { throw source; }, onDiagnostic }), (error) => error === source);
  equal(records.length, 10); equal(detail(records[0]!).boundary, "selection");
  clear(); throws(() => createAwsSdkPlatformSqsWorkerQueueFromEnv(Object.defineProperty({}, "PLATFORM_WORKER_SQS_QUEUE_URL", { get() { throw source; } }), { onDiagnostic }), (error) => error === source);
  equal(records.length, 10); equal(detail(records[0]!).operation, "client-initialization");
  equal(coreQueueBoundaryDiagnosticRecord({ operation: "receive", boundary: "response", reason: "threw", effect: "unknown" }).code, "core.queue.boundary-failed");

  // Pinned modeled exceptions are observed only for their documented commands.
  const allOperations = ["send", "receive", "acknowledge", "release"] as const;
  const modeled = [
    ["QueueDoesNotExist", "queue-absent-reported", allOperations],
    ["RequestThrottled", "request-throttled", allOperations],
    ["InvalidAddress", "address-rejected", allOperations],
    ["InvalidSecurity", "request-security-rejected", allOperations],
    ["UnsupportedOperation", "operation-unsupported", allOperations],
    ["ReceiptHandleIsInvalid", "receipt-rejected", ["acknowledge", "release"]],
    ["InvalidIdFormat", "receipt-rejected", ["acknowledge"]],
    ["MessageNotInflight", "message-not-in-flight", ["release"]],
    ["InvalidMessageContents", "message-content-rejected", ["send"]],
    ["OverLimit", "limit-reported", ["receive"]],
    ["KmsAccessDenied", "key-access-rejected", ["send", "receive"]],
    ["KmsThrottled", "key-throttled", ["send", "receive"]],
    ["KmsDisabled", "key-rejected", ["send", "receive"]],
    ["KmsInvalidKeyUsage", "key-rejected", ["send", "receive"]],
    ["KmsInvalidState", "key-rejected", ["send", "receive"]],
    ["KmsNotFound", "key-rejected", ["send", "receive"]],
    ["KmsOptInRequired", "key-rejected", ["send", "receive"]],
  ] as const;
  for (const [name, condition, applicable] of modeled) for (const operation of allOperations) {
    clear(); let calls = 0;
    const Constructor = sqsSdk[name];
    const cause = Object.freeze(Object.assign(new Constructor({ $metadata: {}, message: "PRIVATE_NATIVE_CANARY" }), { diagnosticRecord: sourceRecords[0], relatedDiagnosticRecords: sourceRecords.slice(1) }));
    const initialDescriptors = Object.getOwnPropertyDescriptors(cause);
    const client: PlatformSqsCommandClient = { send: async () => { calls++; throw cause; } };
    const worker = createPlatformSqsWorkerQueue({ ...baseWorker, client, onDiagnostic });
    if (operation === "send") {
      const failed = await createPlatformSqsQueue({ queueUrl, client, onDiagnostic }).send(durableMessage);
      equal(failed.ok, false); if (!failed.ok) { deepEqual(failed.error.diagnosticRecord, sourceRecords[0]); deepEqual(failed.error.relatedDiagnosticRecords, sourceRecords.slice(1)); }
    } else await rejects(operation === "receive" ? worker.receive() : worker[operation]("PRIVATE_RECEIPT"));
    equal(calls, 1); equal(records.length, 10); deepEqual(records.slice(1), sourceRecords);
    const recognized = (applicable as readonly string[]).includes(operation);
    deepEqual(detail(records[0]!), { operation, boundary: "invocation", reason: "rejected", effect: "unknown",
      native: { codeAvailability: recognized ? "recognized" : "unrecognized", condition: recognized ? condition : "unknown" } });
    contexts.forEach((context) => { equal(context, contexts[0]); deepEqual(context, { operation, boundary: "invocation" }); });
    deepEqual(Object.getOwnPropertyDescriptors(cause), initialDescriptors);
    equal(JSON.stringify(records).includes("PRIVATE_NATIVE_CANARY"), false); equal(JSON.stringify(records).includes("PRIVATE_RECEIPT"), false);
    clear();
    await rejects(sqsObservation({ onDiagnostic }, operation).send({ client: { send() { throw cause; } } }, () => ({})), (error) => error === cause);
    equal(detail(records[0]!).reason, "threw"); equal(detail(records[0]!).effect, "unknown");
  }
  let nativeAccessorReads = 0;
  const accessorName = Object.defineProperty({}, "name", { get() { nativeAccessorReads++; return "RequestThrottled"; } });
  let arbitraryReads = 0;
  const proxyFailure = new Proxy({}, { get(target, key, receiver) { if (["name", "message", "code", "$metadata", "cause"].includes(String(key))) { arbitraryReads++; throw source; } return Reflect.get(target, key, receiver); }, getOwnPropertyDescriptor(target, key) { if (key === "name") throw source; return Reflect.getOwnPropertyDescriptor(target, key); } });
  const privateUnknown = Object.defineProperties({ name: "PRIVATE_UNRECOGNIZED_CANARY" }, { code: { get() { arbitraryReads++; throw source; } }, $metadata: { get() { arbitraryReads++; throw source; } }, cause: { get() { arbitraryReads++; throw source; } } });
  for (const [cause, availability] of [[null, "absent"], [0, "absent"], [{}, "absent"], [Object.create({ name: "RequestThrottled" }), "absent"], [{ name: undefined }, "wrong-type"], [{ name: 3 }, "wrong-type"], [accessorName, "unavailable"], [proxyFailure, "unavailable"], [privateUnknown, "unrecognized"],
    [{ name: "AccessDeniedException" }, "unrecognized"], [{ name: "InvalidParameterValue" }, "unrecognized"], [{ name: "TimeoutError", code: "ETIMEDOUT" }, "unrecognized"], [{ name: "ResourceNotFoundException" }, "unrecognized"]] as const) {
    clear(); await rejects(sqsObservation({ onDiagnostic }, "send").send({ client: { send: async () => { throw cause; } } }, () => ({})));
    equal(records.length, 1); deepEqual(detail(records[0]!).native, { codeAvailability: availability, condition: "unknown" });
    equal(JSON.stringify(records).includes("PRIVATE_UNRECOGNIZED_CANARY"), false);
  }
  equal(nativeAccessorReads, 0); equal(arbitraryReads, 0);
  clear();
  await rejects(sqsObservation({ onDiagnostic }, "send").send({ client: Object.defineProperty({}, "send", { get() { throw accessorName; } }) as PlatformSqsCommandClient }, () => ({})), (error) => error === accessorName);
  equal(detail(records[0]!).boundary, "selection"); equal(Object.hasOwn(detail(records[0]!), "native"), false); equal(nativeAccessorReads, 0);

  console.log("AWS SQS queue adapter runtime test passed.");
}

function platformQueueMessage() {
  return queueMessage({
    id: queueMessageId("outbox-1"),
    type: accepted<QueueMessageType>(queueMessageType("platform-smoke.rebuild")),
    enqueuedAt: accepted(isoDateTime("2026-09-23T12:00:00.000Z")),
    correlationId: correlationId("correlation-1"),
    causationId: causationId("request-1"),
    idempotencyKey: queueIdempotencyKey("outbox-1"),
    payload: { outboxEntryId: "outbox-1" },
  });
}

function accepted<TValue>(
  result: { readonly ok: true; readonly value: TValue } | { readonly ok: false },
): TValue {
  if (!result.ok) throw new Error("Expected a valid Core value.");
  return result.value;
}

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
