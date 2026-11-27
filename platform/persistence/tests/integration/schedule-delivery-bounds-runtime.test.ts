import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import { outboxDeliveryPolicy, outboxEntry, outboxEntryId, outboxMessageType, recordId, recordKind, recordReference } from "@kanbien/core/persistence";
import { isoDateTimeFromDate, ok, uuid, type Clock } from "@kanbien/core/shared";
import { platformJobName } from "@kanbien/platform-contracts";
import { queueMessageType } from "@kanbien/core/queues";
import {
  createInMemoryPlatformScheduleStore, createPlatformSchedule, createPlatformScheduleDelivery,
  createPlatformScheduleDispatcher, platformPersistenceError,
  createPlatformScheduleJobOutboxFactory, persistenceScheduleJobMappingDiagnosticRecord,
  persistenceScheduleDeliveryBoundaryDiagnosticRecord, persistenceScheduleDeliveryConfigurationDiagnosticRecord,
  type PlatformSchedule, type PlatformScheduleStore, type PersistenceScheduleDeliveryBoundaryDetail,
} from "../../src/index";

const clock: Clock = { now: () => new Date("2026-11-26T12:00:00.000Z") };
const jobName = required(platformJobName("fixture.cleanup.run"));
const subjectKind = required(recordKind("platform.schedule"));
const messageType = required(outboxMessageType("fixture.cleanup.requested"));
const policy = required(outboxDeliveryPolicy("fixture.delivery.v1"));
const empty = { inspected: 0, deliveryCreated: 0, deliveryAlreadyCreated: 0, notDue: 0 };

async function main(): Promise<void> {
  await boundedProgressAndStops();
  await phaseReserveStillRelays();
  await failuresRemainFailures();
  configurationIsCapturedAndChecked();
  await jobMappingAndBlocking();
}

async function jobMappingAndBlocking(): Promise<void> {
  const store = await fixture();
  const due = required(await store.listDue({ asOf: isoDateTimeFromDate(clock.now()), limit: 2 }));
  const first = due[0]!;
  const unknown = required(createPlatformSchedule({ jobName: required(platformJobName("other-app.unknown.run")), dueAt: first.dueAt }, {
    generate: () => uuid("15d537eb-e590-488c-97ef-000000000000"),
  }));
  required(await store.create(unknown));
  const records: unknown[] = [];
  const factory = createPlatformScheduleJobOutboxFactory({ clock, deliveryPolicy: policy,
    jobs: [{ name: jobName, messageType: required(queueMessageType("fixture.cleanup.requested")) }],
    onDiagnostic: record => records.push(record),
  });
  const mapped = factory(first)!;
  equal(mapped.messageType, "fixture.cleanup.requested");
  equal(mapped.id, first.id);
  equal(factory(first)?.id, mapped.id);
  equal(mapped.subject.id, first.id);
  const delivery = createPlatformScheduleDelivery({ clock, scheduleStore: store, createOutboxEntry: factory });
  const delivered = required(await delivery.runOnce());
  equal(delivered.blocked, 1); equal(delivered.deliveryCreated, 2);
  deepEqual(records, [persistenceScheduleJobMappingDiagnosticRecord("job-unavailable")]);
  equal((await store.get(unknown.id))?.state, "blocked-job-unavailable");
  deepEqual(required(await delivery.runOnce()), empty);
  equal(required(await store.handoverDue({ scheduleId: unknown.id, asOf: unknown.dueAt, outboxEntry: entry(unknown) })).disposition, "blocked");
  equal(required(await store.resumeBlocked(unknown.id)).state, "waiting");
  equal(required(await store.resumeBlocked(unknown.id)).state, "waiting");
  const repairedFactory = createPlatformScheduleJobOutboxFactory({ clock, deliveryPolicy: policy,
    jobs: [{ name: unknown.jobName, messageType: required(queueMessageType("other-app.repaired.requested")) }],
  });
  equal(required(await createPlatformScheduleDelivery({ clock, scheduleStore: store, createOutboxEntry: repairedFactory }).runOnce()).deliveryCreated, 1);
  equal(required(await store.resumeBlocked(unknown.id)).state, "delivery-created", "repair cannot requeue delivered work");
  equal(required(await store.blockDue({ scheduleId: unknown.id, asOf: unknown.dueAt })).state, "delivery-created");
  const duplicate = { name: jobName, messageType: required(queueMessageType("fixture.cleanup.requested")) };
  throws(() => createPlatformScheduleJobOutboxFactory({ clock, deliveryPolicy: policy, jobs: [duplicate, duplicate] }), error => {
    deepEqual((error as { diagnosticRecord: unknown }).diagnosticRecord, persistenceScheduleJobMappingDiagnosticRecord("duplicate-job")); return true;
  });
}

