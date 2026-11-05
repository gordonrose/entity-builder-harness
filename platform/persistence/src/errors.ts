import {
  messageKey,
  type CoreError,
  type MessageKey,
  type MessageParams,
} from "@kanbien/core/shared";
import { parseRelatedDiagnosticRecords, type DiagnosticDefinition } from "@kanbien/core/diagnostics";

export const platformPersistenceErrorClasses = [
  "PLATFORM_PERSISTENCE_DUPLICATE_OUTBOX_ENTRY", "PLATFORM_PERSISTENCE_DUPLICATE_RECORD_CHANGE",
  "PLATFORM_PERSISTENCE_INVALID_LEASE", "PLATFORM_PERSISTENCE_INVALID_LIMIT", "PLATFORM_PERSISTENCE_INVALID_MUTATION",
  "PLATFORM_PERSISTENCE_LEASE_EXPIRED", "PLATFORM_PERSISTENCE_MIGRATION_CHECKSUM_MISMATCH",
  "PLATFORM_PERSISTENCE_OUTBOX_NOT_FOUND", "PLATFORM_PERSISTENCE_OUTBOX_NOT_LEASED", "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED",
  "PLATFORM_PERSISTENCE_QUEUE_MAPPING_INVALID", "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", "PLATFORM_PERSISTENCE_STALE_FENCE",
] as const;
export type PlatformPersistenceErrorCode = typeof platformPersistenceErrorClasses[number];

export interface PlatformPersistenceError extends CoreError {
  readonly code: PlatformPersistenceErrorCode;
}

export function platformPersistenceError(input: {
  readonly diagnostic?: CoreError["diagnostic"];
  readonly diagnosticRecord?: CoreError["diagnosticRecord"];
  readonly relatedDiagnosticRecords?: CoreError["relatedDiagnosticRecords"];
  /** Selected by the producing adapter; definitions are not retained on errors. */
  readonly relatedDiagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly code: PlatformPersistenceErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly details?: Readonly<Record<string, unknown>>;
}): PlatformPersistenceError {
  const related = input.relatedDiagnosticRecords === undefined ? undefined
    : parseRelatedDiagnosticRecords(input.relatedDiagnosticDefinitions ?? [], input.relatedDiagnosticRecords);
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.diagnostic === undefined ? {} : { diagnostic: input.diagnostic }),
    ...(input.diagnosticRecord === undefined ? {} : { diagnosticRecord: input.diagnosticRecord }),
    ...(related?.ok ? { relatedDiagnosticRecords: related.value } : {}),
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
    ...(input.details === undefined ? {} : { details: input.details }),
  };
}
