import { deepEqual, equal, notEqual, throws } from "node:assert/strict";
import {
  coreDiagnosticCatalog, parseDiagnosticRecord, createDiagnosticRecord, type DiagnosticRecord,
  requiredConfigValue, optionalConfigValue, stringConfigValue, numberConfigValue, booleanConfigValue,
  environmentName, secretReference, configError, recordConfigSource, validateConfigSettings,
  type ConfigSettingDefinition, type ConfigSettingRelationship, type ConfigSource, type ConfigError,
  copyJsonValue, isoDateTime, isoDateTimeFromDate, type JsonValue,
  secretString, hashAlgorithm, hashValue, hash, securityPolicyId, dataClassification, permission,
  principal, principalId, allow, securityPolicyAllowed,
} from "../src/index";
import { coreConfigPrimitiveDiagnostic } from "../src/config/index";
import { coreJsonDiagnostic } from "../src/shared/index";
import { coreSecurityPrimitiveDiagnostic } from "../src/security/index";
import { corePermissionDiagnostic } from "../src/authz/index";

for (const code of ["core.config.source-threw", "core.shared.date-normalization-threw"]) {
  deepEqual(coreDiagnosticCatalog.definitions.find((definition) => definition.code === code)?.classification,
    { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false }, "invocation throws do not prove invalid input or configuration");
}

function record(code: string, detail: unknown): DiagnosticRecord {
  return { schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail };
}
function observed(run: () => unknown): unknown {
  try { run(); } catch (error) { return error; }
  throw new Error("Expected an observed throw.");
}
function thrownRecord(run: () => unknown, message?: string): DiagnosticRecord {
  const error = observed(run);
  equal(error instanceof Error, true);
  if (!(error instanceof Error)) throw new Error("Expected an error.");
  if (message !== undefined) equal(error.message, message);
  const evidence = Object.getOwnPropertyDescriptor(error, "diagnosticRecord")?.value as DiagnosticRecord;
  const definition = coreDiagnosticCatalog.definitions.find((candidate) => candidate.code === evidence?.code);
  equal(definition !== undefined, true);
  if (!definition) throw new Error("Expected a catalogued record.");
  equal(parseDiagnosticRecord<unknown>(definition, evidence).ok, true);
  return evidence;
}
function configRecord(result: ReturnType<typeof requiredConfigValue>): DiagnosticRecord | undefined {
  if (result.ok) throw new Error("Expected a configuration failure.");
  return result.error.diagnosticRecord;
}
const primitive = (reader: string, reason: string, field = "value") => record("core.config.primitive-invalid", { field, reader, reason });
equal(coreDiagnosticCatalog.owner, "core");
deepEqual(coreDiagnosticCatalog.definitions.filter(({ code }) => !code.startsWith("core.persistence.")).map(({ code, version }) => [code, version]), [
  ["core.config.primitive-invalid", 1], ["core.config.source-threw", 1], ["core.config.declaration-invalid", 1], ["core.config.relationship-declaration-invalid", 1], ["core.config.choice-declaration-invalid", 1],
  ["core.shared.date-invalid", 1], ["core.shared.date-normalization-threw", 1], ["core.shared.json-invalid", 1],
  ["core.security.primitive-invalid", 1], ["core.authz.permission-invalid", 1],
  ["core.authn.boundary-failed", 1], ["core.tenancy.boundary-failed", 1],
  ["core.queue.validation-rejected", 1], ["core.queue.boundary-failed", 1], ["core.queue.receive-reduced", 1],
  ["core.monitoring.validation-rejected", 1], ["core.monitoring.boundary-failed", 1], ["core.logging.boundary-failed", 1],
  ["core.audit.validation-rejected", 1], ["core.audit.boundary-failed", 1],
  ["core.events.validation-rejected", 1], ["core.events.boundary-failed", 1],
  ["core.files.validation-rejected", 1], ["core.files.operation-rejected", 1], ["core.files.boundary-failed", 1],
  ["core.i18n.validation-rejected", 1], ["core.i18n.selection-observed", 1], ["core.i18n.boundary-failed", 1],
  ["core.localization.validation-rejected", 1], ["core.localization.unsupported-observed", 1], ["core.localization.boundary-failed", 1],
]);
deepEqual(coreDiagnosticCatalog.definitions.filter(({ code }) => code.startsWith("core.persistence.")).map(({ code, version }) => [code, version]), [
  ["core.persistence.validation-rejected", 1], ["core.persistence.in-memory-boundary-failed", 1],
]);
equal(new Set(coreDiagnosticCatalog.definitions.map(({ code, version }) => `${code}@${version}`)).size, coreDiagnosticCatalog.definitions.length);
for (const definition of coreDiagnosticCatalog.definitions) equal(definition.code.startsWith("core."), true);

