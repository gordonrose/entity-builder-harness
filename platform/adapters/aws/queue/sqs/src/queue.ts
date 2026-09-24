import { SendMessageCommand, SQSClient } from "@aws-sdk/client-sqs";
import {
  err,
  ok,
  queueError,
  type Queue,
  type QueueDelaySeconds,
  type QueueError,
  type QueueMessage,
  type QueuePayload,
  type QueueSendOptions,
} from "@kanbien/core";
import { encodePlatformQueueMessage } from "./messages";
import type { PlatformSqsCommandClient } from "./worker";

export interface PlatformSqsQueueOptions {
  readonly queueUrl: string;
  readonly client: PlatformSqsCommandClient;
}

export interface AwsSdkPlatformSqsQueueOptions {
  readonly queueUrl: string;
  readonly region: string;
}

/**
 * Adapt Core's minimal producer port to SQS Standard. This target does not
 * select FIFO ordering, so grouped messages fail locally instead of relying on
 * an accidental provider-side queue mismatch.
 */
export function createPlatformSqsQueue<TPayload extends QueuePayload = QueuePayload>(
  options: PlatformSqsQueueOptions,
): Queue<TPayload> {
  assertNonEmpty("queueUrl", options.queueUrl);
  return {
    async send(message: QueueMessage<TPayload>, sendOptions?: QueueSendOptions) {
      if (message.messageGroupKey !== undefined) {
        return err(queueError({
          code: "QUEUE_SEND_FAILED",
          defaultMessage: "The selected SQS Standard queue does not support message groups.",
          messageKey: "queues.sqs.standard.message_group.unsupported",
        }));
      }
      const delay = validDelay(sendOptions?.delaySeconds);
      if (!delay.ok) return delay;
      try {
        await options.client.send(new SendMessageCommand({
          QueueUrl: options.queueUrl,
          MessageBody: encodePlatformQueueMessage(message),
          ...(delay.value === undefined ? {} : { DelaySeconds: Number(delay.value) }),
        }));
        return ok(undefined);
      } catch {
        return err(queueError({
          code: "QUEUE_SEND_FAILED",
          defaultMessage: "AWS SQS did not accept the queue message.",
          messageKey: "queues.sqs.send.failed",
        }));
      }
    },
  };
}

export function createAwsSdkPlatformSqsQueue<TPayload extends QueuePayload = QueuePayload>(
  options: AwsSdkPlatformSqsQueueOptions,
): Queue<TPayload> {
  assertNonEmpty("region", options.region);
  return createPlatformSqsQueue<TPayload>({
    queueUrl: options.queueUrl,
    client: new SQSClient({ region: options.region }) as unknown as PlatformSqsCommandClient,
  });
}

function validDelay(
  delay: QueueDelaySeconds | undefined,
): { readonly ok: true; readonly value: QueueDelaySeconds | undefined } | { readonly ok: false; readonly error: QueueError } {
  if (delay === undefined) return { ok: true, value: undefined };
  if (Number.isInteger(delay) && Number(delay) >= 0 && Number(delay) <= 900) return { ok: true, value: delay };
  return err(queueError({
    code: "QUEUE_INVALID_DELAY",
    defaultMessage: "SQS Standard delay must be an integer from 0 to 900 seconds.",
    messageKey: "queues.sqs.delay.invalid",
  }));
}

function assertNonEmpty(name: string, value: string): void {
  if (value.length === 0) throw new RangeError(`${name} must not be empty.`);
}
