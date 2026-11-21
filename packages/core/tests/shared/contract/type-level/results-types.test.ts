import { err, isErr, isOk, ok, type Result, type CoreError } from "../../../../src/shared/index";
import { diagnosticDescriptor } from "../../../../src/diagnostics/index";


// Time and UUID type-level cases now live in their shared/<theme>/type-level/ groups.

const success: Result<string> = ok("ready");
const failure: Result<string> = err({ code: "TEST_FAILURE", defaultMessage: "Expected failure." });
const diagnosticFailure: CoreError = {
  code: "CSV_IMPORT_INVALID_ROW",
  defaultMessage: "CSV import row is invalid.",
  diagnostic: diagnosticDescriptor({
    failureKind: "user_input",
    failureSource: "user",
    severity: "warning",
    recovery: "user_correctable",
    action: "ask_user",
  }),
};

if (isOk(success)) {
  const value: string = success.value;
  void value;
}

if (isErr(failure)) {
  const code: string = failure.error.code;
  void code;
}

void diagnosticFailure;
