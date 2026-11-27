import { ok, type Result } from "@kanbien/core/shared";
import { testEntityCreationConflict, testEntityWriteConflict, type TestEntityError } from "../contract/errors";
import type { TestEntity, TestEntityId, TestEntityStatus } from "../contract/types";
import { testEntityStatusIndexKey } from "../domain/entity";
import type { TestEntityRepository } from "./repository";

/** Local test double only; it does not claim durable storage or target readiness. */
export function inMemoryTestEntityRepository(initial: readonly TestEntity[] = []): TestEntityRepository {
  const entries = new Map<TestEntityId, TestEntity>(initial.map((entity) => [entity.id, copy(entity)]));
  return {
    async get(id) { const entity = entries.get(id); return entity === undefined ? null : copy(entity); },
    async create(entity) { if (entries.has(entity.id)) return { ok: false, error: testEntityCreationConflict() }; const stored = copy(entity); entries.set(entity.id, stored); return ok(copy(stored)); },
    async save(entity, expected): Promise<Result<TestEntity, TestEntityError>> {
      const current = entries.get(entity.id);
      if (current === undefined || !sameSnapshot(current, expected)) return { ok: false, error: testEntityWriteConflict() };
      const stored = copy(entity); entries.set(entity.id, stored); return ok(copy(stored));
    },
    async listByStatus(status) {
      return [...entries.values()].filter((entity) => entity.lifecycle.state === "active" && entity.status === status)
        .sort((left, right) => testEntityStatusIndexKey(left)[1].localeCompare(testEntityStatusIndexKey(right)[1])).map(copy);
    },
    async purgeArchivedDeleted(input) {
      const entity = entries.get(input.id);
      if (entity === undefined || entity.visibility !== "archived" || entity.lifecycle.state !== "deleted") return ok(false);
      if (entity.lifecycle.deletedAt !== input.deletedAt || Date.parse(input.asOf) <= Date.parse(entity.lifecycle.deletedAt) + input.retentionWindowMs
        || Date.parse(input.asOf) <= Date.parse(entity.lifecycle.restoreEligibleUntil)) return ok(false);
      entries.delete(input.id);
      return ok(true);
    },
  };
}
function sameSnapshot(left: TestEntity, right: TestEntity): boolean {
  const scalarKeys = ["id", "integerValue", "uuidValue", "occurredAt", "label", "status", "enabled", "description", "reviewedAt", "visibility", "createdAt", "updatedAt"] as const;
  if (scalarKeys.some(key => left[key] !== right[key])) return false;
  if (JSON.stringify(left.categories) !== JSON.stringify(right.categories) || JSON.stringify(left.notes) !== JSON.stringify(right.notes)
    || JSON.stringify(left.secondaryCategories) !== JSON.stringify(right.secondaryCategories)) return false;
  if (left.lifecycle.state !== right.lifecycle.state) return false;
  return left.lifecycle.state === "active" || (right.lifecycle.state === "deleted"
    && left.lifecycle.deletedAt === right.lifecycle.deletedAt && left.lifecycle.restoreEligibleUntil === right.lifecycle.restoreEligibleUntil
    && left.lifecycle.retentionPolicy === right.lifecycle.retentionPolicy);
}
function copy(entity: TestEntity): TestEntity { return { ...entity, categories: [...entity.categories], notes: [...entity.notes], ...(entity.secondaryCategories === null ? { secondaryCategories: null } : { secondaryCategories: [...entity.secondaryCategories] }), lifecycle: entity.lifecycle.state === "active" ? { state: "active" } : { ...entity.lifecycle } }; }
