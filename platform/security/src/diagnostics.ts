// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: platform.security.diagnostic-definitions
//   version: 2
//   status: active
//   created_on: "2026-10-27"
//   updated_on: "2026-11-04"
//   layer: 03.product
//   domain: security
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Own versioned security observations, closed extraction and evidence-only peer translation.
//   portability: { class: reusable, targets: [entity-builder] }
//   used_by:
//   - id: platform.security.certificate-content
//     path: platform/security/src/certificates.ts
import { createDiagnosticRecord, defineDiagnostic, parseDiagnosticRecord, parseRelatedDiagnosticRecords, type DiagnosticDefinition, type DiagnosticRecord, type DiagnosticDetailSchema, type FailureKind } from "@kanbien/core/diagnostics";
import { jwtConfigurationDiagnosticCatalog } from "./jwt-configuration/index";
import {
  securityOperationReasons, type SecurityOperation, type SecurityOperationReason,
  securityTrustMaterialFailureReasons, securityPeerIdentityFailureReasons, securityPeerTrustFailureReasons,
  type SecurityTrustMaterialFailureReason, type SecurityPeerIdentityFailureReason, type SecurityPeerTrustFailureReason,
  type SecurityTrustMaterialFailureDetail, type SecurityPeerIdentityFailureDetail, type SecurityPeerTrustFailureDetail,
  securityCertificateBlockFailureReasons, type SecurityCertificateBlockFailureReason, type SecurityCertificateBlockFailureDetail,
} from "@kanbien/core/security";

/** Logical fields only. Provider keys/values stay with adapter configuration. */
export const securityConfigurationReferences = ["region", "identity-pool", "client", "additional-clients", "group-mapping", "scope-mapping", "claim-mapping", "table", "limit", "window", "bucket-capacity"] as const;
export const securityOwnedHeaderReferences = ["access-control-allow-credentials", "access-control-allow-headers", "access-control-allow-methods", "access-control-allow-origin", "access-control-max-age", "allow", "content-security-policy", "content-type", "permissions-policy", "referrer-policy", "retry-after", "vary", "x-content-type-options", "x-frame-options", "x-request-id"] as const;
export type SecurityObservationOptions<P extends SecurityOperation = SecurityOperation> =
  P extends "authorization" | "signing-key" ? { readonly referenceIndex?: number; readonly omittedCount?: number } :
  P extends "token" ? { readonly referenceIndex?: number } :
  P extends "adapter-configuration" ? { readonly referenceIndex?: number; readonly itemIndex?: number; readonly attribute?: "claim" | "equals" | "permissions"; readonly reference?: (typeof securityConfigurationReferences)[number] } :
  P extends "response-header" ? { readonly headerReference?: (typeof securityOwnedHeaderReferences)[number] } :
  P extends "rate-limit" ? { readonly reference?: (typeof securityConfigurationReferences)[number]; readonly boundary?: "transport" | "principal"; readonly keyCategory?: "client-address" | "principal" | "anonymous" } :
  P extends "authentication" ? { readonly omittedCount?: number; readonly attribute?: "principal-id" | "principal-type" | "subject" } :
  Readonly<Record<string, never>>;
