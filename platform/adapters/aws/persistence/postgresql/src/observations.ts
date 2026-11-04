import {
  observePlatformPersistenceDiagnostic,
  persistenceBoundaryDiagnosticRecord,
  persistenceLocalRejectionDiagnosticRecord,
  persistenceStoredRecordDiagnosticRecord,
  selectPlatformPersistenceDiagnosticEvidence,
  type PersistenceBoundaryDetail,
  type PersistenceLocalRejectionDetail,
  type PersistenceStoredRecordDetail,
  type PlatformPersistenceDiagnosticOptions,
} from "@kanbien/platform-persistence";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";

export function observeBoundary(options: PlatformPersistenceDiagnosticOptions | undefined, detail: PersistenceBoundaryDetail, cause?: unknown): { readonly diagnosticRecord?: DiagnosticRecord } {
  try { const diagnosticRecord = persistenceBoundaryDiagnosticRecord(detail); observePlatformPersistenceDiagnostic(options, diagnosticRecord, cause); return { diagnosticRecord }; }
  catch { return {}; }
}
export function localRejection(options: PlatformPersistenceDiagnosticOptions | undefined, detail: PersistenceLocalRejectionDetail): { readonly diagnosticRecord?: DiagnosticRecord } {
  try {
    const diagnosticRecord = persistenceLocalRejectionDiagnosticRecord(detail);
    observePlatformPersistenceDiagnostic(options, diagnosticRecord);
    return { diagnosticRecord };
  } catch { return {}; }
}

type Issue = PersistenceStoredRecordDetail["issues"][number];
/** One bounded record per operation, including list/filter reductions. */
export function storedObservation(options: PlatformPersistenceDiagnosticOptions | undefined,
  operation: PersistenceStoredRecordDetail["operation"], reduction: PersistenceStoredRecordDetail["reduction"],
  effect: PersistenceStoredRecordDetail["effect"]) {
  const issues: Issue[] = [];
  let truncated = false;
  let actualReduction = reduction;
  let decodeFailure: DiagnosticRecord | undefined;
  let decodeSource: ReturnType<typeof selectPlatformPersistenceDiagnosticEvidence> = {};
  let decodeDelegated = false;
  const evidence = (): { readonly diagnosticRecord?: DiagnosticRecord } => {
    if (issues.length === 0) return {};
    try { return { diagnosticRecord: persistenceStoredRecordDiagnosticRecord({ operation, reduction: actualReduction, effect, issues, truncated }) }; }
    catch { return {}; }
  };
  return {
    evidence,
    thrownEvidence(): { readonly diagnosticRecord?: DiagnosticRecord } {
      if (decodeFailure === undefined) return {};
      decodeDelegated = true;
      return { diagnosticRecord: decodeFailure };
    },
    threw(cause: unknown): void {
      actualReduction = "thrown";
      try { decodeFailure = persistenceBoundaryDiagnosticRecord({ operation, phase: "invocation", boundary: "decode", condition: "threw", effect });
        decodeSource = selectPlatformPersistenceDiagnosticEvidence(options ?? {}, cause); }
      catch { /* Unknown decoding evidence must not replace the throw. */ }
    },
    issue(field: Issue["field"], condition: Issue["condition"], ordinal?: number): void {
      const existing = issues.find((issue) => issue.field === field && issue.condition === condition);
      if (existing !== undefined) {
        const index = issues.indexOf(existing);
        issues[index] = { ...existing, count: Math.min(Number.MAX_SAFE_INTEGER, (existing.count ?? 1) + 1) };
      } else if (issues.length < 16) issues.push({ field, condition, ...(ordinal === undefined ? {} : { ordinal }) });
      else truncated = true;
    },
    flush(): void {
      if (decodeFailure !== undefined && !decodeDelegated) {
        try { observePlatformPersistenceDiagnostic(options, decodeFailure, decodeSource); } catch { /* Preserve decoding behavior. */ }
      }
      decodeFailure = undefined;
      decodeSource = {};
      decodeDelegated = false;
      if (issues.length === 0) { actualReduction = reduction; return; }
      try { const own = evidence().diagnosticRecord; if (own !== undefined) observePlatformPersistenceDiagnostic(options, own); }
      catch { /* Findings must not change the existing row reduction. */ }
      issues.length = 0;
      truncated = false;
      actualReduction = reduction;
    },
  };
}
export type StoredObservation = ReturnType<typeof storedObservation>;
