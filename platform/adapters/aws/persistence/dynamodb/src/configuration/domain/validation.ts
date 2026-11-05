import { configReasonNames, stringConfigValue, type ConfigValue } from "@kanbien/core/config";
import { capturePlatformPersistenceDiagnostic, persistenceConfigurationDiagnosticRecord, persistenceConfigurationInputDiagnosticRecord } from "@kanbien/platform-persistence";
import type { DynamoDbPersistenceConfiguration } from "../contract/types";
import type { DynamoDbPersistenceConfigurationError } from "../contract/errors";

const requiredFields = ["region", "tableName", "outboxDueIndexName", "lineageCauseIndexName"] as const satisfies readonly (keyof DynamoDbPersistenceConfiguration)[];

export function dynamoDbPersistenceConfiguration(
  input: DynamoDbPersistenceConfiguration,
): { readonly ok: true; readonly value: DynamoDbPersistenceConfiguration } | { readonly ok: false; readonly error: DynamoDbPersistenceConfigurationError } {
  if (typeof input !== "object" || input === null || Array.isArray(input)) {
    return inputFailure("configuration", configReasonNames.wrongShape);
  }
  // Keep the original enumeration/getter boundary. Core reads only this snapshot.
  const entries = Object.entries(input);
  const supplied = new Map<string, unknown>(entries);
  const source = { get: (key: string) => supplied.get(key) as ConfigValue | undefined };
  for (const path of requiredFields) {
    const checked = stringConfigValue(source, path);
    if (!checked.ok) return inputFailure(path, checked.error.code === "CONFIG_MISSING" ? configReasonNames.missing : configReasonNames.wrongType);
    supplied.set(path, checked.value);
  }
  for (const [path] of entries) {
    // Extra-property behaviour remains legacy; it is not a declared-input guarantee.
    if ((supplied.get(path) as string).trim().length === 0) {
      return {
        ok: false,
        error: {
          code: "PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID",
          defaultMessage: "DynamoDB persistence adapter configuration is invalid.",
          details: { path, reason: "A non-empty value is required." },
          diagnosticRecord: capturePlatformPersistenceDiagnostic(() => persistenceConfigurationDiagnosticRecord(configurationField(path), "blank")),
        },
      };
    }
  }

  let oversized: "store" | "outbox-index" | "lineage-index" | undefined;
  if (input.tableName.length > 255) oversized = "store";
  else if (input.outboxDueIndexName.length > 255) oversized = "outbox-index";
  else if (input.lineageCauseIndexName.length > 255) oversized = "lineage-index";
  if (oversized !== undefined) {
    const field = oversized;
    return {
      ok: false,
      error: {
        code: "PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID",
        defaultMessage: "DynamoDB persistence adapter configuration is invalid.",
        details: { path: oversized === "store" ? "tableName" : oversized === "outbox-index" ? "outboxDueIndexName" : "lineageCauseIndexName", reason: "Table and index names must be at most 255 characters." },
        diagnosticRecord: capturePlatformPersistenceDiagnostic(() => persistenceConfigurationDiagnosticRecord(field, "too-long")),
      },
    };
  }

  return { ok: true, value: { ...input } };
}

function configurationField(path: string): "region" | "store" | "outbox-index" | "lineage-index" | "configuration" {
  return path === "region" ? "region" : path === "tableName" ? "store" : path === "outboxDueIndexName" ? "outbox-index" : path === "lineageCauseIndexName" ? "lineage-index" : "configuration";
}

function inputFailure(path: typeof requiredFields[number] | "configuration", reason: "missing" | "wrong-type" | "wrong-shape") {
  return { ok: false as const, error: {
    code: "PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID" as const,
    defaultMessage: "DynamoDB persistence adapter configuration is invalid.",
    details: { path, reason: reason === "missing" ? "A required value is missing." : reason === "wrong-type" ? "A text value is required." : "A configuration object is required." },
    diagnosticRecord: capturePlatformPersistenceDiagnostic(() => persistenceConfigurationInputDiagnosticRecord(configurationField(path), reason)),
  } };
}
