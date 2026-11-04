import { deepEqual, equal, notEqual, throws } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, parseDiagnosticRecord, parseRelatedDiagnosticRecords, selectDiagnosticEvidence, diagnosticRelatedRecordLimit, type DiagnosticRecord } from "../src/diagnostics/index";
import { configReasonNames, configIssueReasons, configValueIssueReasons, parseConfigJsonObject, recordConfigSource, validateConfigSettings } from "../src/config/index";
import { persistenceError } from "../src/persistence/index";
import { auditRecordError, type CoreAuditErrorEvidence } from "../src/audit/index";
import { fileError } from "../src/files/index";
import { i18nError } from "../src/i18n/index";
import { localizationError } from "../src/localization/index";
import { eventPublishError } from "../src/events/index";
import { queueError } from "../src/queues/index";
import type { CoreError } from "../src/shared/index";

type CompanionFactory = (input: { readonly code: never; readonly defaultMessage: string; readonly diagnosticRecord?: DiagnosticRecord }, evidence?: CoreAuditErrorEvidence) => CoreError;
const companionFactories: readonly CompanionFactory[] = [auditRecordError, eventPublishError, fileError];

const definition = defineDiagnostic({ code: "configuration.invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { issues: { type: "array", minItems: 1, maxItems: 8,
    items: { type: "object", properties: { setting: { type: "enum", values: ["database.port", "database.host"] }, reason: { type: "enum", values: ["missing", "out-of-range"] } } } } } },
});
const result = createDiagnosticRecord(definition, { issues: [{ setting: "database.port", reason: "out-of-range" }] });
if (!result.ok) throw new Error("fixture-invalid");
deepEqual(parseRelatedDiagnosticRecords([definition], [result.value]), { ok: true, value: [result.value] });
const emptyRelated = parseRelatedDiagnosticRecords([definition], []);
if (emptyRelated.ok) equal(Object.isFrozen(emptyRelated.value), true);
for (const hostile of [Array(1), Array(diagnosticRelatedRecordLimit + 1).fill(result.value), [ { ...result.value, code: "unknown" } ],
  Object.defineProperty([], "0", { get() { throw new Error("synthetic-secret-canary"); } }), new Proxy([], { get() { throw new Error("synthetic-secret-canary"); } })]) {
  equal(parseRelatedDiagnosticRecords([definition], hostile).ok, false);
}
equal(result.ok, true);
if (result.ok) {
  deepEqual(parseDiagnosticRecord(definition, result.value), result);
  equal(parseDiagnosticRecord(definition, { ...result.value, rawError: "synthetic-secret" }).ok, false);
  equal(parseDiagnosticRecord(definition, { ...result.value, definitionVersion: 2 }).ok, false);
  equal(parseDiagnosticRecord(definition, { ...result.value, detail: { issues: [{ setting: "synthetic-secret", reason: "missing" }] } }).ok, false);
  const input = { code: "fixture" as never, defaultMessage: "Fixed test error.", diagnosticRecord: result.value };
  for (const error of [persistenceError(input), auditRecordError(input), fileError(input), i18nError(input), localizationError(input), eventPublishError(input), queueError(input)]) {
    equal(error.diagnosticRecord, result.value, "existing module helpers must preserve the independently validated record");
  }
  const companions = Array.from({ length: 8 }, () => result.value);
  const evidence = { relatedDiagnosticRecords: companions, relatedDiagnosticDefinitions: [definition] };
  for (const factory of companionFactories) {
    const enriched = factory(input, evidence);
    equal(enriched.diagnosticRecord, result.value);
    deepEqual(enriched.relatedDiagnosticRecords, companions);
    equal(Object.isFrozen(enriched.relatedDiagnosticRecords), true);
    notEqual(enriched.relatedDiagnosticRecords, companions);
    const unsupportedPrimary: DiagnosticRecord = { ...result.value, code: "custom.primary-not-selected" };
    equal(factory({ ...input, diagnosticRecord: unsupportedPrimary }, evidence).diagnosticRecord, unsupportedPrimary,
      "new companion selection does not narrow the legacy primary pass-through");
    let evidenceReads = 0;
    const accessorRecord = Object.defineProperty({ ...result.value }, "code", { get() { evidenceReads++; throw new Error("private-companion-canary"); } });
    for (const options of [
      { ...evidence, relatedDiagnosticRecords: [...companions, result.value] },
      { ...evidence, relatedDiagnosticRecords: [accessorRecord] },
      { relatedDiagnosticRecords: companions },
      Object.defineProperty({}, "relatedDiagnosticRecords", { get() { evidenceReads++; throw new Error("private-companion-canary"); } }),
      Object.defineProperty({ relatedDiagnosticRecords: companions }, "relatedDiagnosticDefinitions", { get() { evidenceReads++; throw new Error("private-companion-canary"); } }),
    ]) {
      const rejected = factory(input, options as never); // Deliberately malformed runtime evidence, not an admitted typed declaration.
      equal(rejected.diagnosticRecord, result.value);
      equal(rejected.relatedDiagnosticRecords, undefined);
      equal(JSON.stringify(rejected).includes("private-companion-canary"), false);
    }
    equal(evidenceReads, 0, "optional companion input cannot execute accessors or replace the legacy error");
  }
}
let accessed = false;
equal(createDiagnosticRecord(definition, Object.defineProperty({}, "issues", { get() { accessed = true; throw new Error("synthetic-secret"); } }) as never).ok, false);
equal(accessed, false);
const enumValues = Object.defineProperty(["missing"], "0", { get() { accessed = true; throw new Error("synthetic-secret"); } });
throws(() => defineDiagnostic({ ...definition, detail: { type: "enum", values: enumValues } }), /DIAGNOSTIC_DEFINITION_INVALID/);
equal(accessed, false, "definition validation must not evaluate enum accessors");
equal(createDiagnosticRecord(definition, { issues: Array(100).fill({ setting: "database.host", reason: "missing" }) } as never).ok, false);
throws(() => defineDiagnostic({ ...definition, detail: { type: "object", properties: JSON.parse('{"__proto__":{"type":"boolean"}}') } }), /DIAGNOSTIC_DEFINITION_INVALID/);
const settings = [{ setting: "database.host", source: "HOST", rule: { kind: "text" } },
  { setting: "database.port", source: "PORT", rule: { kind: "integer", minimum: 1, maximum: 65535 } }] as const;
