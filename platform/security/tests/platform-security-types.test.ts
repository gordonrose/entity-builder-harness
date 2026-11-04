import type { Permission } from "@kanbien/core/authz";
import {
  assertPlatformRateLimitPositiveInteger,
  securityRateLimitPositiveIntegerFailureRecord,
  authzMappingPermissions,
  authorizePlatformPermissions,
  createJwtBearerAuthenticationHook,
  createInMemoryPlatformRateLimiter,
  createPlatformSecurityHeaders,
  denyByDefaultAuthenticationResult,
  platformRateLimitKey,
  principalFromPlatformAuthenticationResult,
  type PlatformPrincipalDiagnosticOptions,
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
void platformRateLimitKey({ bearerToken: "token" });

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

const principalDiagnostics: PlatformPrincipalDiagnosticOptions = {
  onMissingAttribute(attribute) { const field: "principal-id" | "principal-type" | "subject" = attribute; void field; },
  onDiagnostic(_record, context) { const origin: "owned" | "source" = context.evidence; void origin; },
};
void principalFromPlatformAuthenticationResult(denyByDefaultAuthenticationResult, principalDiagnostics);

assertPlatformRateLimitPositiveInteger("limit", 1);
void securityRateLimitPositiveIntegerFailureRecord("bucket-capacity", 1);
if (false) {
  // @ts-expect-error Direct option names are closed, not arbitrary source keys.
  assertPlatformRateLimitPositiveInteger("PRIVATE_ENV_KEY", 1);
  // @ts-expect-error The record uses the logical field, not the direct option spelling.
  void securityRateLimitPositiveIntegerFailureRecord("windowMs", 1);
}
