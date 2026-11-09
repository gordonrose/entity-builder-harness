import { deepEqual, equal } from "node:assert/strict";
import { definePlatformApp, platformAppId, platformJobName, platformCapabilityName, platformObservabilityProfileName } from "@kanbien/platform-contracts";
import type { LogRecord } from "@kanbien/core/logging";
import type { QueueMessageType } from "@kanbien/core/queues";
import { createPlatformTestMountDeps, createPlatformTestQueueMessage } from "@kanbien/platform-testing";
import { createPlatformWorkerShell } from "../../src/index";

async function main(): Promise<void> {
  const appId = platformAppId("metricfixture"), job = platformJobName("metricfixture.execute"),
    capability = platformCapabilityName("metricfixture.execute"), profile = platformObservabilityProfileName("metricfixture.execute");
  if (!appId.ok || !job.ok || !capability.ok || !profile.ok) throw new Error("fixture-invalid");
  for (const mode of ["default", "injected", "metrics-only"] as const) {
    const logs: LogRecord[] = [], injected: { record: unknown; operation: string }[] = [];
    let calls = 0, handled = 0;
    const deps = createPlatformTestMountDeps({ logger: { write(record) { logs.push(record); } }, metrics: { record() { calls++; throw new Error("metrics-private-canary"); } } });
    const shell = await createPlatformWorkerShell({ apps: [definePlatformApp({ id: appId.value, name: "Metrics fixture", mount(registry) {
      registry.registerObservabilityProfile({ name: profile.value, capability: capability.value, action: "execute",
        signals: mode === "metrics-only" ? ["metric"] : ["metric", "operational_log"],
        nfrObjectives: [{ nfrClass: "async_completion", measurement: "job_execution_latency" }, { nfrClass: "async_queue_delay", measurement: "queue_wait_latency" }] });
      registry.registerJob({ name: job.value, messageType: "metricfixture.execute" as QueueMessageType,
        observability: { kind: "profile", profile: profile.value }, handler: { handle() { handled++; } } });
    } })], deps: mode === "injected" ? { ...deps, diagnostics: { report(record, context) { injected.push({ record, operation: context.operation }); return { status: "written" }; } } } : deps });
    if (!shell.ok) throw new Error(shell.error.code);
    equal((await shell.value.start()).ok, true);
    for (let attempt = 0; attempt < 20; attempt++) {
      equal(shell.value.enqueue(createPlatformTestQueueMessage({ id: `metric-fixture-${attempt}`, type: "metricfixture.execute" as QueueMessageType, payload: {} })).ok, true);
      const result = await shell.value.runNext();
      if (!result.ok) throw new Error(result.error.code);
      equal(result.value.status, "succeeded");
    }
    equal(handled, 20); equal(calls, 60);
    const reported = mode === "injected" ? injected : logs.filter((log) => log.message === "platform.diagnostic.observed")
      .map((log) => ({ record: log.fields?.["diagnostic"], operation: log.fields?.["operation"] }));
    deepEqual(reported.map((row) => row.operation).sort(), mode === "metrics-only" ? [] : ["job-delivery", "job-execution", "job-queue-wait"]);
    for (const row of reported) deepEqual(row.record, { schema: "core/diagnostic-record/v1", code: "observability.metric-recording-failed", definitionVersion: 1,
      detail: { reason: "unclassified-invocation-failure", phase: "record-invocation", effect: "unknown" } });
    equal(JSON.stringify(reported).includes("metrics-private-canary"), false);
    await shell.value.shutdown();
  }
  console.log("Worker metric diagnostics preserve delivery outcomes, exact locations, bounded reporting and opt-outs.");
}
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
