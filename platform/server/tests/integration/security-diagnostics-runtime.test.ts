import { deepEqual, equal, ok } from "node:assert/strict";
import type { Permission } from "@kanbien/core/authz";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { definePlatformApp, platformAppId, platformRouteName, platformObservabilityProfileName, platformCapabilityName } from "@kanbien/platform-contracts";
import { createPlatformTestLogger, createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createJwtBearerAuthenticationHook, createInMemoryPlatformRateLimiter, securityOperationDiagnosticRecord, type PlatformAuthenticationHook } from "@kanbien/platform-security";
import { createPlatformServerShell, type PlatformServerOptions } from "../../src/index";

const canary = "private-security-value-canary";
async function main() {
  const id = platformAppId("security-proof"), profile = platformObservabilityProfileName("security-proof.request"), capability = platformCapabilityName("security-proof.request");
  ok(id.ok && profile.ok && capability.ok);
  const permission = "security-proof.route:read" as Permission;
  const identitySourceDefinition = defineDiagnostic({ code: "security-proof.principal-source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } },
  } as const);
  const identitySources = Array.from({ length: 9 }, (_, ordinal) => { const result = createDiagnosticRecord(identitySourceDefinition, { ordinal }); if (!result.ok) throw new Error("Invalid identity source fixture"); return result.value; });
  const identityFailure = Object.freeze(Object.assign(new Error(canary), { diagnosticRecord: identitySources[0], relatedDiagnosticRecords: Object.freeze(identitySources.slice(1)) }));
  let handlerCalls = 0;
  const app = definePlatformApp({ id: id.value, name: "Security proof", mount(registry) {
    registry.registerDiagnosticCatalog({ owner: "security-proof", definitions: [identitySourceDefinition] });
    registry.registerPermission({ permission });
    registry.registerObservabilityProfile({ name: profile.value, capability: capability.value, action: "execute", signals: ["operational_log"], logFieldNames: ["capability", "action", "execution_context", "outcome", "error_class"] });
    for (const mode of ["protected", "public", "opt-out", "mixed-profile", "mixed-opt-out"] as const) {
      const name = platformRouteName(`security-proof.${mode}`); ok(name.ok);
      registry.registerRoute({ name: name.value, method: mode === "mixed-opt-out" ? "POST" : "GET", path: mode.startsWith("mixed-") ? "/mixed" : `/${mode}`, auth: mode === "public" ? { kind: "public" } : { kind: "authenticated", permissions: [permission] },
        observability: mode === "opt-out" || mode === "mixed-opt-out" ? { kind: "opt_out", reason: "non_user_workload_path", justification: "Prove security observations respect route opt-outs." } : { kind: "profile", profile: profile.value },
        handler: { handle: () => { handlerCalls++; return { status: 200, body: { ok: true }, headers: { "X-Frame-Options": "unsafe", "x-app": "safe" } }; } },
      });
    }
  } });
  const logger = createPlatformTestLogger();
  const records = (): DiagnosticRecord[] => logger.records().filter((entry) => entry.message === "platform.diagnostic.observed").map((entry) => entry.fields?.["diagnostic"] as unknown as DiagnosticRecord);
  const shell = async (options: Partial<PlatformServerOptions> = {}) => {
    const result = await createPlatformServerShell({ apps: [app], deps: createPlatformTestMountDeps({ logger }), ...options }); ok(result.ok); return result.value;
  };
  const hook = createJwtBearerAuthenticationHook({ authz: {}, verifier: { verify: async () => ({ ok: false, error: { code: "PLATFORM_SECURITY_INVALID_TOKEN", defaultMessage: canary, diagnosticRecord: securityOperationDiagnosticRecord("token", "expired") } }) } });
  const secured = await shell({ auth: hook });
  let response = await secured.handle({ method: "GET", path: "/protected", headers: { authorization: `Bearer ${canary}` } });
  equal(response.status, 401); equal(handlerCalls, 0); equal(records().some((record) => record.code === "security.token.expired"), true);
  equal(JSON.stringify(response).includes("security.token"), false); equal(JSON.stringify(response).includes("diagnostic"), false);
  response = await secured.handle({ method: "GET", path: "/protected" });
  equal(response.status, 401); equal(records().some((record) => record.code === "security.authentication-header.missing"), true);
  const count = records().length;
  await secured.handle({ method: "GET", path: "/opt-out", headers: { authorization: `Bearer ${canary}` } }); equal(records().length, count);
  const unauthenticated = await shell();
  await unauthenticated.handle({ method: "GET", path: "/protected" }); equal(records().some((record) => record.code === "security.authentication.hook-unavailable"), true);
  const incomplete = await shell({ auth: { authenticate: () => ({ authenticated: true, permissions: [] }) } });
  response = await incomplete.handle({ method: "GET", path: "/protected" }); equal(response.status, 401);
  deepEqual(records().filter((record) => record.code === "security.authentication.principal-attribute-missing").map((record) => record.detail), ["principal-id", "principal-type", "subject"].map((attribute) => ({ phase: "authentication", reason: "principal-attribute-missing", effect: "not-assessed", attribute })));
  for (const [property, attribute] of [["principalId", "principal-id"], ["principalType", "principal-type"], ["subject", "subject"]] as const) {
    let reads = 0;
    const current = { authenticated: true, permissions: [permission], principalId: "id", principalType: "user" as const, subject: "subject" };
    const changing = Object.defineProperty(current, property, { get() { reads++; return reads === 1 ? undefined : property === "principalType" ? "user" : canary; } });
    const before = records().length;
    response = await (await shell({ auth: { authenticate: () => changing } })).handle({ method: "GET", path: "/protected" });
    equal(response.status, 401); equal(reads, 2, "guard plus original Server reread, not an added projection");
    deepEqual(records().slice(before).filter((record) => record.code === "security.authentication.principal-attribute-missing").map((record) => record.detail), [{ phase: "authentication", reason: "principal-attribute-missing", effect: "not-assessed", attribute }], "changing getter cannot erase the actual missing guard");
    let rejectingReads = 0;
    const rejecting = Object.defineProperty({ ...current }, property, { get() { if (++rejectingReads === 1) return undefined; throw identityFailure; } });
    const beforeReject = records().length;
    response = await (await shell({ auth: { authenticate: () => rejecting } })).handle({ method: "GET", path: "/protected" });
    equal(response.status, 500); equal(rejectingReads, 2);
    deepEqual(records().slice(beforeReject).filter((record) => record.code === "security.authentication.principal-attribute-missing").map((record) => record.detail), [{ phase: "authentication", reason: "principal-attribute-missing", effect: "not-assessed", attribute }], "later raw reread failure cannot erase the prior guard fact");
  }
  for (const mode of ["default", "injected", "unavailable", "throwing", "async-rejecting"] as const) {
    const identityLogger = createPlatformTestLogger(), injected: DiagnosticRecord[] = [];
    const baseDeps = createPlatformTestMountDeps({ logger: identityLogger });
    const reporter = { report(record: DiagnosticRecord) {
      if (mode === "unavailable") return { status: "unavailable" as const };
      injected.push(record);
      if (mode === "throwing") throw new Error(canary);
      return mode === "async-rejecting" ? Promise.reject(new Error(canary)) : { status: "written" as const };
    } };
    const deps = mode === "default" ? baseDeps : { ...baseDeps, diagnostics: reporter as unknown as NonNullable<typeof baseDeps.diagnostics> };
    const emitted = () => mode === "default" ? identityLogger.records().filter((entry) => entry.message === "platform.diagnostic.observed").map((entry) => entry.fields?.["diagnostic"] as unknown as DiagnosticRecord) : injected;
    for (const phase of ["projection", "copy"] as const) {
      let propertyReads = 0, iteratorCalls = 0;
      const input = { authenticated: true, permissions: [permission], principalId: "id", principalType: "user" as const, subject: "subject",
        ...(phase === "copy" ? { scopes: { [Symbol.iterator]() { iteratorCalls++; throw identityFailure; } } as unknown as readonly string[] } : {}) };
      if (phase === "projection") Object.defineProperty(input, "subject", { get() { propertyReads++; throw identityFailure; } });
      const identityShell = await shell({ deps, auth: { authenticate: () => input } });
      const before = emitted().length;
      response = await identityShell.handle({ method: "GET", path: "/protected" });
      equal(response.status, 500); equal(propertyReads, phase === "projection" ? 1 : 0); equal(iteratorCalls, phase === "copy" ? 1 : 0);
      const actual = emitted().slice(before);
      const ownedCode = phase === "projection" ? "security.authentication.principal-boundary-failed" : "core.authn.boundary-failed";
      deepEqual(actual.filter((record) => record.code === ownedCode), mode === "unavailable" ? [] : [{ schema: "core/diagnostic-record/v1", code: ownedCode, definitionVersion: 1,
        detail: phase === "projection" ? { operation: "principal-from-authentication", phase: "input-projection", field: "subject", reason: "threw", effect: "value-not-produced" }
          : { operation: "principal", phase: "scopes-copy", field: "scopes", reason: "threw", effect: "value-not-produced" } }]);
      deepEqual(actual.filter((record) => record.code === identitySourceDefinition.code), mode === "unavailable" ? [] : identitySources, "source9 delivered once independently from the owned location");
      const beforeOptOut = emitted().length;
      response = await identityShell.handle({ method: "GET", path: "/opt-out" }); equal(response.status, 500); equal(emitted().length, beforeOptOut);
      equal(JSON.stringify(response).includes(canary), false); equal(JSON.stringify(response).includes("diagnostic"), false);
    }
    await new Promise<void>((resolve) => setImmediate(resolve));
    equal(JSON.stringify(identityLogger.records()).includes(canary), false); equal(JSON.stringify(injected).includes(canary), false);
  }
  const authed: PlatformAuthenticationHook = { authenticate: () => ({ authenticated: true, principalId: canary, principalType: "user", subject: canary, claims: { secret: canary }, scopes: [canary], permissions: [], relatedDiagnosticRecords: [securityOperationDiagnosticRecord("authorization", "claim-unmapped", { referenceIndex: 0 })] }) };
  const forbidden = await shell({ auth: authed }); response = await forbidden.handle({ method: "GET", path: "/protected" });
  equal(response.status, 403); equal(handlerCalls, 0);
  equal(records().some((record) => record.code === "security.authorization.permission-missing"), true); equal(records().some((record) => record.code === "security.authorization.claim-unmapped"), true);
  let getterRead = false;
  const hostile = await shell({ auth: { authenticate: () => Object.defineProperty({ authenticated: false, permissions: [] }, "diagnosticRecord", { get() { getterRead = true; throw new Error(canary); } }) } });
  response = await hostile.handle({ method: "GET", path: "/protected" }); equal(response.status, 401); equal(getterRead, false);
  const broken = await shell({ auth: { authenticate: () => { throw new Error(canary); } } });
  response = await broken.handle({ method: "GET", path: "/protected" }); equal(response.status, 500); equal(records().some((record) => record.code === "security.authentication.component-failed"), true);
  const noPolicyLogs = await shell(); const beforeSuccess = records().length;
  response = await noPolicyLogs.handle({ method: "GET", path: "/public", headers: { origin: `https://${canary}.invalid` } });
  equal(response.status, 200); equal(response.headers["access-control-allow-origin"], undefined); equal(response.headers["x-frame-options"], "DENY"); equal(response.headers["x-app"], "safe");
  equal(records().length, beforeSuccess, "successful decisions are not logged by default");
  const decisions = await shell({ securityDecisionDiagnostics: true, corsAllowlist: ["https://allowed.test"] });
  const beforeOptOutPreflight = records().length;
  await decisions.handle({ method: "OPTIONS", path: "/opt-out" });
  await decisions.handle({ method: "OPTIONS", path: "/mixed" });
  equal(records().length, beforeOptOutPreflight, "preflight respects sole opt-out and conservatively respects mixed-profile paths");
  response = await decisions.handle({ method: "GET", path: "/public", headers: { origin: `https://${canary}.invalid` } });
  equal(response.status, 200, "CORS header omission does not reject the handler"); equal(records().some((record) => record.code === "security.cors.origin-not-allowlisted"), true);
  equal(records().some((record) => record.code === "security.response-header.platform-owned-override-ignored"), true);
  response = await decisions.handle({ method: "OPTIONS", path: "/public", headers: { origin: "https://allowed.test", "access-control-request-method": "UNSUPPORTED", "access-control-request-headers": canary } });
  equal(response.status, 204, "existing preflight checks only registered path, not requested method/header policy");
  equal(records().some((record) => record.code === "security.cors.preflight-path-present"), true);
  response = await decisions.handle({ method: "OPTIONS", path: "/absent" }); equal(response.status, 404); equal(records().some((record) => record.code === "security.cors.preflight-path-missing"), true);
  const limiter = createInMemoryPlatformRateLimiter({ limit: 1 });
  const limited = await shell({ rateLimiter: limiter });
  await limited.handle({ method: "GET", path: "/public", clientAddress: canary });
  response = await limited.handle({ method: "GET", path: "/public", clientAddress: canary }); equal(response.status, 429);
  deepEqual(records().filter((record) => record.code === "security.rate-limit.quota-exhausted").at(-1)?.detail, { phase: "rate-limit", reason: "quota-exhausted", effect: "not-assessed", boundary: "transport", keyCategory: "client-address" });
  const principalLimited = await shell({ auth: { authenticate: () => ({ authenticated: true, principalId: canary, principalType: "user", subject: canary, permissions: [permission], rateLimitKey: canary }) }, rateLimiter: { check: (key) => key === canary ? { allowed: false } : { allowed: true } } });
  response = await principalLimited.handle({ method: "GET", path: "/protected" }); equal(response.status, 429);
  deepEqual(records().filter((record) => record.code === "security.rate-limit.rejected-unclassified").at(-1)?.detail, { phase: "rate-limit", reason: "rejected-unclassified", effect: "not-assessed", boundary: "principal", keyCategory: "principal" });
  const unavailable = await shell({ rateLimiter: { check: () => { throw new Error(canary); } } });
  response = await unavailable.handle({ method: "GET", path: "/public" }); equal(response.status, 500, "direct helper failure status remains compatible");
  await unavailable.lifecycle.start(); const handle = await unavailable.listen();
  try {
    const transportResponse = await fetch(`http://127.0.0.1:${handle.port}/public`); equal(transportResponse.status, 503, "transport dependency status remains compatible");
    const last = records().filter((record) => record.code === "security.rate-limit.dependency-failed").at(-1);
    deepEqual(last?.detail, { phase: "rate-limit", reason: "dependency-failed", effect: "not-assessed", boundary: "transport", keyCategory: "client-address" });
  } finally { unavailable.lifecycle.beginDrain(); await handle.close(); await unavailable.lifecycle.shutdown(); }
  for (const mode of ["default", "injected", "unavailable"] as const) {
    const clockLogger = createPlatformTestLogger();
    const injected: DiagnosticRecord[] = [];
    let clockCalls = 0;
    const failedClock = createInMemoryPlatformRateLimiter({ clock: { now() { clockCalls++; throw Object.freeze(new Error(canary)); } } });
    const baseDeps = createPlatformTestMountDeps({ logger: clockLogger });
    const clockShell = await shell({ rateLimiter: failedClock, deps: mode === "default" ? baseDeps : { ...baseDeps, diagnostics: {
      report(record) { if (mode === "unavailable") return { status: "unavailable" }; injected.push(record); return { status: "written" }; },
    } } });
    const emitted = () => (mode === "injected" ? injected : clockLogger.records().filter((entry) => entry.message === "platform.diagnostic.observed").map((entry) => entry.fields?.["diagnostic"] as unknown as DiagnosticRecord));
    const expectedClock = { schema: "core/diagnostic-record/v1", code: "security.rate-limit-clock-failed", definitionVersion: 1,
      detail: { phase: "clock-evaluation", reason: "evaluation-threw", effect: "decision-not-returned" } };
    response = await clockShell.handle({ method: "GET", path: "/public", clientAddress: canary });
    equal(response.status, 500); equal(clockCalls, 1);
    deepEqual(emitted().filter((record) => record.code === expectedClock.code), mode === "unavailable" ? [] : [expectedClock]);
    equal(JSON.stringify(response).includes("diagnostic"), false);
    await clockShell.lifecycle.start(); const clockHandle = await clockShell.listen();
    try {
      const clockResponse = await fetch(`http://127.0.0.1:${clockHandle.port}/public`);
      equal(clockResponse.status, 503); equal(clockCalls, 2, "each request makes exactly its original clock call");
      const body: unknown = await clockResponse.json();
      equal(JSON.stringify(body).includes("diagnostic"), false); equal(JSON.stringify(body).includes(canary), false);
      deepEqual(emitted().filter((record) => record.code === expectedClock.code), mode === "unavailable" ? [] : [expectedClock, expectedClock], "clock companion reaches both direct and actual transport consumers");
      equal(emitted().filter((record) => record.code === "security.rate-limit.dependency-failed").length, mode === "unavailable" ? 0 : 2, "historical primary remains and is not duplicated");
      equal(emitted().some((record) => record.code.startsWith("security.peer-")), false, "a clock throw is not peer verification evidence");
      equal(JSON.stringify(clockLogger.records()).includes(canary), false); equal(JSON.stringify(injected).includes(canary), false);
    } finally { clockShell.lifecycle.beginDrain(); await clockHandle.close(); await clockShell.lifecycle.shutdown(); }
  }
  const throwingSink = await shell({ auth: hook, deps: { ...createPlatformTestMountDeps(), diagnostics: { report() { throw new Error(canary); } } } });
  response = await throwingSink.handle({ method: "GET", path: "/protected", headers: { authorization: "Bearer ignored" } }); equal(response.status, 401);
  equal(JSON.stringify(logger.records()).includes(canary), false, "no identity, claim, token, address, origin, or exception canary escapes");
  console.log("Server security diagnostics: exact internal delivery, opt-outs, sink isolation, unchanged HTTP/CORS/preflight behaviour and both limiter boundaries passed.");
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
