import { deepEqual, equal, match, throws } from "node:assert/strict";
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
  principalFromPlatformAuthenticationResult,
  validateAuthzMappingPermissions,
  type PlatformJsonWebKey,
  type PlatformAuthenticationResult,
  securityPrincipalBoundaryDiagnostic,
} from "../src/index";
import { createDiagnosticRecord, defineDiagnostic, parseDiagnosticRecord, type DiagnosticRecord } from "@kanbien/core/diagnostics";

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
  equal(principalFromPlatformAuthenticationResult(denyByDefaultAuthenticationResult), undefined);
  equal(principalFromPlatformAuthenticationResult({ authenticated: true, permissions: [] }), undefined);

  const authenticationPrincipal = principalFromPlatformAuthenticationResult({
    authenticated: true,
    permissions: [],
    principalId: "principal-123",
    principalType: "user",
    subject: "subject-123",
    claims: { sub: "subject-123", "custom:role": "operator" },
    scopes: ["openid", "platform-smoke/read"],
  });
  if (authenticationPrincipal === undefined) {
    throw new Error("Expected an authenticated principal to convert to a core Principal.");
  }
  equal(authenticationPrincipal.id, "principal-123");
  equal(authenticationPrincipal.type, "user");
  equal(authenticationPrincipal.subject, "subject-123");
  deepEqual(authenticationPrincipal.claims, { sub: "subject-123", "custom:role": "operator" });
  deepEqual(authenticationPrincipal.scopes, ["openid", "platform-smoke/read"]);

  const identityCanary = "private-authentication-projection-canary";
  const identityRecords: DiagnosticRecord[] = [];
  const origins: string[] = [];
  const missingAttributes: string[] = [];
  const identityOptions = { onDiagnostic(record: DiagnosticRecord, context: { readonly evidence: "owned" | "source" }) { identityRecords.push(record); origins.push(context.evidence); }, onMissingAttribute(attribute: string) { missingAttributes.push(attribute); } };
  const identityInput = { authenticated: true, permissions: [], principalId: "id", principalType: "user" as const, subject: "subject", claims: {}, scopes: [] };
  for (const [property, field] of [["authenticated", "authenticated"], ["principalId", "principal-id"], ["principalType", "principal-type"], ["subject", "subject"], ["claims", "claims"], ["scopes", "scopes"]] as const) {
    for (const failure of [identityCanary, null, 13, Object.freeze(new Error(identityCanary))]) {
      identityRecords.length = 0;
      let caught = false, reads = 0;
      try { principalFromPlatformAuthenticationResult(Object.defineProperty({ ...identityInput }, property, { get() { reads++; throw failure; } }), identityOptions); }
      catch (error) { caught = true; equal(error, failure); }
      equal(caught, true); equal(reads, 1);
      deepEqual(identityRecords, [{ schema: "core/diagnostic-record/v1", code: "security.authentication.principal-boundary-failed", definitionVersion: 1,
        detail: { operation: "principal-from-authentication", phase: "input-projection", field, reason: "threw", effect: "value-not-produced" } }]);
    }
  }
  for (const [property, attribute] of [["principalId", "principal-id"], ["principalType", "principal-type"], ["subject", "subject"]] as const) {
    identityRecords.length = 0; missingAttributes.length = 0;
    equal(principalFromPlatformAuthenticationResult({ ...identityInput, [property]: undefined } as unknown as PlatformAuthenticationResult, identityOptions), undefined);
    deepEqual(missingAttributes, [attribute]);
    deepEqual(identityRecords[0]?.detail, { phase: "authentication", reason: "principal-attribute-missing", effect: "not-assessed", attribute });
  }
  identityRecords.length = 0; missingAttributes.length = 0;
  equal(principalFromPlatformAuthenticationResult(Object.defineProperty({ authenticated: false, permissions: [] }, "principalId", { get() { throw identityCanary; } }), identityOptions), undefined);
  equal(identityRecords.length, 0); equal(missingAttributes.length, 0);
  const projectionOrder: string[] = [];
  const projection = Object.fromEntries(Object.entries(identityInput).map(([key, value]) => [key, key === "permissions" ? value : undefined]));
  for (const [key, value] of Object.entries(identityInput)) if (key !== "permissions") Object.defineProperty(projection, key, { get() { projectionOrder.push(key); return value; } });
  principalFromPlatformAuthenticationResult(projection as unknown as PlatformAuthenticationResult, identityOptions);
  deepEqual(projectionOrder, ["authenticated", "principalId", "principalType", "subject", "principalId", "principalType", "subject", "claims", "scopes"]);
  const identitySourceDefinition = defineDiagnostic({ code: "identityfixture.authentication-source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } },
  } as const);
  const identitySources = Array.from({ length: 9 }, (_, ordinal) => { const result = createDiagnosticRecord(identitySourceDefinition, { ordinal }); if (!result.ok) throw new Error("Invalid source fixture"); return result.value; });
  const identityFailure = Object.freeze({ diagnosticRecord: identitySources[0], relatedDiagnosticRecords: identitySources.slice(1) });
  for (const boundary of ["projection", "copy"] as const) {
    identityRecords.length = 0; origins.length = 0;
    const input = boundary === "projection" ? Object.defineProperty({ ...identityInput }, "subject", { get() { throw identityFailure; } })
      : { ...identityInput, scopes: { [Symbol.iterator]() { throw identityFailure; } } as unknown as readonly string[] };
    let caught = false;
    try { principalFromPlatformAuthenticationResult(input, { ...identityOptions, diagnosticDefinitions: [identitySourceDefinition] }); }
    catch (error) { caught = true; equal(error, identityFailure); }
    equal(caught, true); equal(identityRecords.length, 10); deepEqual(identityRecords.slice(1), identitySources);
    deepEqual(origins, ["owned", ...Array.from({ length: 9 }, () => "source")]);
    equal(identityRecords[0]?.code, boundary === "projection" ? "security.authentication.principal-boundary-failed" : "core.authn.boundary-failed");
  }
  let diagnosticAccessorReads = 0;
  const hostileSource = Object.defineProperty({}, "diagnosticRecord", { get() { diagnosticAccessorReads++; throw identityCanary; } });
  identityRecords.length = 0;
  try { principalFromPlatformAuthenticationResult(Object.defineProperty({ ...identityInput }, "subject", { get() { throw hostileSource; } }), identityOptions); } catch (error) { equal(error, hostileSource); }
  equal(diagnosticAccessorReads, 0); equal(identityRecords.length, 2);
  deepEqual(identityRecords[1], { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1,
    detail: { reason: "evidence-inaccessible" } });
  equal(parseDiagnosticRecord(securityPrincipalBoundaryDiagnostic, identityRecords[0]).ok, true);
  equal(parseDiagnosticRecord(securityPrincipalBoundaryDiagnostic, { ...identityRecords[0], detail: { field: identityCanary } }).ok, false);
  const principalDiagnosticBuilders = require("../src/diagnostics") as Record<string, unknown>;
  const originalPrincipalBuilder = principalDiagnosticBuilders.securityPrincipalBoundaryDiagnosticRecord;
  try {
    for (const [mode, reason] of [["throw", "construction-threw"], ["absent", "construction-rejected"], ["malformed", "evidence-rejected"]] as const) {
      let calls = 0;
      principalDiagnosticBuilders.securityPrincipalBoundaryDiagnosticRecord = () => {
        calls++;
        if (mode === "throw") throw new Error(identityCanary);
        return mode === "absent" ? undefined : { code: identityCanary };
      };
      identityRecords.length = 0;
      throws(() => principalFromPlatformAuthenticationResult(Object.defineProperty({ ...identityInput }, "subject", { get() { throw identityFailure; } }),
        { ...identityOptions, diagnosticDefinitions: [identitySourceDefinition] }), (error) => error === identityFailure);
      equal(calls, 1);
      deepEqual(identityRecords[0], { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason } });
      deepEqual(identityRecords.slice(1), identitySources);
      equal(JSON.stringify(identityRecords).includes(identityCanary), false);
    }
  } finally { principalDiagnosticBuilders.securityPrincipalBoundaryDiagnosticRecord = originalPrincipalBuilder; }
  identityRecords.length = 0;
  const { principalId: _principalId, ...missingPrincipalId } = identityInput;
  equal(principalFromPlatformAuthenticationResult(missingPrincipalId, {
    ...identityOptions,
    get diagnosticDefinitions(): never { throw new Error(identityCanary); },
  }), undefined);
  deepEqual(identityRecords.map((record) => record.code), ["security.authentication.principal-attribute-missing", "core.diagnostics.processing-failed"]);
  deepEqual(identityRecords[1]?.detail, { reason: "definition-selection-failed" });
  for (const sink of [() => { throw identityCanary; }, () => Promise.reject(identityCanary), () => Object.assign(Promise.reject(identityCanary), { then() { throw identityCanary; } }), () => ({ then(_ok: unknown, reject: (reason: unknown) => void) { reject(identityCanary); } })]) {
    let caught = false;
    try { principalFromPlatformAuthenticationResult(Object.defineProperty({ ...identityInput }, "subject", { get() { throw identityFailure; } }), { onDiagnostic: sink, onMissingAttribute: sink }); }
    catch (error) { caught = true; equal(error, identityFailure); }
    equal(caught, true);
    equal(principalFromPlatformAuthenticationResult({ authenticated: true, permissions: [] }, { onMissingAttribute: sink }), undefined);
  }
  await new Promise<void>((resolve) => setImmediate(resolve));
  equal(JSON.stringify(identityRecords).includes(identityCanary), false);

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

  const rateLimitKey = platformRateLimitKey({ bearerToken: "sensitive-token" });
  match(rateLimitKey, /^token:[0-9a-f]{64}$/);
  equal(platformRateLimitKey({ clientAddress: "203.0.113.10" }), "ip:203.0.113.10");
  equal(platformRateLimitKey({}), "anonymous");

  const boundedBuckets = createInMemoryPlatformRateLimiter({
    limit: 1,
    windowMs: 1_000,
    maxBuckets: 1,
    clock: fixedClock(new Date("2026-07-10T00:00:00.000Z")),
  });
  equal(boundedBuckets.check("first-client").allowed, true);
  equal(boundedBuckets.check("unbounded-keyspace-attempt").allowed, false);
  throws(
    () => createInMemoryPlatformRateLimiter({ maxBuckets: 0 }),
    /maxBuckets must be a positive integer/,
  );

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

  const allowlistedVerifier = createJwksJwtVerifier({
    issuer: jwt.issuer,
    jwksUri: jwt.jwksUri,
    requiredClaims: [{ claim: "client_id", oneOf: ["primary-client", "negative-test-client"] }],
    clock: fixedClock(new Date("2026-07-10T00:00:00.000Z")),
    fetchJwks: {
      fetch: async () => ({ keys: [jwt.publicJwk] }),
    },
  });
  equal((await allowlistedVerifier.verify(jwt.token({ client_id: "negative-test-client" }))).ok, true);
  equal((await allowlistedVerifier.verify(jwt.token({ client_id: "unconfigured-client" }))).ok, false);
  equal((await allowlistedVerifier.verify(jwt.token({ client_id: ["negative-test-client"] }))).ok, false);

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
