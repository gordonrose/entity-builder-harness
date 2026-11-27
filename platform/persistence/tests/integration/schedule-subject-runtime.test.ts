import { deepEqual, equal, notEqual } from "node:assert/strict";
import { recordId, recordKind, recordReference } from "@kanbien/core/persistence";
import { uuid } from "@kanbien/core/shared";
import { platformJobName } from "@kanbien/platform-contracts";
import { createInMemoryPlatformScheduleStore, createPlatformSchedule } from "../../src/index";

async function main(): Promise<void> {
  const subject = recordReference({ kind: required(recordKind("fixture.test-entity")), id: required(recordId("entity-1")) });
  const schedule = required(createPlatformSchedule({
    jobName: required(platformJobName("fixture.test-entity.cleanup")), dueAt: "2026-11-26T13:00:00+01:00", subject,
  }, { generate: () => uuid("25d537eb-e590-488c-97ef-a894299ed30e") }));
  deepEqual(schedule.subject, subject);
  notEqual(schedule.subject, subject);
  equal(schedule.dueAt, "2026-11-26T12:00:00.000Z");
  const store = createInMemoryPlatformScheduleStore();
  const created = required(await store.create(schedule));
  notEqual(created.subject, schedule.subject);
  const first = await store.get(schedule.id);
  const second = await store.get(schedule.id);
  deepEqual(first, second);
  notEqual(first?.subject, second?.subject);
  const due = required(await store.listDue({ asOf: schedule.dueAt, limit: 1 }));
  deepEqual(due[0]?.subject, subject);
  notEqual(due[0]?.subject, first?.subject);
  (created.subject as { id: string }).id = "changed-outside-store";
  equal((await store.get(schedule.id))?.subject?.id, "entity-1");
}

function required<T>(result: { readonly ok: true; readonly value: T } | { readonly ok: false; readonly error: unknown }): T {
  if (!result.ok) throw result.error;
  return result.value;
}
void main();
