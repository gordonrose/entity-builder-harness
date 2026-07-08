import {
  diagnosticDescriptor,
  type DiagnosticDescriptor,
  type DiagnosticFacts,
  type FailureKind,
  type RecoveryAction,
} from "../src/diagnostics/index";

const failureKind: FailureKind = "user_input";
const recoveryAction: RecoveryAction = "ask_user";
const facts: DiagnosticFacts = {
  importId: "csv-import-123",
  rowNumber: 42,
  retryable: false,
  fieldName: null,
};
const accepted: DiagnosticDescriptor = diagnosticDescriptor({
  failureKind,
  failureSource: "user",
  severity: "warning",
  recovery: "user_correctable",
  action: recoveryAction,
  messageKey: "diagnostics.csv.invalid_row",
  facts,
});

void accepted;

// @ts-expect-error diagnostics should use the approved failure-kind vocabulary.
const rejectedFailureKind: FailureKind = "input_error";
void rejectedFailureKind;

// @ts-expect-error recovery actions must stay in the shared provider-neutral vocabulary.
const rejectedRecoveryAction: RecoveryAction = "send_email";
void rejectedRecoveryAction;

// @ts-expect-error diagnostic facts must stay primitive and safe for logs, metrics, and workflow correlation.
const rejectedFacts: DiagnosticFacts = { row: { id: "row-1" } };
void rejectedFacts;

diagnosticDescriptor({
  failureKind: "bug",
  failureSource: "app",
  severity: "error",
  recovery: "manual_investigation",
  // @ts-expect-error diagnostic facts must not carry rich runtime values.
  facts: { occurredAt: new Date() },
});
