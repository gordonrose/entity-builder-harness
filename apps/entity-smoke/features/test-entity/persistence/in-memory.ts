import { ok, type Result } from "@kanbien/core/shared";
import { testEntityCreationConflict, testEntityError, type TestEntityError } from "../contract/errors";
import type { TestEntity, TestEntityId, TestEntityStatus } from "../contract/types";
import { testEntityStatusIndexKey } from "../domain/entity";
import type { TestEntityRepository } from "./repository";

/** Local test double only; it does not claim durable storage or target readiness. */
export function inMemoryTestEntityRepository(initial: readonly TestEntity[] = []): TestEntityRepository {
  const entries = new Map<TestEntityId, TestEntity>(initial.map((entity) => [entity.id, copy(entity)]));
  return {
    async get(id) { const entity = entries.get(id); return entity === undefined ? null : copy(entity); },
    async create(entity) { if (entries.has(entity.id)) return { ok: false, error: testEntityCreationConflict() }; const stored = copy(entity); entries.set(entity.id, stored); return ok(copy(stored)); },
    async save(entity): Promise<Result<TestEntity, TestEntityError>> { if (!entries.has(entity.id)) return { ok: false, error: testEntityError("TEST_ENTITY_NOT_FOUND", "The test entity was not found.") }; const stored = copy(entity); entries.set(entity.id, stored); return ok(copy(stored)); },
    async listByStatus(status) {
      return [...entries.values()].filter((entity) => entity.lifecycle.state === "active" && entity.status === status)
        .sort((left, right) => testEntityStatusIndexKey(left)[1].localeCompare(testEntityStatusIndexKey(right)[1])).map(copy);
    },
  };
}
function copy(entity: TestEntity): TestEntity { return { ...entity, categories: [...entity.categories], notes: [...entity.notes], ...(entity.secondaryCategories === null ? { secondaryCategories: null } : { secondaryCategories: [...entity.secondaryCategories] }), lifecycle: entity.lifecycle.state === "active" ? { state: "active" } : { ...entity.lifecycle } }; }
