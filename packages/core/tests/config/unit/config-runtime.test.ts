import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import * as configReporting from "../../../src/config/domain/reporting/diagnostic-reporting";
import * as settingIssueNames from "../../../src/config/contract/reporting/setting-issues";
import { deepEqual, equal, throws } from "node:assert/strict";
import { isErr, isOk } from "../../../src/shared/index";
import {
  booleanConfigValue,
  configError,
  environmentName,
  numberConfigValue,
  optionalConfigValue,
  recordConfigSource,
  requiredConfigValue,
  secretReference,
  stringConfigValue,
  validateConfigSettings,
  validateConfigRequirements,
  createConfigIssueCollector,
  destinationPortConstraint,
  coreConfigDiagnosticCatalog,
  coreConfigDiagnosticDefinitions,
  type ConfigSettingRelationship,
} from "../../../src/config/index";
import { validationIssue } from "../../../src/validation/index";

equal(coreConfigDiagnosticCatalog.owner, "core.config");
// Faults in reporting are not faults in the value/source operation itself.
// Run actual public readers and declaration checking, not only record builders.
const configBuilders = require("../../../src/config/contract/reporting/diagnostics") as typeof import("../../../src/config/contract/reporting/diagnostics");
const originalPrimitive = configBuilders.coreConfigPrimitiveRecord, originalSource = configBuilders.coreConfigSourceRecord;
for (const mode of ["throws", "missing"] as const) {
  const broken = (): never => { if (mode === "throws") throw new Error("PRIVATE-CONFIG-CANARY"); return undefined as never; };
  configBuilders.coreConfigPrimitiveRecord = broken;
  configBuilders.coreConfigSourceRecord = broken;
  try {
    const expected = { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1,
      detail: { reason: mode === "throws" ? "construction-threw" : "construction-rejected" } };
    for (const result of [stringConfigValue(recordConfigSource({}), "PRIVATE"), numberConfigValue(recordConfigSource({ PORT: "bad" }), "PORT"), environmentName("Bad Name"), secretReference(" ")]) {
      if (result.ok) throw new Error("Expected original invalid input.");
      deepEqual(result.error.diagnosticRecord, expected);
    }
    for (const operation of [
      (source: { get(): never }) => stringConfigValue(source, "PRIVATE"),
      (source: { get(): never }) => validateConfigRequirements(source, [{ setting: "port", rule: destinationPortConstraint }]),
    ]) {
      const original = new Error("PRIVATE-CONFIG-CANARY"); let calls = 0;
      throws(() => operation({ get() { calls++; throw original; } }), error => error === original);
      equal(calls, 1); deepEqual(Object.getOwnPropertyDescriptor(original, "diagnosticRecord")?.value, expected);
    }
  } finally {
    configBuilders.coreConfigPrimitiveRecord = originalPrimitive;
    configBuilders.coreConfigSourceRecord = originalSource;
  }
}
equal(coreConfigDiagnosticCatalog.definitions, coreConfigDiagnosticDefinitions, "module catalogue reuses the authoritative objects");
equal(Object.isFrozen(coreConfigDiagnosticCatalog), true);
deepEqual(coreConfigDiagnosticCatalog.definitions.map(({ code, version }) => [code, version]), [
  ["core.config.primitive-invalid", 1], ["core.config.source-threw", 1],
  ["core.config.declaration-invalid", 1], ["core.config.relationship-declaration-invalid", 1],
  ["core.config.choice-declaration-invalid", 1],
]);

const choiceRequirement = [{ setting: "task.operation", rule: { kind: "choice", values: ["apply", "inspect"] } }] as const;
for (const value of ["apply", "inspect"]) deepEqual(validateConfigRequirements(recordConfigSource({ "task.operation": value }), choiceRequirement), { ok: true, value: { "task.operation": value } });
for (const [value, reason] of [[undefined, "missing"], [null, "wrong-type"], [1, "wrong-type"], ["", "blank"], [" \t", "blank"], [" apply", "surrounding-whitespace"], ["rollback", "unsupported-value"]] as const) {
  deepEqual(validateConfigRequirements(recordConfigSource({ "task.operation": value }), choiceRequirement), { ok: false, error: { code: "CONFIGURATION_INVALID", issues: [{ setting: "task.operation", reason }] } });
}
const mutableChoices = ["apply"];
deepEqual(validateConfigRequirements({ get() { mutableChoices[0] = "rollback"; return "apply"; } }, [{ setting: "operation", rule: { kind: "choice", values: mutableChoices } }]),
  { ok: true, value: { operation: "apply" } }, "choice declarations are snapshotted before a source can change them");