const readers = [["required", requiredConfigValue], ["string", stringConfigValue], ["number", numberConfigValue], ["boolean", booleanConfigValue]] as const;
for (const [reader, read] of readers) {
  let reads = 0;
  deepEqual(configRecord(read({ get: () => { reads++; return undefined; } }, "synthetic-private-key")), primitive(reader, "missing"));
  equal(reads, 1);
}
for (const [reader, read, invalids] of [
  ["string", stringConfigValue, [null, true, 0, Number.NaN]],
  ["number", numberConfigValue, [null, false, "0"]],
  ["boolean", booleanConfigValue, [null, "false", 0, Number.NaN]],
] as const) for (const value of invalids) {
  let reads = 0;
  const result = read({ get: () => { reads++; return value; } }, "synthetic-private-key");
  deepEqual(configRecord(result), primitive(reader, "wrong-type"));
  equal(reads, 1);
  equal(JSON.stringify(configRecord(result)).includes("synthetic-private"), false);
}
for (const value of [NaN, Infinity, -Infinity]) deepEqual(configRecord(numberConfigValue({ get: () => value }, "private")), primitive("number", "non-finite"));
for (const [read, value] of [[stringConfigValue, ""], [numberConfigValue, 0], [booleanConfigValue, false], [requiredConfigValue, null]] as const) {
  deepEqual(read({ get: () => value }, "private"), { ok: true, value });
}
for (const [construct, reader, invalid] of [[environmentName, "environment-name", "BAD synthetic-private"], [secretReference, "secret-reference", " synthetic-private/key"]] as const) {
  deepEqual(configRecord(construct("")), primitive(reader, "empty", reader));
  deepEqual(configRecord(construct(invalid)), primitive(reader, "invalid-format", reader));
}
for (const name of ["a", "staging-2", "test0"]) equal(environmentName(name).ok, true);
for (const reference of ["a", "a._:/-Z09", "config/provider-neutral/path"]) equal(secretReference(reference).ok, true);
for (const construct of [environmentName, secretReference]) {
  let conversions = 0, lengthReads = 0;
  const legacyNativeInput = { toString() { conversions++; return "synthetic private"; }, get length() { lengthReads++; throw new Error("Unexpected length read."); } };
  equal(construct(legacyNativeInput as never).ok, false);
  deepEqual([conversions, lengthReads], [1, 0], "regex coercion does not introduce extra native-input property reads");
}

const preserved = configRecord(environmentName(""))!;
const related = Object.freeze([preserved]);
const supplied = configError("CONFIG_INVALID", [{ path: [], code: "CUSTOM", defaultMessage: "Invalid." }], { diagnosticRecord: preserved, relatedDiagnosticRecords: related });
equal(supplied.diagnosticRecord, preserved);
equal(supplied.relatedDiagnosticRecords, related);
deepEqual(configError("CONFIG_INVALID", supplied.issues), { code: "CONFIG_INVALID", issues: supplied.issues });
const readInvocations = [...readers, ["optional", optionalConfigValue] as const];
for (const [reader, read] of readInvocations) {
  const failure = new Error("synthetic-private-source-message");
  equal(observed(() => read({ get: () => { throw failure; } }, "synthetic-private-key")), failure);
  deepEqual(Object.getOwnPropertyDescriptor(failure, "diagnosticRecord")?.value, record("core.config.source-threw", { reader, phase: "source-read", reason: "invocation-threw" }));
  for (const failure of [undefined, null, 7, "synthetic-private", Object.freeze(new Error("frozen"))]) {
    equal(observed(() => read({ get: () => { throw failure; } }, "private")), failure);
  }
}
const upstream = Object.assign(new Error("upstream"), { diagnosticRecord: preserved });
equal(observed(() => requiredConfigValue({ get: () => { throw upstream; } }, "private")), upstream);
equal(upstream.diagnosticRecord, preserved);

