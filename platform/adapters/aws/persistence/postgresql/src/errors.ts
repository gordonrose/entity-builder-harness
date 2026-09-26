import { platformPersistenceError, type PlatformPersistenceError } from "@kanbien/platform-persistence";

export type PostgreSqlPersistenceOperation =
  | "connect"
  | "transaction"
  | "migration"
  | "create_outbox"
  | "write_facts"
  | "write_atomic"
  | "read_outbox"
  | "list_outbox"
  | "claim_outbox"
  | "publish_outbox"
  | "read_processing"
  | "claim_processing"
  | "complete_processing"
  | "release_processing"
  | "append_lineage"
  | "read_lineage";

export const postgreSqlPersistenceProviderFailureClasses = [
  "access_denied",
  "conflict",
  "constraint",
  "resource_not_found",
  "timeout",
  "transaction_rolled_back",
  "transport",
  "validation",
  "unknown",
] as const;

export type PostgreSqlPersistenceProviderFailureClass = (typeof postgreSqlPersistenceProviderFailureClasses)[number];

export function postgreSqlPersistenceOperationError(
  operation: PostgreSqlPersistenceOperation,
  cause?: unknown,
): PlatformPersistenceError {
  return platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED",
    defaultMessage: "The persistence store operation could not complete.",
    messageKey: "platform.persistence.store.operation_failed",
    params: { operation, provider_failure_class: postgreSqlPersistenceProviderFailureClass(cause) },
  });
}

export function postgreSqlPersistenceProviderFailureClass(cause: unknown): PostgreSqlPersistenceProviderFailureClass {
  const code = sqlState(cause);
  if (code === undefined) return isTransportFailure(cause) ? "transport" : "unknown";
  if (code.startsWith("28")) return "access_denied";
  if (code === "23505") return "conflict";
  if (code.startsWith("23")) return "constraint";
  if (code === "42P01" || code === "3D000") return "resource_not_found";
  if (code === "57014") return "timeout";
  if (code.startsWith("40")) return "transaction_rolled_back";
  if (code.startsWith("08")) return "transport";
  if (code.startsWith("22") || code.startsWith("42")) return "validation";
  return "unknown";
}

export function isPostgreSqlUniqueViolation(cause: unknown): boolean {
  return sqlState(cause) === "23505";
}

function sqlState(cause: unknown): string | undefined {
  if (typeof cause !== "object" || cause === null || !("code" in cause)) return undefined;
  const code = (cause as { readonly code?: unknown }).code;
  return typeof code === "string" && /^[0-9A-Z]{5}$/.test(code) ? code : undefined;
}

function isTransportFailure(cause: unknown): boolean {
  if (typeof cause !== "object" || cause === null || !("code" in cause)) return false;
  const code = (cause as { readonly code?: unknown }).code;
  return typeof code === "string" && ["ECONNREFUSED", "ECONNRESET", "ETIMEDOUT", "ENOTFOUND", "EHOSTUNREACH"].includes(code);
}
