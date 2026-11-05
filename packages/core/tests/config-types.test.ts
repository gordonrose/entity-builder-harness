import {
  booleanConfigValue,
  configError,
  configReasonNames,
  environmentName,
  recordConfigSource,
  secretReference,
  stringConfigValue,
  validateConfigSettings,
  validateConfigRequirements,
  type ConfigSettingRequirement,
  createConfigIssueCollector,
  destinationPortConstraint,
  coreConfigDiagnosticCatalog,
  type ConfigRelationshipIssue,
  type ConfigIssueReason,
  type ConfigSettingRelationship,
  type ConfigError,
  type ConfigRecord,
  type ConfigSchema,
  type ConfigSource,
  type ConfigValue,
  type EnvironmentName,
  type SecretReference,
} from "../src/config/index";
import { isOk, type Result } from "../src/shared/index";
import { validationIssue } from "../src/validation/index";

const values: ConfigRecord = {
  API_URL: "https://api.example.test",
  RETRY_LIMIT: 3,
  FEATURE_ENABLED: true,
  EMPTY_VALUE: null,
  MISSING: undefined,
};

const source: ConfigSource = recordConfigSource(values);
const configCatalogueOwner: "core.config" = coreConfigDiagnosticCatalog.owner;
void configCatalogueOwner;
if (false) {
  // @ts-expect-error callers cannot replace the module's selected definition set.
  coreConfigDiagnosticCatalog.definitions = [];
}
const reusable: ConfigSettingRequirement = { setting: "database.port", rule: destinationPortConstraint };
const choice: ConfigSettingRequirement = { setting: "operation", rule: { kind: "choice", values: ["apply"] } };
validateConfigRequirements(source, [choice]);
const unsupportedReason: ConfigIssueReason = configReasonNames.unsupportedValue;
void unsupportedReason;
// @ts-expect-error permitted choices are text, not arbitrary values.
const wrongChoices: ConfigSettingRequirement = { setting: "operation", rule: { kind: "choice", values: [1] } };
void wrongChoices;
validateConfigRequirements(source, [reusable]);
// @ts-expect-error configuration instructions do not accept arbitrary checking kinds.
const invalidRequirement: ConfigSettingRequirement = { setting: "database.port", rule: { kind: "service-specific" } };
void invalidRequirement;
validateConfigSettings(source, [{ setting: "database.port", source: "PORT", rule: destinationPortConstraint }]);
function destinationPortCompileOnly(): void {
  // @ts-expect-error the shared lower bound is readonly.
  destinationPortConstraint.minimum = 0;
  // @ts-expect-error the shared upper bound is readonly.
  destinationPortConstraint.maximum = 70_000;
  // @ts-expect-error consumers cannot change the shared checking kind.
  destinationPortConstraint.kind = "text";
}
void destinationPortCompileOnly;
const namedReason: ConfigIssueReason = configReasonNames.invalidJson;
void namedReason;
if (false) {
  // @ts-expect-error available names are an immutable code-owned contract.
  configReasonNames.missing = "changed";
  // @ts-expect-error a name not declared by Core is not a general configuration reason.
  const unknownReason: ConfigIssueReason = "fixture-future-reason";
  void unknownReason;
}
const optionalValue: ConfigValue | undefined = source.get("API_URL");
void optionalValue;

const environmentResult: Result<EnvironmentName, ConfigError> = environmentName("staging");
const secretReferenceResult: Result<SecretReference, ConfigError> = secretReference("kanbien/staging/api-token");
void environmentResult;
void secretReferenceResult;

const parsedString: Result<string, ConfigError> = stringConfigValue(source, "API_URL");
if (isOk(parsedString)) {
  const apiUrl: string = parsedString.value;
  void apiUrl;
}

const parsedBoolean: Result<boolean, ConfigError> = booleanConfigValue(source, "FEATURE_ENABLED");
void parsedBoolean;

const schema: ConfigSchema<{ readonly apiUrl: string }> = {
  parse(input) {
    const apiUrl = stringConfigValue(input, "API_URL");

    if (!apiUrl.ok) {
      return apiUrl;
    }

    return { ok: true, value: { apiUrl: apiUrl.value } };
  },
};
void schema;

const issue = validationIssue({
  path: ["config", "API_URL"],
  code: "CONFIG_CUSTOM",
  defaultMessage: "Config value is invalid.",
});
const acceptedError: ConfigError = configError("CONFIG_INVALID", [issue]);
void acceptedError;

// @ts-expect-error config records only carry primitive config values.
recordConfigSource({ BAD_VALUE: { nested: true } });

// @ts-expect-error config errors must carry at least one validation issue.
configError("CONFIG_INVALID", []);

// @ts-expect-error config values must not carry provider-specific objects.
const rejectedValue: ConfigValue = new Date();
void rejectedValue;

// @ts-expect-error environment names must be explicitly created and branded.
const rejectedEnvironmentName: EnvironmentName = "staging";
void rejectedEnvironmentName;

// @ts-expect-error secret references must be explicitly created and branded.
const rejectedSecretReference: SecretReference = "kanbien/staging/api-token";
void rejectedSecretReference;

const relationSettings = [{ setting: "left", source: "LEFT", rule: { kind: "text" } }, { setting: "right", source: "RIGHT", rule: { kind: "text" } }] as const;
const relation = { relationship: "separation", rule: "must-differ", left: "left", right: "right" } as const satisfies ConfigSettingRelationship<"left" | "right">;
const relationshipResult = validateConfigSettings(source, relationSettings, [relation]);
if (!relationshipResult.ok) {
  const issues: readonly ConfigRelationshipIssue[] = relationshipResult.error.relationshipIssues;
  void issues;
  // @ts-expect-error failed configuration does not expose parsed values
  relationshipResult.value;
}
const legacyResult = validateConfigSettings(source, relationSettings);
if (!legacyResult.ok) {
  // @ts-expect-error old calls retain the historical failure contract
  legacyResult.error.relationshipIssues;
}
// @ts-expect-error relationship references must belong to the declared setting tuple
validateConfigSettings(source, relationSettings, [{ ...relation, right: "unknown" }]);
// @ts-expect-error no speculative relationship rules
validateConfigSettings(source, relationSettings, [{ ...relation, rule: "must-match" }]);
const issueCollector = createConfigIssueCollector<"missing" | "duplicate">();
issueCollector.add({ setting: "fixture.setting", reason: "duplicate", index: 1, relatedIndex: 0 });
// @ts-expect-error the caller-selected reason vocabulary is closed
issueCollector.add({ setting: "fixture.setting", reason: "invented" });
// @ts-expect-error issues never contain submitted values
issueCollector.add({ setting: "fixture.setting", reason: "missing", value: "private" });
