import type { Permission } from "@kanbien/core/authz";
import {
  authzMappingPermissions,
  authorizePlatformPermissions,
  createJwtBearerAuthenticationHook,
  createInMemoryPlatformRateLimiter,
  createPlatformSecurityHeaders,
  denyByDefaultAuthenticationResult,
  platformRateLimitKey,
  type PlatformAuthzPermissionMapping,
  type PlatformJwtVerifier,
} from "../src/index";

const permission = "smoke:read" as Permission;
const decision = authorizePlatformPermissions([permission], denyByDefaultAuthenticationResult.permissions);
if (!decision.ok) {
  void decision.error.code;
}

const headers: Readonly<Record<string, string>> = createPlatformSecurityHeaders();
void headers;

const limiter = createInMemoryPlatformRateLimiter({ limit: 1, windowMs: 1000 });
void limiter.check("client").allowed;

const authz: PlatformAuthzPermissionMapping = {
  valueClaims: [{ claim: "roles", format: "string-array", values: { admins: [permission] } }],
};
void authzMappingPermissions(authz);
void platformRateLimitKey({ headers: { authorization: "Bearer token" } });

const verifier: PlatformJwtVerifier = {
  verify: async () => ({
    ok: true,
    value: {
      header: { alg: "RS256" },
      claims: { sub: "subject", exp: 1, iss: "issuer", kind: "access" },
    },
  }),
};
const hook = createJwtBearerAuthenticationHook({ verifier, authz });
void hook.grantedPermissions?.();

// @ts-expect-error permissions must use core Permission values
authorizePlatformPermissions([1], []);

const invalidAuthz: PlatformAuthzPermissionMapping = {
  // @ts-expect-error authz maps must grant core Permission values
  valueClaims: [{ claim: "roles", format: "string-array", values: { admins: [1] } }],
};
void invalidAuthz;
