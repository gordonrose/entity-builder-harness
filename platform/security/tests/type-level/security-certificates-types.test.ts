import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { SecurityTrustMaterialFailureDetail, SecurityCertificateBlockFailureDetail } from "@kanbien/core/security";
import { validateCertificateAuthorityContent, securityTrustMaterialDiagnosticRecord, securityPeerTrustDiagnosticRecord, securityPeerIdentityDiagnosticRecord } from "../../src/index";

const contentRecord: DiagnosticRecord<SecurityTrustMaterialFailureDetail> = securityTrustMaterialDiagnosticRecord("malformed-certificate-block");
const result = validateCertificateAuthorityContent(undefined);
if (!result.ok) { const record: DiagnosticRecord<SecurityTrustMaterialFailureDetail | SecurityCertificateBlockFailureDetail> = result.error.diagnosticRecord; void record; }
void contentRecord;
// @ts-expect-error a content parser cannot establish expiry
securityTrustMaterialDiagnosticRecord("expired");
// @ts-expect-error transport refusal is not peer trust verification evidence
securityPeerTrustDiagnosticRecord("connection-refused");
// @ts-expect-error peer-identity and peer-trust reasons are not interchangeable
securityPeerIdentityDiagnosticRecord("untrusted-chain");
