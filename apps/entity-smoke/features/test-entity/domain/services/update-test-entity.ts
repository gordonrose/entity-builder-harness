import type { Result } from "@kanbien/core/shared";
import { testEntityError, type TestEntityError } from "../../contract/errors";
import type { TestEntity, TestEntityId, UpdateTestEntityInput } from "../../contract/types";
import { updateTestEntity } from "../entity";
import type { TestEntityServiceDependencies } from "./dependencies";
export async function updateTestEntityService(id: TestEntityId, input: UpdateTestEntityInput, deps: TestEntityServiceDependencies): Promise<Result<TestEntity, TestEntityError>> { const current = await deps.repository.get(id); if (current === null || current.lifecycle.state !== "active") return { ok: false, error: testEntityError("TEST_ENTITY_NOT_FOUND", "The test entity was not found.") }; const next = updateTestEntity(current, input, deps.clock); return next.ok ? deps.repository.save(next.value) : next; }
