import { deepEqual, equal } from "node:assert/strict";
import type { LogRecord } from "@kanbien/core/logging";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { createPlatformWorkerShell } from "@kanbien/platform-workers";
import { createPlatformServerShell } from "@kanbien/platform-server";
import { createPlatformTestMountDeps, createPlatformTestConfigSource, createPlatformTestQueueMessage } from "@kanbien/platform-testing";
import { platformSmokeApp, platformSmokeWorkItemAcceptedJobMessageType } from "../../src/index";
import { platformSmokeConfigSchema, platformSmokeWorkItemAcceptedValidator } from "../../src/app.mount";

for (const [value, reason] of [[undefined, "missing"], [7, "wrong-type"]] as const) {
  let reads = 0;
  const result = platformSmokeConfigSchema.parse({ get(name) { equal(name, "PLATFORM_SMOKE_APP_NAME"); reads++; return value; } });
  equal(reads, 1); equal(result.ok, false);
  if (result.ok) throw new Error("Expected configuration rejection.");
  deepEqual(result.error.diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "platform-smoke.configuration-invalid", definitionVersion: 1, detail: { field: "app-name", reason } });
  deepEqual(result.error.relatedDiagnosticRecords?.map((record) => record.detail), [{ field: "value", reader: "string", reason }]);
  equal(result.error.code, reason === "missing" ? "CONFIG_MISSING" : "CONFIG_INVALID");
}
for (const value of [null, 1, "synthetic-private-canary"]) {
  equal(platformSmokeWorkItemAcceptedValidator.validate(value), false);
  deepEqual(platformSmokeWorkItemAcceptedValidator.diagnose?.(value)?.detail, { field: "payload", reason: "wrong-shape" });
}
for (const [value, reason] of [[{}, "missing"], [{ outboxEntryId: 3 }, "wrong-type"], [{ outboxEntryId: "" }, "empty"]] as const) {
  equal(platformSmokeWorkItemAcceptedValidator.validate(value), false);
  deepEqual(platformSmokeWorkItemAcceptedValidator.diagnose?.(value)?.detail, { field: "payload.outboxEntryId", reason });
}
for (const value of [{ outboxEntryId: " " }, { outboxEntryId: "synthetic-private-canary", extra: "retained" }, Object.create({ outboxEntryId: "inherited" }), Object.assign([], { outboxEntryId: "array" })]) {
  equal(platformSmokeWorkItemAcceptedValidator.validate(value), true);
  equal(platformSmokeWorkItemAcceptedValidator.explain(value).valid, true);
  equal(platformSmokeWorkItemAcceptedValidator.diagnose?.(value), undefined);
}
let reads = 0;
const accessor = { get outboxEntryId() { reads++; return 3; } };
equal(platformSmokeWorkItemAcceptedValidator.validate(accessor), false); equal(reads, 1);
deepEqual(platformSmokeWorkItemAcceptedValidator.diagnose?.(accessor)?.detail, { field: "payload.outboxEntryId", phase: "diagnostic-projection", reason: "accessor-not-read", effect: "not-assessed" });
equal(reads, 1, "diagnostic must not re-read an application getter");
const inaccessible = new Proxy({}, { getOwnPropertyDescriptor() { throw new Error("synthetic-private-canary"); } });
const record = platformSmokeWorkItemAcceptedValidator.diagnose?.(inaccessible);
deepEqual(record?.detail, { field: "payload.outboxEntryId", phase: "diagnostic-projection", reason: "inspection-threw", effect: "not-assessed" });
equal(JSON.stringify(record).includes("synthetic-private-canary"), false);
let deep: object = { outboxEntryId: "beyond-diagnostic-budget" };
for (let index = 0; index < 32; index++) deep = Object.create(deep) as object;
equal(platformSmokeWorkItemAcceptedValidator.validate(deep), true);
deepEqual(platformSmokeWorkItemAcceptedValidator.diagnose?.(deep)?.detail, { field: "payload.outboxEntryId", phase: "diagnostic-projection", reason: "prototype-limit", effect: "not-assessed" });
console.log("App configuration and accepted-payload diagnostics preserve legacy validation and getter behaviour.");

async function delivery() {
  for (const mode of ["default", "injected", "unavailable"] as const) {
    const logs: LogRecord[] = [], records: DiagnosticRecord[] = [];
    const mountDeps = createPlatformTestMountDeps({ logger: { write(record) { if (mode === "unavailable") throw new Error("synthetic-private-canary"); logs.push(record); } } });
    const deps = mode === "injected" ? { ...mountDeps, diagnostics: { report(record: DiagnosticRecord) { records.push(record); return { status: "written" as const }; } } } : mountDeps;
    const observations = () => mode === "injected" ? records : logs.filter((record) => record.message === "platform.diagnostic.observed").map((record) => record.fields?.["diagnostic"] as DiagnosticRecord);
    const invalid = await createPlatformServerShell({ apps: [platformSmokeApp], deps });
    equal(invalid.ok, false);
    if (invalid.ok) throw new Error("Expected missing app-name rejection.");
    equal(invalid.error.code, "PLATFORM_SERVER_CONFIG_INVALID");
    deepEqual(observations().map((record) => record.code), mode === "unavailable" ? [] : ["platform-config.schema-rejected", "platform-smoke.configuration-invalid", "core.config.primitive-invalid"]);
    logs.length = 0; records.length = 0;
    const worker = await createPlatformWorkerShell({ apps: [platformSmokeApp], deps: { ...deps, config: createPlatformTestConfigSource({ PLATFORM_SMOKE_APP_NAME: "synthetic-private-canary" }) } });
    if (!worker.ok) throw new Error(worker.error.code);
    equal((await worker.value.start()).ok, true);
    equal(worker.value.enqueue(createPlatformTestQueueMessage({ type: platformSmokeWorkItemAcceptedJobMessageType, payload: { outboxEntryId: "" } })).ok, true);
    const rejected = await worker.value.runNext();
    equal(rejected.ok, true);
    if (!rejected.ok) throw new Error("Expected normal dead-letter disposition.");
    equal(rejected.value.status, "dead-lettered");
    const payloadRecords = observations().filter((record) => record.code === "platform-smoke.accepted-payload-invalid");
    deepEqual(payloadRecords.map((record) => record.detail), mode === "unavailable" ? [] : [{ field: "payload.outboxEntryId", reason: "empty" }]);
    equal(JSON.stringify(observations()).includes("synthetic-private-canary"), false);
    await worker.value.shutdown();
  }
}
void delivery().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
