import {
  ChangeMessageVisibilityCommand,
  DeleteMessageCommand,
  ReceiveMessageCommand,
  SQSClient,
} from "@aws-sdk/client-sqs";
import type { QueueMessage, CoreQueueDiagnosticOptions } from "@kanbien/core";
import { assertSqsConfigurationText, invalidConfig, invalidMessage, operationError, type PlatformSqsConfigurationIssue, type PlatformSqsWorkerQueueError } from "./errors";
import { decodePlatformQueueMessage } from "./messages";
import { sqsObservation, receiveReductions, type SqsObservation, type ReceiveReductions } from "./observations";
import type { ConfigSource, Result } from "@kanbien/core";
import { validateSqsWorkerConfiguration, sqsReceiveWaitConstraint, sqsVisibilityTimeoutConstraint,
  type SqsConfigurationCheck, type SqsConfigurationFailure } from "./configuration/index";

export function createAwsSdkPlatformSqsWorkerQueueFromConfiguration(
  source: ConfigSource, diagnostics?: CoreQueueDiagnosticOptions, check?: SqsConfigurationCheck,
): Result<PlatformSqsWorkerQueue, SqsConfigurationFailure> {
  const configuration = validateSqsWorkerConfiguration(source, check, diagnostics);
  return configuration.ok ? { ok: true, value: createAwsSdkPlatformSqsWorkerQueue({ ...configuration.value,
    onDiagnostic(record, context) { return diagnostics?.onDiagnostic?.(record, context); },
    get diagnosticDefinitions() { return diagnostics?.diagnosticDefinitions ?? []; },
  }) } : configuration;
}

export interface PlatformSqsWorkerQueue {
  receive(): Promise<PlatformSqsReceiveResult>;
  acknowledge(receiptHandle: string): Promise<void>;
  release(receiptHandle: string): Promise<void>;
}

export type PlatformSqsReceiveResult =
  | { readonly kind: "empty" }
  | {
      readonly kind: "delivery";
      readonly receiptHandle: string;
      readonly receiveCount: number;
      readonly message: QueueMessage;
    }
  | {
      readonly kind: "invalid";
      readonly receiptHandle: string;
      readonly receiveCount: number;
      readonly error: PlatformSqsWorkerQueueError;
    };

export type { PlatformSqsWorkerQueueError } from "./errors";

export interface PlatformSqsCommandClient {
  send(command: unknown): Promise<unknown>;
}

export interface PlatformSqsWorkerQueueOptions extends CoreQueueDiagnosticOptions {
  readonly queueUrl: string;
  readonly waitTimeSeconds: number;
  readonly visibilityTimeoutSeconds: number;
  readonly client: PlatformSqsCommandClient;
}

export interface AwsSdkPlatformSqsWorkerQueueOptions extends CoreQueueDiagnosticOptions {
  readonly queueUrl: string;
  readonly region: string;
  readonly waitTimeSeconds: number;
  readonly visibilityTimeoutSeconds: number;
}

