import { equal, ok } from "node:assert/strict";
import * as diagnostics from "../src/diagnostics/index";
import type { DiagnosticRecord } from "../src/diagnostics/index";

/** CommonJS test-only substitution: exercise the real public callers, not copies. */
export function withDiagnosticDeliverySuppressed(run: (attempted: DiagnosticRecord[]) => void): void {
  const owner = Object.values(require.cache).map(item => item?.exports).find((item: unknown) => {
    if (typeof item !== "object" || item === null) return false;
    const field = Object.getOwnPropertyDescriptor(item, "deliverDiagnosticRecord");
    return field !== undefined && field.value === diagnostics.deliverDiagnosticRecord && field.writable;
  }) as typeof diagnostics | undefined;
  ok(owner, "the compiled shared implementation must be loaded through the public import");
  const single = owner.deliverDiagnosticRecord, multiple = owner.deliverDiagnosticRecords;
  const attempted: DiagnosticRecord[] = [];
  try {
    Object.assign(owner, {
      deliverDiagnosticRecord(record: DiagnosticRecord) { attempted.push(record); },
      deliverDiagnosticRecords(records: readonly DiagnosticRecord[]) { attempted.push(...records); },
    });
    run(attempted);
  } finally { Object.assign(owner, { deliverDiagnosticRecord: single, deliverDiagnosticRecords: multiple }); }
  equal(diagnostics.deliverDiagnosticRecord, single);
  equal(diagnostics.deliverDiagnosticRecords, multiple);
}
