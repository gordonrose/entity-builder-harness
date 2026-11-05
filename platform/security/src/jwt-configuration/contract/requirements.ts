import { configReasonNames } from "@kanbien/core/config";
import type { PlatformJwtVerificationOptions, PlatformJwtClaimRequirement } from "../../jwt-contract";

export const jwtDefaultClockSkewSeconds = 60;
export const jwtConfigurationSettings = ["configuration", "issuer", "key-source", "clock-tolerance", "required-claims",
  "required-claim.name", "required-claim.comparison", "required-claim.value", "clock.now", "key-fetcher.fetch"] as const;
export const jwtConfigurationReasons = [configReasonNames.missing, configReasonNames.wrongType, configReasonNames.empty,
  configReasonNames.blank, configReasonNames.surroundingWhitespace, configReasonNames.invalidFormat,
  configReasonNames.unsupportedValue, "not-finite", "negative", "unsupported-scheme", "comparison-missing", "comparison-conflict", "not-callable"] as const;
export type JwtConfigurationSetting = (typeof jwtConfigurationSettings)[number];
export type JwtConfigurationReason = (typeof jwtConfigurationReasons)[number];
export type CheckedJwtVerifierConfiguration = Readonly<Pick<PlatformJwtVerificationOptions, "issuer" | "jwksUri" | "clock" | "fetchJwks"> & {
  readonly clockSkewSeconds: number;
  readonly requiredClaims: readonly PlatformJwtClaimRequirement[];
}>;
