import type { JsonValue, Result } from "@kanbien/core/shared";
import type { DiagnosticDefinition, DiagnosticRecord } from "@kanbien/core/diagnostics";
import { workerDiagnosticEvidence, workerDiagnosticRecord } from "./diagnostics";

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
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
}

export function workerFailure(
  code: PlatformWorkerErrorCode,
  defaultMessage: string,
  details?: Readonly<Record<string, JsonValue>>,
  cause?: unknown,
  diagnosticDefinitions: readonly DiagnosticDefinition[] = [],
  fallbackDiagnosticRecord?: DiagnosticRecord,
): Result<never, PlatformWorkerError> {
  return {
    ok: false,
    error: workerError(code, defaultMessage, details, cause, diagnosticDefinitions, fallbackDiagnosticRecord),
  };
}

export function workerError(
  code: PlatformWorkerErrorCode,
  defaultMessage: string,
  details?: Readonly<Record<string, JsonValue>>,
  cause?: unknown,
  diagnosticDefinitions: readonly DiagnosticDefinition[] = [],
  fallbackDiagnosticRecord?: DiagnosticRecord,
): PlatformWorkerError {
  const evidence = workerDiagnosticEvidence(cause, diagnosticDefinitions);
  return {
    code,
    defaultMessage,
    diagnosticRecord: evidence.diagnosticRecord ?? fallbackDiagnosticRecord ?? workerDiagnosticRecord(code,
      details?.["phase"] === "configuration" || details?.["phase"] === "claim" || details?.["phase"] === "complete" || details?.["phase"] === "release" ? details["phase"] : undefined),
    ...(evidence.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: evidence.relatedDiagnosticRecords }),
    ...(details === undefined ? {} : { details }),
    ...(cause === undefined ? {} : { cause }),
  };
}
