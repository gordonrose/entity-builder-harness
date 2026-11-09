import { deliverDiagnosticRecord, deliverDiagnosticRecords, type DiagnosticRecord } from "../../../src/diagnostics/index";
declare const record: DiagnosticRecord;
declare const records: readonly DiagnosticRecord[];
const completion: unknown = deliverDiagnosticRecord(record, () => Promise.resolve());
const noReceipt: void = deliverDiagnosticRecords(records, accepted => { const same: DiagnosticRecord = accepted; void same; });
void [completion, noReceipt];
// @ts-expect-error Raw exceptions are not diagnostic records.
deliverDiagnosticRecords([new Error("private")], () => undefined);
// @ts-expect-error A list is not a single diagnostic record.
deliverDiagnosticRecord(records, () => undefined);
// @ts-expect-error The receiver must be callable.
deliverDiagnosticRecords(records, {});
