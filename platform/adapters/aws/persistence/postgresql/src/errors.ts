import { AsyncLocalStorage } from "node:async_hooks";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { diagnosticDescriptor, diagnosticRelatedRecordLimit, type DiagnosticDescriptor, type DiagnosticDefinition } from "@kanbien/core/diagnostics";
import { securityPeerIdentityDiagnosticRecord, securityPeerTrustDiagnosticRecord, platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import { persistenceFailureClassifications, persistenceObservedPhases, persistenceObservedDiagnosticRecord, persistenceBoundaryDiagnosticRecord, platformPersistenceError, observePlatformPersistenceDiagnostic, selectPlatformPersistenceDiagnosticEvidence, platformPersistenceDiagnosticCatalog, type PlatformPersistenceDiagnosticOptions, type PlatformPersistenceError } from "@kanbien/platform-persistence";

export type PostgreSqlPersistenceOperation =
  | "administration"
  | "restore_verification"
  | "readiness"
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
  options?: PlatformPersistenceDiagnosticOptions,
  localRecord?: import("@kanbien/core/diagnostics").DiagnosticRecord,
  delivery: "all" | "native-only" = "all",
): PlatformPersistenceError {
  const diagnostic = postgreSqlFailureDiagnostic(cause);
  const local = selectPlatformPersistenceDiagnosticEvidence(options ?? {}, { diagnosticRecord: localRecord }).diagnosticRecord;
  const selected = selectPlatformPersistenceDiagnosticEvidence(options ?? {}, cause);
  const peers = diagnostic.facts.classification === "tls_trust_invalid" ? postgreSqlSecurityDiagnosticRecords(cause) : [];
  const hasNativeFacts = diagnostic.facts.classification !== "unknown" || diagnostic.facts.phase !== "unknown" || diagnostic.facts.code_status !== "absent";
  const native = persistenceObservedDiagnosticRecord(diagnostic.facts, operation);
  const own = local ?? (delivery === "all" && !hasNativeFacts ? persistenceBoundaryDiagnosticRecord({ operation, phase: "invocation", boundary: "body", condition: "threw",
    effect: ["readiness", "restore_verification", "read_outbox", "list_outbox", "read_processing", "read_lineage"].includes(operation) ? "not-assessed" : "unknown" }) : native);
  // Selecting a source does not deliver it. A direct catch always reports its
  // observed location; the transaction caller explicitly reports its own first.
  if (delivery === "all") observePlatformPersistenceDiagnostic(options, own, cause);
  else if (hasNativeFacts) observePlatformPersistenceDiagnostic(options, native);
  // These are positively generated adapter-owned security meanings, separate
  // from a source envelope that may already contain its full eight companions.
  const retained = [...(selected.diagnosticRecord === undefined ? [] : [selected.diagnosticRecord]), ...(selected.relatedDiagnosticRecords ?? [])];
  const related = [...(selected.relatedDiagnosticRecords ?? [])];
  for (const record of peers) {
    if (retained.some((source) => source.code === record.code && source.definitionVersion === record.definitionVersion && JSON.stringify(source.detail) === JSON.stringify(record.detail))) continue;
    if (related.length < diagnosticRelatedRecordLimit) related.push(record);
    observePlatformPersistenceDiagnostic({
      diagnosticDefinitions: [...platformSecurityDiagnosticCatalog.definitions, ...explicitDefinitions(options)],
      onDiagnostic: (observed) => options?.onDiagnostic?.(observed),
    }, record);
  }
  return platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED",
    defaultMessage: "The persistence store operation could not complete.",
    messageKey: "platform.persistence.store.operation_failed",
    params: { operation, provider_failure_class: postgreSqlPersistenceProviderFailureClass(cause) },
    details: { diagnostic },
    diagnostic,
    diagnosticRecord: selected.diagnosticRecord ?? own,
    relatedDiagnosticRecords: related,
    relatedDiagnosticDefinitions: [...coreDiagnosticCatalog.definitions, ...platformSecurityDiagnosticCatalog.definitions, ...platformPersistenceDiagnosticCatalog.definitions, ...explicitDefinitions(options)],
  });
}

function explicitDefinitions(options: PlatformPersistenceDiagnosticOptions | undefined): readonly DiagnosticDefinition[] {
  try { const definitions = options?.diagnosticDefinitions; return Array.isArray(definitions) ? [...definitions] : []; }
  catch { return []; }
}

export function postgreSqlPersistenceProviderFailureClass(cause: unknown): PostgreSqlPersistenceProviderFailureClass {
  const classification = postgreSqlFailureDiagnostic(cause).facts.classification;
  if (classification === "authentication_rejected" || classification === "permission_denied") return "access_denied";
  if (classification === "authentication_material_invalid") return "validation";
  if (classification === "content_unavailable") return "resource_not_found";
  if (classification === "transport_unavailable" || classification === "tls_trust_invalid") return "transport";
  // Retain the legacy broad timeout bucket; the diagnostic itself only
  // claims cancellation because 57014 also occurs after explicit cancellation.
  if (classification === "query_canceled") return "timeout";
  return classification;
}

