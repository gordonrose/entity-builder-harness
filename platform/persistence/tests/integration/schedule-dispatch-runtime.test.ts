import { deepEqual, equal, ok as assertOk, rejects, throws } from "node:assert/strict";
import { numberConfigValue } from "@kanbien/core/config";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import {
  outboxDeliveryPolicy, outboxEntry, outboxEntryId, outboxMessageType,
  recordId, recordKind, recordReference,
} from "@kanbien/core/persistence";
import { inMemoryQueue, queueError, type Queue } from "@kanbien/core/queues";
import { isoDateTimeFromDate, ok, uuid, type Clock, type Result } from "@kanbien/core/shared";
import { platformJobName } from "@kanbien/platform-contracts";
import {
  createInMemoryPlatformOutboxStore, createPlatformOutboxRelay,
  createPlatformSchedule, createPlatformScheduleDelivery, createPlatformScheduleDispatcher,
  platformPersistenceAttempt, platformPersistenceFence, platformPersistenceLeaseOwner,
  persistenceScheduleRejectionDiagnosticRecord,
  type PlatformOutboxQueuePayload, type PlatformOutboxRelay, type PlatformOutboxRelayRunResult,
  type PlatformPersistenceError, type PlatformSchedule, type PlatformScheduleDelivery,
  type PlatformScheduleDeliveryRunResult, type PlatformScheduleStore,
} from "../../src/index";
import { withDiagnosticDeliverySuppressed } from "../../../../packages/core/tests/diagnostics/helpers/diagnostic-delivery-fixture";

type DispatcherOptions = Parameters<typeof createPlatformScheduleDispatcher>[0];
const configurationCode = "persistence.schedule-dispatch-configuration-invalid";
const boundaryCode = "persistence.schedule-dispatch-boundary-observed";
const privateCanary = "PRIVATE-DISPATCH-FIXTURE-DO-NOT-REPORT";
const noDue: PlatformScheduleDeliveryRunResult = {
  inspected: 0, deliveryCreated: 0, deliveryAlreadyCreated: 0, notDue: 0,
};
const oneDue: PlatformScheduleDeliveryRunResult = {
  inspected: 1, deliveryCreated: 1, deliveryAlreadyCreated: 0, notDue: 0,
};

async function main(): Promise<void> {
  await connectedBacklogRecovery();
  await limitsAndStops();
  await returnedAndThrownFailures();
  await diagnosticsRemainIndependent();
  await diagnosticFaultInjection();
  await configurationValidation();
  await checkedNumberReaderResult();
  console.log("Schedule dispatcher bounded handoff, backlog recovery, stopping and diagnostic tests passed.");
}

