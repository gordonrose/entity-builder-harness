import { deepEqual, equal, match } from "node:assert/strict";
import { createSign, generateKeyPairSync } from "node:crypto";
import type { Permission } from "@kanbien/core/authz";
import { fixedClock } from "@kanbien/core/shared";
import {
  authzMappingPermissions,
  authorizePlatformPermissions,
  cognitoIssuer,
  cognitoJwksUri,
  corsPolicyForOrigin,
  createCognitoAccessTokenVerifier,
  createInMemoryPlatformRateLimiter,
  createJwtBearerAuthenticationHook,
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
    groups: {
      "kanbien-admins": [permission],
    },
    scopes: {
      "platform-smoke/read": [permission],
    },
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
      "cognito:groups": ["kanbien-admins"],
      scope: "openid platform-smoke/read",
      "custom:role": "operator",
    }, authz),
    [permission],
  );
  equal(validateAuthzMappingPermissions(authz, [permission]).ok, true);
  const unknownMapping = validateAuthzMappingPermissions({ groups: { bad: ["other:read" as Permission] } }, [permission]);
  equal(unknownMapping.ok, false);
  if (!unknownMapping.ok) {
    equal(unknownMapping.error.code, "PLATFORM_SECURITY_INVALID_AUTHZ_MAPPING");
  }

  const cognito = createCognitoFixture();
  const verifier = createCognitoAccessTokenVerifier({
    region: cognito.region,
    userPoolId: cognito.userPoolId,
    appClientId: cognito.appClientId,
    clock: fixedClock(new Date("2026-07-10T00:00:00.000Z")),
    fetchJwks: {
      fetch: async (uri) => {
        equal(uri, cognitoJwksUri(cognito.region, cognito.userPoolId));
        return { keys: [cognito.publicJwk] };
      },
    },
  });
  const verified = await verifier.verify(cognito.token({
    "cognito:groups": ["kanbien-admins"],
    scope: "openid platform-smoke/read",
    "custom:role": "operator",
  }));
  equal(verified.ok, true);
  if (!verified.ok) {
    throw new Error("Expected Cognito-shaped JWT to verify.");
  }
  equal(verified.value.claims["iss"], cognitoIssuer(cognito.region, cognito.userPoolId));
  equal(verified.value.claims["token_use"], "access");

  const badClient = await verifier.verify(cognito.token({ client_id: "wrong-client" }));
  equal(badClient.ok, false);
  if (!badClient.ok) {
    equal(badClient.error.code, "PLATFORM_SECURITY_INVALID_TOKEN");
  }

  const authHook = createJwtBearerAuthenticationHook({ verifier, authz });
  const unauthenticated = await authHook.authenticate({ headers: {} });
  equal(unauthenticated.authenticated, false);
  const authenticated = await authHook.authenticate({
    headers: { authorization: `Bearer ${cognito.token({ "cognito:groups": ["kanbien-admins"] })}` },
  });
  equal(authenticated.authenticated, true);
  equal(authenticated.subject, cognito.subject);
  deepEqual(authenticated.permissions, [permission]);
  equal(authenticated.rateLimitKey, `principal:${cognito.subject}`);
}

function createCognitoFixture(): {
  readonly region: string;
  readonly userPoolId: string;
  readonly appClientId: string;
  readonly subject: string;
  readonly publicJwk: PlatformJsonWebKey;
  token(extraClaims?: Readonly<Record<string, unknown>>): string;
} {
  const region = "eu-west-1";
  const userPoolId = "eu-west-1_example";
  const appClientId = "app-client-123";
  const subject = "subject-123";
  const { publicKey, privateKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const publicJwk = {
    ...publicKey.export({ format: "jwk" }),
    kid: "test-key",
    alg: "RS256",
    use: "sig",
  } as PlatformJsonWebKey;

  return {
    region,
    userPoolId,
    appClientId,
    subject,
    publicJwk,
    token(extraClaims = {}) {
      const header = {
        alg: "RS256",
        kid: "test-key",
        typ: "JWT",
      };
      const payload = {
        iss: cognitoIssuer(region, userPoolId),
        sub: subject,
        token_use: "access",
        client_id: appClientId,
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