export const postgreSqlFailureClassifications = persistenceFailureClassifications;
export type PostgreSqlFailureClassification = (typeof postgreSqlFailureClassifications)[number];
export type PostgreSqlObservedPhase = (typeof persistenceObservedPhases)[number];
export interface PostgreSqlFailureFacts {
  readonly classification: PostgreSqlFailureClassification;
  readonly code_status: "recognized" | "unrecognized" | "absent";
  readonly phase: PostgreSqlObservedPhase;
  readonly elapsed_ms: number | null;
}
export interface PostgreSqlFailureDiagnostic extends DiagnosticDescriptor {
  readonly facts: PostgreSqlFailureFacts & Readonly<Record<string, string | number | null>>;
}

// Observations belong to this adapter's actual invocation, never to a separate
// TCP/TLS probe. Keeping them private preserves driver error identity for SQL
// semantics without copying raw messages, codes, queries or credentials.
type Observation = { phase: PostgreSqlObservedPhase; elapsed_ms: number | null };
const observations = new WeakMap<object, Observation>();
const invocationObservations = new AsyncLocalStorage<WeakMap<object, Observation>>();

export async function observePostgreSqlOperation<T>(phase: Exclude<PostgreSqlObservedPhase, "unknown">, operation: () => Promise<T>): Promise<T> {
  // One map per outer invocation preserves a nested token failure while a
  // subsequent invocation using the same error object gets a fresh observation.
  const invocation = invocationObservations.getStore() ?? new WeakMap<object, Observation>();
  return invocationObservations.run(invocation, async () => {
    const started = performance.now();
    try { return await operation(); }
    catch (cause) {
      if (typeof cause === "object" && cause !== null) {
        const elapsed = Math.floor(performance.now() - started);
        const observation = invocation.get(cause) ?? { phase, elapsed_ms: Number.isSafeInteger(elapsed) && elapsed >= 0 && elapsed <= 3_600_000 ? elapsed : null };
        invocation.set(cause, observation);
        observations.set(cause, observation);
      }
      throw cause;
    }
  });
}

/** Only this closed descriptor may cross the diagnostic/log boundary. */
export function postgreSqlFailureDiagnostic(cause: unknown): PostgreSqlFailureDiagnostic {
  const codes = errorCodes(cause);
  const codeClassification = codes.map(classifyCode).find((value) => value !== "unknown") ?? "unknown";
  const classified = codeClassification !== "unknown" ? codeClassification
    : hasInvalidAuthenticationMaterial(cause) ? "authentication_material_invalid" : "unknown";
  const observation = observedCause(cause);
  const facts: PostgreSqlFailureDiagnostic["facts"] = {
    classification: classified,
    code_status: codes.length === 0 ? "absent" : codeClassification === "unknown" ? "unrecognized" : "recognized",
    phase: observation?.phase ?? "unknown",
    elapsed_ms: observation?.elapsed_ms ?? null,
  };
  const failureKind = classified === "authentication_material_invalid" ? "configuration"
    : classified === "authentication_rejected" ? "authentication"
    : classified === "permission_denied" ? "authorization"
    : classified === "timeout" ? "timeout"
    : classified === "conflict" || classified === "transaction_rolled_back" ? "conflict"
    : classified === "constraint" ? "data_integrity"
    : classified === "validation" ? "validation"
    : classified === "unknown" || classified === "query_canceled" ? "unknown" : "dependency_unavailable";
  // Retryability is an owning workload/controller decision, never inferred
  // from a transient-looking provider code or an interrupted operation.
  return { ...diagnosticDescriptor({ failureKind, failureSource: classified === "tls_trust_invalid" ? "unknown" : "provider", severity: "error", recovery: "manual_investigation", retryable: false, action: "escalate", facts }), facts };
}

/** Wrappers may retain a private cause; recover only this adapter's own
 * invocation observation, never a stage inferred from a successful probe. */
function observedCause(cause: unknown): Observation | undefined {
  const seen = new Set<object>();
  function visit(value: unknown, depth: number): Observation | undefined {
    if (depth > 3 || typeof value !== "object" || value === null || seen.has(value) || seen.size >= 32) return undefined;
    seen.add(value);
    const direct = observations.get(value);
    if (direct !== undefined) return direct;
    try {
      const nested = Object.getOwnPropertyDescriptor(value, "cause");
      const fromCause = nested && "value" in nested ? visit(nested.value, depth + 1) : undefined;
      if (fromCause !== undefined) return fromCause;
      const errors = Object.getOwnPropertyDescriptor(value, "errors");
      if (errors && "value" in errors && Array.isArray(errors.value)) {
        for (let index = 0; index < Math.min(errors.value.length, 32); index++) {
          const child = Object.getOwnPropertyDescriptor(errors.value, String(index));
          const result = child && "value" in child ? visit(child.value, depth + 1) : undefined;
          if (result !== undefined) return result;
        }
      }
    } catch { /* unreadable wrapper evidence remains unavailable */ }
    return undefined;
  }
  return visit(cause, 0);
}

