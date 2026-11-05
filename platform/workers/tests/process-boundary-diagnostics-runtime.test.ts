import { deepEqual, equal, rejects } from "node:assert/strict";
import { setImmediate as nextTurn } from "node:timers/promises";
import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";
import type { LogRecord, Logger } from "@kanbien/core/logging";
import { platformAppId, type PlatformApp } from "@kanbien/platform-contracts";
import { startPlatformWorkerProcess } from "../src/index";

const secret = "worker-private-process-canary@example.invalid";
const checkedId = platformAppId("processfixture"); if (!checkedId.ok) throw new Error("Invalid fixture");
const id = checkedId.value;
const definition = defineDiagnostic({ code: "processfixture.source-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { index: { type: "integer", minimum: 0, maximum: 7 } } } });
const records = Array.from({ length: 8 }, (_, index) => { const result = createDiagnosticRecord(definition, { index }); if (!result.ok) throw new Error("Invalid fixture"); return result.value; });
const source = Object.assign(new Error(secret), { diagnosticRecord: records[0], relatedDiagnosticRecords: records });
const app = (lifecycle: PlatformApp["lifecycle"] = {}): PlatformApp => ({ id, name: secret, lifecycle, mount(registry) { registry.registerDiagnosticCatalog({ owner: "processfixture", definitions: [definition] }); } });
const worker = (operation: string, phase: string, boundary: string, effect: string) => ({ schema: "core/diagnostic-record/v1", code: "platform-worker.boundary-failed", definitionVersion: 1, detail: { operation, phase, boundary, effect } });
const runtime = (operation: string, phase: string) => ({ schema: "core/diagnostic-record/v1", code: "platform-runtime.boundary-failed", definitionVersion: 1,
  detail: { operation, phase, subject: "app", boundary: "invocation", effect: "step-completion-unobserved", ordinal: 0 } });
function sink(failMessage?: string, unavailable = false) {
  const observed: unknown[] = [], logs: LogRecord[] = []; let attempts = 0;
  const logger: Logger = { write(record) {
    if (record.message === failMessage) throw source;
    if (record.message === "platform.diagnostic.observed") { attempts++; if (unavailable) throw source; observed.push(record.fields?.["diagnostic"]); }
    logs.push(record);
  } };
  return { logger, observed, logs, attempts: () => attempts };
}
async function main(): Promise<void> {
  for (const unavailable of [false, true]) {
    const target = sink("platform.worker.started", unavailable); let starts = 0, stops = 0;
    await rejects(startPlatformWorkerProcess({ apps: [app({ beforeStart() { starts++; }, beforeStop() { stops++; } })], logger: target.logger, installSignalHandlers: false }), (error) => error === source);
    deepEqual([starts, stops], [1, 0]); equal(target.attempts(), 10);
    deepEqual(target.observed, unavailable ? [] : [worker("process-start", "startup-log", "invocation", "process-not-returned"), records[0], ...records]);
    equal(JSON.stringify(target.logs).includes(secret), false);
  }
  const getterSink = sink(); let writeReads = 0;
  const write = getterSink.logger.write;
  Object.defineProperty(getterSink.logger, "write", { get() { if (++writeReads === 1) throw source; return write; } });
  await rejects(startPlatformWorkerProcess({ apps: [app()], logger: getterSink.logger, installSignalHandlers: false }), (error) => error === source);
  equal(writeReads, 11); deepEqual(getterSink.observed, [worker("process-start", "startup-log", "selection", "process-not-returned"), records[0], ...records]);
  const failedStart = sink();
  const start = await startPlatformWorkerProcess({ apps: [app({ beforeStart() { throw source; } })], logger: failedStart.logger, installSignalHandlers: false });
  equal(start.ok, false); if (start.ok) throw new Error("Expected failure"); equal(start.error.code, "PLATFORM_WORKER_NOT_READY");
  deepEqual(start.error.diagnosticRecord, records[0]); deepEqual(start.error.relatedDiagnosticRecords, records);
  deepEqual(failedStart.observed, [runtime("start", "app.beforeStart"), records[0], ...records]);
  equal(failedStart.logs.some((record) => record.message === "platform.worker.started"), false);

  const ignored = sink(); let stops = 0;
  const ignoredProcess = await startPlatformWorkerProcess({ apps: [app({ beforeStop() { stops++; throw source; } })], logger: ignored.logger, installSignalHandlers: false });
  if (!ignoredProcess.ok) throw new Error(ignoredProcess.error.code);
  equal(await ignoredProcess.value.close(), undefined); equal(stops, 1); equal(ignoredProcess.value.shell.lifecycle.state(), "failed");
  deepEqual(ignored.observed, [runtime("shutdown", "app.beforeStop"), records[0], ...records]);

  // Process close preserves the raw queue-close rejection; the lower boundary emits it only once.
  const raw = sink(); const rawProcess = await startPlatformWorkerProcess({ apps: [app()], logger: raw.logger, installSignalHandlers: false });
  if (!rawProcess.ok) throw new Error(rawProcess.error.code); let closeCalls = 0;
  rawProcess.value.shell.queue.close = function () { equal(arguments.length, 0); closeCalls++; throw source; };
  await rejects(rawProcess.value.close(), (error) => error === source); equal(closeCalls, 1);
  equal(rawProcess.value.shell.lifecycle.state(), "ready");
  deepEqual(raw.observed, [worker("shutdown", "queue-close", "selection-or-invocation", "lifecycle-shutdown-not-invoked"), records[0], ...records]);

  // Preserve process.once's receiver, two arguments, order and partial registration if its second call throws.
  const once = Object.getOwnPropertyDescriptor(process, "once");
  const originalOnce = process.once;
  const restoreOnce = (): void => { if (once) Object.defineProperty(process, "once", once); else Reflect.deleteProperty(process, "once"); };
  const selectionSink = sink(); let onceReads = 0;
  Object.defineProperty(process, "once", { configurable: true, get(): never { onceReads++; throw source; } });
  try { await rejects(startPlatformWorkerProcess({ apps: [app()], logger: selectionSink.logger }), (error) => error === source); }
  finally { restoreOnce(); }
  equal(onceReads, 1); deepEqual(selectionSink.observed, [worker("process-start", "signal-registration", "selection", "process-not-returned"), records[0], ...records]);
  const registration = sink(); let registrationCalls = 0, registered = "";
  Object.defineProperty(process, "once", { configurable: true, value: function (this: NodeJS.Process, event: string, _callback: unknown) {
    equal(this, process); equal(arguments.length, 2); registered += event; if (++registrationCalls === 2) throw source; return process;
  } });
  try { await rejects(startPlatformWorkerProcess({ apps: [app()], logger: registration.logger }), (error) => error === source); }
  finally { restoreOnce(); }
  equal(process.once, originalOnce); equal(registered, "SIGTERMSIGINT"); equal(registrationCalls, 2);
  deepEqual(registration.observed, [worker("process-start", "signal-registration", "invocation", "process-not-returned"), records[0], ...records]);
  equal(registration.logs.some((record) => record.message === "platform.worker.started"), false);

  // The signal callback deliberately remains void: a failed shutdown log still rejects the same async task, without closing or retrying.
  const handlers = new Map<string, () => void>();
  Object.defineProperty(process, "once", { configurable: true, value: function (event: string, callback: () => void) { handlers.set(event, callback); return process; } });
  const signalSink = sink("platform.worker.shutdown"); let signalStops = 0;
  let signalProcess: Awaited<ReturnType<typeof startPlatformWorkerProcess>>;
  try { signalProcess = await startPlatformWorkerProcess({ apps: [app({ beforeStop() { signalStops++; } })], logger: signalSink.logger }); }
  finally { restoreOnce(); }
  if (!signalProcess.ok) throw new Error(signalProcess.error.code);
  const unhandled: unknown[] = []; const onUnhandled = (reason: unknown): void => { unhandled.push(reason); };
  process.on("unhandledRejection", onUnhandled);
  try {
    equal(handlers.get("SIGTERM")?.(), undefined); await nextTurn();
    deepEqual(unhandled, [source]); equal(signalStops, 0); equal(signalProcess.value.shell.lifecycle.state(), "ready");
    deepEqual(signalSink.observed, [worker("signal-shutdown", "shutdown-log", "invocation", "shutdown-not-completed"), records[0], ...records]);
    handlers.get("SIGINT")?.(); await nextTurn(); equal(signalSink.attempts(), 10); equal(signalStops, 0); deepEqual(unhandled, [source]);
  } finally { process.off("unhandledRejection", onUnhandled); }
  await signalProcess.value.close(); equal(signalStops, 1);
}
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
