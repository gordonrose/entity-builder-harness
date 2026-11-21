import type { Result } from "@kanbien/core/shared";
import { testEntityError, type TestEntityError } from "../../contract/errors";
import type { TestEntity, TestEntityId } from "../../contract/types";
import { logicallyDeleteTestEntity } from "../entity";
import type { TestEntityServiceDependencies } from "./dependencies";
export async function deleteTestEntityService(id: TestEntityId, deps: TestEntityServiceDependencies): Promise<Result<TestEntity, TestEntityError>> { const current = await deps.repository.get(id); if (current === null) return { ok: false, error: testEntityError("TEST_ENTITY_NOT_FOUND", "The test entity was not found.") }; const next = logicallyDeleteTestEntity(current, deps.lifecyclePolicy, deps.clock); return next.ok ? deps.repository.save(next.value) : next; }
