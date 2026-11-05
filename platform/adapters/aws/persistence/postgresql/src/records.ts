import {
  outboxEntry,
  outboxEntryId,
  outboxDeliveryPolicy,
  outboxMessageType,
  outboxMessageVersion,
  recordChange,
  recordChangeActor,
  recordChangeFieldName,
  recordChangeId,
  recordId,
  recordKind,
  recordReference,
  recordRevision,
  type OutboxEntry,
  type RecordChangeFieldName,
  type RecordChange,
} from "@kanbien/core/persistence";
import { tenantId } from "@kanbien/core/tenancy";
import { causationId, correlationId, isoDateTimeFromDate } from "@kanbien/core/shared";
import {
  platformOutboxRecord,
  platformPersistenceAttempt,
  platformPersistenceFence,
  platformPersistenceLease,
  platformPersistenceLeaseOwner,
  platformProcessingRecord,
  type PlatformOutboxRecord,
  type PlatformProcessingRecord,
} from "@kanbien/platform-persistence";
import type { PostgreSqlStatement } from "./connection";
import { postgreSqlIdentifier } from "./configuration/index";
import { localRejection, type StoredObservation } from "./observations";
import type { PlatformPersistenceDiagnosticOptions, PersistenceStoredRecordDetail } from "@kanbien/platform-persistence";

export interface PostgreSqlOutboxRow {
  readonly id: string;
  readonly subject_kind: string;
  readonly subject_id: string;
  readonly message_type: string;
  readonly message_version: number;
  readonly delivery_policy: string;
  readonly created_at: Date;
  readonly tenant_id: string | null;
  readonly correlation_id: string | null;
  readonly causation_id: string | null;
  readonly state: "pending" | "leased" | "published";
  readonly attempt: number;
  readonly lease_owner: string | null;
  readonly lease_fence: number | null;
  readonly lease_acquired_at: Date | null;
  readonly lease_expires_at: Date | null;
  readonly published_at: Date | null;
}

export interface PostgreSqlProcessingRow {
  readonly outbox_entry_id: string;
  readonly state: "claimed" | "retry-eligible" | "completed";
  readonly attempt: number;
  readonly lease_owner: string | null;
  readonly lease_fence: number | null;
  readonly lease_acquired_at: Date | null;
  readonly lease_expires_at: Date | null;
  readonly released_at: Date | null;
  readonly completion_outcome: "succeeded" | "terminal-failure" | null;
  readonly completed_at: Date | null;
}

export interface PostgreSqlLineageRow {
  readonly id: string;
  readonly record_kind: string;
  readonly record_id: string;
  readonly revision: number;
  readonly action: "created" | "updated" | "deleted" | "restored";
  readonly occurred_at: Date;
  readonly tenant_id: string | null;
  readonly actor_kind: "principal" | "system" | null;
  readonly actor_id: string | null;
  readonly correlation_id: string | null;
  readonly causation_id: string | null;
  readonly changed_fields: readonly string[] | null;
}

export function outboxInsertStatement(schema: string, entry: OutboxEntry): PostgreSqlStatement {
  return {
    text: `INSERT INTO ${relation(schema, "platform_outbox")} (id, subject_kind, subject_id, message_type, message_version, delivery_policy, created_at, tenant_id, correlation_id, causation_id, state, attempt) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'pending', 0)`,
    values: [
      String(entry.id), String(entry.subject.kind), String(entry.subject.id), String(entry.messageType), Number(entry.messageVersion), String(entry.deliveryPolicy), entry.createdAt,
      entry.tenantId === undefined ? null : String(entry.tenantId), entry.correlationId === undefined ? null : String(entry.correlationId), entry.causationId === undefined ? null : String(entry.causationId),
    ],
  };
}

export function recordChangeInsertStatement(schema: string, change: RecordChange): PostgreSqlStatement {
  return {
    text: `INSERT INTO ${relation(schema, "platform_record_change")} (id, record_kind, record_id, revision, action, occurred_at, tenant_id, actor_kind, actor_id, correlation_id, causation_id, changed_fields) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)`,
    values: [
      String(change.id), String(change.record.kind), String(change.record.id), Number(change.revision), change.action, change.occurredAt,
      change.tenantId === undefined ? null : String(change.tenantId), change.actor?.kind ?? null, change.actor?.id ?? null,
      change.correlationId === undefined ? null : String(change.correlationId), change.causationId === undefined ? null : String(change.causationId), change.changedFields === undefined ? null : change.changedFields.map(String),
    ],
  };
}