const operationDefinitions = Object.entries(securityOperationReasons).flatMap(([phase, reasons]) => reasons.map((reason) => {
  const extra: Record<string, DiagnosticDetailSchema> = {};
  const indexed = phase === "token" && reason.startsWith("required-claim-")
    || phase === "authorization" && (reason.startsWith("claim-") || reason === "permission-missing" || reason === "undeclared-permission")
    || phase === "signing-key" && ["key-material-invalid", "key-entry-unreadable", "key-id-absent", "key-type-unsupported", "key-modulus-absent", "key-exponent-absent"].includes(reason)
    || phase === "adapter-configuration" && ["entry-wrong-type", "entry-empty", "attribute-missing", "attribute-wrong-type", "attribute-invalid", "duplicate-item"].includes(reason);
  if (indexed) extra["referenceIndex"] = { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER };
  if (phase === "adapter-configuration" && reason.startsWith("attribute-")) extra["attribute"] = { type: "enum", values: ["claim", "equals", "permissions"] };
  if (phase === "authentication" && reason === "principal-attribute-missing") extra["attribute"] = { type: "enum", values: ["principal-id", "principal-type", "subject"] };
  if (phase === "adapter-configuration" && reason === "attribute-invalid") extra["itemIndex"] = { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER };
  if (reason === "additional-observations-omitted") extra["omittedCount"] = { type: "integer", minimum: 1, maximum: Number.MAX_SAFE_INTEGER };
  if (phase === "adapter-configuration" || phase === "rate-limit" && reason === "configuration-invalid") extra["reference"] = { type: "enum", values: securityConfigurationReferences };
  if (phase === "response-header") extra["headerReference"] = { type: "enum", values: securityOwnedHeaderReferences };
  if (phase === "rate-limit" && reason !== "configuration-invalid") {
    extra["boundary"] = { type: "enum", values: ["transport", "principal"] };
    extra["keyCategory"] = { type: "enum", values: ["client-address", "principal", "anonymous"] };
  }
  const ordinary = phase === "cors" || phase === "response-header" || reason.endsWith("-wrong-type-ignored");
  const failureKind: FailureKind = reason === "additional-observations-omitted" ? "unknown" : phase === "adapter-configuration" || reason === "configuration-invalid" || reason === "undeclared-permission" ? "configuration"
    : reason === "hook-unavailable" ? "configuration" : reason === "component-failed" ? "unknown"
    : phase === "authentication-header" || phase === "token" || phase === "authentication" && reason !== "verifier-failed" || reason === "no-matching-usable-key" ? "authentication"
    : phase === "authorization" ? "authorization"
    : reason === "quota-exhausted" ? "rate_limited" : reason === "bucket-capacity-exhausted" ? "resource_exhausted"
    : reason === "dependency-failed" || reason === "fetch-failed" || reason === "http-unsuccessful" || reason === "verifier-failed" ? "dependency_unavailable" : "unknown";
  return defineDiagnostic({ code: `security.${phase}.${reason}`, version: 1,
    classification: { failureKind, failureSource: "unknown", severity: ordinary ? "info" : "warning", recovery: ordinary ? "not_recoverable" : "manual_investigation", action: "none" },
    detail: { type: "object", properties: { phase: { type: "enum", values: [phase] }, reason: { type: "enum", values: [reason] }, effect: { type: "enum", values: ["not-assessed"] }, ...extra }, optional: Object.keys(extra).filter((key) => key === "boundary" || key === "keyCategory") },
  });
}));

type RequiredSecurityOptions<P extends SecurityOperation, R extends string> = SecurityObservationOptions<P>
  & (P extends "adapter-configuration" ? { readonly reference: (typeof securityConfigurationReferences)[number] } : {})
  & (P extends "response-header" ? { readonly headerReference: (typeof securityOwnedHeaderReferences)[number] } : {})
  & (R extends "configuration-invalid" ? { readonly reference: (typeof securityConfigurationReferences)[number] } : {})
  & (R extends "additional-observations-omitted" ? { readonly omittedCount: number } : {})
  & (R extends `required-claim-${string}` | `claim-${string}` | "permission-missing" | "undeclared-permission" | "key-material-invalid" | "key-entry-unreadable" | "key-id-absent" | "key-type-unsupported" | "key-modulus-absent" | "key-exponent-absent" | "entry-wrong-type" | "entry-empty" | "duplicate-item" | `attribute-${string}` ? { readonly referenceIndex: number } : {})
  & (R extends `attribute-${string}` ? { readonly attribute: "claim" | "equals" | "permissions" } : {})
  & (R extends "attribute-invalid" ? { readonly itemIndex: number } : {})
  & (R extends "principal-attribute-missing" ? { readonly attribute: "principal-id" | "principal-type" | "subject" } : {});