export function createPlatformSqsWorkerQueue(
  options: PlatformSqsWorkerQueueOptions,
): PlatformSqsWorkerQueue {
  sqsObservation(options, "client-initialization").at("selection", () => {
    assertSqsConfigurationText("queueUrl", options.queueUrl, "queue-address");
    assertWholeNumberInRange("waitTimeSeconds", options.waitTimeSeconds, sqsReceiveWaitConstraint.minimum, sqsReceiveWaitConstraint.maximum, "receive-wait");
    assertWholeNumberInRange("visibilityTimeoutSeconds", options.visibilityTimeoutSeconds, sqsVisibilityTimeoutConstraint.minimum, sqsVisibilityTimeoutConstraint.maximum, "visibility-timeout");
  });

  return {
    receive: async () => {
      const observed = sqsObservation(options, "receive");
      const reductions = receiveReductions(options);
      try {
        const response = await observed.send(options, () => new ReceiveMessageCommand({
          QueueUrl: options.queueUrl,
          MaxNumberOfMessages: 1,
          WaitTimeSeconds: options.waitTimeSeconds,
          VisibilityTimeout: options.visibilityTimeoutSeconds,
          MessageSystemAttributeNames: ["ApproximateReceiveCount"],
        }));
        const message = observed.at("response", () => firstSqsMessage(response, reductions));
        if (message === undefined) return { kind: "empty" };
        if (message.receiptHandle === undefined) {
          observed.reject("receipt-handle", "missing");
          return invalidDelivery("ReceiptHandle", "SQS delivery did not contain a receipt handle.", "");
        }
        const receiveCount = observed.at("response", () => parseReceiveCount(message.receiveCount, reductions));
        const decoded = decodePlatformQueueMessage(message.body, options);
        if (!decoded.ok) {
          return {
            kind: "invalid",
            receiptHandle: message.receiptHandle,
            receiveCount,
            error: decoded.error,
          };
        }
        return {
          kind: "delivery",
          receiptHandle: message.receiptHandle,
          receiveCount,
          message: decoded.value,
        };
      } catch {
        throw operationError("receive", observed.evidence());
      } finally { reductions.flush(); }
    },
    acknowledge: async (receiptHandle) => {
      const observed = sqsObservation(options, "acknowledge");
      assertNonEmpty("receiptHandle", receiptHandle, observed);
      try {
        await observed.send(options, () => new DeleteMessageCommand({ QueueUrl: options.queueUrl, ReceiptHandle: receiptHandle }));
      } catch {
        throw operationError("acknowledge", observed.evidence());
      }
    },
    release: async (receiptHandle) => {
      const observed = sqsObservation(options, "release");
      assertNonEmpty("receiptHandle", receiptHandle, observed);
      try {
        await observed.send(options, () => new ChangeMessageVisibilityCommand({
          QueueUrl: options.queueUrl,
          ReceiptHandle: receiptHandle,
          VisibilityTimeout: 0,
        }));
      } catch {
        throw operationError("release", observed.evidence());
      }
    },
  };
}

export function createAwsSdkPlatformSqsWorkerQueue(
  options: AwsSdkPlatformSqsWorkerQueueOptions,
): PlatformSqsWorkerQueue {
  const observed = sqsObservation(options, "client-initialization");
  observed.at("selection", () => assertSqsConfigurationText("region", options.region, "region"));
  return createPlatformSqsWorkerQueue({
    queueUrl: observed.at("selection", () => options.queueUrl),
    waitTimeSeconds: observed.at("selection", () => options.waitTimeSeconds),
    visibilityTimeoutSeconds: observed.at("selection", () => options.visibilityTimeoutSeconds),
    client: observed.at("construction", () => new SQSClient({ region: options.region })) as unknown as PlatformSqsCommandClient,
    onDiagnostic(record, context) { return options.onDiagnostic?.(record, context); },
    get diagnosticDefinitions() { return options.diagnosticDefinitions ?? []; },
  });
}

export function createAwsSdkPlatformSqsWorkerQueueFromEnv(
  env: Readonly<Record<string, string | undefined>>,
  diagnostics?: CoreQueueDiagnosticOptions,
): { readonly ok: true; readonly value: PlatformSqsWorkerQueue } | { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  const observed = sqsObservation(diagnostics, "client-initialization");
  const queueUrl = observed.at("selection", () => requiredString(env, "PLATFORM_WORKER_SQS_QUEUE_URL", "queue-address"));
  const region = observed.at("selection", () => requiredString(env, "PLATFORM_WORKER_SQS_REGION", "region"));
  const waitTimeSeconds = observed.at("selection", () => boundedInteger(env, "PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS", sqsReceiveWaitConstraint.minimum, sqsReceiveWaitConstraint.maximum, "receive-wait"));
  const visibilityTimeoutSeconds = observed.at("selection", () => boundedInteger(env, "PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS", sqsVisibilityTimeoutConstraint.minimum, sqsVisibilityTimeoutConstraint.maximum, "visibility-timeout"));
  if (!queueUrl.ok) return queueUrl;
  if (!region.ok) return region;
  if (!waitTimeSeconds.ok) return waitTimeSeconds;
  if (!visibilityTimeoutSeconds.ok) return visibilityTimeoutSeconds;
  return {
    ok: true,
    value: createAwsSdkPlatformSqsWorkerQueue({
      queueUrl: queueUrl.value,
      region: region.value,
      waitTimeSeconds: waitTimeSeconds.value,
      visibilityTimeoutSeconds: visibilityTimeoutSeconds.value,
      onDiagnostic(record, context) { return diagnostics?.onDiagnostic?.(record, context); },
      get diagnosticDefinitions() { return diagnostics?.diagnosticDefinitions ?? []; },
    }),
  };
}

