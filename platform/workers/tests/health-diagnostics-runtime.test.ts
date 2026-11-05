import { deepEqual, equal } from "node:assert/strict";
import type { LogRecord } from "@kanbien/core/logging";
import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";
import { healthCheckName, healthCheckResult, monitoringComponent } from "@kanbien/core/monitoring";
import { isoDateTimeFromDate } from "@kanbien/core/shared";
import { definePlatformApp, platformAppId, platformHealthName } from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createPlatformWorkerShell } from "../src/index";

async function main(): Promise<void> {
  const id = platformAppId("healthfixture"), name = platformHealthName("healthfixture.ready");
  if (!id.ok || !name.ok) throw new Error("fixture-invalid");
  const definition = defineDiagnostic({ code: "healthfixture.check-failed", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" },
    detail: { type: "object", properties: { phase: { type: "enum", values: ["probe"] } } } } as const);
  const upstream = createDiagnosticRecord(definition, { phase: "probe" }); if (!upstream.ok) throw new Error("fixture-invalid");
  for (const mode of ["default", "injected", "unavailable"] as const) {
    const logs: LogRecord[] = [], records: unknown[] = []; let calls = 0, returnedHealthy = false;
    const deps = createPlatformTestMountDeps({ logger: { write(record) { if (mode === "unavailable") throw new Error("private-health-canary"); logs.push(record); } } });
    const shell = await createPlatformWorkerShell({ apps: [definePlatformApp({ id: id.value, name: "Health fixture", mount(registry) {
      registry.registerDiagnosticCatalog({ owner: "healthfixture", definitions: [definition] });
      registry.registerHealthCheck({ name: name.value, check: { check() {
        calls++;
        if (returnedHealthy) return healthCheckResult({ name: healthCheckName("healthfixture.ready"), type: "readiness",
          component: monitoringComponent({ type: "runtime", name: "fixture" }), status: "healthy", checkedAt: isoDateTimeFromDate(deps.clock.now()),
          message: { code: "HEALTH_FIXTURE", defaultMessage: "private-health-canary" }, metadata: { dependency: "ready", detail: "private-health-canary" } });
        return Promise.reject(Object.assign(new Error("private-health-canary"), { code: "private-health-canary", name: "private-health-canary", diagnosticRecord: upstream.value }));
      } } });
    } })], deps: mode === "injected" ? { ...deps, diagnostics: { report(record) { records.push(record); return { status: "written" }; } } } : deps });
    if (!shell.ok) throw new Error(shell.error.code);
    equal((await shell.value.start()).ok, true);
    const health = await shell.value.health(); equal(health.status, "not-ready"); equal(calls, 1);
    const generic = { schema: "core/diagnostic-record/v1", code: "health.check-rejected", definitionVersion: 1, detail: { index: 0, phase: "completion", effect: "unknown" } };
    deepEqual(mode === "injected" ? records : logs.filter((log) => log.message === "platform.diagnostic.observed").map((log) => log.fields?.["diagnostic"]), mode === "unavailable" ? [] : [generic, upstream.value]);
    equal(JSON.stringify(health).includes("diagnostic"), false); equal(JSON.stringify(health).includes("private-health-canary"), false);
    equal(health.checks[0]?.message, "Health check failed."); deepEqual(health.checks[0]?.metadata, { failure: "check-failed" });
    returnedHealthy = true;
    const healthy = await shell.value.health(); equal(healthy.status, "ready"); equal(calls, 2);
    equal(healthy.checks[0]?.message, "Health check passed."); deepEqual(healthy.checks[0]?.metadata, { dependency: "ready" });
    equal(JSON.stringify(healthy).includes("private-health-canary"), false);
    await shell.value.shutdown(); equal(calls, 2);
  }
  console.log("Worker health() retains exact rejected-check evidence without altering polling, health or cleanup.");
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