const text = (setting = "first", source = "FIRST"): ConfigSettingDefinition => ({ setting, source, rule: { kind: "text" } });
const integer = (minimum: number, maximum: number): ConfigSettingDefinition => ({ setting: "first", source: "FIRST", rule: { kind: "integer", minimum, maximum } });
const definitions = [text(), text("second", "SECOND")];
const declarationCases: readonly [readonly ConfigSettingDefinition[], unknown][] = [
  [[], { field: "definitions", reason: "empty" }],
  [Array.from({ length: 33 }, (_, index) => text(`field-${index}`)), { field: "definitions", reason: "too-many" }],
  [[text(), text()], { field: "setting", reason: "identity-count-mismatch" }],
  [[text("synthetic-private name")], { field: "setting", reason: "invalid-format", index: 0 }],
  [[text("first", "synthetic-private source")], { field: "source", reason: "invalid-format", index: 0 }],
  [[text("constructor")], { field: "setting", reason: "reserved", index: 0 }],
  [[text("prototype")], { field: "setting", reason: "reserved", index: 0 }],
  [[text("__proto__")], { field: "setting", reason: "invalid-format", index: 0 }],
  [[integer(Infinity, 1)], { field: "minimum", reason: "not-safe-integer", index: 0 }],
  [[integer(0, 1.5)], { field: "maximum", reason: "not-safe-integer", index: 0 }],
  [[integer(2, 1)], { field: "bounds", reason: "reversed", index: 0 }],
];
for (const [declarations, detail] of declarationCases) {
  let reads = 0;
  deepEqual(thrownRecord(() => validateConfigSettings({ get: () => { reads++; return "value"; } }, declarations), "CONFIGURATION_SCHEMA_INVALID"), record("core.config.declaration-invalid", detail));
  equal(reads, 0);
}
const relationship: ConfigSettingRelationship = { relationship: "first-second", rule: "must-differ", left: "first", right: "second" };
const relationshipCases: readonly [readonly ConfigSettingRelationship[], unknown][] = [
  [Array.from({ length: 33 }, () => relationship), { field: "relationships", reason: "too-many" }],
  [[relationship, relationship], { field: "relationship", reason: "identity-count-mismatch" }],
  [[{ ...relationship, relationship: "synthetic-private name" }], { field: "relationship", reason: "invalid-format", index: 0 }],
  [[{ ...relationship, rule: "unsupported" } as never], { field: "rule", reason: "unsupported", index: 0 }],
  [[{ ...relationship, left: "synthetic-private" }], { field: "left", reason: "undeclared", index: 0 }],
  [[{ ...relationship, right: "synthetic-private" }], { field: "right", reason: "undeclared", index: 0 }],
  [[{ ...relationship, right: "first" }], { field: "participants", reason: "self-reference", index: 0 }],
  [[relationship, { ...relationship, relationship: "reverse", left: "second", right: "first" }], { field: "participants", reason: "duplicate-pair", index: 1 }],
];
for (const [relationships, detail] of relationshipCases) {
  let reads = 0;
  deepEqual(thrownRecord(() => validateConfigSettings({ get: () => { reads++; return "value"; } }, definitions, relationships), "CONFIGURATION_RELATIONSHIP_SCHEMA_INVALID"), record("core.config.relationship-declaration-invalid", detail));
  equal(reads, 0);
}
let settingReads = 0, sourceReads = 0, ruleReads = 0, valueReads = 0;
const counted = { get setting() { settingReads++; return "first"; }, get source() { sourceReads++; return "FIRST"; }, get rule() { ruleReads++; return { kind: "text" as const }; } };
deepEqual(validateConfigSettings({ get: () => { valueReads++; return ""; } }, [counted]), { ok: false, error: { code: "CONFIGURATION_INVALID", issues: [{ setting: "first", reason: "blank" }] } });
deepEqual([settingReads, sourceReads, ruleReads, valueReads], [4, 2, 2, 1]);
let kindReads = 0;
deepEqual(validateConfigSettings(recordConfigSource({ FIRST: "value" }), [{ setting: "first", source: "FIRST", rule: {
  get kind() { kindReads++; return "text" as const; },
} }]), { ok: true, value: { first: "value" } });
equal(kindReads, 2, "adding a rule variant must not reread the discriminant for existing text rules");
let invocation = 0;
const sourceFailure = new Error("synthetic-private-source");
equal(observed(() => validateConfigSettings({ get: () => { if (invocation++ === 0) return "one"; throw sourceFailure; } }, definitions)), sourceFailure);
deepEqual(Object.getOwnPropertyDescriptor(sourceFailure, "diagnosticRecord")?.value, record("core.config.source-threw", { reader: "schema", phase: "source-read", reason: "invocation-threw", index: 1 }));
equal(invocation, 2);
deepEqual(validateConfigSettings(recordConfigSource({ FIRST: "one" }), [{ ...text(), rule: { kind: "future" } as never }]), { ok: true, value: { first: "one" } }, "unsupported setting rule kinds keep historical text fallback");
deepEqual(validateConfigSettings(recordConfigSource({ FIRST: "01", SECOND: "1" }), [integer(0, 2), { ...integer(0, 2), setting: "second", source: "SECOND" }], [relationship]), { ok: false, error: { code: "CONFIGURATION_INVALID", issues: [], relationshipIssues: [relationship] } });
deepEqual(validateConfigSettings(recordConfigSource({ FIRST: undefined, SECOND: false }), definitions), { ok: false, error: { code: "CONFIGURATION_INVALID", issues: [{ setting: "first", reason: "missing" }, { setting: "second", reason: "wrong-type" }] } });

