import { deepEqual, equal } from "node:assert/strict";
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
} from "@kanbien/core";
import {
  createAwsSdkPlatformSqsWorkerQueueFromEnv,
  createPlatformSqsQueue,
  createPlatformSqsWorkerQueue,
  type PlatformSqsCommandClient,
} from "../src/index";

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
