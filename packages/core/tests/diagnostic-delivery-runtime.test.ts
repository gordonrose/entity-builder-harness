import { deepEqual, equal } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, deliverDiagnosticRecord, deliverDiagnosticRecords, type DiagnosticRecord } from "../src/diagnostics/index";
import { deliverDiagnosticRecords as rootDelivery } from "../src/index";

async function main(): Promise<void> {
  equal(rootDelivery, deliverDiagnosticRecords);
  const definition = defineDiagnostic({ code: "fixture.delivery", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable" },
    detail: { type: "integer", minimum: 0, maximum: 9 } } as const);
  const records = Array.from({ length: 10 }, (_, ordinal) => {
    const result = createDiagnosticRecord(definition, ordinal);
    if (!result.ok) throw new Error("fixture-invalid");
    return result.value;
  });
  const marker = Object.freeze({ accepted: true });
  const receiver = { receive(record: DiagnosticRecord) { equal(this, receiver); equal(record, records[0]); return marker; } };
  equal(deliverDiagnosticRecord(records[0]!, record => receiver.receive(record)), marker);
  equal(deliverDiagnosticRecord(records[0]!, () => { throw new Error("private-reporting-canary"); }), undefined);
  const unhandled: unknown[] = [], uncaught = (reason: unknown): void => { unhandled.push(reason); };
  process.on("unhandledRejection", uncaught);
  try {
    let shadowReads = 0, thenableCalls = 0;
    for (const mode of ["void", "number", "object", "throw", "resolved", "rejected", "shadowed", "thenable", "then-getter"] as const) {
      const seen: DiagnosticRecord[] = [];
      const returned = deliverDiagnosticRecords(records, record => {
        seen.push(record);
        if (mode === "throw") throw new Error("private-reporting-canary");
        if (mode === "number") return 17;
        if (mode === "object") return marker;
        if (mode === "void") return;
        if (mode === "then-getter") return Object.defineProperty({}, "then", { get() { throw new Error("private-reporting-canary"); } });
        if (mode === "thenable") {
          const thenable = { then(_resolve: unknown, reject: (reason: unknown) => void) {
            equal(this, thenable); thenableCalls++; reject(new Error("private-reporting-canary"));
          } };
          return thenable;
        }
        const pending = mode === "resolved" ? Promise.resolve() : Promise.reject(new Error("private-reporting-canary"));
        if (mode === "shadowed") Object.defineProperty(pending, "then", { get() { shadowReads++; throw new Error("must not read own then"); } });
        return pending;
      });
      equal(returned, undefined);
      deepEqual(seen, records, "every record is attempted once in order despite earlier failures");
      seen.forEach((record, index) => equal(record, records[index], "delivery does not copy or rewrite records"));
    }
    const pending = Promise.resolve(marker);
    equal(deliverDiagnosticRecord(records[0]!, () => pending), pending, "wrappers retain the exact returned promise");
    let called = false, finish: (() => void) | undefined;
    const unsettled = new Promise<void>(resolve => { finish = resolve; });
    deliverDiagnosticRecords(records.slice(0, 2), record => { if (record === records[0]) return unsettled; called = true; });
    equal(called, true, "later records are attempted without waiting for earlier completion");
    finish!();
    deliverDiagnosticRecords([], () => { throw new Error("empty list must not invoke receiver"); });
    await new Promise<void>(resolve => setImmediate(resolve));
    equal(shadowReads, 0); equal(thenableCalls, records.length); deepEqual(unhandled, []);
  } finally { process.off("unhandledRejection", uncaught); }
  console.log("Shared diagnostic delivery: order, identity, no wait/retry and receiver failure isolation passed.");
}
void main().catch(error => { console.error(error); process.exitCode = 1; });