async function connectedBacklogRecovery(): Promise<void> {
  let milliseconds = Date.parse("2026-11-26T12:00:00.000Z");
  const clock: Clock = { now: () => new Date(milliseconds) };
  const sharedOutbox = createInMemoryPlatformOutboxStore();
  const acceptedQueue = inMemoryQueue<PlatformOutboxQueuePayload>();
  let failSend = true;
  let sends = 0;
  const queue: Queue<PlatformOutboxQueuePayload> = {
    async send(message, options) {
      sends++;
      if (failSend) return { ok: false, error: queueError({
        code: "QUEUE_UNAVAILABLE", defaultMessage: privateCanary,
      }) };
      return acceptedQueue.send(message, options);
    },
  };
  const initial = required(createPlatformSchedule({
    jobName: required(platformJobName("fixture.cleanup.run")),
    dueAt: clock.now().toISOString(),
  }, { generate: () => uuid("3e1265be-b0af-4be2-8ff7-340b7eca142d") }));
  let stored: PlatformSchedule = initial;
  let handovers = 0;
  let scans = 0;

  // This controlled single-process participant connects the actual due pass
  // to the SAME outbox consumed by the relay. It does not prove database
  // atomicity or concurrent handover; those require a real database fixture.
  const scheduleStore: PlatformScheduleStore = {
    async blockDue() { throw new Error("This registered-job fixture never blocks."); },
    async resumeBlocked() { throw new Error("This fixture never resumes blocked work."); },
    async create() { throw new Error("The fixture starts with its one stored reminder."); },
    async get(id) { return id === stored.id ? { ...stored } : null; },
    async listDue({ asOf, limit }) {
      scans++;
      equal(limit, 100, "the existing due-pass contract is unchanged");
      return ok(stored.state === "waiting" && Date.parse(stored.dueAt) <= Date.parse(asOf)
        ? [{ ...stored }] : []);
    },
    async handoverDue({ scheduleId, asOf, outboxEntry: entry }) {
      equal(scheduleId, stored.id);
      if (stored.state === "delivery-created") return ok({
        disposition: "outbox-already-created" as const, schedule: { ...stored },
      });
      if (Date.parse(stored.dueAt) > Date.parse(asOf)) return ok({
        disposition: "not-due" as const, schedule: { ...stored },
      });
      const created = await sharedOutbox.create(entry);
      if (!created.ok) return created;
      handovers++;
      stored = { ...stored, state: "delivery-created", outboxEntryId: entry.id };
      return ok({ disposition: "outbox-created" as const, schedule: { ...stored }, outbox: created.value });
    },
  };
  const delivery = createPlatformScheduleDelivery({
    clock, scheduleStore,
    createOutboxEntry: schedule => outboxEntry({
      id: outboxEntryId("fixture.schedule." + schedule.id),
      subject: recordReference({ kind: required(recordKind("platform.schedule")), id: required(recordId(String(schedule.id))) }),
      messageType: required(outboxMessageType("fixture.cleanup.requested")),
      deliveryPolicy: required(outboxDeliveryPolicy("fixture.delivery.v1")),
      createdAt: isoDateTimeFromDate(clock.now()),
    }),
  });
  const relay = createPlatformOutboxRelay({
    outbox: sharedOutbox, queue, clock,
    owner: required(platformPersistenceLeaseOwner("fixture.dispatcher")), leaseDurationMs: 1_000,
  });
  const dispatcher = createPlatformScheduleDispatcher({ delivery, relay, maximumRelayAttempts: 3 });

  deepEqual(required(await dispatcher.runOnce()), {
    delivery: oneDue, relayAttempts: 1, published: 0, stopReason: "queue-send-failed",
  });
  equal(handovers, 1);
  equal(stored.state, "delivery-created");
  assertOk(stored.outboxEntryId !== undefined);
  const entryId = stored.outboxEntryId;
  equal((await sharedOutbox.get(entryId))?.state, "leased");
  equal(acceptedQueue.acceptedMessages().length, 0);

  failSend = false;
  milliseconds += 1_001;
  deepEqual(required(await dispatcher.runOnce()), {
    delivery: noDue, relayAttempts: 2, published: 1, stopReason: "idle",
  }, "old backlog is relayed even though there are no newly due reminders");
  equal(handovers, 1, "recovery does not hand over the reminder again");
  equal(sends, 2);
  equal((await sharedOutbox.get(entryId))?.state, "published");
  const messages = acceptedQueue.acceptedMessages();
  equal(messages.length, 1);
  equal(messages[0]!.id, entryId);
  equal(messages[0]!.idempotencyKey, entryId);
  equal(messages[0]!.type, "fixture.cleanup.requested");
  deepEqual(messages[0]!.payload, { outboxEntryId: String(entryId) });

  deepEqual(required(await dispatcher.runOnce()), {
    delivery: noDue, relayAttempts: 1, published: 0, stopReason: "idle",
  });
  equal(scans, 3);
  equal(sends, 2, "an already published entry is not sent again");
}

