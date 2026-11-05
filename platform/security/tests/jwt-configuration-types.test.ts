import { createJwksJwtVerifier, validateJwtVerifierConfiguration, type PlatformJwtVerificationOptions, type PlatformJwtVerifier } from "../src/index";
import type { PlatformJwtVerificationOptions as LegacyOptions } from "../src/jwt";
declare const options: LegacyOptions;
const same: PlatformJwtVerificationOptions = options;
const verifier: PlatformJwtVerifier = createJwksJwtVerifier(same);
const result = validateJwtVerifierConfiguration(same);
if (result.ok) {
  const seconds: number = result.value.clockSkewSeconds;
  // @ts-expect-error Checked instructions are readonly.
  result.value.issuer = "changed";
  // @ts-expect-error Checked claim lists are readonly.
  result.value.requiredClaims.push({ claim: "role", equals: false });
  void seconds;
}
// @ts-expect-error A number must not be supplied as text.
createJwksJwtVerifier({ issuer: "issuer", jwksUri: "https://example.invalid", clockSkewSeconds: "60" });
void verifier;
