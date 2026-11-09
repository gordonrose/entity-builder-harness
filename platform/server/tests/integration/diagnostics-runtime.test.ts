import { deepEqual, equal } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";
import { invalidResult, validationIssue } from "@kanbien/core/validation";
import { definePlatformApp, platformAppId, platformRouteName, platformObservabilityProfileName, platformCapabilityName } from "@kanbien/platform-contracts";
import { createPlatformTestLogger, createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createPlatformServerShell, platformServerDiagnosticCatalog } from "../../src/index";

async function main() {
  const id = platformAppId("diagnostic-proof"), profile = platformObservabilityProfileName("diagnostic-proof.operation"), capability = platformCapabilityName("diagnostic-proof.operation");
  if (!id.ok || !profile.ok || !capability.ok) throw new Error("fixture-invalid");
  const definition = defineDiagnostic({ code: "diagnostic-proof.attribute-invalid", version: 1,
    classification: { failureKind: "validation", failureSource: "app", severity: "warning", recovery: "manual_investigation" },
    detail: { type: "object", properties: { field: { type: "enum", values: ["enabled"] }, reason: { type: "enum", values: ["wrong-type"] } } },
  } as const);
  const detail = createDiagnosticRecord(definition, { field: "enabled", reason: "wrong-type" });
  if (!detail.ok) throw new Error("fixture-invalid");
  const logger = createPlatformTestLogger();
  let handled = 0;
  const app = definePlatformApp({ id: id.value, name: "Diagnostic proof", mount(registry) {
    registry.registerDiagnosticCatalog({ owner: "diagnostic-proof", definitions: [definition] });
    registry.registerObservabilityProfile({ name: profile.value, capability: capability.value, action: "execute", signals: ["operational_log"], logFieldNames: ["capability", "action", "execution_context", "outcome", "error_class"] });
    for (const mode of ["validated", "hostile", "opt-out", "validation", "auth-exception"] as const) {
      const route = platformRouteName(`diagnostic-proof.${mode}`);
      if (!route.ok) throw new Error("fixture-invalid");
      registry.registerRoute({ name: route.value, method: "POST", path: `/${mode}`, auth: mode === "auth-exception" ? { kind: "authenticated" } : { kind: "public" },
        observability: mode === "opt-out" ? { kind: "opt_out", reason: "non_user_workload_path", justification: "Prove diagnostic details do not bypass a signal opt-out." } : { kind: "profile", profile: profile.value },
        ...(mode === "validation" ? { validator: { validate: (_value: unknown): _value is never => false,
          explain: () => invalidResult(validationIssue({ code: "WRONG_TYPE", path: ["enabled"], defaultMessage: "Enabled must be boolean." })), diagnose: () => detail.value } } : {}),
        handler: { handle: () => { handled++; return { status: 503, body: { code: "PUBLIC_FAILURE" }, observability: {
          errorClass: "PRIVATE_FAILURE", diagnosticRecord: mode === "hostile" ? { ...detail.value, detail: { value: "synthetic-secret-canary" } } : detail.value,
        } }; } },
      });
    }
  } });
  const result = await createPlatformServerShell({ apps: [app], deps: createPlatformTestMountDeps({ logger }), auth: { authenticate: async (request) => {
    if (request.headers?.["x-fixture-auth-fail"] === "true") throw new Error("synthetic-secret-canary");
    return { authenticated: false, permissions: [] };
  } } });
  if (!result.ok) throw new Error(result.error.code);
  await result.value.lifecycle.start();
  for (const mode of ["validated", "hostile", "opt-out", "validation"]) {
    const response = await result.value.handle({ method: "POST", path: `/${mode}`, body: { enabled: "synthetic-secret-canary" } });
    equal(response.status, mode === "validation" ? 400 : 503);
    equal(JSON.stringify(response).includes("diagnosticRecord"), false);
    equal(JSON.stringify(response).includes("attribute-invalid"), false);
  }
  equal(handled, 3, "validation rejects before the handler runs");
  const authentication = await result.value.handle({ method: "POST", path: "/auth-exception", headers: { "x-fixture-auth-fail": "true" } });
  equal(authentication.status, 500);
  const boundary = logger.records().filter((record) => record.message === "platform.diagnostic.observed").at(-1)?.fields?.["diagnostic"] as { detail: { phase: string; effect: string } };
  deepEqual({ phase: boundary.detail.phase, effect: boundary.detail.effect }, { phase: "authentication", effect: "unknown" }, "a thrown authentication call must not be mislabelled as handler execution or a proven rejection");
  const diagnostics = logger.records().filter((record) => record.message === "platform.diagnostic.observed");
  equal(diagnostics.length, 5, "valid selected records, one validation-location observation, and the existing authentication observations are emitted; opt-outs remain quiet");
  deepEqual(diagnostics[0]?.fields?.["diagnostic"], detail.value);
  equal(typeof diagnostics[0]?.correlationId, "string", "diagnostics must correlate with the failed request without copying request data");
  equal(JSON.stringify(logger.records()).includes("synthetic-secret-canary"), false);
  await result.value.lifecycle.shutdown();
  const conflictingId = platformAppId("platform-server");
  if (!conflictingId.ok) throw new Error("fixture-invalid");
  const conflicting = await createPlatformServerShell({ apps: [definePlatformApp({ id: conflictingId.value, name: "Conflict proof", mount(registry) {
    registry.registerDiagnosticCatalog(platformServerDiagnosticCatalog);
  } })], deps: createPlatformTestMountDeps() });
  equal(conflicting.ok, false, "a built-in catalog ownership conflict must return a bounded startup failure, not throw");
  if (!conflicting.ok) equal(conflicting.error.code, "PLATFORM_SERVER_MOUNT_FAILED");
  console.log("Server exact validation diagnostics, hostile detail rejection, opt-out and HTTP exclusion passed.");
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
