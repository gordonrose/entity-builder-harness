import type { Result } from "@kanbien/core/shared";
import type { TestEntityError } from "../contract/errors";
import type { TestEntity, TestEntityId, TestEntityStatus } from "../contract/types";

/** App-owned access patterns: ordinary reads exclude deleted entities; indexed list is status then created time. */
export interface TestEntityRepository {
  get(id: TestEntityId): Promise<TestEntity | null>;
  create(entity: TestEntity): Promise<Result<TestEntity, TestEntityError>>;
  save(entity: TestEntity): Promise<Result<TestEntity, TestEntityError>>;
  listByStatus(status: TestEntityStatus): Promise<readonly TestEntity[]>;
}
