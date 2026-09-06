import type { Permission, PrincipalClaims, Result } from "@kanbien/core";
import type { PlatformSecurityError } from "./errors";

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
      },
    };
  }

  return { ok: true, value: undefined };
}

export function permissionsFromClaims(
  claims: PrincipalClaims,
  mapping: PlatformAuthzPermissionMapping,
): readonly Permission[] {
  const permissions = new Set<Permission>();

  for (const valueClaim of mapping.valueClaims ?? []) {
    for (const value of valuesFromClaim(claims, valueClaim.claim, valueClaim.format)) {
      for (const permission of valueClaim.values[value] ?? []) {
        permissions.add(permission);
      }
    }
  }

  for (const claimMapping of mapping.claims ?? []) {
    if (claims[claimMapping.claim] !== claimMapping.equals) {
      continue;
    }

    for (const permission of claimMapping.permissions) {
      permissions.add(permission);
    }
  }

  return [...permissions];
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
