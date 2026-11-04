import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { isoDateTimeFromDate } from "@kanbien/core/shared";
import { platformAppId, type PlatformApp } from "@kanbien/platform-contracts";
import {
  createPlatformRuntimeLifecycle, platformRuntimeBoundaryDiagnostic, platformRuntimeDiagnosticCatalog,
  platformRuntimeStateDiagnostic, type PlatformRuntimeError, type PlatformRuntimeLifecycleController,
} from "../src/index";

const secret = "private-runtime-canary@example.invalid";
const cause = new Error(secret);
const id = platformAppId("fixture"); if (!id.ok) throw new Error("Fixture invalid");
const appId = id.value;
const app = (lifecycle: PlatformApp["lifecycle"] = {}): PlatformApp => ({ id: id.value, name: secret, mount() {}, lifecycle });
function failed(result: { readonly ok: boolean; readonly error?: PlatformRuntimeError }): PlatformRuntimeError {
  equal(result.ok, false); if (!result.error) throw new Error("Expected failure"); return result.error;
}
function detail(record: DiagnosticRecord | undefined, expected: Record<string, unknown>): void {
  equal(record?.code, "platform-runtime.boundary-failed"); equal(record?.definitionVersion, 1);
  deepEqual(record?.detail, expected);
  equal(JSON.stringify(record).includes(secret), false);
}
const base = { operation: "start", phase: "app.beforeStart", subject: "app", boundary: "invocation", effect: "step-completion-unobserved", ordinal: 0 };

