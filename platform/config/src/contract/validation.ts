import type { ConfigSchema, ConfigSource } from "@kanbien/core/config";
import type { JsonValue } from "@kanbien/core/shared";
import type { DiagnosticDefinition, DiagnosticRecord } from "@kanbien/core/diagnostics";

export type PlatformConfigErrorCode = "PLATFORM_CONFIG_INVALID";

export interface PlatformConfigError {
  readonly code: PlatformConfigErrorCode;
  readonly defaultMessage: string;
  readonly details: Readonly<Record<string, JsonValue>>;
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
}

export interface PlatformConfigValidationInput {
  readonly source: ConfigSource;
  readonly schemas: readonly ConfigSchema<unknown>[];
  /** Selected app/capability definitions; Core definitions are always known. */
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  /** Independent internal observation; never awaited and never changes parsing. */
  readonly onDiagnostic?: (record: DiagnosticRecord) => unknown;
}
