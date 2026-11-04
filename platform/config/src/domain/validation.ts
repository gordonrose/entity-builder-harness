import type { ConfigError } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { createDiagnosticRecord, selectDiagnosticEvidence, deliverDiagnosticRecord, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformConfigDiagnostic, platformConfigWideDiagnostic, platformConfigThrownDiagnostic } from "../contract/diagnostics";
import type { PlatformConfigError, PlatformConfigValidationInput } from "../contract/validation";

export function validatePlatformConfigSchemas(
  input: PlatformConfigValidationInput,
): Result<readonly unknown[], PlatformConfigError> {
  const parsedValues: unknown[] = [];

  for (const [schemaIndex, schema] of input.schemas.entries()) {
    let phase: "parse" | "projection" = "parse";
    try {
      const parsed = schema.parse(input.source);
      phase = "projection";
      if (!parsed.ok) {
        const failure = parsed.error;
        const position = rejectionRecord(schemaIndex, failure);
        const error = platformConfigError(schemaIndex, failure, selectedEvidence(input, failure), position);
        if (position !== undefined) observe(input, position);
        if (error.diagnosticRecord !== undefined && error.diagnosticRecord !== position) observe(input, error.diagnosticRecord);
        for (const record of error.relatedDiagnosticRecords ?? []) observe(input, record);
        return { ok: false, error };
      }
      parsedValues.push(parsed.value);
    } catch (error) {
      const checked = createDiagnosticRecord(platformConfigThrownDiagnostic, { schemaIndex, phase, reason: "boundary-threw", effect: "result-not-returned" });
      if (checked.ok) observe(input, checked.value);
      const retained = selectedEvidence(input, error);
      if (retained.diagnosticRecord !== undefined) observe(input, retained.diagnosticRecord);
      for (const record of retained.relatedDiagnosticRecords ?? []) observe(input, record);
      throw error;
    }
  }

  return { ok: true, value: parsedValues };
}

export function assertPlatformConfigValid(
  input: PlatformConfigValidationInput,
): Result<void, PlatformConfigError> {
  const validated = validatePlatformConfigSchemas(input);

  if (!validated.ok) {
    return validated;
  }

  return { ok: true, value: undefined };
}

function rejectionRecord(schemaIndex: number, error: ConfigError): DiagnosticRecord | undefined {
  const diagnostic = createDiagnosticRecord(schemaIndex <= 65_535 ? platformConfigDiagnostic : platformConfigWideDiagnostic,
    { schemaIndex, reason: error.code === "CONFIG_MISSING" ? "missing" : "invalid" });
  return diagnostic.ok ? diagnostic.value : undefined;
}

function platformConfigError(schemaIndex: number, error: ConfigError,
  retained: ReturnType<typeof selectDiagnosticEvidence>, position: DiagnosticRecord | undefined): PlatformConfigError {
  const primary = retained.diagnosticRecord ?? position;
  return {
    code: "PLATFORM_CONFIG_INVALID",
    defaultMessage: "Platform config validation failed before runtime startup.",
    ...(primary === undefined ? {} : { diagnosticRecord: primary }),
    ...(retained.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: retained.relatedDiagnosticRecords }),
    details: {
      schemaIndex,
      configCode: error.code,
      issues: error.issues.map((issue) => ({
        path: [...issue.path],
        code: issue.code,
        defaultMessage: issue.defaultMessage,
        ...(issue.messageKey === undefined ? {} : { messageKey: String(issue.messageKey) }),
      })),
    },
  };
}

function selectedEvidence(input: PlatformConfigValidationInput, value: unknown): ReturnType<typeof selectDiagnosticEvidence> {
  try { return selectDiagnosticEvidence([...coreDiagnosticCatalog.definitions, ...(input.diagnosticDefinitions ?? [])], value); }
  catch { return {}; }
}

function observe(input: PlatformConfigValidationInput, record: DiagnosticRecord): void {
  deliverDiagnosticRecord(record, selected => input.onDiagnostic?.(selected));
}
