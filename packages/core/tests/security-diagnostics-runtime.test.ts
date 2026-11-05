import { deepEqual, equal, throws } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, parseDiagnosticRecord } from "../src/diagnostics/index";
import { securityTrustMaterialFailureReasons, securityPeerIdentityFailureReasons, securityPeerTrustFailureReasons, securityOperationReasons } from "../src/security/index";

for (const reasons of [securityTrustMaterialFailureReasons, securityPeerIdentityFailureReasons, securityPeerTrustFailureReasons]) {
  equal(Object.isFrozen(reasons), true);
  equal(new Set(reasons).size, reasons.length);
  throws(() => (reasons as unknown as string[]).push("synthetic-sensitive-value"), TypeError);
}
equal(Object.isFrozen(securityOperationReasons), true);
for (const reasons of Object.values(securityOperationReasons)) {
  equal(Object.isFrozen(reasons), true);
  equal(new Set(reasons).size, reasons.length);
  throws(() => (reasons as unknown as string[]).push("synthetic-sensitive-value"), TypeError);
}
const definition = defineDiagnostic({ code: "fixture.security-content-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { reason: { type: "enum", values: securityTrustMaterialFailureReasons } } },
} as const);
for (const reason of securityTrustMaterialFailureReasons) {
  const record = createDiagnosticRecord(definition, { reason });
  equal(record.ok, true);
  if (!record.ok) throw new Error("fixture-invalid");
  equal(Object.isFrozen(record.value), true);
  equal(Object.isFrozen(record.value.detail), true);
  deepEqual(parseDiagnosticRecord(definition, record.value), record);
}
for (const detail of [{ reason: "expired" }, { reason: "synthetic-sensitive-value" }, { reason: "wrong-type", content: "synthetic-sensitive-value" }]) {
  equal(createDiagnosticRecord(definition, detail as never).ok, false);
}
let accessed = false;
equal(createDiagnosticRecord(definition, Object.defineProperty({}, "reason", { enumerable: true, get() { accessed = true; return "wrong-type"; } }) as never).ok, false);
equal(accessed, false);
console.log("Core security diagnostic vocabulary is immutable and closed.");