async function limitsAndStops(): Promise<void> {
  let dueCalls = 0;
  let relayCalls = 0;
  const delivery: PlatformScheduleDelivery = { async runOnce() { dueCalls++; return ok(noDue); } };
  const relay: PlatformOutboxRelay = { async runOnce() { relayCalls++; return ok(relayOutcome("published")); } };
  const dispatcher = createPlatformScheduleDispatcher({ delivery, relay, maximumRelayAttempts: 2 });

  deepEqual(required(await dispatcher.runOnce({ shouldContinue: () => false })), {
    delivery: null, relayAttempts: 0, published: 0, stopReason: "requested-stop",
  });
  equal(dueCalls, 0); equal(relayCalls, 0);

  let checks = 0;
  deepEqual(required(await dispatcher.runOnce({ shouldContinue: () => ++checks < 2 })), {
    delivery: noDue, relayAttempts: 0, published: 0, stopReason: "requested-stop",
  });
  equal(dueCalls, 1); equal(relayCalls, 0);

  checks = 0;
  deepEqual(required(await dispatcher.runOnce({ shouldContinue: () => ++checks < 3 })), {
    delivery: noDue, relayAttempts: 1, published: 1, stopReason: "requested-stop",
  });
  equal(dueCalls, 2); equal(relayCalls, 1);

  const bounded = { delivery: noDue, relayAttempts: 2, published: 2, stopReason: "attempt-limit" };
  deepEqual(required(await dispatcher.runOnce()), bounded);
  deepEqual(required(await dispatcher.runOnce()), bounded, "counts reset on every invocation");
  equal(dueCalls, 4); equal(relayCalls, 5);

  for (const status of ["idle", "contended", "queue-send-failed", "publish-marker-failed"] as const) {
    let calls = 0;
    const stopped = createPlatformScheduleDispatcher({
      delivery, maximumRelayAttempts: 4,
      relay: { async runOnce() { calls++; return ok(relayOutcome(status)); } },
    });
    deepEqual(required(await stopped.runOnce()), {
      delivery: noDue, relayAttempts: 1, published: 0, stopReason: status,
    });
    equal(calls, 1, `${status} must not busy-loop or consume the remaining budget`);
  }

  let outcome = 0;
  const mixed = createPlatformScheduleDispatcher({
    delivery, maximumRelayAttempts: 3,
    relay: { async runOnce() { return ok(relayOutcome(++outcome === 1 ? "published" : "queue-send-failed")); } },
  });
  deepEqual(required(await mixed.runOnce()), {
    delivery: noDue, relayAttempts: 2, published: 1, stopReason: "queue-send-failed",
  }, "attempt and publication counts have different meanings");
}

async function returnedAndThrownFailures(): Promise<void> {
  const error: PlatformPersistenceError = { code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: privateCanary };
  const failure = { ok: false as const, error };
  let forbiddenCalls = 0;
  const dueRecords: DiagnosticRecord[] = [];
  const dueFailure = createPlatformScheduleDispatcher({
    delivery: { async runOnce() { return failure; } },
    relay: { async runOnce() { forbiddenCalls++; return ok({ status: "idle" as const }); } },
    maximumRelayAttempts: 2, onDiagnostic: record => dueRecords.push(record),
  });
  equal(await dueFailure.runOnce(), failure, "the original failed Result is preserved");
  equal(forbiddenCalls, 0, "a failed due pass is fail-fast");
  assertBoundary(dueRecords, "due-delivery", "returned-failure", "due-outcome-unknown");

  const relayRecords: DiagnosticRecord[] = [];
  let calls = 0;
  const relayFailure = createPlatformScheduleDispatcher({
    delivery: { async runOnce() { return ok(noDue); } },
    relay: { async runOnce() { calls++; return failure; } },
    maximumRelayAttempts: 2, onDiagnostic: record => relayRecords.push(record),
  });
  equal(await relayFailure.runOnce(), failure);
  equal(calls, 1);
  assertBoundary(relayRecords, "outbox-relay", "returned-failure", "relay-outcome-unknown");

  let laterCalls = 0;
  let laterDueCalls = 0;
  const laterRecords: DiagnosticRecord[] = [];
  const backlog = createInMemoryPlatformOutboxStore();
  const acceptedQueue = inMemoryQueue<PlatformOutboxQueuePayload>();
  const clock: Clock = { now: () => new Date("2026-11-26T12:00:00.000Z") };
  for (const id of ["fixture.partial.first", "fixture.partial.second"]) {
    required(await backlog.create(outboxEntry({
      id: outboxEntryId(id),
      subject: recordReference({ kind: required(recordKind("platform.schedule")), id: required(recordId(id)) }),
      messageType: required(outboxMessageType("fixture.cleanup.requested")),
      deliveryPolicy: required(outboxDeliveryPolicy("fixture.delivery.v1")),
      createdAt: isoDateTimeFromDate(clock.now()),
    })));
  }
  const actualRelay = createPlatformOutboxRelay({
    outbox: {
      ...backlog,
      async listDeliverable(input) {
        if (++laterCalls === 2) return failure;
        return backlog.listDeliverable(input);
      },
    },
    queue: acceptedQueue, clock,
    owner: required(platformPersistenceLeaseOwner("fixture.partial-dispatcher")), leaseDurationMs: 1_000,
  });
  const laterFailure = createPlatformScheduleDispatcher({
    delivery: { async runOnce() { laterDueCalls++; return ok(noDue); } },
    relay: actualRelay,
    maximumRelayAttempts: 4, onDiagnostic: record => laterRecords.push(record),
  });
  equal(await laterFailure.runOnce(), failure, "a prior successful publish does not replace the later failed Result");
  equal(laterDueCalls, 1); equal(laterCalls, 2, "already attempted work is not replayed after failure");
  equal(acceptedQueue.acceptedMessages().length, 1, "the actual relay published once before the failure");
  const publishedId = acceptedQueue.acceptedMessages()[0]!.payload.outboxEntryId;
  const pendingId = publishedId === "fixture.partial.first" ? "fixture.partial.second" : "fixture.partial.first";
  equal((await backlog.get(outboxEntryId(publishedId)))?.state, "published");
  equal((await backlog.get(outboxEntryId(pendingId)))?.state, "pending");
  assertBoundary(laterRecords, "outbox-relay", "returned-failure", "relay-outcome-unknown");

  for (const boundary of ["due-delivery", "outbox-relay"] as const) {
    const original = new Error(privateCanary);
    const records: DiagnosticRecord[] = [];
    const dispatcher = createPlatformScheduleDispatcher({
      delivery: { async runOnce() { if (boundary === "due-delivery") throw original; return ok(noDue); } },
      relay: { async runOnce() { throw original; } },
      maximumRelayAttempts: 2, onDiagnostic: record => records.push(record),
    });
    await rejects(() => dispatcher.runOnce(), cause => cause === original);
    assertBoundary(records, boundary, "threw", boundary === "due-delivery" ? "due-outcome-unknown" : "relay-outcome-unknown");
  }

  for (const [throwOnCheck, effect] of [
    [1, "dispatch-not-started"], [2, "due-success-returned"], [3, "relay-success-returned"],
  ] as const) {
    let checks = 0;
    let due = 0;
    let relayed = 0;
    const original = new Error(privateCanary);
    const records: DiagnosticRecord[] = [];
    const dispatcher = createPlatformScheduleDispatcher({
      delivery: { async runOnce() { due++; return ok(noDue); } },
      relay: { async runOnce() { relayed++; return ok(relayOutcome("published")); } },
      maximumRelayAttempts: 3, onDiagnostic: record => records.push(record),
    });
    await rejects(() => dispatcher.runOnce({ shouldContinue() {
      if (++checks === throwOnCheck) throw original;
      return true;
    } }), cause => cause === original);
    equal(due, throwOnCheck === 1 ? 0 : 1);
    equal(relayed, throwOnCheck === 3 ? 1 : 0);
    assertBoundary(records, "continuation-check", "threw", effect);
  }
}

