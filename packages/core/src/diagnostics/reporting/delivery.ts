import type { DiagnosticRecord } from "../record";

const intrinsicPromiseThen = Promise.prototype.then;

/** Delivery assumes owner-validated records; it neither validates nor logs them. */
export function deliverDiagnosticRecord(
  record: DiagnosticRecord,
  receive: (record: DiagnosticRecord) => unknown,
): unknown {
  try {
    const pending = receive(record);
    if (pending !== undefined) {
      const ignore = (): void => undefined;
      try { Reflect.apply(intrinsicPromiseThen, pending, [undefined, ignore]); }
      catch { Reflect.apply(intrinsicPromiseThen, Promise.resolve(pending), [undefined, ignore]); }
    }
    return pending;
  } catch { return undefined; }
}

/** Attempt each record once, in call order, without awaiting optional reporting. */
export function deliverDiagnosticRecords(
  records: readonly DiagnosticRecord[],
  receive: (record: DiagnosticRecord) => unknown,
): void {
  for (const record of records) deliverDiagnosticRecord(record, receive);
}