for (const [value, reason] of [["synthetic-private date", "invalid-format"], ["2026-99-01T00:00:00Z", "parse-rejected"]]) {
  const result = isoDateTime(value!);
  equal(result.ok, false);
  if (!result.ok) deepEqual(result.error.diagnosticRecord, record("core.shared.date-invalid", { reason }));
}
deepEqual(isoDateTime("2026-02-30T00:00:00Z"), { ok: true, value: "2026-03-02T00:00:00.000Z" }, "native calendar normalization remains accepted");
const invalidDateError = observed(() => isoDateTimeFromDate(new Date(NaN)));
equal(invalidDateError instanceof RangeError, true);
deepEqual(Object.getOwnPropertyDescriptor(invalidDateError as object, "diagnosticRecord")?.value, record("core.shared.date-normalization-threw", { phase: "date-normalization", reason: "invocation-threw" }));
for (const failure of [new RangeError("synthetic-private"), Object.freeze(new Error("frozen")), "synthetic-private"]) {
  const date = new Date();
  date.toISOString = () => { throw failure; };
  equal(observed(() => isoDateTimeFromDate(date)), failure);
}
let dateMethodReads = 0, dateCalls = 0;
const countedDate = new Date();
Object.defineProperty(countedDate, "toISOString", { get() { dateMethodReads++; return function(this: Date) { dateCalls++; equal(this, countedDate); return "legacy-result"; }; } });
equal(isoDateTimeFromDate(countedDate), "legacy-result");
deepEqual([dateMethodReads, dateCalls], [1, 1]);
const originalToISOString = Date.prototype.toISOString;
const normalizationFailure = new Error("synthetic-private-normalization");
try {
  Date.prototype.toISOString = () => { throw normalizationFailure; };
  equal(observed(() => isoDateTime("2026-01-01T00:00:00Z")), normalizationFailure);
} finally { Date.prototype.toISOString = originalToISOString; }
deepEqual(Object.getOwnPropertyDescriptor(normalizationFailure, "diagnosticRecord")?.value, record("core.shared.date-normalization-threw", { phase: "string-normalization", reason: "invocation-threw" }));
const json = (reason: string, depth: number, path: readonly number[], pathTruncated = false) => record("core.shared.json-invalid", { reason, depth, path, pathTruncated });
for (const value of [NaN, Infinity, -Infinity]) deepEqual(thrownRecord(() => copyJsonValue(value, "synthetic-private-label"), "synthetic-private-label must contain only finite numbers."), json("non-finite-number", 0, []));
for (const value of [new Date(), Object.create(null), new (class Private {})()]) deepEqual(thrownRecord(() => copyJsonValue(value as JsonValue)), json("non-plain-object", 0, []));
deepEqual(thrownRecord(() => copyJsonValue({ "synthetic-private-key": [0, { anotherPrivate: Infinity }] })), json("non-finite-number", 3, [0, 1, 0]));
let deep: JsonValue = Infinity;
for (let i = 0; i < 18; i++) deep = [deep];
deepEqual(thrownRecord(() => copyJsonValue(deep)), json("non-finite-number", 18, Array(16).fill(0), true));
let firstReads = 0, secondReads = 0;
const getterObject = { get syntheticPrivateFirst() { firstReads++; return Infinity; }, get syntheticPrivateSecond() { secondReads++; return "value"; } };
deepEqual(thrownRecord(() => copyJsonValue(getterObject)), json("non-finite-number", 1, [0]));
deepEqual([firstReads, secondReads], [1, 1], "Object.entries reads each getter once before recursive validation");
let laterArrayReads = 0;
const getterArray = [Infinity, 0];
Object.defineProperty(getterArray, "1", { get() { laterArrayReads++; return 0; } });
deepEqual(thrownRecord(() => copyJsonValue(getterArray)), json("non-finite-number", 1, [0]));
equal(laterArrayReads, 0, "array first failure precedes later getters");
const validJson = { nested: [0, "", false, null] };
deepEqual(copyJsonValue(validJson), validJson);
notEqual(copyJsonValue(validJson), validJson);
equal(copyJsonValue(undefined as never), undefined, "no new runtime input policy");
const callable = () => 1;
equal(copyJsonValue(callable as never), callable, "no new runtime input policy");
for (const run of [
  () => principal({ id: principalId("fixture"), type: "user", subject: "fixture", claims: { syntheticPrivate: Infinity } }),
  () => allow({ evidence: { syntheticPrivate: Infinity } }),
  () => securityPolicyAllowed({ evidence: { syntheticPrivate: Infinity } }),
]) deepEqual(thrownRecord(run), json("non-finite-number", 0, []));

