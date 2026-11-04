import { deepEqual, equal } from "node:assert/strict";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { withDiagnosticDeliverySuppressed } from "../../../packages/core/tests/diagnostic-delivery-fixture";
import { persistenceBoundaryDiagnosticRecord, observePlatformPersistenceDiagnostic, resolvePlatformPersistenceDiagnosticOptions } from "../src/index";

const record = persistenceBoundaryDiagnosticRecord({ operation: "transaction", phase: "completion", boundary: "release", condition: "threw", effect: "commit-completed" });
withDiagnosticDeliverySuppressed(attempted => {
  let delivered = 0;
  const options = { onDiagnostic() { delivered++; } };
  deepEqual(observePlatformPersistenceDiagnostic(options, record, { diagnosticRecord: record }), { diagnosticRecord: record });
  resolvePlatformPersistenceDiagnosticOptions(undefined, options).onDiagnostic?.(record);
  equal(delivered, 0, "observer and option wrapper both delegate to Core delivery");
  deepEqual(attempted, [record, record, record]);
});
const returned = Object.freeze({ accepted: true });
const owner = { onDiagnostic(value: DiagnosticRecord) { equal(this, owner); equal(value, record); return returned; } };
equal(resolvePlatformPersistenceDiagnosticOptions(undefined, owner).onDiagnostic?.(record), returned);
observePlatformPersistenceDiagnostic(undefined, record);
console.log("Persistence shared delivery wiring, callback receiver/return identity and opt-out passed.");
