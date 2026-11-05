import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { createInMemoryTracer, type Tracer } from "@kanbien/core/monitoring";
import type { QueueMessage, QueueMessageType, QueueIdempotencyKey } from "@kanbien/core/queues";
import type { JsonValue, Result } from "@kanbien/core/shared";
import { platformAppId, platformCapabilityName, platformJobName, platformObservabilityProfileName, type PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { createInMemoryPlatformProcessingStore, platformPersistenceLeaseOwner, platformPersistenceError } from "@kanbien/platform-persistence";
import { createPlatformTestMountDeps, createPlatformTestQueueMessage, validatorForTest } from "@kanbien/platform-testing";
import { createInMemoryPlatformWorkerQueue, createPlatformWorkerShell, type PlatformWorkerShellOptions } from "../src/index";
import { workerError } from "../src/errors";
import { platformWorkerDeliveryRejectedDiagnostic } from "../src/diagnostics";

const canary = "private-worker-delivery-canary";
function required<T>(value: Result<T, unknown>): T { if (!value.ok) throw new Error("Invalid fixture"); return value.value; }
const id = required(platformAppId("deliveryfixture"));
const name = required(platformJobName("deliveryfixture.execute"));
const profileName = required(platformObservabilityProfileName("deliveryfixture.execute"));
const capability = required(platformCapabilityName("deliveryfixture.execute"));
const type = "deliveryfixture.execute" as QueueMessageType;
const definition = defineDiagnostic({ code: "deliveryfixture.source", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } } } as const);
const records = Array.from({ length: 9 }, (_, ordinal) => required(createDiagnosticRecord(definition, { ordinal })));
const source = Object.freeze(Object.assign(new Error(canary), { diagnosticRecord: records[0], relatedDiagnosticRecords: records.slice(1) }));
const failed = platformPersistenceError({ code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: canary,
  diagnosticRecord: records[0]!, relatedDiagnosticRecords: records.slice(1), relatedDiagnosticDefinitions: [definition] });
const own = (phase: string, reason = "thrown", effect = "handler-not-invoked") => ({ schema: "core/diagnostic-record/v1", code: "platform-worker.boundary-failed", definitionVersion: 2,
  detail: { operation: "job-delivery", phase, reason, effect } });
const rejected = (field: string, condition: string) => ({ schema: "core/diagnostic-record/v1", code: "platform-worker.delivery-rejected", definitionVersion: 1,
  detail: { operation: "job-delivery", field, condition, effect: "handler-not-invoked" } });