for (const [raw, reason] of [[undefined, "missing"], ["", "blank"], [" 1", "surrounding-whitespace"], ["5e3", "invalid-integer"], ["65536", "out-of-range"], [null, "wrong-type"]] as const) {
  const checked = validateConfigSettings(recordConfigSource({ HOST: "synthetic-private-host", PORT: raw }), settings);
  equal(checked.ok, false);
  if (!checked.ok) { deepEqual(checked.error.issues, [{ setting: "database.port", reason }]); equal(JSON.stringify(checked.error).includes("synthetic-private-host"), false); }
}
deepEqual(validateConfigSettings(recordConfigSource({}), settings), { ok: false, error: { code: "CONFIGURATION_INVALID", issues: [
  { setting: "database.host", reason: "missing" }, { setting: "database.port", reason: "missing" },
] } });
console.log("Core closed diagnostic records and precise configuration validation passed.");

for (const [value, reason] of [[undefined, "missing"], [null, "wrong-type"], [1, "wrong-type"], [{}, "wrong-type"], ["", "blank"], [" \n\t", "blank"],
  ['{"synthetic-private-json":', "invalid-json"], ['"synthetic-private-json"', "wrong-shape"], ["null", "wrong-shape"], ["[]", "wrong-shape"], ["true", "wrong-shape"], ["42", "wrong-shape"]] as const) {
  const parsed = parseConfigJsonObject(value);
  deepEqual(parsed, { ok: false, error: { reason } });
  equal(JSON.stringify(parsed).includes("synthetic-private-json"), false);
}
deepEqual(parseConfigJsonObject(' \n {"password":"  synthetic-private-json  ","extra":true} \t'), { ok: true, value: { password: "  synthetic-private-json  ", extra: true } });
deepEqual(configIssueReasons, ["missing", "blank", "surrounding-whitespace", "wrong-type", "invalid-format", "invalid-integer", "out-of-range", "inconsistent-settings"], "retained diagnostic definitions keep their exact reason enum");
deepEqual(configValueIssueReasons, ["missing", "blank", "surrounding-whitespace", "wrong-type", "invalid-format", "invalid-integer", "out-of-range", "inconsistent-settings", "invalid-json", "wrong-shape", "empty", "forbidden-character"]);
deepEqual(Object.values(configReasonNames), [...configValueIssueReasons, "unsupported-value"], "canonical reasons may grow without widening retained compatibility lists");
equal(Object.isFrozen(configReasonNames), true);
throws(() => Object.assign(configReasonNames, { missing: "changed" }), TypeError);
const grownReasonNames = { ...configReasonNames, future: "fixture-future-reason" } as const;
const reasonDefinition = (version: number, reasons: readonly string[]) => defineDiagnostic({
  code: "fixture.reason-stability", version, classification: definition.classification,
  detail: { type: "object", properties: { reason: { type: "enum", values: reasons } } },
} as const);
const priorReasonDefinition = reasonDefinition(1, [configReasonNames.missing]);
const nextReasonDefinition = reasonDefinition(2, [configReasonNames.missing, grownReasonNames.future]);
const retainedReasonLiteral = { schema: "core/diagnostic-record/v1", code: "fixture.reason-stability", definitionVersion: 1, detail: { reason: "missing" } };
equal(parseDiagnosticRecord(priorReasonDefinition, retainedReasonLiteral).ok, true);
equal(createDiagnosticRecord(priorReasonDefinition, { reason: grownReasonNames.future }).ok, false);
equal(createDiagnosticRecord(nextReasonDefinition, { reason: grownReasonNames.future }).ok, true);
equal(parseDiagnosticRecord(priorReasonDefinition, { ...retainedReasonLiteral, detail: { reason: grownReasonNames.future } }).ok, false);
equal(parseDiagnosticRecord(priorReasonDefinition, retainedReasonLiteral).ok, true, "growth leaves the retained literal readable");

