import { deepEqual, equal } from "node:assert/strict";
import {
  ChangeMessageVisibilityCommand,
  DeleteMessageCommand,
  ReceiveMessageCommand,
} from "@aws-sdk/client-sqs";
import {
  createPlatformSqsWorkerQueue,
  createAwsSdkPlatformSqsWorkerQueueFromEnv,
  type PlatformSqsCommandClient,
} from "../src/index";

async function main(): Promise<void> {
  const commands: unknown[] = [];
  const client: PlatformSqsCommandClient = {
    send: async (command) => {
      commands.push(command);
      if (command instanceof ReceiveMessageCommand) {
        return {
          Messages: [{
            MessageId: "delivery-1",
            ReceiptHandle: "receipt-1",
            Attributes: { ApproximateReceiveCount: "2" },
            Body: JSON.stringify({
              type: "platform-smoke.rebuild",
              version: 1,
              enqueuedAt: "2026-09-23T12:00:00.000Z",
              correlationId: "correlation-1",
              idempotencyKey: "smoke-rebuild-1",
              payload: { rebuild: true },
            }),
          }],
        };
      }
      return {};
    },
  };
  const queue = createPlatformSqsWorkerQueue({
    queueUrl: "https://sqs.eu-west-1.amazonaws.com/123456789012/worker",
    waitTimeSeconds: 20,
    visibilityTimeoutSeconds: 30,
    client,
  });

  const delivery = await queue.receive();
  equal(delivery.kind, "delivery");
  if (delivery.kind !== "delivery") throw new Error("Expected SQS delivery.");
  equal(delivery.receiveCount, 2);
  deepEqual(delivery.message, {
    id: "delivery-1",
    type: "platform-smoke.rebuild",
    version: 1,
    enqueuedAt: "2026-09-23T12:00:00.000Z",
    correlationId: "correlation-1",
    idempotencyKey: "smoke-rebuild-1",
    payload: { rebuild: true },
  });
  const receive = commands[0];
  equal(receive instanceof ReceiveMessageCommand, true);
  if (!(receive instanceof ReceiveMessageCommand)) throw new Error("Expected receive command.");
  deepEqual(receive.input, {
    QueueUrl: "https://sqs.eu-west-1.amazonaws.com/123456789012/worker",
    MaxNumberOfMessages: 1,
    WaitTimeSeconds: 20,
    VisibilityTimeout: 30,
    MessageSystemAttributeNames: ["ApproximateReceiveCount"],
  });

  await queue.acknowledge(delivery.receiptHandle);
  await queue.release(delivery.receiptHandle);
  const acknowledge = commands[1];
  const release = commands[2];
  equal(acknowledge instanceof DeleteMessageCommand, true);
  equal(release instanceof ChangeMessageVisibilityCommand, true);
  if (!(acknowledge instanceof DeleteMessageCommand) || !(release instanceof ChangeMessageVisibilityCommand)) {
    throw new Error("Expected acknowledgement and release commands.");
  }
  deepEqual(acknowledge.input, {
    QueueUrl: "https://sqs.eu-west-1.amazonaws.com/123456789012/worker",
    ReceiptHandle: "receipt-1",
  });
  deepEqual(release.input, {
    QueueUrl: "https://sqs.eu-west-1.amazonaws.com/123456789012/worker",
    ReceiptHandle: "receipt-1",
    VisibilityTimeout: 0,
  });

  const empty = createPlatformSqsWorkerQueue({
    queueUrl: "https://sqs.eu-west-1.amazonaws.com/123456789012/worker",
    waitTimeSeconds: 1,
    visibilityTimeoutSeconds: 30,
    client: { send: async () => ({ Messages: [] }) },
  });
  deepEqual(await empty.receive(), { kind: "empty" });

  const invalid = createPlatformSqsWorkerQueue({
    queueUrl: "https://sqs.eu-west-1.amazonaws.com/123456789012/worker",
    waitTimeSeconds: 1,
    visibilityTimeoutSeconds: 30,
    client: {
      send: async () => ({
        Messages: [{
          MessageId: "delivery-invalid",
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

  const missingConfig = createAwsSdkPlatformSqsWorkerQueueFromEnv({});
  equal(missingConfig.ok, false);
  if (!missingConfig.ok) {
    equal(missingConfig.error.code, "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID");
    equal(missingConfig.error.details?.path, "PLATFORM_WORKER_SQS_QUEUE_URL");
  }

  console.log("AWS SQS worker adapter runtime test passed.");
}

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
