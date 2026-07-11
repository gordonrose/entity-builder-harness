import { createHash, createPublicKey, createVerify, type JsonWebKey, type KeyObject } from "node:crypto";
import { principalId, type Clock, type JsonValue, type Permission, type PrincipalClaims, type PrincipalType, type Result } from "@kanbien/core";

export type PlatformSecurityErrorCode =
  | "PLATFORM_SECURITY_UNAUTHENTICATED"
  | "PLATFORM_SECURITY_INVALID_TOKEN"
  | "PLATFORM_SECURITY_INVALID_AUTHZ_MAPPING"
  | "PLATFORM_SECURITY_FORBIDDEN"
  | "PLATFORM_SECURITY_RATE_LIMITED";

export interface PlatformSecurityError {
  readonly code: PlatformSecurityErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
}

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

export interface PlatformCorsPolicy {
  readonly allowedOrigin?: string;
  readonly allowedMethods?: readonly string[];
  readonly allowedHeaders?: readonly string[];
  readonly allowCredentials?: boolean;
}

export interface PlatformSecurityHeadersOptions {
  readonly cors?: PlatformCorsPolicy;
}

export interface PlatformRateLimitDecision {
  readonly allowed: boolean;
  readonly retryAfterMs?: number;
}

export interface PlatformRateLimiter {
  check(key: string): PlatformRateLimitDecision;
}

export interface InMemoryPlatformRateLimiterOptions {
  readonly limit?: number;
  readonly windowMs?: number;
  readonly clock?: Clock;
}

export interface PlatformRateLimitKeyInput {
  readonly headers?: Readonly<Record<string, string | readonly string[]>>;
  readonly authentication?: PlatformAuthenticationResult;
}

export interface PlatformJwtVerificationOptions {
  readonly issuer: string;
  readonly jwksUri: string;
  readonly clientId?: string;
  readonly tokenUse?: "access" | "id";
  readonly clock?: Clock;
  readonly clockSkewSeconds?: number;
  readonly fetchJwks?: PlatformJwksFetcher;
}

export interface CognitoAccessTokenVerifierOptions {
  readonly region: string;
  readonly userPoolId: string;
  readonly appClientId: string;
  readonly clock?: Clock;
  readonly clockSkewSeconds?: number;
  readonly fetchJwks?: PlatformJwksFetcher;
}

export interface PlatformJwtVerifier {
  verify(token: string): Promise<Result<PlatformVerifiedJwt, PlatformSecurityError>>;
}

export interface PlatformVerifiedJwt {
  readonly header: Readonly<Record<string, JsonValue>>;
  readonly claims: PrincipalClaims;
}

export interface PlatformJwks {
  readonly keys: readonly PlatformJsonWebKey[];
}

export interface PlatformJsonWebKey {
  readonly kid?: string;
  readonly kty?: string;
  readonly alg?: string;
  readonly use?: string;
  readonly n?: string;
  readonly e?: string;
}

export interface PlatformJwksFetcher {
  fetch(uri: string): Promise<PlatformJwks>;
}

export interface PlatformAuthzPermissionMapping {
  readonly groups?: Readonly<Record<string, readonly Permission[]>>;
  readonly scopes?: Readonly<Record<string, readonly Permission[]>>;
  readonly claims?: readonly PlatformClaimPermissionMapping[];
}

export interface PlatformClaimPermissionMapping {
  readonly claim: string;
  readonly equals: string | number | boolean;
  readonly permissions: readonly Permission[];
}

export interface JwtBearerAuthenticationHookOptions {
  readonly verifier: PlatformJwtVerifier;
  readonly authz: PlatformAuthzPermissionMapping;
  readonly principalType?: PrincipalType;
}

interface RateLimitBucket {
  readonly windowStartedAtMs: number;
  readonly count: number;
}

export const denyByDefaultAuthenticationResult: PlatformAuthenticationResult = {
  authenticated: false,
  permissions: [],
};

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

export function createCognitoAccessTokenVerifier(
  options: CognitoAccessTokenVerifierOptions,
): PlatformJwtVerifier {
  return createJwksJwtVerifier({
    issuer: cognitoIssuer(options.region, options.userPoolId),
    jwksUri: cognitoJwksUri(options.region, options.userPoolId),
    clientId: options.appClientId,
    tokenUse: "access",
    ...(options.clock === undefined ? {} : { clock: options.clock }),
    ...(options.clockSkewSeconds === undefined ? {} : { clockSkewSeconds: options.clockSkewSeconds }),
    ...(options.fetchJwks === undefined ? {} : { fetchJwks: options.fetchJwks }),
  });
}

