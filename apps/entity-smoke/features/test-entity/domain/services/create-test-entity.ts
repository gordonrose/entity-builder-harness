import type { Result } from "@kanbien/core/shared";
import type { TestEntityError } from "../../contract/errors";
import type { CreateTestEntityInput, TestEntity } from "../../contract/types";
import { createTestEntity } from "../entity";
import type { TestEntityServiceDependencies } from "./dependencies";
export async function createTestEntityService(input: CreateTestEntityInput, deps: TestEntityServiceDependencies): Promise<Result<TestEntity, TestEntityError>> { const entity = createTestEntity(input, deps); return entity.ok ? deps.repository.create(entity.value) : entity; }
