import { deepEqual, equal } from "node:assert/strict";
import { isErr, isOk } from "../src/shared/index";
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
} from "../src/config/index";
import { validationIssue } from "../src/validation/index";

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

console.log("packages/core config runtime test passed.");