export function cognitoIssuer(region: string, userPoolId: string): string {
  return `https://cognito-idp.${region}.amazonaws.com/${userPoolId}`;
}

export function cognitoJwksUri(region: string, userPoolId: string): string {
  return `${cognitoIssuer(region, userPoolId)}/.well-known/jwks.json`;
}

export function createJwksJwtVerifier(options: PlatformJwtVerificationOptions): PlatformJwtVerifier {
  const fetchJwks = options.fetchJwks ?? defaultJwksFetcher;
  const clock = options.clock ?? { now: () => new Date() };
  const clockSkewSeconds = options.clockSkewSeconds ?? 60;
  const keys = new Map<string, KeyObject>();

  async function keyForKid(kid: string): Promise<KeyObject | undefined> {
    const cached = keys.get(kid);
    if (cached !== undefined) {
      return cached;
    }

    const jwks = await fetchJwks.fetch(options.jwksUri);
    for (const key of jwks.keys) {
      if (key.kid === undefined || key.kty !== "RSA" || key.n === undefined || key.e === undefined) {
        continue;
      }

      keys.set(key.kid, createPublicKey({ key: jsonWebKey(key), format: "jwk" }));
    }

    return keys.get(kid);
  }

  return {
    async verify(token) {
      const decoded = decodeJwt(token);
      if (!decoded.ok) {
        return decoded;
      }

      const alg = stringValue(decoded.value.header["alg"]);
      const kid = stringValue(decoded.value.header["kid"]);
      if (alg !== "RS256" || kid === undefined) {
        return invalidToken("JWT header must include RS256 alg and kid.");
      }

      const key = await keyForKid(kid);
      if (key === undefined) {
        return invalidToken("JWT signing key id was not found in JWKS.");
      }

      const verifier = createVerify("RSA-SHA256");
      verifier.update(decoded.value.signingInput);
      verifier.end();
      if (!verifier.verify(key, decoded.value.signature)) {
        return invalidToken("JWT signature is invalid.");
      }

      const claimsValidation = validateJwtClaims(decoded.value.claims, {
        issuer: options.issuer,
        ...(options.clientId === undefined ? {} : { clientId: options.clientId }),
        tokenUse: options.tokenUse ?? "access",
        clock,
        clockSkewSeconds,
      });
      if (!claimsValidation.ok) {
        return claimsValidation;
      }

      return {
        ok: true,
        value: {
          header: decoded.value.header,
          claims: decoded.value.claims,
        },
      };
    },
  };
}

export function createPlatformSecurityHeaders(
  options: PlatformSecurityHeadersOptions = {},
): Readonly<Record<string, string>> {
  return {
    "content-type": "application/json; charset=utf-8",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    ...(options.cors?.allowedOrigin === undefined ? {} : { "access-control-allow-origin": options.cors.allowedOrigin }),
    ...(options.cors?.allowedMethods === undefined ? {} : { "access-control-allow-methods": options.cors.allowedMethods.join(", ") }),
    ...(options.cors?.allowedHeaders === undefined ? {} : { "access-control-allow-headers": options.cors.allowedHeaders.join(", ") }),
    ...(options.cors?.allowCredentials === undefined ? {} : { "access-control-allow-credentials": String(options.cors.allowCredentials) }),
  };
}

export function corsPolicyForOrigin(origin: string | undefined): PlatformCorsPolicy {
  if (origin === undefined || origin.length === 0) {
    return {};
  }

  return {
    allowedOrigin: origin,
    allowedMethods: ["GET", "POST", "PUT", "PATCH", "DELETE"],
    allowedHeaders: ["authorization", "content-type", "x-request-id"],
  };
}

