import { deepEqual, equal, rejects } from "node:assert/strict";
import { setImmediate as nextTurn } from "node:timers/promises";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { configError, numberConfigValue, type ConfigSchema } from "@kanbien/core/config";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import { definePlatformApp, platformAppId, platformRouteName, type PlatformApp, type PlatformDiagnosticContext, type PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createPlatformWorkerShell, type PlatformWorkerDurableOutboxProcessingOptions } from "../src/index";

const canary = "synthetic-private-startup-canary";
const id = platformAppId("startupfixture"), route = platformRouteName("startupfixture.invalid");
if (!id.ok || !route.ok) throw new Error("fixture-invalid");
const appId = id.value, routeName = route.value;
const definition = defineDiagnostic({ code: "startupfixture.setting-rejected", version: 1,
  classification: { failureKind: "configuration", failureSource: "app", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { index: { type: "integer", minimum: 0, maximum: 7 }, reason: { type: "enum", values: ["invalid"] } } },
} as const);
const appRecords = Array.from({ length: 8 }, (_, index) => {
  const checked = createDiagnosticRecord(definition, { index, reason: "invalid" });
  if (!checked.ok) throw new Error("fixture-invalid");
  return checked.value;
});
const appLiterals = Array.from({ length: 8 }, (_, index) => ({ schema: "core/diagnostic-record/v1", code: "startupfixture.setting-rejected", definitionVersion: 1, detail: { index, reason: "invalid" } }));
const coreLiteral = { schema: "core/diagnostic-record/v1", code: "core.config.primitive-invalid", definitionVersion: 1, detail: { field: "value", reader: "number", reason: "wrong-type" } };
const positionLiteral = { schema: "core/diagnostic-record/v1", code: "platform-config.schema-rejected", definitionVersion: 1, detail: { schemaIndex: 1, reason: "invalid" } };
const parseLiteral = { schema: "core/diagnostic-record/v1", code: "platform-config.schema-boundary-threw", definitionVersion: 1,
  detail: { schemaIndex: 1, phase: "parse", reason: "boundary-threw", effect: "result-not-returned" } };
const sourceLiteral = { schema: "core/diagnostic-record/v1", code: "core.config.source-threw", definitionVersion: 1, detail: { reader: "number", phase: "source-read", reason: "invocation-threw" } };
const configContext = { capability: "platform-config", operation: "validate-schema", stage: "configuration" } as const;
type Mode = "default" | "injected" | "unavailable" | "async-rejecting" | "injected-throws";
interface Observation { readonly record: unknown; readonly context: unknown }
const usesInjected = (mode: Mode) => mode === "injected" || mode === "async-rejecting" || mode === "injected-throws";

function delivery(mode: Mode) {
  const logs: LogRecord[] = [], observations: Observation[] = [];
  let attempts = 0;
  const base = createPlatformTestMountDeps({ logger: { write(log) {
    if (log.message === "platform.diagnostic.observed") {
      attempts++;
      if (mode === "unavailable") throw new Error(canary);
      observations.push({ record: log.fields?.["diagnostic"], context: { capability: log.fields?.["capability"], operation: log.fields?.["operation"], stage: log.fields?.["stage"] } });
    }
    logs.push(log);
  } } });
  const reporter = { report(record: DiagnosticRecord, context: PlatformDiagnosticContext) {
    attempts++;
    observations.push({ record, context });
    if (mode === "injected-throws") throw new Error(canary);
    return mode === "async-rejecting" ? Promise.reject(new Error(canary)) : { status: "written" as const };
  } } as unknown as PlatformDiagnosticReporter;
  const deps = usesInjected(mode) ? { ...base, diagnostics: reporter } : base;
  return { deps, observations, logs, attempts: () => attempts };
}
function expectObserved(target: ReturnType<typeof delivery>, mode: Mode, records: readonly unknown[], context: unknown = configContext): void {
  deepEqual(target.observations, mode === "unavailable" ? [] : records.map((record) => ({ record, context })));
  equal(target.attempts(), records.length);
  equal(JSON.stringify(target.logs).includes(canary), false);
}
function app(schemas: readonly ConfigSchema<unknown>[], state: { mounts: number; lifecycle: number }): PlatformApp {
  return definePlatformApp({ id: appId, name: "Startup fixture", lifecycle: { beforeStart() { state.lifecycle++; } }, mount(registry) {
    state.mounts++;
    registry.registerDiagnosticCatalog({ owner: "startupfixture", definitions: [definition] });
    for (const schema of schemas) registry.registerConfigSchema(schema);
  } });
}

