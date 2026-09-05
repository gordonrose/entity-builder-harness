import type { Permission } from "@kanbien/core/authz";
import type { JsonValue } from "@kanbien/core/shared";

export type PlatformRegistrationKind = "app" | "route" | "permission" | "job" | "health" | "config";

export type PlatformContractErrorCode =
  | "PLATFORM_CONTRACT_INVALID_NAME"
  | "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION"
  | "PLATFORM_CONTRACT_RESERVED_PATH"
  | "PLATFORM_CONTRACT_UNKNOWN_PERMISSION"
  | "PLATFORM_CONTRACT_NAMESPACE_MISMATCH"
  | "PLATFORM_CONTRACT_MALFORMED_PERMISSION"
  | "PLATFORM_CONTRACT_MALFORMED_ROUTE"
  | "PLATFORM_CONTRACT_MALFORMED_JOB";

export interface PlatformContractError {
  readonly code: PlatformContractErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
}

export function duplicatePlatformRegistration(kind: PlatformRegistrationKind, key: string): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION",
    defaultMessage: `Duplicate platform ${kind} registration.`,
    details: { kind, key },
  };
}

export function reservedPlatformPath(path: string, reservedPath: string): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_RESERVED_PATH",
    defaultMessage: "Route path uses a reserved platform path.",
    details: { path, reservedPath },
  };
}

export function unknownPlatformPermission(permission: Permission, declaredPermissions: readonly Permission[]): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_UNKNOWN_PERMISSION",
    defaultMessage: "Route references a permission that has not been declared.",
    details: { permission, declaredPermissions: [...declaredPermissions] },
  };
}

export function platformRegistrationNamespaceMismatch(
  kind: PlatformRegistrationKind,
  appId: string,
  name: string,
): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_NAMESPACE_MISMATCH",
    defaultMessage: "Platform registration name does not belong to the mounting app namespace.",
    details: { kind, appId, name },
  };
}

export function malformedPlatformPermission(reason: string, details?: Readonly<Record<string, JsonValue>>): PlatformContractError {
  return platformContractError("PLATFORM_CONTRACT_MALFORMED_PERMISSION", reason, details);
}

export function malformedPlatformRoute(reason: string, details?: Readonly<Record<string, JsonValue>>): PlatformContractError {
  return platformContractError("PLATFORM_CONTRACT_MALFORMED_ROUTE", reason, details);
}

export function malformedPlatformJob(reason: string, details?: Readonly<Record<string, JsonValue>>): PlatformContractError {
  return platformContractError("PLATFORM_CONTRACT_MALFORMED_JOB", reason, details);
}

export function invalidContractName(label: string, value: unknown): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_INVALID_NAME",
    defaultMessage: `${label} must use dot-separated lowercase segments.`,
    details: { value: stringifyDetail(value) },
  };
}

function platformContractError(
  code: PlatformContractErrorCode,
  defaultMessage: string,
  details?: Readonly<Record<string, JsonValue>>,
): PlatformContractError {
  return {
    code,
    defaultMessage,
    ...(details === undefined ? {} : { details }),
  };
}

function stringifyDetail(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }

  return String(value);
}
