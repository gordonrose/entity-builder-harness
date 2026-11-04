import { validationIssue, type NonEmptyValidationIssues } from "../../../validation/index";
import type { DiagnosticRecord } from "../../../diagnostics/index";
import { coreConfigPrimitiveRecord, type CoreConfigReader } from "./diagnostics";
import type { ConfigSettingIssue, ConfigRelationshipIssue } from "./setting-issues";

export type ConfigErrorCode = "CONFIG_INVALID" | "CONFIG_MISSING";

export interface ConfigError {
  readonly code: ConfigErrorCode;
  readonly issues: NonEmptyValidationIssues;
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
}

export interface ConfigSettingsFailure { readonly code: "CONFIGURATION_INVALID"; readonly issues: readonly ConfigSettingIssue[] }
export interface ConfigSettingsRelationshipFailure extends ConfigSettingsFailure {
  readonly relationshipIssues: readonly ConfigRelationshipIssue[];
}

export function configError(code: ConfigErrorCode, issues: NonEmptyValidationIssues, options: {
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
} = {}): ConfigError {
  return { code, issues,
    ...(options.diagnosticRecord === undefined ? {} : { diagnosticRecord: options.diagnosticRecord }),
    ...(options.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: options.relatedDiagnosticRecords }),
  };
}

export function missingConfigError(key: string, reader: Exclude<CoreConfigReader, "optional" | "schema">): ConfigError {
  return configError("CONFIG_MISSING", [
    validationIssue({
      path: ["config", key],
      code: "CONFIG_MISSING",
      defaultMessage: "Config value is required.",
      messageKey: "config.missing",
      params: { key },
    }),
  ], { diagnosticRecord: coreConfigPrimitiveRecord({ field: "value", reader, reason: "missing" }) });
}

export function invalidConfigTypeError(key: string, expected: string, value: unknown, reader: "string" | "number" | "boolean", reason: "wrong-type" | "non-finite" = "wrong-type"): ConfigError {
  return invalidConfigValueError(
    ["config", key],
    "CONFIG_INVALID_TYPE",
    "Config value has the wrong type.",
    "config.invalid_type",
    { key, expected, actual: configValueType(value) },
    coreConfigPrimitiveRecord({ field: "value", reader, reason }),
  );
}

export function invalidConfigValueError(
  path: readonly string[],
  code: string,
  defaultMessage: string,
  messageKey: string,
  params: Record<string, string>,
  diagnosticRecord: DiagnosticRecord,
): ConfigError {
  return configError("CONFIG_INVALID", [
    validationIssue({
      path,
      code,
      defaultMessage,
      messageKey,
      params,
    }),
  ], { diagnosticRecord });
}

function configValueType(value: unknown): string {
  if (value === null) {
    return "null";
  }

  if (typeof value === "number" && !Number.isFinite(value)) {
    return "non-finite number";
  }

  return typeof value;
}
