import type { JsonValue } from "@kanbien/core";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";

export type PlatformSecurityErrorCode =
  | "PLATFORM_SECURITY_UNAUTHENTICATED"
  | "PLATFORM_SECURITY_INVALID_TOKEN"
  | "PLATFORM_SECURITY_INVALID_AUTHZ_MAPPING"
  | "PLATFORM_SECURITY_FORBIDDEN"
  | "PLATFORM_SECURITY_RATE_LIMITED";

export interface PlatformSecurityError {
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
  readonly code: PlatformSecurityErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
}
