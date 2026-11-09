import { equal } from "node:assert/strict";
import { err, isErr, isOk, ok } from "../../../../src/shared/index";
import { diagnosticDescriptor } from "../../../../src/diagnostics/index";

const success = ok({ enabled: true });
equal(isOk(success), true);
if (!isOk(success)) {
  throw new Error("Expected result to be ok.");
}
equal(success.value.enabled, true);

const failure = err({ code: "TEST_FAILURE", defaultMessage: "Expected failure." });
equal(isErr(failure), true);
if (!isErr(failure)) {
  throw new Error("Expected result to be err.");
}
equal(failure.error.code, "TEST_FAILURE");
equal(failure.error.defaultMessage, "Expected failure.");

const diagnosticFailure = err({
  code: "CSV_IMPORT_INVALID_ROW",
  defaultMessage: "CSV import row is invalid.",
  diagnostic: diagnosticDescriptor({
    failureKind: "user_input",
    failureSource: "user",
    severity: "warning",
    recovery: "user_correctable",
    action: "ask_user",
  }),
});
equal(isErr(diagnosticFailure), true);
if (!isErr(diagnosticFailure)) {
  throw new Error("Expected diagnostic failure to be err.");
}
equal(diagnosticFailure.error.diagnostic?.failureKind, "user_input");
equal(diagnosticFailure.error.diagnostic?.userCorrectable, true);


console.log("Core shared result unit tests passed.");
