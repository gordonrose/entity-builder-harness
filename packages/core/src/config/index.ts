import { err, ok, type Result } from "../shared/index";
import { validationIssue, type NonEmptyValidationIssues, type ValidationIssue } from "../validation/index";

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
  return configError("CONFIG_INVALID", [
    validationIssue({
      path: ["config", key],
      code: "CONFIG_INVALID_TYPE",
      defaultMessage: "Config value has the wrong type.",
      messageKey: "config.invalid_type",
      params: { key, expected, actual: configValueType(value) },
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
