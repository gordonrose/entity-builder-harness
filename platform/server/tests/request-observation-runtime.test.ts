import { deepEqual, equal, ok, rejects } from "node:assert/strict";
import { createInMemoryTracer, type MetricPoint } from "@kanbien/core/monitoring";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import { correlationId } from "@kanbien/core/shared";
import { definePlatformApp, platformAppId, platformCapabilityName, platformObservabilityProfileName, platformRouteName,
  type PlatformDiagnosticContext, type PlatformDiagnosticReporter, type PlatformRequestContext } from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createPlatformServerShell } from "../src/index";

const canary = "synthetic-private-request-observation";
const checkedId = platformAppId("observationfixture");
const checkedCapability = platformCapabilityName("observationfixture.execute");
const checkedProfile = platformObservabilityProfileName("observationfixture.execute");
const checkedMetricProfile = platformObservabilityProfileName("observationfixture.metrics");
if (!checkedId.ok || !checkedCapability.ok || !checkedProfile.ok || !checkedMetricProfile.ok) throw new Error("Invalid observation fixture.");
const appId = checkedId.value, capability = checkedCapability.value, profile = checkedProfile.value, metricProfile = checkedMetricProfile.value;
const definition = defineDiagnostic({ code: "observationfixture.operation", version: 1,
  classification: { failureKind: "unknown", failureSource: "app", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { index: { type: "integer", minimum: 0, maximum: 9 } } },
} as const);
const literals = Array.from({ length: 10 }, (_, index) => ({ schema: "core/diagnostic-record/v1", code: "observationfixture.operation", definitionVersion: 1, detail: { index } }));
const records = literals.map((record) => {
  const checked = createDiagnosticRecord(definition, record.detail);
  if (!checked.ok) throw new Error("Invalid observation record.");
  return checked.value;
});
type Mode = "default" | "injected" | "logger-unavailable" | "reporter-unavailable" | "reporter-throws" | "reporter-rejects";
type Observed = { record: unknown; context: PlatformDiagnosticContext };

async function fixture(mode: Mode, handler?: (context: PlatformRequestContext) => Promise<void>) {
  const observed: Observed[] = [], logs: LogRecord[] = [], callbackPresence: boolean[] = [];
  let attempts = 0, calls = 0;
  let toSend: readonly unknown[] = [records[9], ...records.slice(0, 9)];
  const base = createPlatformTestMountDeps({ logger: { write(log) {
    if (log.message === "platform.diagnostic.observed") {
      attempts++;
      if (mode === "logger-unavailable") throw new Error(canary);
      observed.push({ record: log.fields?.["diagnostic"], context: {
        capability: log.fields?.["capability"] as string, operation: log.fields?.["operation"] as string,
        stage: log.fields?.["stage"] as "request", correlationId: log.correlationId!,
      } });
    }
    logs.push(log);
  } } });
  const reporter = { report(record: DiagnosticRecord, context: PlatformDiagnosticContext) {
    attempts++;
    if (mode === "reporter-unavailable") return { status: "unavailable" as const };
    observed.push({ record, context });
    if (mode === "reporter-throws") throw new Error(canary);
    if (mode === "reporter-rejects") return Promise.reject(new Error(canary));
    return { status: "written" as const };
  } } as unknown as PlatformDiagnosticReporter;
  const app = definePlatformApp({ id: appId, name: "Request observation", mount(registry) {
    registry.registerDiagnosticCatalog({ owner: "observationfixture", definitions: [definition] });
    registry.registerObservabilityProfile({ name: profile, capability, action: "execute", signals: ["operational_log"], logFieldNames: ["capability"] });
    registry.registerObservabilityProfile({ name: metricProfile, capability, action: "execute", signals: ["metric"], metricDimensionFieldNames: ["capability"] });
    for (const name of ["observe", "opt-out", "metric-only"] as const) {
      const route = platformRouteName(`observationfixture.${name}`);
      if (!route.ok) throw new Error("Invalid observation route.");
      registry.registerRoute({ name: route.value, method: "GET", path: `/${name}`, auth: { kind: "public" },
        observability: name === "opt-out" ? { kind: "opt_out", reason: "non_user_workload_path", justification: "Prove no diagnostic output on an opted-out request." }
          : { kind: "profile", profile: name === "metric-only" ? metricProfile : profile },
        handler: { async handle(_request, context) {
          calls++; callbackPresence.push(context.onDiagnostic !== undefined);
          if (handler !== undefined) await handler(context);
          else for (const record of toSend) context.onDiagnostic?.(record as DiagnosticRecord);
          return { status: 200, body: { outcome: "confirmed" } };
        } },
      });
    }
  } });
  const injected = mode !== "default" && mode !== "logger-unavailable";
  const mounted = await createPlatformServerShell({ apps: [app], deps: injected ? { ...base, diagnostics: reporter } : base,
    rateLimiter: { check: () => ({ allowed: true }) } });
  ok(mounted.ok); ok((await mounted.value.lifecycle.start()).ok);
  observed.length = 0; logs.length = 0; attempts = 0;
  return { shell: mounted.value, observed, logs, callbackPresence,
    attempts: () => attempts, calls: () => calls, send: (values: readonly unknown[]) => { toSend = values; },
    request: (path = "/observe", id = "observation-request") => mounted.value.handle({ method: "GET", path, requestId: correlationId(id) }),
  };
}