function firstSqsMessage(response: unknown, reductions: ReceiveReductions): { readonly receiptHandle: string | undefined; readonly body: string | undefined; readonly receiveCount: string | undefined } | undefined {
  if (!isRecord(response)) { reductions.add("response", "not-record", "empty-receive"); return undefined; }
  let messages: unknown;
  if (!Array.isArray(messages = response.Messages)) { if (messages !== undefined) reductions.add("messages", "not-array", "empty-receive"); return undefined; }
  const first = (response.Messages as readonly unknown[])[0];
  if (!isRecord(first)) { if (first !== undefined) reductions.add("message", "not-record", "empty-receive"); return undefined; }
  let suppliedAttributes: unknown;
  const attributes = isRecord(suppliedAttributes = first.Attributes) ? first.Attributes as Readonly<Record<string, unknown>> : (reductions.add("attributes", suppliedAttributes === undefined ? "absent" : "not-record", "empty-attributes"), {});
  return {
    receiptHandle: projectedString(first.ReceiptHandle, "receipt-handle", reductions),
    body: projectedString(first.Body, "body", reductions),
    receiveCount: projectedString(attributes.ApproximateReceiveCount, "receive-count", reductions),
  };
}

function requiredString(
  env: Readonly<Record<string, string | undefined>>,
  path: string,
  setting: "queue-address" | "region",
): { readonly ok: true; readonly value: string } | { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  const value = env[path];
  if (value === undefined || value.trim().length === 0) return invalidConfig(path, "A non-empty value is required.", { setting, reason: value === undefined ? "missing" : "blank" });
  return { ok: true, value };
}

function boundedInteger(
  env: Readonly<Record<string, string | undefined>>,
  path: string,
  min: number,
  max: number,
  setting: "receive-wait" | "visibility-timeout",
): { readonly ok: true; readonly value: number } | { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  const raw = env[path];
  const value = Number(raw);
  const integer = Number.isInteger(value);
  if (!integer || value < min || value > max) return invalidConfig(path, `Expected an integer from ${min} to ${max}.`, { setting, reason: raw === undefined ? "missing" : !integer ? "invalid-integer" : "out-of-range" });
  return { ok: true, value };
}

function parseReceiveCount(value: string | undefined, reductions: ReceiveReductions): number {
  const parsed = Number(value);
  let reason: "not-integer" | "not-positive" = "not-integer";
  if (Number.isInteger(parsed) && (reason = "not-positive", parsed > 0)) return parsed;
  reductions.add("receive-count", value === undefined ? "absent" : reason, "count-one");
  return 1;
}

function invalidDelivery(path: string, reason: string, receiptHandle: string): PlatformSqsReceiveResult {
  if (receiptHandle.length === 0) {
    throw operationError("receive");
  }
  return { kind: "invalid", receiptHandle, receiveCount: 1, error: invalidMessage(path, reason).error };
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}
function projectedString(value: unknown, field: "receipt-handle" | "body" | "receive-count", reductions: ReceiveReductions): string | undefined {
  const projected = stringValue(value);
  if (projected === undefined) reductions.add(field, value === undefined ? "absent" : "wrong-type", "field-unavailable");
  return projected;
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assertNonEmpty(name: string, value: string, observed: SqsObservation): void {
  const empty = observed.at("selection", () => value.length === 0);
  if (empty) throw Object.assign(new RangeError(`${name} must not be empty.`), observed.reject("receipt-handle", "empty"));
}

function assertWholeNumberInRange(name: string, value: number, min: number, max: number, setting: "receive-wait" | "visibility-timeout"): void {
  const integer = Number.isInteger(value);
  if (!integer || value < min || value > max) {
    const reason: PlatformSqsConfigurationIssue["reason"] = value === undefined ? "missing" : typeof value !== "number" ? "wrong-type" : value !== value || value === Infinity || value === -Infinity ? "not-finite" : !integer ? "invalid-integer" : "out-of-range";
    throw Object.assign(new RangeError(`${name} must be an integer from ${min} to ${max}.`), { configurationIssue: { setting, reason } });
  }
}
