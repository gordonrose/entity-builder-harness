import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import {
  capturePlatformPersistenceDiagnostic,
  observePlatformPersistenceDiagnostic,
  persistenceCommandDiagnosticRecord,
  persistenceLocalRejectionDiagnosticRecord,
  persistenceStateReconciliationDiagnosticRecord,
  persistenceStoredAttributeDiagnosticRecord,
  selectPlatformPersistenceDiagnosticEvidence,
  type PersistenceCommandObservationDetail,
  type PersistenceLocalRejectionDetail,
  type PersistenceStateReconciliationDetail,
  type PersistenceStoredAttributeDetail,
  type PlatformPersistenceDiagnosticOptions,
} from "@kanbien/platform-persistence";
import type { DynamoDbPersistenceCommandClient } from "./client";
import { dynamoDbPersistenceOperationError, type DynamoDbPersistenceOperation } from "./errors";
import type { DynamoDbPersistenceItem } from "./records";

type Command = PersistenceCommandObservationDetail;
type Issue = PersistenceStoredAttributeDetail["issues"][number];
const nativeNames: Readonly<Record<string, Command["condition"]>> = {
  AccessDeniedException: "access-rejected", UnrecognizedClientException: "identity-unrecognized", ExpiredTokenException: "credential-expired",
  ConditionalCheckFailedException: "condition-rejected", TransactionCanceledException: "transaction-canceled", ResourceNotFoundException: "resource-unavailable",
  ValidationException: "input-rejected", ProvisionedThroughputExceededException: "throughput-exceeded", RequestLimitExceeded: "request-limit-exceeded",
  ThrottlingException: "throttled", TimeoutError: "timeout", NetworkingError: "network-failure",
};
function own(value: unknown, key: string): { status: Command["codeStatus"]; value?: unknown } {
  try {
    if ((typeof value !== "object" || value === null) && typeof value !== "function") return { status: "absent" };
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if (descriptor === undefined) return { status: "absent" };
    return "value" in descriptor ? { status: "recognized", value: descriptor.value } : { status: "unavailable" };
  } catch { return { status: "unavailable" }; }
}
function nativeCondition(value: unknown, names: Readonly<Record<string, Command["condition"]>> = nativeNames): Pick<Command, "condition" | "codeStatus"> {
  if (typeof value !== "string") return { condition: "unclassified", codeStatus: "wrong-type" };
  const condition = Object.prototype.hasOwnProperty.call(names, value) ? names[value] : undefined;
  return condition === undefined ? { condition: "unclassified", codeStatus: "unrecognized" } : { condition, codeStatus: "recognized" };
}
function cancellation(cause: unknown): NonNullable<Command["cancellation"]> {
  const field = own(cause, "CancellationReasons");
  if (field.status === "absent" || field.status === "unavailable") return { availability: field.status, truncated: false, reasons: [] };
  if (!Array.isArray(field.value)) return { availability: "wrong-type", truncated: false, reasons: [] };
  try {
    const length = own(field.value, "length").value;
    if (!Number.isSafeInteger(length) || typeof length !== "number" || length < 0) return { availability: "unavailable", truncated: false, reasons: [] };
    const reasons: NonNullable<Command["cancellation"]>["reasons"][number][] = [];
    const codes = { ConditionalCheckFailed: "condition-rejected", ProvisionedThroughputExceeded: "throughput-exceeded", ThrottlingError: "throttled", ValidationError: "input-rejected" } as const;
    for (let ordinal = 0; ordinal < Math.min(length, 64); ordinal++) {
      const entry = own(field.value, String(ordinal));
      const code = entry.status === "recognized" ? own(entry.value, "Code") : entry;
      reasons.push({ ordinal, ...(code.status === "recognized" ? nativeCondition(code.value, codes) : { condition: "unclassified", codeStatus: code.status }) });
    }
    return { availability: "available", truncated: length > 64, reasons };
  } catch { return { availability: "unavailable", truncated: false, reasons: [] }; }
}

