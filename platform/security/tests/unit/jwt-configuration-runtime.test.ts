import { deepEqual, equal, throws } from "node:assert/strict";
import { createSign, generateKeyPairSync } from "node:crypto";
import { createJwksJwtVerifier, validateJwtVerifierConfiguration, jwtDefaultClockSkewSeconds, jwtConfigurationDiagnostic,
  jwtConfigurationError, isJwtConfigurationError, securityFailureDiagnosticRecord, securityDiagnosticRecordsFrom,
  type PlatformJwtVerificationOptions, type PlatformJsonWebKey } from "../../src/index";
import { parseDiagnosticRecord, type DiagnosticRecord } from "@kanbien/core/diagnostics";

const canary = "PRIVATE_JWT_CONFIGURATION_CANARY";
const issue = (setting: string, reason: string, index?: number, attributeIndex?: number) => ({ setting, reason,
  ...(index === undefined ? {} : { index }), ...(attributeIndex === undefined ? {} : { attributeIndex }) });
const packet = (issues: readonly unknown[], truncated = false) => ({ schema: "core/diagnostic-record/v1", code: "security.jwt-configuration-invalid", definitionVersion: 1,
  detail: { phase: "verifier-construction", effect: "verifier-not-created", issues, truncated } });
const asOptions = (value: unknown) => value as PlatformJwtVerificationOptions;
let fetches = 0, clocks = 0;
const clock = { now() { equal(this, clock); clocks++; return new Date(1_000_000); } };
const fetchJwks = { async fetch(uri: string) { equal(this, fetchJwks); fetches++; equal(uri, "opaque-source"); return { keys: [publicJwk] }; } };
const base = { issuer: "issuer", jwksUri: "opaque-source", clock, fetchJwks };
const { publicKey, privateKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
const publicJwk: PlatformJsonWebKey = { ...publicKey.export({ format: "jwk" }), kid: "fixture-key", alg: "RS256" };
function token(overrides: Record<string, unknown> = {}): string {
  const header = Buffer.from(JSON.stringify({ alg: "RS256", kid: "fixture-key" })).toString("base64url");
  const claims = Buffer.from(JSON.stringify({ iss: "issuer", sub: "subject", exp: 2000, ...overrides })).toString("base64url");
  const input = `${header}.${claims}`, signer = createSign("RSA-SHA256"); signer.update(input); signer.end();
  return `${input}.${signer.sign(privateKey).toString("base64url")}`;
}
function rejected(overrides: Record<string, unknown>, expected: readonly unknown[]): void {
  const options = asOptions({ ...base, ...overrides });
  const result = validateJwtVerifierConfiguration(options);
  equal(result.ok, false);
  if (result.ok) throw Error("Expected configuration rejection");
  deepEqual(result.error, { code: "PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID", diagnosticRecord: packet(expected) });
  equal(JSON.stringify(result).includes(canary), false);
  const before = [fetches, clocks];
  throws(() => createJwksJwtVerifier(options), error => {
    equal(isJwtConfigurationError(error), true); equal(error instanceof TypeError, true);
    equal((error as Error).message, "PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID");
    deepEqual(securityFailureDiagnosticRecord(error), packet(expected));
    deepEqual(securityDiagnosticRecordsFrom(error), [packet(expected)]); return true;
  });
  deepEqual([fetches, clocks], before, "rejection never probes injected dependencies");
}
async function main(): Promise<void> {
  equal(jwtDefaultClockSkewSeconds, 60);
  const defaulted = validateJwtVerifierConfiguration(base); if (!defaulted.ok) throw Error("fixture-invalid");
  equal(defaulted.value.clockSkewSeconds, 60); deepEqual(defaulted.value.requiredClaims, []);
  for (const value of [0, -0, 0.5, 30, Number.MAX_VALUE]) equal(validateJwtVerifierConfiguration({ ...base, clockSkewSeconds: value }).ok, true);
  for (const [value, reason] of [[null, "wrong-type"], ["30", "wrong-type"], [true, "wrong-type"], [NaN, "not-finite"], [Infinity, "not-finite"], [-Infinity, "not-finite"], [-1, "negative"]] as const)
    rejected({ clockSkewSeconds: value }, [issue("clock-tolerance", reason)]);
  for (const name of ["issuer", "jwksUri"]) for (const [value, reason] of [[undefined, "missing"], [null, "wrong-type"], [42, "wrong-type"], ["", "empty"], [" \t", "blank"], [` ${canary}`, "surrounding-whitespace"]] as const)
    rejected({ [name]: value }, [issue(name === "issuer" ? "issuer" : "key-source", reason)]);
  for (const [jwksUri, reason] of [["not-an-address", "invalid-format"], ["http://example.invalid/keys", "unsupported-scheme"], ["file:///fixture", "unsupported-scheme"]] as const)
    rejected({ fetchJwks: undefined, jwksUri }, [issue("key-source", reason)]);
  equal(validateJwtVerifierConfiguration({ issuer: "issuer", jwksUri: "https://example.invalid/keys" }).ok, true);
  for (const value of [null, {}, [], { now: 1 }]) rejected({ clock: value }, [issue("clock.now", "not-callable")]);
  for (const value of [null, {}, [], { fetch: 1 }]) rejected({ fetchJwks: value }, [issue("key-fetcher.fetch", "not-callable")]);
  for (const value of [null, {}, "rules"]) rejected({ requiredClaims: value }, [issue("required-claims", "wrong-type")]);
  rejected({ requiredClaims: [null] }, [issue("required-claims", "wrong-type", 0)]);
  rejected({ requiredClaims: [{ equals: false }] }, [issue("required-claim.name", "missing", 0)]);
  for (const [claim, reason] of [[1, "wrong-type"], ["", "empty"], [" ", "blank"], [" role", "surrounding-whitespace"]] as const)
    rejected({ requiredClaims: [{ claim, equals: false }] }, [issue("required-claim.name", reason, 0)]);
  rejected({ requiredClaims: [{ claim: "role" }] }, [issue("required-claim.comparison", "comparison-missing", 0)]);
  rejected({ requiredClaims: [{ claim: "role", equals: true, oneOf: [true] }] }, [issue("required-claim.comparison", "comparison-conflict", 0)]);
  for (const value of [undefined, null, {}, [], NaN, Infinity]) rejected({ requiredClaims: [{ claim: "role", equals: value }] }, [issue("required-claim.value", "unsupported-value", 0)]);
  rejected({ requiredClaims: [{ claim: "role", oneOf: true }] }, [issue("required-claim.value", "wrong-type", 0)]);
  rejected({ requiredClaims: [{ claim: "role", oneOf: [] }] }, [issue("required-claim.value", "empty", 0)]);
  rejected({ requiredClaims: [{ claim: "role", oneOf: [false, canary, null, NaN] }] }, [issue("required-claim.value", "unsupported-value", 0, 2), issue("required-claim.value", "unsupported-value", 0, 3)]);
  rejected({ issuer: "", clockSkewSeconds: NaN }, [issue("issuer", "empty"), issue("clock-tolerance", "not-finite")]);
  const overflow = validateJwtVerifierConfiguration(asOptions({ ...base, requiredClaims: Array(33).fill(null) }));
  if (overflow.ok) throw Error("Expected overflow");
  deepEqual(overflow.error.diagnosticRecord, packet(Array.from({ length: 32 }, (_, index) => issue("required-claims", "wrong-type", index)), true));
  for (const badRoot of [null, [], 1]) { const result = validateJwtVerifierConfiguration(asOptions(badRoot)); if (result.ok) throw Error("Expected invalid root"); deepEqual(result.error.diagnosticRecord, packet([issue("configuration", "wrong-type")])); }
  const cause = Object.freeze(new Error(canary));
  for (const property of ["issuer", "jwksUri", "clockSkewSeconds", "requiredClaims", "clock", "fetchJwks"]) {
    const options = Object.defineProperty({ ...base }, property, { get() { throw cause; } });
    throws(() => createJwksJwtVerifier(options), value => value === cause);
  }
  throws(() => createJwksJwtVerifier({ ...base, clock: Object.defineProperty({}, "now", { get() { throw cause; } }) as never }), value => value === cause);
  throws(() => createJwksJwtVerifier({ ...base, fetchJwks: Object.defineProperty({}, "fetch", { get() { throw cause; } }) as never }), value => value === cause);
  equal(isJwtConfigurationError(Object.assign(new TypeError("PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID"), { code: "PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID" })), false);
  throws(() => jwtConfigurationError({ ...packet([issue("issuer", "missing")]), detail: { raw: canary } } as DiagnosticRecord), TypeError);
  equal(parseDiagnosticRecord(jwtConfigurationDiagnostic, packet([issue(canary, "missing")])).ok, false);
  const before = [fetches, clocks], verifier = createJwksJwtVerifier(base);
  deepEqual([fetches, clocks], before);
  equal((await verifier.verify(token())).ok, true); equal(fetches, before[0]! + 1); equal(clocks, before[1]! + 1);
  equal((await verifier.verify(token({ iss: "Issuer" }))).ok, false);
  equal((await verifier.verify(token({ iss: "issuer/" }))).ok, false);
  equal((await verifier.verify(token({ exp: 940 }))).ok, false); equal((await verifier.verify(token({ exp: 941 }))).ok, true);
  equal((await createJwksJwtVerifier({ ...base, clockSkewSeconds: 0 }).verify(token({ exp: 1000 }))).ok, false);
  equal((await createJwksJwtVerifier({ ...base, clockSkewSeconds: 0.5 }).verify(token({ exp: 999.75 }))).ok, true);
  for (const scalar of [0, false, ""]) for (const rule of [{ claim: "role", equals: scalar }, { claim: "role", oneOf: [scalar] }]) {
    const configured = createJwksJwtVerifier({ ...base, requiredClaims: [rule] });
    equal((await configured.verify(token({ role: scalar }))).ok, true);
    equal((await configured.verify(token({ role: null }))).ok, false);
  }
  const typedClaim = createJwksJwtVerifier({ ...base, requiredClaims: [{ claim: "role", oneOf: [1] }] });
  equal((await typedClaim.verify(token({ role: 1 }))).ok, true); equal((await typedClaim.verify(token({ role: "1" }))).ok, false);
  const reportBuilder = require("../../src/jwt-configuration/contract/reporting/diagnostics") as {
    jwtConfigurationDiagnosticRecord(input: { issues: readonly unknown[]; truncated: boolean }): DiagnosticRecord;
  };
  for (const unsafe of [issue("required-claim.name", "missing"), issue("clock-tolerance", "negative", 0), issue("issuer", "empty", undefined, 0)])
    throws(() => reportBuilder.jwtConfigurationDiagnosticRecord({ issues: [unsafe], truncated: false }), TypeError);
  const requiredClaims = [{ claim: "role", oneOf: ["reader"] }], mutable = { ...base, requiredClaims };
  const stable = createJwksJwtVerifier(mutable);
  mutable.issuer = "changed"; mutable.jwksUri = "changed"; requiredClaims[0]!.claim = "changed"; requiredClaims[0]!.oneOf[0] = "changed";
  equal((await stable.verify(token({ role: "reader" }))).ok, true, "the real verifier consumes the checked snapshot");
  equal((await stable.verify(token({ role: "changed" }))).ok, false);
  let clockReads = 0, fetchReads = 0;
  const statefulClock = { calls: 0, get now() { clockReads++; return function (this: typeof statefulClock) { this.calls++; return new Date(1_000_000); }; } };
  const statefulFetcher = { calls: 0, get fetch() { fetchReads++; return async function (this: typeof statefulFetcher, uri: string) {
    equal(uri, "opaque-source"); this.calls++; return { keys: [publicJwk] };
  }; } };
  const bound = createJwksJwtVerifier({ ...base, clock: statefulClock, fetchJwks: statefulFetcher });
  equal(clockReads, 1); equal(fetchReads, 1); equal(statefulClock.calls, 0); equal(statefulFetcher.calls, 0);
  equal(Object.isFrozen(statefulClock), false); equal(Object.isFrozen(statefulFetcher), false);
  equal((await bound.verify(token())).ok, true); equal((await bound.verify(token())).ok, true);
  equal(clockReads, 1); equal(fetchReads, 1); equal(statefulClock.calls, 2); equal(statefulFetcher.calls, 1);
  const implementation = require("../../src/jwt-configuration/domain/validation") as { validateJwtVerifierConfiguration: typeof validateJwtVerifierConfiguration };
  const original = implementation.validateJwtVerifierConfiguration;
  const failure = validateJwtVerifierConfiguration({ ...base, issuer: "" }); if (failure.ok) throw Error("fixture-invalid");
  try {
    implementation.validateJwtVerifierConfiguration = () => failure;
    throws(() => createJwksJwtVerifier(base), isJwtConfigurationError);
    implementation.validateJwtVerifierConfiguration = () => defaulted;
    equal((await createJwksJwtVerifier(asOptions({ issuer: "unchecked", jwksUri: "unchecked", clockSkewSeconds: -1 })).verify(token())).ok, true,
      "actual constructor uses returned checked values instead of original instructions");
  } finally { implementation.validateJwtVerifierConfiguration = original; }
  console.log("JWT configuration predicates, default/fractional policy, snapshots, real verifier wiring and safe failures passed.");
}
void main().catch(error => { console.error(error); process.exitCode = 1; });