for (const [values, reason, index] of [[null, "wrong-type", undefined], [[], "empty", undefined], [Array(33).fill("x"), "too-many", undefined],
  [[1], "wrong-type", 0], [[" "], "blank", 0], [[" apply"], "surrounding-whitespace", 0], [["apply", "apply"], "duplicate", 1]] as const) {
  let reads = 0;
  throws(() => validateConfigRequirements({ get() { reads++; return "apply"; } }, [{ setting: "operation", rule: { kind: "choice", values } }] as never), error => {
    equal(error instanceof TypeError, true);
    const record = Object.getOwnPropertyDescriptor(error, "diagnosticRecord")?.value;
    deepEqual(record, { schema: "core/diagnostic-record/v1", code: "core.config.choice-declaration-invalid", definitionVersion: 1, detail: { reason, ...(index === undefined ? {} : { index }) } });
    return true;
  });
  equal(reads, 0, "malformed choices must not blame or read supplied values");
}

deepEqual(destinationPortConstraint, { kind: "integer", minimum: 1, maximum: 65_535 });
equal(Object.isFrozen(destinationPortConstraint), true);
throws(() => Object.assign(destinationPortConstraint, { maximum: 0 }), TypeError);
equal(destinationPortConstraint.maximum, 65_535);
const portDefinition = [{ setting: "database.port", source: "PORT", rule: destinationPortConstraint }] as const;
const logicalPort = [{ setting: "database.port", rule: destinationPortConstraint }] as const;
deepEqual(validateConfigRequirements(recordConfigSource({ "database.port": "443" }), logicalPort), { ok: true, value: { "database.port": 443 } });
deepEqual(validateConfigRequirements(recordConfigSource({}), logicalPort), { ok: false, error: { code: "CONFIGURATION_INVALID", issues: [{ setting: "database.port", reason: "missing" }] } });
for (const port of ["1", "5432", "65535", "0001"]) {
  deepEqual(validateConfigSettings(recordConfigSource({ PORT: port }), portDefinition), {
    ok: true, value: { "database.port": Number(port) },
  });
}
for (const [port, reason] of [
  [undefined, "missing"], [5432, "wrong-type"], [null, "wrong-type"], ["", "blank"],
  [" 1", "surrounding-whitespace"], ["+1", "invalid-integer"], ["1.5", "invalid-integer"],
  ["1e3", "invalid-integer"], ["NaN", "invalid-integer"], ["Infinity", "invalid-integer"],
  ["0", "out-of-range"], ["-1", "out-of-range"], ["65536", "out-of-range"],
] as const) {
  deepEqual(validateConfigSettings(recordConfigSource({ PORT: port }), portDefinition), {
    ok: false, error: { code: "CONFIGURATION_INVALID", issues: [{ setting: "database.port", reason }] },
  });
}

const source = recordConfigSource({
  API_URL: "https://api.example.test",
  RETRY_LIMIT: 3,
  FEATURE_ENABLED: false,
  EMPTY_VALUE: null,
});

const mutableValues: Record<string, string | undefined> = { MODE: "initial" };
const snapshotSource = recordConfigSource(mutableValues);
mutableValues.MODE = "changed";
equal(snapshotSource.get("MODE"), "initial");

const validEnvironment = environmentName("staging");
equal(isOk(validEnvironment), true);
if (!isOk(validEnvironment)) {
  throw new Error("Expected staging environment name to be valid.");
}
equal(validEnvironment.value, "staging");

const invalidEnvironment = environmentName("Staging");
equal(isErr(invalidEnvironment), true);
if (!isErr(invalidEnvironment)) {
  throw new Error("Expected uppercase environment name to be invalid.");
}
equal(invalidEnvironment.error.issues[0].messageKey, "config.environment.invalid");

const validSecretReference = secretReference("kanbien/staging/api-token");
equal(isOk(validSecretReference), true);
if (!isOk(validSecretReference)) {
  throw new Error("Expected secret reference to be valid.");
}
equal(validSecretReference.value, "kanbien/staging/api-token");

const invalidSecretReference = secretReference(" kanbien/staging/api-token");
equal(isErr(invalidSecretReference), true);
if (!isErr(invalidSecretReference)) {
  throw new Error("Expected untrimmed secret reference to be invalid.");
}
equal(invalidSecretReference.error.issues[0].messageKey, "config.secret_reference.invalid");

const required = requiredConfigValue(source, "API_URL");
equal(isOk(required), true);
if (!isOk(required)) {
  throw new Error("Expected API_URL to be present.");
}
equal(required.value, "https://api.example.test");

equal(optionalConfigValue(source, "MISSING"), undefined);
equal(optionalConfigValue(source, "EMPTY_VALUE"), null);

const apiUrl = stringConfigValue(source, "API_URL");
equal(isOk(apiUrl), true);
if (!isOk(apiUrl)) {
  throw new Error("Expected API_URL to be a string.");
}
equal(apiUrl.value, "https://api.example.test");