async function diagnosticsRemainIndependent(): Promise<void> {
  const definition = defineDiagnostic({
    code: "fixture.dispatch-source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { boundary: { type: "enum", values: ["source"] } } },
  } as const);
  const primary = required(createDiagnosticRecord(definition, { boundary: "source" }));
  const related = Array.from({ length: 8 }, () => primary);
  const source: PlatformPersistenceError = {
    code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: privateCanary,
    diagnosticRecord: primary, relatedDiagnosticRecords: related,
  };
  const failure = { ok: false as const, error: source };
  const records: DiagnosticRecord[] = [];
  const dispatcher = createPlatformScheduleDispatcher({
    delivery: { async runOnce() { return failure; } },
    relay: { async runOnce() { throw new Error("Relay must not run after the failure."); } },
    maximumRelayAttempts: 1, diagnosticDefinitions: [definition], onDiagnostic: record => records.push(record),
  });
  equal(await dispatcher.runOnce(), failure);
  equal(source.diagnosticRecord, primary);
  equal(source.relatedDiagnosticRecords, related, "the independent location must not replace source evidence");
  equal(records[0]?.code, boundaryCode);
  deepEqual(records.slice(1), [primary, ...related], "source primary plus all eight related records survive");
  assertPrivate(records);

  for (const mode of ["returned", "thrown"] as const) {
    let observations = 0;
    const original = new Error(privateCanary);
    const guarded = createPlatformScheduleDispatcher({
      delivery: { async runOnce() { if (mode === "thrown") throw original; return failure; } },
      relay: { async runOnce() { throw new Error("Relay must not run after the failure."); } },
      maximumRelayAttempts: 1, diagnosticDefinitions: [definition],
      onDiagnostic() { observations++; throw new Error("PRIVATE-OBSERVER-FAILURE"); },
    });
    if (mode === "returned") equal(await guarded.runOnce(), failure);
    else await rejects(() => guarded.runOnce(), cause => cause === original);
    assertOk(observations > 0, "the observer was exercised without replacing the primary outcome");
  }

  const successful = createPlatformScheduleDispatcher({
    delivery: { async runOnce() { return ok(noDue); } },
    relay: { async runOnce() { return ok({ status: "idle" as const }); } },
    maximumRelayAttempts: 1, onDiagnostic() { throw new Error("PRIVATE-OBSERVER-FAILURE"); },
  });
  equal(required(await successful.runOnce()).stopReason, "idle");
}

