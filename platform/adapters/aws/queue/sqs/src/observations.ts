import {
  coreQueueBoundaryDiagnosticRecord, coreQueueValidationDiagnosticRecord,
  coreQueueReceiveReductionDiagnosticRecord, observeCoreQueueDiagnostic,
  selectCoreQueueDiagnosticEvidence, type CoreQueueDiagnosticOptions,
  type CoreQueueBoundaryDetail, type CoreQueueValidationDetail, type CoreQueueReceiveReductionDetail,
  captureDiagnosticRecord, requireDiagnosticRecord, coreDiagnosticCatalog, type CoreQueueDiagnosticContext, type DiagnosticRecord,
} from "@kanbien/core";
import type { PlatformSqsCommandClient } from "./worker";

type Native = NonNullable<CoreQueueBoundaryDetail["native"]>;
const allSdkOperations = ["send", "receive", "acknowledge", "release"] as const;
const keyOperations = ["send", "receive"] as const;
/** Pinned SQS modeled names only, restricted to the actual command's model. */
const modeledNativeNames: Readonly<Record<string, { readonly operations: readonly string[]; readonly condition: Native["condition"] }>> = {
  QueueDoesNotExist: { operations: allSdkOperations, condition: "queue-absent-reported" },
  RequestThrottled: { operations: allSdkOperations, condition: "request-throttled" },
  InvalidAddress: { operations: allSdkOperations, condition: "address-rejected" },
  InvalidSecurity: { operations: allSdkOperations, condition: "request-security-rejected" },
  UnsupportedOperation: { operations: allSdkOperations, condition: "operation-unsupported" },
  ReceiptHandleIsInvalid: { operations: ["acknowledge", "release"], condition: "receipt-rejected" },
  InvalidIdFormat: { operations: ["acknowledge"], condition: "receipt-rejected" },
  MessageNotInflight: { operations: ["release"], condition: "message-not-in-flight" },
  InvalidMessageContents: { operations: ["send"], condition: "message-content-rejected" },
  OverLimit: { operations: ["receive"], condition: "limit-reported" },
  KmsAccessDenied: { operations: keyOperations, condition: "key-access-rejected" },
  KmsThrottled: { operations: keyOperations, condition: "key-throttled" },
  KmsDisabled: { operations: keyOperations, condition: "key-rejected" },
  KmsInvalidKeyUsage: { operations: keyOperations, condition: "key-rejected" },
  KmsInvalidState: { operations: keyOperations, condition: "key-rejected" },
  KmsNotFound: { operations: keyOperations, condition: "key-rejected" },
  KmsOptInRequired: { operations: keyOperations, condition: "key-rejected" },
};
function nativeObservation(cause: unknown, operation: CoreQueueBoundaryDetail["operation"]): Native {
  try {
    if ((typeof cause !== "object" || cause === null) && typeof cause !== "function") return { codeAvailability: "absent", condition: "unknown" };
    const name = Object.getOwnPropertyDescriptor(cause, "name");
    if (name === undefined) return { codeAvailability: "absent", condition: "unknown" };
    if (!("value" in name)) return { codeAvailability: "unavailable", condition: "unknown" };
    if (typeof name.value !== "string") return { codeAvailability: "wrong-type", condition: "unknown" };
    const facts = Object.prototype.hasOwnProperty.call(modeledNativeNames, name.value) ? modeledNativeNames[name.value] : undefined;
    return facts !== undefined && facts.operations.includes(operation)
      ? { codeAvailability: "recognized", condition: facts.condition }
      : { codeAvailability: "unrecognized", condition: "unknown" };
  } catch { return { codeAvailability: "unavailable", condition: "unknown" }; }
}

export function sqsObservation(options: CoreQueueDiagnosticOptions | undefined, operation: CoreQueueBoundaryDetail["operation"]) {
  let evidence: ReturnType<typeof selectCoreQueueDiagnosticEvidence> = {};
  const emit = (build: () => DiagnosticRecord, context: CoreQueueDiagnosticContext, cause?: unknown): void => {
    const own = requireDiagnosticRecord(coreDiagnosticCatalog.definitions, captureDiagnosticRecord(build));
    const source = observeCoreQueueDiagnostic(options, own, cause, context);
    evidence = { diagnosticRecord: source.diagnosticRecord ?? own, ...(source.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: source.relatedDiagnosticRecords }) };
  };
  const failure = (boundary: CoreQueueBoundaryDetail["boundary"], cause: unknown, reason: "threw" | "rejected" = "threw"): void => {
    emit(() => coreQueueBoundaryDiagnosticRecord({ operation, boundary, reason,
      effect: operation === "decode" ? "not-assessed" : boundary === "construction" || boundary === "selection" || boundary === "encoding" ? "not-invoked" : "unknown",
      ...(boundary === "invocation" && (allSdkOperations as readonly string[]).includes(operation) ? { native: nativeObservation(cause, operation) } : {}),
    }), { operation, boundary }, cause);
  };
  return {
    failure,
    at<T>(boundary: CoreQueueBoundaryDetail["boundary"], action: () => T): T {
      try { return action(); } catch (cause) { failure(boundary, cause); throw cause; }
    },
    reject(field: CoreQueueValidationDetail["field"], reason: CoreQueueValidationDetail["reason"], cause?: unknown): ReturnType<typeof selectCoreQueueDiagnosticEvidence> {
      const validationOperation = operation === "client-initialization" ? "validate" : operation;
      emit(() => coreQueueValidationDiagnosticRecord({ operation: validationOperation, field, reason, effect: "rejected" }), { operation: validationOperation }, cause);
      return evidence;
    },
    async send(source: { readonly client: PlatformSqsCommandClient }, argument: () => unknown): Promise<unknown> {
      let boundary: CoreQueueBoundaryDetail["boundary"] = "selection";
      let pending: Promise<unknown>;
      try {
        const client = source.client;
        const send = client.send;
        boundary = "encoding";
        const command = argument();
        boundary = "invocation";
        pending = Reflect.apply(send, client, [command]) as Promise<unknown>;
      } catch (cause) { failure(boundary, cause); throw cause; }
      try { return await pending; } catch (cause) { failure("invocation", cause, "rejected"); throw cause; }
    },
    evidence: () => evidence,
  };
}
export type SqsObservation = ReturnType<typeof sqsObservation>;
export function receiveReductions(options: CoreQueueDiagnosticOptions) {
  type Issue = CoreQueueReceiveReductionDetail["issues"][number];
  const issues: Issue[] = [];
  let truncated = false;
  return {
    add(field: Issue["field"], reason: Issue["reason"], reduction: Issue["reduction"]): void {
      const index = issues.findIndex((item) => item.field === field && item.reason === reason && item.reduction === reduction);
      if (index >= 0) { const prior = issues[index]!; issues[index] = { ...prior, count: Math.min(Number.MAX_SAFE_INTEGER, (prior.count ?? 1) + 1) }; }
      else if (issues.length < 16) issues.push({ field, reason, reduction }); else truncated = true;
    },
    flush(): void {
      if (issues.length !== 0) {
        const own = requireDiagnosticRecord(coreDiagnosticCatalog.definitions, captureDiagnosticRecord(() => coreQueueReceiveReductionDiagnosticRecord({ operation: "receive", issues, truncated, effect: "reduction-observed" })));
        observeCoreQueueDiagnostic(options, own, undefined, { operation: "receive" });
      }
      issues.length = 0; truncated = false;
    },
  };
}
export type ReceiveReductions = ReturnType<typeof receiveReductions>;