const security = (field: string, reason: string) => record("core.security.primitive-invalid", { field, reason });
deepEqual(thrownRecord(() => secretString(""), "secret string must be non-empty."), security("secret-string", "empty"));
equal(secretString(" \n"), " \n", "secret strings retain whitespace acceptance");
for (const [field, construct, label] of [["hash-algorithm", hashAlgorithm, "hash algorithm"], ["hash-value", hashValue, "hash value"], ["security-policy-id", securityPolicyId, "security policy id"]] as const) {
  deepEqual(thrownRecord(() => construct(""), `${label} must be non-empty.`), security(field, "empty"));
  deepEqual(thrownRecord(() => construct(" synthetic-private"), `${label} must not contain whitespace.`), security(field, "surrounding-whitespace"));
  deepEqual(thrownRecord(() => construct("synthetic private"), `${label} must not contain whitespace.`), security(field, "whitespace"));
  equal(construct("a:b.$/_-"), "a:b.$/_-");
}
deepEqual(thrownRecord(() => dataClassification({ kind: "synthetic-private" as never, sensitivity: "secret" })), security("sensitive-value-kind", "unsupported"));
deepEqual(thrownRecord(() => dataClassification({ kind: "token", sensitivity: "synthetic-private" as never })), security("data-sensitivity", "unsupported"));
let hashValueReads = 0;
deepEqual(thrownRecord(() => hash({ algorithm: "", get value() { hashValueReads++; return ""; } })), security("hash-algorithm", "empty"));
equal(hashValueReads, 0);
let sensitivityReads = 0;
deepEqual(thrownRecord(() => dataClassification({ kind: "synthetic-private" as never, get sensitivity() { sensitivityReads++; return "secret" as const; } })), security("sensitive-value-kind", "unsupported"));
equal(sensitivityReads, 0);
for (const field of ["resource", "action"] as const) for (const [input, reason] of [["", "empty"], [" synthetic-private", "surrounding-whitespace"], ["synthetic:private", "colon-separator"], ["synthetic private", "whitespace"]] as const) {
  deepEqual(thrownRecord(() => permission(field === "resource" ? input : "valid", field === "action" ? input : "valid"), `Permission ${field} must be a non-empty string without whitespace or colon separators.`), record("core.authz.permission-invalid", { field, reason }));
}
deepEqual(thrownRecord(() => permission("", "")), record("core.authz.permission-invalid", { field: "resource", reason: "empty" }));
equal(permission("a.b/0", "a-b_0"), "a.b/0:a-b_0");

for (const [definition, detail] of [
  [coreConfigPrimitiveDiagnostic, { field: "value", reader: "number", reason: "non-finite" }],
  [coreJsonDiagnostic, { reason: "non-finite-number", depth: 0, path: [], pathTruncated: false }],
  [coreSecurityPrimitiveDiagnostic, { field: "secret-string", reason: "empty" }],
  [corePermissionDiagnostic, { field: "resource", reason: "empty" }],
] as const) {
  equal(createDiagnosticRecord<unknown>(definition, { ...detail, raw: "synthetic-private" }).ok, false);
  equal(createDiagnosticRecord<unknown>(definition, { ...detail, reason: "synthetic-private" }).ok, false);
}

