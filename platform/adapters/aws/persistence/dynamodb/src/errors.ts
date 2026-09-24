import { platformPersistenceError, type PlatformPersistenceError } from "@kanbien/platform-persistence";

export type DynamoDbPersistenceOperation =
  | "create_outbox"
  | "read_outbox"
  | "list_outbox"
  | "claim_outbox"
  | "publish_outbox"
  | "read_processing"
  | "claim_processing"
  | "complete_processing"
  | "release_processing"
  | "append_lineage"
  | "read_lineage"
  | "write_facts"
  | "write_atomic";

export function dynamoDbPersistenceOperationError(
  operation: DynamoDbPersistenceOperation,
): PlatformPersistenceError {
  return platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED",
    defaultMessage: "The persistence store operation could not complete.",
    messageKey: "platform.persistence.store.operation_failed",
    params: { operation },
  });
}

export function isDynamoDbConditionalFailure(error: unknown): boolean {
  return typeof error === "object"
    && error !== null
    && "name" in error
    && (error as { readonly name?: unknown }).name === "ConditionalCheckFailedException";
}

export function isDynamoDbTransactionCancellation(error: unknown): boolean {
  return typeof error === "object"
    && error !== null
    && "name" in error
    && (error as { readonly name?: unknown }).name === "TransactionCanceledException";
}