export function outboxRecordFromRow(row: PostgreSqlOutboxRow, observation?: StoredObservation, ordinal?: number): PlatformOutboxRecord | undefined {
  try {
  const kind = recordKind(row.subject_kind);
  const id = recordId(row.subject_id);
  const messageType = outboxMessageType(row.message_type);
  const messageVersion = outboxMessageVersion(row.message_version);
  const deliveryPolicy = outboxDeliveryPolicy(row.delivery_policy);
  if (!kind.ok || !id.ok || !messageType.ok || !messageVersion.ok || !deliveryPolicy.ok) {
    if (!kind.ok) observation?.issue("subject-kind", rejectionCondition(kind.error, "pattern"), ordinal);
    if (!id.ok) observation?.issue("subject-id", rejectionCondition(id.error, "invalid"), ordinal);
    if (!messageType.ok) observation?.issue("message-type", rejectionCondition(messageType.error, "pattern"), ordinal);
    if (!messageVersion.ok) observation?.issue("message-version", rejectionCondition(messageVersion.error, "invalid"), ordinal);
    if (!deliveryPolicy.ok) observation?.issue("delivery-policy", rejectionCondition(deliveryPolicy.error, "pattern"), ordinal);
    return undefined;
  }
  const entry = outboxEntry({
    id: outboxEntryId(row.id),
    subject: recordReference({ kind: kind.value, id: id.value }),
    messageType: messageType.value,
    messageVersion: messageVersion.value,
    deliveryPolicy: deliveryPolicy.value,
    createdAt: iso(row.created_at),
    ...(row.tenant_id === null ? {} : { tenantId: tenantId(row.tenant_id) }),
    ...(row.correlation_id === null ? {} : { correlationId: correlationId(row.correlation_id) }),
    ...(row.causation_id === null ? {} : { causationId: causationId(row.causation_id) }),
  });
  const attempt = platformPersistenceAttempt(row.attempt);
  if (!attempt.ok) { observation?.issue("attempt", rejectionCondition(attempt.error, "invalid"), ordinal); return undefined; }
  const lease = leaseFromRow(row, observation, ordinal);
  if (lease === undefined && row.state === "leased") { observation?.issue("lease", "required", ordinal); return undefined; }
  return platformOutboxRecord({
    entry,
    state: row.state,
    attempt: attempt.value,
    ...(lease === undefined ? {} : { lease }),
    ...(row.published_at === null ? {} : { publishedAt: iso(row.published_at) }),
  });
  } catch (cause) { observation?.threw(cause); throw cause; }
}

export function processingRecordFromRow(row: PostgreSqlProcessingRow, observation?: StoredObservation, ordinal?: number): PlatformProcessingRecord | undefined {
  try {
  const attempt = platformPersistenceAttempt(row.attempt);
  if (!attempt.ok) { observation?.issue("attempt", rejectionCondition(attempt.error, "invalid"), ordinal); return undefined; }
  const lease = leaseFromRow(row, observation, ordinal);
  if (lease === undefined && row.state === "claimed") { observation?.issue("lease", "required", ordinal); return undefined; }
  if ((row.completion_outcome === null) !== (row.completed_at === null)) { observation?.issue("completion", "nullness-mismatch", ordinal); return undefined; }
  return platformProcessingRecord({
    outboxEntryId: outboxEntryId(row.outbox_entry_id),
    state: row.state,
    attempt: attempt.value,
    ...(lease === undefined ? {} : { lease }),
    ...(row.released_at === null ? {} : { releasedAt: iso(row.released_at) }),
    ...(row.completion_outcome === null || row.completed_at === null ? {} : { completion: { outcome: row.completion_outcome, completedAt: iso(row.completed_at) } }),
  });
  } catch (cause) { observation?.threw(cause); throw cause; }
}