// Selection is a safe projection of evidence, never an exception traversal.
const selectedLiteral = { schema: "core/diagnostic-record/v1", code: "configuration.invalid", definitionVersion: 1,
  detail: { issues: [{ setting: "database.port", reason: "out-of-range" }] } } as const;
const anotherVersion = defineDiagnostic({ ...definition, version: 2 });
const versionTwo = { ...selectedLiteral, definitionVersion: 2 };
const unselected = { ...selectedLiteral, code: "synthetic.private", detail: { raw: "synthetic-private-canary" } };
const malformed = { ...selectedLiteral, detail: { issues: [{ setting: "synthetic-private-canary", reason: "missing" }] } };
deepEqual(selectDiagnosticEvidence([definition], { diagnosticRecord: selectedLiteral }), { diagnosticRecord: selectedLiteral });
deepEqual(selectDiagnosticEvidence([definition], { diagnosticRecord: versionTwo }), {}, "definition version must be selected explicitly");
deepEqual(selectDiagnosticEvidence([definition, anotherVersion], { diagnosticRecord: versionTwo }), { diagnosticRecord: versionTwo });
deepEqual(selectDiagnosticEvidence([], { diagnosticRecord: selectedLiteral, relatedDiagnosticRecords: [selectedLiteral] }), { relatedDiagnosticRecords: [] });
deepEqual(selectDiagnosticEvidence([definition], { diagnosticRecord: malformed, relatedDiagnosticRecords: [unselected, selectedLiteral, malformed, null, versionTwo, selectedLiteral] }), {
  relatedDiagnosticRecords: [selectedLiteral, selectedLiteral],
}, "malformed primary cannot drop independently valid selected companions or reorder them");
for (const primary of [unselected, malformed, undefined, null, "synthetic-private-canary", new Error("synthetic-private-canary")]) {
  const selected = selectDiagnosticEvidence([definition], { diagnosticRecord: primary, relatedDiagnosticRecords: [selectedLiteral] });
  deepEqual(selected, { relatedDiagnosticRecords: [selectedLiteral] });
  equal(JSON.stringify(selected).includes("synthetic-private-canary"), false);
}
for (const input of [undefined, null, true, 1, "synthetic-private-canary", new Error("synthetic-private-canary")]) deepEqual(selectDiagnosticEvidence([definition], input), {});
const inheritedEvidence = Object.create({ diagnosticRecord: selectedLiteral, relatedDiagnosticRecords: [selectedLiteral] });
deepEqual(selectDiagnosticEvidence([definition], inheritedEvidence), {}, "prototype evidence is not owned evidence");
let sourceGetterReads = 0;
const primaryAccessor = Object.defineProperty({ relatedDiagnosticRecords: [selectedLiteral] }, "diagnosticRecord", { get() { sourceGetterReads++; throw new Error("synthetic-private-canary"); } });
deepEqual(selectDiagnosticEvidence([definition], primaryAccessor), { relatedDiagnosticRecords: [selectedLiteral] });
const companionsAccessor = Object.defineProperty({ diagnosticRecord: selectedLiteral }, "relatedDiagnosticRecords", { get() { sourceGetterReads++; throw new Error("synthetic-private-canary"); } });
deepEqual(selectDiagnosticEvidence([definition], companionsAccessor), { diagnosticRecord: selectedLiteral });
equal(sourceGetterReads, 0);
let nativeReads = 0;
const native = Object.assign(new Error("synthetic-private-canary"), { diagnosticRecord: selectedLiteral, relatedDiagnosticRecords: [selectedLiteral] });
for (const key of ["cause", "message", "stack"]) Object.defineProperty(native, key, { configurable: true, get() { nativeReads++; throw new Error("synthetic-private-canary"); } });
deepEqual(selectDiagnosticEvidence([definition], native), { diagnosticRecord: selectedLiteral, relatedDiagnosticRecords: [selectedLiteral] });
equal(nativeReads, 0);
let exceptionEnumerations = 0, exceptionPrototypeReads = 0, exceptionValueReads = 0;
const opaqueException = new Proxy({ diagnosticRecord: selectedLiteral, relatedDiagnosticRecords: [selectedLiteral] }, {
  ownKeys() { exceptionEnumerations++; throw new Error("synthetic-private-canary"); },
  getPrototypeOf() { exceptionPrototypeReads++; throw new Error("synthetic-private-canary"); },
  get() { exceptionValueReads++; throw new Error("synthetic-private-canary"); },
});
deepEqual(selectDiagnosticEvidence([definition], opaqueException), { diagnosticRecord: selectedLiteral, relatedDiagnosticRecords: [selectedLiteral] });
deepEqual([exceptionEnumerations, exceptionPrototypeReads, exceptionValueReads], [0, 0, 0]);
for (const rejectedField of ["diagnosticRecord", "relatedDiagnosticRecords"]) {
  const independentFields = new Proxy({ diagnosticRecord: selectedLiteral, relatedDiagnosticRecords: [selectedLiteral] }, {
    getOwnPropertyDescriptor(target, key) { if (key === rejectedField) throw new Error("synthetic-private-canary"); return Reflect.getOwnPropertyDescriptor(target, key); },
  });
  deepEqual(selectDiagnosticEvidence([definition], independentFields), rejectedField === "diagnosticRecord" ? { relatedDiagnosticRecords: [selectedLiteral] } : { diagnosticRecord: selectedLiteral });
}
let recordGetterReads = 0;
const codeAccessor = Object.defineProperty({ ...selectedLiteral }, "code", { enumerable: true, get() { recordGetterReads++; return "configuration.invalid"; } });
const detailAccessor = Object.defineProperty({ ...selectedLiteral }, "detail", { enumerable: true, get() { recordGetterReads++; throw new Error("synthetic-private-canary"); } });
const versionAccessor = Object.defineProperty({ ...selectedLiteral }, "definitionVersion", { enumerable: true, get() { recordGetterReads++; return 1; } });
const recordProxy = new Proxy({ ...selectedLiteral }, { ownKeys() { throw new Error("synthetic-private-canary"); } });
deepEqual(selectDiagnosticEvidence([definition], { diagnosticRecord: detailAccessor, relatedDiagnosticRecords: [codeAccessor, detailAccessor, versionAccessor, recordProxy, selectedLiteral] }), { relatedDiagnosticRecords: [selectedLiteral] });
equal(recordGetterReads, 0);
class RecordArray extends Array<unknown> {}
const badArrays = [Array(1), Array(diagnosticRelatedRecordLimit + 1).fill(selectedLiteral), new RecordArray(selectedLiteral), Object.assign([selectedLiteral], { extra: true }),
  Object.defineProperty([selectedLiteral], "0", { enumerable: true, get() { recordGetterReads++; throw new Error("synthetic-private-canary"); } }),
  Object.defineProperty([selectedLiteral], "0", { value: selectedLiteral, enumerable: false }),
  new Proxy([selectedLiteral], { getOwnPropertyDescriptor() { throw new Error("synthetic-private-canary"); } }),
];
for (const badArray of badArrays) deepEqual(selectDiagnosticEvidence([definition], { diagnosticRecord: selectedLiteral, relatedDiagnosticRecords: badArray }), { diagnosticRecord: selectedLiteral }, "malformed lists are rejected whole without dropping the valid primary");
equal(recordGetterReads, 0);
let prematureRecordReads = 0;
const countedRecord = new Proxy({ ...selectedLiteral }, { getOwnPropertyDescriptor(target, key) { prematureRecordReads++; return Reflect.getOwnPropertyDescriptor(target, key); } });
const laterHole = [countedRecord, selectedLiteral];
delete (laterHole as unknown[])[1];
const laterAccessor = Object.defineProperty([countedRecord, selectedLiteral], "1", { enumerable: true, get() { throw new Error("synthetic-private-canary"); } });
for (const badArray of [laterHole, laterAccessor, Array(diagnosticRelatedRecordLimit + 1).fill(countedRecord)]) deepEqual(selectDiagnosticEvidence([definition], { relatedDiagnosticRecords: badArray }), {});
equal(prematureRecordReads, 0, "validate the whole list shape before inspecting any record");
const mutableRecord = { ...selectedLiteral, detail: { issues: [{ setting: "database.port", reason: "out-of-range" }] } };
const mutableCompanions = [mutableRecord];
const copiedEvidence = selectDiagnosticEvidence([definition], { diagnosticRecord: mutableRecord, relatedDiagnosticRecords: mutableCompanions });
notEqual(copiedEvidence.diagnosticRecord, mutableRecord);
notEqual(copiedEvidence.relatedDiagnosticRecords?.[0], mutableRecord);
mutableRecord.detail.issues[0]!.setting = "synthetic-private-canary";
mutableCompanions.length = 0;
deepEqual(copiedEvidence, { diagnosticRecord: selectedLiteral, relatedDiagnosticRecords: [selectedLiteral] });
equal(Object.isFrozen(copiedEvidence), true);
equal(Object.isFrozen(copiedEvidence.relatedDiagnosticRecords), true);
equal(Object.isFrozen(copiedEvidence.diagnosticRecord?.detail), true);
console.log("Core selects only validated owned diagnostic evidence without traversing exceptions.");
