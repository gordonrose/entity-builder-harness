import type { Clock, JsonValue, PrincipalClaims, Result } from "@kanbien/core";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { PlatformSecurityError } from "./errors";

export interface PlatformJwtVerificationOptions {
  readonly issuer: string;
  readonly jwksUri: string;
  readonly requiredClaims?: readonly PlatformJwtClaimRequirement[];
  readonly clock?: Clock;
  readonly clockSkewSeconds?: number;
  readonly fetchJwks?: PlatformJwksFetcher;
}

export type PlatformJwtClaimRequirement = PlatformJwtExactClaimRequirement | PlatformJwtOneOfClaimRequirement;

/** Require a JWT claim to match one exact configured scalar value. */
export interface PlatformJwtExactClaimRequirement {
  readonly claim: string;
  readonly equals: PlatformJwtClaimScalar;
}

/** Require a JWT claim to match one of a finite, explicitly configured set of scalar values. */
export interface PlatformJwtOneOfClaimRequirement {
  readonly claim: string;
  readonly oneOf: readonly PlatformJwtClaimScalar[];
}

/** The only JWT claim values that may be used as configured verification requirements. */
export type PlatformJwtClaimScalar = string | number | boolean;

export interface PlatformJwtVerifier {
  verify(token: string): Promise<Result<PlatformVerifiedJwt, PlatformSecurityError>>;
}

export interface PlatformVerifiedJwt {
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
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
