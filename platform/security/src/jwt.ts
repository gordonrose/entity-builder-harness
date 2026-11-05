import { createPublicKey, createVerify, type JsonWebKey, type KeyObject } from "node:crypto";
import type { Clock, JsonValue, PrincipalClaims, Result } from "@kanbien/core";
import type { PlatformSecurityError } from "./errors";
import { observeSecurityFailure, observedSecurityPeerFailures, securityFailureDiagnosticRecord, securityOperationDiagnosticRecord } from "./diagnostics";
import type { SecurityOperationReason } from "@kanbien/core/security";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";

export type { PlatformJwtVerificationOptions, PlatformJwtClaimRequirement, PlatformJwtExactClaimRequirement, PlatformJwtOneOfClaimRequirement, PlatformJwtClaimScalar, PlatformJwtVerifier, PlatformVerifiedJwt, PlatformJwks, PlatformJsonWebKey, PlatformJwksFetcher } from "./jwt-contract";
import type { PlatformJwtVerificationOptions, PlatformJwtClaimRequirement, PlatformJwtExactClaimRequirement, PlatformJwtOneOfClaimRequirement, PlatformJwtClaimScalar, PlatformJwtVerifier, PlatformVerifiedJwt, PlatformJwks, PlatformJsonWebKey, PlatformJwksFetcher } from "./jwt-contract";
import { validateJwtVerifierConfiguration, jwtConfigurationError } from "./jwt-configuration/index";