async function diagnosticFaultInjection(): Promise<void> {
  // CommonJS test-only substitution at the implementation owner, restored
  // after each group. These calls exercise the actual dispatcher, not copies.
  const diagnosticOwner = require("../../src/diagnostics") as typeof import("../../src/diagnostics");
  const originalBoundaryBuilder = diagnosticOwner.persistenceScheduleDispatchBoundaryDiagnosticRecord;
  const originalConfigurationBuilder = diagnosticOwner.persistenceScheduleDispatchConfigurationDiagnosticRecord;
  const primary = persistenceScheduleRejectionDiagnosticRecord({
    operation: "list-due", field: "limit", condition: "not-positive", effect: "local-state-unchanged",
  });
  const related = Array.from({ length: 8 }, () => primary);
  const source: PlatformPersistenceError = {
    code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: privateCanary,
    diagnosticRecord: primary, relatedDiagnosticRecords: related,
  };
  const failure = { ok: false as const, error: source };

  try {
    for (const fault of ["threw", "undefined", "malformed"] as const) {
      let builderCalls = 0;
      const brokenBuilder = () => {
        builderCalls++;
        if (fault === "threw") throw new Error(privateCanary);
        return fault === "undefined" ? undefined : { schema: "invalid", code: privateCanary };
      };
      diagnosticOwner.persistenceScheduleDispatchBoundaryDiagnosticRecord = brokenBuilder as unknown as typeof originalBoundaryBuilder;
      for (const outcome of ["returned", "thrown"] as const) {
        let dueCalls = 0;
        let relayCalls = 0;
        const records: DiagnosticRecord[] = [];
        const beforeBuilds = builderCalls;
        const dispatcher = createPlatformScheduleDispatcher({
          delivery: { async runOnce() { dueCalls++; if (outcome === "thrown") throw source; return failure; } },
          relay: { async runOnce() { relayCalls++; return ok({ status: "idle" as const }); } },
          maximumRelayAttempts: 1, onDiagnostic: record => records.push(record),
        });
        if (outcome === "returned") equal(await dispatcher.runOnce(), failure);
        else await rejects(() => dispatcher.runOnce(), cause => cause === source);
        equal(dueCalls, 1); equal(relayCalls, 0);
        equal(builderCalls - beforeBuilds, 1, "diagnostic construction is not retried");
        equal(records[0]?.code, "core.diagnostics.processing-failed");
        deepEqual(records.slice(1), [primary, ...related]);
        equal(source.diagnosticRecord, primary); equal(source.relatedDiagnosticRecords, related);
        assertPrivate(records);
      }

      diagnosticOwner.persistenceScheduleDispatchConfigurationDiagnosticRecord = brokenBuilder as unknown as typeof originalConfigurationBuilder;
      let dependentReads = 0;
      throws(() => createPlatformScheduleDispatcher({
        maximumRelayAttempts: 0,
        get delivery(): never { dependentReads++; throw new Error(privateCanary); },
        get relay(): never { dependentReads++; throw new Error(privateCanary); },
      }), cause => {
        assertOk(cause instanceof TypeError);
        const record = (cause as TypeError & { diagnosticRecord: DiagnosticRecord }).diagnosticRecord;
        equal(record.code, "core.diagnostics.processing-failed");
        assertPrivate([record]);
        return true;
      });
      equal(dependentReads, 0);
    }
  } finally {
    diagnosticOwner.persistenceScheduleDispatchBoundaryDiagnosticRecord = originalBoundaryBuilder;
    diagnosticOwner.persistenceScheduleDispatchConfigurationDiagnosticRecord = originalConfigurationBuilder;
  }

  const definitionRecords: DiagnosticRecord[] = [];
  let definitionReads = 0;
  let dueCalls = 0;
  const unavailableDefinitions = createPlatformScheduleDispatcher({
    delivery: { async runOnce() { dueCalls++; return failure; } },
    relay: { async runOnce() { throw new Error("Relay must not run."); } },
    maximumRelayAttempts: 1,
    get diagnosticDefinitions(): never { definitionReads++; throw new Error(privateCanary); },
    onDiagnostic: record => definitionRecords.push(record),
  });
  equal(await unavailableDefinitions.runOnce(), failure);
  equal(dueCalls, 1); assertOk(definitionReads > 0);
  equal(definitionRecords[0]?.code, boundaryCode);
  deepEqual(definitionRecords.filter(record => record.code === primary.code), [primary, ...related]);
  assertOk(definitionRecords.some(record => record.code === "core.diagnostics.processing-failed"
    && (record.detail as { reason?: string }).reason === "definition-selection-failed"));
  assertPrivate(definitionRecords);

  let reports = 0;
  const asynchronousSink = createPlatformScheduleDispatcher({
    delivery: { async runOnce() { return failure; } },
    relay: { async runOnce() { throw new Error("Relay must not run."); } },
    maximumRelayAttempts: 1,
    onDiagnostic() { reports++; return Promise.reject(new Error(privateCanary)); },
  });
  equal(await asynchronousSink.runOnce(), failure);
  // Let promise-rejection handling run; an unhandled sink rejection must not
  // escape the shared delivery guard after the dispatch operation has ended.
  await new Promise<void>(resolve => setImmediate(resolve));
  assertOk(reports > 0);

  let pending: ReturnType<ReturnType<typeof createPlatformScheduleDispatcher>["runOnce"]> | undefined;
  let suppressedReports = 0;
  let suppressedDueCalls = 0;
  withDiagnosticDeliverySuppressed(attempted => {
    const dispatcher = createPlatformScheduleDispatcher({
      // A synchronous dependency throw reaches the actual dispatch boundary
      // while the existing synchronous suppression fixture is installed.
      delivery: { runOnce() { suppressedDueCalls++; throw source; } },
      relay: { async runOnce() { throw new Error("Relay must not run."); } },
      maximumRelayAttempts: 1, onDiagnostic() { suppressedReports++; },
    });
    pending = dispatcher.runOnce();
    equal(attempted[0]?.code, boundaryCode);
    deepEqual(attempted.slice(1), [primary, ...related]);
    equal(suppressedReports, 0, "intentional suppression uses the shared delivery guard");
    assertPrivate(attempted);
  });
  assertOk(pending !== undefined);
  await rejects(pending, cause => cause === source);
  equal(suppressedDueCalls, 1); equal(suppressedReports, 0);
}

