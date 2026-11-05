import { deepEqual, equal, rejects } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import type { QueueIdempotencyKey, QueueMessageType } from "@kanbien/core/queues";
import { platformAppId, platformCapabilityName, platformJobName, platformObservabilityProfileName, type PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { createPlatformTestMetrics, createPlatformTestMountDeps, createPlatformTestQueueMessage } from "@kanbien/platform-testing";
import { createInMemoryPlatformWorkerQueue, createPlatformWorkerShell } from "../src/index";
import { workerError } from "../src/errors";
import { createInMemoryPlatformProcessingStore, platformPersistenceLeaseOwner } from "@kanbien/platform-persistence";

const secret = "private-worker-context-canary@example.invalid";
const checkedId = platformAppId("contextfixture"), checkedJob = platformJobName("contextfixture.execute"), checkedProfile = platformObservabilityProfileName("contextfixture.execute"), checkedCapability = platformCapabilityName("contextfixture.execute");
if (!checkedId.ok || !checkedJob.ok || !checkedProfile.ok || !checkedCapability.ok) throw new Error("Invalid fixture");
const id = checkedId.value, name = checkedJob.value, profile = checkedProfile.value, capability = checkedCapability.value;
const definition = defineDiagnostic({ code: "contextfixture.source-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { index: { type: "integer", minimum: 0, maximum: 7 } } } });
const records = Array.from({ length: 8 }, (_, index) => { const result = createDiagnosticRecord(definition, { index }); if (!result.ok) throw new Error("Invalid fixture"); return result.value; });
const location = { schema: "core/diagnostic-record/v1", code: "platform-runtime.boundary-failed", definitionVersion: 1,
  detail: { operation: "job-context", phase: "clock-read", subject: "context", boundary: "invocation", effect: "context-not-returned" } };
async function main(): Promise<void> {
  for (const mode of ["default", "injected", "unavailable", "opt-out", "metrics-only"] as const) for (const hasUpstream of [false, true]) {
    const source = hasUpstream ? Object.assign(new Error(secret), { diagnosticRecord: records[0], relatedDiagnosticRecords: records }) : new Error(secret);
    const observed: unknown[] = [], logs: LogRecord[] = [];
    let clocks = 0, handled = 0, diagnosticAttempts = 0;
    const metrics = createPlatformTestMetrics();
    const base = createPlatformTestMountDeps({ metrics, clock: { now() { if (++clocks === 2) throw source; return new Date("2026-01-01T00:00:00Z"); } }, logger: { write(record) {
      if (record.message === "platform.diagnostic.observed") { diagnosticAttempts++; if (mode === "unavailable") throw source; observed.push(record.fields?.["diagnostic"]); }
      logs.push(record);
    } } });
    const reporter: PlatformDiagnosticReporter = { report(record) { diagnosticAttempts++; observed.push(record); return { status: "written" }; } };
    const queue = createInMemoryPlatformWorkerQueue();
    const shell = await createPlatformWorkerShell({ apps: [{ id, name: secret, mount(registry) {
      registry.registerDiagnosticCatalog({ owner: "contextfixture", definitions: [definition] });
      registry.registerObservabilityProfile({ name: profile, capability, action: "execute", signals: mode === "metrics-only" ? ["metric"] : ["operational_log", "metric"],
        nfrObjectives: [{ nfrClass: "async_completion", measurement: "job_execution_latency" }] });
      registry.registerJob({ name, messageType: "contextfixture.execute" as QueueMessageType,
        observability: mode === "opt-out" ? { kind: "opt_out", reason: "non_user_workload_path", justification: "Fixture." } : { kind: "profile", profile }, handler: { handle() { handled++; } } });
    } }], deps: mode === "injected" ? { ...base, diagnostics: reporter } : base, queue, maxAttempts: 1 });
    if (!shell.ok) throw new Error(shell.error.code); equal((await shell.value.start()).ok, true);
    equal(shell.value.enqueue(createPlatformTestQueueMessage({ type: "contextfixture.execute" as QueueMessageType, payload: {} })).ok, true);
    const result = await shell.value.runNext(); equal(result.ok, true); if (!result.ok || result.value.status !== "dead-lettered") throw new Error("Expected legacy terminal delivery");
    equal(handled, 0); equal(result.value.error.code, "PLATFORM_WORKER_HANDLER_FAILED"); equal(result.value.error.defaultMessage, "Platform job handler failed."); equal(result.value.error.cause, source);
    deepEqual(result.value.error.diagnosticRecord, hasUpstream ? records[0] : location);
    deepEqual(result.value.error.relatedDiagnosticRecords, hasUpstream ? records : undefined);
    const enabled = mode !== "opt-out" && mode !== "metrics-only";
    deepEqual(observed, !enabled || mode === "unavailable" ? [] : [location, ...(hasUpstream ? [records[0], ...records] : [])]);
    equal(diagnosticAttempts, enabled ? hasUpstream ? 10 : 1 : 0); equal(JSON.stringify(logs).includes(secret), false);
    // This diagnostic batch deliberately preserves the existing handlerStarted metric population.
    equal(metrics.points().filter((metric) => metric.name === "platform.worker.job.execution_latency").length, mode === "opt-out" ? 0 : 1);
    equal(queue.deadLetters().length, 1); equal((await shell.value.shutdown()).ok, true);
  }

  // An argument accessor can fail before the Runtime factory exists. It has Worker, not invented Runtime, provenance.
  let correlationReads = 0, handlers = 0;
  const source = Object.assign(new Error(secret), { diagnosticRecord: records[0], relatedDiagnosticRecords: records });
  const observed: DiagnosticRecord[] = [];
  const queue = createInMemoryPlatformWorkerQueue();
  const shell = await createPlatformWorkerShell({ apps: [{ id, name: secret, mount(registry) {
    registry.registerDiagnosticCatalog({ owner: "contextfixture", definitions: [definition] });
    registry.registerObservabilityProfile({ name: profile, capability, action: "execute", signals: ["operational_log"] });
    registry.registerJob({ name, messageType: "contextfixture.execute" as QueueMessageType, observability: { kind: "profile", profile }, handler: { handle() { handlers++; } } });
  } }], deps: { ...createPlatformTestMountDeps(), diagnostics: { report(record) { observed.push(record); return { status: "written" }; } } }, queue, maxAttempts: 1 });
  if (!shell.ok) throw new Error(shell.error.code); await shell.value.start();
  shell.value.enqueue({ ...createPlatformTestQueueMessage({ type: "contextfixture.execute" as QueueMessageType }), get correlationId() { if (++correlationReads === 1) throw source; return undefined as never; } });
  const result = await shell.value.runNext(); if (!result.ok || result.value.status !== "dead-lettered") throw new Error("Expected original delivery policy");
  equal(handlers, 0); equal(correlationReads, 2); equal(result.value.error.cause, source);
  deepEqual(observed, [{ schema: "core/diagnostic-record/v1", code: "platform-worker.boundary-failed", definitionVersion: 1,
    detail: { operation: "job-delivery", phase: "context-input", boundary: "selection", effect: "handler-not-invoked" } }, records[0], ...records]);
  await shell.value.shutdown();

  for (const enabled of [false, true]) {
    const emitted: DiagnosticRecord[] = []; const contexts: unknown[] = []; let clocks = 0, handlers = 0;
    const q = createInMemoryPlatformWorkerQueue();
    const preContext = await createPlatformWorkerShell({ apps: [{ id, name: secret, mount(registry) {
      registry.registerDiagnosticCatalog({ owner: "contextfixture", definitions: [definition] });
      registry.registerObservabilityProfile({ name: profile, capability, action: "execute", signals: ["operational_log"] });
      registry.registerJob({ name, messageType: "contextfixture.execute" as QueueMessageType, observability: enabled ? { kind: "profile", profile } : { kind: "opt_out", reason: "non_user_workload_path", justification: "Fixture." }, handler: { handle() { handlers++; } } });
    } }], queue: q, deps: { ...createPlatformTestMountDeps({ clock: { now() { clocks++; throw source; } } }), diagnostics: { report(record, context) { emitted.push(record); contexts.push(context); return { status: "written" }; } } } });
    if (!preContext.ok) throw new Error(preContext.error.code); await preContext.value.start();
    preContext.value.enqueue(createPlatformTestQueueMessage({ type: "contextfixture.execute" as QueueMessageType }));
    await rejects(preContext.value.runNext(), (error) => error === source);
    equal(clocks, 1); equal(handlers, 0); equal(q.pending().length, 0); equal(q.deadLetters().length, 0);
    deepEqual(emitted, enabled ? [{ schema: "core/diagnostic-record/v1", code: "platform-worker.boundary-failed", definitionVersion: 1,
      detail: { operation: "job-delivery", phase: "delivery-clock", boundary: "selection-or-invocation", effect: "handler-not-invoked" } }, records[0], ...records] : []);
    deepEqual(contexts, enabled ? Array.from({ length: 10 }, () => ({ capability: "platform-worker", operation: "job-delivery", stage: "request" })) : []);
    await preContext.value.shutdown();
  }

  // The original context envelope must be observed before cleanup can replace its result or throw.
  for (const mode of ["retry-return", "retry-throw", "backoff-throw", "settlement-return", "settlement-clock"] as const) {
    const emitted: DiagnosticRecord[] = []; const contexts: unknown[] = [];
    const cleanupThrown = new Error("private-cleanup-canary");
    const retryError = workerError("PLATFORM_WORKER_QUEUE_CLOSED", "Original retry error.");
    const persistenceError = { code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED" as const, defaultMessage: "Original settlement error." };
    const durable = mode.startsWith("settlement"); let clocks = 0, retries = 0, releases = 0, handlers = 0;
    const q = createInMemoryPlatformWorkerQueue();
    q.retry = () => { retries++; equal(emitted.length, 10); if (mode === "retry-throw") throw cleanupThrown; return { ok: false, error: retryError }; };
    const processingStore = createInMemoryPlatformProcessingStore();
    processingStore.release = async () => { releases++; equal(emitted.length, 10); return { ok: false, error: persistenceError }; };
    const owner = platformPersistenceLeaseOwner("fixture.worker"); if (!owner.ok) throw new Error("Invalid fixture");
    const correction = await createPlatformWorkerShell({ apps: [{ id, name: secret, mount(registry) {
      registry.registerDiagnosticCatalog({ owner: "contextfixture", definitions: [definition] });
      registry.registerObservabilityProfile({ name: profile, capability, action: "execute", signals: ["operational_log"] });
      registry.registerJob({ name, messageType: "contextfixture.execute" as QueueMessageType, observability: { kind: "profile", profile }, handler: { handle() { handlers++; } } });
    } }], queue: q, maxAttempts: 2, retryBackoffMs() { if (mode === "backoff-throw") { equal(emitted.length, 10); throw cleanupThrown; } return 1; },
      ...(durable ? { durableOutboxProcessing: { processingStore, owner: owner.value, leaseDurationMs: 1000 } } : {}),
      deps: { ...createPlatformTestMountDeps({ clock: { now() {
        clocks++;
        if (clocks === (durable ? 3 : 2)) throw source;
        if (mode === "settlement-clock" && clocks === 4) { equal(emitted.length, 10); throw cleanupThrown; }
        return new Date("2026-01-01T00:00:00Z");
      } } }), diagnostics: { report(record, context) { emitted.push(record); contexts.push(context); return { status: "written" }; } } } });
    if (!correction.ok) throw new Error(correction.error.code); await correction.value.start();
    correction.value.enqueue({ ...createPlatformTestQueueMessage({ id: "outbox-fixture", type: "contextfixture.execute" as QueueMessageType, payload: { outboxEntryId: "outbox-fixture" } }), idempotencyKey: "outbox-fixture" as QueueIdempotencyKey });
    if (mode === "retry-throw" || mode === "backoff-throw" || mode === "settlement-clock") {
      await rejects(correction.value.runNext(), (error) => error === cleanupThrown);
    } else {
      const result = await correction.value.runNext(); if (result.ok) throw new Error("Expected original cleanup failure result");
      if (mode === "retry-return") equal(result.error, retryError);
      else { equal(result.error.code, "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED"); equal(result.error.cause, persistenceError); deepEqual(result.error.details, { phase: "release", persistenceCode: persistenceError.code }); }
    }
    equal(handlers, 0); equal(retries, mode === "retry-return" || mode === "retry-throw" ? 1 : 0); equal(releases, mode === "settlement-return" ? 1 : 0);
    deepEqual(emitted.slice(0, 10), [location, records[0], ...records]);
    deepEqual(contexts.slice(0, 10), Array.from({ length: 10 }, () => ({ capability: "platform-runtime", operation: "job-context", stage: "request" })));
    equal(emitted.length, mode === "retry-return" ? 12 : 11);
    deepEqual(emitted[10], { schema: "core/diagnostic-record/v1", code: "platform-worker.boundary-failed", definitionVersion: 2,
      detail: { operation: "job-delivery", phase: mode === "settlement-return" ? "release" : mode === "settlement-clock" ? "settlement-clock" : mode === "backoff-throw" ? "backoff" : "retry",
        reason: mode === "retry-return" || mode === "settlement-return" ? "returned-failure" : "thrown", effect: mode === "settlement-return" ? "settlement-unknown" : "handler-not-invoked" } });
    if (mode === "retry-return") deepEqual(emitted[11], retryError.diagnosticRecord);
    equal(q.pending().length, 0); equal(q.deadLetters().length, 0); await correction.value.shutdown();
  }
}
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
