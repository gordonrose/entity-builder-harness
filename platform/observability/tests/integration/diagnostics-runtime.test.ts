import { deepEqual, equal, throws } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";
import type { Logger, LogRecord } from "@kanbien/core/logging";
import { createPlatformDiagnosticReporter, createPlatformSafeLogger, reportPlatformDiagnostic } from "../../src/index";
import { withDiagnosticDeliverySuppressed } from "../../../../packages/core/tests/diagnostics/helpers/diagnostic-delivery-fixture";
import { bindPlatformDiagnosticContext } from '@kanbien/platform-contracts';

const definition = defineDiagnostic({ code: "fixture.config-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { reason: { type: "enum", values: ["missing"] } } },
} as const);
const records: LogRecord[] = [];
const reporter = createPlatformDiagnosticReporter({ catalogs: [{ owner: "fixture", definitions: [definition] }],
  logger: { write: (record) => records.push(record) }, clock: { now: () => new Date("2026-10-27T00:00:00.000Z") } });
const record = createDiagnosticRecord(definition, { reason: "missing" });
if (!record.ok) throw new Error("fixture-invalid");
const checkedRecord = record.value;
const context = { capability: "fixture", operation: "start", stage: "startup" } as const;
withDiagnosticDeliverySuppressed(attempted => {
  let delivered = 0;
  reportPlatformDiagnostic({ report() { delivered++; return { status: "written" }; } }, checkedRecord, context);
  equal(delivered, 0, "actual optional reporter wrapper delegates to Core delivery");
  deepEqual(attempted, [checkedRecord]);
});
const receiver = { report(value: typeof checkedRecord, selectedContext: typeof context) {
  equal(this, receiver); equal(value, checkedRecord); equal(selectedContext, context); return { status: "written" as const };
} };
reportPlatformDiagnostic(receiver, checkedRecord, context);
const bound = bindPlatformDiagnosticContext(context, [definition]);
const evidence = bound.select(checkedRecord);
if (!evidence) throw new Error('fixture-context-invalid');
deepEqual(reporter.report(evidence.record, evidence.context), { status: 'written' });
deepEqual(records.pop()?.fields?.['diagnostic'], checkedRecord);
equal(bound.select({ ...checkedRecord, code: 'fixture.another-operation' }), undefined);
throws(() => createPlatformDiagnosticReporter({ catalogs: [{ owner: "fixture", definitions: [definition] }, { owner: "fixture", definitions: [definition] }],
  logger: { write() { throw new Error("Must reject before writing."); } }, clock: { now: () => new Date() } }), (error: unknown) => {
  equal(error instanceof TypeError, true);
  equal((error as Error).message, "PLATFORM_DIAGNOSTIC_CATALOG_INVALID");
  deepEqual((error as { diagnosticRecord?: unknown }).diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "platform-contracts.registration-rejected", definitionVersion: 1,
    detail: { registration: "diagnostic-catalog", field: "owner", condition: "duplicate-owner", phase: "conflicts", effect: "rejected" } });
  return true;
});
deepEqual(reporter.report(record.value, { ...context, stage: "runtime" }), { status: "written" });
equal(records.pop()?.fields?.["stage"], "runtime");
deepEqual(reporter.report(record.value, { ...context, stage: "synthetic-invalid-stage" } as never), { status: "rejected" });
deepEqual(reporter.report(record.value, context), { status: "written" });
equal(records.length, 1);
equal(records[0]?.message, "platform.diagnostic.observed");
deepEqual(reporter.report({ ...record.value, detail: { reason: "password=synthetic-canary" } }, context), { status: "rejected" });
deepEqual(reporter.report(record.value, { ...context, raw: "synthetic-canary" } as never), { status: "rejected" });
equal(records.length, 1);
const unavailable = createPlatformDiagnosticReporter({ catalogs: [{ owner: "fixture", definitions: [definition] }],
  logger: { write: () => { throw new Error("synthetic-canary"); } }, clock: { now: () => new Date() } });
deepEqual(unavailable.report(record.value, context), { status: "unavailable" });
const wrappedUnavailable = createPlatformDiagnosticReporter({ catalogs: [{ owner: "fixture", definitions: [definition] }],
  logger: createPlatformSafeLogger({ write: () => { throw new Error("synthetic-canary"); } }), clock: { now: () => new Date() } });
