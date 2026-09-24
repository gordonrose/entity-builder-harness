export interface PlatformSqsWorkerQueueError {
  readonly code:
    | "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID"
    | "PLATFORM_ADAPTER_AWS_SQS_MESSAGE_INVALID"
    | "PLATFORM_ADAPTER_AWS_SQS_OPERATION_FAILED";
  readonly defaultMessage: string;
  readonly details?: Readonly<{ readonly path: string; readonly reason: string }>;
}

export function invalidConfig(
  path: string,
  reason: string,
): { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  return { ok: false, error: { code: "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID", defaultMessage: "AWS SQS worker queue configuration is invalid.", details: { path, reason } } };
}

export function invalidMessage(
  path: string,
  reason: string,
): { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  return { ok: false, error: { code: "PLATFORM_ADAPTER_AWS_SQS_MESSAGE_INVALID", defaultMessage: "SQS delivery is not a valid platform queue message.", details: { path, reason } } };
}

export function operationError(operation: string): PlatformSqsWorkerQueueError {
  return { code: "PLATFORM_ADAPTER_AWS_SQS_OPERATION_FAILED", defaultMessage: `AWS SQS ${operation} operation failed.` };
}