export function createJwksJwtVerifier(options: PlatformJwtVerificationOptions): PlatformJwtVerifier {
  const checked = validateJwtVerifierConfiguration(options);
  if (!checked.ok) throw jwtConfigurationError(checked.error.diagnosticRecord);
  const configuration = checked.value;
  const fetchJwks = configuration.fetchJwks ?? defaultJwksFetcher;
  const clock = configuration.clock ?? { now: () => new Date() };
  const clockSkewSeconds = configuration.clockSkewSeconds;
  const keys = new Map<string, KeyObject>();

  async function keyForKid(kid: string): Promise<{ readonly key: KeyObject | undefined; readonly observations: readonly DiagnosticRecord[] }> {
    const cached = keys.get(kid);
    if (cached !== undefined) {
      return { key: cached, observations: [] };
    }

    let jwks: PlatformJwks;
    try { jwks = await fetchJwks.fetch(configuration.jwksUri); }
    catch (error) { throw observeSecurityFailure(error, securityFailureDiagnosticRecord(error) ?? securityOperationDiagnosticRecord("signing-key", "fetch-failed"), observedSecurityPeerFailures(error)); }
    if (!isJwks(jwks)) throw observeSecurityFailure(new TypeError("JWKS response did not contain a keys array."), securityOperationDiagnosticRecord("signing-key", "key-set-invalid"));
    const observations: DiagnosticRecord[] = [];
    let omitted = 0;
    for (const [referenceIndex, key] of jwks.keys.entries()) {
      const skip = (reason: SecurityOperationReason<"signing-key">) => {
        if (observations.length < 7) observations.push(securityOperationDiagnosticRecord("signing-key", reason, { referenceIndex }));
        else omitted++;
      };
      try {
      if (key.kid === undefined) { skip("key-id-absent"); continue; }
      if (key.kty !== "RSA") { skip("key-type-unsupported"); continue; }
      if (key.n === undefined) { skip("key-modulus-absent"); continue; }
      if (key.e === undefined) { skip("key-exponent-absent"); continue; }

      try { keys.set(key.kid, createPublicKey({ key: jsonWebKey(key), format: "jwk" })); }
      catch (error) { throw observeSecurityFailure(error, securityOperationDiagnosticRecord("signing-key", "key-material-invalid", { referenceIndex })); }
      } catch (error) { throw observeSecurityFailure(error, securityFailureDiagnosticRecord(error) ?? securityOperationDiagnosticRecord("signing-key", "key-entry-unreadable", { referenceIndex })); }
    }

    if (omitted > 0) observations.push(securityOperationDiagnosticRecord("signing-key", "additional-observations-omitted", { omittedCount: omitted }));
    return { key: keys.get(kid), observations };
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
        const field = alg !== "RS256" ? "alg" : "kid";
        const prefix = field === "alg" ? "algorithm" : "key-id";
        const raw = decoded.value.header[field];
        const reason = raw === undefined ? `${prefix}-missing` : typeof raw !== "string" ? `${prefix}-wrong-type` : raw.length === 0 ? `${prefix}-empty` : "algorithm-unsupported";
        return invalidToken("JWT header must include RS256 alg and kid.", reason as SecurityOperationReason<"token">);
      }

      const lookup = await keyForKid(kid);
      const key = lookup.key;
      if (key === undefined) {
        return { ok: false, error: { code: "PLATFORM_SECURITY_INVALID_TOKEN", defaultMessage: "JWT signing key id was not found in JWKS.", diagnosticRecord: securityOperationDiagnosticRecord("signing-key", "no-matching-usable-key"), ...(lookup.observations.length === 0 ? {} : { relatedDiagnosticRecords: lookup.observations }) } };
      }

      const verifier = createVerify("RSA-SHA256");
      verifier.update(decoded.value.signingInput);
      verifier.end();
      if (!verifier.verify(key, decoded.value.signature)) {
        return invalidToken("JWT signature is invalid.", "signature-invalid");
      }

      const optionalTimeObservations: DiagnosticRecord[] = [];
      if (decoded.value.claims["nbf"] !== undefined && numberClaim(decoded.value.claims, "nbf") === undefined) optionalTimeObservations.push(securityOperationDiagnosticRecord("token", "not-before-wrong-type-ignored"));
      if (decoded.value.claims["iat"] !== undefined && numberClaim(decoded.value.claims, "iat") === undefined) optionalTimeObservations.push(securityOperationDiagnosticRecord("token", "issued-at-wrong-type-ignored"));
      const claimsValidation = validateJwtClaims(decoded.value.claims, {
        issuer: configuration.issuer,
        requiredClaims: configuration.requiredClaims,
        clock,
        clockSkewSeconds,
      });
      if (!claimsValidation.ok) {
        return optionalTimeObservations.length === 0 ? claimsValidation : { ok: false, error: { ...claimsValidation.error, relatedDiagnosticRecords: optionalTimeObservations } };
      }

      return {
        ok: true,
        value: {
          header: decoded.value.header,
          claims: decoded.value.claims,
          ...(optionalTimeObservations.length === 0 ? {} : { relatedDiagnosticRecords: optionalTimeObservations }),
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
    return invalidToken("JWT issuer does not match the configured issuer.", stringFailure(claims["iss"], "issuer", "issuer-mismatch"));
  }

  for (const [referenceIndex, requiredClaim] of (options.requiredClaims ?? []).entries()) {
    if (!matchesRequiredClaim(claims[requiredClaim.claim], requiredClaim)) {
      const actual = claims[requiredClaim.claim];
      const expected = "equals" in requiredClaim ? [requiredClaim.equals] : requiredClaim.oneOf;
      return invalidToken(`JWT claim ${requiredClaim.claim} does not match the configured value.`, actual === undefined ? "required-claim-missing" : !isClaimScalar(actual) || expected.length > 0 && !expected.some((value) => typeof value === typeof actual) ? "required-claim-wrong-type" : "required-claim-mismatch", referenceIndex);
    }
  }

  const nowSeconds = Math.floor(options.clock.now().getTime() / 1000);
  const expiresAt = numberClaim(claims, "exp");
  if (expiresAt === undefined || expiresAt <= nowSeconds - options.clockSkewSeconds) {
    return invalidToken("JWT is expired or missing exp.", claims["exp"] === undefined ? "expiry-missing" : expiresAt === undefined ? "expiry-wrong-type" : "expired");
  }

  const notBefore = numberClaim(claims, "nbf");
  if (notBefore !== undefined && notBefore > nowSeconds + options.clockSkewSeconds) {
    return invalidToken("JWT is not valid yet.", "not-before-in-future");
  }

  const issuedAt = numberClaim(claims, "iat");
  if (issuedAt !== undefined && issuedAt > nowSeconds + options.clockSkewSeconds) {
    return invalidToken("JWT issued-at time is in the future.", "issued-at-in-future");
  }

  if (stringClaim(claims, "sub") === undefined) {
    return invalidToken("JWT subject is missing.", stringFailure(claims["sub"], "subject", "subject-empty"));
  }

  return { ok: true, value: undefined };
}

function matchesRequiredClaim(
  actual: JsonValue | undefined,
  requirement: PlatformJwtClaimRequirement,
): boolean {
  if (!isClaimScalar(actual)) {
    return false;
  }

  if ("equals" in requirement) {
    return actual === requirement.equals;
  }

  return requirement.oneOf.length > 0 && requirement.oneOf.some((expected) => actual === expected);
}

function decodeJwt(token: string): Result<{
  readonly header: Readonly<Record<string, JsonValue>>;
  readonly claims: PrincipalClaims;
  readonly signingInput: string;
  readonly signature: Buffer;
}, PlatformSecurityError> {
  const parts = token.split(".");
  if (parts.length !== 3 || parts.some((part) => part.length === 0)) {
    return invalidToken("JWT must have header, payload, and signature segments.", parts.length !== 3 ? "segment-count" : "empty-segment");
  }

  const [encodedHeader, encodedPayload, encodedSignature] = parts as [string, string, string];
  const header = decodeJsonSegment(encodedHeader, "header");
  const claims = decodeJsonSegment(encodedPayload, "payload");
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

function decodeJsonSegment(segment: string, part: "header" | "payload"): Result<Readonly<Record<string, JsonValue>>, PlatformSecurityError> {
  try {
    const value = JSON.parse(Buffer.from(segment, "base64url").toString("utf8")) as unknown;
    if (isJsonObject(value)) {
      return { ok: true, value };
    }
    return invalidToken("JWT segment must decode to a JSON object.", `${part}-not-object`);
  } catch {
    return invalidToken("JWT segment must decode to a JSON object.", `${part}-json-invalid`);
  }
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

function isClaimScalar(value: JsonValue | undefined): value is PlatformJwtClaimScalar {
  return typeof value === "string" || typeof value === "number" || typeof value === "boolean";
}

function invalidToken(defaultMessage: string, reason: SecurityOperationReason<"token">, referenceIndex?: number): Result<never, PlatformSecurityError> {
  return {
    ok: false,
    error: {
      code: "PLATFORM_SECURITY_INVALID_TOKEN",
      defaultMessage,
      diagnosticRecord: securityOperationDiagnosticRecord("token", reason, referenceIndex === undefined ? {} : { referenceIndex }),
    },
  };
}

function isJsonObject(value: unknown): value is Readonly<Record<string, JsonValue>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

const defaultJwksFetcher: PlatformJwksFetcher = {
  async fetch(uri) {
    let response: Response;
    try { response = await fetch(uri); }
    catch (error) { throw observeSecurityFailure(error, securityOperationDiagnosticRecord("signing-key", "fetch-failed")); }
    if (!response.ok) {
      throw observeSecurityFailure(new Error(`JWKS request failed with status ${response.status}.`), securityOperationDiagnosticRecord("signing-key", "http-unsuccessful"));
    }

    let value: unknown;
    try { value = await response.json(); }
    catch (error) { throw observeSecurityFailure(error, securityOperationDiagnosticRecord("signing-key", "response-json-invalid")); }
    if (!isJwks(value)) {
      throw observeSecurityFailure(new Error("JWKS response did not contain a keys array."), securityOperationDiagnosticRecord("signing-key", "key-set-invalid"));
    }

    return value;
  },
};

function stringFailure(value: JsonValue | undefined, prefix: "issuer" | "subject", mismatch: SecurityOperationReason<"token">): SecurityOperationReason<"token"> {
  return value === undefined ? `${prefix}-missing` : typeof value !== "string" ? `${prefix}-wrong-type` : value.length === 0 ? `${prefix}-empty` : mismatch;
}

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
