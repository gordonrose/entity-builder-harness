import { deepEqual, equal } from "node:assert/strict";
import { createSign, generateKeyPairSync } from "node:crypto";
import type { Permission } from "@kanbien/core/authz";
import { fixedClock } from "@kanbien/core/shared";
import {
  definePlatformApp,
  platformAppId,
  platformRouteName,
} from "@kanbien/platform-contracts";
import { createPlatformServerShell } from "@kanbien/platform-server";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import {
  cognitoIssuer,
  cognitoJwksUri,
  createCognitoJwtBearerAuthenticationHookFromEnv,
  createCognitoAccessTokenVerifier,
  type CognitoAccessTokenVerifierOptions,
} from "../src/index";
import { isJwtConfigurationError, securityFailureDiagnosticRecord, type PlatformJsonWebKey } from "@kanbien/platform-security";

async function main(): Promise<void> {
  const fixture = createCognitoFixture();
  const fetchJwks = {
    fetch: async (uri: string) => {
      equal(uri, cognitoJwksUri(fixture.region, fixture.userPoolId));
      return { keys: [fixture.publicJwk] };
    },
  };
  const authentication = createCognitoJwtBearerAuthenticationHookFromEnv({
    PLATFORM_AUTH_COGNITO_REGION: fixture.region,
    PLATFORM_AUTH_COGNITO_USER_POOL_ID: fixture.userPoolId,
    PLATFORM_AUTH_COGNITO_APP_CLIENT_ID: fixture.appClientId,
    PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS: JSON.stringify([fixture.negativeTestClientId]),
    PLATFORM_AUTHZ_GROUP_PERMISSIONS: JSON.stringify({ "kanbien-admins": ["adapter-smoke.smoke:read"] }),
    PLATFORM_AUTHZ_SCOPE_PERMISSIONS: JSON.stringify({ "platform-smoke/read": ["adapter-smoke.smoke:read"] }),
    PLATFORM_AUTHZ_CLAIM_PERMISSIONS: JSON.stringify([{ claim: "custom:role", equals: "operator", permissions: ["adapter-smoke.smoke:read"] }]),
  }, {
    clock: fixedClock(new Date("2026-07-10T00:00:00.000Z")),
    fetchJwks,
  });
  equal(authentication.ok, true);
  if (!authentication.ok) {
    throw new Error("Expected valid adapter environment configuration.");
  }

  const missingConfiguration = createCognitoJwtBearerAuthenticationHookFromEnv({});
  equal(missingConfiguration.ok, false);
  if (!missingConfiguration.ok) {
    equal(missingConfiguration.error.code, "PLATFORM_ADAPTER_AWS_COGNITO_CONFIG_INVALID");
    deepEqual(missingConfiguration.error.diagnosticRecord?.detail, { phase: "adapter-configuration", reason: "missing", effect: "not-assessed", reference: "region" });
  }
  const validEnv = { PLATFORM_AUTH_COGNITO_REGION: "r", PLATFORM_AUTH_COGNITO_USER_POOL_ID: "pool", PLATFORM_AUTH_COGNITO_APP_CLIENT_ID: "client" };
  for (const skew of [NaN, Infinity, -1, null] as const) {
    const result = createCognitoJwtBearerAuthenticationHookFromEnv(validEnv, { clockSkewSeconds: skew as number, fetchJwks });
    equal(result.ok, false);
    if (!result.ok) {
      equal(result.error.code, "PLATFORM_ADAPTER_AWS_COGNITO_CONFIG_INVALID");
      deepEqual(result.error.details, { path: "verifier", reason: "Verifier configuration was rejected." });
      deepEqual(result.error.diagnosticRecord?.detail, { phase: "verifier-construction", effect: "verifier-not-created",
        issues: [{ setting: "clock-tolerance", reason: skew === null ? "wrong-type" : skew === -1 ? "negative" : "not-finite" }], truncated: false });
      equal(JSON.stringify(result.error.diagnosticRecord).includes("private-canary"), false);
    }
  }
  let directRejected = false;
  try { createCognitoAccessTokenVerifier({ region: "r", userPoolId: "pool", appClientId: "client", clockSkewSeconds: NaN }); }
  catch (error) { directRejected = true; equal(isJwtConfigurationError(error), true); equal(securityFailureDiagnosticRecord(error)?.code, "security.jwt-configuration-invalid"); }
  equal(directRejected, true);
  const sourceError = Object.freeze(new TypeError("PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID"));
  let propagated = false;
  try { createCognitoJwtBearerAuthenticationHookFromEnv(validEnv, { get clockSkewSeconds(): never { throw sourceError; } }); }
  catch (error) { propagated = true; equal(error, sourceError); }
  equal(propagated, true, "matching an exception message cannot spoof an owned configuration failure");
  equal(createCognitoJwtBearerAuthenticationHookFromEnv({}, { clockSkewSeconds: NaN }).ok, false);
  for (const [key, reference] of [["PLATFORM_AUTH_COGNITO_REGION", "region"], ["PLATFORM_AUTH_COGNITO_USER_POOL_ID", "identity-pool"], ["PLATFORM_AUTH_COGNITO_APP_CLIENT_ID", "client"]] as const) for (const value of [undefined, ""]) {
    const result = createCognitoJwtBearerAuthenticationHookFromEnv({ ...validEnv, [key]: value });
    equal(result.ok, false); if (!result.ok) deepEqual(result.error.diagnosticRecord?.detail, { phase: "adapter-configuration", reason: value === undefined ? "missing" : "empty", effect: "not-assessed", reference });
  }
  for (const [key, value, reference, reason] of [
    ["PLATFORM_AUTH_COGNITO_USER_POOL_ID", "", "identity-pool", "empty"],
    ["PLATFORM_AUTH_COGNITO_APP_CLIENT_ID", "", "client", "empty"],
    ["PLATFORM_AUTHZ_GROUP_PERMISSIONS", "private-canary", "group-mapping", "invalid-json"],
    ["PLATFORM_AUTHZ_SCOPE_PERMISSIONS", "[]", "scope-mapping", "wrong-shape"],
    ["PLATFORM_AUTHZ_CLAIM_PERMISSIONS", "{}", "claim-mapping", "wrong-shape"],
    ["PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS", '["x","x"]', "additional-clients", "duplicate-item"],
    ["PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS", '["client"]', "additional-clients", "duplicate-item"],
  ] as const) {
    const result = createCognitoJwtBearerAuthenticationHookFromEnv({ ...validEnv, [key]: value });
    equal(result.ok, false); if (!result.ok) {
      deepEqual(result.error.diagnosticRecord?.detail, { phase: "adapter-configuration", reason, effect: "not-assessed", reference, ...(reason === "duplicate-item" ? { referenceIndex: value === '["x","x"]' ? 1 : 0 } : {}) });
      equal(JSON.stringify(result.error.diagnosticRecord).includes("private-canary"), false);
    }
  }
  for (const [key, value, reference, reason, location] of [
    ["PLATFORM_AUTHZ_GROUP_PERMISSIONS", '{"private-canary":1}', "group-mapping", "attribute-wrong-type", { attribute: "permissions" }],
    ["PLATFORM_AUTHZ_GROUP_PERMISSIONS", '{"private-canary":[1]}', "group-mapping", "attribute-invalid", { attribute: "permissions", itemIndex: 0 }],
    ["PLATFORM_AUTHZ_CLAIM_PERMISSIONS", '[null]', "claim-mapping", "entry-wrong-type", {}],
    ["PLATFORM_AUTHZ_CLAIM_PERMISSIONS", '[{}]', "claim-mapping", "attribute-missing", { attribute: "claim" }],
    ["PLATFORM_AUTHZ_CLAIM_PERMISSIONS", '[{"claim":1}]', "claim-mapping", "attribute-wrong-type", { attribute: "claim" }],
    ["PLATFORM_AUTHZ_CLAIM_PERMISSIONS", '[{"claim":"role"}]', "claim-mapping", "attribute-missing", { attribute: "equals" }],
    ["PLATFORM_AUTHZ_CLAIM_PERMISSIONS", '[{"claim":"role","equals":null}]', "claim-mapping", "attribute-wrong-type", { attribute: "equals" }],
    ["PLATFORM_AUTHZ_CLAIM_PERMISSIONS", '[{"claim":"role","equals":true}]', "claim-mapping", "attribute-missing", { attribute: "permissions" }],
    ["PLATFORM_AUTHZ_CLAIM_PERMISSIONS", '[{"claim":"role","equals":true,"permissions":1}]', "claim-mapping", "attribute-wrong-type", { attribute: "permissions" }],
    ["PLATFORM_AUTHZ_CLAIM_PERMISSIONS", '[{"claim":"role","equals":true,"permissions":["invalid"]}]', "claim-mapping", "attribute-invalid", { attribute: "permissions", itemIndex: 0 }],
    ["PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS", '[1]', "additional-clients", "entry-wrong-type", {}],
    ["PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS", '[""]', "additional-clients", "entry-empty", {}],
  ] as const) {
    const result = createCognitoJwtBearerAuthenticationHookFromEnv({ ...validEnv, [key]: value });
    equal(result.ok, false); if (!result.ok) {
      deepEqual(result.error.diagnosticRecord?.detail, { phase: "adapter-configuration", reason, effect: "not-assessed", reference, referenceIndex: 0, ...location });
      equal(JSON.stringify(result.error.diagnosticRecord).includes("private-canary"), false);
    }
  }
  equal(createCognitoJwtBearerAuthenticationHookFromEnv({ ...validEnv, PLATFORM_AUTHZ_CLAIM_PERMISSIONS: '[{"claim":"","equals":"","permissions":[]}]' }).ok, true, "existing empty claim/equals acceptance remains unchanged");

  const permission = "adapter-smoke.smoke:read" as Permission;
  const testObservability = { kind: "opt_out", reason: "non_user_workload_path", justification: "Authentication adapter fixture only." } as const;
  const appId = platformAppId("adapter-smoke");
  const routeName = platformRouteName("adapter-smoke.protected");
  if (!appId.ok || !routeName.ok) {
    throw new Error("Expected valid adapter test app identifiers.");
  }
  const app = definePlatformApp({
    id: appId.value,
    name: "Adapter smoke",
    mount(registry) {
      registry.registerPermission({ permission });
      registry.registerRoute({
        name: routeName.value,
        method: "GET",
        path: "/adapter-protected",
        auth: { kind: "authenticated", permissions: [permission] },
        observability: testObservability,
        handler: { handle: () => ({ status: 200, body: { status: "ok" } }) },
      });
    },
  });
  let startedAfterRejectedConfiguration = 0;
  const rejectedConfiguration = createCognitoJwtBearerAuthenticationHookFromEnv(validEnv, { clockSkewSeconds: -1 });
  if (rejectedConfiguration.ok) {
    startedAfterRejectedConfiguration++;
    await createPlatformServerShell({ apps: [app], deps: createPlatformTestMountDeps(), auth: rejectedConfiguration.value });
  }
  equal(startedAfterRejectedConfiguration, 0, "the local composition caller handles configuration failure before server assembly");
  const shell = await createPlatformServerShell({
    apps: [app],
    deps: createPlatformTestMountDeps(),
    auth: authentication.value,
  });
  equal(shell.ok, true);
  if (!shell.ok) {
    throw new Error("Expected the adapter authentication hook to compose with platform/server.");
  }

  const denied = await shell.value.handle({ method: "GET", path: "/adapter-protected" });
  equal(denied.status, 401);
  const allowed = await shell.value.handle({
    method: "GET",
    path: "/adapter-protected",
    headers: {
      authorization: `Bearer ${fixture.token({
        "cognito:groups": ["kanbien-admins"],
        scope: "openid platform-smoke/read",
        "custom:role": "operator",
      })}`,
    },
  });
  equal(allowed.status, 200);
  deepEqual(allowed.body, { status: "ok" });
  const validButUnauthorized = await shell.value.handle({
    method: "GET",
    path: "/adapter-protected",
    headers: {
      authorization: `Bearer ${fixture.token({
        client_id: fixture.negativeTestClientId,
        scope: "platform-smoke/negative-test",
      })}`,
    },
  });
  equal(validButUnauthorized.status, 403);
  const untrustedClient = await shell.value.handle({
    method: "GET",
    path: "/adapter-protected",
    headers: {
      authorization: `Bearer ${fixture.token({ client_id: "untrusted-client" })}`,
    },
  });
  equal(untrustedClient.status, 401);
}

function createCognitoFixture(): {
  readonly region: string;
  readonly userPoolId: string;
  readonly appClientId: string;
  readonly negativeTestClientId: string;
  readonly publicJwk: PlatformJsonWebKey;
  token(extraClaims?: Readonly<Record<string, unknown>>): string;
} {
  const region = "eu-west-1";
  const userPoolId = "eu-west-1_example";
  const appClientId = "app-client-123";
  const negativeTestClientId = "negative-test-client-456";
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
    negativeTestClientId,
    publicJwk,
    token(extraClaims = {}) {
      const header = { alg: "RS256", kid: "test-key", typ: "JWT" };
      const payload = {
        iss: cognitoIssuer(region, userPoolId),
        sub: "adapter-subject",
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

void ({} as CognitoAccessTokenVerifierOptions);

main()
  .then(() => {
    console.log("Cognito adapter runtime and composition test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
