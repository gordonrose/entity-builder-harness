import {
  principal,
  principalId,
  type Permission,
  type Principal,
  type PrincipalClaims,
  type PrincipalType,
} from "@kanbien/core";
import {
  authzMappingPermissions,
  permissionsFromClaims,
  type PlatformAuthzPermissionMapping,
} from "./authorization";
import type { PlatformJwtVerifier } from "./jwt";

export interface PlatformAuthenticationResult {
  readonly authenticated: boolean;
  readonly permissions: readonly Permission[];
  readonly principalId?: string;
  readonly principalType?: PrincipalType;
  readonly subject?: string;
  readonly claims?: PrincipalClaims;
  readonly scopes?: readonly string[];
  readonly rateLimitKey?: string;
}

export interface PlatformAuthenticationRequest {
  readonly headers?: Readonly<Record<string, string | readonly string[]>>;
}

export interface PlatformAuthenticationHook {
  authenticate(request: PlatformAuthenticationRequest): Promise<PlatformAuthenticationResult> | PlatformAuthenticationResult;
  grantedPermissions?(): readonly Permission[];
}

export interface JwtBearerAuthenticationHookOptions {
  readonly verifier: PlatformJwtVerifier;
  readonly authz: PlatformAuthzPermissionMapping;
  readonly principalType?: PrincipalType;
}

export const denyByDefaultAuthenticationResult: PlatformAuthenticationResult = {
  authenticated: false,
  permissions: [],
};

export function principalFromPlatformAuthenticationResult(
  authentication: PlatformAuthenticationResult,
): Principal | undefined {
  if (
    !authentication.authenticated
    || authentication.principalId === undefined
    || authentication.principalType === undefined
    || authentication.subject === undefined
  ) {
    return undefined;
  }

  return principal({
    id: principalId(authentication.principalId),
    type: authentication.principalType,
    subject: authentication.subject,
    claims: authentication.claims ?? {},
    scopes: authentication.scopes ?? [],
  });
}

export function createJwtBearerAuthenticationHook(
  options: JwtBearerAuthenticationHookOptions,
): PlatformAuthenticationHook {
  const granted = authzMappingPermissions(options.authz);

  return {
    grantedPermissions: () => granted,
    async authenticate(request) {
      const token = bearerTokenFromHeaders(request.headers ?? {});
      if (token === undefined) {
        return denyByDefaultAuthenticationResult;
      }

      const verified = await options.verifier.verify(token);
      if (!verified.ok) {
        return denyByDefaultAuthenticationResult;
      }

      const subject = stringClaim(verified.value.claims, "sub");
      if (subject === undefined) {
        return denyByDefaultAuthenticationResult;
      }

      const scopes = scopesFromClaims(verified.value.claims);
      return {
        authenticated: true,
        permissions: permissionsFromClaims(verified.value.claims, options.authz),
        principalId: principalId(subject),
        principalType: options.principalType ?? "user",
        subject,
        claims: verified.value.claims,
        scopes,
        rateLimitKey: `principal:${subject}`,
      };
    },
  };
}

export function bearerTokenFromHeaders(headers: Readonly<Record<string, string | readonly string[]>>): string | undefined {
  const authorization = firstHeaderValue(headers, "authorization");
  if (authorization === undefined) {
    return undefined;
  }

  const match = /^Bearer\s+(.+)$/i.exec(authorization);
  return match?.[1];
}

export function firstHeaderValue(headers: Readonly<Record<string, string | readonly string[]>>, name: string): string | undefined {
  const entry = Object.entries(headers).find(([key]) => key.toLowerCase() === name.toLowerCase());
  const value = entry?.[1];
  return typeof value === "string" ? value : value?.[0];
}

function scopesFromClaims(claims: PrincipalClaims): readonly string[] {
  const scope = stringClaim(claims, "scope");
  if (scope === undefined) {
    return [];
  }

  return scope.split(/\s+/).filter((item) => item.length > 0);
}

function stringClaim(claims: PrincipalClaims, name: string): string | undefined {
  const value = claims[name];
  return typeof value === "string" && value.length > 0 ? value : undefined;
}