for (const claimedIndex of ["synthetic-private-index", 7, -1, Number.NaN, Infinity, { private: "synthetic-private-index" }]) {
  let mapReads = 0, mapCalls = 0;
  const customMap: JsonValue[] = [Infinity];
  Object.defineProperty(customMap, "map", { get() { mapReads++; return function(this: JsonValue[], visit: (item: JsonValue, index: unknown) => JsonValue) {
    equal(this, customMap); equal(visit.length, 1); mapCalls++;
    return [visit(Infinity, claimedIndex)];
  }; } });
  const evidence = thrownRecord(() => copyJsonValue(customMap), "JSON value must contain only finite numbers.");
  deepEqual(evidence, record("core.shared.json-invalid", { reason: "non-finite-number", depth: 1, path: [], pathTruncated: true, locationUnavailable: true }));
  deepEqual([mapReads, mapCalls], [1, 1]);
  equal(JSON.stringify(evidence).includes("synthetic-private"), false);
}
const customNested: JsonValue[] = [0];
Object.defineProperty(customNested, "map", { value(visit: (item: JsonValue, index: unknown) => JsonValue) { return [visit([Infinity], 9)]; } });
deepEqual(thrownRecord(() => copyJsonValue({ first: customNested })), record("core.shared.json-invalid", { reason: "non-finite-number", depth: 3, path: [0], pathTruncated: true, locationUnavailable: true }), "No native descendant index can bridge an unavailable custom-map step");
const customSuccess: JsonValue[] = [0];
Object.defineProperty(customSuccess, "map", { configurable: true, value() { return "legacy-map-result"; } });
equal(copyJsonValue(customSuccess), "legacy-map-result", "No new custom-map return policy");
const customThrown = new Error("synthetic-private-map");
Object.defineProperty(customSuccess, "map", { configurable: true, value() { throw customThrown; } });
equal(observed(() => copyJsonValue(customSuccess)), customThrown);
let noncallableReads = 0;
const noncallable: JsonValue[] = [0];
Object.defineProperty(noncallable, "map", { get() { noncallableReads++; return 42; } });
const legacyArrayMap = (value: JsonValue[]) => value.map((item) => item);
const oldMapError = observed(() => legacyArrayMap(noncallable));
equal(noncallableReads, 1);
noncallableReads = 0;
const newMapError = observed(() => copyJsonValue(noncallable));
equal(newMapError instanceof TypeError, true);
equal((newMapError as Error).message, (oldMapError as Error).message);
equal(noncallableReads, 1);

for (const returned of [true, "synthetic-private-truthy"]) {
  let someReads = 0, someCalls = 0, sourceCalls = 0;
  const customDefinitions = [text()];
  Object.defineProperty(customDefinitions, "some", { get() { someReads++; return function(this: readonly ConfigSettingDefinition[], _visit: unknown) {
    equal(this, customDefinitions); someCalls++; return returned;
  }; } });
  deepEqual(thrownRecord(() => validateConfigSettings({ get() { sourceCalls++; return "value"; } }, customDefinitions), "CONFIGURATION_SCHEMA_INVALID"),
    record("core.config.declaration-invalid", { field: "definitions", reason: "predicate-rejected-unclassified" }));
  deepEqual([someReads, someCalls, sourceCalls], [1, 1, 0]);

  someReads = 0; someCalls = 0;
  const customRelationships = [relationship];
  Object.defineProperty(customRelationships, "some", { get() { someReads++; return function(this: readonly ConfigSettingRelationship[], _visit: unknown) {
    equal(this, customRelationships); someCalls++; return returned;
  }; } });
  deepEqual(thrownRecord(() => validateConfigSettings({ get() { sourceCalls++; return "value"; } }, definitions, customRelationships), "CONFIGURATION_RELATIONSHIP_SCHEMA_INVALID"),
    record("core.config.relationship-declaration-invalid", { field: "relationships", reason: "predicate-rejected-unclassified" }));
  deepEqual([someReads, someCalls, sourceCalls], [1, 1, 0]);
}
const customSomeFalse = [text()];
Object.defineProperty(customSomeFalse, "some", { value() { return false; } });
deepEqual(validateConfigSettings(recordConfigSource({ FIRST: "legacy" }), customSomeFalse), { ok: true, value: { first: "legacy" } });

