import { deepEqual, equal, ok, rejects } from "node:assert/strict";
import type { LogRecord } from "@kanbien/core/logging";
import { definePlatformApp, platformAppId } from "@kanbien/platform-contracts";
import { startPlatformServerProcess } from "../src/main";
import type { Server } from "node:http";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";

const canary = "synthetic-private-process-boundary";
const observations = (logs: readonly LogRecord[]) => logs.filter((record) => record.message === "platform.diagnostic.observed")
  .map((record) => record.fields?.["diagnostic"] as { code: string; detail: Record<string, unknown> });

async function selectionAndRegistrationBoundaries(): Promise<void> {
  const http = require("node:http") as typeof import("node:http");
  const originalCreateServer = http.createServer;
  const originalOnce = process.once;
  const originalOnceDescriptor = Object.getOwnPropertyDescriptor(process, "once");
  const failure = Object.freeze(new Error(canary));
  for (const mode of ["logger-getter", "first-once-getter", "second-once-getter", "second-registration"] as const) {
    let server: Server | undefined;
    let stopped = 0, onceSelections = 0, startupInvocations = 0;
    let loggerRejected = false;
    const logs: LogRecord[] = [], registrations: { signal: string | symbol; listener: (...args: unknown[]) => void }[] = [];
    const baselineTerm = process.listenerCount("SIGTERM"), baselineInt = process.listenerCount("SIGINT");
    const id = platformAppId("process-selection");
    ok(id.ok);
    http.createServer = ((...args: Parameters<typeof originalCreateServer>) => {
      server = Reflect.apply(originalCreateServer, http, args) as Server;
      return server;
    }) as typeof originalCreateServer;
    const logger = {
      get write() {
        if (mode === "logger-getter" && server?.listening && !loggerRejected) {
          loggerRejected = true;
          throw failure;
        }
        return (record: LogRecord) => {
          if (record.message === "platform.server.started") startupInvocations++;
          logs.push(record);
        };
      },
    };
    if (mode !== "logger-getter") {
      Object.defineProperty(process, "once", { configurable: true, get() {
        if (server?.listening) {
          onceSelections++;
          if (mode === "first-once-getter" || mode === "second-once-getter" && onceSelections === 2) throw failure;
        }
        return function (this: NodeJS.Process, signal: string | symbol, listener: (...args: unknown[]) => void) {
          if (signal === "SIGTERM" || signal === "SIGINT") {
            registrations.push({ signal, listener });
            if (mode === "second-registration" && signal === "SIGINT") throw failure;
          }
          return Reflect.apply(originalOnce, this, [signal, listener]);
        };
      } });
    }
    try {
      await rejects(startPlatformServerProcess({ env: {}, host: "127.0.0.1", port: 0, installSignalHandlers: mode !== "logger-getter", logger,
        apps: [definePlatformApp({ id: id.value, name: "Selection boundary", mount() {}, lifecycle: { beforeStop() { stopped++; } } })],
      }), (error) => error === failure);
      equal(server?.listening, true, "The failure after listening does not introduce automatic cleanup.");
      equal(stopped, 0); equal(startupInvocations, 0, "A failed logger getter does not prove logger invocation.");
      const own = observations(logs).filter((record) => record.code === "platform-server.process-boundary-failed");
      deepEqual(own.map((record) => record.detail), [{ phase: mode === "logger-getter" ? "startup-log" : "signal-registration",
        reason: "boundary-threw", effect: "process-not-returned" }]);
      if (mode === "first-once-getter") {
        deepEqual(registrations, []); equal(onceSelections, 1);
      } else if (mode === "second-once-getter") {
        deepEqual(registrations.map((entry) => entry.signal), ["SIGTERM"]); equal(onceSelections, 2);
      } else if (mode === "second-registration") {
        deepEqual(registrations.map((entry) => entry.signal), ["SIGTERM", "SIGINT"]); equal(onceSelections, 2);
      }
      equal(process.listenerCount("SIGTERM"), baselineTerm + (mode === "second-once-getter" || mode === "second-registration" ? 1 : 0));
      equal(process.listenerCount("SIGINT"), baselineInt, "Failed second registration leaves only the already-installed SIGTERM listener.");
      equal(JSON.stringify(logs).includes(canary), false);
    } finally {
      http.createServer = originalCreateServer;
      if (originalOnceDescriptor === undefined) Reflect.deleteProperty(process, "once");
      else Object.defineProperty(process, "once", originalOnceDescriptor);
      for (const { signal, listener } of registrations) process.removeListener(signal, listener);
      if (server?.listening) await new Promise<void>((resolve, reject) => server!.close((error) => error ? reject(error) : resolve()));
    }
    equal(process.listenerCount("SIGTERM"), baselineTerm); equal(process.listenerCount("SIGINT"), baselineInt);
  }
}

