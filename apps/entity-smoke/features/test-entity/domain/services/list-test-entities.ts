import type { TestEntity, TestEntityStatus } from "../../contract/types";
import type { TestEntityServiceDependencies } from "./dependencies";
export function listTestEntitiesService(status: TestEntityStatus, deps: TestEntityServiceDependencies): Promise<readonly TestEntity[]> { return deps.repository.listByStatus(status); }
