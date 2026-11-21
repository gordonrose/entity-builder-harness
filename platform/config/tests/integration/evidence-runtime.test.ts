import { deepEqual, equal, throws } from "node:assert/strict";
import { configError, recordConfigSource, stringConfigValue, type ConfigSchema } from "@kanbien/core/config";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { validationIssue } from "@kanbien/core/validation";
import { validatePlatformConfigSchemas } from "../../src/index";

const selected = defineDiagnostic({ code: "fixture.configuration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "app", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { field: { type: "enum", values: ["app-name"] }, reason: { type: "enum", values: ["missing"] } } },
} as const);
const checked = createDiagnosticRecord(selected, { field: "app-name", reason: "missing" });
if (!checked.ok) throw new Error("Expected fixed diagnostic.");
const record = checked.value;
const issue = validationIssue({ code: "FIXTURE_CONFIGURATION_INVALID", defaultMessage: "Fixture invalid.", path: ["synthetic-private-canary"], params: { secret: "synthetic-private-canary" } });
const failure = configError("CONFIG_MISSING", [issue], { diagnosticRecord: record, relatedDiagnosticRecords: Array.from({ length: 8 }, () => record) });
let calls = 0;
const schema: ConfigSchema<never> = { parse(source) { equal(this, schema); equal(source, input.source); calls++; return { ok: false, error: failure }; } };
const observed: DiagnosticRecord[] = [];
const input = { source: recordConfigSource({}), schemas: [schema, { parse() { throw new Error("Must retain first failure."); } }], diagnosticDefinitions: [selected], onDiagnostic: (value: DiagnosticRecord) => { observed.push(value); } };
const result = validatePlatformConfigSchemas(input);
equal(calls, 1);
equal(result.ok, false);
if (result.ok) throw new Error("Expected rejection.");
deepEqual(result.error.diagnosticRecord, record);
equal(result.error.relatedDiagnosticRecords?.length, 8, "schema location must not displace valid upstream companions");
equal(observed.length, 10);
deepEqual(observed[0], { schema: "core/diagnostic-record/v1", code: "platform-config.schema-rejected", definitionVersion: 1, detail: { schemaIndex: 0, reason: "missing" } });
deepEqual(observed.slice(1), Array.from({ length: 9 }, () => record));
equal(JSON.stringify(observed).includes("synthetic-private-canary"), false);
deepEqual(result.error.details, { schemaIndex: 0, configCode: "CONFIG_MISSING", issues: [{ path: ["synthetic-private-canary"], code: "FIXTURE_CONFIGURATION_INVALID", defaultMessage: "Fixture invalid." }] });
const unselected = validatePlatformConfigSchemas({ source: input.source, schemas: input.schemas, diagnosticDefinitions: [] });
if (unselected.ok) throw new Error("Expected rejection.");
equal(unselected.error.diagnosticRecord?.code, "platform-config.schema-rejected");
equal(unselected.error.relatedDiagnosticRecords?.length, 0);
let reads = 0;
const primitive = validatePlatformConfigSchemas({ source: { get() { reads++; return undefined; } }, schemas: [{ parse: (source) => stringConfigValue(source, "synthetic-private-canary") }] });
equal(reads, 1);
if (primitive.ok) throw new Error("Expected missing.");
deepEqual(primitive.error.diagnosticRecord?.detail, { field: "value", reader: "string", reason: "missing" });

for (const thrown of [new Error("synthetic-private-canary"), "synthetic-private-canary", Object.freeze({ secret: "synthetic-private-canary" })]) {
  const reports: DiagnosticRecord[] = [];
  throws(() => validatePlatformConfigSchemas({ source: recordConfigSource({}), schemas: [{ parse() { throw thrown; } }], onDiagnostic: (value) => reports.push(value) }), (value) => value === thrown);
  deepEqual(reports, [{ schema: "core/diagnostic-record/v1", code: "platform-config.schema-boundary-threw", definitionVersion: 1,
    detail: { schemaIndex: 0, phase: "parse", reason: "boundary-threw", effect: "result-not-returned" } }]);
}
const projectionFailure = new Error("synthetic-private-canary");
const reports: DiagnosticRecord[] = [];
throws(() => validatePlatformConfigSchemas({ source: recordConfigSource({}), schemas: [{ parse: () => ({ get ok() { throw projectionFailure; } }) as never }], onDiagnostic: (value) => reports.push(value) }), (value) => value === projectionFailure);
deepEqual(reports[0]?.detail, { schemaIndex: 0, phase: "projection", reason: "boundary-threw", effect: "result-not-returned" });
const large = validatePlatformConfigSchemas({ source: recordConfigSource({}), schemas: [...Array.from({ length: 65_536 }, (): ConfigSchema<null> => ({ parse: () => ({ ok: true, value: null }) })), { parse: () => ({ ok: false, error: configError("CONFIG_MISSING", [issue]) }) }] });
if (large.ok) throw new Error("Expected large-index rejection.");
deepEqual(large.error.diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "platform-config.schema-rejected", definitionVersion: 2, detail: { schemaIndex: 65_536, reason: "missing" } });

