import type { JsonValue, Result } from "@kanbien/core/shared";

export type PlatformWorkerErrorCode =
  | "PLATFORM_WORKER_MOUNT_FAILED"
  | "PLATFORM_WORKER_CONFIG_INVALID"
  | "PLATFORM_WORKER_QUEUE_CLOSED"
  | "PLATFORM_WORKER_NOT_READY"
  | "PLATFORM_WORKER_JOB_NOT_FOUND"
  | "PLATFORM_WORKER_INVALID_PAYLOAD"
  | "PLATFORM_WORKER_DURABLE_OUTBOX_ENVELOPE_INVALID"
  | "PLATFORM_WORKER_DURABLE_PROCESSING_BUSY"
  | "PLATFORM_WORKER_DURABLE_PROCESSING_TERMINAL_FAILURE"
  | "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED"
  | "PLATFORM_WORKER_HANDLER_FAILED"
  | "PLATFORM_WORKER_IDEMPOTENCY_FAILED";

export interface PlatformWorkerError {
  readonly code: PlatformWorkerErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
  readonly cause?: unknown;
}

export function workerFailure(
  code: PlatformWorkerErrorCode,
  defaultMessage: string,
  details?: Readonly<Record<string, JsonValue>>,
  cause?: unknown,
): Result<never, PlatformWorkerError> {
  return {
    ok: false,
    error: workerError(code, defaultMessage, details, cause),
  };
}

export function workerError(
  code: PlatformWorkerErrorCode,
  defaultMessage: string,
  details?: Readonly<Record<string, JsonValue>>,
  cause?: unknown,
): PlatformWorkerError {
  return {
    code,
    defaultMessage,
    ...(details === undefined ? {} : { details }),
    ...(cause === undefined ? {} : { cause }),
  };
}
