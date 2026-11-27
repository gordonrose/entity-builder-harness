import { entityId, isoDateTimeFromDate, ok, uuid, type Result } from "@kanbien/core/shared";
import type { PlatformSchedule } from "@kanbien/platform-persistence";
import { testEntityPurgeEligibility } from "../entity";
import { testEntityExpiredPurgeDueAt, testEntityRetentionSatisfied, testEntityRetentionWindowMs } from "../retention";
import { testEntityRetentionRejected, type TestEntityError } from "../../contract/errors";
import type { TestEntityServiceDependencies } from "./dependencies";

export interface TestEntityExpiredPurgeResult {
  readonly inspected: number;
  readonly purged: number;
}

/**
 * One reminder can remove only its referenced entity and deletion generation.
 * Retain for five minutes after deletion, and only purge an archived row. The real
 * product policy belongs to its owning app; this smoke feature has no hold
 * facility, so it explicitly supplies `false` rather than silently skipping
 * the Core eligibility check.
 */
export async function purgeExpiredTestEntityService(
  schedule: PlatformSchedule,
  deps: TestEntityServiceDependencies,
): Promise<Result<TestEntityExpiredPurgeResult, TestEntityError>> {
  if (schedule.subject === undefined) return { ok: false, error: testEntityRetentionRejected("subject", "missing") };
  if (schedule.subject.kind !== "entity-smoke.test-entity") return { ok: false, error: testEntityRetentionRejected("subject", "mismatch") };
  const identity = uuid(schedule.subject.id);
  if (!identity.ok) return { ok: false, error: testEntityRetentionRejected("entity-id", "invalid-format") };
  const entity = await deps.repository.get(entityId<"TestEntity">(identity.value));
  if (entity === null) return ok({ inspected: 0, purged: 0 });
  const asOf = deps.clock.now();
  if (entity.visibility !== "archived" || entity.lifecycle.state !== "deleted"
    || testEntityExpiredPurgeDueAt(entity)?.toISOString() !== schedule.dueAt
    || testEntityPurgeEligibility(entity, asOf, testEntityRetentionSatisfied(entity, asOf), false) !== "eligible") return ok({ inspected: 1, purged: 0 });
  const removed = await deps.repository.purgeArchivedDeleted({ id: entity.id, deletedAt: entity.lifecycle.deletedAt,
    asOf: isoDateTimeFromDate(asOf), retentionWindowMs: testEntityRetentionWindowMs });
  return removed.ok ? ok({ inspected: 1, purged: removed.value ? 1 : 0 }) : removed;
}
