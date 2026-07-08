import { deepEqual, equal, throws } from "node:assert/strict";
import {
  copyDiagnosticFacts,
  diagnosticDescriptor,
  isRetryableDiagnostic,
  isUserCorrectableDiagnostic,
} from "../src/diagnostics/index";

const userCorrectable = diagnosticDescriptor({
  failureKind: "user_input",
  failureSource: "user",
  severity: "warning",
  recovery: "user_correctable",
  action: "ask_user",
  messageKey: "diagnostics.csv.invalid_row",
  facts: {
    importId: "csv-import-123",
    rowNumber: 42,
    fieldName: "email",
  },
});

equal(userCorrectable.retryable, false);
equal(userCorrectable.userCorrectable, true);
equal(isUserCorrectableDiagnostic(userCorrectable), true);
equal(isRetryableDiagnostic(userCorrectable), false);
deepEqual(userCorrectable.facts, {
  importId: "csv-import-123",
  rowNumber: 42,
  fieldName: "email",
});

const retryable = diagnosticDescriptor({
  failureKind: "dependency_unavailable",
  failureSource: "provider",
  severity: "error",
  recovery: "automation_retryable",
  action: "retry",
});

equal(retryable.retryable, true);
equal(retryable.userCorrectable, false);
equal(isRetryableDiagnostic(retryable), true);
equal(isUserCorrectableDiagnostic(retryable), false);

const facts = { rowNumber: 1, accepted: false, fieldName: "email" };
const copiedFacts = copyDiagnosticFacts(facts);
deepEqual(copiedFacts, facts);
equal(copiedFacts === facts, false);

throws(
  () =>
    diagnosticDescriptor({
      failureKind: "not-real" as never,
      failureSource: "app",
      severity: "error",
      recovery: "manual_investigation",
    }),
  /failure kind/,
);
throws(
  () =>
    diagnosticDescriptor({
      failureKind: "bug",
      failureSource: "app",
      severity: "error",
      recovery: "manual_investigation",
      messageKey: " ",
    }),
  /messageKey/,
);
throws(
  () =>
    diagnosticDescriptor({
      failureKind: "dependency_unavailable",
      failureSource: "provider",
      severity: "error",
      recovery: "automation_retryable",
      retryable: false,
    }),
  /must be retryable/,
);
throws(
  () =>
    diagnosticDescriptor({
      failureKind: "user_input",
      failureSource: "user",
      severity: "warning",
      recovery: "user_correctable",
      userCorrectable: false,
    }),
  /must be user-correctable/,
);
throws(() => copyDiagnosticFacts({ rowNumber: Number.POSITIVE_INFINITY }), /finite number/);
throws(() => copyDiagnosticFacts({ fieldName: "email" }, { maxFactCount: 0 }), /positive integer/);
throws(() => copyDiagnosticFacts({ fieldName: "email" }, { maxStringLength: 4 }), /4 characters or fewer/);
throws(
  () =>
    copyDiagnosticFacts(
      {
        first: "a",
        second: "b",
      },
      { maxFactCount: 1 },
    ),
  /no more than 1 entries/,
);

console.log("packages/core diagnostics runtime test passed.");
