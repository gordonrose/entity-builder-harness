import type { TestEntity, TestEntityId } from "../../contract/types";
import type { TestEntityServiceDependencies } from "./dependencies";
export async function getTestEntityService(id: TestEntityId, deps: TestEntityServiceDependencies): Promise<TestEntity | null> { const entity = await deps.repository.get(id); return entity?.lifecycle.state === "active" ? entity : null; }
