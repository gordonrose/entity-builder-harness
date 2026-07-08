import { brand, err, ok, type Brand, type Result } from "../shared/index";
import { validationIssue, type NonEmptyValidationIssues, type ValidationIssue } from "../validation/index";

export type EnvironmentName = Brand<string, "EnvironmentName">;
export type SecretReference = Brand<string, "SecretReference">;
export type ConfigValue = string | number | boolean | null;
export type ConfigRecord = Readonly<Record<string, ConfigValue | undefined>>;
export type ConfigErrorCode = "CONFIG_INVALID" | "CONFIG_MISSING";

export interface ConfigSource {
  get(key: string): ConfigValue | undefined;
}

export interface ConfigSchema<TConfig> {
  parse(source: ConfigSource): Result<TConfig, ConfigError>;
}

export interface ConfigError {
  readonly code: ConfigErrorCode;
  readonly issues: NonEmptyValidationIssues;
}

export function recordConfigSource(values: ConfigRecord): ConfigSource {
  const snapshot = { ...values };

  return {
    get: (key) => snapshot[key],
  };
}

export function configError(code: ConfigErrorCode, issues: NonEmptyValidationIssues): ConfigError {
  return { code, issues };
}

export function environmentName(value: string): Result<EnvironmentName, ConfigError> {
  if (!environmentNamePattern.test(value)) {
    return err(
      invalidConfigValueError(
        ["config", "environment"],
        "CONFIG_INVALID_ENVIRONMENT_NAME",
        "Environment name must use lowercase words separated by hyphens.",
        "config.environment.invalid",
        { value },
      ),
    );
  }

  return ok(brand<string, "EnvironmentName">(value));
}

export function secretReference(value: string): Result<SecretReference, ConfigError> {
  if (!secretReferencePattern.test(value)) {
    return err(
      invalidConfigValueError(
        ["config", "secret"],
        "CONFIG_INVALID_SECRET_REFERENCE",
        "Secret reference must be a trimmed provider-neutral key or path.",
        "config.secret_reference.invalid",
        { value },
      ),
    );
  }

  return ok(brand<string, "SecretReference">(value));
}

export function requiredConfigValue(source: ConfigSource, key: string): Result<ConfigValue, ConfigError> {
  const value = source.get(key);

  if (value === undefined) {
    return err(missingConfigError(key));
  }

  return ok(value);
}

export function optionalConfigValue(source: ConfigSource, key: string): ConfigValue | undefined {
  return source.get(key);
}

export function stringConfigValue(source: ConfigSource, key: string): Result<string, ConfigError> {
  const value = requiredConfigValue(source, key);

  if (!value.ok) {
    return value;
  }

  if (typeof value.value !== "string") {
    return err(invalidConfigTypeError(key, "string", value.value));
  }

  return ok(value.value);
}

export function numberConfigValue(source: ConfigSource, key: string): Result<number, ConfigError> {
  const value = requiredConfigValue(source, key);

  if (!value.ok) {
    return value;
  }

  if (typeof value.value !== "number" || !Number.isFinite(value.value)) {
    return err(invalidConfigTypeError(key, "finite number", value.value));
  }

  return ok(value.value);
}

export function booleanConfigValue(source: ConfigSource, key: string): Result<boolean, ConfigError> {
  const value = requiredConfigValue(source, key);

  if (!value.ok) {
    return value;
  }

  if (typeof value.value !== "boolean") {
    return err(invalidConfigTypeError(key, "boolean", value.value));
  }

  return ok(value.value);
}

function missingConfigError(key: string): ConfigError {
  return configError("CONFIG_MISSING", [
    validationIssue({
      path: ["config", key],
      code: "CONFIG_MISSING",
      defaultMessage: "Config value is required.",
      messageKey: "config.missing",
      params: { key },
    }),
  ]);
}

function invalidConfigTypeError(key: string, expected: string, value: ConfigValue): ConfigError {
  return invalidConfigValueError(
    ["config", key],
    "CONFIG_INVALID_TYPE",
    "Config value has the wrong type.",
    "config.invalid_type",
    { key, expected, actual: configValueType(value) },
  );
}

function invalidConfigValueError(
  path: readonly string[],
  code: string,
  defaultMessage: string,
  messageKey: string,
  params: Record<string, string>,
): ConfigError {
  return configError("CONFIG_INVALID", [
    validationIssue({
      path,
      code,
      defaultMessage,
      messageKey,
      params,
    }),
  ]);
}

function configValueType(value: ConfigValue): string {
  if (value === null) {
    return "null";
  }

  if (typeof value === "number" && !Number.isFinite(value)) {
    return "non-finite number";
  }

  return typeof value;
}

const environmentNamePattern = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;
const secretReferencePattern = /^[A-Za-z0-9][A-Za-z0-9._:/-]*$/;
