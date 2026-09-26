import {
  messageKey,
  type CoreError,
  type MessageKey,
  type MessageParams,
} from "@kanbien/core/shared";

export type PlatformPersistenceErrorCode =
  | "PLATFORM_PERSISTENCE_DUPLICATE_OUTBOX_ENTRY"
  | "PLATFORM_PERSISTENCE_DUPLICATE_RECORD_CHANGE"
  | "PLATFORM_PERSISTENCE_INVALID_LEASE"
  | "PLATFORM_PERSISTENCE_INVALID_LIMIT"
  | "PLATFORM_PERSISTENCE_INVALID_MUTATION"
  | "PLATFORM_PERSISTENCE_LEASE_EXPIRED"
  | "PLATFORM_PERSISTENCE_MIGRATION_CHECKSUM_MISMATCH"
  | "PLATFORM_PERSISTENCE_OUTBOX_NOT_FOUND"
  | "PLATFORM_PERSISTENCE_OUTBOX_NOT_LEASED"
  | "PLATFORM_PERSISTENCE_PROCESSING_NOT_CLAIMED"
  | "PLATFORM_PERSISTENCE_QUEUE_MAPPING_INVALID"
  | "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED"
  | "PLATFORM_PERSISTENCE_STALE_FENCE";

export interface PlatformPersistenceError extends CoreError {
  readonly code: PlatformPersistenceErrorCode;
}

export function platformPersistenceError(input: {
  readonly code: PlatformPersistenceErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly details?: Readonly<Record<string, unknown>>;
}): PlatformPersistenceError {
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
    ...(input.details === undefined ? {} : { details: input.details }),
  };
}
