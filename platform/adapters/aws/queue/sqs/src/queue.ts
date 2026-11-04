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
  type CoreQueueDiagnosticOptions,
} from "@kanbien/core";
import { encodePlatformQueueMessage } from "./messages";
import { assertSqsConfigurationText } from "./errors";
import type { PlatformSqsCommandClient } from "./worker";
import { sqsObservation, type SqsObservation } from "./observations";
import type { ConfigSource, Result } from "@kanbien/core";
import { validateSqsSenderConfiguration, type SqsConfigurationCheck, type SqsConfigurationFailure } from "./configuration/index";

export function createAwsSdkPlatformSqsQueueFromConfiguration<TPayload extends QueuePayload = QueuePayload>(
  source: ConfigSource, diagnostics?: CoreQueueDiagnosticOptions, check?: SqsConfigurationCheck,
): Result<Queue<TPayload>, SqsConfigurationFailure> {
  const configuration = validateSqsSenderConfiguration(source, check, diagnostics);
  return configuration.ok ? { ok: true, value: createAwsSdkPlatformSqsQueue<TPayload>({ ...configuration.value,
    onDiagnostic(record, context) { return diagnostics?.onDiagnostic?.(record, context); },
    get diagnosticDefinitions() { return diagnostics?.diagnosticDefinitions ?? []; },
  }) } : configuration;
}

export interface PlatformSqsQueueOptions extends CoreQueueDiagnosticOptions {
  readonly queueUrl: string;
  readonly client: PlatformSqsCommandClient;
}

export interface AwsSdkPlatformSqsQueueOptions extends CoreQueueDiagnosticOptions {
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
  sqsObservation(options, "client-initialization").at("selection", () => assertSqsConfigurationText("queueUrl", options.queueUrl, "queue-address"));
  return {
    async send(message: QueueMessage<TPayload>, sendOptions?: QueueSendOptions) {
      const observed = sqsObservation(options, "send");
      if (observed.at("selection", () => message.messageGroupKey !== undefined)) {
        return err(queueError({
          code: "QUEUE_SEND_FAILED",
          defaultMessage: "The selected SQS Standard queue does not support message groups.",
          messageKey: "queues.sqs.standard.message_group.unsupported",
          ...observed.reject("message-group-key", "unsupported"),
        }));
      }
      const delay = observed.at("selection", () => validDelay(sendOptions?.delaySeconds, observed));
      if (!delay.ok) return delay;
      try {
        await observed.send(options, () => new SendMessageCommand({
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
          ...observed.evidence(),
        }));
      }
    },
  };
}

export function createAwsSdkPlatformSqsQueue<TPayload extends QueuePayload = QueuePayload>(
  options: AwsSdkPlatformSqsQueueOptions,
): Queue<TPayload> {
  const observed = sqsObservation(options, "client-initialization");
  observed.at("selection", () => assertSqsConfigurationText("region", options.region, "region"));
  return createPlatformSqsQueue<TPayload>({
    queueUrl: observed.at("selection", () => options.queueUrl),
    client: observed.at("construction", () => new SQSClient({ region: options.region })) as unknown as PlatformSqsCommandClient,
    onDiagnostic(record, context) { return options.onDiagnostic?.(record, context); },
    get diagnosticDefinitions() { return options.diagnosticDefinitions ?? []; },
  });
}

function validDelay(
  delay: QueueDelaySeconds | undefined,
  observed: SqsObservation,
): { readonly ok: true; readonly value: QueueDelaySeconds | undefined } | { readonly ok: false; readonly error: QueueError } {
  if (delay === undefined) return { ok: true, value: undefined };
  let reason: "not-integer" | "negative" | "above-maximum" = "not-integer";
  if (Number.isInteger(delay) && (reason = "negative", Number(delay) >= 0) && (reason = "above-maximum", Number(delay) <= 900)) return { ok: true, value: delay };
  return err(queueError({
    code: "QUEUE_INVALID_DELAY",
    defaultMessage: "SQS Standard delay must be an integer from 0 to 900 seconds.",
    messageKey: "queues.sqs.delay.invalid",
    ...observed.reject("delay", reason),
  }));
}