type SecurityRecordArguments<P extends SecurityOperation, R extends string> = {} extends RequiredSecurityOptions<P, R> ? [options?: RequiredSecurityOptions<P, R>] : [options: RequiredSecurityOptions<P, R>];

export function securityOperationDiagnosticRecord<P extends SecurityOperation, R extends SecurityOperationReason<NoInfer<P>>>(phase: P, reason: R, ...args: SecurityRecordArguments<NoInfer<P>, NoInfer<R>>): DiagnosticRecord;
export function securityOperationDiagnosticRecord(phase: SecurityOperation, reason: string, options: SecurityObservationOptions = {}): DiagnosticRecord {
  const definition = operationDefinitions.find((item) => item.code === `security.${phase}.${reason}`);
  if (definition === undefined) throw new TypeError("PLATFORM_SECURITY_DIAGNOSTIC_INVALID");
  return observed(definition as DiagnosticDefinition, { phase, reason, effect: "not-assessed", ...options });
}

/** Privately retain native exceptions without enumerating/serializing their contents.
 * Existing throw-vs-return behaviour and exception messages remain unchanged.
 */
const observedFailures = new WeakMap<object, DiagnosticRecord>();
const observedCompanions = new WeakMap<object, readonly DiagnosticRecord[]>();
export function observeSecurityFailure(error: unknown, record: DiagnosticRecord, companions?: readonly DiagnosticRecord[]): unknown {
  if (typeof error === "object" && error !== null) {
    observedFailures.set(error, record);
    if (companions !== undefined) observedCompanions.set(error, companions);
    else observedCompanions.delete(error);
    return error;
  }
  const replacement = new Error("Security component failed.");
  observedFailures.set(replacement, record);
  return replacement;
}
export function securityFailureDiagnosticRecord(error: unknown): DiagnosticRecord | undefined {
  if (typeof error !== "object" || error === null) return undefined;
  const retained = observedFailures.get(error);
  if (retained !== undefined) return copySecurityDiagnosticRecord(retained);
  try {
    const field = Object.getOwnPropertyDescriptor(error, "diagnosticRecord");
    if (!field || !("value" in field)) return undefined;
    const candidate: unknown = field.value;
    return copySecurityDiagnosticRecord(candidate);
  } catch { /* Untrusted hook records cannot alter authentication outcomes. */ }
  return undefined;
}

function copySecurityDiagnosticRecord(candidate: unknown): DiagnosticRecord | undefined {
  for (const definition of platformSecurityDiagnosticCatalog.definitions) {
    const parsed = parseDiagnosticRecord(definition as DiagnosticDefinition, candidate);
    if (parsed.ok) return parsed.value;
  }
  return undefined;
}

/** Copy only closed, catalog-validated observations. Never forward the credential-bearing envelope. */
export function securityDiagnosticRecordsFrom(value: unknown): readonly DiagnosticRecord[] {
  const primary = securityFailureDiagnosticRecord(value);
  const records: DiagnosticRecord[] = primary === undefined ? [] : [primary];
  try {
    if (typeof value !== "object" || value === null) return records;
    const retained = observedCompanions.get(value);
    if (retained !== undefined) {
      const checked = parseRelatedDiagnosticRecords(platformSecurityDiagnosticCatalog.definitions as readonly DiagnosticDefinition[], retained);
      if (checked.ok) records.push(...checked.value);
      return Object.freeze(records);
    }
    const field = Object.getOwnPropertyDescriptor(value, "relatedDiagnosticRecords");
    if (field && "value" in field) {
      const checked = parseRelatedDiagnosticRecords(platformSecurityDiagnosticCatalog.definitions as readonly DiagnosticDefinition[], field.value);
      if (checked.ok) records.push(...checked.value);
    }
  } catch { /* Invalid optional observations never change the security outcome. */ }
  return Object.freeze(records);
}

