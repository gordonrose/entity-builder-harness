import { deepEqual, equal, throws } from "node:assert/strict";
import { configError, configReasonNames, optionalConfigValue, recordConfigSource, requiredConfigValue, stringConfigValue, type ConfigSchema, type ConfigSource } from "@kanbien/core/config";
import * as coreConfiguration from "@kanbien/core/config";
import { validationIssue } from "@kanbien/core/validation";
import { assertPlatformConfigValid, validatePlatformConfigSchemas, defineConfigurationRelationshipDiagnostics, configurationRelationshipDiagnostic } from "../src/index";
import { configurationDiagnostic, defineConfigurationDiagnostic } from "../src/diagnostics";
import { withDiagnosticDeliverySuppressed } from "../../../packages/core/tests/diagnostic-delivery-fixture";

async function main(): Promise<void> {
  reasonSelectionGrowthRegression();
  const oldDefinition = defineConfigurationDiagnostic("fixture.config-invalid", ["fixture.setting"]);
  equal(configurationDiagnostic(oldDefinition, [{ setting: "fixture.setting", reason: "invalid-json" }]).ok, false, "default definitions must not silently widen");
  const selectionDefinition = defineConfigurationDiagnostic("fixture.selection-invalid", ["fixture.provider"], ["unsupported-selection"]);
  equal(configurationDiagnostic(selectionDefinition, [{ setting: "fixture.provider", reason: "unsupported-selection" }]).ok, true);
  equal(configurationDiagnostic(selectionDefinition, [{ setting: "fixture.provider", reason: "synthetic-private-canary" }]).ok, false);
  equal(configurationDiagnostic(selectionDefinition, [{ setting: "synthetic-private-canary", reason: "unsupported-selection" }]).ok, false);
  equal(configurationDiagnostic(oldDefinition, [{ setting: "fixture.setting", reason: "unsupported-selection" }]).ok, false);
  const structuredDefinition = defineConfigurationDiagnostic("fixture.structured-selected", ["fixture.setting"], [
    configReasonNames.invalidJson, configReasonNames.wrongShape, configReasonNames.empty, configReasonNames.forbiddenCharacter,
  ]);
  for (const reason of ["invalid-json", "wrong-shape", "empty", "forbidden-character"] as const) {
    const record = configurationDiagnostic(structuredDefinition, [{ setting: "fixture.setting", reason }]);
    equal(record.ok, true);
    if (record.ok) deepEqual(record.value.detail, { issues: [{ setting: "fixture.setting", reason }] });
  }
  const validSchema: ConfigSchema<{ readonly name: string }> = {
    parse: (source) => {
      const value = stringConfigValue(source, "APP_NAME");
      return value.ok
        ? { ok: true, value: { name: value.value } }
        : value;
    },
  };

  const valid = validatePlatformConfigSchemas({
    source: recordConfigSource({ APP_NAME: "platform" }),
    schemas: [validSchema],
  });
  equal(valid.ok, true);
  if (valid.ok) {
    deepEqual(valid.value, [{ name: "platform" }]);
  }

  // A real higher-level caller consumes returned values and gates dependent work.
  const schema: ConfigSchema<{ name: string; mode: string; label: string | undefined }> = {
    parse(source) {
      const name = stringConfigValue(source, "APP_NAME");
      if (!name.ok) return name;
      const suppliedMode = optionalConfigValue(source, "MODE");
      const mode = suppliedMode === undefined ? "local" : stringConfigValue(source, "MODE");
      if (typeof mode !== "string" && !mode.ok) return mode;
      const selectedMode = typeof mode === "string" ? mode : mode.value;
      if (selectedMode === "remote") {
        const endpoint = requiredConfigValue(source, "ENDPOINT");
        if (!endpoint.ok) return endpoint;
      }
      const label = optionalConfigValue(source, "LABEL");
      let selectedLabel: string | undefined;
      if (label !== undefined) {
        const checked = stringConfigValue(source, "LABEL");
        if (!checked.ok) return checked;
        selectedLabel = checked.value;
      }
      return { ok: true, value: { name: name.value, mode: selectedMode, label: selectedLabel } };
    },
  };
  const started: unknown[] = [];
  const start = (source: ConfigSource, onDiagnostic?: () => unknown) => {
    const result = validatePlatformConfigSchemas({ source, schemas: [schema], ...(onDiagnostic ? { onDiagnostic } : {}) });
    if (!result.ok) return result;
    started.push(...result.value);
    return result;
  };
  const optional = start(recordConfigSource({ APP_NAME: "checked", EXTRA: "synthetic-private-canary" }));
  equal(optional.ok, true);
  if (optional.ok) deepEqual(optional.value, [{ name: "checked", mode: "local", label: undefined }]);
  equal(start(recordConfigSource({ APP_NAME: "checked", MODE: "remote" })).ok, false);
  equal(start(recordConfigSource({ APP_NAME: "checked", MODE: "remote", ENDPOINT: "present", LABEL: "label" })).ok, true);
  let laterSchemas = 0;
  const neverReached: ConfigSchema<string> = { parse() { laterSchemas++; return { ok: true, value: "unexpected" }; } };
  equal(validatePlatformConfigSchemas({ source: recordConfigSource({}), schemas: [schema, neverReached] }).ok, false);
  equal(laterSchemas, 0);
  const startedBefore = started.length;
  const rejected = start(recordConfigSource({ APP_NAME: 42 }), () => { throw new Error("synthetic-reporter-canary"); });
  equal(rejected.ok, false); equal(started.length, startedBefore);
  equal(JSON.stringify(rejected).includes("synthetic-reporter-canary"), false);
  const sourceFailure = new Error("synthetic-source-canary");
  throws(() => start({ get() { throw sourceFailure; } }), error => error === sourceFailure);
  equal(started.length, startedBefore);

  const invalidSchema: ConfigSchema<never> = {
    parse: () => ({
      ok: false,
      error: configError("CONFIG_INVALID", [
        validationIssue({
          path: ["config", "SECRET_TOKEN"],
          code: "CONFIG_INVALID_SECRET",
          defaultMessage: "Secret config is invalid.",
          params: { token: "do-not-leak" },
        }),
      ]),
    }),
  };
  const invalid = assertPlatformConfigValid({
    source: recordConfigSource({ SECRET_TOKEN: "secret" }),
    schemas: [invalidSchema],
  });
  withDiagnosticDeliverySuppressed(attempted => {
    let delivered = 0;
    const failure = validatePlatformConfigSchemas({ source: recordConfigSource({}), schemas: [validSchema], onDiagnostic() { delivered++; } });
    equal(failure.ok, false);
    equal(delivered, 0, "actual configuration reporting delegates to Core delivery");
    deepEqual(attempted.map(record => record.code), ["platform-config.schema-rejected", "core.config.primitive-invalid"]);
  });
  equal(invalid.ok, false);
  if (!invalid.ok) {
    equal(invalid.error.code, "PLATFORM_CONFIG_INVALID");
    equal(invalid.error.details["schemaIndex"], 0);
    deepEqual(invalid.error.diagnosticRecord?.detail, { schemaIndex: 0, reason: "invalid" });
    equal(JSON.stringify(invalid.error.diagnosticRecord).includes("do-not-leak"), false);
    deepEqual(invalid.error.details["issues"], [{
      path: ["config", "SECRET_TOKEN"],
      code: "CONFIG_INVALID_SECRET",
      defaultMessage: "Secret config is invalid.",
    }]);
  }
}

