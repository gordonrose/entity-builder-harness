import {
  booleanConfigValue,
  configError,
  environmentName,
  recordConfigSource,
  secretReference,
  stringConfigValue,
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
