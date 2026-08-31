import { deepEqual, equal, match } from "node:assert/strict";
import { createSign, generateKeyPairSync } from "node:crypto";
import type { Permission } from "@kanbien/core/authz";
import { fixedClock } from "@kanbien/core/shared";
import {
  authzMappingPermissions,
  authorizePlatformPermissions,
  corsPolicyForOrigin,
  createInMemoryPlatformRateLimiter,
  createJwtBearerAuthenticationHook,
  createJwksJwtVerifier,
  createPlatformSecurityHeaders,
  denyByDefaultAuthenticationResult,
  permissionsFromClaims,
  platformRateLimitKey,
  platformRateLimitError,
  validateAuthzMappingPermissions,
  type PlatformJsonWebKey,
} from "../src/index";

async function main(): Promise<void> {
  const defaultHeaders = createPlatformSecurityHeaders();
  equal(defaultHeaders["x-content-type-options"], "nosniff");
  equal(defaultHeaders["x-frame-options"], "DENY");
  equal(defaultHeaders["access-control-allow-origin"], undefined);

  const corsHeaders = createPlatformSecurityHeaders({
    cors: corsPolicyForOrigin("https://app.example.test"),
  });
  equal(corsHeaders["access-control-allow-origin"], "https://app.example.test");
  equal(corsHeaders["access-control-allow-headers"], "authorization, content-type, x-request-id");

  equal(denyByDefaultAuthenticationResult.authenticated, false);
  equal(denyByDefaultAuthenticationResult.permissions.length, 0);

  const permission = "smoke:read" as Permission;
  equal(authorizePlatformPermissions([permission], [permission]).ok, true);
  const forbidden = authorizePlatformPermissions([permission], []);
  equal(forbidden.ok, false);
  if (!forbidden.ok) {
    equal(forbidden.error.code, "PLATFORM_SECURITY_FORBIDDEN");
    equal(forbidden.error.details?.["permission"], permission);
  }

  const limiter = createInMemoryPlatformRateLimiter({
    limit: 2,
    windowMs: 1000,
    clock: fixedClock(new Date("2026-07-10T00:00:00.000Z")),
  });
  equal(limiter.check("client").allowed, true);
  equal(limiter.check("client").allowed, true);
  const limited = limiter.check("client");
  equal(limited.allowed, false);
  equal(limited.retryAfterMs, 1000);
  equal(platformRateLimitError(limited.retryAfterMs).code, "PLATFORM_SECURITY_RATE_LIMITED");

  const rateLimitKey = platformRateLimitKey({ headers: { authorization: "Bearer sensitive-token" } });
  match(rateLimitKey, /^token:[0-9a-f]{64}$/);
  equal(platformRateLimitKey({ headers: { "x-forwarded-for": "203.0.113.10, 10.0.0.1" } }), "ip:203.0.113.10");
  equal(platformRateLimitKey({ headers: {} }), "anonymous");

  const authz = {
    valueClaims: [
      {
        claim: "roles",
        format: "string-array" as const,
        values: { administrators: [permission] },
      },
      {
        claim: "scope",
        format: "space-delimited" as const,
        values: { "platform-smoke/read": [permission] },
      },
    ],
    claims: [
      {
        claim: "custom:role",
        equals: "operator",
        permissions: [permission],
      },
    ],
  };
  deepEqual(authzMappingPermissions(authz), [permission]);
  deepEqual(
    permissionsFromClaims({
      roles: ["administrators"],
      scope: "openid platform-smoke/read",
      "custom:role": "operator",
    }, authz),
    [permission],
  );
  equal(validateAuthzMappingPermissions(authz, [permission]).ok, true);
  const unknownMapping = validateAuthzMappingPermissions({
    valueClaims: [{ claim: "roles", format: "string-array", values: { bad: ["other:read" as Permission] } }],
  }, [permission]);
  equal(unknownMapping.ok, false);
  if (!unknownMapping.ok) {
    equal(unknownMapping.error.code, "PLATFORM_SECURITY_INVALID_AUTHZ_MAPPING");
  }

  const jwt = createJwtFixture();
  const verifier = createJwksJwtVerifier({
    issuer: jwt.issuer,
    jwksUri: jwt.jwksUri,
    requiredClaims: [{ claim: "kind", equals: "access" }],
    clock: fixedClock(new Date("2026-07-10T00:00:00.000Z")),
    fetchJwks: {
      fetch: async (uri) => {
        equal(uri, jwt.jwksUri);
        return { keys: [jwt.publicJwk] };
      },
    },
  });
  const verified = await verifier.verify(jwt.token({
    roles: ["administrators"],
    scope: "openid platform-smoke/read",
    "custom:role": "operator",
  }));
  equal(verified.ok, true);
  if (!verified.ok) {
    throw new Error("Expected generic JWT to verify.");
  }
  equal(verified.value.claims["iss"], jwt.issuer);
  equal(verified.value.claims["kind"], "access");

  const badRequiredClaim = await verifier.verify(jwt.token({ kind: "other" }));
  equal(badRequiredClaim.ok, false);
  if (!badRequiredClaim.ok) {
    equal(badRequiredClaim.error.code, "PLATFORM_SECURITY_INVALID_TOKEN");
  }

  const authHook = createJwtBearerAuthenticationHook({ verifier, authz });
  const unauthenticated = await authHook.authenticate({ headers: {} });
  equal(unauthenticated.authenticated, false);
  const authenticated = await authHook.authenticate({
    headers: { authorization: `Bearer ${jwt.token({ roles: ["administrators"] })}` },
  });
  equal(authenticated.authenticated, true);
  equal(authenticated.subject, jwt.subject);
  deepEqual(authenticated.permissions, [permission]);
  equal(authenticated.rateLimitKey, `principal:${jwt.subject}`);
}

function createJwtFixture(): {
  readonly issuer: string;
  readonly jwksUri: string;
  readonly subject: string;
  readonly publicJwk: PlatformJsonWebKey;
  token(extraClaims?: Readonly<Record<string, unknown>>): string;
} {
  const issuer = "https://identity.example.test/tenant";
  const jwksUri = `${issuer}/keys`;
  const subject = "subject-123";
  const { publicKey, privateKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const publicJwk = {
    ...publicKey.export({ format: "jwk" }),
    kid: "test-key",
    alg: "RS256",
    use: "sig",
  } as PlatformJsonWebKey;

  return {
    issuer,
    jwksUri,
    subject,
    publicJwk,
    token(extraClaims = {}) {
      const header = {
        alg: "RS256",
        kid: "test-key",
        typ: "JWT",
      };
      const payload = {
        iss: issuer,
        sub: subject,
        kind: "access",
        exp: 1_784_160_000,
        iat: 1_783_555_200,
        ...extraClaims,
      };
      const signingInput = `${base64urlJson(header)}.${base64urlJson(payload)}`;
      const signature = createSign("RSA-SHA256").update(signingInput).end().sign(privateKey).toString("base64url");
      return `${signingInput}.${signature}`;
    },
  };
}

function base64urlJson(value: unknown): string {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

main()
  .then(() => {
    console.log("platform/security runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
