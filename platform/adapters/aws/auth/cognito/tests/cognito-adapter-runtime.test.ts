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
  type CognitoAccessTokenVerifierOptions,
} from "../src/index";
import type { PlatformJsonWebKey } from "@kanbien/platform-security";

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
    PLATFORM_AUTHZ_GROUP_PERMISSIONS: JSON.stringify({ "kanbien-admins": ["smoke:read"] }),
    PLATFORM_AUTHZ_SCOPE_PERMISSIONS: JSON.stringify({ "platform-smoke/read": ["smoke:read"] }),
    PLATFORM_AUTHZ_CLAIM_PERMISSIONS: JSON.stringify([{ claim: "custom:role", equals: "operator", permissions: ["smoke:read"] }]),
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
  }

  const permission = "smoke:read" as Permission;
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
        handler: { handle: () => ({ status: 200, body: { status: "ok" } }) },
      });
    },
  });
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
}

function createCognitoFixture(): {
  readonly region: string;
  readonly userPoolId: string;
  readonly appClientId: string;
  readonly publicJwk: PlatformJsonWebKey;
  token(extraClaims?: Readonly<Record<string, unknown>>): string;
} {
  const region = "eu-west-1";
  const userPoolId = "eu-west-1_example";
  const appClientId = "app-client-123";
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
