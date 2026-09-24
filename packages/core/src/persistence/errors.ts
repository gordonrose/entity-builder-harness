import type { DiagnosticDescriptor } from "../diagnostics/index";
import {
  messageKey,
  type CoreError,
  type MessageKey,
  type MessageParams,
} from "../shared/index";

export type PersistenceErrorCode =
  | "PERSISTENCE_CONFLICT"
  | "PERSISTENCE_DUPLICATE"
  | "PERSISTENCE_INVALID_LINEAGE"
  | "PERSISTENCE_INVALID_OUTBOX_DELIVERY_POLICY"
  | "PERSISTENCE_INVALID_OUTBOX_MESSAGE_TYPE"
  | "PERSISTENCE_INVALID_OUTBOX_MESSAGE_VERSION"
  | "PERSISTENCE_INVALID_RECORD_LIFECYCLE"
  | "PERSISTENCE_INVALID_PAGE"
  | "PERSISTENCE_INVALID_PAGE_REQUEST"
  | "PERSISTENCE_NOT_FOUND"
  | "PERSISTENCE_RECORD_NOT_DELETED"
  | "PERSISTENCE_RESTORE_WINDOW_EXPIRED"
  | "PERSISTENCE_TIMEOUT"
  | "PERSISTENCE_TRANSACTION_FAILED"
  | "PERSISTENCE_TRANSACTION_UNSUPPORTED"
  | "PERSISTENCE_UNAVAILABLE";

export interface PersistenceError extends CoreError {
  readonly code: PersistenceErrorCode;
}

export interface PersistenceErrorInput {
  readonly code: PersistenceErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  readonly details?: Readonly<Record<string, unknown>>;
}

export function persistenceError(input: PersistenceErrorInput): PersistenceError {
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
    ...(input.diagnostic === undefined ? {} : { diagnostic: input.diagnostic }),
    ...(input.details === undefined ? {} : { details: input.details }),
  };
}