async function main(): Promise<void> {
  const unhandled: unknown[] = [];
  const observeUnhandled = (reason: unknown): void => { unhandled.push(reason); };
  process.on("unhandledRejection", observeUnhandled);
  try {
    for (const mode of ["default", "injected", "unavailable", "async-rejecting", "injected-throws"] as const) {
      const sink = delivery(mode), state = { mounts: 0, lifecycle: 0 };
      let first = 0, reads = 0, later = 0, queueReads = 0;
      const schema: ConfigSchema<unknown> = { parse(source) {
        const parsed = numberConfigValue(source, "PRIVATE_SETTING");
        if (parsed.ok) throw new Error("Expected invalid fixture value.");
        return { ok: false, error: configError(parsed.error.code, parsed.error.issues, { diagnosticRecord: parsed.error.diagnosticRecord!, relatedDiagnosticRecords: appRecords }) };
      } };
      const result = await createPlatformWorkerShell({ apps: [app([
        { parse() { first++; return { ok: true, value: "first" }; } }, schema,
        { parse() { later++; return { ok: true, value: "later" }; } },
      ], state)], deps: { ...sink.deps, config: { get() { reads++; return canary; } } }, get queue(): never { queueReads++; throw new Error("Queue must remain unused."); } });
      equal(result.ok, false);
      if (result.ok) throw new Error("Expected configuration rejection.");
      equal(result.error.code, "PLATFORM_WORKER_CONFIG_INVALID");
      equal(result.error.defaultMessage, "Platform worker config validation failed before polling.");
      deepEqual(result.error.diagnosticRecord, coreLiteral);
      deepEqual(result.error.relatedDiagnosticRecords, appLiterals);
      deepEqual(result.error.details, { schemaIndex: 1, configCode: "CONFIG_INVALID", issues: [{ path: ["config", "PRIVATE_SETTING"], code: "CONFIG_INVALID_TYPE", defaultMessage: "Config value has the wrong type.", messageKey: "config.invalid_type" }] });
      deepEqual([first, reads, later, queueReads, state.mounts, state.lifecycle], [1, 1, 0, 0, 1, 0]);
      expectObserved(sink, mode, [positionLiteral, coreLiteral, ...appLiterals]);
      equal(JSON.stringify(result.error.details).includes("diagnostic"), false);
      equal(JSON.stringify(result.error.details).includes(canary), false);

      for (const kind of ["schema", "source", "frozen", "primitive"] as const) {
        const thrown = kind === "schema" ? Object.assign(new Error(canary), { diagnosticRecord: appRecords[0] })
          : kind === "frozen" ? Object.freeze(new Error(canary)) : kind === "primitive" ? canary : new Error(canary);
        const thrownSink = delivery(mode), thrownState = { mounts: 0, lifecycle: 0 };
        let sourceReads = 0, schemaCalls = 0, skipped = 0, queueReads = 0;
        const throwingSchema: ConfigSchema<unknown> = { parse(source) { schemaCalls++; if (kind === "source") return numberConfigValue(source, "PRIVATE_SETTING"); throw thrown; } };
        await rejects(createPlatformWorkerShell({ apps: [app([{ parse: () => ({ ok: true, value: null }) }, throwingSchema, { parse() { skipped++; return { ok: true, value: null }; } }], thrownState)],
          deps: { ...thrownSink.deps, config: { get() { sourceReads++; throw thrown; } } }, get queue(): never { queueReads++; throw new Error("Queue must remain unused."); } }), (error: unknown) => error === thrown);
        expectObserved(thrownSink, mode, [parseLiteral, ...(kind === "schema" ? [appLiterals[0]] : kind === "source" ? [sourceLiteral] : [])]);
        deepEqual([sourceReads, schemaCalls, skipped, queueReads, thrownState.lifecycle], [kind === "source" ? 1 : 0, 1, 0, 0, 0]);
      }

      const mountSink = delivery(mode);
      let mountCalls = 0, lifecycleCalls = 0, schemaCalls = 0, mountQueueReads = 0;
      const badMount = await createPlatformWorkerShell({ deps: mountSink.deps, get queue(): never { mountQueueReads++; throw new Error("Queue must remain unused."); }, apps: [definePlatformApp({ id: appId, name: "Rejected registration", lifecycle: { beforeStart() { lifecycleCalls++; } }, mount(registry) {
        mountCalls++;
        registry.registerRoute({ name: routeName, method: "GET", path: canary, auth: { kind: "public" }, observability: { kind: "opt_out", reason: "non_user_workload_path", justification: "Startup registration fixture." }, handler: { handle: () => ({ status: 200 }) } });
        registry.registerConfigSchema({ parse() { schemaCalls++; return { ok: true, value: null }; } });
      } })] });
      equal(badMount.ok, false);
      if (!badMount.ok) {
        equal(badMount.error.code, "PLATFORM_WORKER_MOUNT_FAILED");
        deepEqual(badMount.error.details, { runtimeCode: "PLATFORM_RUNTIME_REGISTRY_INVALID" });
      }
      deepEqual([mountCalls, lifecycleCalls, schemaCalls, mountQueueReads], [1, 0, 0, 0]);
      expectObserved(mountSink, mode, [{ schema: "core/diagnostic-record/v1", code: "platform-contracts.registration-rejected", definitionVersion: 1,
        detail: { registration: "route", field: "path", condition: "path-not-absolute", phase: "validation", effect: "rejected" } }], { capability: "platform-contracts", operation: "register", stage: "configuration" });

      for (const [value, reason, expectedReads] of [[undefined, "missing", 1], [canary, "wrong-type", 1], [null, "wrong-type", 1], [NaN, "not-finite", 1], [Infinity, "not-finite", 1], [-Infinity, "not-finite", 1], [1.5, "invalid-integer", 1], [0, "not-positive", 1], [-1, "not-positive", 1]] as const) {
        const leaseSink = delivery(mode), leaseState = { mounts: 0, lifecycle: 0 };
        let leaseReads = 0, rejectedQueueReads = 0, storeReads = 0;
        const processing = { get leaseDurationMs() { leaseReads++; return value; }, get processingStore() { storeReads++; throw new Error("Store must remain unused."); } } as unknown as PlatformWorkerDurableOutboxProcessingOptions;
        const rejected = await createPlatformWorkerShell({ deps: leaseSink.deps, apps: [app([], leaseState)], durableOutboxProcessing: processing,
          get queue(): never { rejectedQueueReads++; throw new Error("Queue must remain unused."); } });
        const literal = { schema: "core/diagnostic-record/v1", code: "platform-worker.configuration-invalid", definitionVersion: 1, detail: { issues: [{ setting: "durable-lease-duration", reason }] } };
        deepEqual(rejected, { ok: false, error: { code: "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED", defaultMessage: "Durable outbox processing requires a positive lease duration.", details: { phase: "configuration" }, diagnosticRecord: literal } });
        deepEqual([leaseReads, rejectedQueueReads, storeReads, leaseState.mounts, leaseState.lifecycle], [expectedReads, 0, 0, 1, 0]);
        expectObserved(leaseSink, mode, [literal], { capability: "platform-worker", operation: "configure", stage: "configuration" });
      }
      const changingSink = delivery(mode);
      let changingReads = 0;
      const changing = await createPlatformWorkerShell({ deps: changingSink.deps, apps: [],
        durableOutboxProcessing: { get leaseDurationMs() { if (++changingReads > 1) throw new Error("Duration must not be re-read"); return 1; } } as PlatformWorkerDurableOutboxProcessingOptions });
      equal(changing.ok, true); equal(changingReads, 1);
      expectObserved(changingSink, mode, []);

      const healthySink = delivery(mode), healthyState = { mounts: 0, lifecycle: 0 };
      let healthyReads = 0;
      const healthy = await createPlatformWorkerShell({ apps: [app([{ parse(source) { healthyReads++; return numberConfigValue(source, "PRIVATE_SETTING"); } }], healthyState)], deps: { ...healthySink.deps, config: { get: () => 0 } } });
      equal(healthy.ok, true);
      deepEqual([healthyReads, healthyState.mounts, healthyState.lifecycle], [1, 1, 0]);
      expectObserved(healthySink, mode, []);
      const conflictSink = delivery(mode), coreApp = platformAppId("core");
      if (!coreApp.ok) throw new Error("fixture-invalid");
      let conflictLifecycle = 0;
      const conflict = await createPlatformWorkerShell({ deps: conflictSink.deps, apps: [definePlatformApp({ id: coreApp.value, name: "Conflicting catalog fixture", lifecycle: { beforeStart() { conflictLifecycle++; } }, mount(registry) { registry.registerDiagnosticCatalog(coreDiagnosticCatalog); } })] });
      equal(conflict.ok, usesInjected(mode), "injected reporters retain existing catalog-validation precedence");
      if (!conflict.ok) {
        equal(conflict.error.code, "PLATFORM_WORKER_MOUNT_FAILED");
        equal(conflict.error.defaultMessage, "Platform worker diagnostic catalog selection is invalid.");
      }
      equal(conflictLifecycle, 0);
      expectObserved(conflictSink, mode, usesInjected(mode) ? [] : [{ schema: "core/diagnostic-record/v1", code: "platform-contracts.registration-rejected", definitionVersion: 1,
        detail: { registration: "diagnostic-catalog", field: "owner", condition: "duplicate-owner", phase: "conflicts", effect: "rejected" } }], { capability: "platform-contracts", operation: "select-diagnostic-catalog", stage: "configuration" });

      const combinedSink = delivery(mode);
      const customDefinition = defineDiagnostic({ ...definition, code: "core.fixture.setting-rejected" });
      const customRecords = Array.from({ length: 8 }, (_, index) => {
        const checked = createDiagnosticRecord(customDefinition, { index, reason: "invalid" });
        if (!checked.ok) throw new Error("fixture-invalid");
        return checked.value;
      });
      const customLiterals = appLiterals.map((record) => ({ ...record, code: "core.fixture.setting-rejected" }));
      let combinedReads = 0, combinedQueueReads = 0, combinedLifecycle = 0;
      const combined = await createPlatformWorkerShell({ deps: { ...combinedSink.deps, config: { get() { combinedReads++; return canary; } } },
        get queue(): never { combinedQueueReads++; throw new Error("Queue must remain unused."); }, apps: [definePlatformApp({ id: coreApp.value, name: "Combined configuration and catalog rejection", lifecycle: { beforeStart() { combinedLifecycle++; } }, mount(registry) {
          registry.registerDiagnosticCatalog(coreDiagnosticCatalog);
          registry.registerDiagnosticCatalog({ owner: "core.fixture", definitions: [customDefinition] });
          registry.registerConfigSchema({ parse: () => ({ ok: true, value: null }) });
          registry.registerConfigSchema({ parse(source) {
            const parsed = numberConfigValue(source, "PRIVATE_SETTING");
            if (parsed.ok) throw new Error("Expected invalid fixture value.");
            return { ok: false, error: configError(parsed.error.code, parsed.error.issues, { diagnosticRecord: parsed.error.diagnosticRecord!, relatedDiagnosticRecords: customRecords }) };
          } });
        } })] });
      equal(combined.ok, false);
      if (combined.ok) throw new Error("Expected original configuration failure precedence.");
      equal(combined.error.code, "PLATFORM_WORKER_CONFIG_INVALID");
      deepEqual(combined.error.diagnosticRecord, coreLiteral);
      deepEqual(combined.error.relatedDiagnosticRecords, customLiterals, "selected custom evidence remains in the internal result even when fallback delivery cannot select it");
      deepEqual([combinedReads, combinedQueueReads, combinedLifecycle], [1, 0, 0]);
      const catalogConflictLiteral = { schema: "core/diagnostic-record/v1", code: "platform-contracts.registration-rejected", definitionVersion: 1,
        detail: { registration: "diagnostic-catalog", field: "owner", condition: "duplicate-owner", phase: "conflicts", effect: "rejected" } };
      const conflictContext = { capability: "platform-contracts", operation: "select-diagnostic-catalog", stage: "configuration" };
      const injected = usesInjected(mode);
      deepEqual(combinedSink.observations, mode === "unavailable" ? [] : injected
        ? [positionLiteral, coreLiteral, ...customLiterals].map((record) => ({ record, context: configContext }))
        : [{ record: catalogConflictLiteral, context: conflictContext }, ...[positionLiteral, coreLiteral].map((record) => ({ record, context: configContext }))]);
      equal(combinedSink.attempts(), injected ? 10 : 3, "fallback reports the catalog conflict once and never claims custom records were delivered");
      equal(JSON.stringify(combinedSink.logs).includes(canary), false);
      await nextTurn();
      deepEqual(unhandled, [], "async rejecting reporters are observed without unhandled rejection");
    }
  } finally { process.off("unhandledRejection", observeUnhandled); }
  console.log("Worker startup retains exact configuration/contract evidence and lease getter counts before queue/lifecycle across optional reporter failures.");
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