const retryLimit = numberConfigValue(source, "RETRY_LIMIT");
equal(isOk(retryLimit), true);
if (!isOk(retryLimit)) {
  throw new Error("Expected RETRY_LIMIT to be a number.");
}
equal(retryLimit.value, 3);

const featureEnabled = booleanConfigValue(source, "FEATURE_ENABLED");
equal(isOk(featureEnabled), true);
if (!isOk(featureEnabled)) {
  throw new Error("Expected FEATURE_ENABLED to be a boolean.");
}
equal(featureEnabled.value, false);

const missing = requiredConfigValue(source, "MISSING");
equal(isErr(missing), true);
if (!isErr(missing)) {
  throw new Error("Expected MISSING to fail.");
}
equal(missing.error.code, "CONFIG_MISSING");
deepEqual(missing.error.issues[0], {
  path: ["config", "MISSING"],
  code: "CONFIG_MISSING",
  defaultMessage: "Config value is required.",
  messageKey: "config.missing",
  params: { key: "MISSING" },
});

const invalidType = numberConfigValue(source, "API_URL");
equal(isErr(invalidType), true);
if (!isErr(invalidType)) {
  throw new Error("Expected API_URL as number to fail.");
}
equal(invalidType.error.code, "CONFIG_INVALID");
deepEqual(invalidType.error.issues[0], {
  path: ["config", "API_URL"],
  code: "CONFIG_INVALID_TYPE",
  defaultMessage: "Config value has the wrong type.",
  messageKey: "config.invalid_type",
  params: { key: "API_URL", expected: "finite number", actual: "string" },
});

const explicitError = configError("CONFIG_INVALID", [
  validationIssue({
    path: ["config", "CUSTOM"],
    code: "CONFIG_CUSTOM",
    defaultMessage: "Config value is invalid.",
  }),
]);
equal(explicitError.issues[0].code, "CONFIG_CUSTOM");

