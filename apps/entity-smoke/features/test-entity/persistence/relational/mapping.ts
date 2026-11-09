import { entityId, isoDateTime, isoDateTimeFromDate, ok, uuid, type Result } from "@kanbien/core/shared";
import { recordRetentionPolicyReference, type RecordLifecycle } from "@kanbien/core/persistence";
import { createTestEntitySchema } from "../../contract/schemas";
import { testEntityError, type TestEntityError } from "../../contract/errors";
import { testEntityStoredRecordDiagnostic } from "../../contract/diagnostics";
import { createDiagnosticRecord } from "@kanbien/core/diagnostics";
import type { TestEntity } from "../../contract/types";

export function testEntityValues(entity: TestEntity): readonly unknown[] {
  return [entity.id, entity.integerValue, entity.uuidValue, entity.occurredAt,
    entity.label, entity.status, entity.enabled, JSON.stringify(entity.categories),
    JSON.stringify(entity.notes), entity.description, entity.reviewedAt,
    entity.secondaryCategories === null ? null : JSON.stringify(entity.secondaryCategories),
    entity.visibility, JSON.stringify(entity.lifecycle), entity.createdAt, entity.updatedAt];
}

/** PostgreSQL bigint arrives as text and timestamps as Date. Do not cast an
 * unvalidated provider row into the feature's public branded contract. */
export function testEntityFromRow(row: Readonly<Record<string, unknown>>): Result<TestEntity, TestEntityError> {
  const id = typeof row.id === "string" ? uuid(row.id) : undefined;
  if (!id?.ok) return rejected("id");
  const integerValue = typeof row.integer_value === "string" && /^-?\d+$/.test(row.integer_value)
    ? Number(row.integer_value) : row.integer_value;
  const input = { integerValue, uuidValue: row.uuid_value, occurredAt: dateText(row.occurred_at),
    label: row.label, status: row.status, enabled: row.enabled, categories: row.categories,
    notes: row.notes, description: row.description,
    reviewedAt: row.reviewed_at === null ? null : dateText(row.reviewed_at),
    secondaryCategories: row.secondary_categories };
  if (!createTestEntitySchema.validate(input)) return rejected("attributes");
  if (row.visibility !== "active" && row.visibility !== "archived") return rejected("visibility");
  const createdAt = isoDateTime(dateText(row.created_at) ?? "");
  const updatedAt = isoDateTime(dateText(row.updated_at) ?? "");
  if (!createdAt.ok || !updatedAt.ok) return rejected("timestamps");
  const lifecycle = lifecycleFromRow(row.lifecycle);
  if (lifecycle === undefined) return rejected("lifecycle");
  const uuidValue = uuid(input.uuidValue); const occurredAt = isoDateTime(input.occurredAt);
  const reviewedAt = input.reviewedAt === null ? null : isoDateTime(input.reviewedAt);
  if (!uuidValue.ok || !occurredAt.ok || (reviewedAt !== null && !reviewedAt.ok)) return rejected("attributes");
  return ok({ ...input, id: entityId<"TestEntity">(id.value), uuidValue: uuidValue.value,
    occurredAt: occurredAt.value, reviewedAt: reviewedAt === null ? null : reviewedAt.value,
    visibility: row.visibility, lifecycle, createdAt: createdAt.value, updatedAt: updatedAt.value });
}

function dateText(value: unknown): string | undefined {
  if (value instanceof Date) return Number.isFinite(value.getTime()) ? isoDateTimeFromDate(value) : undefined;
  return typeof value === "string" ? value : undefined;
}

function lifecycleFromRow(value: unknown): RecordLifecycle | undefined {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return undefined;
  const row = value as Record<string, unknown>;
  if (row.state === "active") return { state: "active" };
  if (row.state !== "deleted" || typeof row.deletedAt !== "string" || typeof row.restoreEligibleUntil !== "string" || typeof row.retentionPolicy !== "string") return undefined;
  const deletedAt = isoDateTime(row.deletedAt); const restoreEligibleUntil = isoDateTime(row.restoreEligibleUntil);
  const retentionPolicy = recordRetentionPolicyReference(row.retentionPolicy);
  if (!deletedAt.ok || !restoreEligibleUntil.ok || !retentionPolicy.ok || Date.parse(restoreEligibleUntil.value) < Date.parse(deletedAt.value)) return undefined;
  return { state: "deleted", deletedAt: deletedAt.value, restoreEligibleUntil: restoreEligibleUntil.value, retentionPolicy: retentionPolicy.value };
}

export function rejectedStoredTestEntity(): Result<never, TestEntityError> { return rejected("row-count"); }

function rejected(field: "id" | "attributes" | "visibility" | "timestamps" | "lifecycle" | "row-count"): Result<never, TestEntityError> {
  const record = createDiagnosticRecord(testEntityStoredRecordDiagnostic, { field, reason: "invalid-shape", effect: "not-returned" });
  if (!record.ok) throw new TypeError("TEST_ENTITY_DIAGNOSTIC_INVALID");
  return { ok: false, error: testEntityError("TEST_ENTITY_STORED_RECORD_INVALID", "The stored test entity could not be read safely.", record.value) };
}
