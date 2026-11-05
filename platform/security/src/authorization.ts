import type { Permission, PrincipalClaims, Result } from "@kanbien/core";
import type { PlatformSecurityError } from "./errors";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { securityOperationDiagnosticRecord } from "./diagnostics";

export interface PlatformAuthzPermissionMapping {
  readonly valueClaims?: readonly PlatformClaimValuePermissionMapping[];
  readonly claims?: readonly PlatformClaimPermissionMapping[];
}

export interface PlatformClaimValuePermissionMapping {
  readonly claim: string;
  readonly format: "string-array" | "space-delimited";
  readonly values: Readonly<Record<string, readonly Permission[]>>;
}

export interface PlatformClaimPermissionMapping {
  readonly claim: string;
  readonly equals: string | number | boolean;
  readonly permissions: readonly Permission[];
}

export function authorizePlatformPermissions(
  required: readonly Permission[],
  actual: readonly Permission[],
): Result<void, PlatformSecurityError> {
  const missingPermission = required.find((permission) => !actual.includes(permission));
  if (missingPermission !== undefined) {
    return {
      ok: false,
      error: {
        code: "PLATFORM_SECURITY_FORBIDDEN",
        defaultMessage: "A required route permission is missing.",
        details: { permission: missingPermission },
        diagnosticRecord: securityOperationDiagnosticRecord("authorization", "permission-missing", { referenceIndex: required.indexOf(missingPermission) }),
      },
    };
  }

  return { ok: true, value: undefined };
}

export function permissionsFromClaims(
  claims: PrincipalClaims,
  mapping: PlatformAuthzPermissionMapping,
): readonly Permission[] {
  return observePermissionsFromClaims(claims, mapping).permissions;
}

export function observePermissionsFromClaims(claims: PrincipalClaims, mapping: PlatformAuthzPermissionMapping): { readonly permissions: readonly Permission[]; readonly relatedDiagnosticRecords: readonly DiagnosticRecord[] } {
  const permissions = new Set<Permission>();
  const records: DiagnosticRecord[] = [];
  let omitted = 0;
  const record = (reason: "claim-missing" | "claim-wrong-type" | "claim-empty" | "claim-unmapped" | "claim-mismatch", referenceIndex: number) => {
    if (records.length < 7) records.push(securityOperationDiagnosticRecord("authorization", reason, { referenceIndex }));
    else omitted++;
  };

  for (const [referenceIndex, valueClaim] of (mapping.valueClaims ?? []).entries()) {
    const raw = claims[valueClaim.claim];
    const values = valuesFromClaim(claims, valueClaim.claim, valueClaim.format);
    if (raw === undefined) record("claim-missing", referenceIndex);
    else if (valueClaim.format === "string-array" ? !Array.isArray(raw) || raw.some((value) => typeof value !== "string") : typeof raw !== "string") record("claim-wrong-type", referenceIndex);
    else if (values.length === 0) record("claim-empty", referenceIndex);
    for (const value of values) {
      if (valueClaim.values[value] === undefined) record("claim-unmapped", referenceIndex);
      for (const permission of valueClaim.values[value] ?? []) {
        permissions.add(permission);
      }
    }
  }

  for (const [index, claimMapping] of (mapping.claims ?? []).entries()) {
    if (claims[claimMapping.claim] !== claimMapping.equals) {
      const raw = claims[claimMapping.claim];
      record(raw === undefined ? "claim-missing" : typeof raw !== typeof claimMapping.equals ? "claim-wrong-type" : "claim-mismatch", (mapping.valueClaims?.length ?? 0) + index);
      continue;
    }

    for (const permission of claimMapping.permissions) {
      permissions.add(permission);
    }
  }

  if (omitted > 0) records.push(securityOperationDiagnosticRecord("authorization", "additional-observations-omitted", { omittedCount: omitted }));
  return { permissions: [...permissions], relatedDiagnosticRecords: records };
}

export function authzMappingPermissions(mapping: PlatformAuthzPermissionMapping): readonly Permission[] {
  const permissions = new Set<Permission>();

  for (const valueClaim of mapping.valueClaims ?? []) {
    for (const permissionList of Object.values(valueClaim.values)) {
      for (const permission of permissionList) {
        permissions.add(permission);
      }
    }
  }

  for (const claimMapping of mapping.claims ?? []) {
    for (const permission of claimMapping.permissions) {
      permissions.add(permission);
    }
  }

  return [...permissions];
}

export function validateAuthzMappingPermissions(
  mapping: PlatformAuthzPermissionMapping,
  declaredPermissions: readonly Permission[],
): Result<void, PlatformSecurityError> {
  const unknown = authzMappingPermissions(mapping).filter((permission) => !declaredPermissions.includes(permission));
  if (unknown.length > 0) {
    return {
      ok: false,
      error: {
        code: "PLATFORM_SECURITY_INVALID_AUTHZ_MAPPING",
        defaultMessage: "Authz mapping grants permissions that were not declared by mounted apps.",
        details: {
          permissions: unknown,
          declaredPermissions: [...declaredPermissions],
        },
        diagnosticRecord: securityOperationDiagnosticRecord("authorization", "undeclared-permission", { referenceIndex: authzMappingPermissions(mapping).indexOf(unknown[0]!) }),
      },
    };
  }

  return { ok: true, value: undefined };
}

function valuesFromClaim(
  claims: PrincipalClaims,
  name: string,
  format: PlatformClaimValuePermissionMapping["format"],
): readonly string[] {
  const value = claims[name];
  if (format === "string-array") {
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
  }

  return typeof value === "string" ? value.split(/\s+/).filter((item) => item.length > 0) : [];
}