function reasonSelectionGrowthRegression(): void {
  const future = "fixture-future-reason";
  const grownNames = Object.freeze({ ...coreConfiguration.configReasonNames, future });
  const fixture = { exports: { defineConfigurationDiagnostic, defineConfigurationRelationshipDiagnostics } };
  equal(defineConfigurationDiagnostic, coreConfiguration.defineConfigurationDiagnostic, "compatibility exports use the single Core implementation");
  const previous = defineConfigurationDiagnostic("fixture.reason-growth", ["fixture.setting"]);
  const retained = fixture.exports.defineConfigurationDiagnostic("fixture.reason-growth", ["fixture.setting"]);
  deepEqual(retained, previous, "a shared-name or legacy-list addition must not widen the real helper's default");
  equal(configurationDiagnostic(retained, [{ setting: "fixture.setting", reason: future }]).ok, false);
  const selected = fixture.exports.defineConfigurationDiagnostic("fixture.explicit-future", ["fixture.setting"], [grownNames.future]);
  equal(configurationDiagnostic(selected, [{ setting: "fixture.setting", reason: future }]).ok, true);
  const relationships = [{ relationship: "separation", rule: "must-differ", left: "first", right: "second" }] as const;
  deepEqual(fixture.exports.defineConfigurationRelationshipDiagnostics("fixture.relationship-growth", ["first", "second"], relationships).definitions,
    defineConfigurationRelationshipDiagnostics("fixture.relationship-growth", ["first", "second"], relationships).definitions);
}

