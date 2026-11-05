import { deepEqual, equal, throws } from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseDiagnosticRecord } from "@kanbien/core/diagnostics";
import { securityTrustMaterialFailureReasons, securityPeerIdentityFailureReasons, securityPeerTrustFailureReasons } from "@kanbien/core/security";
import {
  validateCertificateAuthorityContent, platformSecurityDiagnosticCatalog,
  securityTrustMaterialDiagnostic, securityPeerIdentityDiagnostic, securityPeerTrustDiagnostic,
  securityTrustMaterialDiagnosticRecord, securityPeerIdentityDiagnosticRecord, securityPeerTrustDiagnosticRecord,
  securityCertificateBlockDiagnosticRecord, securityCertificateBlockDiagnostic,
} from "../src/index";

const bundle = readFileSync("platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt", "utf8");
const blocks = bundle.match(/-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----/g)!;
const malformed = "-----BEGIN CERTIFICATE-----\nsynthetic-certificate-canary\n-----END CERTIFICATE-----";
const valid = validateCertificateAuthorityContent(bundle);
deepEqual(valid, { ok: true, value: { certificateCount: blocks.length } });
if (!valid.ok) throw new Error("fixture-invalid");
equal(Object.isFrozen(valid.value), true);
deepEqual(Object.keys(valid.value), ["certificateCount"], "success reports syntax count, not trust/expiry/CA-role/identity/handshake claims");
deepEqual(validateCertificateAuthorityContent(`ignored surrounding text\n${blocks[0]}\nignored trailing text`), { ok: true, value: { certificateCount: 1 } });
for (const [input, reason] of [
  [undefined, "wrong-type"], [null, "wrong-type"], [1, "wrong-type"], [{ toString() { throw new Error("must-not-run"); } }, "wrong-type"],
  ["", "no-certificate-blocks"], ["synthetic-secret-canary", "no-certificate-blocks"],
  ["-----BEGIN CERTIFICATE-----", "no-certificate-blocks"],
] as const) {
  const result = validateCertificateAuthorityContent(input);
  equal(result.ok, false);
  if (result.ok) throw new Error("fixture-accepted");
  deepEqual(result.error, { code: "PLATFORM_CERTIFICATE_CONTENT_INVALID", diagnosticRecord: securityTrustMaterialDiagnosticRecord(reason) });
  equal(JSON.stringify(result).includes("canary"), false);
  equal(JSON.stringify(result).includes("BEGIN CERTIFICATE"), false);
  equal(Object.isFrozen(result.error), true);
}
for (const index of [0, 1, 2]) {
  const input = [blocks[0], blocks[0], blocks[0]];
  input[index] = malformed;
  const result = validateCertificateAuthorityContent(input.join("\n"));
  equal(result.ok, false);
  if (!result.ok) {
    deepEqual(result.error.diagnosticRecord, securityCertificateBlockDiagnosticRecord("malformed-certificate-block", index + 1));
    equal(Object.isFrozen(result.error), true);
    equal(JSON.stringify(result).includes("canary"), false);
  }
}
const begin = "-----BEGIN CERTIFICATE-----", end = "-----END CERTIFICATE-----";
for (const [input, reason, number] of [[begin, "unfinished-certificate-block", 1], [`${blocks[0]}\n${begin}`, "unfinished-certificate-block", 2],
  [end, "unmatched-certificate-end", 1], [`${blocks[0]}\n${end}`, "unmatched-certificate-end", 2], [`${begin}\n${begin}`, "unfinished-certificate-block", 1]] as const) {
  const strict = validateCertificateAuthorityContent(input, "strict-markers");
  equal(strict.ok, false);
  if (!strict.ok) deepEqual(strict.error.diagnosticRecord, securityCertificateBlockDiagnosticRecord(reason, number));
}
deepEqual(validateCertificateAuthorityContent(`${blocks[0]}\n${begin}`), { ok: true, value: { certificateCount: 1 } }, "production-compatible policy does not silently tighten acceptance");
deepEqual(validateCertificateAuthorityContent(`comments\n${blocks[0]}\ncomments`, "strict-markers"), { ok: true, value: { certificateCount: 1 } });
throws(() => validateCertificateAuthorityContent(bundle, "unknown-policy" as never), /PLATFORM_CERTIFICATE_POLICY_INVALID/);
for (const number of [0, -1, 1.5, Infinity, Number.MAX_SAFE_INTEGER + 1]) throws(() => securityCertificateBlockDiagnosticRecord("malformed-certificate-block", number), /PLATFORM_SECURITY_DIAGNOSTIC_INVALID/);
const blockRecord = securityCertificateBlockDiagnosticRecord("malformed-certificate-block", 2);
equal(parseDiagnosticRecord(securityCertificateBlockDiagnostic, { ...blockRecord, detail: { phase: "certificate-content-parsing", reason: "malformed-certificate-block", effect: "not-assessed" } }).ok, false);
for (const [definition, reasons, construct] of [
  [securityTrustMaterialDiagnostic, securityTrustMaterialFailureReasons, securityTrustMaterialDiagnosticRecord],
  [securityPeerIdentityDiagnostic, securityPeerIdentityFailureReasons, securityPeerIdentityDiagnosticRecord],
  [securityPeerTrustDiagnostic, securityPeerTrustFailureReasons, securityPeerTrustDiagnosticRecord],
] as const) {
  for (const reason of reasons) {
    const record = construct(reason as never);
    equal(parseDiagnosticRecord<unknown>(definition, record).ok, true);
    equal(Object.isFrozen(record.detail), true);
    equal(definition.classification.retryable, false);
    for (const detail of [
      { ...record.detail, phase: "synthetic-unobserved-phase" },
      { ...record.detail, reason: "synthetic-provider-error-canary" },
      { ...record.detail, effect: "not-started" },
      { ...record.detail, subject: "synthetic-private-name-canary" },
    ]) equal(parseDiagnosticRecord<unknown>(definition, { ...record, detail }).ok, false);
  }
  throws(() => construct("synthetic-unrecognized" as never), /PLATFORM_SECURITY_DIAGNOSTIC_INVALID/);
}
equal(parseDiagnosticRecord(securityTrustMaterialDiagnostic, { ...securityTrustMaterialDiagnosticRecord("wrong-type"), detail: { phase: "certificate-content-parsing", reason: "expired", effect: "not-assessed" } }).ok, false);
equal(parseDiagnosticRecord(securityPeerTrustDiagnostic, { ...securityPeerTrustDiagnosticRecord("untrusted-chain"), detail: { phase: "peer-trust-verification", reason: "hostname-mismatch", effect: "not-assessed" } }).ok, false);
equal(Object.isFrozen(platformSecurityDiagnosticCatalog), true);
equal(Object.isFrozen(platformSecurityDiagnosticCatalog.definitions), true);
equal(securityTrustMaterialDiagnostic.classification.failureSource, "platform");
equal(securityPeerIdentityDiagnostic.classification.failureSource, "unknown", "identity verification does not establish provider fault");
equal(securityPeerTrustDiagnostic.classification.failureSource, "unknown", "trust verification does not establish provider fault");
console.log("Shared security certificate-content validation and exact diagnostic alternatives passed; no peer verification is claimed.");
