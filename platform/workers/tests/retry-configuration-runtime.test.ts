import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import { setImmediate as nextTurn } from "node:timers/promises";
import type { Result } from "@kanbien/core/shared";
import { parseDiagnosticRecord, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { queueIdempotencyKey, type QueueMessageType } from "@kanbien/core/queues";
import { platformAppId, platformJobName, platformCapabilityName, platformObservabilityProfileName, type PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps, createPlatformTestQueueMessage } from "@kanbien/platform-testing";
import { createInMemoryPlatformProcessingStore, platformPersistenceLeaseOwner, validatePersistenceLeaseDuration } from "@kanbien/platform-persistence";
import { createPlatformWorkerShell, createInMemoryPlatformWorkerQueue, validateWorkerRetryConfiguration, validateWorkerRetryDelay,
  workerRetryConfigurationDiagnostic, workerRetryDelayDiagnostic, type PlatformWorkerShellOptions, type WorkerRetryConfigurationInput } from "../src/index";

function accepted<T>(result: Result<T, unknown>): T { if (!result.ok) throw new Error("Invalid fixture"); return result.value; }
const canary = "private-retry-canary";
const startup = (issues: readonly { setting: string; reason: string }[]) => ({ schema: "core/diagnostic-record/v1", code: "platform-worker.retry-configuration-invalid", definitionVersion: 1,
  detail: { operation: "configure-worker", phase: "configuration", issues, effect: "worker-not-created" } });
const delayPacket = (reason: string) => ({ schema: "core/diagnostic-record/v1", code: "platform-worker.retry-delay-invalid", definitionVersion: 1,
  detail: { operation: "job-delivery", phase: "backoff", setting: "retry-delay", reason, effect: "retry-not-submitted" } });
const id = accepted(platformAppId("retryfixture")), name = accepted(platformJobName("retryfixture.execute"));
const profile = accepted(platformObservabilityProfileName("retryfixture.execute")), capability = accepted(platformCapabilityName("retryfixture.execute"));
const type = "retryfixture.execute" as QueueMessageType;

async function main() {
  for (const [value, reason] of [[null, "wrong-type"], [canary, "wrong-type"], [false, "wrong-type"], [NaN, "not-finite"], [Infinity, "not-finite"], [-Infinity, "not-finite"], [0.5, "invalid-integer"], [0, "not-positive"], [-1, "not-positive"]] as const) {
    const input = { maxAttempts: value } as unknown as WorkerRetryConfigurationInput;
    const expected = startup([{ setting: "max-attempts", reason }]);
    deepEqual(validateWorkerRetryConfiguration(input), { ok: false, error: { diagnosticRecord: expected } });
    let queueReads = 0; const observed: unknown[] = [];
    const result = await createPlatformWorkerShell({ apps: [], deps: { ...createPlatformTestMountDeps(), diagnostics: { report(record, context) { observed.push({ record, context }); throw new Error(canary); } } }, ...input,
      get queue(): never { queueReads++; throw new Error("Queue must remain unused"); } });
    equal(result.ok, false); if (result.ok) throw new Error("Expected rejection");
    equal(result.error.code, "PLATFORM_WORKER_CONFIG_INVALID"); deepEqual(result.error.diagnosticRecord, expected); equal(queueReads, 0);
    deepEqual(observed, [{ record: expected, context: { capability: "platform-worker", operation: "configure", stage: "configuration" } }]);
    equal(JSON.stringify(result).includes(canary), false);
  }
  for (const value of [null, false, 1, canary, {}]) {
    deepEqual(validateWorkerRetryConfiguration({ retryBackoffMs: value } as unknown as WorkerRetryConfigurationInput),
      { ok: false, error: { diagnosticRecord: startup([{ setting: "retry-delay-calculator", reason: "not-callable" }]) } });
  }
  deepEqual(validateWorkerRetryConfiguration({ maxAttempts: 0, retryBackoffMs: null } as unknown as WorkerRetryConfigurationInput),
    { ok: false, error: { diagnosticRecord: startup([{ setting: "max-attempts", reason: "not-positive" }, { setting: "retry-delay-calculator", reason: "not-callable" }]) } });
  const defaults = accepted(validateWorkerRetryConfiguration({})); equal(defaults.maxAttempts, 3); equal(defaults.retryBackoffMs(1), 1000); equal(defaults.retryBackoffMs(2), 2000);
  for (const value of [1, 2, 3, Number.MAX_SAFE_INTEGER]) equal(accepted(validateWorkerRetryConfiguration({ maxAttempts: value })).maxAttempts, value);
  for (const value of [0, -0, 0.5, 25, Number.MAX_VALUE]) equal(accepted(validateWorkerRetryDelay(value)), value);
  const raw = Object.freeze(new Error(canary));
  throws(() => validateWorkerRetryConfiguration({ get maxAttempts(): never { throw raw; } }), error => error === raw);
  await rejects(createPlatformWorkerShell({ apps: [], deps: createPlatformTestMountDeps(), get retryBackoffMs(): never { throw raw; } }), error => error === raw);

  const unhandled: unknown[] = []; const onUnhandled = (error: unknown) => unhandled.push(error); process.on("unhandledRejection", onUnhandled);
  try {
    for (const mode of ["written", "throwing", "rejecting", "opt-out"] as const) for (const [value, reason] of [[undefined, "missing"], [null, "wrong-type"], [canary, "wrong-type"], [false, "wrong-type"], [NaN, "not-finite"], [Infinity, "not-finite"], [-1, "negative"]] as const) {
      const events: string[] = [], records: DiagnosticRecord[] = [];
      const q = createInMemoryPlatformWorkerQueue(); q.retry = () => { events.push("retry"); throw new Error("Invalid delay reached queue"); };
      const store = createInMemoryPlatformProcessingStore(), release = store.release.bind(store);
      store.release = async input => { events.push("release"); return release(input); };
      const processing = { processingStore: store, owner: accepted(platformPersistenceLeaseOwner("retry.worker")), leaseDurationMs: 1000 };
      const reporter = { report(record: DiagnosticRecord) { records.push(record); if (mode === "throwing") throw raw; return mode === "rejecting" ? Promise.reject(raw) : { status: "written" }; } } as unknown as PlatformDiagnosticReporter;
      const shell = accepted(await createPlatformWorkerShell({ apps: [{ id, name: "Retry fixture", mount(registry) {
        registry.registerObservabilityProfile({ name: profile, capability, action: "execute", signals: ["operational_log"] });
        registry.registerJob({ name, messageType: type, observability: mode === "opt-out" ? { kind: "opt_out", reason: "non_user_workload_path", justification: "Retry fixture." } : { kind: "profile", profile },
          handler: { handle() { events.push("handler"); throw raw; } } });
      } }], deps: { ...createPlatformTestMountDeps(), diagnostics: reporter }, queue: q, maxAttempts: 2, durableOutboxProcessing: processing,
        retryBackoffMs(attempt) { events.push("calculate"); equal(attempt, 1); return value as number; } }));
      deepEqual(events, []); processing.leaseDurationMs = 0;
      accepted(await shell.start()); shell.enqueue({ ...createPlatformTestQueueMessage({ id: "outbox-retry", type, payload: { outboxEntryId: "outbox-retry" } }), idempotencyKey: queueIdempotencyKey("outbox-retry") });
      await rejects(shell.runNext(), error => { equal(error instanceof TypeError, true); deepEqual((error as { diagnosticRecord: unknown }).diagnosticRecord, delayPacket(reason)); return true; });
      deepEqual(events, ["handler", "release", "calculate"]); equal(q.pending().length, 0); equal(q.deadLetters().length, 0);
      const observed = records.filter(record => record.code === "platform-worker.retry-delay-invalid");
      deepEqual(observed, mode === "opt-out" ? [] : [delayPacket(reason)]); equal(JSON.stringify(records).includes(canary), false);
      await shell.shutdown();
    }
    await nextTurn(); deepEqual(unhandled, []);
  } finally { process.off("unhandledRejection", onUnhandled); }

  for (const limit of [undefined, 1, 2]) {
    const q = createInMemoryPlatformWorkerQueue(); let limitReads = 0, calculatorReads = 0, calculations = 0, handlers = 0;
    const options = { apps: [{ id, name: "Accepted retry fixture", mount(registry: Parameters<NonNullable<PlatformWorkerShellOptions["apps"][number]["mount"]>>[0]) {
      registry.registerJob({ name, messageType: type, observability: { kind: "opt_out" as const, reason: "non_user_workload_path" as const, justification: "Retry defaults fixture." }, handler: { handle() { handlers++; throw raw; } } });
    } }], deps: createPlatformTestMountDeps(), queue: q,
      get maxAttempts() { limitReads++; return limit; },
      get retryBackoffMs() { calculatorReads++; return limit === undefined ? undefined : (attempt: number) => { calculations++; equal(attempt, 1); return 0.5; }; },
    } as PlatformWorkerShellOptions;
    const shell = accepted(await createPlatformWorkerShell(options));
    deepEqual([limitReads, calculatorReads, calculations], [1, 1, 0]);
    Object.defineProperty(options, "maxAttempts", { value: 0 }); Object.defineProperty(options, "retryBackoffMs", { value: () => { throw raw; } });
    accepted(await shell.start()); shell.enqueue(createPlatformTestQueueMessage({ id: "retry-valid", type, payload: {} }));
    const expectedAttempts = limit ?? 3;
    for (let attempt = 1; attempt <= expectedAttempts; attempt++) {
      const result = accepted(await shell.runNext());
      equal(result.status, attempt < expectedAttempts ? "retry" : "dead-lettered");
      if (result.status === "retry") equal(result.delayMs, limit === undefined ? attempt * 1000 : 0.5);
    }
    equal(handlers, expectedAttempts); equal(calculations, limit === 2 ? 1 : 0); equal(q.deadLetters().length, 1); equal(q.pending().length, 0);
    await shell.shutdown();
  }
  for (const definition of [workerRetryConfigurationDiagnostic, workerRetryDelayDiagnostic]) {
    const valid = definition === workerRetryConfigurationDiagnostic ? startup([{ setting: "max-attempts", reason: "not-positive" }]) : delayPacket("negative");
    equal(parseDiagnosticRecord<unknown>(definition, valid).ok, true);
    equal(parseDiagnosticRecord<unknown>(definition, { ...valid, detail: { ...valid.detail, raw: canary } }).ok, false);
    equal(parseDiagnosticRecord<unknown>(definition, { ...valid, definitionVersion: 2 }).ok, false);
  }
  // Test-only substitution proves the worker consumes the shared persistence check.
  const duration = require("../../persistence/src/leasing/domain/validation/duration") as { validatePersistenceLeaseDuration: typeof validatePersistenceLeaseDuration };
  const original = duration.validatePersistenceLeaseDuration;
  try {
    duration.validatePersistenceLeaseDuration = () => ({ ok: false, error: { reason: "not-positive" } });
    const result = await createPlatformWorkerShell({ apps: [], deps: createPlatformTestMountDeps(), durableOutboxProcessing: { leaseDurationMs: 1000 } as NonNullable<PlatformWorkerShellOptions["durableOutboxProcessing"]> });
    equal(result.ok, false);
  } finally { duration.validatePersistenceLeaseDuration = original; }

  // Test-only substituted checked values prove the caller does not fall back to raw options/results.
  const startupCheck = require("../src/configuration/domain/validation/startup") as { validateWorkerRetryConfiguration: typeof validateWorkerRetryConfiguration };
  const delayCheck = require("../src/configuration/domain/validation/retry-delay") as { validateWorkerRetryDelay: typeof validateWorkerRetryDelay };
  const originalStartup = startupCheck.validateWorkerRetryConfiguration, originalDelay = delayCheck.validateWorkerRetryDelay;
  try {
    startupCheck.validateWorkerRetryConfiguration = () => ({ ok: true, value: { maxAttempts: 2, retryBackoffMs: () => 5 } });
    delayCheck.validateWorkerRetryDelay = value => { equal(value, 5); return { ok: true, value: 77 }; };
    const shell = accepted(await createPlatformWorkerShell({ apps: [{ id, name: "Checked result fixture", mount(registry) {
      registry.registerJob({ name, messageType: type, observability: { kind: "opt_out", reason: "non_user_workload_path", justification: "Checked results fixture." }, handler: { handle() { throw raw; } } });
    } }], deps: createPlatformTestMountDeps(), maxAttempts: 1, retryBackoffMs: () => { throw Error("Unchecked calculator used"); } }));
    accepted(await shell.start()); shell.enqueue(createPlatformTestQueueMessage({ id: "checked-result", type, payload: {} }));
    const result = accepted(await shell.runNext()); equal(result.status, "retry"); if (result.status === "retry") equal(result.delayMs, 77);
    equal(accepted(await shell.runNext()).status, "dead-lettered"); await shell.shutdown();
  } finally { startupCheck.validateWorkerRetryConfiguration = originalStartup; delayCheck.validateWorkerRetryDelay = originalDelay; }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
