import type { ConfigSchema } from "@kanbien/core/config";
import { configReasonNames, recordConfigSource, type ConfigIssueReason } from "@kanbien/core/config";
import { loadPlatformConfiguration, type PlatformConfigurationLoadingInput } from "../src/index";

const loading: PlatformConfigurationLoadingInput<{ port: number }, { code: "ADAPTER_FAILURE" }> = {
  requirements: [{ setting: "port", rule: { kind: "integer", minimum: 1, maximum: 65535 } }],
  bindings: { port: "PORT" }, source: recordConfigSource({ PORT: "443" }),
  assemble: values => ({ ok: true, value: { port: values["port"] as number } }),
};
const loaded = loadPlatformConfiguration(loading);
if (loaded.ok) { const port: number = loaded.value.port; void port; }
// @ts-expect-error source bindings must name a source, not supply a value object.
loadPlatformConfiguration({ ...loading, bindings: { port: { value: "443" } } });
// @ts-expect-error assembly must return a checked result.
loadPlatformConfiguration({ ...loading, assemble: () => ({ port: 443 }) });
import { assertPlatformConfigValid, validatePlatformConfigSchemas, defineConfigurationRelationshipDiagnostics, configurationRelationshipDiagnostic } from "../src/index";

const namedReason: ConfigIssueReason = configReasonNames.missing;
void namedReason;

const schema: ConfigSchema<{ readonly enabled: boolean }> = {
  parse: () => ({ ok: true, value: { enabled: true } }),
};

const result = validatePlatformConfigSchemas({
  source: recordConfigSource({ ENABLED: true }),
  schemas: [schema],
});
if (result.ok) {
  const values: readonly unknown[] = result.value;
  void values;
}

assertPlatformConfigValid({ source: recordConfigSource({}), schemas: [] });
validatePlatformConfigSchemas({ source: recordConfigSource({}), schemas: [schema], diagnosticDefinitions: [],
  onDiagnostic(record) { const code: string = record.code; void code; return Promise.resolve(); } });
// @ts-expect-error diagnostic definitions must be actual closed definitions.
validatePlatformConfigSchemas({ source: recordConfigSource({}), schemas: [], diagnosticDefinitions: [{ code: "fixture.unchecked" }] });

// @ts-expect-error schemas must implement ConfigSchema
validatePlatformConfigSchemas({ source: recordConfigSource({}), schemas: [{}] });

const relation = { relationship: "separation", rule: "must-differ", left: "first", right: "second" } as const;
const definitions = defineConfigurationRelationshipDiagnostics("fixture.configuration-invalid", ["first", "second"], [relation]);
const record = configurationRelationshipDiagnostic(definitions, { code: "CONFIGURATION_INVALID", issues: [], relationshipIssues: [relation] });
if (record.ok) {
  const code: string = record.value.code;
  void code;
}
// @ts-expect-error undeclared relationship kinds are not supported
defineConfigurationRelationshipDiagnostics("fixture.invalid", ["first", "second"], [{ ...relation, rule: "must-match" }]);
// @ts-expect-error relationship evidence must carry logical participants
configurationRelationshipDiagnostic(definitions, { code: "CONFIGURATION_INVALID", issues: [], relationshipIssues: [{ relationship: "separation", rule: "must-differ" }] });
