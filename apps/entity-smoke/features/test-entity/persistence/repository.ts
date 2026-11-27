import type { ISODateTime, Result } from "@kanbien/core/shared";
import type { TestEntityError } from "../contract/errors";
import type { TestEntity, TestEntityId, TestEntityStatus } from "../contract/types";

/** App-owned access patterns: ordinary reads exclude deleted entities; indexed list is status then created time. */
export interface TestEntityRepository {
  get(id: TestEntityId): Promise<TestEntity | null>;
  create(entity: TestEntity): Promise<Result<TestEntity, TestEntityError>>;
  /** Save only if the row still equals the snapshot read for this operation. */
  save(entity: TestEntity, expected: TestEntity): Promise<Result<TestEntity, TestEntityError>>;
  listByStatus(status: TestEntityStatus): Promise<readonly TestEntity[]>;
  /** Re-check this deletion generation, retention and recovery at the mutation boundary. */
  purgeArchivedDeleted(input: TestEntityPurgeCondition): Promise<Result<boolean, TestEntityError>>;
}

export interface TestEntityPurgeCondition {
  readonly id: TestEntityId;
  readonly deletedAt: ISODateTime;
  readonly asOf: ISODateTime;
  readonly retentionWindowMs: number;
}
