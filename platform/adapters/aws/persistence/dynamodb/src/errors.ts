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

export const dynamoDbPersistenceProviderFailureClasses = [
  "access_denied",
  "conditional_check_failed",
  "resource_not_found",
  "validation",
  "throttled",
  "transport",
  "unknown",
] as const;

export type DynamoDbPersistenceProviderFailureClass = typeof dynamoDbPersistenceProviderFailureClasses[number];

export function dynamoDbPersistenceOperationError(
  operation: DynamoDbPersistenceOperation,
  cause?: unknown,
): PlatformPersistenceError {
  return platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED",
    defaultMessage: "The persistence store operation could not complete.",
    messageKey: "platform.persistence.store.operation_failed",
    params: { operation, provider_failure_class: dynamoDbPersistenceProviderFailureClass(cause) },
  });
}

export function dynamoDbPersistenceProviderFailureClass(cause: unknown): DynamoDbPersistenceProviderFailureClass {
  const name = typeof cause === "object" && cause !== null && "name" in cause && typeof (cause as { readonly name?: unknown }).name === "string"
    ? (cause as { readonly name: string }).name
    : undefined;
  if (name === "AccessDeniedException" || name === "UnrecognizedClientException" || name === "ExpiredTokenException") return "access_denied";
  if (name === "ConditionalCheckFailedException" || name === "TransactionCanceledException") return "conditional_check_failed";
  if (name === "ResourceNotFoundException") return "resource_not_found";
  if (name === "ValidationException") return "validation";
  if (name === "ProvisionedThroughputExceededException" || name === "RequestLimitExceeded" || name === "ThrottlingException") return "throttled";
  if (name === "TimeoutError" || name === "NetworkingError") return "transport";
  return "unknown";
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
