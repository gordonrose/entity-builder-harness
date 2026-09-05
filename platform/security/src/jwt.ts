import { createPublicKey, createVerify, type JsonWebKey, type KeyObject } from "node:crypto";
import type { Clock, JsonValue, PrincipalClaims, Result } from "@kanbien/core";
import type { PlatformSecurityError } from "./errors";

export interface PlatformJwtVerificationOptions {
  readonly issuer: string;
  readonly jwksUri: string;
  readonly requiredClaims?: readonly PlatformJwtClaimRequirement[];
  readonly clock?: Clock;
  readonly clockSkewSeconds?: number;
  readonly fetchJwks?: PlatformJwksFetcher;
}

export interface PlatformJwtClaimRequirement {
  readonly claim: string;
  readonly equals: string | number | boolean;
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
        ...(options.requiredClaims === undefined ? {} : { requiredClaims: options.requiredClaims }),
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

function validateJwtClaims(
  claims: PrincipalClaims,
  options: {
    readonly issuer: string;
    readonly requiredClaims?: readonly PlatformJwtClaimRequirement[];
    readonly clock: Clock;
    readonly clockSkewSeconds: number;
  },
): Result<void, PlatformSecurityError> {
  if (stringClaim(claims, "iss") !== options.issuer) {
    return invalidToken("JWT issuer does not match the configured issuer.");
  }

  for (const requiredClaim of options.requiredClaims ?? []) {
    if (claims[requiredClaim.claim] !== requiredClaim.equals) {
      return invalidToken(`JWT claim ${requiredClaim.claim} does not match the configured value.`);
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