async function configurationValidation(): Promise<void> {
  const delivery: PlatformScheduleDelivery = { async runOnce() { return ok(noDue); } };
  const relay: PlatformOutboxRelay = { async runOnce() { return ok(relayOutcome("published")); } };
  const invalid: readonly (readonly [unknown, string])[] = [
    [undefined, "missing"], [null, "wrong-type"], [privateCanary, "wrong-type"], [true, "wrong-type"],
    [Number.NaN, "not-finite"], [Number.POSITIVE_INFINITY, "not-finite"], [Number.NEGATIVE_INFINITY, "not-finite"],
    [0.5, "not-integer"], [0, "not-positive"], [-1, "not-positive"], [101, "too-large"],
  ];
  for (const [value, reason] of invalid) {
    let dependentReads = 0;
    let reports = 0;
    throws(() => createPlatformScheduleDispatcher({ maximumRelayAttempts: value,
      get delivery(): never { dependentReads++; throw new Error(privateCanary); },
      get relay(): never { dependentReads++; throw new Error(privateCanary); },
      get diagnosticDefinitions(): never { dependentReads++; throw new Error(privateCanary); },
      onDiagnostic() { reports++; },
    } as unknown as DispatcherOptions), cause => {
      assertOk(cause instanceof TypeError);
      const record = (cause as TypeError & { diagnosticRecord?: DiagnosticRecord }).diagnosticRecord;
      deepEqual(record, { schema: "core/diagnostic-record/v1", code: configurationCode, definitionVersion: 1,
        detail: { field: "maximum-relay-attempts", reason } });
      assertPrivate([record!]);
      return true;
    });
    equal(dependentReads, 0, "invalid configuration does not select or invoke dependencies");
    equal(reports, 0, "constructor errors carry evidence to the caller rather than reporting runtime observations");
  }

  const rawSettingFailure = Object.freeze(new Error(privateCanary));
  let untouched = 0;
  throws(() => createPlatformScheduleDispatcher({
    get maximumRelayAttempts(): never { throw rawSettingFailure; },
    get delivery(): never { untouched++; throw new Error("Dependency must not be selected."); },
    get relay(): never { untouched++; throw new Error("Dependency must not be selected."); },
  }), cause => cause === rawSettingFailure);
  equal(untouched, 0);

  for (const limit of [1, 100]) {
    const dispatcher = createPlatformScheduleDispatcher({ delivery, relay, maximumRelayAttempts: limit });
    deepEqual(required(await dispatcher.runOnce()), {
      delivery: noDue, relayAttempts: limit, published: limit, stopReason: "attempt-limit",
    });
  }

  let reads = 0;
  const options: DispatcherOptions = {
    delivery, relay,
    get maximumRelayAttempts() { reads++; return reads === 1 ? 2 : 100; },
  };
  const captured = createPlatformScheduleDispatcher(options);
  equal(reads, 1, "validated configuration is read once at construction");
  equal(required(await captured.runOnce()).relayAttempts, 2);
  equal(required(await captured.runOnce()).relayAttempts, 2);
  equal(reads, 1, "invocations use captured configuration rather than rereading it");

  throws(() => createPlatformScheduleDispatcher({ delivery, relay, maximumRelayAttempts: 0,
    onDiagnostic() { throw new Error("PRIVATE-OBSERVER-FAILURE"); },
  }), cause => cause instanceof TypeError
    && (cause as TypeError & { diagnosticRecord?: DiagnosticRecord }).diagnosticRecord?.code === configurationCode);
}