async function fixture(count = 2) {
  const store = createInMemoryPlatformScheduleStore();
  for (let index = 0; index < count; index++) {
    required(await store.create(required(createPlatformSchedule({ jobName, dueAt: clock.now().toISOString() }, {
      generate: () => uuid(`25d537eb-e590-488c-97ef-${String(index).padStart(12, "0")}`),
    }))));
  }
  return store;
}

function entry(schedule: PlatformSchedule) {
  return outboxEntry({ id: outboxEntryId(String(schedule.id)),
    subject: recordReference({ kind: subjectKind, id: required(recordId(String(schedule.id))) }),
    messageType, deliveryPolicy: policy, createdAt: isoDateTimeFromDate(clock.now()),
  });
}

async function boundedProgressAndStops(): Promise<void> {
  const store = await fixture(105);
  let clocks = 0;
  let factories = 0;
  const delivery = createPlatformScheduleDelivery({ clock: { now() { clocks++; return clock.now(); } },
    scheduleStore: store, maximumSchedules: 20, createOutboxEntry(schedule) { factories++; return entry(schedule); },
  });
  deepEqual(required(await delivery.runOnce({ shouldContinue: () => false })), { ...empty, stopped: true });
  equal(clocks, 0); equal(factories, 0);
  let calls = 0;
  deepEqual(required(await delivery.runOnce({ shouldContinue: () => ++calls < 3 })), {
    inspected: 1, deliveryCreated: 1, deliveryAlreadyCreated: 0, notDue: 0, stopped: true,
  });
  equal(clocks, 1); equal(factories, 1);
  let total = 1;
  for (let pass = 0; pass < 6; pass++) {
    const result = required(await delivery.runOnce());
    equal(result.inspected <= 20, true);
    total += result.deliveryCreated;
  }
  equal(total, 105, "bounded passes progress beyond the existing 100-row selection cap");
  deepEqual(required(await delivery.runOnce()), empty);

  const cutoffs: string[] = [];
  let milliseconds = clock.now().getTime();
  const timed = await fixture();
  const stable: PlatformScheduleStore = { ...timed, async handoverDue(input) {
    cutoffs.push(input.asOf); milliseconds += 60_000; return timed.handoverDue(input);
  } };
  required(await createPlatformScheduleDelivery({ scheduleStore: stable,
    clock: { now: () => new Date(milliseconds) }, createOutboxEntry: entry,
  }).runOnce());
  deepEqual(cutoffs, [clock.now().toISOString(), clock.now().toISOString()]);
}

async function phaseReserveStillRelays(): Promise<void> {
  const store = await fixture();
  let sends = 0;
  let dueChecks = 0;
  const dispatcher = createPlatformScheduleDispatcher({
    delivery: createPlatformScheduleDelivery({ clock, scheduleStore: store, createOutboxEntry: entry }),
    relay: { async runOnce() { sends++; return ok({ status: "idle" as const }); } }, maximumRelayAttempts: 1,
  });
  const result = required(await dispatcher.runOnce({ shouldContinue: () => true,
    shouldContinueDelivery: () => ++dueChecks < 3,
  }));
  equal(result.delivery?.inspected, 1);
  equal(result.delivery?.stopped, true);
  equal(sends, 1, "a stopped due phase preserves its reserved relay opportunity");
  equal(result.stopReason, "idle");
}

