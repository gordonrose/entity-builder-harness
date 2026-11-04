import { deepEqual, equal, rejects } from "node:assert/strict";
import { setImmediate as nextTurn } from "node:timers/promises";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import { platformAppId, type PlatformApp, type PlatformDiagnosticContext, type PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createInMemoryPlatformWorkerQueue, createPlatformWorkerShell, type PlatformWorkerQueue } from "../src/index";

const secret = "worker-private-lifecycle-canary@example.invalid";
const checkedId = platformAppId("workerfixture"); if (!checkedId.ok) throw new Error("Invalid fixture");
const id = checkedId.value;
const definition = defineDiagnostic({ code: "workerfixture.upstream-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { index: { type: "integer", minimum: 0, maximum: 7 } } } });
const records = Array.from({ length: 8 }, (_, index) => { const checked = createDiagnosticRecord(definition, { index }); if (!checked.ok) throw new Error("Invalid fixture"); return checked.value; });
const source = Object.assign(new Error(secret), { diagnosticRecord: records[0], relatedDiagnosticRecords: records });
const literals = Array.from({ length: 8 }, (_, index) => ({ schema: "core/diagnostic-record/v1", code: "workerfixture.upstream-failed", definitionVersion: 1, detail: { index } }));
const runtime = (operation: string, phase: string, subject = "app", boundary = "invocation", effect = "step-completion-unobserved") => ({ schema: "core/diagnostic-record/v1", code: "platform-runtime.boundary-failed", definitionVersion: 1,
  detail: { operation, phase, subject, boundary, effect, ordinal: 0 } });
type Mode = "default" | "injected" | "unavailable" | "throws" | "rejects";
function sink(mode: Mode) {
  const observed: { record: unknown; context: unknown }[] = [], logs: LogRecord[] = []; let attempts = 0;
  const base = createPlatformTestMountDeps({ logger: { write(record) {
    if (record.message === "platform.diagnostic.observed") {
      attempts++; if (mode === "unavailable") throw source;
      observed.push({ record: record.fields?.["diagnostic"], context: { capability: record.fields?.["capability"], operation: record.fields?.["operation"], stage: record.fields?.["stage"] } });
    }
    logs.push(record);
  } } });
  const reporter = { report(record: DiagnosticRecord, context: PlatformDiagnosticContext) {
    attempts++; observed.push({ record, context }); if (mode === "throws") throw source;
    return mode === "rejects" ? Promise.reject(source) : { status: "written" };
  } } as unknown as PlatformDiagnosticReporter;
  return { deps: mode === "injected" || mode === "throws" || mode === "rejects" ? { ...base, diagnostics: reporter } : base, observed, logs, attempts: () => attempts };
}
function app(lifecycle: PlatformApp["lifecycle"] = {}, mountThrows = false): PlatformApp {
  return { id, name: secret, lifecycle, mount(registry) {
    equal(registry.registerDiagnosticCatalog({ owner: "workerfixture", definitions: [definition] }).ok, true);
    if (mountThrows) throw source;
  } };
}
function expectSeen(target: ReturnType<typeof sink>, mode: Mode, own: unknown, context: unknown): void {
  deepEqual(target.observed, mode === "unavailable" ? [] : [own, literals[0], ...literals].map((record) => ({ record, context })));
  equal(target.attempts(), 10); equal(JSON.stringify(target.logs).includes(secret), false);
}
async function main(): Promise<void> {
  const unhandled: unknown[] = []; const onUnhandled = (reason: unknown): void => { unhandled.push(reason); };
  process.on("unhandledRejection", onUnhandled);
  try {
    for (const mode of ["default", "injected", "unavailable", "throws", "rejects"] as const) {
      let queueReads = 0, hooks = 0;
      const mountSink = sink(mode);
      const mounted = await createPlatformWorkerShell({ apps: [app({}, true)], deps: mountSink.deps, get queue(): never { queueReads++; throw new Error("Must remain unused"); } });
      equal(mounted.ok, false); if (mounted.ok) throw new Error("Expected failure");
      equal(mounted.error.code, "PLATFORM_WORKER_MOUNT_FAILED"); equal(mounted.error.defaultMessage, "Platform worker failed to mount apps.");
      deepEqual(mounted.error.details, { runtimeCode: "PLATFORM_RUNTIME_APP_MOUNT_FAILED" });
      deepEqual(mounted.error.diagnosticRecord, literals[0]); deepEqual(mounted.error.relatedDiagnosticRecords, literals); equal(queueReads, 0);
      expectSeen(mountSink, mode, runtime("mount", "app-mount"), { capability: "platform-runtime", operation: "mount", stage: "startup" });

      const startSink = sink(mode);
      const shell = await createPlatformWorkerShell({ apps: [app({ beforeStart() { hooks++; throw source; } })], deps: startSink.deps });
      if (!shell.ok) throw new Error(shell.error.code);
      const started = await shell.value.start(); equal(started.ok, false); if (started.ok) throw new Error("Expected failure");
      equal(started.error.code, "PLATFORM_WORKER_NOT_READY"); equal(started.error.defaultMessage, "Platform worker lifecycle failed to start.");
      deepEqual(started.error.details, {}); equal((started.error.cause as { cause: unknown }).cause, source); equal(hooks, 1);
      deepEqual(started.error.diagnosticRecord, literals[0]); deepEqual(started.error.relatedDiagnosticRecords, literals);
      expectSeen(startSink, mode, runtime("start", "app.beforeStart"), { capability: "platform-runtime", operation: "start", stage: "startup" });

      const stopSink = sink(mode); let sequence = "";
      const queue = createInMemoryPlatformWorkerQueue(); const originalClose = queue.close;
      queue.close = function () { equal(this, queue); equal(arguments.length, 0); sequence += "queue"; originalClose(); };
      const stopShell = await createPlatformWorkerShell({ apps: [app({ beforeStop() { sequence += "hook"; throw source; } })], deps: stopSink.deps, queue });
      if (!stopShell.ok) throw new Error(stopShell.error.code); await stopShell.value.start();
      const stopped = await stopShell.value.shutdown(); equal(stopped.ok, false); if (stopped.ok) throw new Error("Expected failure");
      equal(sequence, "queuehook"); equal(queue.isClosed(), true); equal(stopShell.value.lifecycle.state(), "failed");
      equal(stopped.error.defaultMessage, "Platform worker lifecycle failed to shut down.");
      deepEqual(stopped.error.diagnosticRecord, literals[0]); deepEqual(stopped.error.relatedDiagnosticRecords, literals);
      expectSeen(stopSink, mode, runtime("shutdown", "app.beforeStop"), { capability: "platform-runtime", operation: "shutdown", stage: "shutdown" });

      for (const getter of [false, true]) {
        const closeSink = sink(mode); let closes = 0, reads = 0, stoppedHooks = 0;
        const q = createInMemoryPlatformWorkerQueue();
        Object.defineProperty(q, "close", { configurable: true, get() { reads++; if (getter) throw source; return function (this: PlatformWorkerQueue) { equal(this, q); equal(arguments.length, 0); closes++; throw source; }; } });
        const closeShell = await createPlatformWorkerShell({ apps: [app({ beforeStop() { stoppedHooks++; } })], deps: closeSink.deps, queue: q });
        if (!closeShell.ok) throw new Error(closeShell.error.code); await closeShell.value.start();
        await rejects(closeShell.value.shutdown(), (error) => error === source);
        deepEqual([reads, closes, stoppedHooks], [1, getter ? 0 : 1, 0]); equal(closeShell.value.lifecycle.state(), "ready");
        expectSeen(closeSink, mode, { schema: "core/diagnostic-record/v1", code: "platform-worker.boundary-failed", definitionVersion: 1,
          detail: { operation: "shutdown", phase: "queue-close", boundary: "selection-or-invocation", effect: "lifecycle-shutdown-not-invoked" } }, { capability: "platform-worker", operation: "shutdown", stage: "shutdown" });
      }
    }
    const malformed = [{ diagnosticRecord: { ...records[0], definitionVersion: 99 }, relatedDiagnosticRecords: records },
      { get diagnosticRecord(): never { throw new Error("No accessor read"); }, relatedDiagnosticRecords: records }];
    for (const bad of malformed) {
      const target = sink("injected");
      const shell = await createPlatformWorkerShell({ apps: [{ ...app(), lifecycle: { beforeStart() { throw bad; } } }], deps: target.deps });
      if (!shell.ok) throw new Error(shell.error.code); const result = await shell.value.start(); if (result.ok) throw new Error("Expected failure");
      deepEqual(result.error.diagnosticRecord, runtime("start", "app.beforeStart")); deepEqual(result.error.relatedDiagnosticRecords, literals);
      equal(target.observed.length, 9); equal((result.error.cause as { cause: unknown }).cause, bad);
    }
    const q = createInMemoryPlatformWorkerQueue(); Object.defineProperty(q, "close", { value: 42 });
    const shell = await createPlatformWorkerShell({ apps: [], deps: createPlatformTestMountDeps(), queue: q }); if (!shell.ok) throw new Error(shell.error.code);
    await rejects(shell.value.shutdown(), (error) => error instanceof TypeError && error.message === "queue.close is not a function");
    await nextTurn(); deepEqual(unhandled, []);
  } finally { process.off("unhandledRejection", onUnhandled); }
}
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