export function corsPolicyForRequestOrigin(input: {
  readonly requestOrigin?: string;
  readonly allowedOrigins?: readonly string[];
  readonly allowCredentials?: boolean;
}): PlatformCorsPolicy {
  const requestOrigin = input.requestOrigin;
  if (requestOrigin === undefined || requestOrigin.length === 0) {
    return {};
  }

  const allowedOrigins = input.allowedOrigins ?? [];
  if (!allowedOrigins.includes(requestOrigin)) {
    return {};
  }

  return {
    ...corsPolicyForOrigin(requestOrigin),
    ...(input.allowCredentials === undefined ? {} : { allowCredentials: input.allowCredentials }),
  };
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

export function createInMemoryPlatformRateLimiter(
  options: InMemoryPlatformRateLimiterOptions = {},
): PlatformRateLimiter {
  const limit = options.limit ?? 1000;
  const windowMs = options.windowMs ?? 60_000;
  const clock = options.clock ?? { now: () => new Date() };
  const buckets = new Map<string, RateLimitBucket>();

  return {
    check(key) {
      const nowMs = clock.now().getTime();
      const current = buckets.get(key);
      if (current === undefined || nowMs - current.windowStartedAtMs >= windowMs) {
        buckets.set(key, { windowStartedAtMs: nowMs, count: 1 });
        return { allowed: true };
      }

      if (current.count >= limit) {
        return {
          allowed: false,
          retryAfterMs: Math.max(0, windowMs - (nowMs - current.windowStartedAtMs)),
        };
      }

      buckets.set(key, { ...current, count: current.count + 1 });
      return { allowed: true };
    },
  };
}

export function platformRateLimitKey(input: PlatformRateLimitKeyInput): string {
  if (input.authentication?.rateLimitKey !== undefined) {
    return input.authentication.rateLimitKey;
  }

  const bearerToken = bearerTokenFromHeaders(input.headers ?? {});
  if (bearerToken !== undefined) {
    return `token:${sha256(bearerToken)}`;
  }

  const forwardedFor = firstHeaderValue(input.headers ?? {}, "x-forwarded-for");
  if (forwardedFor !== undefined && forwardedFor.length > 0) {
    return `ip:${forwardedFor.split(",")[0]?.trim() ?? forwardedFor}`;
  }

  const realIp = firstHeaderValue(input.headers ?? {}, "x-real-ip");
  if (realIp !== undefined && realIp.length > 0) {
    return `ip:${realIp}`;
  }

  return "anonymous";
}

export function platformRateLimitError(retryAfterMs?: number): PlatformSecurityError {
  return {
    code: "PLATFORM_SECURITY_RATE_LIMITED",
    defaultMessage: "Request rate limit exceeded.",
    ...(retryAfterMs === undefined ? {} : { details: { retryAfterMs } }),
  };
}

export function permissionsFromClaims(
  claims: PrincipalClaims,
  mapping: PlatformAuthzPermissionMapping,
): readonly Permission[] {
  const permissions = new Set<Permission>();

  for (const group of stringArrayClaim(claims, "cognito:groups")) {
    for (const permission of mapping.groups?.[group] ?? []) {
      permissions.add(permission);
    }
  }

  for (const scope of scopesFromClaims(claims)) {
    for (const permission of mapping.scopes?.[scope] ?? []) {
      permissions.add(permission);
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

  for (const permissionList of Object.values(mapping.groups ?? {})) {
    for (const permission of permissionList) {
      permissions.add(permission);
    }
  }

  for (const permissionList of Object.values(mapping.scopes ?? {})) {
    for (const permission of permissionList) {
      permissions.add(permission);
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

function validateJwtClaims(
  claims: PrincipalClaims,
  options: {
    readonly issuer: string;
    readonly clientId?: string;
    readonly tokenUse: "access" | "id";
    readonly clock: Clock;
    readonly clockSkewSeconds: number;
  },
): Result<void, PlatformSecurityError> {
  if (stringClaim(claims, "iss") !== options.issuer) {
    return invalidToken("JWT issuer does not match the configured issuer.");
  }

  if (stringClaim(claims, "token_use") !== options.tokenUse) {
    return invalidToken("JWT token_use does not match the configured token use.");
  }

  if (options.clientId !== undefined) {
    const clientClaim = options.tokenUse === "access" ? stringClaim(claims, "client_id") : stringClaim(claims, "aud");
    if (clientClaim !== options.clientId) {
      return invalidToken("JWT client id does not match the configured app client.");
    }
  }

  const nowSeconds = Math.floor(options.clock.now().getTime() / 1000);
  const expiresAt = numberClaim(claims, "exp");
  if (expiresAt === undefined || expiresAt <= nowSeconds - options.clockSkewSeconds) {
    return invalidToken("JWT is expired or missing exp.");
  }

  const notBefore = numberClaim(claims, "nbf");
  if (notBefore !== undefined && notBefore > nowSeconds + options.clockSkewSeconds) {
    return invalidToken("JWT is not valid yet.");
  }

  const issuedAt = numberClaim(claims, "iat");
  if (issuedAt !== undefined && issuedAt > nowSeconds + options.clockSkewSeconds) {
    return invalidToken("JWT issued-at time is in the future.");
  }

  if (stringClaim(claims, "sub") === undefined) {
    return invalidToken("JWT subject is missing.");
  }

  return { ok: true, value: undefined };
}

function decodeJwt(token: string): Result<{
  readonly header: Readonly<Record<string, JsonValue>>;
  readonly claims: PrincipalClaims;
  readonly signingInput: string;
  readonly signature: Buffer;
}, PlatformSecurityError> {
  const parts = token.split(".");
  if (parts.length !== 3 || parts.some((part) => part.length === 0)) {
    return invalidToken("JWT must have header, payload, and signature segments.");
  }

  const [encodedHeader, encodedPayload, encodedSignature] = parts as [string, string, string];
  const header = decodeJsonSegment(encodedHeader);
  const claims = decodeJsonSegment(encodedPayload);
  if (!header.ok) {
    return header;
  }
  if (!claims.ok) {
    return claims;
  }

  return {
    ok: true,
    value: {
      header: header.value,
      claims: claims.value,
      signingInput: `${encodedHeader}.${encodedPayload}`,
      signature: Buffer.from(encodedSignature, "base64url"),
    },
  };
}

function decodeJsonSegment(segment: string): Result<Readonly<Record<string, JsonValue>>, PlatformSecurityError> {
  try {
    const value = JSON.parse(Buffer.from(segment, "base64url").toString("utf8")) as unknown;
    if (isJsonObject(value)) {
      return { ok: true, value };
    }
  } catch {
    // Fall through to the shared invalid-token response.
  }

  return invalidToken("JWT segment must decode to a JSON object.");
}

function bearerTokenFromHeaders(headers: Readonly<Record<string, string | readonly string[]>>): string | undefined {
  const authorization = firstHeaderValue(headers, "authorization");
  if (authorization === undefined) {
    return undefined;
  }

  const match = /^Bearer\s+(.+)$/i.exec(authorization);
  return match?.[1];
}

function firstHeaderValue(headers: Readonly<Record<string, string | readonly string[]>>, name: string): string | undefined {
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

function stringArrayClaim(claims: PrincipalClaims, name: string): readonly string[] {
  const value = claims[name];
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function stringClaim(claims: PrincipalClaims, name: string): string | undefined {
  return stringValue(claims[name]);
}

function numberClaim(claims: PrincipalClaims, name: string): number | undefined {
  const value = claims[name];
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function stringValue(value: JsonValue | undefined): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function sha256(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}

function invalidToken(defaultMessage: string): Result<never, PlatformSecurityError> {
  return {
    ok: false,
    error: {
      code: "PLATFORM_SECURITY_INVALID_TOKEN",
      defaultMessage,
    },
  };
}

function isJsonObject(value: unknown): value is Readonly<Record<string, JsonValue>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

const defaultJwksFetcher: PlatformJwksFetcher = {
  async fetch(uri) {
    const response = await fetch(uri);
    if (!response.ok) {
      throw new Error(`JWKS request failed with status ${response.status}.`);
    }

    const value = await response.json() as unknown;
    if (!isJwks(value)) {
      throw new Error("JWKS response did not contain a keys array.");
    }

    return value;
  },
};

function isJwks(value: unknown): value is PlatformJwks {
  return isJsonObject(value) && Array.isArray(value["keys"]);
}

function jsonWebKey(key: PlatformJsonWebKey): JsonWebKey {
  return {
    ...(key.kid === undefined ? {} : { kid: key.kid }),
    ...(key.kty === undefined ? {} : { kty: key.kty }),
    ...(key.alg === undefined ? {} : { alg: key.alg }),
    ...(key.use === undefined ? {} : { use: key.use }),
    ...(key.n === undefined ? {} : { n: key.n }),
    ...(key.e === undefined ? {} : { e: key.e }),
  };
}
