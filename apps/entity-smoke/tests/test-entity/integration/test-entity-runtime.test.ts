import { deepEqual, equal } from "node:assert/strict";
import { fixedClock, ok, type UuidGenerator, type UUID } from "@kanbien/core/shared";
import { recordLifecyclePolicy, recordRetentionPolicyReference } from "@kanbien/core/persistence";
import { assessTestEntityPurgeEligibilityService, archiveTestEntityService, createTestEntityService, deleteTestEntityService, getTestEntityService, inMemoryTestEntityRepository, listTestEntitiesService, restoreLogicallyDeletedTestEntityService, restoreTestEntityService, updateTestEntityService } from "../../../src/index";

async function main(): Promise<void> {
const generated = "a0b1c2d3-e4f5-4a67-8b90-123456789abc" as UUID;
const generator: UuidGenerator = { generate: () => ok(generated) };
const policyReference = recordRetentionPolicyReference("test-entity.retention");
if (!policyReference.ok) throw new Error("Expected policy reference.");
const policy = recordLifecyclePolicy({ recoveryWindowMs: 60_000, retentionPolicy: policyReference.value, legalHoldCheckRequired: true });
if (!policy.ok) throw new Error("Expected lifecycle policy.");
const deps = { repository: inMemoryTestEntityRepository(), clock: fixedClock(new Date("2026-11-06T12:00:00Z")), uuidGenerator: generator, lifecyclePolicy: policy.value };
const input = { integerValue: 7, uuidValue: "b0b1c2d3-e4f5-4a67-8b90-123456789abc", occurredAt: "2026-11-01T10:00:00Z", label: "  First record  ", status: "draft" as const, enabled: true, categories: ["alpha"] as const, notes: ["note"], description: null, reviewedAt: null, secondaryCategories: null };
const created = await createTestEntityService(input, deps);
equal(created.ok, true); if (!created.ok) throw new Error("Expected creation to succeed.");
equal(created.value.id, generated); equal(created.value.label, "First record"); equal(created.value.description, null);
const listed = await listTestEntitiesService("draft", deps); equal(listed.length, 1);
const updated = await updateTestEntityService(created.value.id, { description: "kept", secondaryCategories: [], reviewedAt: "2026-11-06T13:00:00Z" }, deps);
equal(updated.ok, true); if (!updated.ok) throw new Error("Expected update to succeed."); deepEqual(updated.value.secondaryCategories, []);
const archived = await archiveTestEntityService(created.value.id, deps); equal(archived.ok, true);
const unarchived = await restoreTestEntityService(created.value.id, deps); equal(unarchived.ok, true);
const deleted = await deleteTestEntityService(created.value.id, deps); equal(deleted.ok, true);
equal(await getTestEntityService(created.value.id, deps), null);
const eligibility = await assessTestEntityPurgeEligibilityService(created.value.id, { asOf: new Date("2026-11-06T12:00:30Z"), retentionSatisfied: true, legalHold: false }, deps);
equal(eligibility, "within-recovery-window");
const restored = await restoreLogicallyDeletedTestEntityService(created.value.id, deps); equal(restored.ok, true);
const invalid = await createTestEntityService({ ...input, uuidValue: "bad" }, deps); equal(invalid.ok, false);
// A duplicate generator output is a conflict, never an upsert. Concurrent
// callers of the local double must have the same preservation semantics.
const collisionRepository = inMemoryTestEntityRepository();
const collisionDeps = { ...deps, repository: collisionRepository };
const concurrent = await Promise.all([
  createTestEntityService({ ...input, label: "original" }, collisionDeps),
  createTestEntityService({ ...input, label: "must not overwrite" }, collisionDeps),
]);
equal(concurrent.filter(result => result.ok).length, 1);
equal(concurrent[0]!.ok, true); equal(concurrent[1]!.ok, false);
if (concurrent[0]!.ok && !concurrent[1]!.ok) {
  equal(concurrent[1]!.error.code, "TEST_ENTITY_ID_CONFLICT");
  deepEqual(concurrent[1]!.error.diagnosticRecord, {
    schema: "core/diagnostic-record/v1", code: "entity-smoke.test-entity.identifier-conflict", definitionVersion: 1,
    detail: { operation: "create", effect: "not-created" },
  });
  deepEqual(await collisionRepository.get(concurrent[0]!.value.id), concurrent[0]!.value);
  const empty = inMemoryTestEntityRepository();
  const missingSave = await empty.save(concurrent[0]!.value);
  equal(missingSave.ok, false);
  if (!missingSave.ok) equal(missingSave.error.code, "TEST_ENTITY_NOT_FOUND");
  equal(await empty.get(concurrent[0]!.value.id), null, "saving cannot recreate a missing record");
}
console.log("apps/entity-smoke test-entity runtime test passed.");
}
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
