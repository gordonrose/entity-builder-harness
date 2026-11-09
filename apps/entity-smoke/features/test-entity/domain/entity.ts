import { activeRecordLifecycle, isRecordLifecycleActive, logicallyDeleteRecord, recordPurgeEligibility, restoreLogicallyDeletedRecord, type RecordLifecyclePolicy, type RecordPurgeEligibility } from "@kanbien/core/persistence";
import { entityId, isoDateTime, isoDateTimeFromDate, uuid, type Clock, type Result, type UuidGenerator } from "@kanbien/core/shared";
import { testEntityError, type TestEntityError } from "../contract/errors";
import { createTestEntitySchema, updateTestEntitySchema } from "../contract/schemas";
import type { CreateTestEntityInput, TestEntity, TestEntityId, TestEntityStatus, UpdateTestEntityInput } from "../contract/types";

export interface TestEntityCreationDependencies { readonly clock: Clock; readonly uuidGenerator: UuidGenerator; }

export function createTestEntity(input: CreateTestEntityInput, deps: TestEntityCreationDependencies): Result<TestEntity, TestEntityError> {
  const validation = createTestEntitySchema.explain(input);
  if (!validation.valid) return { ok: false, error: testEntityError("TEST_ENTITY_VALIDATION_FAILED", "Test entity input is invalid.", createTestEntitySchema.diagnose?.(input)) };
  const generated = deps.uuidGenerator.generate();
  if (!generated.ok) return { ok: false, error: testEntityError("TEST_ENTITY_ID_GENERATION_FAILED", "A test entity ID could not be created.", generated.error.diagnosticRecord, generated.error.relatedDiagnosticRecords) };
  const now = isoDateTimeFromDate(deps.clock.now());
  return { ok: true, value: {
    id: entityId<"TestEntity">(generated.value), integerValue: input.integerValue, uuidValue: required(uuid(input.uuidValue)),
    occurredAt: required(isoDateTime(input.occurredAt)), label: input.label.trim(), status: input.status, enabled: input.enabled,
    categories: [...input.categories], notes: [...input.notes], description: input.description,
    reviewedAt: input.reviewedAt === null ? null : required(isoDateTime(input.reviewedAt)),
    secondaryCategories: input.secondaryCategories === null ? null : [...input.secondaryCategories],
    visibility: "active", lifecycle: activeRecordLifecycle(), createdAt: now, updatedAt: now,
  } };
}

export function updateTestEntity(current: TestEntity, input: UpdateTestEntityInput, clock: Clock): Result<TestEntity, TestEntityError> {
  const validation = updateTestEntitySchema.explain(input);
  if (!validation.valid) return { ok: false, error: testEntityError("TEST_ENTITY_VALIDATION_FAILED", "Test entity update is invalid.", updateTestEntitySchema.diagnose?.(input)) };
  return { ok: true, value: {
    ...current, ...(input.integerValue === undefined ? {} : { integerValue: input.integerValue }),
    ...(input.uuidValue === undefined ? {} : { uuidValue: required(uuid(input.uuidValue)) }),
    ...(input.occurredAt === undefined ? {} : { occurredAt: required(isoDateTime(input.occurredAt)) }),
    ...(input.label === undefined ? {} : { label: input.label.trim() }), ...(input.status === undefined ? {} : { status: input.status }),
    ...(input.enabled === undefined ? {} : { enabled: input.enabled }), ...(input.categories === undefined ? {} : { categories: [...input.categories] }),
    ...(input.notes === undefined ? {} : { notes: [...input.notes] }), ...(input.description === undefined ? {} : { description: input.description }),
    ...(input.reviewedAt === undefined ? {} : { reviewedAt: input.reviewedAt === null ? null : required(isoDateTime(input.reviewedAt)) }),
    ...(input.secondaryCategories === undefined ? {} : { secondaryCategories: input.secondaryCategories === null ? null : [...input.secondaryCategories] }),
    updatedAt: isoDateTimeFromDate(clock.now()),
  } };
}

export function archiveTestEntity(current: TestEntity, clock: Clock): Result<TestEntity, TestEntityError> {
  if (!isRecordLifecycleActive(current.lifecycle)) return { ok: false, error: testEntityError("TEST_ENTITY_DELETED", "A logically deleted test entity cannot be archived.") };
  if (current.visibility === "archived") return { ok: false, error: testEntityError("TEST_ENTITY_ALREADY_ARCHIVED", "The test entity is already archived.") };
  return { ok: true, value: { ...current, visibility: "archived", updatedAt: isoDateTimeFromDate(clock.now()) } };
}
export function restoreTestEntityArchive(current: TestEntity, clock: Clock): Result<TestEntity, TestEntityError> {
  if (current.visibility !== "archived") return { ok: false, error: testEntityError("TEST_ENTITY_NOT_ARCHIVED", "Only an archived test entity can be restored from archive.") };
  return { ok: true, value: { ...current, visibility: "active", updatedAt: isoDateTimeFromDate(clock.now()) } };
}
export function logicallyDeleteTestEntity(current: TestEntity, policy: RecordLifecyclePolicy, clock: Clock): Result<TestEntity, TestEntityError> {
  const lifecycle = logicallyDeleteRecord({ current: current.lifecycle, deletedAt: isoDateTimeFromDate(clock.now()), policy });
  return lifecycle.ok ? { ok: true, value: { ...current, lifecycle: lifecycle.value, updatedAt: isoDateTimeFromDate(clock.now()) } }
    : { ok: false, error: testEntityError(lifecycle.error.code, lifecycle.error.defaultMessage, lifecycle.error.diagnosticRecord, lifecycle.error.relatedDiagnosticRecords) };
}
export function restoreLogicallyDeletedTestEntity(current: TestEntity, clock: Clock): Result<TestEntity, TestEntityError> {
  const lifecycle = restoreLogicallyDeletedRecord({ current: current.lifecycle, restoredAt: isoDateTimeFromDate(clock.now()) });
  return lifecycle.ok ? { ok: true, value: { ...current, lifecycle: lifecycle.value, updatedAt: isoDateTimeFromDate(clock.now()) } }
    : { ok: false, error: testEntityError(lifecycle.error.code, lifecycle.error.defaultMessage, lifecycle.error.diagnosticRecord, lifecycle.error.relatedDiagnosticRecords) };
}
export function testEntityPurgeEligibility(entity: TestEntity, asOf: Date, retentionSatisfied: boolean, legalHold: boolean): RecordPurgeEligibility {
  return recordPurgeEligibility({ current: entity.lifecycle, asOf: isoDateTimeFromDate(asOf), retentionSatisfied, legalHold });
}
export function testEntityStatusIndexKey(entity: TestEntity): readonly [TestEntityStatus, string] { return [entity.status, String(entity.createdAt)]; }
function required<T>(result: Result<T>): T { if (!result.ok) throw new Error(result.error.defaultMessage); return result.value; }
