import type { Permission } from "@kanbien/core/authz";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformContractDiagnosticRecord, type PlatformContractDiagnosticField } from "./registration-diagnostics";
import type { JsonValue } from "@kanbien/core/shared";

export type PlatformRegistrationKind = "app" | "route" | "permission" | "job" | "health" | "config" | "observability-profile" | "diagnostic-catalog";

export type PlatformContractErrorCode =
  | "PLATFORM_CONTRACT_MALFORMED_DIAGNOSTIC_CATALOG"
  | "PLATFORM_CONTRACT_INVALID_NAME"
  | "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION"
  | "PLATFORM_CONTRACT_RESERVED_PATH"
  | "PLATFORM_CONTRACT_UNKNOWN_PERMISSION"
  | "PLATFORM_CONTRACT_NAMESPACE_MISMATCH"
  | "PLATFORM_CONTRACT_MALFORMED_PERMISSION"
  | "PLATFORM_CONTRACT_MALFORMED_ROUTE"
  | "PLATFORM_CONTRACT_MALFORMED_JOB"
  | "PLATFORM_CONTRACT_MALFORMED_OBSERVABILITY_PROFILE"
  | "PLATFORM_CONTRACT_UNKNOWN_OBSERVABILITY_PROFILE";

export interface PlatformContractError {
  readonly code: PlatformContractErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
}

export function duplicatePlatformRegistration(kind: PlatformRegistrationKind, key: string, dimension: "duplicate-name" | "duplicate-route-key" | "duplicate-message-type" | "duplicate-permission" | "duplicate-identity" = "duplicate-identity"): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION",
    defaultMessage: `Duplicate platform ${kind} registration.`,
    details: { kind, key },
    diagnosticRecord: platformContractDiagnosticRecord(kind, "identity", dimension, "registration"),
  };
}

export function reservedPlatformPath(path: string, reservedPath: string): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_RESERVED_PATH",
    defaultMessage: "Route path uses a reserved platform path.",
    details: { path, reservedPath },
    diagnosticRecord: platformContractDiagnosticRecord("route", "path", "reserved-path"),
  };
}

export function unknownPlatformPermission(permission: Permission, declaredPermissions: readonly Permission[], field: PlatformContractDiagnosticField = "permission"): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_UNKNOWN_PERMISSION",
    defaultMessage: "Route references a permission that has not been declared.",
    details: { permission, declaredPermissions: [...declaredPermissions] },
    diagnosticRecord: platformContractDiagnosticRecord("route", field, "undeclared-permission", "resolution"),
  };
}

export function unknownPlatformObservabilityProfile(
  profile: string,
  declaredProfiles: readonly string[],
  registration: "route" | "job" | "identifier" = "identifier",
): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_UNKNOWN_OBSERVABILITY_PROFILE",
    defaultMessage: "Route or job references an observability profile that has not been declared.",
    details: { profile, declaredProfiles: [...declaredProfiles] },
    diagnosticRecord: platformContractDiagnosticRecord(registration, "observability", "undeclared-profile", "resolution"),
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
    diagnosticRecord: platformContractDiagnosticRecord(kind, "name", "namespace-mismatch", "registration"),
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

export function malformedPlatformObservabilityProfile(
  reason: string,
  details?: Readonly<Record<string, JsonValue>>,
): PlatformContractError {
  return platformContractError("PLATFORM_CONTRACT_MALFORMED_OBSERVABILITY_PROFILE", reason, details);
}

export function invalidContractName(label: string, value: unknown): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_INVALID_NAME",
    defaultMessage: `${label} must use dot-separated lowercase segments.`,
    details: { value: stringifyDetail(value) },
    diagnosticRecord: platformContractDiagnosticRecord("identifier", "name", typeof value === "string" ? "invalid-format" : "string-required"),
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
    diagnosticRecord: platformContractDiagnosticRecord(
      code === "PLATFORM_CONTRACT_MALFORMED_ROUTE" ? "route" : code === "PLATFORM_CONTRACT_MALFORMED_JOB" ? "job" : code === "PLATFORM_CONTRACT_MALFORMED_PERMISSION" ? "permission" : "observability-profile",
      "declaration", "declaration-rejected"),
  };
}

function stringifyDetail(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }

  return String(value);
}