/** Node verification codes on this failed invocation only; no exception text,
 * hostnames, certificates or guessed revocation support. Bounded native causes.
 */
export function observedSecurityPeerFailures(error: unknown): readonly DiagnosticRecord[] {
  const codes = new Set<string>();
  const seen = new Set<object>();
  try {
    for (let depth = 0; depth < 8 && typeof error === "object" && error !== null && !seen.has(error); depth++) {
      seen.add(error);
      const code = Object.getOwnPropertyDescriptor(error, "code");
      if (code && "value" in code && typeof code.value === "string") codes.add(code.value);
      const cause = Object.getOwnPropertyDescriptor(error, "cause");
      error = cause && "value" in cause ? cause.value : undefined;
    }
  } catch { /* No diagnostic authority from hostile native wrappers. */ }
  const records: DiagnosticRecord[] = [];
  if (codes.has("ERR_TLS_CERT_ALTNAME_INVALID")) records.push(securityPeerIdentityDiagnosticRecord("hostname-mismatch"));
  if (codes.has("CERT_HAS_EXPIRED")) records.push(securityPeerTrustDiagnosticRecord("expired"));
  if (codes.has("CERT_NOT_YET_VALID")) records.push(securityPeerTrustDiagnosticRecord("not-yet-valid"));
  if (["SELF_SIGNED_CERT_IN_CHAIN", "DEPTH_ZERO_SELF_SIGNED_CERT", "UNABLE_TO_VERIFY_LEAF_SIGNATURE", "UNABLE_TO_GET_ISSUER_CERT_LOCALLY"].some((code) => codes.has(code))) records.push(securityPeerTrustDiagnosticRecord("untrusted-chain"));
  return Object.freeze(records);
}

/** Internal operational observations: not security-incident classification or audit delivery.
 * Configuration/source access failures belong to configuration/files, not peer verification.
 * Adapters must map positive evidence; these constructors never infer a root cause.
 */
