// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: platform.security.certificate-content
//   version: 1
//   status: active
//   created_on: "2026-10-27"
//   updated_on: "2026-10-27"
//   layer: 03.product
//   domain: security
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Validate certificate bundle syntax using the established runtime parser without claiming peer trust.
//   portability: { class: reusable, targets: [entity-builder] }
//   used_by:
//   - id: platform.security.index
//     path: platform/security/src/index.ts
import { X509Certificate } from "node:crypto";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { SecurityTrustMaterialFailureReason, SecurityTrustMaterialFailureDetail, SecurityCertificateBlockFailureDetail } from "@kanbien/core/security";
import type { Result } from "@kanbien/core/shared";
import { securityTrustMaterialDiagnosticRecord, securityCertificateBlockDiagnosticRecord } from "./diagnostics";

export interface CertificateAuthorityContentObservation {
  /** Number of complete certificate blocks that were successfully parsed. */
  readonly certificateCount: number;
}
export interface CertificateAuthorityContentError {
  readonly code: "PLATFORM_CERTIFICATE_CONTENT_INVALID";
  readonly diagnosticRecord: DiagnosticRecord<SecurityTrustMaterialFailureDetail | SecurityCertificateBlockFailureDetail>;
}

/** Pure content-validation boundary: no file access, environment or network calls.
 * Recognizes complete PEM certificate blocks and parses each using X509Certificate.
 * Like existing certificate bundle readers, surrounding text is not interpreted.
 * Success is syntax only: NOT CA-role, lifetime, chain, revocation, hostname or TLS
 * verification. The caller retains content privately; it is never diagnostic detail.
 */
export function validateCertificateAuthorityContent(content: unknown, policy: "compatible-complete-blocks" | "strict-markers" = "compatible-complete-blocks"): Result<CertificateAuthorityContentObservation, CertificateAuthorityContentError> {
  if (policy !== "compatible-complete-blocks" && policy !== "strict-markers") throw new TypeError("PLATFORM_CERTIFICATE_POLICY_INVALID");
  const invalidBlock = (reason: Parameters<typeof securityCertificateBlockDiagnosticRecord>[0], blockNumber: number): Result<never, CertificateAuthorityContentError> => ({
    ok: false, error: Object.freeze({ code: "PLATFORM_CERTIFICATE_CONTENT_INVALID", diagnosticRecord: securityCertificateBlockDiagnosticRecord(reason, blockNumber) }),
  });
  const invalid = (reason: SecurityTrustMaterialFailureReason): Result<never, CertificateAuthorityContentError> => ({
    ok: false, error: Object.freeze({ code: "PLATFORM_CERTIFICATE_CONTENT_INVALID", diagnosticRecord: securityTrustMaterialDiagnosticRecord(reason) }),
  });
  if (typeof content !== "string") return invalid("wrong-type");
  // Strict marker policy is opt-in: migrating diagnostics must not silently
  // reject files previously accepted by the complete-block reader.
  if (policy === "strict-markers") {
    let opened = false, blockNumber = 0;
    for (const marker of content.matchAll(/-----BEGIN CERTIFICATE-----|-----END CERTIFICATE-----/g)) {
      if (marker[0] === "-----BEGIN CERTIFICATE-----") {
        if (opened) return invalidBlock("unfinished-certificate-block", blockNumber);
        opened = true; blockNumber++;
      } else {
        if (!opened) return invalidBlock("unmatched-certificate-end", blockNumber + 1);
        opened = false;
      }
    }
    if (opened) return invalidBlock("unfinished-certificate-block", blockNumber);
  }
  const certificates = content.match(/-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----/g);
  if (certificates === null || certificates.length === 0) return invalid("no-certificate-blocks");
  for (let index = 0; index < certificates.length; index++) {
    try { new X509Certificate(certificates[index]!); }
    catch {
      // Number only, never native parser text or certificate content.
      return invalidBlock("malformed-certificate-block", index + 1);
    }
  }
  return { ok: true, value: Object.freeze({ certificateCount: certificates.length }) };
}