// Actual schema callers retain their precise source even if the positional
// diagnostic cannot be constructed. This is separate from normal-reason proof.
const builderModule = require("../../../../packages/core/src/diagnostics/record") as { createDiagnosticRecord: typeof createDiagnosticRecord };
const originalBuilder = builderModule.createDiagnosticRecord;
for (const mode of ["throws", "rejected", "malformed"] as const) {
  const reports: DiagnosticRecord[] = [];
  builderModule.createDiagnosticRecord = ((definition: typeof selected, detail: never) => {
    if (!definition.code.startsWith("platform-config.")) return originalBuilder(definition, detail);
    if (mode === "throws") throw new Error("synthetic-private-canary");
    if (mode === "rejected") return { ok: false, error: {} };
    return { ok: true, value: { schema: "core/diagnostic-record/v1", code: definition.code, definitionVersion: definition.version, detail: { private: "synthetic-private-canary" } } };
  }) as typeof createDiagnosticRecord;
  try {
    const failed = validatePlatformConfigSchemas({ ...input, onDiagnostic: record => reports.push(record) });
    if (failed.ok) throw new Error("Expected original rejection.");
    deepEqual(failed.error.diagnosticRecord, record);
    deepEqual(failed.error.relatedDiagnosticRecords, Array.from({ length: 8 }, () => record));
    const expected = { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1,
      detail: { reason: mode === "throws" ? "construction-threw" : mode === "rejected" ? "construction-rejected" : "evidence-rejected" } };
    deepEqual(reports, [expected, ...Array.from({ length: 9 }, () => record)]);
    reports.length = 0;
    throws(() => validatePlatformConfigSchemas({ source: input.source, schemas: [{ parse() { throw projectionFailure; } }], onDiagnostic: value => reports.push(value) }), value => value === projectionFailure);
    deepEqual(reports, [expected]);
    const noSource = validatePlatformConfigSchemas({ source: input.source, schemas: [{ parse: () => ({ ok: false, error: configError("CONFIG_MISSING", [issue]) }) }] });
    if (noSource.ok) throw new Error("Expected original rejection without upstream evidence.");
    deepEqual(noSource.error.diagnosticRecord, expected);
  } finally { builderModule.createDiagnosticRecord = originalBuilder; }
}
const selectionReports: DiagnosticRecord[] = [];
const builtinFailure = stringConfigValue(recordConfigSource({}), "PRIVATE_NAME");
if (builtinFailure.ok) throw new Error("Expected missing input.");
const builtinResult = validatePlatformConfigSchemas({ source: input.source, schemas: [{ parse: () => builtinFailure }],
  get diagnosticDefinitions(): never { throw projectionFailure; }, onDiagnostic: record => selectionReports.push(record) });
if (builtinResult.ok) throw new Error("Expected original missing-input result.");
deepEqual(builtinResult.error.diagnosticRecord?.detail, { field: "value", reader: "string", reason: "missing" });
deepEqual(selectionReports.at(-1)?.detail, { reason: "definition-selection-failed" });
equal(JSON.stringify(selectionReports).includes("PRIVATE_NAME"), false);

async function isolation() {
  const unhandled: unknown[] = [];
  const listener = (value: unknown) => { unhandled.push(value); };
  process.on("unhandledRejection", listener);
  try {
    for (const onDiagnostic of [() => { throw new Error("synthetic-private-canary"); }, () => Promise.reject("synthetic-private-canary"), () => ({ then(_ok: unknown, reject: (value: unknown) => void) { reject("synthetic-private-canary"); } })]) {
      equal(validatePlatformConfigSchemas({ source: recordConfigSource({}), schemas: [{ parse: () => ({ ok: false, error: failure }) }], diagnosticDefinitions: [selected], onDiagnostic }).ok, false);
    }
    await new Promise<void>((resolve) => setImmediate(resolve));
    deepEqual(unhandled, []);
  } finally { process.removeListener("unhandledRejection", listener); }
}
void isolation().then(() => console.log("Platform config evidence passed.")).catch((error) => { console.error(error); process.exitCode = 1; });