export function recordChangeFromRow(row: PostgreSqlLineageRow, observation?: StoredObservation, ordinal?: number): RecordChange | undefined {
  try {
  const kind = recordKind(row.record_kind);
  const id = recordId(row.record_id);
  const revision = recordRevision(row.revision);
  if (!kind.ok || !id.ok || !revision.ok) {
    if (!kind.ok) observation?.issue("record-kind", rejectionCondition(kind.error, "pattern"), ordinal);
    if (!id.ok) observation?.issue("record-id", rejectionCondition(id.error, "invalid"), ordinal);
    if (!revision.ok) observation?.issue("revision", rejectionCondition(revision.error, "invalid"), ordinal);
    return undefined;
  }
  const actor = row.actor_kind === null || row.actor_id === null ? undefined : recordChangeActor({ kind: row.actor_kind, id: row.actor_id });
  if (actor !== undefined && !actor.ok) { observation?.issue("actor", rejectionCondition(actor.error, "invalid"), ordinal); return undefined; }
  const fields = row.changed_fields === null ? undefined : row.changed_fields.map(recordChangeFieldName);
  if (fields?.some((field) => !field.ok)) { observation?.issue("changed-fields", "pattern", ordinal); return undefined; }
  const changedFields: RecordChangeFieldName[] = [];
  if (fields !== undefined) {
    for (const field of fields) {
      if (!field.ok) return undefined;
      changedFields.push(field.value);
    }
  }
  const result = recordChange({
    id: recordChangeId(row.id),
    record: recordReference({ kind: kind.value, id: id.value }),
    revision: revision.value,
    action: row.action,
    occurredAt: iso(row.occurred_at),
    ...(row.tenant_id === null ? {} : { tenantId: tenantId(row.tenant_id) }),
    ...(actor === undefined ? {} : { actor: actor.value }),
    ...(row.correlation_id === null ? {} : { correlationId: correlationId(row.correlation_id) }),
    ...(row.causation_id === null ? {} : { causationId: causationId(row.causation_id) }),
    ...(fields === undefined ? {} : { changedFields }),
  });
  if (!result.ok) observation?.issue("record-change", rejectionCondition(result.error, "invalid"), ordinal);
  return result.ok ? result.value : undefined;
  } catch (cause) { observation?.threw(cause); throw cause; }
}

export function relation(schema: string, table: string, diagnostics?: PlatformPersistenceDiagnosticOptions): string {
  if (postgreSqlIdentifier(schema) === undefined || postgreSqlIdentifier(table) === undefined) {
    const cause = new TypeError("PostgreSQL relation identifiers must be reviewed lowercase SQL identifiers.");
    Object.assign(cause, localRejection(diagnostics, { operation: "validate-identifier", field: "identifier", condition: "pattern", phase: "preflight", effect: "not-started" }));
    throw cause;
  }
  return `"${schema}"."${table}"`;
}

function leaseFromRow(row: Pick<PostgreSqlOutboxRow | PostgreSqlProcessingRow, "lease_owner" | "lease_fence" | "lease_acquired_at" | "lease_expires_at" | "attempt">, observation?: StoredObservation, ordinal?: number) {
  if (row.lease_owner === null && row.lease_fence === null && row.lease_acquired_at === null && row.lease_expires_at === null) return undefined;
  if (row.lease_owner === null || row.lease_fence === null || row.lease_acquired_at === null || row.lease_expires_at === null) { observation?.issue("lease", "partial", ordinal); return undefined; }
  const owner = platformPersistenceLeaseOwner(row.lease_owner);
  const fence = platformPersistenceFence(row.lease_fence);
  const attempt = platformPersistenceAttempt(row.attempt);
  if (!owner.ok || !fence.ok || !attempt.ok) {
    if (!owner.ok) observation?.issue("owner", rejectionCondition(owner.error, "pattern"), ordinal);
    if (!fence.ok) observation?.issue("fence", rejectionCondition(fence.error, "invalid"), ordinal);
    if (!attempt.ok) observation?.issue("attempt", rejectionCondition(attempt.error, "invalid"), ordinal);
    return undefined;
  }
  const lease = platformPersistenceLease({ owner: owner.value, fence: fence.value, attempt: attempt.value, acquiredAt: iso(row.lease_acquired_at), expiresAt: iso(row.lease_expires_at) });
  if (!lease.ok) observation?.issue("expiry", "not-after-acquisition", ordinal);
  return lease.ok ? lease.value : undefined;
}

/** Read only validated output facts; never submitted row values or messages. */
function rejectionCondition(error: unknown, fallback: PersistenceStoredRecordDetail["issues"][number]["condition"]): PersistenceStoredRecordDetail["issues"][number]["condition"] {
  try {
    const record = Object.getOwnPropertyDescriptor(error, "diagnosticRecord");
    const detail = record && "value" in record ? Object.getOwnPropertyDescriptor(record.value, "detail") : undefined;
    const condition = detail && "value" in detail ? Object.getOwnPropertyDescriptor(detail.value, "condition") ?? Object.getOwnPropertyDescriptor(detail.value, "reason") : undefined;
    const value: unknown = condition && "value" in condition ? condition.value : undefined;
    if (value === "invalid-format") return "pattern";
    if (value === "not-integer" || value === "not-positive" || value === "negative" || value === "pattern" || value === "empty" || value === "untrimmed" || value === "duplicate" || value === "too-many") return value;
  } catch { /* Unavailable validator evidence does not affect decoding. */ }
  return fallback;
}

function iso(value: Date) {
  return isoDateTimeFromDate(value);
}
