import { createPlatformSchedule } from "@kanbien/platform-persistence";
import { recordId, recordKind, recordReference } from "@kanbien/core/persistence";
import { testEntityError, type TestEntityError } from "../../contract/errors";
import type { TestEntity } from "../../contract/types";
import { testEntityExpiredPurgeDueAt } from "../retention";
import type { TestEntityServiceDependencies } from "./dependencies";

/** Save one future invocation of the existing purge job; this does not run it. */
export async function rememberExpiredTestEntityPurge(
  entity: TestEntity,
  deps: TestEntityServiceDependencies,
): Promise<{ readonly ok: true } | { readonly ok: false; readonly error: TestEntityError }> {
  const reminder = deps.expiredPurgeReminder;
  const dueAt = testEntityExpiredPurgeDueAt(entity);
  if (reminder === undefined || entity.visibility !== "archived" || dueAt === undefined) return { ok: true };

  const kind = recordKind("entity-smoke.test-entity"), id = recordId(entity.id);
  if (!kind.ok) return kind;
  if (!id.ok) return id;
  const schedule = createPlatformSchedule({ jobName: reminder.jobName, dueAt: dueAt.toISOString(),
    subject: recordReference({ kind: kind.value, id: id.value }) }, deps.uuidGenerator);
  if (!schedule.ok) return { ok: false, error: testEntityError(schedule.error.code, schedule.error.defaultMessage,
    schedule.error.diagnosticRecord, schedule.error.relatedDiagnosticRecords) };

  const stored = await reminder.store.create(schedule.value);
  if (!stored.ok) return { ok: false, error: testEntityError(stored.error.code, stored.error.defaultMessage,
    stored.error.diagnosticRecord, stored.error.relatedDiagnosticRecords) };
  return { ok: true };
}
