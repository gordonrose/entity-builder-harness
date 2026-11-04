import { brand, err, ok, type Result } from "../../../shared/index";
import { coreConfigPrimitiveRecord, type CoreConfigReader } from "../../contract/reporting/diagnostics";
import { missingConfigError, invalidConfigTypeError, invalidConfigValueError, type ConfigError } from "../../contract/reporting/errors";
import { readConfigSource } from "./source";
import type { EnvironmentName, SecretReference, ConfigValue, ConfigSource } from "../../contract/types";

export function environmentName(value: string): Result<EnvironmentName, ConfigError> {
  if (!environmentNamePattern.test(value)) {
    return err(
      invalidConfigValueError(
        ["config", "environment"],
        "CONFIG_INVALID_ENVIRONMENT_NAME",
        "Environment name must use lowercase words separated by hyphens.",
        "config.environment.invalid",
        { value },
        coreConfigPrimitiveRecord({ field: "environment-name", reader: "environment-name", reason: value === "" ? "empty" : "invalid-format" }),
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
        coreConfigPrimitiveRecord({ field: "secret-reference", reader: "secret-reference", reason: value === "" ? "empty" : "invalid-format" }),
      ),
    );
  }

  return ok(brand<string, "SecretReference">(value));
}

export function requiredConfigValue(source: ConfigSource, key: string): Result<ConfigValue, ConfigError> {
  return readRequiredConfigValue(source, key, "required");
}

function readRequiredConfigValue(source: ConfigSource, key: string, reader: Exclude<CoreConfigReader, "optional" | "schema">): Result<ConfigValue, ConfigError> {
  const value = readConfigSource(source, key, reader);

  if (value === undefined) {
    return err(missingConfigError(key, reader));
  }

  return ok(value);
}

export function optionalConfigValue(source: ConfigSource, key: string): ConfigValue | undefined {
  return readConfigSource(source, key, "optional");
}

export function stringConfigValue(source: ConfigSource, key: string): Result<string, ConfigError> {
  const value = readRequiredConfigValue(source, key, "string");

  if (!value.ok) {
    return value;
  }

  if (typeof value.value !== "string") {
    return err(invalidConfigTypeError(key, "string", value.value, "string"));
  }

  return ok(value.value);
}

export function numberConfigValue(source: ConfigSource, key: string): Result<number, ConfigError> {
  const value = readRequiredConfigValue(source, key, "number");

  if (!value.ok) {
    return value;
  }

  if (typeof value.value !== "number") {
    return err(invalidConfigTypeError(key, "finite number", value.value, "number"));
  }
  if (!Number.isFinite(value.value)) {
    return err(invalidConfigTypeError(key, "finite number", value.value, "number", "non-finite"));
  }

  return ok(value.value);
}

export function booleanConfigValue(source: ConfigSource, key: string): Result<boolean, ConfigError> {
  const value = readRequiredConfigValue(source, key, "boolean");

  if (!value.ok) {
    return value;
  }

  if (typeof value.value !== "boolean") {
    return err(invalidConfigTypeError(key, "boolean", value.value, "boolean"));
  }

  return ok(value.value);
}

const environmentNamePattern = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;

const secretReferencePattern = /^[A-Za-z0-9][A-Za-z0-9._:/-]*$/;
