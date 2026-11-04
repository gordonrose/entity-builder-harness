import { deepEqual, equal, rejects } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import { correlationId } from "@kanbien/core/shared";
import type { TenantResolution } from "@kanbien/core/tenancy";
import { invalidResult, validationIssue } from "@kanbien/core/validation";
import { definePlatformApp, platformAppId, platformCapabilityName, platformObservabilityProfileName, platformRouteName,
  type PlatformDiagnosticReporter, type PlatformResourceAuthorizationResolution } from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createPlatformServerShell, type PlatformServerRequest } from "../src/index";

const canary = "synthetic-private-request-canary";
const id = platformAppId("requestfixture"), capability = platformCapabilityName("requestfixture.execute"), profile = platformObservabilityProfileName("requestfixture.execute");
if (!id.ok || !capability.ok || !profile.ok) throw new Error("Invalid request fixture identifiers.");
const appId = id.value, capabilityName = capability.value, profileName = profile.value;
const permission = "requestfixture.record:read" as const;
const requestId = correlationId("request-fixture-id");
const definition = defineDiagnostic({ code: "requestfixture.operation-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "app", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { index: { type: "integer", minimum: 0, maximum: 8 } } },
} as const);
const evidence = Array.from({ length: 9 }, (_, index) => {
  const checked = createDiagnosticRecord(definition, { index });
  if (!checked.ok) throw new Error("Invalid evidence fixture.");
  return checked.value;
});
const evidenceLiterals = Array.from({ length: 9 }, (_, index) => ({ schema: "core/diagnostic-record/v1", code: "requestfixture.operation-observed", definitionVersion: 1, detail: { index } }));
const failure = Object.freeze(Object.assign(new Error(canary), { diagnosticRecord: evidence[0], relatedDiagnosticRecords: Object.freeze(evidence.slice(1)) }));
type Mode = "default" | "injected" | "unavailable" | "async-rejecting" | "injected-throws";