type Mode = "default" | "injected" | "unavailable" | "throwing" | "rejecting" | "shadowed" | "opt-out" | "metrics-only";
async function fixture(input: { mode?: Mode; handle?: () => void; validate?: (value: unknown) => value is JsonValue;
  options?: Partial<PlatformWorkerShellOptions>; message?: QueueMessage; clock?: { now(): Date }; metrics?: boolean; trace?: boolean; logFailure?: unknown } = {}) {
  const observed: unknown[] = []; const attempts: DiagnosticRecord[] = []; let handled = 0, validated = 0;
  const mode = input.mode ?? "injected";
  const deps = createPlatformTestMountDeps({ ...(input.clock === undefined ? {} : { clock: input.clock }), logger: { write(record) {
    if (record.message === "platform.diagnostic.observed") observed.push(record.fields?.["diagnostic"]);
    else if (handled > 0 && input.logFailure !== undefined) throw input.logFailure;
  } } });
  const reporter = { report(record: DiagnosticRecord) {
    attempts.push(record); if (mode === "throwing") throw source;
    if (mode === "rejecting" || mode === "shadowed") {
      const pending = Promise.reject(source);
      if (mode === "shadowed") Object.defineProperty(pending, "then", { value() { throw new Error("Shadowed then must not run"); } });
      return pending;
    }
    if (mode === "unavailable") return { status: "unavailable" };
    observed.push(record); return { status: "written" };
  } } as unknown as PlatformDiagnosticReporter;
  const queue = input.options?.queue ?? createInMemoryPlatformWorkerQueue();
  const shell = required(await createPlatformWorkerShell({ apps: [{ id, name: "Delivery fixture", mount(registry) {
    registry.registerDiagnosticCatalog({ owner: "deliveryfixture", definitions: [definition] });
    registry.registerObservabilityProfile({ name: profileName, capability, action: "execute", signals: mode === "metrics-only" ? ["metric"] : input.trace ? ["operational_log", "trace"] : input.metrics ? ["operational_log", "metric"] : ["operational_log"] });
    registry.registerJob({ name, messageType: type, observability: mode === "opt-out" ? { kind: "opt_out", reason: "non_user_workload_path", justification: "Fixture opt-out." } : { kind: "profile", profile: profileName },
      ...(input.validate === undefined ? {} : { validator: validatorForTest((value: unknown): value is Readonly<Record<string, JsonValue>> => { validated++; return input.validate!(value); }) }),
      handler: { handle() { handled++; input.handle?.(); } } });
  } }], deps: mode === "default" ? deps : { ...deps, diagnostics: reporter }, maxAttempts: 1, ...input.options, queue }));
  equal((await shell.start()).ok, true); observed.length = 0; attempts.length = 0;
  shell.enqueue(input.message ?? createPlatformTestQueueMessage({ type, id: "delivery-id", payload: {} }));
  return { shell, queue, observed, attempts, handled: () => handled, validated: () => validated };
}
const durableMessage = () => ({ ...createPlatformTestQueueMessage({ type, id: "outbox-fixture", payload: { outboxEntryId: "outbox-fixture" } }), idempotencyKey: "outbox-fixture" as QueueIdempotencyKey });
const owner = required(platformPersistenceLeaseOwner("fixture.worker"));