/** One actual operation owns its observations; no shared writer is mutated. */
export function dynamoDbObservation(options: PlatformPersistenceDiagnosticOptions | undefined,
  operation: Command["operation"], role: Command["role"] = "primary") {
  let evidence: ReturnType<typeof selectPlatformPersistenceDiagnosticEvidence> = {};
  const effect = operation.startsWith("read_") || operation === "list_outbox" ? "not-assessed" : "unknown";
  const emit = (record: DiagnosticRecord, cause?: unknown): void => {
    const selected = observePlatformPersistenceDiagnostic(options, record, cause);
    evidence = { diagnosticRecord: selected.diagnosticRecord ?? record, ...(selected.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: selected.relatedDiagnosticRecords }) };
  };
  const observe = (boundary: Command["boundary"], cause: unknown): void => {
    try {
      const name = boundary === "invocation" ? own(cause, "name") : { status: "not-inspected" as const };
      const facts = name.status === "recognized" ? nativeCondition(name.value) : { condition: "unclassified" as const, codeStatus: name.status };
      emit(capturePlatformPersistenceDiagnostic(() => persistenceCommandDiagnosticRecord({ operation, boundary, role, ...facts,
        effect: boundary === "selection" || boundary === "encoding" || boundary === "client-construction" ? "not-invoked" : effect,
        ...(facts.condition === "transaction-canceled" ? { cancellation: cancellation(cause) } : {}) })), cause);
    } catch { /* Optional diagnostics cannot replace a workload failure. */ }
  };
  return {
    observe,
    async send(source: { readonly client: DynamoDbPersistenceCommandClient }, command: () => unknown): Promise<unknown> {
      let boundary: Command["boundary"] = "selection";
      try {
        const client = source.client;
        const send = client.send;
        boundary = "encoding";
        const argument = command();
        boundary = "invocation";
        return await Reflect.apply(send, client, [argument]);
      } catch (cause) { observe(boundary, cause); throw cause; }
    },
    at<T>(boundary: Command["boundary"], action: () => T): T {
      try { return action(); } catch (cause) { observe(boundary, cause); throw cause; }
    },
    decode<T>(attributes: AttributeObservation, action: () => T): T {
      return attributes.decode(action, emit, (cause) => observe("decoding", cause));
    },
    reject(field: PersistenceLocalRejectionDetail["field"], condition: PersistenceLocalRejectionDetail["condition"], phase: PersistenceLocalRejectionDetail["phase"] = "state-check", knownEffect: PersistenceLocalRejectionDetail["effect"] = "unknown"): ReturnType<typeof selectPlatformPersistenceDiagnosticEvidence> {
      emit(capturePlatformPersistenceDiagnostic(() => persistenceLocalRejectionDiagnosticRecord({ operation: operation as DynamoDbPersistenceOperation, field, condition, phase, effect: knownEffect })));
      return evidence;
    },
    source(cause: unknown): void {
      const selected = selectPlatformPersistenceDiagnosticEvidence(options ?? {}, cause, record => observePlatformPersistenceDiagnostic(options, record));
      if (selected.diagnosticRecord !== undefined) observePlatformPersistenceDiagnostic(options, selected.diagnosticRecord, { relatedDiagnosticRecords: selected.relatedDiagnosticRecords ?? [] });
      else for (const record of selected.relatedDiagnosticRecords ?? []) observePlatformPersistenceDiagnostic(options, record);
      evidence = selected;
    },
    error(legacyOperation: DynamoDbPersistenceOperation, legacyCause?: unknown): import("@kanbien/platform-persistence").PlatformPersistenceError {
      return { ...dynamoDbPersistenceOperationError(legacyOperation, legacyCause), ...evidence };
    },
    reconcile(observed: PersistenceStateReconciliationDetail["observed"]): void {
      observePlatformPersistenceDiagnostic(options, capturePlatformPersistenceDiagnostic(() => persistenceStateReconciliationDiagnosticRecord({ operation: operation as PersistenceStateReconciliationDetail["operation"], primaryOutcome: "condition-rejected", observed, effect: "read-result-observed" })));
    },
    evidence: () => evidence,
  };
}
export type DynamoDbObservation = ReturnType<typeof dynamoDbObservation>;

