import { deepEqual, equal, ok } from "node:assert/strict";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import { configError } from "@kanbien/core/config";
import { platformAppId, type PlatformApp, type PlatformDiagnosticContext, type PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createPlatformServerShell } from "../src/index";
import { serverDiagnosticRecord } from "../src/diagnostics";

const canary = "private-server-builtin-evidence-canary";
const checkedId = platformAppId("builtinevidence");
if (!checkedId.ok) throw new Error("Invalid fixture");
const id = checkedId.value;
const records = (["PLATFORM_SERVER_HANDLER_FAILED", "PLATFORM_SERVER_INVALID_REQUEST", "PLATFORM_SERVER_REQUEST_TIMEOUT",
  "PLATFORM_SERVER_UNSUPPORTED_MEDIA_TYPE", "PLATFORM_SERVER_PAYLOAD_TOO_LARGE", "PLATFORM_SERVER_FORBIDDEN",
  "PLATFORM_SERVER_UNAUTHENTICATED", "PLATFORM_SERVER_SERVICE_UNAVAILABLE"] as const).map((code) => serverDiagnosticRecord(code));
const source = Object.assign(new Error(canary), { diagnosticRecord: records[0], relatedDiagnosticRecords: records });
const own = (operation: "mount" | "start" | "shutdown") => ({ schema: "core/diagnostic-record/v1", code: "platform-runtime.boundary-failed", definitionVersion: 1,
  detail: { operation, phase: operation === "mount" ? "app-mount" : operation === "start" ? "app.beforeStart" : "app.beforeStop", subject: "app", boundary: "invocation",
    effect: "step-completion-unobserved", ordinal: 0 } });

async function main(): Promise<void> {
  for (const mode of ["default", "injected", "unavailable"] as const) for (const boundary of ["mount", "start", "shutdown", "configuration"] as const) {
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
    // No app or explicit diagnostic catalog: these records already belong to the selected Server builtins.
    const app: PlatformApp = { id, name: "Builtin evidence", mount(registry) {
      mounts++;
      if (boundary === "mount") throw source;
      if (boundary === "configuration") registry.registerConfigSchema({ parse: () => ({ ok: false, error: configError("CONFIG_INVALID", [{ path: [], code: "CONFIG_INVALID", defaultMessage: "Fixture rejected." }], {
        diagnosticRecord: records[0]!, relatedDiagnosticRecords: records,
      }) }) });
    }, lifecycle: { beforeStart() { starts++; if (boundary === "start") throw source; }, beforeStop() { stops++; if (boundary === "shutdown") throw source; } } };
    const mounted = await createPlatformServerShell({ apps: [app], deps: mode === "injected" ? { ...deps, diagnostics: reporter } : deps });
    let failure: { diagnosticRecord?: DiagnosticRecord; relatedDiagnosticRecords?: readonly DiagnosticRecord[] };
    if (boundary === "mount" || boundary === "configuration") {
      equal(mounted.ok, false); if (mounted.ok) throw new Error("Expected startup failure");
      equal(mounted.error.code, boundary === "mount" ? "PLATFORM_SERVER_MOUNT_FAILED" : "PLATFORM_SERVER_CONFIG_INVALID");
      failure = mounted.error;
    } else {
      ok(mounted.ok);
      const started = await mounted.value.lifecycle.start();
      if (boundary === "start") {
        equal(started.ok, false); if (started.ok) throw new Error("Expected lifecycle failure");
        equal(started.error.cause, source); failure = started.error;
      } else {
        ok(started.ok); const stopped = await mounted.value.lifecycle.shutdown();
        equal(stopped.ok, false); if (stopped.ok) throw new Error("Expected lifecycle failure");
        equal(stopped.error.cause, source); failure = stopped.error;
      }
    }
    deepEqual(failure.diagnosticRecord, records[0]); deepEqual(failure.relatedDiagnosticRecords, records);
    equal(failure.relatedDiagnosticRecords?.length, 8);
    const location = boundary === "configuration" ? { schema: "core/diagnostic-record/v1", code: "platform-config.schema-rejected", definitionVersion: 1,
      detail: { schemaIndex: 0, reason: "invalid" } } : own(boundary);
    const context = boundary === "configuration" ? { capability: "platform-config", operation: "validate-schema", stage: "configuration" }
      : { capability: "platform-runtime", operation: boundary, stage: boundary === "shutdown" ? "shutdown" : "startup" };
    deepEqual(observed, mode === "unavailable" ? [] : [location, records[0], ...records].map((record) => ({ record, context })));
    equal(attempts, 10); deepEqual([mounts, starts, stops], [1, boundary === "start" || boundary === "shutdown" ? 1 : 0, boundary === "shutdown" ? 1 : 0]);
    equal(JSON.stringify(logs).includes(canary), false);
  }
  let selections = 0;
  const healthy = await createPlatformServerShell({ apps: [], deps: createPlatformTestMountDeps(), get diagnosticCatalogs() { selections++; return []; } });
  ok(healthy.ok); equal(selections, 1, "Runtime/config selection stays lazy on the healthy path.");
  ok((await healthy.value.lifecycle.start()).ok); equal(selections, 1);
  ok((await healthy.value.lifecycle.shutdown()).ok); equal(selections, 1);
  console.log("Server builtin evidence survives mount, configuration and lifecycle without redundant catalog registration.");
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
