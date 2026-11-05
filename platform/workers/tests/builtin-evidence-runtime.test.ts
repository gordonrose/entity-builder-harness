import { deepEqual, equal, ok } from "node:assert/strict";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import { platformAppId, type PlatformApp, type PlatformDiagnosticContext, type PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createPlatformWorkerShell } from "../src/index";
import { workerDiagnosticRecord } from "../src/diagnostics";

const canary = "private-worker-builtin-evidence-canary";
const checkedId = platformAppId("builtinevidence");
if (!checkedId.ok) throw new Error("Invalid fixture");
const id = checkedId.value;
const records = (["PLATFORM_WORKER_HANDLER_FAILED", "PLATFORM_WORKER_INVALID_PAYLOAD", "PLATFORM_WORKER_QUEUE_CLOSED",
  "PLATFORM_WORKER_NOT_READY", "PLATFORM_WORKER_JOB_NOT_FOUND", "PLATFORM_WORKER_DURABLE_PROCESSING_BUSY",
  "PLATFORM_WORKER_IDEMPOTENCY_FAILED", "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED"] as const).map((code) => workerDiagnosticRecord(code));
const source = Object.assign(new Error(canary), { diagnosticRecord: records[0], relatedDiagnosticRecords: records });
const own = (operation: "mount" | "start" | "shutdown") => ({ schema: "core/diagnostic-record/v1", code: "platform-runtime.boundary-failed", definitionVersion: 1,
  detail: { operation, phase: operation === "mount" ? "app-mount" : operation === "start" ? "app.beforeStart" : "app.beforeStop", subject: "app", boundary: "invocation",
    effect: "step-completion-unobserved", ordinal: 0 } });

async function main(): Promise<void> {
  for (const mode of ["default", "injected", "unavailable"] as const) for (const boundary of ["mount", "start", "shutdown"] as const) {
    const observed: { record: unknown; context: unknown }[] = [], logs: LogRecord[] = [];
    let attempts = 0, mounts = 0, starts = 0, stops = 0;
    const deps = createPlatformTestMountDeps({ logger: { write(log) {
      if (log.message === "platform.diagnostic.observed") {
        attempts++;
        if (mode === "unavailable") throw source;
        observed.push({ record: log.fields?.["diagnostic"], context: { capability: log.fields?.["capability"], operation: log.fields?.["operation"], stage: log.fields?.["stage"] } });
      }
      logs.push(log);
    } } });
    const reporter: PlatformDiagnosticReporter = { report(record: DiagnosticRecord, context: PlatformDiagnosticContext) {
      attempts++; observed.push({ record, context }); return { status: "written" };
    } };
    // No app or explicit diagnostic catalog: the Worker selects this vocabulary itself.
    const app: PlatformApp = { id, name: "Builtin evidence", mount() { mounts++; if (boundary === "mount") throw source; },
      lifecycle: { beforeStart() { starts++; if (boundary === "start") throw source; }, beforeStop() { stops++; if (boundary === "shutdown") throw source; } } };
    const mounted = await createPlatformWorkerShell({ apps: [app], deps: mode === "injected" ? { ...deps, diagnostics: reporter } : deps });
    let failure: { diagnosticRecord?: DiagnosticRecord; relatedDiagnosticRecords?: readonly DiagnosticRecord[] };
    if (boundary === "mount") {
      equal(mounted.ok, false); if (mounted.ok) throw new Error("Expected mount failure");
      equal(mounted.error.code, "PLATFORM_WORKER_MOUNT_FAILED"); failure = mounted.error;
    } else {
      ok(mounted.ok); const started = await mounted.value.start();
      if (boundary === "start") {
        equal(started.ok, false); if (started.ok) throw new Error("Expected lifecycle failure");
        equal(started.error.code, "PLATFORM_WORKER_NOT_READY"); failure = started.error;
      } else {
        ok(started.ok); const stopped = await mounted.value.shutdown();
        equal(stopped.ok, false); if (stopped.ok) throw new Error("Expected lifecycle failure");
        equal(stopped.error.code, "PLATFORM_WORKER_NOT_READY"); failure = stopped.error;
      }
    }
    deepEqual(failure.diagnosticRecord, records[0]); deepEqual(failure.relatedDiagnosticRecords, records);
    equal(failure.relatedDiagnosticRecords?.length, 8);
    const context = { capability: "platform-runtime", operation: boundary, stage: boundary === "shutdown" ? "shutdown" : "startup" };
    deepEqual(observed, mode === "unavailable" ? [] : [own(boundary), records[0], ...records].map((record) => ({ record, context })));
    equal(attempts, 10); deepEqual([mounts, starts, stops], [1, boundary === "mount" ? 0 : 1, boundary === "shutdown" ? 1 : 0]);
    equal(JSON.stringify(logs).includes(canary), false);
  }
  let selections = 0;
  const healthy = await createPlatformWorkerShell({ apps: [], deps: createPlatformTestMountDeps(), get diagnosticCatalogs() { selections++; return []; } });
  // The existing shell reads once for reporter selection and once when copying options with its reporter.
  ok(healthy.ok); equal(selections, 2, "Runtime/config selection adds no healthy-path catalog read.");
  ok((await healthy.value.start()).ok); equal(selections, 2);
  ok((await healthy.value.shutdown()).ok); equal(selections, 2);
  console.log("Worker builtin evidence survives mount and lifecycle without redundant catalog registration.");
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
