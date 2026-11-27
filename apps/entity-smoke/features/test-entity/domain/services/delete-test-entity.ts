import type { Result } from "@kanbien/core/shared";
import { testEntityError, testEntityRetentionRejected, type TestEntityError } from "../../contract/errors";
import type { TestEntity, TestEntityId } from "../../contract/types";
import { logicallyDeleteTestEntity } from "../entity";
import type { TestEntityServiceDependencies } from "./dependencies";
import { rememberExpiredTestEntityPurge } from "./remember-expired-purge";

export async function deleteTestEntityService(id: TestEntityId, deps: TestEntityServiceDependencies): Promise<Result<TestEntity, TestEntityError>> {
  if (deps.expiredPurgeReminder !== undefined) {
    const reminder = deps.expiredPurgeReminder;
    if (deps.deletionTransaction === undefined) return { ok: false, error: testEntityRetentionRejected("transaction", "missing") };
    return deps.deletionTransaction.run(scope => deleteWithinScope(id, { ...deps, repository: scope.repository,
      expiredPurgeReminder: { jobName: reminder.jobName, store: scope.schedules } }));
  }
  return deleteWithinScope(id, deps);
}

async function deleteWithinScope(id: TestEntityId, deps: TestEntityServiceDependencies): Promise<Result<TestEntity, TestEntityError>> {
  const current = await deps.repository.get(id);
  if (current === null) return { ok: false, error: testEntityError("TEST_ENTITY_NOT_FOUND", "The test entity was not found.") };
  const next = logicallyDeleteTestEntity(current, deps.lifecyclePolicy, deps.clock);
  if (!next.ok) return next;

  // The durable composition locks this read and commits both participants together.
  const reminder = await rememberExpiredTestEntityPurge(next.value, deps);
  if (!reminder.ok) return reminder;
  return deps.repository.save(next.value, current);
}