async function main(): Promise<void> {
  equal(platformRuntimeDiagnosticCatalog.owner, "platform-runtime");
  deepEqual(platformRuntimeBoundaryDiagnostic.classification, { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false });
  deepEqual(platformRuntimeStateDiagnostic.classification, { failureKind: "validation", failureSource: "platform", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false });
  const seen: DiagnosticRecord[] = [];
  let controller = createPlatformRuntimeLifecycle({ apps: [app({ beforeStart() { throw cause; } })], onDiagnostic(record) { seen.push(record); } });
  let error = failed(await controller.start());
  equal(error.code, "PLATFORM_RUNTIME_LIFECYCLE_FAILED"); equal(error.defaultMessage, "Runtime startup lifecycle failed.");
  deepEqual(error.details, { state: "starting" }); equal(error.cause, cause); equal(controller.state(), "failed");
  detail(error.diagnosticRecord, base); equal(seen.length, 1);
  const stateError = failed(await controller.start());
  equal(stateError.diagnosticRecord?.code, "platform-runtime.state-rejected"); equal(stateError.diagnosticRecord?.definitionVersion, 1);
  deepEqual(stateError.diagnosticRecord?.detail, { operation: "start", state: "failed", effect: "state-unchanged" });

  // The existing guard and argument expressions read lifecycle/hook twice, then fail before invocation.
  let lifeReads = 0, hookReads = 0, idReads = 0, effects = 0;
  const hooks = { get beforeStart() { if (++hookReads === 2) throw cause; return () => { effects++; }; } };
  const observed = { ...app(), get id() { idReads++; return appId; }, get lifecycle() { lifeReads++; return hooks; } };
  controller = createPlatformRuntimeLifecycle({ apps: [observed] });
  error = failed(await controller.start());
  deepEqual([lifeReads, hookReads, idReads, effects], [2, 2, 1, 0]);
  detail(error.diagnosticRecord, { ...base, boundary: "selection", effect: "step-not-invoked" });
  hookReads = 0;
  controller = createPlatformRuntimeLifecycle({ apps: [app({ get beforeStart() { return ++hookReads === 1 ? () => undefined : undefined; } } as never)] });
  error = failed(await controller.start());
  equal((error.cause as Error).message, "step is not a function");
  detail(error.diagnosticRecord, base);
  let receiver: unknown = secret;
  controller = createPlatformRuntimeLifecycle({ apps: [app({ beforeStart() { receiver = this; } })] });
  equal((await controller.start()).ok, true); equal(receiver, undefined);

  // A rejected completion is not evidence that the effect did not happen.
  controller = createPlatformRuntimeLifecycle({ apps: [app({ beforeStart() { effects++; return Promise.reject(cause); } })] });
  error = failed(await controller.start());
  detail(error.diagnosticRecord, { ...base, boundary: "completion" });
  equal(effects, 1);
  let clockCalls = 0;
  controller = createPlatformRuntimeLifecycle({ apps: [app({ beforeStart() { effects++; } })], clock: { now() { clockCalls++; throw cause; } } });
  error = failed(await controller.start()); equal(error.cause, cause); equal(effects, 2); equal(clockCalls, 1); equal(controller.events().length, 0);
  detail(error.diagnosticRecord, { ...base, boundary: "event-clock", effect: "step-completed-event-unrecorded" });

  const invalidDateSeen: DiagnosticRecord[] = [];
  controller = createPlatformRuntimeLifecycle({ apps: [app({ beforeStart() {} })], clock: { now: () => new Date(NaN) }, onDiagnostic(r) { invalidDateSeen.push(r); } });
  error = failed(await controller.start());
  equal(error.diagnosticRecord?.code, "core.shared.date-normalization-threw");
  detail(invalidDateSeen[0], { ...base, boundary: "event-normalization", effect: "step-completed-event-unrecorded" });
  equal(invalidDateSeen.length, 2);

  // Resolving events.push still precedes timestamp evaluation, even for non-callable push.
  for (const throwingGetter of [false, true]) {
    controller = createPlatformRuntimeLifecycle({ apps: [app({ beforeStart() {} })], clock: { now() { clockCalls++; return new Date("2026-01-01T00:00:00Z"); } } });
    const push = Object.getOwnPropertyDescriptor(Array.prototype, "push")!;
    let target: unknown, accesses = 0; clockCalls = 0;
    Object.defineProperty(Array.prototype, "push", { configurable: true, get(this: unknown) {
      if (target === undefined) target = this;
      if (this === target) { accesses++; if (throwingGetter) throw cause; return 42; }
      return push.value;
    } });
    try { error = failed(await controller.start()); }
    finally { Object.defineProperty(Array.prototype, "push", push); }
    equal(accesses, 1); equal(clockCalls, throwingGetter ? 0 : 1);
    equal(throwingGetter ? error.cause : (error.cause as Error).message, throwingGetter ? cause : "events.push is not a function");
    detail(error.diagnosticRecord, { ...base, boundary: throwingGetter ? "event-selection" : "event-append", effect: throwingGetter ? "step-completed-event-unrecorded" : "step-completed-event-outcome-unknown" });
  }

  const phases = ["app.beforeStart", "resource.start", "app.afterStart", "app.beforeStop", "resource.drain", "resource.close", "telemetry.flush", "app.afterStop"] as const;
  for (const phase of phases) {
    const call = (at: string) => () => { if (phase === at) throw cause; };
    controller = createPlatformRuntimeLifecycle({ apps: [app({ beforeStart: call("app.beforeStart"), afterStart: call("app.afterStart"), beforeStop: call("app.beforeStop"), afterStop: call("app.afterStop") })],
      resources: [{ name: secret, start: call("resource.start"), drain: call("resource.drain"), close: call("resource.close") }], telemetry: [{ name: secret, flush: call("telemetry.flush") }] });
    const start = await controller.start();
    error = failed(phase === "app.beforeStart" || phase === "resource.start" || phase === "app.afterStart" ? start : await controller.shutdown());
    detail(error.diagnosticRecord, { operation: phase === "app.beforeStart" || phase === "resource.start" || phase === "app.afterStart" ? "start" : "shutdown", phase,
      subject: phase.startsWith("app.") ? "app" : phase.startsWith("resource.") ? "resource" : "telemetry", boundary: "invocation", effect: "step-completion-unobserved", ordinal: 0 });
  }
  let order = "";
  controller = createPlatformRuntimeLifecycle({ apps: [], resources: [
    { name: "first", drain() { order += "d1"; }, close() { order += "c1"; } },
    { name: "second", drain() { order += "d2"; }, close() { order += "c2"; throw cause; } },
  ], telemetry: [{ name: secret, flush() { order += "flush"; } }] });
  await controller.start(); error = failed(await controller.shutdown()); equal(order, "d1d2c2");
  detail(error.diagnosticRecord, { operation: "shutdown", phase: "resource.close", subject: "resource", boundary: "invocation", effect: "step-completion-unobserved", ordinal: 0 });

  // Construction remains synchronous and stops before subsequent dependency reads.
  for (const phase of ["resources-snapshot", "telemetry-snapshot", "apps-snapshot", "clock-selection"] as const) {
    const emitted: DiagnosticRecord[] = []; let reads = "";
    const input = { get resources() { reads += "r"; if (phase === "resources-snapshot") throw cause; return []; },
      get telemetry() { reads += "t"; if (phase === "telemetry-snapshot") throw cause; return []; },
      get apps() { reads += "a"; if (phase === "apps-snapshot") throw cause; return []; },
      get clock(): never { reads += "c"; throw cause; }, onDiagnostic(r: DiagnosticRecord) { emitted.push(r); } };
    throws(() => createPlatformRuntimeLifecycle(input), (e) => e === cause);
    equal(reads, phase === "resources-snapshot" ? "r" : phase === "telemetry-snapshot" ? "rt" : phase === "apps-snapshot" ? "rta" : "rtac");
    detail(emitted[0], { operation: "construct-lifecycle", phase, subject: "runtime", boundary: "selection", effect: "boundary-outcome-unknown" });
  }
  let iterations = 0;
  const resources = { *[Symbol.iterator]() { iterations++; yield { name: secret, start() {} }; } };
  controller = createPlatformRuntimeLifecycle({ apps: [], resources: resources as never });
  equal(iterations, 1); equal((await controller.start()).ok, true); equal((await controller.shutdown()).ok, true); equal(iterations, 1);

  // A separate invalid-state call cannot overwrite an in-flight invocation's location.
  let release!: () => void;
  controller = createPlatformRuntimeLifecycle({ apps: [app({ beforeStart: () => new Promise<void>((resolve) => { release = resolve; }) })], clock: { now() { throw cause; } } });
  const pending = controller.start(); equal(failed(await controller.shutdown()).code, "PLATFORM_RUNTIME_INVALID_STATE"); release();
  detail(failed(await pending).diagnosticRecord, { ...base, boundary: "event-clock", effect: "step-completed-event-unrecorded" });

  const upstream = defineDiagnostic({ code: "fixture.failure", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" }, detail: { type: "object", properties: {} } });
  const checked = createDiagnosticRecord(upstream, {}); if (!checked.ok) throw new Error("Fixture record invalid");
  const source = { diagnosticRecord: checked.value, relatedDiagnosticRecords: Array.from({ length: 8 }, () => checked.value) };
  const all: DiagnosticRecord[] = [];
  controller = createPlatformRuntimeLifecycle({ apps: [app({ beforeStart() { throw source; } })], diagnosticDefinitions: [upstream], onDiagnostic(r) { all.push(r); throw cause; } });
  error = failed(await controller.start()); equal(error.cause, source); equal(error.diagnosticRecord?.code, "fixture.failure"); equal(error.relatedDiagnosticRecords?.length, 8); equal(all.length, 10);
  detail(all[0], base);
  equal((await createPlatformRuntimeLifecycle({ apps: [], get diagnosticDefinitions(): never { throw cause; }, onDiagnostic() { return Promise.reject(cause); } }).start()).ok, true);

  // Snapshot failures keep the original sync events()/async shutdown escape policy.
  async function projectionFailure(mode: "events" | "created" | "stopped" | "cleanup"): Promise<void> {
    const emitted: DiagnosticRecord[] = [];
    const c: PlatformRuntimeLifecycleController = createPlatformRuntimeLifecycle({ apps: [], onDiagnostic(r) { emitted.push(r); } });
    if (mode === "stopped") await c.shutdown();
    if (mode === "cleanup") await c.start();
    const iterator = Object.getOwnPropertyDescriptor(Array.prototype, Symbol.iterator)!;
    let target: object | undefined;
    Object.defineProperty(Array.prototype, Symbol.iterator, { configurable: true, get(this: object) { target = this; return iterator.value; } });
    try { c.events(); } finally { Object.defineProperty(Array.prototype, Symbol.iterator, iterator); }
    if (target === undefined) throw new Error("Missing event array");
    Object.defineProperty(target, Symbol.iterator, { configurable: true, value() { throw cause; } });
    try {
      if (mode === "events") throws(() => c.events(), (e) => e === cause);
      else if (mode === "cleanup") { error = failed(await c.shutdown()); equal(error.cause, cause); equal(c.state(), "failed"); }
      else { await rejects(c.shutdown(), (e) => e === cause); equal(c.state(), "stopped"); }
    } finally { Reflect.deleteProperty(target, Symbol.iterator); }
    detail(emitted[0], { operation: mode === "events" ? "events" : "shutdown", phase: "events-projection", subject: "runtime", boundary: "projection",
      effect: mode === "cleanup" ? "cleanup-completed-result-not-returned" : "boundary-outcome-unknown" });
  }
  for (const mode of ["events", "created", "stopped", "cleanup"] as const) await projectionFailure(mode);
  equal(isoDateTimeFromDate(new Date("2026-01-01T00:00:00Z")), "2026-01-01T00:00:00.000Z");
}
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
