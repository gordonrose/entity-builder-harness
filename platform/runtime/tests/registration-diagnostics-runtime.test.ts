import { deepEqual, equal } from "node:assert/strict";
import { createPlatformRuntimeRegistry, mountPlatformRuntimeApps } from "../src/index";
import { createPlatformTestRegistry, createPlatformTestMountDeps, mountPlatformAppForTest } from "@kanbien/platform-testing";
import { platformAppId, platformContractDiagnosticCatalog, type PlatformAppRegistry, type PlatformContractError } from "@kanbien/platform-contracts";
const canary = "private-registration-canary@example.invalid";
const requirement = { kind: "opt_out", reason: "non_user_workload_path", justification: "Fixture." };
const baseRoute = { name: "test.route", method: "GET", path: "/example", auth: { kind: "public" }, observability: requirement, handler: { handle() {} } };
const baseJob = { name: "test.job", messageType: "test.message", observability: requirement, handler: { handle() {} } };
function record(error: PlatformContractError, registration: string, field: string, condition: string, phase = "registration"): void {
  equal(error.diagnosticRecord?.code, "platform-contracts.registration-rejected");
  equal(error.diagnosticRecord?.definitionVersion, 1);
  deepEqual(error.diagnosticRecord?.detail, { registration, field, condition, phase, effect: "rejected" });
  equal(JSON.stringify(error.diagnosticRecord).includes(canary), false);
}
function failure(result: { readonly ok: boolean; readonly error?: PlatformContractError }): PlatformContractError {
  equal(result.ok, false); if (!result.error) throw new Error("Expected failure"); return result.error;
}
for (const create of [createPlatformRuntimeRegistry, createPlatformTestRegistry]) {
  let registry = create();
  equal(registry.registerPermission({ permission: "test:read" } as never).ok, true);
  record(failure(registry.registerPermission({ permission: "test:read" } as never)), "permission", "identity", "duplicate-permission");
  equal(registry.permissions().length, 1);

  registry = create();
  equal(registry.registerRoute(baseRoute as never).ok, true);
  record(failure(registry.registerRoute({ ...baseRoute, path: "/second" } as never)), "route", "identity", "duplicate-name");
  record(failure(registry.registerRoute({ ...baseRoute, name: "test.second" } as never)), "route", "identity", "duplicate-route-key");
  // The original OR observes name first when both identities match.
  record(failure(registry.registerRoute(baseRoute as never)), "route", "identity", "duplicate-name");
  equal(registry.routes().length, 1);

  registry = create();
  equal(registry.registerJob(baseJob as never).ok, true);
  record(failure(registry.registerJob({ ...baseJob, messageType: "test.other" } as never)), "job", "identity", "duplicate-name");
  record(failure(registry.registerJob({ ...baseJob, name: "test.other" } as never)), "job", "identity", "duplicate-message-type");
  record(failure(registry.registerJob(baseJob as never)), "job", "identity", "duplicate-name");
  equal(registry.jobs().length, 1);

  const app = platformAppId("test"); if (!app.ok) throw new Error("Fixture invalid");
  const scoped = create().forApp(app.value);
  for (const [kind, register] of [
    ["route", () => scoped.registerRoute({ ...baseRoute, name: canary } as never)],
    ["job", () => scoped.registerJob({ ...baseJob, name: canary } as never)],
    ["permission", () => scoped.registerPermission({ permission: canary } as never)],
    ["health", () => scoped.registerHealthCheck({ name: canary } as never)],
    ["observability-profile", () => scoped.registerObservabilityProfile({ name: canary } as never)],
    ["diagnostic-catalog", () => scoped.registerDiagnosticCatalog(platformContractDiagnosticCatalog)],
  ] as const) record(failure(register()), kind, "name", "namespace-mismatch");

  registry = create();
  equal(registry.registerRoute({ ...baseRoute, auth: { kind: "authenticated", permissions: ["test:read", "test:write"] } } as never).ok, true);
  equal(registry.registerJob({ ...baseJob, observability: { kind: "profile", profile: "test.missing" } } as never).ok, true);
  equal(registry.registerRoute({ ...baseRoute, name: "test.second", path: "/second", observability: { kind: "profile", profile: "test.missing" } } as never).ok, true);
  const errors = registry.validate();
  equal(errors.length, 4);
  record(errors[0]!, "route", "permission", "undeclared-permission", "resolution");
  record(errors[1]!, "route", "permission", "undeclared-permission", "resolution");
  record(errors[2]!, "route", "observability", "undeclared-profile", "resolution");
  record(errors[3]!, "job", "observability", "undeclared-profile", "resolution");
  equal(registry.errors().length, 0, "Deferred failures do not become registration mutations");
  equal(registry.registerConfigSchema(null as never).ok, true, "Config schema registration retains append-only admission");
  equal(registry.configSchemas()[0], null);

  registry = create();
  equal(registry.registerRoute(baseRoute as never).ok, true);
  let observedPath = 0;
  const second = { ...baseRoute, get path() { observedPath++; return "/second"; } };
  record(failure(registry.registerRoute(second as never)), "route", "identity", "duplicate-name");
  equal(observedPath, 2, "One validation path read and the existing duplicate error key read; OR must not probe its second dimension");
  const stored = registry.errors()[0]!;
  equal(stored, registry.validate()[0], "Stored contract records retain error identity");
}

// Existing test-helper resolution policy omits resourceAuthorization references.
const resourceRoute = { ...baseRoute, auth: { kind: "authenticated" }, resourceAuthorization: { permission: "test:resource", resolve() {} } };
const production = createPlatformRuntimeRegistry();
const testing = createPlatformTestRegistry();
equal(production.registerRoute(resourceRoute as never).ok, true);
equal(testing.registerRoute(resourceRoute as never).ok, true);
record(production.validate()[0]!, "route", "resourceAuthorization.permission", "undeclared-permission", "resolution");
equal(testing.validate().length, 0);

async function proveMountPreservation(): Promise<void> {
  const id = platformAppId("test"); if (!id.ok) throw new Error("Fixture invalid");
  let captured: PlatformContractError | undefined;
  const app = { id: id.value, name: "Fixture", mount(registry: PlatformAppRegistry) {
    captured = failure(registry.registerRoute({ ...baseRoute, method: "OPTIONS" } as never));
  } };
  const runtime = await mountPlatformRuntimeApps({ apps: [app], deps: createPlatformTestMountDeps() });
  equal(runtime.ok, false); if (runtime.ok) throw new Error("Expected mount failure");
  equal(runtime.error.contractErrors[0], captured);
  record(runtime.error.contractErrors[0]!, "route", "method", "unsupported", "validation");
  const helper = await mountPlatformAppForTest(app);
  equal(helper.ok, false); if (helper.ok) throw new Error("Expected test mount failure");
  equal(helper.error.contractErrors[0], captured);
  record(helper.error.contractErrors[0]!, "route", "method", "unsupported", "validation");
}
proveMountPreservation().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
