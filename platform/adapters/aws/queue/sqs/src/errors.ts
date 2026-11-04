export interface PlatformSqsConfigurationIssue {
  readonly setting: "queue-address" | "region" | "receive-wait" | "visibility-timeout";
  readonly reason: "missing" | "empty" | "blank" | "wrong-type" | "not-finite" | "invalid-integer" | "out-of-range";
}

/** Both queue constructors historically check only length, without trimming or
 * a type policy. Preserve that guard and its original native access exception. */
export function assertSqsConfigurationText(name: string, value: string, setting: "queue-address" | "region"): void {
  let empty: boolean;
  try { empty = value.length === 0; }
  catch (error) {
    // An arbitrary getter failure establishes no value/configuration cause.
    if ((value === undefined || value === null) && typeof error === "object" && error !== null) {
      Object.assign(error, { configurationIssue: { setting, reason: value === undefined ? "missing" : "wrong-type" } });
    }
    throw error;
  }
  if (empty) throw Object.assign(new RangeError(`${name} must not be empty.`), { configurationIssue: { setting, reason: "empty" } });
}

export interface PlatformSqsWorkerQueueError {
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
  readonly configurationIssue?: PlatformSqsConfigurationIssue;
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
  configurationIssue?: PlatformSqsConfigurationIssue,
): { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  return { ok: false, error: { code: "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID", defaultMessage: "AWS SQS worker queue configuration is invalid.", details: { path, reason }, ...(configurationIssue === undefined ? {} : { configurationIssue }) } };
}

export function invalidMessage(
  path: string,
  reason: string,
  evidence: Pick<PlatformSqsWorkerQueueError, "diagnosticRecord" | "relatedDiagnosticRecords"> = {},
): { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  return { ok: false, error: { code: "PLATFORM_ADAPTER_AWS_SQS_MESSAGE_INVALID", defaultMessage: "SQS delivery is not a valid platform queue message.", details: { path, reason }, ...evidence } };
}

export function operationError(operation: string, evidence: Pick<PlatformSqsWorkerQueueError, "diagnosticRecord" | "relatedDiagnosticRecords"> = {}): PlatformSqsWorkerQueueError {
  return { code: "PLATFORM_ADAPTER_AWS_SQS_OPERATION_FAILED", defaultMessage: `AWS SQS ${operation} operation failed.`, ...evidence };
}
import type { DiagnosticRecord } from "@kanbien/core";