async function fixture(mode: Mode = "default") {
  const observed: DiagnosticRecord[] = [], logs: LogRecord[] = [];
  let attempts = 0;
  const state = {
    tenant: { tenantId: canary, isolationKey: canary } as unknown,
    resource: { kind: "authorize" } as unknown,
    tenantError: undefined as unknown, resourceError: undefined as unknown, handlerError: undefined as unknown,
    validatorError: undefined as unknown, validationAllowed: true,
    clockFailureAt: 0, clockCalls: 0, tenantCalls: 0, resourceCalls: 0, handlerCalls: 0, authorizerCalls: 0,
    validatorCalls: 0, optionalTenant: undefined as unknown,
  };
  const base = createPlatformTestMountDeps({
    logger: { write(log) {
      if (log.message === "platform.diagnostic.observed") {
        attempts++;
        if (mode === "unavailable") throw new Error(canary);
        observed.push(log.fields?.["diagnostic"] as DiagnosticRecord);
      }
      logs.push(log);
    } },
    clock: { now() { state.clockCalls++; if (state.clockCalls === state.clockFailureAt) throw failure; return new Date("2026-10-30T00:00:00.000Z"); } },
    authorizer: { async decide() { state.authorizerCalls++; return { allowed: true }; } },
  });
  const injected = { report(record: DiagnosticRecord) {
    attempts++; observed.push(record);
    if (mode === "injected-throws") throw new Error(canary);
    return mode === "async-rejecting" ? Promise.reject(new Error(canary)) : { status: "written" as const };
  } } as unknown as PlatformDiagnosticReporter;
  const deps = mode === "injected" || mode === "async-rejecting" || mode === "injected-throws" ? { ...base, diagnostics: injected } : base;
  const app = definePlatformApp({ id: appId, name: "Request fixture", mount(registry) {
    registry.registerDiagnosticCatalog({ owner: "requestfixture", definitions: [definition] });
    registry.registerPermission({ permission });
    registry.registerObservabilityProfile({ name: profileName, capability: capabilityName, action: "execute", signals: ["operational_log"],
      logFieldNames: ["capability", "action", "execution_context", "outcome", "error_class"] });
    for (const name of ["tenant", "optional", "resource", "handler", "validation", "decode", "opt-out"] as const) {
      const route = platformRouteName(`requestfixture.${name}`);
      if (!route.ok) throw new Error("Invalid route fixture.");
      registry.registerRoute({ name: route.value, method: "GET", path: name === "decode" ? "/decode/:first/:second" : `/${name}/:id`,
        auth: name === "tenant" || name === "optional" || name === "resource" ? { kind: "authenticated", permissions: [permission] } : { kind: "public" },
        observability: name === "opt-out" ? { kind: "opt_out", reason: "non_user_workload_path", justification: "Prove per-request diagnostic opt-out." } : { kind: "profile", profile: profileName },
        ...(name === "tenant" ? { tenant: "required" as const } : name === "optional" ? { tenant: "optional" as const } : {}),
        ...(name === "resource" ? { resourceAuthorization: { permission, resolve() {
          state.resourceCalls++; if (state.resourceError !== undefined) throw state.resourceError;
          return state.resource as PlatformResourceAuthorizationResolution;
        } } } : {}),
        ...(name === "validation" ? { validator: {
          validate(value: unknown): value is unknown { void value; state.validatorCalls++; if (state.validatorError !== undefined) throw state.validatorError; return state.validationAllowed; },
          explain: () => invalidResult(validationIssue({ code: "WRONG_TYPE", defaultMessage: "Request body rejected." })),
        } } : {}),
        handler: { handle(_request, context) {
          state.handlerCalls++; if (state.handlerError !== undefined) throw state.handlerError;
          state.optionalTenant = context.tenant; return { status: 200, body: { ok: true } };
        } },
      });
    }
  } });
  const built = await createPlatformServerShell({ apps: [app], deps,
    rateLimiter: { check: () => ({ allowed: true }) },
    auth: { grantedPermissions: () => [permission], authenticate: () => ({ authenticated: true, permissions: [permission], principalId: "request-principal", principalType: "user", subject: "request-subject" }) },
    tenantResolver: { async resolve() { state.tenantCalls++; if (state.tenantError !== undefined) throw state.tenantError; return state.tenant as TenantResolution; } },
  });
  if (!built.ok) throw new Error(built.error.code);
  await built.value.lifecycle.start();
  const request = (path: string, method: PlatformServerRequest["method"] = "GET") => built.value.handle({ method, path, requestId });
  const clear = () => { observed.length = 0; logs.length = 0; attempts = 0; };
  return { shell: built.value, state, observed, logs, request, clear, attempts: () => attempts };
}

function predicate(field: string, condition: string, phase: string) {
  return { schema: "core/diagnostic-record/v1", code: "platform-server.request-predicate-rejected", definitionVersion: 1,
    detail: { field, condition, phase, effect: "handler-not-invoked" } };
}
function boundary(phase: string, effect: string, index?: number) {
  return { schema: "core/diagnostic-record/v1", code: "platform-server.request-boundary-failed", definitionVersion: 1,
    detail: { phase, reason: "boundary-threw", effect, ...(index === undefined ? {} : { index }) } };
}
function predicateRecords(records: readonly DiagnosticRecord[]) { return records.filter((record) => record.code === "platform-server.request-predicate-rejected"); }
function assertPrivate(value: unknown) { const serialized = JSON.stringify(value); equal(serialized.includes(canary), false); equal(serialized.includes("diagnosticRecord"), false); }