export const securityTrustMaterialDiagnostic = defineDiagnostic({
  code: "security.trust-material-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["certificate-content-parsing"] },
    reason: { type: "enum", values: securityTrustMaterialFailureReasons },
    effect: { type: "enum", values: ["not-assessed"] },
  } },
} as const);
export const securityPeerIdentityDiagnostic = defineDiagnostic({
  code: "security.peer-identity-verification-failed", version: 1,
  // Verification evidence does not distinguish peer configuration from local
  // expected-name/trust/clock settings. Do not assign provider fault.
  classification: { failureKind: "authentication", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["peer-identity-verification"] },
    reason: { type: "enum", values: securityPeerIdentityFailureReasons },
    effect: { type: "enum", values: ["not-assessed"] },
  } },
} as const);
export const securityPeerTrustDiagnostic = defineDiagnostic({
  code: "security.peer-trust-verification-failed", version: 1,
  classification: { failureKind: "authentication", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["peer-trust-verification"] },
    reason: { type: "enum", values: securityPeerTrustFailureReasons },
    effect: { type: "enum", values: ["not-assessed"] },
  } },
} as const);
export const securityCertificateBlockDiagnostic = defineDiagnostic({
  code: "security.certificate-block-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["certificate-content-parsing"] },
    reason: { type: "enum", values: securityCertificateBlockFailureReasons },
    blockNumber: { type: "integer", minimum: 1, maximum: Number.MAX_SAFE_INTEGER },
    effect: { type: "enum", values: ["not-assessed"] },
  } },
} as const);
export const securityConfigurationPredicateDiagnostic = defineDiagnostic({ code: "security.configuration-predicate-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["table", "region", "limit", "window", "bucket-capacity"] },
    reason: { type: "enum", values: ["empty", "wrong-type", "not-finite", "not-integer", "not-positive"] },
    phase: { type: "enum", values: ["configuration"] }, effect: { type: "enum", values: ["rejected"] },
  } },
} as const);
export function securityConfigurationPredicateRecord(field: "table" | "region" | "limit" | "window" | "bucket-capacity", reason: "empty" | "wrong-type" | "not-finite" | "not-integer" | "not-positive") {
  return observed(securityConfigurationPredicateDiagnostic, { field, reason, phase: "configuration", effect: "rejected" });
}
/** Observe the unchanged clock expression, without guessing which component threw. */
export const securityRateLimitClockDiagnostic = defineDiagnostic({ code: "security.rate-limit-clock-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation", action: "none" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["clock-evaluation"] }, reason: { type: "enum", values: ["evaluation-threw"] },
    effect: { type: "enum", values: ["decision-not-returned"] },
  } },
} as const);
export function securityRateLimitClockFailureRecord() {
  return observed(securityRateLimitClockDiagnostic, { phase: "clock-evaluation", reason: "evaluation-threw", effect: "decision-not-returned" });
}
/** Actual helper projections only; this says nothing about credential validity. */
export const securityPrincipalBoundaryDiagnostic = defineDiagnostic({ code: "security.authentication.principal-boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation", action: "none" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["principal-from-authentication"] },
    phase: { type: "enum", values: ["input-projection"] },
    field: { type: "enum", values: ["authenticated", "principal-id", "principal-type", "subject", "claims", "scopes"] },
    reason: { type: "enum", values: ["threw"] }, effect: { type: "enum", values: ["value-not-produced"] },
  } },
} as const);
export type SecurityPrincipalBoundaryDetail = NonNullable<typeof securityPrincipalBoundaryDiagnostic.__detail>;
export function securityPrincipalBoundaryDiagnosticRecord(field: SecurityPrincipalBoundaryDetail["field"]) {
  return observed(securityPrincipalBoundaryDiagnostic, { operation: "principal-from-authentication", phase: "input-projection", field, reason: "threw", effect: "value-not-produced" });
}
export const platformSecurityDiagnosticCatalog = Object.freeze({ owner: "security",
  definitions: Object.freeze([securityTrustMaterialDiagnostic, securityPeerIdentityDiagnostic, securityPeerTrustDiagnostic, securityCertificateBlockDiagnostic, securityConfigurationPredicateDiagnostic, securityRateLimitClockDiagnostic, securityPrincipalBoundaryDiagnostic, ...operationDefinitions, ...jwtConfigurationDiagnosticCatalog.definitions]),
});

function observed<T>(definition: DiagnosticDefinition<T>, detail: NoInfer<T>): DiagnosticRecord<T> {
  const record = createDiagnosticRecord(definition, detail);
  if (!record.ok) throw new TypeError("PLATFORM_SECURITY_DIAGNOSTIC_INVALID");
  return record.value;
}
export function securityTrustMaterialDiagnosticRecord(reason: SecurityTrustMaterialFailureReason): DiagnosticRecord<SecurityTrustMaterialFailureDetail> {
  return observed(securityTrustMaterialDiagnostic, { phase: "certificate-content-parsing", reason, effect: "not-assessed" });
}
export function securityPeerIdentityDiagnosticRecord(reason: SecurityPeerIdentityFailureReason): DiagnosticRecord<SecurityPeerIdentityFailureDetail> {
  return observed(securityPeerIdentityDiagnostic, { phase: "peer-identity-verification", reason, effect: "not-assessed" });
}
export function securityPeerTrustDiagnosticRecord(reason: SecurityPeerTrustFailureReason): DiagnosticRecord<SecurityPeerTrustFailureDetail> {
  return observed(securityPeerTrustDiagnostic, { phase: "peer-trust-verification", reason, effect: "not-assessed" });
}
export function securityCertificateBlockDiagnosticRecord(reason: SecurityCertificateBlockFailureReason, blockNumber: number): DiagnosticRecord<SecurityCertificateBlockFailureDetail> {
  return observed(securityCertificateBlockDiagnostic, { phase: "certificate-content-parsing", reason, blockNumber, effect: "not-assessed" });
}
