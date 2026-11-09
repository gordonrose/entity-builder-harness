import { deepEqual, equal } from "node:assert/strict";
import { definePlatformApp, platformAppId, platformRouteName, platformCapabilityName, platformObservabilityProfileName } from "@kanbien/platform-contracts";
import type { LogRecord } from "@kanbien/core/logging";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createPlatformServerShell } from "../../src/index";

async function main(): Promise<void> {
  const appId = platformAppId("metricfixture"), route = platformRouteName("metricfixture.read"),
    capability = platformCapabilityName("metricfixture.read"), profile = platformObservabilityProfileName("metricfixture.read");
  if (!appId.ok || !route.ok || !capability.ok || !profile.ok) throw new Error("fixture-invalid");
  for (const mode of ["default", "injected", "metrics-only"] as const) {
    const logs: LogRecord[] = [], injected: { record: unknown; operation: string }[] = [];
    let calls = 0;
    const deps = createPlatformTestMountDeps({ logger: { write(record) { logs.push(record); } }, metrics: { record() { calls++; return Promise.reject(new Error("metrics-private-canary")); } } });
    const shell = await createPlatformServerShell({ apps: [definePlatformApp({ id: appId.value, name: "Metrics fixture", mount(registry) {
      registry.registerObservabilityProfile({ name: profile.value, capability: capability.value, action: "read",
        signals: mode === "metrics-only" ? ["metric"] : ["metric", "operational_log"],
        nfrObjectives: [{ nfrClass: "interactive_read", measurement: "request_response_latency" }] });
      registry.registerRoute({ name: route.value, method: "GET", path: "/metric-fixture", auth: { kind: "public" },
        observability: { kind: "profile", profile: profile.value }, handler: { handle: () => ({ status: 204 }) } });
    } })], deps: mode === "injected" ? { ...deps, diagnostics: { report(record, context) { injected.push({ record, operation: context.operation }); return { status: "written" }; } } } : deps });
    if (!shell.ok) throw new Error(shell.error.code);
    equal((await shell.value.lifecycle.start()).ok, true);
    for (let attempt = 0; attempt < 20; attempt++) equal((await shell.value.handle({ method: "GET", path: "/metric-fixture" })).status, 204);
    await new Promise<void>((resolve) => setImmediate(resolve));
    equal(calls, 40, "outcome and latency each retain their normal invocation count");
    const reported = mode === "injected" ? injected : logs.filter((log) => log.message === "platform.diagnostic.observed")
      .map((log) => ({ record: log.fields?.["diagnostic"], operation: log.fields?.["operation"] }));
    deepEqual(reported.map((row) => row.operation).sort(), mode === "metrics-only" ? [] : ["request-latency", "request-outcome"]);
    for (const row of reported) {
      deepEqual(row.record, { schema: "core/diagnostic-record/v1", code: "observability.metric-recording-failed", definitionVersion: 1,
        detail: { reason: "unclassified-invocation-failure", phase: "record-invocation", effect: "unknown" } });
    }
    equal(JSON.stringify(reported).includes("metrics-private-canary"), false);
    await shell.value.lifecycle.shutdown();
  }
  console.log("Server metric diagnostics reach default/injected reporters once per location and honor metric-only profiles.");
}
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
