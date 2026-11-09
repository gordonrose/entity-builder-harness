import { deepEqual, equal } from "node:assert/strict";
import type { LogRecord } from "@kanbien/core/logging";
import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";
import { healthCheckName, healthCheckResult, monitoringComponent } from "@kanbien/core/monitoring";
import { isoDateTimeFromDate } from "@kanbien/core/shared";
import { definePlatformApp, platformAppId, platformHealthName } from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createPlatformServerShell, platformServerDiagnosticCatalog } from "../../src/index";

async function main(): Promise<void> {
  const id = platformAppId("healthfixture"), name = platformHealthName("healthfixture.ready");
  if (!id.ok || !name.ok) throw new Error("fixture-invalid");
  const definition = defineDiagnostic({ code: "dependency.check-failed", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" },
    detail: { type: "object", properties: { phase: { type: "enum", values: ["probe"] } } } } as const);
  const detail = createDiagnosticRecord(definition, { phase: "probe" }); if (!detail.ok) throw new Error("fixture-invalid");
  for (const mode of ["selected", "unselected", "injected", "unavailable"] as const) {
    const logs: LogRecord[] = [], records: unknown[] = []; let calls = 0, returnedHealthy = false;
    const deps = createPlatformTestMountDeps({ logger: { write(record) { if (mode === "unavailable") throw new Error("private-health-canary"); logs.push(record); } } });
    const shell = await createPlatformServerShell({ diagnosticCatalogs: mode === "selected" || mode === "unavailable" ? [{ owner: "dependency", definitions: [definition] }] : [],
      apps: [definePlatformApp({ id: id.value, name: "Health fixture", mount(registry) { registry.registerHealthCheck({ name: name.value,
        check: { check() {
          calls++;
          if (returnedHealthy) return healthCheckResult({ name: healthCheckName("healthfixture.ready"), type: "readiness",
            component: monitoringComponent({ type: "runtime", name: "fixture" }), status: "healthy", checkedAt: isoDateTimeFromDate(deps.clock.now()),
            message: { code: "HEALTH_FIXTURE", defaultMessage: "private-health-canary" }, metadata: { dependency: "ready", detail: "private-health-canary" } });
          throw Object.assign(new Error("private-health-canary"), { code: "private-health-canary", name: "private-health-canary", diagnosticRecord: detail.value });
        } } }); } })],
      deps: mode === "injected" ? { ...deps, diagnostics: { report(record) { records.push(record); return { status: "written" }; } } } : deps });
    if (!shell.ok) throw new Error(shell.error.code);
    await shell.value.lifecycle.start();
    const live = await shell.value.handle({ method: "GET", path: "/livez" }); equal(live.status, 200); equal(calls, 0);
    const ready = await shell.value.handle({ method: "GET", path: "/readyz" }); equal(ready.status, 503); equal(calls, 1);
    const generic = { schema: "core/diagnostic-record/v1", code: "health.check-threw", definitionVersion: 1, detail: { index: 0, phase: "invocation", effect: "unknown" } };
    const emitted = mode === "injected" ? records : logs.filter((log) => log.message === "platform.diagnostic.observed").map((log) => log.fields?.["diagnostic"]);
    deepEqual(emitted, mode === "unavailable" ? [] : mode === "unselected" ? [generic] : [generic, detail.value]);
    equal(JSON.stringify(ready).includes("diagnostic"), false); equal(JSON.stringify(ready).includes("private-health-canary"), false);
    equal(JSON.stringify(logs).includes("private-health-canary"), false);
    const failedBody = ready.body as { checks: readonly { message?: string; metadata?: unknown }[] };
    equal(failedBody.checks[0]?.message, "Health check failed."); deepEqual(failedBody.checks[0]?.metadata, { failure: "check-failed" });
    returnedHealthy = true;
    const healthy = await shell.value.handle({ method: "GET", path: "/readyz" }); equal(healthy.status, 200); equal(calls, 2);
    const healthyBody = healthy.body as { checks: readonly { message?: string; metadata?: unknown }[] };
    equal(healthyBody.checks[0]?.message, "Health check passed."); deepEqual(healthyBody.checks[0]?.metadata, { dependency: "ready" });
    equal(JSON.stringify(healthy).includes("private-health-canary"), false);
    await shell.value.lifecycle.shutdown();
  }
  const conflict = await createPlatformServerShell({ apps: [], deps: createPlatformTestMountDeps(), diagnosticCatalogs: [platformServerDiagnosticCatalog] });
  equal(conflict.ok, false, "explicit target catalogs keep conflict validation");
  if (!conflict.ok) equal(conflict.error.code, "PLATFORM_SERVER_MOUNT_FAILED");
  const precedence = await createPlatformServerShell({ apps: [], deps: { ...createPlatformTestMountDeps(), diagnostics: { report: () => ({ status: "rejected" }) } }, diagnosticCatalogs: [platformServerDiagnosticCatalog] });
  equal(precedence.ok, true, "an injected reporter retains selection precedence");
  console.log("Server health preserves selected dependency records, generic observations and public output through optional delivery failures.");
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
