import { deepEqual, equal } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import { healthCheckName, healthCheckResult, monitoringComponent, type HealthCheckResult } from "@kanbien/core/monitoring";
import { fixedClock, isoDateTimeFromDate } from "@kanbien/core/shared";
import { platformHealthName, type PlatformDiagnosticReporter, type PlatformHealthRegistration } from "@kanbien/platform-contracts";
import { createPlatformDiagnosticReporter, createPlatformSafeLogger } from "@kanbien/platform-observability";
import { platformHealthDiagnosticCatalog, platformReadiness } from "../src/index";

async function main(): Promise<void> {
  const clock = fixedClock(new Date("2026-10-30T00:00:00.000Z")), logs: LogRecord[] = [];
  const definition = defineDiagnostic({ code: "fixture.check-failed", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" },
    detail: { type: "object", properties: { phase: { type: "enum", values: ["probe"] } } } } as const);
  const upstream = createDiagnosticRecord(definition, { phase: "probe" }); if (!upstream.ok) throw new Error("fixture-invalid");
  const diagnostics = createPlatformDiagnosticReporter({ catalogs: [platformHealthDiagnosticCatalog, { owner: "fixture", definitions: [definition] }], clock,
    logger: createPlatformSafeLogger({ write(record) { logs.push(record); } }) });
  const name = platformHealthName("fixture.check"); if (!name.ok) throw new Error("fixture-invalid");
  const registration = (check: PlatformHealthRegistration["check"]["check"]): PlatformHealthRegistration => ({ name: name.value, check: { check } });
  const result = (status: HealthCheckResult["status"] = "healthy"): HealthCheckResult => healthCheckResult({ name: healthCheckName("fixture.check"), type: "readiness",
    component: monitoringComponent({ type: "runtime", name: "fixture" }), status, checkedAt: isoDateTimeFromDate(clock.now()) });
  const observed = () => logs.filter((log) => log.message === "platform.diagnostic.observed").map((log) => log.fields?.["diagnostic"]);
  const literal = (code: string, detail: unknown) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
  for (const mode of ["healthy", "degraded", "unhealthy", "throw", "reject", "projection"] as const) {
    logs.length = 0; let calls = 0;
    const error = Object.assign(new Error("private-health-canary"), { diagnosticRecord: upstream.value });
    const summary = await platformReadiness({ clock, lifecycleReady: true, diagnostics, healthChecks: [registration(() => {
      calls++;
      if (mode === "throw") throw error;
      if (mode === "reject") return Promise.reject(error);
      if (mode === "projection") return Object.defineProperty({ ...result(), diagnosticRecord: upstream.value }, "component", { get() { throw new Error("private-health-canary"); } });
      return { ...result(mode), diagnosticRecord: upstream.value };
    })] });
    equal(calls, 1); equal(summary.status, mode === "healthy" ? "ready" : "not-ready");
    const generic = mode === "healthy" ? [] : mode === "degraded" || mode === "unhealthy"
      ? [literal("health.check-not-ready", { index: 0, status: mode, phase: "result", effect: "returned-not-ready" })]
      : [literal(`health.check-${mode === "projection" ? "projection-failed" : mode === "throw" ? "threw" : "rejected"}`,
        { index: 0, phase: mode === "projection" ? "projection" : mode === "throw" ? "invocation" : "completion", effect: mode === "projection" ? "output-unhealthy" : "unknown" })];
    deepEqual(observed(), mode === "healthy" ? [] : mode === "throw" || mode === "reject" ? [...generic, upstream.value] : [upstream.value, ...generic]);
    equal(JSON.stringify(summary).includes("diagnostic"), false); equal(JSON.stringify(summary).includes("private-health-canary"), false);
    equal(JSON.stringify(logs).includes("private-health-canary"), false);
  }
  for (const checks of [[], [registration(() => result())]]) {
    logs.length = 0;
    equal((await platformReadiness({ lifecycleReady: false, clock, diagnostics, healthChecks: checks })).status, "not-ready");
    deepEqual(observed(), [literal("health.lifecycle-not-ready", { phase: "aggregation", effect: "output-not-ready" })]);
  }
  logs.length = 0; let getters = 0;
  const withGetter = Object.defineProperty(result("unhealthy"), "diagnosticRecord", { get() { getters++; throw new Error("private-health-canary"); } });
  const malformed = { ...result("degraded"), diagnosticRecord: { ...upstream.value, detail: { private: "private-health-canary" } }, relatedDiagnosticRecords: [upstream.value] };
  const safe = await platformReadiness({ lifecycleReady: true, clock, diagnostics, healthChecks: [registration(() => withGetter), registration(() => malformed)] });
  equal(getters, 0); deepEqual(safe.checks.map((check) => check.status), ["unhealthy", "degraded"]);
  deepEqual(observed(), [literal("health.check-not-ready", { index: 0, status: "unhealthy", phase: "result", effect: "returned-not-ready" }), upstream.value,
    literal("health.check-not-ready", { index: 1, status: "degraded", phase: "result", effect: "returned-not-ready" })]);
  equal(JSON.stringify(logs).includes("private-health-canary"), false);

  const order: number[] = []; let complete!: (value: HealthCheckResult) => void;
  const pending = new Promise<HealthCheckResult>((resolve) => { complete = resolve; });
  const aggregate = platformReadiness({ lifecycleReady: true, clock, diagnostics, healthChecks: [registration(() => { order.push(0); return pending; }), registration(() => { order.push(1); return result(); })] });
  deepEqual(order, [0, 1]); let settled = false; void aggregate.then(() => { settled = true; });
  await Promise.resolve(); equal(settled, false, "health retains its existing wait policy without adding deadlines");
  complete(result()); equal((await aggregate).status, "ready"); deepEqual(order, [0, 1]);

  const withoutCatalog = createPlatformDiagnosticReporter({ catalogs: [{ owner: "fixture", definitions: [definition] }], logger: { write() { throw new Error("private-health-canary"); } }, clock });
  for (const reporter of [undefined, withoutCatalog, { report() { throw new Error("private-health-canary"); } } as PlatformDiagnosticReporter]) {
    let calls = 0;
    const summary = await platformReadiness({ lifecycleReady: true, clock, ...(reporter === undefined ? {} : { diagnostics: reporter }),
      healthChecks: [registration(() => { calls++; throw new Error("private-health-canary"); })] });
    equal(summary.status, "not-ready"); equal(calls, 1);
  }
  // User-approved compatibility change: public detail is defined by Health,
  // not arbitrary check messages, metadata keys or exception strings.
  const canary = "private-public-health-canary";
  let privateReads = 0;
  const privateMessage = Object.defineProperty({ code: canary }, "defaultMessage", { get() { privateReads++; throw new Error(canary); } });
  const metadata = Object.defineProperties({ dependency: "ready", config: "present", arbitrary: canary,
    nested: { error: Object.assign(new Error(canary), { code: canary, name: canary }) } }, {
    password: { enumerable: true, get() { privateReads++; throw new Error(canary); } },
  });
  for (const [status, message] of [["healthy", "Health check passed."], ["degraded", "Health check is degraded."], ["unhealthy", "Health check failed."]] as const) {
    logs.length = 0; let calls = 0;
    const summary = await platformReadiness({ lifecycleReady: true, clock, diagnostics, healthChecks: [registration(() => {
      calls++; return { ...result(status), durationMs: 3, message: privateMessage as never, metadata: metadata as unknown as NonNullable<HealthCheckResult["metadata"]>, diagnosticRecord: upstream.value };
    })] });
    equal(calls, 1); equal(summary.status, status === "healthy" ? "ready" : "not-ready");
    deepEqual(summary.checks[0], { name: "fixture.check", type: "readiness", component: "fixture", status,
      checkedAt: "2026-10-30T00:00:00.000Z", durationMs: 3, message, metadata: { dependency: "ready", config: "present" } });
    equal(JSON.stringify(summary).includes(canary), false); equal(JSON.stringify(logs).includes(canary), false);
    deepEqual(observed(), status === "healthy" ? [] : [upstream.value,
      literal("health.check-not-ready", { index: 0, status, phase: "result", effect: "returned-not-ready" })]);
  }
  for (const dependency of ["ready", "not-ready", "unknown", canary]) {
    const summary = await platformReadiness({ lifecycleReady: true, clock, healthChecks: [registration(() => ({ ...result(), metadata: { dependency } }))] });
    deepEqual(summary.checks[0]?.metadata, dependency === canary ? {} : { dependency });
  }
  for (const config of ["missing", "present", canary]) {
    const summary = await platformReadiness({ lifecycleReady: true, clock, healthChecks: [registration(() => ({ ...result(), metadata: { config } }))] });
    deepEqual(summary.checks[0]?.metadata, config === canary ? {} : { config });
  }
  const inherited = Object.create({ dependency: "ready" }) as Record<string, never>;
  const accessor = Object.defineProperty({}, "dependency", { enumerable: true, get() { privateReads++; throw new Error(canary); } });
  const coercible = { toString() { privateReads++; throw new Error(canary); } };
  const uninspectable = new Proxy({}, { getOwnPropertyDescriptor() { throw new Error(canary); }, ownKeys() { privateReads++; throw new Error(canary); } });
  for (const value of [inherited, accessor, { dependency: coercible }, uninspectable, { arbitrary: canary }]) {
    const summary = await platformReadiness({ lifecycleReady: true, clock, healthChecks: [registration(() => ({ ...result(), metadata: value as never }))] });
    equal(summary.status, "ready"); deepEqual(summary.checks[0]?.metadata, {});
  }
  equal(privateReads, 0, "public projection must not evaluate withheld text, unknown keys, accessors or coercions");
  const absent = await platformReadiness({ lifecycleReady: true, clock, healthChecks: [registration(() => result())] });
  equal(Object.prototype.hasOwnProperty.call(absent.checks[0], "message"), false);
  equal(Object.prototype.hasOwnProperty.call(absent.checks[0], "metadata"), false);
  for (const rejected of [false, true]) {
    logs.length = 0;
    const error = Object.assign(new Error(canary), { name: canary, code: canary, diagnosticRecord: upstream.value });
    const summary = await platformReadiness({ lifecycleReady: true, clock, diagnostics, healthChecks: [registration(() => {
      if (rejected) return Promise.reject(error); throw error;
    })] });
    equal(summary.status, "not-ready"); equal(summary.checks[0]?.status, "unhealthy");
    equal(summary.checks[0]?.message, "Health check failed."); deepEqual(summary.checks[0]?.metadata, { failure: "check-failed" });
    equal(JSON.stringify(summary).includes(canary), false); equal(JSON.stringify(logs).includes(canary), false);
    deepEqual(observed(), [literal(rejected ? "health.check-rejected" : "health.check-threw",
      { index: 0, phase: rejected ? "completion" : "invocation", effect: "unknown" }), upstream.value]);
  }
  console.log("Health exact phases, preserved internal records, controlled public detail and independent reporter isolation passed.");
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
