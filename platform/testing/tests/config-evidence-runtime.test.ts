import { deepEqual, equal, throws } from "node:assert/strict";
import { configError, requiredConfigValue, type ConfigError, type ConfigSchema } from "@kanbien/core/config";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { validatePlatformTestConfigSchemas, createPlatformTestConfigSource } from "../src/index";
const canary = "configuration-private-canary@example.invalid";
const definition = defineDiagnostic({ code: "fixture.config-rejected", version: 1,
  classification: { failureKind: "configuration", failureSource: "app", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { reason: { type: "enum", values: ["required"] } } },
});
const created = createDiagnosticRecord(definition, { reason: "required" });
if (!created.ok) throw new Error("Fixture invalid");
const selectedRecord = created.value;
const issues = [{ path: [canary], code: "FIXTURE_REJECTED", defaultMessage: canary }] as const;
const reject = (error: ConfigError): ConfigSchema<unknown> => ({ parse() { return { ok: false, error }; } });
function result(error: ConfigError, selected = false) {
  const checked = validatePlatformTestConfigSchemas([reject(error)], createPlatformTestConfigSource(), selected ? [definition] : []);
  equal(checked.ok, false); if (checked.ok) throw new Error("Expected failure");
  const { diagnosticRecord: _primary, relatedDiagnosticRecords: _related, ...legacy } = checked.error;
  deepEqual(legacy, { code: "PLATFORM_TEST_INVALID_CONFIG", defaultMessage: "A platform test config schema rejected the supplied config source.", details: { schemaIndex: 0, configCode: "CONFIG_INVALID" } });
  equal((JSON.stringify(checked.error.diagnosticRecord) ?? "").includes(canary), false);
  equal((JSON.stringify(checked.error.relatedDiagnosticRecords) ?? "").includes(canary), false);
  return checked.error;
}
const error = configError("CONFIG_INVALID", issues, { diagnosticRecord: selectedRecord, relatedDiagnosticRecords: [selectedRecord] });
deepEqual(result(error, true).diagnosticRecord, selectedRecord);
deepEqual(result(error, true).relatedDiagnosticRecords, [selectedRecord]);
equal(result(error).diagnosticRecord, undefined);
deepEqual(result(error).relatedDiagnosticRecords, []);
for (const bad of [null, {}, { ...selectedRecord, code: "unknown.code" }, { ...selectedRecord, definitionVersion: 99 }, { ...selectedRecord, detail: { reason: canary } }]) {
  const checked = result(configError("CONFIG_INVALID", issues, { diagnosticRecord: bad as DiagnosticRecord, relatedDiagnosticRecords: [selectedRecord] }), true);
  equal(checked.diagnosticRecord, undefined);
  deepEqual(checked.relatedDiagnosticRecords, [selectedRecord]);
}
for (const bad of [Array(9).fill(selectedRecord), Array(1), Object.assign([selectedRecord], { extra: canary })]) {
  equal(result(configError("CONFIG_INVALID", issues, { diagnosticRecord: selectedRecord, relatedDiagnosticRecords: bad as readonly DiagnosticRecord[] }), true).relatedDiagnosticRecords, undefined);
}
equal(result(configError("CONFIG_INVALID", issues, { relatedDiagnosticRecords: Array(8).fill(selectedRecord) }), true).relatedDiagnosticRecords?.length, 8);
let reads = 0;
const accessor = Object.defineProperty({ code: "CONFIG_INVALID", issues }, "diagnosticRecord", { enumerable: true, get() { reads++; throw new Error(canary); } }) as ConfigError;
equal(result(accessor, true).diagnosticRecord, undefined);
equal(reads, 0);
const badRecord = new Proxy({}, { getPrototypeOf() { throw new Error(canary); } });
equal(result(configError("CONFIG_INVALID", issues, { diagnosticRecord: badRecord as DiagnosticRecord }), true).diagnosticRecord, undefined);

const missing = validatePlatformTestConfigSchemas([{ parse(source) { return requiredConfigValue(source, canary); } }]);
equal(missing.ok, false);
if (missing.ok) throw new Error("Expected missing primitive");
equal(missing.error.diagnosticRecord?.code, "core.config.primitive-invalid");
equal(missing.error.diagnosticRecord?.definitionVersion, 1);
deepEqual(missing.error.diagnosticRecord?.detail, { field: "value", reader: "required", reason: "missing" });
equal(JSON.stringify(missing.error).includes(canary), false);
let firstCalls = 0, secondCalls = 0, thirdCalls = 0;
const source = createPlatformTestConfigSource();
const schema: ConfigSchema<unknown> = { parse(supplied) { equal(this, schema); equal(supplied, source); secondCalls++; return { ok: false, error }; } };
const checked = validatePlatformTestConfigSchemas([{ parse() { firstCalls++; return { ok: true, value: 1 }; } }, schema, { parse() { thirdCalls++; return { ok: true, value: 3 }; } }], source, [definition]);
equal(checked.ok, false); equal(firstCalls, 1); equal(secondCalls, 1); equal(thirdCalls, 0);
if (checked.ok) throw new Error("Expected second failure");
equal(checked.error.details?.["schemaIndex"], 1);
let errorReads = 0;
const accessorResult = { ok: false as const, get error() { errorReads++; return error; } };
equal(validatePlatformTestConfigSchemas([{ parse() { return accessorResult; } }], source, [definition]).ok, false);
equal(errorReads, 1, "Diagnostic selection must reuse the error from the existing result read");
const thrown = new Error(canary);
throws(() => validatePlatformTestConfigSchemas([{ parse() { throw thrown; } }]), (value) => value === thrown);
const uninspectableDefinitions = new Proxy([], { get() { throw thrown; } }) as readonly typeof definition[];
const rejectedWithUnavailableSelection = validatePlatformTestConfigSchemas([reject(error)], source, uninspectableDefinitions);
equal(rejectedWithUnavailableSelection.ok, false);
if (rejectedWithUnavailableSelection.ok) throw new Error("Expected original rejection.");
equal(rejectedWithUnavailableSelection.error.code, "PLATFORM_TEST_INVALID_CONFIG");
equal(rejectedWithUnavailableSelection.error.diagnosticRecord, undefined);

// Optional selection failure must not erase the reason already established by Core.
const coreFailure = requiredConfigValue(source, canary);
if (coreFailure.ok) throw new Error("Expected missing configuration.");
const coreRecord = coreFailure.error.diagnosticRecord!;
const coreCompanions = Array.from({ length: 8 }, () => coreRecord);
const failureWithCompanions = { ...coreFailure.error, relatedDiagnosticRecords: coreCompanions };
let rejectedCalls = 0, skippedCalls = 0;
const retained = validatePlatformTestConfigSchemas([
  { parse(supplied) { equal(supplied, source); return { ok: true, value: 443 }; } },
  { parse(supplied) { equal(supplied, source); rejectedCalls++; return { ok: false, error: failureWithCompanions }; } },
  { parse() { skippedCalls++; return { ok: true, value: 1 }; } },
], source, uninspectableDefinitions);
equal(retained.ok, false);
if (retained.ok) throw new Error("Expected original rejection.");
equal(rejectedCalls, 1); equal(skippedCalls, 0);
deepEqual(retained.error.details, { schemaIndex: 1, configCode: "CONFIG_MISSING" });
deepEqual(retained.error.diagnosticRecord, coreRecord);
deepEqual(retained.error.diagnosticRecord?.detail, { field: "value", reader: "required", reason: "missing" });
deepEqual(retained.error.relatedDiagnosticRecords, coreCompanions);
equal(JSON.stringify(retained.error).includes(canary), false);