async function checkedNumberReaderResult(): Promise<void> {
  const owner = Object.values(require.cache).map(module => module?.exports).find((candidate: unknown) => {
    if (typeof candidate !== "object" || candidate === null) return false;
    const descriptor = Object.getOwnPropertyDescriptor(candidate, "numberConfigValue");
    return descriptor !== undefined && descriptor.value === numberConfigValue && descriptor.writable;
  }) as { numberConfigValue: typeof numberConfigValue } | undefined;
  assertOk(owner, "the actual Core number reader must be loaded through the public import");
  const original = owner.numberConfigValue;
  let reads = 0;
  try {
    owner.numberConfigValue = (source, key) => {
      reads++;
      equal(key, "maximum-relay-attempts");
      equal(source.get(key), 9);
      return ok(2);
    };
    const dispatcher = createPlatformScheduleDispatcher({
      delivery: { async runOnce() { return ok(noDue); } },
      relay: { async runOnce() { return ok(relayOutcome("published")); } },
      maximumRelayAttempts: 9,
    });
    deepEqual(required(await dispatcher.runOnce()), {
      delivery: noDue, relayAttempts: 2, published: 2, stopReason: "attempt-limit",
    }, "the shared reader's checked value, not the submitted number, controls execution");
    equal(reads, 1);
  } finally { owner.numberConfigValue = original; }
  equal(numberConfigValue, original);
}

function relayOutcome(status: PlatformOutboxRelayRunResult["status"]): PlatformOutboxRelayRunResult {
  if (status === "idle") return { status };
  const entryId = outboxEntryId("fixture.dispatch.delivery");
  if (status === "contended") return { status, outboxEntryId: entryId };
  return { status, outboxEntryId: entryId,
    attempt: required(platformPersistenceAttempt(1)), fence: required(platformPersistenceFence(1)) };
}

function assertBoundary(records: readonly DiagnosticRecord[], boundary: string, reason: string, effect: string): void {
  const own = records.filter(record => record.code === boundaryCode);
  equal(own.length, 1);
  deepEqual(own[0], { schema: "core/diagnostic-record/v1", code: boundaryCode, definitionVersion: 1,
    detail: { boundary, reason, effect } });
  assertPrivate(records);
}

function assertPrivate(records: readonly DiagnosticRecord[]): void {
  equal(JSON.stringify(records).includes(privateCanary), false, "diagnostics must not report native messages or submitted values");
}

function required<TValue, TError>(result: Result<TValue, TError>): TValue {
  if (!result.ok) throw result.error;
  return result.value;
}

void main().catch(error => { console.error(error); process.exitCode = 1; });
