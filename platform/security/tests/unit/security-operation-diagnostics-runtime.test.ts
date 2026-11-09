import { deepEqual, equal, ok, rejects, throws } from "node:assert/strict";
import { createSign, generateKeyPairSync } from "node:crypto";
import type { Permission } from "@kanbien/core/authz";
import type { Clock } from "@kanbien/core/shared";
import { securityOperationReasons } from "@kanbien/core/security";
import { parseDiagnosticRecord, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import {
  createJwksJwtVerifier, createJwtBearerAuthenticationHook, observeBearerTokenFromHeaders,
  observeCorsPolicyForRequestOrigin, observePermissionsFromClaims, authorizePlatformPermissions,
  createInMemoryPlatformRateLimiter, observePlatformRateLimitCheck,
  platformSecurityDiagnosticCatalog, securityOperationDiagnosticRecord, securityFailureDiagnosticRecord,
  securityDiagnosticRecordsFrom, observeSecurityFailure, type PlatformJsonWebKey, type PlatformJwksFetcher,
  securityRateLimitClockFailureRecord,
} from "../../src/index";

const canary = "synthetic-sensitive-security-canary";
const { publicKey, privateKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
const publicJwk = { ...publicKey.export({ format: "jwk" }), kid: "fixture", kty: "RSA" } as PlatformJsonWebKey;
const clock = { now: () => new Date(1_000_000) };
const baseClaims = { iss: "issuer", sub: canary, exp: 2000, role: "reader" };
const segment = (value: unknown) => Buffer.from(JSON.stringify(value)).toString("base64url");
function token(claims: Record<string, unknown> = {}, header: unknown = { alg: "RS256", kid: "fixture" }): string {
  const input = `${segment(header)}.${segment({ ...baseClaims, ...claims })}`;
  const signer = createSign("RSA-SHA256"); signer.update(input); signer.end();
  return `${input}.${signer.sign(privateKey).toString("base64url")}`;
}
function verifier(fetchJwks: PlatformJwksFetcher = { fetch: async () => ({ keys: [publicJwk] }) }) {
  return createJwksJwtVerifier({ issuer: "issuer", jwksUri: `https://${canary}.invalid/keys`, clock,
    requiredClaims: [{ claim: "role", equals: "reader" }], fetchJwks });
}
function reason(record: DiagnosticRecord | undefined): string {
  ok(record); equal(JSON.stringify(record).includes(canary), false);
  const definition = platformSecurityDiagnosticCatalog.definitions.find((item) => item.code === record.code && item.version === record.definitionVersion);
  ok(definition); equal(parseDiagnosticRecord(definition as DiagnosticDefinition, record).ok, true);
  return (record.detail as { reason: string }).reason;
}
async function invalid(value: string, expected: string) {
  const result = await verifier().verify(value); equal(result.ok, false);
  if (!result.ok) { equal(result.error.code, "PLATFORM_SECURITY_INVALID_TOKEN"); equal(reason(result.error.diagnosticRecord), expected); }
}

async function main() {
  await rateLimitClockObservations();
  equal(Object.isFrozen(securityOperationReasons), true);
  for (const reasons of Object.values(securityOperationReasons)) equal(Object.isFrozen(reasons), true);
  for (const [phase, reasons] of Object.entries(securityOperationReasons)) for (const value of reasons) {
    const definition = platformSecurityDiagnosticCatalog.definitions.find((item) => item.code === `security.${phase}.${value}`);
    ok(definition, `${phase}.${value} is executable and registered`);
    ok(definition.detail.type === "object");
    const extra: Record<string, unknown> = {};
    for (const [name, schema] of Object.entries(definition.detail.properties)) {
      if (["phase", "reason", "effect"].includes(name) || definition.detail.optional?.includes(name)) continue;
      extra[name] = schema.type === "enum" ? schema.values[0] : schema.type === "integer" ? schema.minimum : undefined;
    }
    const record = { schema: "core/diagnostic-record/v1", code: definition.code, definitionVersion: 1, detail: { phase, reason: value, effect: "not-assessed", ...extra } };
    equal(parseDiagnosticRecord(definition as DiagnosticDefinition, record).ok, true);
    equal(parseDiagnosticRecord(definition as DiagnosticDefinition, { ...record, detail: { ...record.detail, token: canary } }).ok, false);
    equal(parseDiagnosticRecord(definition as DiagnosticDefinition, { ...record, detail: { ...record.detail, reason: "unregistered" } }).ok, false);
    for (const name of Object.keys(extra)) {
      const incomplete: Record<string, unknown> = { ...record.detail }; delete incomplete[name];
      equal(parseDiagnosticRecord(definition as DiagnosticDefinition, { ...record, detail: incomplete }).ok, false, `${phase}.${value} requires ${name}`);
    }
  }
  // @ts-expect-error token detail cannot contain rate-limit context
  throws(() => securityOperationDiagnosticRecord("token", "expired", { keyCategory: "principal" }), /DIAGNOSTIC_INVALID/);
  // @ts-expect-error CORS detail cannot contain adapter configuration references
  throws(() => securityOperationDiagnosticRecord("cors", "origin-missing", { reference: "table" }), /DIAGNOSTIC_INVALID/);
  let getterRead = false;
  equal(securityFailureDiagnosticRecord(Object.defineProperty({}, "diagnosticRecord", { get() { getterRead = true; throw new Error(canary); } })), undefined);
  equal(getterRead, false);
  const untrusted = { diagnosticRecord: { ...securityOperationDiagnosticRecord("token", "expired"), secret: canary }, relatedDiagnosticRecords: [{ bad: canary }] };
  deepEqual(securityDiagnosticRecordsFrom(untrusted), []);
  const reused = new Error(canary);
  observeSecurityFailure(reused, securityOperationDiagnosticRecord("signing-key", "fetch-failed"), [securityOperationDiagnosticRecord("token", "expired")]);
  equal(securityDiagnosticRecordsFrom(reused).length, 2);
  observeSecurityFailure(reused, securityOperationDiagnosticRecord("authentication", "component-failed"));
  equal(securityDiagnosticRecordsFrom(reused).length, 1, "new invocation clears old companions");
  observeSecurityFailure(reused, { ...securityOperationDiagnosticRecord("token", "expired"), secret: canary } as DiagnosticRecord);
  deepEqual(securityDiagnosticRecordsFrom(reused), [], "even retained JS-injected records are validated before extraction");

  for (const [headers, expected] of [[{}, "missing"], [{ authorization: [] }, "missing"], [{ authorization: "Basic private" }, "unsupported-scheme"], [{ authorization: "Bearer" }, "malformed-bearer"], [{ authorization: "" }, "malformed-bearer"]] as const) {
    equal(reason(observeBearerTokenFromHeaders(headers).diagnosticRecord), expected);
  }
  equal(observeBearerTokenFromHeaders({ Authorization: [`bEaReR ${canary}`, "invalid"], authorization: "ignored" }).token, canary, "first case-insensitive header and first array value remain authoritative");
  equal(observeBearerTokenFromHeaders({ authorization: "Bearer   " }).token, " ", "preserve permissive existing whitespace acceptance");
  await invalid("one.two", "segment-count"); await invalid("one..three", "empty-segment");
  await invalid(`!.${segment({})}.eA`, "header-json-invalid");
  await invalid(`${segment([])}.${segment({})}.eA`, "header-not-object");
  await invalid(`${segment({})}.!.eA`, "payload-json-invalid");
  await invalid(`${segment({})}.${segment(null)}.eA`, "payload-not-object");
  for (const [header, expected] of [[{ kid: "fixture" }, "algorithm-missing"], [{ alg: 1, kid: "fixture" }, "algorithm-wrong-type"], [{ alg: "", kid: "fixture" }, "algorithm-empty"], [{ alg: "none", kid: "fixture" }, "algorithm-unsupported"], [{ alg: "RS256" }, "key-id-missing"], [{ alg: "RS256", kid: 1 }, "key-id-wrong-type"], [{ alg: "RS256", kid: "" }, "key-id-empty"]] as const) await invalid(token({}, header), expected);
  await invalid(`${token().split(".").slice(0, 2).join(".")}.eA`, "signature-invalid");
  for (const [claims, expected] of [[{ iss: undefined }, "issuer-missing"], [{ iss: 1 }, "issuer-wrong-type"], [{ iss: "" }, "issuer-empty"], [{ iss: "other" }, "issuer-mismatch"], [{ role: undefined }, "required-claim-missing"], [{ role: [] }, "required-claim-wrong-type"], [{ role: 1 }, "required-claim-wrong-type"], [{ role: "other" }, "required-claim-mismatch"], [{ exp: undefined }, "expiry-missing"], [{ exp: "2000" }, "expiry-wrong-type"], [{ exp: 940 }, "expired"], [{ nbf: 1061 }, "not-before-in-future"], [{ iat: 1061 }, "issued-at-in-future"], [{ sub: undefined }, "subject-missing"], [{ sub: 1 }, "subject-wrong-type"], [{ sub: "" }, "subject-empty"]] as const) await invalid(token(claims), expected);
  for (const claims of [{ exp: 941 }, { nbf: 1060 }, { iat: 1060 }, { nbf: "ignored" }, { iat: null }]) equal((await verifier().verify(token(claims))).ok, true, "expiry/skew and ignored optional wrong-type time values remain compatible");
  const ignoredTimes = await verifier().verify(token({ nbf: canary, iat: null }));
  if (ignoredTimes.ok) deepEqual(ignoredTimes.value.relatedDiagnosticRecords?.map(reason), ["not-before-wrong-type-ignored", "issued-at-wrong-type-ignored"]);
  const required = await verifier().verify(token({ role: "other" }));
  if (!required.ok) deepEqual(required.error.diagnosticRecord?.detail, { phase: "token", reason: "required-claim-mismatch", effect: "not-assessed", referenceIndex: 0 });
  const none = await verifier({ fetch: async () => ({ keys: [{ kid: "other", kty: "EC" }] }) }).verify(token());
  if (!none.ok) equal(reason(none.error.diagnosticRecord), "no-matching-usable-key"); else throw new Error("Expected no matching key");
  const skipped = await verifier({ fetch: async () => ({ keys: [{}, { kid: "a", kty: "EC" }, { kid: "b", kty: "RSA" }, { kid: "c", kty: "RSA", n: "x" }] }) }).verify(token());
  if (!skipped.ok) deepEqual(skipped.error.relatedDiagnosticRecords?.map(reason), ["key-id-absent", "key-type-unsupported", "key-modulus-absent", "key-exponent-absent"]); else throw new Error("Expected skipped keys");
  const manyKeys = await verifier({ fetch: async () => ({ keys: Array.from({ length: 10 }, () => ({})) }) }).verify(token());
  if (!manyKeys.ok) deepEqual(manyKeys.error.relatedDiagnosticRecords?.at(-1)?.detail, { phase: "signing-key", reason: "additional-observations-omitted", effect: "not-assessed", omittedCount: 3 });
  let calls = 0;
  const cached = verifier({ fetch: async () => { calls++; return { keys: [publicJwk] }; } });
  equal((await cached.verify(token())).ok, true); equal((await cached.verify(token())).ok, true); equal(calls, 1, "cache semantics unchanged");
  const native = Object.assign(new Error(canary), { cause: Object.assign(new Error(canary), { code: "CERT_HAS_EXPIRED" }) });
  await rejects(() => verifier({ fetch: async () => { throw native; } }).verify(token()), (error: unknown) => {
    equal(error, native); equal(reason(securityFailureDiagnosticRecord(error)), "fetch-failed");
    deepEqual(securityDiagnosticRecordsFrom(error).map((record) => (record.detail as { reason: string }).reason), ["fetch-failed", "expired"]); return true;
  });
  await rejects(() => verifier({ fetch: async () => ({ keys: [{ kid: "fixture", kty: "RSA", n: null, e: "AQAB" } as unknown as PlatformJsonWebKey] }) }).verify(token()), (error: unknown) => { equal(reason(securityFailureDiagnosticRecord(error)), "key-material-invalid"); return true; });
  await rejects(() => verifier({ fetch: async () => ({ keys: [null as unknown as PlatformJsonWebKey] }) }).verify(token()), (error: unknown) => { deepEqual(securityFailureDiagnosticRecord(error)?.detail, { phase: "signing-key", reason: "key-entry-unreadable", effect: "not-assessed", referenceIndex: 0 }); return true; });
  const primitiveKey = await verifier({ fetch: async () => ({ keys: [1 as unknown as PlatformJsonWebKey] }) }).verify(token());
  equal(primitiveKey.ok, false); if (!primitiveKey.ok) equal(reason(primitiveKey.error.relatedDiagnosticRecords?.[0]), "key-id-absent", "primitive property access previously skipped; do not tighten acceptance");
  const originalFetch = globalThis.fetch;
  try {
    for (const [response, expected] of [[new Response("", { status: 503 }), "http-unsuccessful"], [new Response("not json"), "response-json-invalid"], [new Response("{}"), "key-set-invalid"]] as const) {
      globalThis.fetch = async () => response;
      const real = createJwksJwtVerifier({ issuer: "issuer", jwksUri: "https://invalid.test/keys", clock });
      await rejects(() => real.verify(token()), (error: unknown) => { equal(reason(securityFailureDiagnosticRecord(error)), expected); return true; });
    }
  } finally { globalThis.fetch = originalFetch; }
  let verified = 0;
  const hook = createJwtBearerAuthenticationHook({ authz: {}, verifier: { verify: async () => { verified++; return { ok: false, error: { code: "PLATFORM_SECURITY_INVALID_TOKEN", defaultMessage: canary } }; } } });
  equal(reason((await hook.authenticate({})).diagnosticRecord), "missing"); equal(verified, 0);
  equal(reason((await hook.authenticate({ headers: { authorization: "Bearer x" } })).diagnosticRecord), "verifier-rejected-unclassified");
  const exact = createJwtBearerAuthenticationHook({ authz: {}, verifier: verifier() });
  equal(reason((await exact.authenticate({ headers: { authorization: `Bearer ${token({ exp: 940 })}` } })).diagnosticRecord), "expired");
  const combined = createJwtBearerAuthenticationHook({ verifier: verifier(), authz: { claims: Array.from({ length: 12 }, () => ({ claim: "missing", equals: true, permissions: [] })) } });
  const combinedResult = await combined.authenticate({ headers: { authorization: `Bearer ${token({ nbf: canary, iat: null })}` } });
  equal(combinedResult.authenticated, true); equal(combinedResult.relatedDiagnosticRecords?.length, 8);
  deepEqual(combinedResult.relatedDiagnosticRecords?.at(-1)?.detail, { phase: "authentication", reason: "additional-observations-omitted", effect: "not-assessed", omittedCount: 7 });
  const p = "safe:read" as Permission;
  const mixed = observePermissionsFromClaims({ roles: [canary, 1, "known"] }, { valueClaims: [{ claim: "roles", format: "string-array", values: { known: [p] } }] });
  deepEqual(mixed.permissions, [p]); deepEqual(mixed.relatedDiagnosticRecords.map(reason), ["claim-wrong-type", "claim-unmapped"]);
  for (const [claims, expected] of [[{}, "claim-missing"], [{ roles: [] }, "claim-empty"], [{ roles: 1 }, "claim-wrong-type"], [{ roles: [canary] }, "claim-unmapped"]] as const) equal(reason(observePermissionsFromClaims(claims, { valueClaims: [{ claim: "roles", format: "string-array", values: {} }] }).relatedDiagnosticRecords[0]), expected);
  const many = observePermissionsFromClaims({}, { claims: Array.from({ length: 12 }, () => ({ claim: canary, equals: true, permissions: [p] })) });
  equal(many.relatedDiagnosticRecords.length, 8); deepEqual(many.relatedDiagnosticRecords[7]?.detail, { phase: "authorization", reason: "additional-observations-omitted", effect: "not-assessed", omittedCount: 5 });
  const denied = authorizePlatformPermissions([p], []); if (!denied.ok) equal(reason(denied.error.diagnosticRecord), "permission-missing");
  for (const [origin, expected] of [[undefined, "origin-missing"], ["", "origin-empty"], [canary, "origin-not-allowlisted"], ["allowed", "origin-allowed"]] as const) equal(reason(observeCorsPolicyForRequestOrigin({ ...(origin === undefined ? {} : { requestOrigin: origin }), allowedOrigins: ["allowed"] }).diagnosticRecord), expected);
  let now = 0;
  const limiter = createInMemoryPlatformRateLimiter({ limit: 1, windowMs: 1000, maxBuckets: 1, clock: { now: () => new Date(now) } });
  equal(limiter.check(canary).allowed, true); equal(reason(limiter.check(canary).diagnosticRecord), "quota-exhausted");
  equal(reason(limiter.check("other").diagnosticRecord), "bucket-capacity-exhausted"); now = 1000; equal(limiter.check("other").allowed, true);
  const contextual = await observePlatformRateLimitCheck(limiter, "other", { boundary: "principal", keyCategory: "principal" });
  deepEqual(contextual.diagnosticRecord?.detail, { phase: "rate-limit", reason: "quota-exhausted", effect: "not-assessed", boundary: "principal", keyCategory: "principal" });
  await rejects(() => observePlatformRateLimitCheck({ check: () => { throw new Error(canary); } }, canary, { boundary: "transport", keyCategory: "client-address" }), (error: unknown) => { equal(reason(securityFailureDiagnosticRecord(error)), "dependency-failed"); return true; });
  let decisionGetter = false;
  const untrustedDecision = Object.defineProperty({ allowed: false, retryAfterMs: 1 }, "diagnosticRecord", { enumerable: true, get() { decisionGetter = true; throw new Error(canary); } });
  const deniedDecision = await observePlatformRateLimitCheck({ check: () => untrustedDecision }, canary, { boundary: "transport", keyCategory: "anonymous" });
  equal(deniedDecision.allowed, false); equal(deniedDecision.retryAfterMs, 1); equal(decisionGetter, false); equal(reason(deniedDecision.diagnosticRecord), "rejected-unclassified");
  throws(() => createInMemoryPlatformRateLimiter({ limit: 0 }), (error: unknown) => { equal(reason(securityFailureDiagnosticRecord(error)), "configuration-invalid"); return true; });
  let verifierGetter = false;
  const hostileVerifier = createJwtBearerAuthenticationHook({ authz: {}, verifier: { verify: async () => ({ ok: false, error: Object.defineProperty({ code: "PLATFORM_SECURITY_INVALID_TOKEN" as const, defaultMessage: canary }, "diagnosticRecord", { get() { verifierGetter = true; throw new Error(canary); } }) }) } });
  equal((await hostileVerifier.authenticate({ headers: { authorization: "Bearer x" } })).authenticated, false); equal(verifierGetter, false);
  const hugeCounts = createJwtBearerAuthenticationHook({ authz: {}, verifier: { verify: async () => ({ ok: true, value: { header: {}, claims: { sub: canary }, relatedDiagnosticRecords: Array(8).fill(securityOperationDiagnosticRecord("authentication", "additional-observations-omitted", { omittedCount: Number.MAX_SAFE_INTEGER })) } }) } });
  const hugeResult = await hugeCounts.authenticate({ headers: { authorization: "Bearer x" } }); equal(hugeResult.authenticated, true);
  deepEqual(hugeResult.relatedDiagnosticRecords?.[0]?.detail, { phase: "authentication", reason: "additional-observations-omitted", effect: "not-assessed", omittedCount: Number.MAX_SAFE_INTEGER });
  const hostileRelated = createJwtBearerAuthenticationHook({ authz: {}, verifier: { verify: async () => ({ ok: true, value: { header: {}, claims: { sub: canary }, relatedDiagnosticRecords: new Proxy([], { get() { throw new Error(canary); } }) } }) } });
  equal((await hostileRelated.authenticate({ headers: { authorization: "Bearer x" } })).authenticated, true);
  console.log("Security branch diagnostics: JWT/header/JWKS/authz/CORS/rate limits, compatibility boundaries, bounded observations and sensitive-canary exclusions passed.");
}

async function rateLimitClockObservations(): Promise<void> {
  const clockRecord = { schema: "core/diagnostic-record/v1", code: "security.rate-limit-clock-failed", definitionVersion: 1,
    detail: { phase: "clock-evaluation", reason: "evaluation-threw", effect: "decision-not-returned" } };
  const primary = { schema: "core/diagnostic-record/v1", code: "security.rate-limit.dependency-failed", definitionVersion: 1,
    detail: { phase: "rate-limit", reason: "dependency-failed", effect: "not-assessed", boundary: "principal", keyCategory: "principal" } };
  const context = { boundary: "principal", keyCategory: "principal" } as const;
  const caught = (run: () => unknown): unknown => { try { run(); } catch (error) { return error; } throw new Error("Expected clock failure."); };
  type Stage = "now-accessor" | "now-call" | "time-accessor" | "time-call";
  function fixture(stage: Stage, failure: unknown) {
    const counts = [0, 0, 0, 0];
    const date = Object.defineProperty({}, "getTime", { get() {
      counts[2]!++;
      if (stage === "time-accessor") throw failure;
      return function(this: unknown) { counts[3]!++; equal(this, date); throw failure; };
    } });
    const clock = Object.defineProperty({}, "now", { get() {
      counts[0]!++;
      if (stage === "now-accessor") throw failure;
      return function(this: unknown) { counts[1]!++; equal(this, clock); if (stage === "now-call") throw failure; return date; };
    } }) as Clock;
    return { clock, counts };
  }
  const failures = [new Error(canary), Object.freeze(new Error(canary)), { privateValue: canary }, null, undefined, canary, 7, function privateFailure() {}];
  for (const [stage, expected] of [["now-accessor", [1, 0, 0, 0]], ["now-call", [1, 1, 0, 0]], ["time-accessor", [1, 1, 1, 0]], ["time-call", [1, 1, 1, 1]]] as const) for (const failure of failures) {
    const direct = fixture(stage, failure);
    const limiter = createInMemoryPlatformRateLimiter({ clock: direct.clock });
    deepEqual(direct.counts, [0, 0, 0, 0]);
    equal(caught(() => limiter.check(canary)), failure, "producer preserves the exact object/frozen/primitive/function throw");
    deepEqual(direct.counts, expected);
    const objectFailure = typeof failure === "object" && failure !== null;
    deepEqual(securityDiagnosticRecordsFrom(failure), objectFailure ? [clockRecord] : [], "object-only retention never wraps a primitive just to add evidence");
    const wrapped = fixture(stage, failure);
    await rejects(() => observePlatformRateLimitCheck(createInMemoryPlatformRateLimiter({ clock: wrapped.clock }), canary, context), (error: unknown) => {
      if (objectFailure) equal(error, failure);
      else { ok(error instanceof Error); equal(error.message, "Security component failed."); }
      deepEqual(securityDiagnosticRecordsFrom(error), objectFailure ? [primary, clockRecord] : [primary]);
      equal(JSON.stringify(securityDiagnosticRecordsFrom(error)).includes(canary), false);
      return true;
    });
    deepEqual(wrapped.counts, expected, "wrapper observation never re-evaluates clock or projection");
  }
  let nativeReads = 0;
  const nativeLooking = Object.defineProperties(new Error(canary), {
    code: { get() { nativeReads++; return "CERT_HAS_EXPIRED"; } },
    cause: { get() { nativeReads++; throw new Error(canary); } },
  });
  await rejects(() => observePlatformRateLimitCheck(createInMemoryPlatformRateLimiter({ clock: { now() { throw nativeLooking; } } }), canary, context), (error: unknown) => {
    equal(error, nativeLooking); deepEqual(securityDiagnosticRecordsFrom(error), [primary, clockRecord]); return true;
  });
  equal(nativeReads, 0, "a clock failure supplies no peer-verification evidence");
  for (const returned of [null, {}]) {
    const clock = { now: () => returned } as unknown as Clock;
    const legacy = caught(() => clock.now().getTime()) as Error;
    const current = caught(() => createInMemoryPlatformRateLimiter({ clock }).check(canary)) as Error;
    equal(current.constructor, legacy.constructor); equal(current.message, legacy.message, "unchanged expression retains native TypeError text");
    deepEqual(securityDiagnosticRecordsFrom(current), [clockRecord]);
  }
  let calls = 0;
  const accounting = createInMemoryPlatformRateLimiter({ limit: 1, clock: { now() { if (calls++ === 0) throw new Error(canary); return new Date(0); } } });
  caught(() => accounting.check(canary));
  deepEqual(accounting.check(canary), { allowed: true }, "failed clock evaluation never consumes bucket quota");
  equal(accounting.check(canary).allowed, false); equal(calls, 3);
  deepEqual(createInMemoryPlatformRateLimiter({ clock: { now: () => new Date(NaN) } }).check(canary), { allowed: true }, "NaN timestamps keep their legacy acceptance");
  deepEqual(await observePlatformRateLimitCheck(createInMemoryPlatformRateLimiter({ clock: { now: () => new Date(NaN) } }), canary, context), { allowed: true });
  deepEqual(securityRateLimitClockFailureRecord(), clockRecord);
  const definition = platformSecurityDiagnosticCatalog.definitions.find((candidate) => candidate.code === "security.rate-limit-clock-failed") as DiagnosticDefinition;
  equal(definition.classification.failureKind, "unknown"); equal(definition.classification.failureSource, "unknown"); equal(definition.classification.retryable, false);
  equal(parseDiagnosticRecord(definition, { ...clockRecord, detail: { ...clockRecord.detail, value: canary } }).ok, false);
  equal(parseDiagnosticRecord(definition, { ...clockRecord, detail: { ...clockRecord.detail, reason: "invalid-time" } }).ok, false);
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