async function delivery(): Promise<void> {
  const unhandled: unknown[] = [];
  const collectUnhandled = (cause: unknown) => { unhandled.push(cause); };
  process.on("unhandledRejection", collectUnhandled);
  try {
    for (const mode of ["default", "injected", "logger-unavailable", "reporter-unavailable", "reporter-throws", "reporter-rejects"] as const) {
      const f = await fixture(mode);
      try {
        const response = await f.request();
        equal(response.status, 200); deepEqual(response.body, { outcome: "confirmed" });
        equal(f.calls(), 1); deepEqual(f.callbackPresence, [true]); equal(f.attempts(), 10);
        const expected = mode === "logger-unavailable" || mode === "reporter-unavailable" ? []
          : [literals[9], ...literals.slice(0, 9)].map((record) => ({ record, context: {
            capability: "observationfixture.execute", operation: "request-observation", stage: "request", correlationId: "observation-request",
          } }));
        deepEqual(f.observed, expected, "The independent own observation must not displace any of the nine source records.");
        equal(JSON.stringify(f.logs).includes(canary), false);
        equal(JSON.stringify(response).includes("diagnostic"), false);
        f.observed.length = 0;
        const before = f.attempts();
        equal((await f.request("/opt-out")).status, 200);
        equal((await f.request("/metric-only")).status, 200);
        deepEqual(f.callbackPresence, [true, false, false]); equal(f.attempts(), before); deepEqual(f.observed, []);
      } finally { await f.shell.lifecycle.shutdown(); }
    }
    await new Promise<void>((resolve) => setImmediate(resolve));
    deepEqual(unhandled, [], "Rejected optional diagnostic delivery must not become an unhandled workload rejection.");
  } finally { process.removeListener("unhandledRejection", collectUnhandled); }
}

async function selection(): Promise<void> {
  for (const mode of ["default", "injected"] as const) {
    const f = await fixture(mode);
    try {
      let reads = 0;
      const accessors = { get code() { reads++; throw new Error(canary); }, definitionVersion: 1, detail: { index: 0 } };
      f.send([undefined, null, canary, accessors, { ...literals[0], definitionVersion: 2 },
        { ...literals[0], code: "unselected.operation" }, { ...literals[0], detail: { index: canary } },
        { ...literals[0], detail: { index: 0, token: canary } }]);
      equal((await f.request()).status, 200); equal(reads, 0); equal(f.attempts(), 5);
      deepEqual(f.observed.map(item => item.record), ["evidence-rejected", "evidence-rejected", "evidence-inaccessible", "evidence-rejected", "evidence-rejected"].map(reason => ({
        schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason },
      })));
      equal(JSON.stringify(f.logs).includes(canary), false);
      f.observed.length = 0;
      const mutable = { ...literals[0]!, detail: { index: 0 } };
      f.send([mutable]); equal((await f.request()).status, 200); mutable.detail.index = 9;
      deepEqual(f.observed.map((item) => item.record), [literals[0]], "Validated records are copied before an injected sink sees them.");
    } finally { await f.shell.lifecycle.shutdown(); }
  }
}