async function tenantPredicates(): Promise<void> {
  const f = await fixture();
  const cases: readonly [unknown, string, string][] = [
    [undefined, "tenant-result", "object-required"], [null, "tenant-result", "object-required"], [canary, "tenant-result", "object-required"],
    [{ tenantId: 1, isolationKey: canary }, "tenantId", "string-required"], [{ tenantId: "", isolationKey: canary }, "tenantId", "nonempty-required"],
    [{ tenantId: canary, isolationKey: 1 }, "isolationKey", "string-required"], [{ tenantId: canary, isolationKey: "" }, "isolationKey", "nonempty-required"],
  ];
  for (const [value, field, condition] of cases) {
    f.clear(); f.state.tenant = value; const before = f.state.handlerCalls;
    const result = await f.request("/tenant/private");
    equal(result.status, 403); equal(f.state.handlerCalls, before);
    deepEqual(predicateRecords(f.observed), [predicate(field, condition, "tenant-resolution")]);
    assertPrivate(result); equal(JSON.stringify(f.logs).includes(canary), false);
  }
  for (const accepted of [
    { tenantId: " ", isolationKey: " " }, Object.assign([], { tenantId: canary, isolationKey: canary }),
    Object.create({ tenantId: canary, isolationKey: canary }) as unknown,
  ]) {
    f.clear(); f.state.tenant = accepted;
    equal((await f.request("/tenant/private")).status, 200); deepEqual(f.observed, []);
  }
  let tenantReads = 0, isolationReads = 0;
  f.state.tenant = { get tenantId() { tenantReads++; return canary; }, get isolationKey() { isolationReads++; return canary; } };
  f.clear(); equal((await f.request("/tenant/private")).status, 200);
  deepEqual([tenantReads, isolationReads], [2, 2]);
  f.clear(); f.state.tenant = null;
  equal((await f.request("/optional/private")).status, 200); equal(f.state.optionalTenant, undefined); deepEqual(f.observed, []);
  await f.shell.lifecycle.shutdown();
}

async function resourcePredicates(): Promise<void> {
  const f = await fixture();
  const cases: readonly [unknown, number, string, string][] = [
    [undefined, 403, "resource-result", "object-required"], [null, 403, "resource-result", "object-required"],
    [{ kind: canary }, 403, "resource.kind", "kind-rejected"], [{ kind: "not-found", disclosure: canary }, 403, "resource.disclosure", "disclosure-rejected"],
    [{ kind: "not-found", disclosure: "not-found" }, 404, "resource", "not-found"], [{ kind: "not-found", disclosure: "forbidden" }, 403, "resource", "forbidden-disclosure"],
  ];
  for (const [value, status, field, condition] of cases) {
    f.clear(); f.state.resource = value; const before = [f.state.handlerCalls, f.state.authorizerCalls];
    const result = await f.request("/resource/private");
    equal(result.status, status); deepEqual([f.state.handlerCalls, f.state.authorizerCalls], before);
    deepEqual(predicateRecords(f.observed), [predicate(field, condition, "resource-resolution")]);
    assertPrivate(result); equal(JSON.stringify(f.logs).includes(canary), false);
  }
  let kindReads = 0, disclosureReads = 0;
  f.clear(); f.state.resource = { get kind() { kindReads++; return "not-found"; }, get disclosure() { disclosureReads++; return canary; } };
  equal((await f.request("/resource/private")).status, 403); deepEqual([kindReads, disclosureReads], [2, 2]);
  f.clear();
  f.state.resource = Object.assign([], { kind: "authorize" });
  equal((await f.request("/resource/private")).status, 200); deepEqual(f.observed, []);
  f.clear(); f.state.resource = Object.create({ kind: "authorize" });
  equal((await f.request("/resource/private")).status, 200); deepEqual(f.observed, []);
  await f.shell.lifecycle.shutdown();
}

async function deliveryAndFullEvidence(): Promise<void> {
  for (const mode of ["default", "injected", "unavailable", "async-rejecting", "injected-throws"] as const) {
    const f = await fixture(mode);
    for (const location of ["handler", "context"] as const) {
      f.clear(); f.state.clockCalls = 0; f.state.clockFailureAt = location === "context" ? 2 : 0;
      f.state.handlerError = location === "handler" ? failure : undefined;
      const before: number = f.state.handlerCalls;
      const result = await f.request("/handler/private"); equal(result.status, 500); assertPrivate(result);
      equal(f.state.handlerCalls, before + (location === "handler" ? 1 : 0));
      const own = location === "handler" ? boundary("handler", "handler-invocation-outcome-unknown") : {
        schema: "core/diagnostic-record/v1", code: "platform-runtime.boundary-failed", definitionVersion: 1,
        detail: { operation: "request-context", phase: "clock-read", subject: "context", boundary: "invocation", effect: "context-not-returned" },
      };
      deepEqual(f.observed, mode === "unavailable" ? [] : [own, ...evidenceLiterals]);
      equal(f.attempts(), 10, "Own location must not evict any of primary plus eight selected companions.");
      equal(JSON.stringify(f.logs).includes(canary), false);
    }
    f.clear(); f.state.clockFailureAt = 0; f.state.handlerError = failure;
    equal((await f.request("/opt-out/private")).status, 500); deepEqual(f.observed, []); equal(f.attempts(), 0);
    await f.shell.lifecycle.shutdown();
  }
  await new Promise((resolve) => setImmediate(resolve));
}