export function attributeObservation(options: PlatformPersistenceDiagnosticOptions | undefined, operation: PersistenceStoredAttributeDetail["operation"], reduction: PersistenceStoredAttributeDetail["reduction"]) {
  const issues: Issue[] = [];
  let truncated = false;
  let rowOrdinal: number | undefined;
  let dirty = false;
  let activeDecode: { failure?: { readonly error: TypeError; readonly source: unknown } } | undefined;
  const evidence = (): ReturnType<typeof selectPlatformPersistenceDiagnosticEvidence> => {
    if (issues.length === 0) return {};
    return { diagnosticRecord: capturePlatformPersistenceDiagnostic(() => persistenceStoredAttributeDiagnosticRecord({ operation, reduction, effect: operation.startsWith("read_") || operation === "list_outbox" ? "not-assessed" : "unknown", issues, truncated })) };
  };
  return {
    row(ordinal: number): void { rowOrdinal = Number.isSafeInteger(ordinal) && ordinal >= 0 ? ordinal : undefined; },
    issue(field: Issue["field"], condition: Issue["condition"], rowOrdinal?: number, attributeOrdinal?: number): void {
      dirty = true;
      const index = issues.findIndex((issue) => issue.field === field && issue.condition === condition);
      if (index >= 0) { const issue = issues[index]; if (issue !== undefined) issues[index] = { ...issue, count: Math.min(Number.MAX_SAFE_INTEGER, (issue.count ?? 1) + 1) }; }
      else if (issues.length < 16) issues.push({ field, condition, ...(rowOrdinal === undefined ? {} : { rowOrdinal }), ...(attributeOrdinal === undefined ? {} : { attributeOrdinal }) });
      else truncated = true;
    },
    failure(message: string, field: Issue["field"], condition: Issue["condition"], source?: unknown, attributeOrdinal?: number): TypeError {
      reduction = "thrown";
      this.issue(field, condition, rowOrdinal, attributeOrdinal);
      const selected = selectPlatformPersistenceDiagnosticEvidence(options ?? {}, source, record => observePlatformPersistenceDiagnostic(options, record));
      const error = Object.assign(new TypeError(message), { ...evidence(), ...selected });
      if (activeDecode !== undefined) activeDecode.failure = { error, source };
      return error;
    },
    decode<T>(action: () => T, known: (record: DiagnosticRecord, source: unknown) => void, unexpected: (cause: unknown) => void): T {
      const prior = activeDecode;
      const current: NonNullable<typeof activeDecode> = {};
      activeDecode = current;
      try { return action(); }
      catch (cause) {
        if (issues.length !== 0) reduction = "thrown";
        // Only a guard executed in this decode frame establishes new row evidence.
        // An old diagnostic-bearing TypeError thrown by a getter is still unknown.
        try {
          if (current.failure !== undefined && current.failure.error === cause) {
            const record = evidence().diagnosticRecord;
            if (record !== undefined) { known(record, current.failure.source); dirty = false; }
          } else unexpected(cause);
        } catch { /* Optional observation must preserve the original decoder throw. */ }
        throw cause;
      } finally { activeDecode = prior; }
    },
    evidence,
    reduction(value: PersistenceStoredAttributeDetail["reduction"]): void { reduction = value; },
    flush(): void { const record = dirty ? evidence().diagnosticRecord : undefined; if (record !== undefined) observePlatformPersistenceDiagnostic(options, record); issues.length = 0; truncated = false; dirty = false; },
  };
}
export type AttributeObservation = ReturnType<typeof attributeObservation>;

export function responseItem(response: unknown, observation: AttributeObservation): DynamoDbPersistenceItem | undefined {
  if (typeof response !== "object" || response === null) { observation.issue("response", response === null ? "null" : "not-object"); observation.reduction("null"); return undefined; }
  if (!("Item" in response)) return undefined;
  const item = (response as { readonly Item?: unknown }).Item;
  const valid = isItem(item);
  if (!valid && item !== undefined) { observation.issue("item", item === null ? "null" : typeof item === "object" ? "predicate-rejected" : "not-object"); observation.reduction("null"); }
  return valid ? item : undefined;
}
export function responseItems(response: unknown, observation: AttributeObservation): readonly DynamoDbPersistenceItem[] {
  if (typeof response !== "object" || response === null) { observation.issue("response", response === null ? "null" : "not-object"); observation.reduction("empty-list"); return []; }
  if (!("Items" in response)) return [];
  const items = (response as { readonly Items?: unknown }).Items;
  if (!Array.isArray(items)) { if (items !== undefined) observation.issue("items", items === null ? "null" : "not-array"); observation.reduction("empty-list"); return []; }
  return items.filter((item, ordinal) => {
    const valid = isItem(item);
    if (!valid) observation.issue("item", item === null ? "null" : typeof item === "object" ? "predicate-rejected" : "not-object", ordinal);
    return valid;
  });
}
function isItem(value: unknown): value is DynamoDbPersistenceItem { return typeof value === "object" && value !== null && !Array.isArray(value); }