/** Only positive invocation evidence; no inference from preflight or transport. */
export function postgreSqlSecurityDiagnosticRecords(cause: unknown) {
  const observed = new Set(errorCodes(cause).filter((code): code is string => typeof code === "string"));
  const records = [];
  if (observed.has("ERR_TLS_CERT_ALTNAME_INVALID")) records.push(securityPeerIdentityDiagnosticRecord("hostname-mismatch"));
  if (observed.has("CERT_HAS_EXPIRED")) records.push(securityPeerTrustDiagnosticRecord("expired"));
  if (observed.has("CERT_NOT_YET_VALID")) records.push(securityPeerTrustDiagnosticRecord("not-yet-valid"));
  if (["SELF_SIGNED_CERT_IN_CHAIN", "DEPTH_ZERO_SELF_SIGNED_CERT", "UNABLE_TO_VERIFY_LEAF_SIGNATURE", "UNABLE_TO_GET_ISSUER_CERT_LOCALLY"].some((code) => observed.has(code))) records.push(securityPeerTrustDiagnosticRecord("untrusted-chain"));
  return Object.freeze(records);
}

function classifyCode(code: unknown): PostgreSqlFailureClassification {
  if (typeof code !== "string") return "unknown";
  if (["CERT_HAS_EXPIRED", "CERT_NOT_YET_VALID", "ERR_TLS_CERT_ALTNAME_INVALID", "SELF_SIGNED_CERT_IN_CHAIN", "DEPTH_ZERO_SELF_SIGNED_CERT", "UNABLE_TO_VERIFY_LEAF_SIGNATURE", "UNABLE_TO_GET_ISSUER_CERT_LOCALLY"].includes(code)) return "tls_trust_invalid";
  if (code === "ETIMEDOUT") return "timeout";
  if (code === "57014") return "query_canceled";
  if (["ECONNREFUSED", "ECONNRESET", "EHOSTUNREACH", "ENETUNREACH", "EAI_AGAIN", "ENOTFOUND", "EPIPE"].includes(code)) return "transport_unavailable";
  if (!/^[0-9A-Z]{5}$/.test(code)) return "unknown";
  if (code.startsWith("28")) return "authentication_rejected";
  if (code === "42501") return "permission_denied";
  if (code === "42P01" || code === "3D000") return "content_unavailable";
  if (code === "23505") return "conflict";
  if (code.startsWith("23")) return "constraint";
  if (code.startsWith("40")) return "transaction_rolled_back";
  if (code.startsWith("08")) return "transport_unavailable";
  if (code.startsWith("22") || code.startsWith("42")) return "validation";
  return "unknown";
}

// pg emits this exact fixed invariant only after its password callback has
// returned invalid material. Match privately; never retain the message itself.
function hasInvalidAuthenticationMaterial(cause: unknown): boolean {
  const seen = new Set<object>();
  function visit(value: unknown, depth: number): boolean {
    if (depth > 3 || typeof value !== "object" || value === null || seen.has(value) || seen.size >= 32) return false;
    seen.add(value);
    try {
      const error = value as { message?: unknown; cause?: unknown; errors?: unknown };
      if (error.message === "SASL: SCRAM-SERVER-FIRST-MESSAGE: client password must be a string") return true;
      if (visit(error.cause, depth + 1)) return true;
      if (Array.isArray(error.errors)) for (const nested of error.errors.slice(0, 32)) if (visit(nested, depth + 1)) return true;
    } catch { /* unreadable provider fields remain unknown */ }
    return false;
  }
  return visit(cause, 0);
}

function errorCodes(cause: unknown): readonly unknown[] {
  const seen = new Set<object>();
  const codes: unknown[] = [];
  function visit(value: unknown, depth: number): void {
    if (depth > 3 || typeof value !== "object" || value === null || seen.has(value) || seen.size >= 32) return;
    seen.add(value);
    // Provider objects can have accessors. An unreadable field is unavailable,
    // never a reason to emit arbitrary error details or fail diagnostics.
    try {
      const error = value as { code?: unknown; cause?: unknown; errors?: unknown };
      if (error.code !== undefined && error.code !== null) codes.push(error.code);
      visit(error.cause, depth + 1);
      if (Array.isArray(error.errors)) for (const nested of error.errors.slice(0, 32)) visit(nested, depth + 1);
    } catch { /* no provider text crosses this boundary */ }
  }
  visit(cause, 0);
  return codes;
}

export function isPostgreSqlUniqueViolation(cause: unknown): boolean {
  return sqlState(cause) === "23505";
}

function sqlState(cause: unknown): string | undefined {
  if (typeof cause !== "object" || cause === null || !("code" in cause)) return undefined;
  const code = (cause as { readonly code?: unknown }).code;
  return typeof code === "string" && /^[0-9A-Z]{5}$/.test(code) ? code : undefined;
}
