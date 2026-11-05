// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: core.security.diagnostic-contracts
//   version: 1
//   status: active
//   created_on: "2026-10-27"
//   updated_on: "2026-10-30"
//   layer: 03.product
//   domain: security
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Define provider-neutral security failure observations without runtime or secret-bearing evidence.
//   portability: { class: reusable, targets: [entity-builder] }
//   used_by:
//   - id: platform.security.diagnostic-definitions
//     path: platform/security/src/diagnostics.ts

import { createDiagnosticRecord, defineDiagnostic } from "../diagnostics/index";

/** Content parsing is not peer trust, certificate lifetime or identity verification. */
export const securityTrustMaterialFailureReasons = Object.freeze([
  "wrong-type", "no-certificate-blocks", "malformed-certificate-block",
] as const);
export type SecurityTrustMaterialFailureReason = (typeof securityTrustMaterialFailureReasons)[number];

export const securityPeerIdentityFailureReasons = Object.freeze([
  "hostname-mismatch", "unclassified-peer-identity-failure",
] as const);
export type SecurityPeerIdentityFailureReason = (typeof securityPeerIdentityFailureReasons)[number];

/** These require actual failed verification evidence, not parsing or a guessed cause.
 * Lifetime/revocation observations may concern any certificate in the verified chain.
 */
export const securityPeerTrustFailureReasons = Object.freeze([
  "untrusted-chain", "expired", "not-yet-valid", "revoked", "unclassified-peer-trust-failure",
] as const);
export type SecurityPeerTrustFailureReason = (typeof securityPeerTrustFailureReasons)[number];

export interface SecurityTrustMaterialFailureDetail {
  readonly phase: "certificate-content-parsing";
  readonly reason: SecurityTrustMaterialFailureReason;
  /** A security observation alone establishes no application-operation outcome. */
  readonly effect: "not-assessed";
}
/** Positional syntax evidence only; neither contents nor identity are exposed. */
export const securityCertificateBlockFailureReasons = Object.freeze([
  "malformed-certificate-block", "unfinished-certificate-block", "unmatched-certificate-end",
] as const);
export type SecurityCertificateBlockFailureReason = (typeof securityCertificateBlockFailureReasons)[number];
export interface SecurityCertificateBlockFailureDetail {
  readonly phase: "certificate-content-parsing";
  readonly reason: SecurityCertificateBlockFailureReason;
  readonly blockNumber: number;
  readonly effect: "not-assessed";
}
export interface SecurityPeerIdentityFailureDetail {
  readonly phase: "peer-identity-verification";
  readonly reason: SecurityPeerIdentityFailureReason;
  readonly effect: "not-assessed";
}
export interface SecurityPeerTrustFailureDetail {
  readonly phase: "peer-trust-verification";
  readonly reason: SecurityPeerTrustFailureReason;
  readonly effect: "not-assessed";
}

/** Observations, not claims about fault, incidents, identity or mutation outcomes.
 * Indices are zero-based references to configured requirements or fetched key
 * entries, never the values stored at those positions.
 */
export const securityOperationReasons = Object.freeze({
  "authentication-header": ["missing", "unsupported-scheme", "malformed-bearer"],
  authentication: ["verifier-rejected-unclassified", "verifier-failed", "component-failed", "subject-missing", "subject-wrong-type", "subject-empty", "hook-unavailable", "principal-attribute-missing", "additional-observations-omitted"],
  token: ["segment-count", "empty-segment", "header-json-invalid", "header-not-object", "payload-json-invalid", "payload-not-object", "algorithm-missing", "algorithm-wrong-type", "algorithm-empty", "algorithm-unsupported", "key-id-missing", "key-id-wrong-type", "key-id-empty", "signature-invalid", "issuer-missing", "issuer-wrong-type", "issuer-empty", "issuer-mismatch", "required-claim-missing", "required-claim-wrong-type", "required-claim-mismatch", "expiry-missing", "expiry-wrong-type", "expired", "not-before-in-future", "issued-at-in-future", "not-before-wrong-type-ignored", "issued-at-wrong-type-ignored", "subject-missing", "subject-wrong-type", "subject-empty"],
  "signing-key": ["fetch-failed", "http-unsuccessful", "response-json-invalid", "key-set-invalid", "key-material-invalid", "key-entry-unreadable", "key-id-absent", "key-type-unsupported", "key-modulus-absent", "key-exponent-absent", "no-matching-usable-key", "additional-observations-omitted"],
  authorization: ["permission-missing", "undeclared-permission", "claim-missing", "claim-wrong-type", "claim-empty", "claim-unmapped", "claim-mismatch", "component-failed", "resource-denied", "additional-observations-omitted"],
  cors: ["origin-missing", "origin-empty", "origin-allowed", "origin-not-allowlisted", "preflight-path-missing", "preflight-path-present"],
  "response-header": ["platform-owned-override-ignored"],
  "rate-limit": ["quota-exhausted", "bucket-capacity-exhausted", "configuration-invalid", "dependency-failed", "rejected-unclassified"],
  "adapter-configuration": ["missing", "empty", "invalid-json", "wrong-shape", "entry-wrong-type", "entry-empty", "attribute-missing", "attribute-wrong-type", "attribute-invalid", "duplicate-item", "invalid-positive-integer"],
} as const);
for (const reasons of Object.values(securityOperationReasons)) Object.freeze(reasons);
export type SecurityOperation = keyof typeof securityOperationReasons;
export type SecurityOperationReason<P extends SecurityOperation> = (typeof securityOperationReasons)[P][number];

export const coreSecurityPrimitiveDiagnostic = defineDiagnostic({ code: "core.security.primitive-invalid", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["secret-string", "hash-algorithm", "hash-value", "security-policy-id", "sensitive-value-kind", "data-sensitivity"] },
    reason: { type: "enum", values: ["empty", "surrounding-whitespace", "whitespace", "unsupported"] },
  } },
} as const);
export const coreSecurityDiagnosticDefinitions = Object.freeze([coreSecurityPrimitiveDiagnostic]);
export function coreSecurityPrimitiveRecord(field: NonNullable<typeof coreSecurityPrimitiveDiagnostic.__detail>["field"], reason: NonNullable<typeof coreSecurityPrimitiveDiagnostic.__detail>["reason"]) {
  const result = createDiagnosticRecord(coreSecurityPrimitiveDiagnostic, { field, reason });
  if (!result.ok) throw new TypeError("CORE_SECURITY_DIAGNOSTIC_INVALID");
  return result.value;
}
