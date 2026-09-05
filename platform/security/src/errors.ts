import type { JsonValue } from "@kanbien/core";

export type PlatformSecurityErrorCode =
  | "PLATFORM_SECURITY_UNAUTHENTICATED"
  | "PLATFORM_SECURITY_INVALID_TOKEN"
  | "PLATFORM_SECURITY_INVALID_AUTHZ_MAPPING"
  | "PLATFORM_SECURITY_FORBIDDEN"
  | "PLATFORM_SECURITY_RATE_LIMITED";

export interface PlatformSecurityError {
  readonly code: PlatformSecurityErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
}
