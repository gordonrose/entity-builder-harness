import type { EntityId, ISODateTime, UUID } from "@kanbien/core/shared";
import type { RecordLifecycle } from "@kanbien/core/persistence";

export type TestEntityId = EntityId<"TestEntity">;
export type TestEntityStatus = "draft" | "active" | "closed";
export type TestEntityCategory = "alpha" | "beta" | "gamma";
export type TestEntityVisibility = "active" | "archived";

export interface TestEntity {
  readonly id: TestEntityId;
  readonly integerValue: number;
  readonly uuidValue: UUID;
  readonly occurredAt: ISODateTime;
  readonly label: string;
  readonly status: TestEntityStatus;
  readonly enabled: boolean;
  readonly categories: readonly TestEntityCategory[];
  readonly notes: readonly string[];
  readonly description: string | null;
  readonly reviewedAt: ISODateTime | null;
  readonly secondaryCategories: readonly TestEntityCategory[] | null;
  readonly visibility: TestEntityVisibility;
  readonly lifecycle: RecordLifecycle;
  readonly createdAt: ISODateTime;
  readonly updatedAt: ISODateTime;
}

export interface CreateTestEntityInput {
  readonly integerValue: number;
  readonly uuidValue: string;
  readonly occurredAt: string;
  readonly label: string;
  readonly status: TestEntityStatus;
  readonly enabled: boolean;
  readonly categories: readonly TestEntityCategory[];
  readonly notes: readonly string[];
  readonly description: string | null;
  readonly reviewedAt: string | null;
  readonly secondaryCategories: readonly TestEntityCategory[] | null;
}

export interface UpdateTestEntityInput {
  readonly integerValue?: number;
  readonly uuidValue?: string;
  readonly occurredAt?: string;
  readonly label?: string;
  readonly status?: TestEntityStatus;
  readonly enabled?: boolean;
  readonly categories?: readonly TestEntityCategory[];
  readonly notes?: readonly string[];
  readonly description?: string | null;
  readonly reviewedAt?: string | null;
  readonly secondaryCategories?: readonly TestEntityCategory[] | null;
}
