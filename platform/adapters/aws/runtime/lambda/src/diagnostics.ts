import { captureDiagnosticRecord, createDiagnosticRecord, defineDiagnostic, requireDiagnosticRecord } from "@kanbien/core/diagnostics";

export const lambdaInvocationBudgetDiagnostic = defineDiagnostic({ code: "aws-lambda.invocation-budget-invalid", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["minimum-remaining-ms", "minimum-delivery-remaining-ms", "remaining-time"] },
    reason: { type: "enum", values: ["missing", "wrong-type", "not-finite", "not-integer", "not-positive", "negative", "not-after-total-margin"] },
    effect: { type: "enum", values: ["next-operation-not-started"] },
  } },
} as const);
export const lambdaDispatchOutcomeDiagnostic = defineDiagnostic({ code: "aws-lambda.dispatch-outcome-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    status: { type: "enum", values: ["queue-send-failed", "publish-marker-failed"] },
    effect: { type: "enum", values: ["earlier-effects-possible"] },
  } },
} as const);
export const lambdaRuntimeDiagnosticCatalog = Object.freeze({ owner: "aws-lambda", definitions: Object.freeze([
  lambdaInvocationBudgetDiagnostic, lambdaDispatchOutcomeDiagnostic,
]) });
export type LambdaBudgetReason = NonNullable<typeof lambdaInvocationBudgetDiagnostic.__detail>["reason"];
export function lambdaBudgetError(field: "minimum-remaining-ms" | "minimum-delivery-remaining-ms" | "remaining-time", reason: LambdaBudgetReason) {
  return Object.assign(new RangeError("Lambda invocation budget is invalid."), { diagnosticRecord: captureDiagnosticRecord(() => {
    const checked = createDiagnosticRecord(lambdaInvocationBudgetDiagnostic, { field, reason, effect: "next-operation-not-started" });
    return checked.ok ? requireDiagnosticRecord([lambdaInvocationBudgetDiagnostic], checked.value) : undefined;
  }) });
}
export function lambdaDispatchError(status: "queue-send-failed" | "publish-marker-failed") {
  return Object.assign(new Error("Lambda dispatch did not finish its queue handoff."), { diagnosticRecord: captureDiagnosticRecord(() => {
    const checked = createDiagnosticRecord(lambdaDispatchOutcomeDiagnostic, { status, effect: "earlier-effects-possible" });
    return checked.ok ? requireDiagnosticRecord([lambdaDispatchOutcomeDiagnostic], checked.value) : undefined;
  }) });
}