async function concurrentRequests(): Promise<void> {
  let release: (() => void) | undefined, ready: (() => void) | undefined, entered = 0;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  const bothEntered = new Promise<void>((resolve) => { ready = resolve; });
  const f = await fixture("injected", async (context) => {
    entered++; if (entered === 2) ready!();
    await gate;
    context.onDiagnostic?.(records[context.requestId === "first-request" ? 0 : 1]!);
  });
  try {
    const first = f.request("/observe", "first-request"), second = f.request("/observe", "second-request");
    await bothEntered; release!();
    deepEqual((await Promise.all([first, second])).map((response) => response.status), [200, 200]);
    deepEqual([...f.observed].sort((left, right) => String(left.context.correlationId).localeCompare(String(right.context.correlationId))), [0, 1].map((index) => ({ record: literals[index], context: {
      capability: "observationfixture.execute", operation: "request-observation", stage: "request", correlationId: index === 0 ? "first-request" : "second-request",
    } })));
    equal(f.calls(), 2);
  } finally { release?.(); await f.shell.lifecycle.shutdown(); }
}

async function main(): Promise<void> {
  await delivery(); await selection(); await concurrentRequests(); await wrapperBoundaries();
  console.log("Request observations retain independent source evidence through selected profile-governed sinks.");
}

