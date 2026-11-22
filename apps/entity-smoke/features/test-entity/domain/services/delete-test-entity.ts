import type { Result } from "@kanbien/core/shared";
import { testEntityError, type TestEntityError } from "../../contract/errors";
import type { TestEntity, TestEntityId } from "../../contract/types";
import { logicallyDeleteTestEntity } from "../entity";
import type { TestEntityServiceDependencies } from "./dependencies";
import { rememberExpiredTestEntityPurge } from "./remember-expired-purge";

export async function deleteTestEntityService(id: TestEntityId, deps: TestEntityServiceDependencies): Promise<Result<TestEntity, TestEntityError>> {
  const current = await deps.repository.get(id);
  if (current === null) return { ok: false, error: testEntityError("TEST_ENTITY_NOT_FOUND", "The test entity was not found.") };
  const next = logicallyDeleteTestEntity(current, deps.lifecyclePolicy, deps.clock);
  if (!next.ok) return next;

  // Store first. If the entity write later fails, the generic purge job merely
  // finds no eligible row; the reverse order could leave eligible data with no reminder.
  const reminder = await rememberExpiredTestEntityPurge(next.value, deps);
  if (!reminder.ok) return reminder;
  return deps.repository.save(next.value);
}
