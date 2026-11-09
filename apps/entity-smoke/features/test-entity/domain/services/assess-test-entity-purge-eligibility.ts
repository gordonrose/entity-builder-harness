import type { RecordPurgeEligibility } from "@kanbien/core/persistence";
import { testEntityError, type TestEntityError } from "../../contract/errors";
import type { TestEntityId } from "../../contract/types";
import { testEntityPurgeEligibility } from "../entity";
import type { TestEntityServiceDependencies } from "./dependencies";
export async function assessTestEntityPurgeEligibilityService(id: TestEntityId, input: { readonly asOf: Date; readonly retentionSatisfied: boolean; readonly legalHold: boolean }, deps: TestEntityServiceDependencies): Promise<RecordPurgeEligibility | TestEntityError> { const entity = await deps.repository.get(id); return entity === null ? testEntityError("TEST_ENTITY_NOT_FOUND", "The test entity was not found.") : testEntityPurgeEligibility(entity, input.asOf, input.retentionSatisfied, input.legalHold); }