async function wrapperBoundaries(): Promise<void> {
  const observationModule = require("../../observability/src/normalization") as Record<string, unknown>;
  const contractModule = require("../../contracts/src/observability-profiles") as Record<string, unknown>;
  const source = Object.freeze(Object.assign(new Error(canary), { diagnosticRecord: records[0], relatedDiagnosticRecords: records.slice(1, 9) }));
  const cases = ["clock", "elapsed-computation", "error-class", "profile-projection", "log-projection", "metric-projection", "trace-projection", "latency-clock"] as const;
  for (const phase of cases) for (const enabled of [true, false]) {
    const seen: DiagnosticRecord[] = [], logs: LogRecord[] = [], points: MetricPoint[] = [];
    let armed = false, failed = false, handled = 0, afterHandlerClocks = 0;
    const target = phase === "error-class" ? observationModule : contractModule;
    const key = phase === "error-class" ? "platformErrorClass" : phase === "profile-projection" ? "platformProfileAllowsSignal"
      : phase === "log-projection" ? "platformProfileLogFields" : phase === "metric-projection" ? "platformProfileMetricLabels" : "platformProfileTraceFields";
    const patch = phase !== "clock" && phase !== "elapsed-computation" && phase !== "latency-clock";
    const descriptor = Object.getOwnPropertyDescriptor(target, key)!;
    const original = descriptor.value as (...args: unknown[]) => unknown;
    if (patch) Object.defineProperty(target, key, { ...descriptor, value: (...args: unknown[]) => {
      if (armed && !failed) { failed = true; throw source; }
      return Reflect.apply(original, undefined, args);
    } });
    const deps = createPlatformTestMountDeps({
      clock: { now() {
        const value = new Date("2026-10-30T00:00:00Z");
        if (armed) {
          afterHandlerClocks++;
          if (!failed && (phase === "clock" || phase === "latency-clock" && afterHandlerClocks === 3)) { failed = true; throw source; }
          if (!failed && phase === "elapsed-computation") {
            Object.defineProperty(value, "getTime", { value() { failed = true; throw source; } });
          }
        }
        return value;
      } },
      logger: { write(record) { logs.push(record); } }, metrics: { record(point) { points.push(point); } },
    });
    const app = definePlatformApp({ id: appId, name: "Wrapper fixture", mount(registry) {
      registry.registerDiagnosticCatalog({ owner: "observationfixture", definitions: [definition] });
      registry.registerObservabilityProfile({ name: profile, capability, action: "execute", signals: enabled ? ["operational_log", "metric", "trace"] : ["metric", "trace"],
        errorClasses: ["APP_FIXED"], ...(enabled ? { logFieldNames: ["capability"] as const } : {}),
        metricDimensionFieldNames: ["capability"], traceAttributeNames: ["capability"],
        nfrObjectives: [{ nfrClass: "interactive_command", measurement: "request_response_latency" }] });
      registry.registerRoute({ name: "observationfixture.wrapper" as never, method: "GET", path: "/wrapper", auth: { kind: "public" },
        observability: { kind: "profile", profile }, handler: { handle() { handled++; armed = true; return { status: 200, body: { confirmed: true }, observability: { errorClass: "APP_FIXED" } }; } } });
    } });
    let shell: Awaited<ReturnType<typeof createPlatformServerShell>> | undefined;
    try {
      shell = await createPlatformServerShell({ apps: [app], deps: { ...deps, diagnostics: { report(record) { seen.push(record); return { status: "written" }; } } },
        tracer: createInMemoryTracer(), rateLimiter: { check: () => ({ allowed: true }) } });
      ok(shell.ok); ok((await shell.value.lifecycle.start()).ok); seen.length = 0; points.length = 0;
      const response = await shell.value.handle({ method: "GET", path: "/wrapper" });
      equal(response.status, phase === "log-projection" && !enabled ? 200 : 500); equal(handled, 1);
      const own = seen.findIndex((record) => record.code === "observability.boundary-failed");
      if (enabled) {
        ok(own >= 0);
        deepEqual(seen[own], { schema: "core/diagnostic-record/v1", code: "observability.boundary-failed", definitionVersion: 1,
          detail: { operation: "request-observation", phase: phase === "latency-clock" ? "clock" : phase, reason: "threw", effect: "observation-incomplete" } });
        deepEqual(seen.slice(own + 1, own + 10), records.slice(0, 9), "own location must not evict source9 before the request catch replaces the failure");
      } else equal(own, -1);
      if (phase === "latency-clock") equal(points.filter((point) => point.name === "platform.server.request.outcome").length, 2, "one prior outcome plus original catch's response observation; no replay of the handler");
      equal(JSON.stringify([seen, logs, response]).includes(canary), false);
    } finally {
      armed = false; if (shell?.ok) await shell.value.lifecycle.shutdown();
      if (patch) Object.defineProperty(target, key, descriptor);
    }
  }
  // The second finish remains allowed to escape: diagnostics must not replace that raw identity.
  let armed = false, calls = 0;
  const seen: DiagnosticRecord[] = [];
  const deps = createPlatformTestMountDeps({ clock: { now() { if (armed) throw source; return new Date("2026-10-30T00:00:00Z"); } } });
  const app = definePlatformApp({ id: appId, name: "Raw wrapper", mount(registry) {
    registry.registerDiagnosticCatalog({ owner: "observationfixture", definitions: [definition] });
    registry.registerObservabilityProfile({ name: profile, capability, action: "execute", signals: ["operational_log"] });
    registry.registerRoute({ name: "observationfixture.raw" as never, method: "GET", path: "/raw", auth: { kind: "public" }, observability: { kind: "profile", profile },
      handler: { handle() { calls++; armed = true; return { status: 200 }; } } });
  } });
  const shell = await createPlatformServerShell({ apps: [app], deps: { ...deps, diagnostics: { report(record) { seen.push(record); return { status: "written" }; } } }, rateLimiter: { check: () => ({ allowed: true }) } });
  ok(shell.ok); ok((await shell.value.lifecycle.start()).ok); seen.length = 0;
  try { await rejects(shell.value.handle({ method: "GET", path: "/raw" }), (error) => error === source); equal(calls, 1);
    equal(seen.filter((record) => record.code === "observability.boundary-failed").length, 2);
  } finally { armed = false; await shell.value.lifecycle.shutdown(); }
}
void main().catch((cause: unknown) => { console.error(cause); process.exitCode = 1; });