deepEqual(wrappedUnavailable.report(record.value, context), { status: "unavailable" });
let accessed = false;
const accessorRecord = Object.defineProperty({}, "code", { get() { accessed = true; return "fixture.config-invalid"; } });
deepEqual(reporter.report(accessorRecord as never, context), { status: "rejected" });
equal(accessed, false);
const nested = defineDiagnostic({ code: "fixture.settings-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { issues: { type: "array", minItems: 1, maxItems: 32,
    items: { type: "object", properties: { setting: { type: "enum", values: ["connection.port"] }, reason: { type: "enum", values: ["missing"] } } } } } },
} as const);
const manyIssues = createDiagnosticRecord(nested, { issues: Array.from({ length: 32 }, () => ({ setting: "connection.port" as const, reason: "missing" as const })) });
if (!manyIssues.ok) throw new Error("fixture-invalid");
const wrapped: LogRecord[] = [];
const guarded = createPlatformDiagnosticReporter({ catalogs: [{ owner: "fixture", definitions: [nested] }],
  logger: createPlatformSafeLogger({ write: (value) => wrapped.push(value) }), clock: { now: () => new Date() } });
deepEqual(guarded.report(manyIssues.value, context), { status: "written" });
deepEqual(wrapped[0]?.fields?.["diagnostic"], manyIssues.value, "approved nested diagnostic detail must survive the generic safe logger without depth/item truncation");
const forbidden: LogRecord[] = [];
const policyConflict = createPlatformDiagnosticReporter({ catalogs: [{ owner: "fixture", definitions: [nested] }],
  logger: createPlatformSafeLogger({ write: (value) => forbidden.push(value) }, { additionalSensitiveKeys: ["reason"] }), clock: { now: () => new Date() } });
deepEqual(policyConflict.report(manyIssues.value, context), { status: "unavailable" }, "a stronger sink policy must block delivery instead of silently altering diagnostic meaning");
equal(forbidden.length, 0);
const spoofed: LogRecord[] = [];
createPlatformSafeLogger({ write: (value) => spoofed.push(value) }).write({ ...wrapped[0]!, fields: { diagnostic: manyIssues.value } });
equal((spoofed[0]?.fields?.["diagnostic"] as { detail: { issues: unknown[] } }).detail.issues.length, 20, "copying the message or fields must not spoof reporter provenance or bypass generic normalization");
console.log("Validated diagnostic emission and sink failure isolation passed.");

async function asyncSinkCoverage(): Promise<void> {
  const unhandled: unknown[] = [];
  const onUnhandled = (reason: unknown): void => { unhandled.push(reason); };
  process.on("unhandledRejection", onUnhandled);
  try {
    let shadowReads = 0;
    for (const wrapped of [false, true]) for (const mode of ["resolved", "rejected", "shadowed", "thenable", "then-getter", "numeric", "object"] as const) {
      let calls = 0;
      const inner: Logger = { write() {
        equal(this, inner); calls++;
        if (mode === "numeric") return 3;
        if (mode === "object") return { accepted: true };
        if (mode === "then-getter") return Object.defineProperty({}, "then", { get() { throw new Error("private-sink-canary"); } });
        if (mode === "thenable") return { then(_resolve: unknown, reject: (reason: unknown) => void) { reject(new Error("private-sink-canary")); } };
        const pending = mode === "resolved" ? Promise.resolve() : Promise.reject(new Error("private-sink-canary"));
        if (mode === "shadowed") Object.defineProperty(pending, "then", { get() { shadowReads++; throw new Error("must bypass own then"); } });
        return pending;
      } };
      let recursiveReports = 0;
      const selectedLogger = wrapped ? createPlatformSafeLogger(inner, {}, { context, reporter: { report() { recursiveReports++; return { status: "written" }; } } }) : inner;
      const selectedReporter = createPlatformDiagnosticReporter({ catalogs: [{ owner: "fixture", definitions: [definition] }], logger: selectedLogger, clock: { now: () => new Date() } });
      deepEqual(selectedReporter.report(checkedRecord, context), { status: mode === "numeric" || mode === "object" ? "written" : "unavailable" });
      equal(calls, 1); equal(recursiveReports, 0, "the diagnostic sink never recursively diagnoses its own failure");
    }
    await new Promise<void>((resolve) => setImmediate(resolve));
    equal(shadowReads, 0); deepEqual(unhandled, []);
  } finally { process.off("unhandledRejection", onUnhandled); }
}
void asyncSinkCoverage().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