async function failuresRemainFailures(): Promise<void> {
  const cause = Object.freeze({ private: "PRIVATE-BOUNDARY-CANARY" });
  for (const boundary of ["continuation-check", "clock", "selection", "entry-construction", "handover"] as const) {
    const store = await fixture(1);
    const records: unknown[] = [];
    let handovers = 0;
    const delivery = createPlatformScheduleDelivery({
      clock: { now() { if (boundary === "clock") throw cause; return clock.now(); } },
      scheduleStore: { ...store,
        async listDue(input) { if (boundary === "selection") throw cause; return store.listDue(input); },
        async handoverDue(input) { handovers++; if (boundary === "handover") throw cause; return store.handoverDue(input); },
      },
      createOutboxEntry(schedule) { if (boundary === "entry-construction") throw cause; return entry(schedule); },
      onDiagnostic(record) { records.push(record); throw new Error("PRIVATE-REPORTER-FAULT"); },
    });
    await rejects(() => delivery.runOnce({ shouldContinue() { if (boundary === "continuation-check") throw cause; return true; } }), error => error === cause);
    const effect: PersistenceScheduleDeliveryBoundaryDetail["effect"] = boundary === "handover" ? "handover-outcome-unknown" : "handover-not-started";
    equal(records.some(record => JSON.stringify(record) === JSON.stringify(persistenceScheduleDeliveryBoundaryDiagnosticRecord({ boundary, reason: "threw", effect }))), true);
    equal(JSON.stringify(records).includes("PRIVATE"), false);
    equal(handovers, boundary === "handover" ? 1 : 0);
  }
  {
    const store = await fixture(1);
    let selections = 0, handovers = 0;
    const records: unknown[] = [];
    const delivery = createPlatformScheduleDelivery({ clock: { now: () => new Date(NaN) }, createOutboxEntry: entry,
      scheduleStore: { ...store,
        async listDue(input) { selections++; return store.listDue(input); },
        async handoverDue(input) { handovers++; return store.handoverDue(input); },
      }, onDiagnostic: record => records.push(record) });
    await rejects(() => delivery.runOnce());
    equal(selections, 0, "an invalid clock value cannot reach the public store boundary");
    equal(handovers, 0);
    equal(records.some(record => JSON.stringify(record) === JSON.stringify(persistenceScheduleDeliveryBoundaryDiagnosticRecord({
      boundary: "clock", reason: "threw", effect: "handover-not-started" }))), true);
  }
  for (const boundary of ["selection", "handover"] as const) {
    const store = await fixture(1);
    const failure = { ok: false as const, error: platformPersistenceError({ code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: "PRIVATE-DEPENDENCY" }) };
    const records: unknown[] = [];
    const delivery = createPlatformScheduleDelivery({ clock, createOutboxEntry: entry,
      scheduleStore: { ...store,
        listDue: input => boundary === "selection" ? Promise.resolve(failure) : store.listDue(input),
        handoverDue: input => boundary === "handover" ? Promise.resolve(failure) : store.handoverDue(input),
      }, onDiagnostic: record => records.push(record),
    });
    equal(await delivery.runOnce(), failure);
    equal(records.some(record => JSON.stringify(record) === JSON.stringify(persistenceScheduleDeliveryBoundaryDiagnosticRecord({ boundary, reason: "returned-failure", effect: boundary === "handover" ? "handover-outcome-unknown" : "handover-not-started" }))), true);
    equal(JSON.stringify(records).includes("PRIVATE"), false);
  }
}

function configurationIsCapturedAndChecked(): void {
  const neverStore = {} as PlatformScheduleStore;
  for (const [maximumSchedules, reason] of [[null, "wrong-type"], ["4", "wrong-type"], [NaN, "not-finite"], [Infinity, "not-finite"], [1.5, "not-integer"], [0, "not-positive"], [101, "too-large"]] as const) {
    throws(() => createPlatformScheduleDelivery({ clock, scheduleStore: neverStore, createOutboxEntry: entry, maximumSchedules: maximumSchedules as number }), error => {
      deepEqual((error as { diagnosticRecord: unknown }).diagnosticRecord, persistenceScheduleDeliveryConfigurationDiagnosticRecord(reason)); return true;
    });
  }
  let reads = 0;
  createPlatformScheduleDelivery({ clock, scheduleStore: neverStore, createOutboxEntry: entry,
    get maximumSchedules() { reads++; if (reads > 1) throw new Error("Setting must be read once."); return 3; },
  });
  equal(reads, 1);
}

function required<T>(result: { readonly ok: true; readonly value: T } | { readonly ok: false; readonly error: unknown }): T {
  if (!result.ok) throw result.error;
  return result.value;
}
void main();
