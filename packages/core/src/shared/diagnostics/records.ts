import { createDiagnosticRecord, type DiagnosticRecord } from "../../diagnostics/index";
import { coreDateDiagnostic, coreDateNormalizationDiagnostic, coreUuidDiagnostic, coreUuidGenerationDiagnostic, coreJsonDiagnostic } from "./definitions";

/** Never replace an existing record or change a thrown value to make it writable. */
export function attachCoreDiagnosticRecord<T>(error: T, record: DiagnosticRecord): T {
  inspectCoreDiagnosticAttachment(error, record);
  return error;
}
export type CoreDiagnosticAttachmentStatus = "unsupported-target" | "existing-field" | "inspection-failed" | "write-failed" | "write-accepted";
/** A write accepted by a proxy is not proof of later retention or observer delivery. */
export function inspectCoreDiagnosticAttachment(error: unknown, record: DiagnosticRecord): CoreDiagnosticAttachmentStatus {
  if ((typeof error !== "object" || error === null) && typeof error !== "function") return "unsupported-target";
  try { if (Object.getOwnPropertyDescriptor(error, "diagnosticRecord")) return "existing-field"; }
  catch { return "inspection-failed"; }
  try {
    Object.defineProperty(error, "diagnosticRecord", { value: record, enumerable: true, configurable: true });
    return "write-accepted";
  } catch { return "write-failed"; }
}
export function coreDateRecord(reason: "invalid-format" | "parse-rejected") {
  const result = createDiagnosticRecord(coreDateDiagnostic, { reason });
  if (!result.ok) throw new TypeError("CORE_DATE_DIAGNOSTIC_INVALID");
  return result.value;
}
export function coreDateNormalizationRecord(phase: "string-normalization" | "date-normalization") {
  const result = createDiagnosticRecord(coreDateNormalizationDiagnostic, { phase, reason: "invocation-threw" });
  if (!result.ok) throw new TypeError("CORE_DATE_DIAGNOSTIC_INVALID");
  return result.value;
}
export function coreUuidRecord(reason: "invalid-format") {
  const result = createDiagnosticRecord(coreUuidDiagnostic, { reason });
  if (!result.ok) throw new TypeError("CORE_UUID_DIAGNOSTIC_INVALID");
  return result.value;
}
export function coreUuidGenerationRecord(reason: "generation-threw" | "generated-value-invalid") {
  const result = createDiagnosticRecord(coreUuidGenerationDiagnostic, { reason });
  if (!result.ok) throw new TypeError("CORE_UUID_DIAGNOSTIC_INVALID");
  return result.value;
}
export function coreJsonRecord(reason: "non-finite-number" | "non-plain-object", depth: number, path: readonly number[], locationUnavailable = false) {
  const result = createDiagnosticRecord(coreJsonDiagnostic, { reason, depth, path, pathTruncated: depth > path.length,
    ...(locationUnavailable ? { locationUnavailable: true } : {}),
  });
  if (!result.ok) throw new TypeError("CORE_JSON_DIAGNOSTIC_INVALID");
  return result.value;
}
