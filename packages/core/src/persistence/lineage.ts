import type { TenantId } from "../tenancy/index";
import {
  brand,
  entityId,
  err,
  ok,
  type Brand,
  type CausationId,
  type CorrelationId,
  type EntityId,
  type ISODateTime,
  type Result,
} from "../shared/index";
import { persistenceError, type PersistenceError } from "./errors";
import { corePersistenceValidationRecord, type CorePersistenceValidationDetail } from "./diagnostics";

export type RecordChangeId = EntityId<"RecordChangeId">;
export type RecordKind = Brand<string, "RecordKind">;
export type RecordId = Brand<string, "RecordId">;
export type RecordRevision = Brand<number, "RecordRevision">;
export type RecordChangeFieldName = Brand<string, "RecordChangeFieldName">;
export type RecordChangeAction = "created" | "updated" | "deleted" | "restored";
export type RecordChangeActorKind = "principal" | "system";

export interface RecordReference {
  readonly kind: RecordKind;
  readonly id: RecordId;
}

export interface RecordChangeActor {
  readonly kind: RecordChangeActorKind;
  readonly id: string;
}

export interface RecordChange {
  readonly id: RecordChangeId;
  readonly record: RecordReference;
  readonly revision: RecordRevision;
  readonly action: RecordChangeAction;
  readonly occurredAt: ISODateTime;
  readonly tenantId?: TenantId;
  readonly actor?: RecordChangeActor;
  readonly correlationId?: CorrelationId;
  readonly causationId?: CausationId;
  readonly changedFields?: readonly RecordChangeFieldName[];
}

export const recordChangeActions: readonly RecordChangeAction[] = [
  "created",
  "updated",
  "deleted",
  "restored",
];

export function recordChangeId(value: string): RecordChangeId {
  return entityId<"RecordChangeId">(value);
}

export function recordKind(value: string): Result<RecordKind, PersistenceError> {
  if (!recordKindPattern.test(value)) {
    return err(invalidLineageError("Record kind must use lowercase identifier segments.", "persistence.lineage.record_kind.invalid", "record-kind", "kind", "invalid-format", { kind: value }));
  }

  return ok(brand<string, "RecordKind">(value));
}

export function recordId(value: string): Result<RecordId, PersistenceError> {
  if (value.length === 0) {
    return err(invalidLineageError("Record id must be a non-empty trimmed string.", "persistence.lineage.record_id.invalid", "record-id", "id", "empty"));
  }
  if (value.trim() !== value) {
    return err(invalidLineageError("Record id must be a non-empty trimmed string.", "persistence.lineage.record_id.invalid", "record-id", "id", "untrimmed"));
  }

  return ok(brand<string, "RecordId">(value));
}

export function recordReference(input: {
  readonly kind: RecordKind;
  readonly id: RecordId;
}): RecordReference {
  return { kind: input.kind, id: input.id };
}

export function recordRevision(value: number): Result<RecordRevision, PersistenceError> {
  if (!Number.isInteger(value)) {
    return err(invalidLineageError("Record revision must be a positive integer.", "persistence.lineage.revision.invalid", "record-revision", "revision", "not-integer", { revision: String(value) }));
  }
  if (value <= 0) {
    return err(invalidLineageError("Record revision must be a positive integer.", "persistence.lineage.revision.invalid", "record-revision", "revision", "not-positive", { revision: String(value) }));
  }

  return ok(brand<number, "RecordRevision">(value));
}

export function recordChangeFieldName(value: string): Result<RecordChangeFieldName, PersistenceError> {
  if (!recordChangeFieldNamePattern.test(value)) {
    return err(invalidLineageError("Record change field name must use lowercase identifier segments.", "persistence.lineage.field_name.invalid", "change-field", "field-name", "invalid-format", { field: value }));
  }

  return ok(brand<string, "RecordChangeFieldName">(value));
}

export function recordChangeActor(input: {
  readonly kind: RecordChangeActorKind;
  readonly id: string;
}): Result<RecordChangeActor, PersistenceError> {
  if (input.id.length === 0) {
    return err(invalidLineageError("Record change actor id must be a non-empty trimmed string.", "persistence.lineage.actor.invalid", "change-actor", "actor-id", "empty"));
  }
  if (input.id.trim() !== input.id) {
    return err(invalidLineageError("Record change actor id must be a non-empty trimmed string.", "persistence.lineage.actor.invalid", "change-actor", "actor-id", "untrimmed"));
  }

  return ok({ kind: input.kind, id: input.id });
}

export function recordChange(input: {
  readonly id: RecordChangeId;
  readonly record: RecordReference;
  readonly revision: RecordRevision;
  readonly action: RecordChangeAction;
  readonly occurredAt: ISODateTime;
  readonly tenantId?: TenantId;
  readonly actor?: RecordChangeActor;
  readonly correlationId?: CorrelationId;
  readonly causationId?: CausationId;
  readonly changedFields?: readonly RecordChangeFieldName[];
}): Result<RecordChange, PersistenceError> {
  const changedFields = input.changedFields === undefined ? undefined : [...input.changedFields];
  if (changedFields !== undefined && changedFields.length > maximumRecordChangeFields) {
    return err(invalidLineageError("Record change must not list more than 32 changed fields.", "persistence.lineage.fields.too_many", "record-change", "changed-fields", "too-many", { maximum: String(maximumRecordChangeFields) }));
  }

  if (changedFields !== undefined && new Set(changedFields).size !== changedFields.length) {
    return err(invalidLineageError("Record change fields must not contain duplicates.", "persistence.lineage.fields.duplicate", "record-change", "changed-fields", "duplicate"));
  }

  return ok({
    id: input.id,
    record: recordReference(input.record),
    revision: input.revision,
    action: input.action,
    occurredAt: input.occurredAt,
    ...(input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
    ...(input.actor === undefined ? {} : { actor: { ...input.actor } }),
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    ...(input.causationId === undefined ? {} : { causationId: input.causationId }),
    ...(changedFields === undefined || changedFields.length === 0 ? {} : { changedFields }),
  });
}

const maximumRecordChangeFields = 32;
const recordKindPattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*$/;
const recordChangeFieldNamePattern = /^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$/;

function invalidLineageError(
  defaultMessage: string,
  key: string,
  operation: CorePersistenceValidationDetail["operation"],
  field: CorePersistenceValidationDetail["field"],
  reason: CorePersistenceValidationDetail["reason"],
  params?: Readonly<Record<string, string>>,
): PersistenceError {
  return persistenceError({
    code: "PERSISTENCE_INVALID_LINEAGE",
    defaultMessage,
    messageKey: key,
    diagnosticRecord: corePersistenceValidationRecord({ operation, field, reason }),
    ...(params === undefined ? {} : { params }),
  });
}