const settings = ["first", "second", "third"].map((setting) => ({ setting, source: setting, rule: { kind: "text" as const, pattern: /^[a-z]+$/ } }));
const relationships = [
  { relationship: "first-second", rule: "must-differ", left: "first", right: "second" },
  { relationship: "first-third", rule: "must-differ", left: "first", right: "third" },
  { relationship: "second-third", rule: "must-differ", left: "second", right: "third" },
] as const;
deepEqual(validateConfigSettings(recordConfigSource({}), settings), { ok: false, error: { code: "CONFIGURATION_INVALID", issues: settings.map(({ setting }) => ({ setting, reason: "missing" })) } }, "legacy callers retain exact failure shape");
deepEqual(validateConfigSettings(recordConfigSource({ first: "a", second: "b", third: "c" }), settings, relationships), { ok: true, value: { first: "a", second: "b", third: "c" } });
const equalValues = validateConfigSettings(recordConfigSource({ first: "syntheticcanary", second: "syntheticcanary", third: "syntheticcanary" }), settings, relationships);
deepEqual(equalValues, { ok: false, error: { code: "CONFIGURATION_INVALID", issues: [], relationshipIssues: relationships } });
equal(JSON.stringify(equalValues).includes("syntheticcanary"), false);
for (const [raw, reason] of [[undefined, "missing"], [false, "wrong-type"], ["", "blank"], [" a", "surrounding-whitespace"], ["A", "invalid-format"]] as const) {
  deepEqual(validateConfigSettings(recordConfigSource({ first: raw, second: "same", third: "same" }), settings, relationships), {
    ok: false, error: { code: "CONFIGURATION_INVALID", issues: [{ setting: "first", reason }], relationshipIssues: [relationships[2]] },
  }, "invalid participant is not compared; independent comparison survives");
}
const invalidDeclarations: readonly (readonly ConfigSettingRelationship[])[] = [
  [{ ...relationships[0], left: "unknown" }], [{ ...relationships[0], right: "first" }],
  [relationships[0], relationships[0]], [relationships[0], { ...relationships[0], relationship: "reversed", left: "second", right: "first" }],
  [{ ...relationships[0], relationship: "unsafe value" }], [{ ...relationships[0], rule: "unsupported" } as unknown as ConfigSettingRelationship],
  Array.from({ length: 33 }, (_, i) => ({ ...relationships[0], relationship: `relation-${i}` })),
];
for (const declarations of invalidDeclarations) {
  let reads = 0;
  throws(() => validateConfigSettings({ get: () => { reads += 1; return "same"; } }, settings, declarations), /CONFIGURATION_RELATIONSHIP_SCHEMA_INVALID/);
  equal(reads, 0, "declaration rejection precedes configuration reads");
}
deepEqual(validateConfigSettings(recordConfigSource({ first: "one", second: "two", third: "three" }), settings, []), { ok: true, value: { first: "one", second: "two", third: "three" } });
const maximumSettings = Array.from({ length: 32 }, (_, i) => ({ setting: `setting-${i}`, source: `SETTING_${i}`, rule: { kind: "text" as const } }));
const maximumRelationships = [
  ...Array.from({ length: 31 }, (_, i) => ({ relationship: `relation-${i}`, rule: "must-differ" as const, left: "setting-0", right: `setting-${i + 1}` })),
  { relationship: "relation-31", rule: "must-differ" as const, left: "setting-1", right: "setting-2" },
];
const maximumResult = validateConfigSettings(recordConfigSource(Object.fromEntries(maximumSettings.map(({ source }) => [source, "same"]))), maximumSettings, maximumRelationships);
equal(maximumResult.ok, false);
if (!maximumResult.ok) deepEqual(maximumResult.error.relationshipIssues, maximumRelationships);
const integerSettings = ["first", "second"].map((setting) => ({ setting, source: setting, rule: { kind: "integer" as const, minimum: 1, maximum: 100 } }));
deepEqual(validateConfigSettings(recordConfigSource({ first: "01", second: "1" }), integerSettings, [relationships[0]]), {
  ok: false, error: { code: "CONFIGURATION_INVALID", issues: [], relationshipIssues: [relationships[0]] },
}, "relationships compare parsed integers, not different source spellings");
console.log("packages/core config runtime test passed.");
const bounded = createConfigIssueCollector<"missing">();
const mutableIssue = { setting: "fixture.setting", reason: "missing" as const, index: 0 };
bounded.add(mutableIssue); mutableIssue.index = 4;
const firstSnapshot = bounded.finish();
deepEqual(firstSnapshot, { issues: [{ setting: "fixture.setting", reason: "missing", index: 0 }], truncated: false });
for (let i = 1; i < 34; i++) bounded.add({ setting: "fixture.setting", reason: "missing", index: i });
equal(bounded.finish().issues.length, 32); equal(bounded.finish().truncated, true); equal(firstSnapshot.issues.length, 1);
equal(Object.isFrozen(firstSnapshot.issues[0]), true); equal(Object.isFrozen(firstSnapshot.issues), true);
let issueGetterReads = 0;
throws(() => bounded.add(Object.defineProperty({ setting: "fixture.setting", reason: "missing" as const }, "index", { enumerable: true, get() { issueGetterReads++; return 0; } })), /CONFIGURATION_ISSUE_INVALID/);
equal(issueGetterReads, 0);
for (const value of [{ setting: "fixture.setting", reason: "missing", value: "synthetic-private" }, { setting: "fixture.setting", reason: "missing", index: -1 },
  { setting: "fixture.setting", reason: "missing", attributeIndex: 0.5 }, { setting: "unsafe value", reason: "missing" }]) throws(() => bounded.add(value as typeof mutableIssue), /CONFIGURATION_ISSUE_INVALID/);

// Re-evaluate the actual moved helper, so a future vocabulary growth cannot widen old defaults.
const reportingFile = require.resolve("../../../src/config/domain/reporting/diagnostic-reporting");
const reportingRequire = createRequire(reportingFile), reportingFixture = { exports: {} as typeof configReporting };
const futureReason = "fixture-future-reason";
new Function("require", "module", "exports", readFileSync(reportingFile, "utf8"))(
  (name: string) => name === "../../contract/reporting/setting-issues" ? { ...settingIssueNames,
    configReasonNames: { ...settingIssueNames.configReasonNames, future: futureReason },
    configIssueReasons: [...settingIssueNames.configIssueReasons, futureReason],
    configValueIssueReasons: [...settingIssueNames.configValueIssueReasons, futureReason],
  } : reportingRequire(name), reportingFixture, reportingFixture.exports,
);
const previousDefinition = configReporting.defineConfigurationDiagnostic("fixture.moved-report", ["database.port"]);
deepEqual(reportingFixture.exports.defineConfigurationDiagnostic("fixture.moved-report", ["database.port"]), previousDefinition);
equal(reportingFixture.exports.configurationDiagnostic(previousDefinition, [{ setting: "database.port", reason: futureReason }]).ok, false);
const explicitFuture = reportingFixture.exports.defineConfigurationDiagnostic("fixture.new-selected-report", ["database.port"], [futureReason]);
equal(reportingFixture.exports.configurationDiagnostic(explicitFuture, [{ setting: "database.port", reason: futureReason }]).ok, true);
let malformedReads = 0;
throws(() => validateConfigRequirements({ get() { malformedReads++; return "443"; } }, [{ setting: "port", rule: { kind: "unsupported" } }] as never),
  error => error instanceof TypeError && error.message === "CONFIGURATION_SCHEMA_INVALID");
equal(malformedReads, 0);