main()
  .then(() => {
    console.log("platform/config runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
import { defineConfigurationSourceReadDiagnostic, configurationSourceReadDiagnosticRecord } from "../src/diagnostics";
import { configSourceReadFailureReasons } from "@kanbien/core/config";
import { parseDiagnosticRecord } from "@kanbien/core/diagnostics";
const sourceDiagnostic = defineConfigurationSourceReadDiagnostic("fixture.source-unavailable", ["fixture.configuration"]);
for (const reason of configSourceReadFailureReasons) {
  const record = configurationSourceReadDiagnosticRecord(sourceDiagnostic, "fixture.configuration", reason);
  if (!parseDiagnosticRecord(sourceDiagnostic, record).ok || parseDiagnosticRecord(sourceDiagnostic, { ...record, detail: { ...record.detail, path: "/private/synthetic-secret-canary" } }).ok) throw new Error("source diagnostic contract failed");
}

const relation = { relationship: "separation", rule: "must-differ", left: "first", right: "second" } as const;
const relationshipDefinitions = defineConfigurationRelationshipDiagnostics("fixture.configuration-invalid", ["first", "second"], [relation]);
const fieldIssues = [{ setting: "first", reason: "missing" }] as const;
for (const [issues, relationshipIssues, definition, detail] of [
  [fieldIssues, [], relationshipDefinitions.fields, { issues: fieldIssues }],
  [[], [relation], relationshipDefinitions.relations, { relationshipIssues: [{ relationship: "separation", rule: "must-differ" }] }],
  [fieldIssues, [relation], relationshipDefinitions.combined, { issues: fieldIssues, relationshipIssues: [{ relationship: "separation", rule: "must-differ" }] }],
] as const) {
  const result = configurationRelationshipDiagnostic(relationshipDefinitions, { code: "CONFIGURATION_INVALID", issues, relationshipIssues });
  equal(result.ok, true);
  if (!result.ok) throw new Error("expected configuration relationship diagnostic");
  equal(result.value.code, definition.code);
  deepEqual(result.value.detail, detail);
  equal(parseDiagnosticRecord<unknown>(definition, result.value).ok, true);
  equal(parseDiagnosticRecord<unknown>(definition, { ...result.value, detail: {} }).ok, false);
  equal(parseDiagnosticRecord<unknown>(definition, { ...result.value, detail: { ...detail, rawValue: "synthetic-sensitive-canary" } }).ok, false);
  equal(parseDiagnosticRecord<unknown>(definition, { ...result.value, detail: Object.fromEntries(Object.keys(detail).map((key) => [key, []])) }).ok, false);
  for (const other of relationshipDefinitions.definitions.filter((item) => item !== definition)) {
    equal(parseDiagnosticRecord<unknown>(other, { ...result.value, code: other.code }).ok, false, "wrong family shape is rejected");
  }
}
equal(configurationRelationshipDiagnostic(relationshipDefinitions, { code: "CONFIGURATION_INVALID", issues: [], relationshipIssues: [] }).ok, false);
throws(() => configurationRelationshipDiagnostic(relationshipDefinitions, { code: "CONFIGURATION_INVALID", issues: [], relationshipIssues: [{ ...relation, right: "synthetic-sensitive-canary" }] }), /CONFIGURATION_RELATIONSHIP_ISSUE_INVALID/);
throws(() => configurationRelationshipDiagnostic(relationshipDefinitions, { code: "CONFIGURATION_INVALID", issues: [], relationshipIssues: [{ ...relation, value: "synthetic-sensitive-canary" } as typeof relation] }), /CONFIGURATION_RELATIONSHIP_ISSUE_INVALID/);
for (const issue of [{ setting: "unknown", reason: "missing" }, { setting: "first", reason: "invalid-json" }] as const) {
  equal(configurationRelationshipDiagnostic(relationshipDefinitions, { code: "CONFIGURATION_INVALID", issues: [issue], relationshipIssues: [] }).ok, false);
}
throws(() => defineConfigurationRelationshipDiagnostics("fixture.empty", ["first", "second"], []), /CONFIGURATION_RELATIONSHIP_SCHEMA_INVALID/);
throws(() => defineConfigurationRelationshipDiagnostics("fixture.invalid", ["first", "second"], [{ ...relation, right: "unknown" }]), /CONFIGURATION_RELATIONSHIP_SCHEMA_INVALID/);
throws(() => defineConfigurationRelationshipDiagnostics(`fixture.${"a".repeat(120)}`, ["first", "second"], [relation]), /DIAGNOSTIC_DEFINITION_INVALID/);

let evidenceAccessorReads = 0;
const sensitiveGetter = () => { evidenceAccessorReads += 1; throw new Error("synthetic-sensitive-canary"); };
const validEvidence = () => ({ code: "CONFIGURATION_INVALID", issues: [{ setting: "first", reason: "missing" }], relationshipIssues: [{ ...relation }] });
function rejectEvidence(value: unknown): void {
  throws(() => configurationRelationshipDiagnostic(relationshipDefinitions, value as Parameters<typeof configurationRelationshipDiagnostic>[1]),
    (error: unknown) => error instanceof TypeError && error.message === "CONFIGURATION_RELATIONSHIP_ISSUE_INVALID");
  equal(evidenceAccessorReads, 0, "rejected evidence must not execute caller accessors");
}
for (const key of ["code", "issues", "relationshipIssues"]) {
  rejectEvidence(Object.defineProperty(validEvidence(), key, { enumerable: true, get: sensitiveGetter }));
}
rejectEvidence({ ...validEvidence(), value: "synthetic-sensitive-canary" });
rejectEvidence(Object.assign(validEvidence(), { [Symbol("private")]: "synthetic-sensitive-canary" }));
rejectEvidence(Object.assign(Object.create({ private: "synthetic-sensitive-canary" }), validEvidence()));
for (const key of ["issues", "relationshipIssues"] as const) {
  const entry = key === "issues" ? { setting: "first", reason: "missing" } : { ...relation };
  const arrays: unknown[] = [Array.from({ length: 33 }, () => entry), Array(1),
    Object.defineProperty([entry], "0", { enumerable: true, get: sensitiveGetter }),
    Object.assign([entry], { value: "synthetic-sensitive-canary" }),
    Object.assign([entry], { [Symbol("private")]: "synthetic-sensitive-canary" }),
    Object.setPrototypeOf([entry], { private: "synthetic-sensitive-canary" }),
    Object.defineProperty([entry], "map", { get: sensitiveGetter }),
    Object.defineProperty([entry], "0", { enumerable: false, value: entry }),
  ];
  for (const array of arrays) rejectEvidence({ ...validEvidence(), [key]: array });
  for (const field of Object.keys(entry)) {
    rejectEvidence({ ...validEvidence(), [key]: [Object.defineProperty({ ...entry }, field, { enumerable: true, get: sensitiveGetter })] });
  }
  rejectEvidence({ ...validEvidence(), [key]: [{ ...entry, value: "synthetic-sensitive-canary" }] });
  rejectEvidence({ ...validEvidence(), [key]: [Object.assign({ ...entry }, { [Symbol("private")]: "synthetic-sensitive-canary" })] });
  rejectEvidence({ ...validEvidence(), [key]: [Object.assign(Object.create({ private: "synthetic-sensitive-canary" }), entry)] });
  let oversizedArrayTraversal = 0;
  const oversized = new Proxy(Array(33), { ownKeys: () => { oversizedArrayTraversal += 1; throw new Error("synthetic-sensitive-canary"); } });
  rejectEvidence({ ...validEvidence(), [key]: oversized });
  equal(oversizedArrayTraversal, 0, "oversized arrays reject before entry traversal");
}
equal(configurationRelationshipDiagnostic(relationshipDefinitions, {
  code: "CONFIGURATION_INVALID", issues: Array.from({ length: 32 }, () => ({ setting: "first", reason: "missing" as const })),
  relationshipIssues: Array.from({ length: 32 }, () => ({ ...relation })),
}).ok, true, "bounded maximum evidence remains accepted");