async function listenEvidencePreservation(): Promise<void> {
  const shellModule = require("../src/index.js") as { createPlatformServerShell: typeof import("../src/index").createPlatformServerShell };
  const original = shellModule.createPlatformServerShell;
  const builtin = coreDiagnosticCatalog.definitions.find(item => item.code === "core.shared.date-invalid")!;
  const appDefinition = defineDiagnostic({ code: "fixture.listen.failure", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "integer", minimum: 0, maximum: 8 } } as const);
  const appCatalog = { owner: "fixture", definitions: [appDefinition] };
  try {
    for (const mode of ["normal", "mounted-unavailable", "explicit-unavailable", "both-unavailable"] as const) {
      const checked = createDiagnosticRecord(mode === "both-unavailable" ? builtin : appDefinition,
        mode === "both-unavailable" ? { reason: "invalid-format" } : 0);
      ok(checked.ok);
      const primary = checked.value;
      const companions: DiagnosticRecord[] = Array.from({ length: 8 }, () => primary);
      const cause = Object.freeze(Object.assign(Error(canary), { diagnosticRecord: primary, relatedDiagnosticRecords: companions }));
      const order: string[] = [], logs: LogRecord[] = [];
      shellModule.createPlatformServerShell = async () => ({ ok: true, value: {
        mounted: { get diagnosticCatalogs() {
          if (mode === "mounted-unavailable" || mode === "both-unavailable") throw Error(canary);
          return [appCatalog];
        } },
        lifecycle: { async start() { order.push("start"); return { ok: true, value: undefined }; },
          async shutdown() { order.push("shutdown"); return { ok: true, value: undefined }; } },
        async listen() { order.push("listen"); throw cause; },
      } as never });
      let selections = 0;
      const result = await startPlatformServerProcess({ env: {}, installSignalHandlers: false,
        logger: { write(record) { logs.push(record); } },
        get diagnosticCatalogs() {
          if (++selections > 2 && (mode === "explicit-unavailable" || mode === "both-unavailable")) throw Error(canary);
          return [appCatalog];
        },
      });
      ok(!result.ok);
      equal(result.error.code, "PLATFORM_SERVER_START_FAILED"); equal(result.error.status, 500);
      deepEqual(result.error.diagnosticRecord, primary); deepEqual(result.error.relatedDiagnosticRecords, companions);
      deepEqual(order, ["start", "listen", "shutdown"]); equal(selections, 3);
      const processing = observations(logs).filter(record => record.code === "core.diagnostics.processing-failed");
      deepEqual(processing.map(record => record.detail), Array.from({ length: mode === "normal" ? 0 : mode === "both-unavailable" ? 2 : 1 },
        () => ({ reason: "definition-selection-failed" })));
      equal(JSON.stringify([result, logs]).includes(canary), false);
    }
  } finally { shellModule.createPlatformServerShell = original; }
}

async function main() {
  const id = platformAppId("process-boundary");
  ok(id.ok);
  const logs: LogRecord[] = [];
  let stopped = 0;
  const failure = Object.freeze(new Error(canary));
  const started = await startPlatformServerProcess({ env: {}, host: "127.0.0.1", port: 0, installSignalHandlers: false,
    logger: { write(record) { logs.push(record); } },
    apps: [definePlatformApp({ id: id.value, name: "Process boundary", mount() {}, lifecycle: { beforeStop() { stopped++; throw failure; } } })],
  });
  ok(started.ok);
  await started.value.close();
  equal(stopped, 1);
  equal(started.value.shell.lifecycle.state(), "failed");
  const shutdown = observations(logs).filter((record) => record.code === "platform-runtime.boundary-failed");
  deepEqual(shutdown.map((record) => record.detail), [{
    operation: "shutdown", phase: "app.beforeStop", subject: "app", boundary: "invocation",
    effect: "step-completion-unobserved", ordinal: 0,
  }], "ignored unsuccessful shutdown Result is still observed once");
  equal(JSON.stringify(logs).includes(canary), false);

  const http = require("node:http") as typeof import("node:http");
  const original = http.createServer;
  let server: Server | undefined;
  http.createServer = ((...args: Parameters<typeof original>) => {
    server = Reflect.apply(original, http, args) as Server;
    return server;
  }) as typeof original;
  const lateLogs: LogRecord[] = [];
  try {
    await rejects(startPlatformServerProcess({ env: {}, host: "127.0.0.1", port: 0, installSignalHandlers: false,
      logger: { write(record) {
        if (record.message === "platform.server.started") throw failure;
        lateLogs.push(record);
      } },
    }), (error: unknown) => error === failure);
    ok(server?.listening, "startup-log failure retains the original already-listening effect; no new cleanup policy");
    const own = observations(lateLogs).filter((record) => record.code === "platform-server.process-boundary-failed");
    deepEqual(own.map((record) => record.detail), [{ phase: "startup-log", reason: "boundary-threw", effect: "process-not-returned" }]);
    equal(JSON.stringify(lateLogs).includes(canary), false);
  } finally {
    http.createServer = original;
    if (server?.listening) await new Promise<void>((resolve, reject) => server!.close((error) => error ? reject(error) : resolve()));
  }
  await selectionAndRegistrationBoundaries();
  await listenEvidencePreservation();
  console.log("Server process shutdown, logger selection and partial signal registration preserve effects and throw identity.");
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
