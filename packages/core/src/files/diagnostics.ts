import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";

const validationOperations = ["name", "content-type", "size", "checksum-algorithm", "checksum-value", "storage-key", "scan-result", "access-intent"] as const;
const fields = ["name", "content-type", "size", "checksum-algorithm", "checksum-value", "storage-key", "scan-status", "scanner", "access-operation", "id", "tenant-id", "file-name", "correlation-id", "checksum", "metadata", "scan", "retention", "duplicate-strategy", "body", "storage", "created-at", "scanned-at", "scan-details", "retain-until", "legal-hold", "expires-at", "reason", "options", "storage-key-for", "now", "error-code", "default-message", "message-key", "params", "cause", "diagnostic", "diagnostic-record", "details"] as const;

export const coreFileValidationDiagnostic = defineDiagnostic({
  code: "core.files.validation-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: validationOperations },
    field: { type: "enum", values: ["name", "content-type", "size", "checksum-algorithm", "checksum-value", "storage-key", "scan-status", "scanner", "access-operation"] },
    reason: { type: "enum", values: ["empty", "too-long", "untrimmed", "path-separator", "control-character", "invalid-format", "not-safe-integer", "negative", "whitespace", "absolute-path", "empty-segment", "dot-segment", "parent-segment", "closed-value-rejected", "blank", "predicate-rejected"] },
    effect: { type: "enum", values: ["rejected"] },
    ordinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["ordinal"] },
} as const);
export const coreFileOperationDiagnostic = defineDiagnostic({
  code: "core.files.operation-rejected", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["put", "get", "delete"] },
    field: { type: "enum", values: ["id", "access-operation", "tenant-id", "file-name", "content-type", "size", "correlation-id", "checksum", "metadata", "scan", "retention", "duplicate-strategy"] },
    reason: { type: "enum", values: ["existing-file", "idempotent-mismatch", "file-absent", "operation-mismatch", "tenant-mismatch"] },
    effect: { type: "enum", values: ["rejected-before-write"] },
  } },
} as const);
export const coreFileBoundaryDiagnostic = defineDiagnostic({
  code: "core.files.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: [...validationOperations, "checksum", "metadata", "storage-ref", "retention-policy", "file-object", "put-input", "error", "initialize", "put", "get", "delete", "accepted-puts", "stored-files"] },
    phase: { type: "enum", values: ["input-projection", "normalization", "predicate-invocation", "result-projection", "metadata-enumeration", "metadata-copy", "storage-copy", "checksum-copy", "scan-copy", "retention-copy", "options-enumeration", "options-copy", "storage-key-selection", "storage-key-invocation", "default-storage-key", "map-selection", "map-lookup", "map-write", "history-selection", "history-copy", "history-append", "json-comparison", "map-delete", "snapshot-selection", "snapshot-iteration", "snapshot-copy", "state-creation"] },
    field: { type: "enum", values: fields },
    reason: { type: "enum", values: ["threw"] },
    effect: { type: "enum", values: ["value-not-produced", "put-write-not-reached", "map-write-unknown", "map-written-history-not-appended", "map-written-history-append-unknown", "map-written-history-appended", "delete-not-reached", "delete-unknown", "delete-returned", "read-only"] },
  }, optional: ["field"] },
} as const);
export const coreFileDiagnosticDefinitions = Object.freeze([coreFileValidationDiagnostic, coreFileOperationDiagnostic, coreFileBoundaryDiagnostic]);
export type CoreFileValidationDetail = NonNullable<typeof coreFileValidationDiagnostic.__detail>;
export type CoreFileOperationDetail = NonNullable<typeof coreFileOperationDiagnostic.__detail>;
export type CoreFileBoundaryDetail = NonNullable<typeof coreFileBoundaryDiagnostic.__detail>;
export interface CoreFileDiagnosticContext {
  readonly operation: CoreFileBoundaryDetail["operation"];
  readonly phase?: CoreFileBoundaryDetail["phase"];
  readonly field?: CoreFileBoundaryDetail["field"];
}
export interface CoreFileDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: CoreFileDiagnosticContext) => unknown;
}
/** New companions are opt-in and validated against these explicitly selected definitions. */
export interface CoreFileDiagnosticEvidence {
  readonly relatedDiagnosticDefinitions: readonly DiagnosticDefinition[];
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
}
function required<T>(definition: DiagnosticDefinition<T>, detail: T): DiagnosticRecord<T> {
  const result = createDiagnosticRecord(definition, detail);
  if (!result.ok) throw new TypeError("CORE_FILE_DIAGNOSTIC_INVALID");
  return result.value;
}
export function coreFileValidationDiagnosticRecord(detail: CoreFileValidationDetail) { return required(coreFileValidationDiagnostic, detail); }
export function coreFileOperationDiagnosticRecord(detail: CoreFileOperationDetail) { return required(coreFileOperationDiagnostic, detail); }
export function coreFileBoundaryDiagnosticRecord(detail: CoreFileBoundaryDetail) { return required(coreFileBoundaryDiagnostic, detail); }