for (const claimedIndex of ["synthetic-private-index", 7]) {
  const customDefinitions = [text()];
  Object.defineProperty(customDefinitions, "some", { value(visit: (item: ConfigSettingDefinition, index: unknown) => boolean) {
    equal(visit.length, 1); return visit(text("invalid setting"), claimedIndex);
  } });
  deepEqual(thrownRecord(() => validateConfigSettings(recordConfigSource({}), customDefinitions), "CONFIGURATION_SCHEMA_INVALID"),
    record("core.config.declaration-invalid", { field: "definitions", reason: "predicate-rejected-unclassified" }));
  const customRelationships = [relationship];
  Object.defineProperty(customRelationships, "some", { value(visit: (item: ConfigSettingRelationship, index: unknown) => boolean) {
    equal(visit.length, 1); return visit({ ...relationship, rule: "unsupported" as never }, claimedIndex);
  } });
  deepEqual(thrownRecord(() => validateConfigSettings(recordConfigSource({}), definitions, customRelationships), "CONFIGURATION_RELATIONSHIP_SCHEMA_INVALID"),
    record("core.config.relationship-declaration-invalid", { field: "relationships", reason: "predicate-rejected-unclassified" }));
}
let continuedAfterCallback = 0;
const ignoresDeclarationCallback = [text()];
Object.defineProperty(ignoresDeclarationCallback, "some", { value(visit: (item: ConfigSettingDefinition) => boolean) {
  equal(visit(text("invalid setting")), true); continuedAfterCallback++; return false;
} });
deepEqual(validateConfigSettings(recordConfigSource({ FIRST: "legacy" }), ignoresDeclarationCallback), { ok: true, value: { first: "legacy" } });
const ignoresRelationshipCallback = [relationship];
Object.defineProperty(ignoresRelationshipCallback, "some", { value(visit: (item: ConfigSettingRelationship) => boolean) {
  equal(visit({ ...relationship, rule: "unsupported" as never }), true); continuedAfterCallback++; return false;
} });
deepEqual(validateConfigSettings(recordConfigSource({ FIRST: "one", SECOND: "two" }), definitions, ignoresRelationshipCallback), { ok: true, value: { first: "one", second: "two" } });
equal(continuedAfterCallback, 2, "Keep callback booleans and the custom method's continuation and false result");

for (const countKind of ["definitions", "relationships"] as const) {
  let firstPositionReads = 0, iteratorReads = 0, sourceCalls = 0;
  const names = new Proxy(["same", "same"], { get(target, key, receiver) {
    if (key === Symbol.iterator) iteratorReads++;
    if (key === "0" && ++firstPositionReads > 1) throw new Error("synthetic-private-second-index-read");
    return Reflect.get(target, key, receiver);
  } });
  if (countKind === "definitions") {
    const declarations = [text(), text("second", "SECOND")];
    Object.defineProperty(declarations, "map", { value() { return names; } });
    deepEqual(thrownRecord(() => validateConfigSettings({ get() { sourceCalls++; return "value"; } }, declarations), "CONFIGURATION_SCHEMA_INVALID"),
      record("core.config.declaration-invalid", { field: "setting", reason: "identity-count-mismatch" }));
  } else {
    const declarations = [relationship, { ...relationship, relationship: "second" }];
    Object.defineProperty(declarations, "map", { value() { return names; } });
    deepEqual(thrownRecord(() => validateConfigSettings({ get() { sourceCalls++; return "value"; } }, definitions, declarations), "CONFIGURATION_RELATIONSHIP_SCHEMA_INVALID"),
      record("core.config.relationship-declaration-invalid", { field: "relationship", reason: "identity-count-mismatch" }));
  }
  deepEqual([firstPositionReads, iteratorReads, sourceCalls], [1, 1, 0], "Diagnosis must not reread the mapped identities after the original Set predicate");
}
const uniqueWrongCount = [text(), text("second", "SECOND")];
Object.defineProperty(uniqueWrongCount, "map", { value() { return ["unique"]; } });
deepEqual(thrownRecord(() => validateConfigSettings(recordConfigSource({}), uniqueWrongCount), "CONFIGURATION_SCHEMA_INVALID"),
  record("core.config.declaration-invalid", { field: "setting", reason: "identity-count-mismatch" }), "A custom mapping length mismatch does not prove a duplicate");
console.log("packages/core foundation diagnostics runtime test passed.");
