import { securityOperationDiagnosticRecord } from "../../src/index";

function compileOnly() {
  securityOperationDiagnosticRecord("token", "expired");
  securityOperationDiagnosticRecord("authorization", "claim-unmapped", { referenceIndex: 0 });
  securityOperationDiagnosticRecord("rate-limit", "quota-exhausted", { boundary: "transport", keyCategory: "anonymous" });
  // @ts-expect-error reason must belong to the selected operation, not an inferred union
  securityOperationDiagnosticRecord("token", "origin-missing");
  // @ts-expect-error provider keys and arbitrary setting names are not approved references
  securityOperationDiagnosticRecord("adapter-configuration", "missing", { reference: "MY_SECRET_KEY" });
  // @ts-expect-error token diagnostics cannot contain rate-limit context
  securityOperationDiagnosticRecord("token", "expired", { keyCategory: "principal" });
  // @ts-expect-error arbitrary claim values have no diagnostic field
  securityOperationDiagnosticRecord("authorization", "claim-mismatch", { claim: "secret" });
  // @ts-expect-error required claim failure must identify the configured requirement
  securityOperationDiagnosticRecord("token", "required-claim-missing");
  // @ts-expect-error adapter configuration must identify the logical setting
  securityOperationDiagnosticRecord("adapter-configuration", "missing", {});
  // @ts-expect-error indexed attribute failure must identify the actual attribute
  securityOperationDiagnosticRecord("adapter-configuration", "attribute-missing", { reference: "claim-mapping", referenceIndex: 0 });
}
void compileOnly;
