import { ok, type Result } from "@kanbien/core/shared";
import { testEntityPurgeEligibility } from "../entity";
import { testEntityRetentionSatisfied } from "../retention";
import type { TestEntityError } from "../../contract/errors";
import type { TestEntityServiceDependencies } from "./dependencies";

export interface TestEntityExpiredPurgeResult {
  readonly inspected: number;
  readonly purged: number;
}

/**
 * Entity Smoke's disposable cleanup rule: retain for five minutes after a
 * logical deletion, and only purge rows that were also archived.  The real
 * product policy belongs to its owning app; this smoke feature has no hold
 * facility, so it explicitly supplies `false` rather than silently skipping
 * the Core eligibility check.
 */
export async function purgeExpiredTestEntitiesService(
  deps: TestEntityServiceDependencies,
): Promise<Result<TestEntityExpiredPurgeResult, TestEntityError>> {
  const candidates = await deps.repository.listArchivedDeleted();
  let purged = 0;
  const asOf = deps.clock.now();

  for (const entity of candidates) {
    const eligibility = testEntityPurgeEligibility(entity, asOf, testEntityRetentionSatisfied(entity, asOf), false);
    if (eligibility !== "eligible") continue;
    const removed = await deps.repository.purgeArchivedDeleted(entity.id);
    if (!removed.ok) return removed;
    if (removed.value) purged++;
  }

  return ok({ inspected: candidates.length, purged });
}