async function main(): Promise<void> {
  equal(platformWorkerDeliveryRejectedDiagnostic.classification.failureSource, "unknown", "an observed rejection does not establish who caused it");
  const unready = required(await createPlatformWorkerShell({ apps: [], deps: createPlatformTestMountDeps() }));
  const admission = await unready.runNext(); if (admission.ok) throw new Error("Expected admission rejection");
  deepEqual(admission.error.diagnosticRecord, rejected("lifecycle", "not-ready"));
  equal((await unready.start()).ok, true);
  unready.enqueue(createPlatformTestQueueMessage({ type }));
  const unmatched = await unready.runNext(); if (!unmatched.ok || unmatched.value.status !== "dead-lettered") throw new Error("Expected unmatched delivery");
  deepEqual(unmatched.value.error.diagnosticRecord, rejected("job", "unmatched"));
  await unready.shutdown();

  for (const mode of ["default", "injected", "unavailable", "throwing", "rejecting", "shadowed", "opt-out", "metrics-only"] as const) {
    const current = await fixture({ mode, handle() { throw source; } });
    const result = await current.shell.runNext(); if (!result.ok || result.value.status !== "dead-lettered") throw new Error("Expected terminal result");
    equal(result.value.error.cause, source); deepEqual(result.value.error.diagnosticRecord, records[0]); deepEqual(result.value.error.relatedDiagnosticRecords, records.slice(1));
    const enabled = mode !== "opt-out" && mode !== "metrics-only";
    const expected = [own("handler", "thrown", "handler-outcome-unknown"), ...records];
    deepEqual(current.observed, mode === "default" || mode === "injected" ? expected : []);
    deepEqual(current.attempts, mode === "default" || !enabled ? [] : expected);
    equal(current.handled(), 1); equal(current.queue.deadLetters().length, 1);
    equal(JSON.stringify(current.observed).includes(canary), false);
    await current.shell.shutdown();
  }
  for (const mode of ["default", "injected", "opt-out", "metrics-only"] as const) {
    const current = await fixture({ mode, logFailure: source });
    const result = await current.shell.runNext();
    if (!result.ok || result.value.status !== "succeeded") throw new Error("A swallowed log fault must not retry completed work");
    const expected = { schema: "core/diagnostic-record/v1", code: "observability.boundary-failed", definitionVersion: 1,
      detail: { operation: "log-write", phase: "sink-invocation", field: "logger", reason: "threw", effect: "unknown" } };
    deepEqual(current.observed, mode === "opt-out" || mode === "metrics-only" ? [] : [expected, ...records]);
    equal(current.handled(), 1); equal(current.queue.deadLetters().length, 0); equal(current.queue.pending().length, 0);
    equal(current.observed.some((record) => (record as DiagnosticRecord).code === "platform-worker.boundary-failed"), false, "swallowed helper faults cannot invent a Worker failure");
    await current.shell.shutdown();
  }
  for (const mode of ["injected", "opt-out", "metrics-only"] as const) {
    const backing = createInMemoryTracer(); let starts = 0, ends = 0;
    const tracer: Tracer = { startSpan(input) {
      equal(this, tracer); starts++;
      const span = backing.startSpan(input);
      return { context: span.context, end() { ends++; throw source; } };
    } };
    const current = await fixture({ mode, trace: true, options: { tracer } });
    const result = await current.shell.runNext();
    if (!result.ok || result.value.status !== "succeeded") throw new Error("A swallowed span fault must not retry completed work");
    deepEqual(current.observed, mode === "injected" ? [{ schema: "core/diagnostic-record/v1", code: "observability.boundary-failed", definitionVersion: 1,
      detail: { operation: "trace-end", phase: "span-end", field: "provider", reason: "threw", effect: "unknown" } }, ...records] : []);
    equal(starts, mode === "injected" ? 1 : 0); equal(ends, mode === "injected" ? 1 : 0);
    equal(current.handled(), 1); equal(current.queue.deadLetters().length, 0);
    await current.shell.shutdown();
  }
  for (const reject of [false, true]) {
    const current = await fixture({ validate(_value): _value is JsonValue { if (!reject) throw source; return false; } });
    if (reject) {
      const result = await current.shell.runNext(); if (!result.ok || result.value.status !== "dead-lettered") throw new Error("Expected rejected payload");
      deepEqual(result.value.error.diagnosticRecord, rejected("payload", "validator-rejected"));
      deepEqual(current.observed, [rejected("payload", "validator-rejected")]);
    } else {
      await rejects(current.shell.runNext(), (error) => error === source);
      deepEqual(current.observed, [own("validation"), ...records]); equal(current.queue.deadLetters().length, 0);
    }
    equal(current.validated(), 1); equal(current.handled(), 0); await current.shell.shutdown();
  }
  for (const [payload, messageId, key, field, condition] of [
    [null, "outbox-fixture", "outbox-fixture", "payload", "null"], [[], "outbox-fixture", "outbox-fixture", "payload", "array"],
    [false, "outbox-fixture", "outbox-fixture", "payload", "nonobject"], [{}, "outbox-fixture", "outbox-fixture", "outbox-id", "absent"],
    [{ outboxEntryId: 1 }, "outbox-fixture", "outbox-fixture", "outbox-id", "wrong-type"], [{ outboxEntryId: "" }, "outbox-fixture", "outbox-fixture", "outbox-id", "empty"],
    [{ outboxEntryId: "outbox-fixture" }, "different", "outbox-fixture", "message-id", "mismatch"],
    [{ outboxEntryId: "outbox-fixture" }, "outbox-fixture", "different", "idempotency-key", "mismatch"],
  ] as const) {
    const store = createInMemoryPlatformProcessingStore(); let claims = 0;
    store.claim = async () => { claims++; return { ok: false, error: failed }; };
    const current = await fixture({ options: { durableOutboxProcessing: { processingStore: store, owner, leaseDurationMs: 1000 } },
      message: { ...createPlatformTestQueueMessage({ type, id: messageId }), payload, idempotencyKey: key as QueueIdempotencyKey } as unknown as QueueMessage });
    const result = await current.shell.runNext(); if (!result.ok || result.value.status !== "dead-lettered") throw new Error("Expected envelope rejection");
    deepEqual(result.value.error.diagnosticRecord, rejected(field, condition)); deepEqual(current.observed, [rejected(field, condition)]);
    equal(claims, 0); equal(current.handled(), 0); await current.shell.shutdown();
  }
  for (const validIdentity of [false, true]) {
    let payloadReads = 0, keyReads = 0;
    const store = createInMemoryPlatformProcessingStore();
    const message = { ...durableMessage(), id: (validIdentity ? "outbox-fixture" : "mismatch") as QueueMessage["id"],
      payload: { get outboxEntryId() { payloadReads++; return "outbox-fixture"; } },
      get idempotencyKey() { keyReads++; return "outbox-fixture" as QueueIdempotencyKey; } };
    const current = await fixture({ options: { durableOutboxProcessing: { processingStore: store, owner, leaseDurationMs: 1000 } }, message });
    const result = await current.shell.runNext(); equal(result.ok, true);
    equal(payloadReads, 3, "retain type, length and captured-ID reads"); equal(keyReads, validIdentity ? 1 : 0, "message mismatch short circuits the idempotency getter");
    equal(current.handled(), validIdentity ? 1 : 0); await current.shell.shutdown();
  }
  for (const at of ["claim-return", "claim-throw", "complete-return", "complete-throw", "release-return", "terminal-return", "lookup", "record", "retry", "backoff", "dead-letter", "observation"] as const) {
    let clockCalls = 0;
    const store = createInMemoryPlatformProcessingStore(); let releases = 0, completions = 0;
    const originalComplete = store.complete.bind(store);
    if (at.startsWith("claim")) store.claim = async () => { if (at === "claim-throw") throw source; return { ok: false, error: failed }; };
    store.complete = async (input) => { completions++; if (at === "complete-throw") throw source;
      if (at === "complete-return" || at === "terminal-return") return { ok: false, error: failed }; return originalComplete(input); };
    store.release = async () => { releases++; return { ok: false, error: failed }; };
    const durable = !["lookup", "record", "retry", "backoff", "dead-letter", "observation"].includes(at);
    const q = createInMemoryPlatformWorkerQueue();
    if (at === "retry") q.retry = () => { throw source; };
    if (at === "dead-letter") q.deadLetter = () => { throw source; };
    const current = await fixture({ handle() { if (["release-return", "terminal-return", "retry", "backoff", "dead-letter"].includes(at)) throw source; },
      ...(at === "observation" ? { metrics: true, clock: { now() { if (++clockCalls > 2) throw source; return new Date("2026-01-01T00:00:00Z"); } } } : {}),
      options: { queue: q, maxAttempts: ["release-return", "retry", "backoff", "complete-throw"].includes(at) ? 2 : 1,
        ...(durable ? { durableOutboxProcessing: { processingStore: store, owner, leaseDurationMs: 1000 } } : {}),
        ...(at === "lookup" || at === "record" ? { idempotency: { hasProcessed() { if (at === "lookup") throw source; return false; }, recordProcessed() { throw source; } } } : {}),
        retryBackoffMs() { if (at === "backoff") throw source; return 0; } },
      message: durableMessage() });
    if (["retry", "backoff", "dead-letter", "observation"].includes(at)) await rejects(current.shell.runNext(), (error) => error === source);
    else await current.shell.runNext();
    const expectedPhase = at === "record" ? "idempotency-record" : at === "terminal-return" ? "terminal-complete" : at === "dead-letter" ? "dead-letter" : at.split("-")[0]!;
    const boundaryRecords = current.observed.filter((record) => (record as DiagnosticRecord).code === "platform-worker.boundary-failed") as DiagnosticRecord[];
    equal(boundaryRecords.some((record) => (record.detail as { phase: string }).phase === expectedPhase), true, at);
    if (at === "complete-return") { equal(releases, 0); equal(completions, 1); }
    if (at === "complete-throw") { equal(releases, 1); equal(completions, 1); }
    for (const record of boundaryRecords) {
      const index = current.observed.indexOf(record);
      deepEqual(current.observed.slice(index + 1, index + 10), records, `source9 follows ${at} independently`);
    }
    await current.shell.shutdown();
  }

  for (const disposition of ["missing-outcome", "missing-lease", "lease-active", "succeeded", "terminal"] as const) {
    const store = createInMemoryPlatformProcessingStore();
    const claimed = required(await store.claim({ outboxEntryId: "outbox-fixture" as never, owner, acquiredAt: "2026-01-01T00:00:00Z" as never, leaseDurationMs: 1000 }));
    const { lease: _lease, ...withoutLease } = claimed.record;
    store.claim = async () => ({ ok: true, value: disposition === "missing-lease" ? { disposition: "claimed", record: withoutLease }
      : disposition === "lease-active" ? { disposition: "lease-active", record: claimed.record }
      : { disposition: "already-completed", record: { ...withoutLease, state: "completed", ...(disposition === "missing-outcome" ? {} : { completion: { outcome: disposition === "terminal" ? "terminal-failure" : "succeeded", completedAt: "2026-01-01T00:00:00Z" as never } }) } } });
    const current = await fixture({ options: { durableOutboxProcessing: { processingStore: store, owner, leaseDurationMs: 1000 } }, message: durableMessage() });
    const result = await current.shell.runNext();
    if (disposition === "missing-outcome" || disposition === "missing-lease") deepEqual(current.observed, [rejected(disposition === "missing-outcome" ? "completion-outcome" : "claimed-lease", "absent")]);
    else deepEqual(current.observed, [{ schema: "core/diagnostic-record/v1", code: "platform-worker.coordination-observed", definitionVersion: 1,
      detail: { condition: disposition === "lease-active" ? "lease-active" : disposition === "terminal" ? "already-terminal" : "already-completed", effect: "handler-not-invoked" } }]);
    equal(current.handled(), 0);
    equal(result.ok, disposition === "succeeded" || disposition === "terminal");
    if (disposition === "terminal") {
      if (!result.ok || result.value.status !== "dead-lettered") throw new Error("Expected unchanged terminal disposition");
      deepEqual(result.value.error.diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "platform-worker.coordination-observed", definitionVersion: 1,
        detail: { condition: "already-terminal", effect: "handler-not-invoked" } }, "terminal duplication preserves neutral evidence through result and persistence observation");
    }
    await current.shell.shutdown();
  }

  // Own-data selection rejects source accessors, unknown definitions and malformed records without evaluating them.
  let accessorReads = 0;
  const unsafe = Object.assign(new Error(canary), { relatedDiagnosticRecords: [records[1], { ...records[2]!, detail: { ordinal: canary } }] });
  Object.defineProperty(unsafe, "diagnosticRecord", { get() { accessorReads++; throw source; } });
  const current = await fixture({ handle() { throw unsafe; } });
  const unsafeResult = await current.shell.runNext(); if (!unsafeResult.ok || unsafeResult.value.status !== "dead-lettered") throw new Error("Expected terminal result");
  deepEqual(current.observed, [own("handler", "thrown", "handler-outcome-unknown"), records[1],
    { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason: "evidence-inaccessible" } },
    { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason: "evidence-rejected" } }]); equal(accessorReads, 0);
  equal(unsafeResult.value.error.cause, unsafe); await current.shell.shutdown();
  for (const thrown of [0, undefined, Object.freeze(new Error(canary)), { diagnosticRecord: { ...records[0]!, code: "unselected.source" } }]) {
    const unselected = await fixture({ handle() { throw thrown; } });
    const result = await unselected.shell.runNext(); if (!result.ok || result.value.status !== "dead-lettered") throw new Error("Expected original terminal result");
    equal(result.value.error.cause, thrown); deepEqual(unselected.observed, [own("handler", "thrown", "handler-outcome-unknown")]);
    equal(unselected.handled(), 1); await unselected.shell.shutdown();
  }

  for (const operation of ["enqueue", "retry", "deadLetter"] as const) {
    const seen: DiagnosticRecord[] = []; let reads = 0;
    const queue = createInMemoryPlatformWorkerQueue({ diagnosticDefinitions: [definition], now() { reads++; throw source; }, onDiagnostic(record) { equal(this.onDiagnostic !== undefined, true); seen.push(record); return Promise.reject(source); } });
    const entry = { message: durableMessage(), attempt: 1, enqueuedAt: "2026-01-01T00:00:00Z" as never };
    throws(() => operation === "enqueue" ? queue.enqueue(entry.message) : operation === "retry" ? queue.retry(entry, 0) : queue.deadLetter(entry, workerError("PLATFORM_WORKER_HANDLER_FAILED", "Fixture")), (error) => error === source);
    deepEqual(seen, [{ ...own("queue-clock", "thrown", "queue-not-mutated"), detail: { operation: operation === "deadLetter" ? "queue-dead-letter" : `queue-${operation}`, phase: "queue-clock", reason: "thrown", effect: "queue-not-mutated" } }, ...records]);
    equal(reads, 1); equal(queue.pending().length, 0); equal(queue.deadLetters().length, 0);
  }
  const builders = require("../src/diagnostics") as Record<string, unknown>;
  for (const mode of ["throws", "undefined", "malformed"] as const) {
    const processing = { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1,
      detail: { reason: mode === "throws" ? "construction-threw" : mode === "malformed" ? "evidence-rejected" : "construction-rejected" } };
    for (const key of ["workerDeliveryBoundaryRecord", "workerDeliveryRejectedRecord"]) {
      const descriptor = Object.getOwnPropertyDescriptor(builders, key)!;
      Object.defineProperty(builders, key, { ...descriptor, value: () => {
        if (mode === "throws") throw new Error(canary);
        return mode === "undefined" ? undefined : { code: canary };
      } });
      try {
        const seen: DiagnosticRecord[] = [];
        const queue = createInMemoryPlatformWorkerQueue({ diagnosticDefinitions: [definition], now() { throw source; }, onDiagnostic(record) { seen.push(record); } });
        if (key === "workerDeliveryBoundaryRecord") {
          throws(() => queue.enqueue(durableMessage()), error => error === source);
          deepEqual(seen, [processing, ...records]);
          const current = await fixture({ handle() { throw source; } });
          const result = await current.shell.runNext();
          if (!result.ok || result.value.status !== "dead-lettered") throw new Error("Expected unchanged terminal result");
          equal(result.value.error.cause, source); equal(current.handled(), 1);
          deepEqual(current.observed, [processing, ...records]);
          await current.shell.shutdown();
        } else {
          queue.close();
          const result = queue.enqueue(durableMessage());
          if (result.ok) throw new Error("Expected closed rejection");
          equal(result.error.code, "PLATFORM_WORKER_QUEUE_CLOSED");
          deepEqual(result.error.diagnosticRecord, processing); deepEqual(seen, [processing]);
        }
        equal(queue.pending().length, 0); equal(JSON.stringify(seen).includes(canary), false);
      } finally { Object.defineProperty(builders, key, descriptor); }
    }
  }
  const closedRecords: DiagnosticRecord[] = [];
  const closedQueue = createInMemoryPlatformWorkerQueue({ onDiagnostic(record) { closedRecords.push(record); } });
  closedQueue.close(); const closedResult = closedQueue.enqueue(durableMessage());
  if (closedResult.ok) throw new Error("Expected closed queue");
  deepEqual(closedResult.error.diagnosticRecord, { ...rejected("queue-state", "closed"), detail: { operation: "queue-enqueue", field: "queue-state", condition: "closed", effect: "queue-not-mutated" } });
  const retryClosed = closedQueue.retry({ message: createPlatformTestQueueMessage({ type }), attempt: 1, enqueuedAt: "2026-01-01T00:00:00Z" as never }, 0);
  if (retryClosed.ok) throw new Error("Expected unchanged closed retry rejection");
  deepEqual(retryClosed.error.diagnosticRecord, { ...rejected("queue-state", "closed"), detail: { operation: "queue-retry", field: "queue-state", condition: "closed", effect: "queue-not-mutated" } });
  deepEqual(closedRecords, [closedResult.error.diagnosticRecord, retryClosed.error.diagnosticRecord]); equal(closedQueue.pending().length, 0);
  await new Promise<void>((resolve) => setImmediate(resolve));
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
