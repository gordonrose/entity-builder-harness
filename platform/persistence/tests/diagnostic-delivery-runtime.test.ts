import { deepEqual, equal } from "node:assert/strict";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { withDiagnosticDeliverySuppressed } from "../../../packages/core/tests/diagnostic-delivery-fixture";
import { persistenceBoundaryDiagnosticRecord, observePlatformPersistenceDiagnostic, resolvePlatformPersistenceDiagnosticOptions, capturePlatformPersistenceDiagnostic } from "../src/index";
import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";

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
const external = defineDiagnostic({ code: "fixture.selected-source", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {} } } as const);
const made = createDiagnosticRecord(external, {}); if (!made.ok) throw new Error("Invalid fixture.");
const reports: DiagnosticRecord[] = [];
const configured = { diagnosticDefinitions: [external], onDiagnostic: (record: DiagnosticRecord) => reports.push(record) };
observePlatformPersistenceDiagnostic(configured, made.value);
deepEqual(reports, [made.value], "explicitly selected non-persistence evidence remains supported");
reports.length = 0;
const processing = capturePlatformPersistenceDiagnostic(() => undefined);
const source = { diagnosticRecord: made.value, relatedDiagnosticRecords: Array.from({ length: 8 }, () => made.value) };
deepEqual(observePlatformPersistenceDiagnostic(configured, processing, source), source);
deepEqual(reports, [processing, ...Array.from({ length: 9 }, () => made.value)]);
reports.length = 0;
const inaccessible = Object.defineProperty({ relatedDiagnosticRecords: [record] }, "diagnosticRecord", { get() { throw new Error("PRIVATE-CANARY"); } });
observePlatformPersistenceDiagnostic(configured, record, inaccessible);
deepEqual(reports, [record, record, { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason: "evidence-inaccessible" } }]);
console.log("Persistence shared delivery wiring, callback receiver/return identity and opt-out passed.");