async function rawThrowsAndOtherCalls(): Promise<void> {
  const f = await fixture("injected");
  f.clear(); f.state.clockCalls = 0; f.state.clockFailureAt = 1;
  await rejects(f.request("/handler/private"), (error) => error === failure);
  deepEqual(f.observed, [boundary("request-clock", "handler-not-invoked"), ...evidenceLiterals]);
  equal(f.state.handlerCalls, 0);
  f.state.clockFailureAt = 0;
  const originalDecode = globalThis.decodeURIComponent;
  const decodingError = Object.freeze(new URIError(canary));
  let decodeCalls = 0;
  globalThis.decodeURIComponent = (value) => { decodeCalls++; if (decodeCalls === 2) throw decodingError; return originalDecode(value); };
  try {
    f.clear(); await rejects(f.request("/decode/one/private"), (error) => error === decodingError);
    equal(decodeCalls, 2); deepEqual(f.observed, [boundary("route-parameter-decoding", "handler-not-invoked", 1)]);
  } finally { globalThis.decodeURIComponent = originalDecode; }
  f.clear(); await rejects(f.request("/decode/one/%"), URIError);
  deepEqual(f.observed, [boundary("route-parameter-decoding", "handler-not-invoked", 1)]);
  for (const location of ["tenant", "resource", "validation"] as const) {
    f.clear(); f.state.tenantError = location === "tenant" ? failure : undefined;
    f.state.resourceError = location === "resource" ? failure : undefined;
    f.state.validatorError = location === "validation" ? failure : undefined;
    const before: number = f.state.handlerCalls;
    equal((await f.request(`/${location}/private`)).status, 500); equal(f.state.handlerCalls, before);
    const phase = location === "tenant" ? "tenant-resolution" : location === "resource" ? "resource-resolution" : "request-validation";
    equal(f.observed.some((record) => record.code === "platform-server.request-boundary-failed" && (record.detail as { phase: string }).phase === phase), true);
    deepEqual(f.observed.filter((record) => record.code === definition.code), evidenceLiterals);
  }
  f.state.tenantError = undefined; f.state.resourceError = undefined; f.state.validatorError = undefined;
  f.clear(); f.state.validationAllowed = false; const before = f.state.handlerCalls;
  equal((await f.request("/validation/private")).status, 400); equal(f.state.handlerCalls, before);
  deepEqual(predicateRecords(f.observed), [predicate("request-body", "validator-rejected", "request-validation")]);
  f.clear(); equal((await f.request("/unknown/private")).status, 404);
  deepEqual(predicateRecords(f.observed), [predicate("route", "path-not-registered", "routing")]);
  f.clear(); equal((await f.request("/handler/private", "POST")).status, 405);
  deepEqual(predicateRecords(f.observed), [predicate("route", "method-not-registered", "routing")]);
  equal(JSON.stringify(f.logs).includes(canary), false);
  await f.shell.lifecycle.shutdown();
}

async function main(): Promise<void> {
  await tenantPredicates(); await resourcePredicates(); await deliveryAndFullEvidence(); await rawThrowsAndOtherCalls();
  console.log("Server request predicates, raw boundary throws, full evidence delivery and profile/privacy tests passed.");
}
void main().catch((error) => { console.error(error); process.exitCode = 1; });
