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
import { postgreSqlIdentifier } from "./config";

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

export function outboxRecordFromRow(row: PostgreSqlOutboxRow): PlatformOutboxRecord | undefined {
  const kind = recordKind(row.subject_kind);
  const id = recordId(row.subject_id);
  const messageType = outboxMessageType(row.message_type);
  const messageVersion = outboxMessageVersion(row.message_version);
  const deliveryPolicy = outboxDeliveryPolicy(row.delivery_policy);
  if (!kind.ok || !id.ok || !messageType.ok || !messageVersion.ok || !deliveryPolicy.ok) return undefined;
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
  if (!attempt.ok) return undefined;
  const lease = leaseFromRow(row);
  if (lease === undefined && row.state === "leased") return undefined;
  return platformOutboxRecord({
    entry,
    state: row.state,
    attempt: attempt.value,
    ...(lease === undefined ? {} : { lease }),
    ...(row.published_at === null ? {} : { publishedAt: iso(row.published_at) }),
  });
}

export function processingRecordFromRow(row: PostgreSqlProcessingRow): PlatformProcessingRecord | undefined {
  const attempt = platformPersistenceAttempt(row.attempt);
  if (!attempt.ok) return undefined;
  const lease = leaseFromRow(row);
  if (lease === undefined && row.state === "claimed") return undefined;
  if ((row.completion_outcome === null) !== (row.completed_at === null)) return undefined;
  return platformProcessingRecord({
    outboxEntryId: outboxEntryId(row.outbox_entry_id),
    state: row.state,
    attempt: attempt.value,
    ...(lease === undefined ? {} : { lease }),
    ...(row.released_at === null ? {} : { releasedAt: iso(row.released_at) }),
    ...(row.completion_outcome === null || row.completed_at === null ? {} : { completion: { outcome: row.completion_outcome, completedAt: iso(row.completed_at) } }),
  });
}

export function recordChangeFromRow(row: PostgreSqlLineageRow): RecordChange | undefined {
  const kind = recordKind(row.record_kind);
  const id = recordId(row.record_id);
  const revision = recordRevision(row.revision);
  if (!kind.ok || !id.ok || !revision.ok) return undefined;
  const actor = row.actor_kind === null || row.actor_id === null ? undefined : recordChangeActor({ kind: row.actor_kind, id: row.actor_id });
  if (actor !== undefined && !actor.ok) return undefined;
  const fields = row.changed_fields === null ? undefined : row.changed_fields.map(recordChangeFieldName);
  if (fields?.some((field) => !field.ok)) return undefined;
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
  return result.ok ? result.value : undefined;
}

export function relation(schema: string, table: string): string {
  if (postgreSqlIdentifier(schema) === undefined || postgreSqlIdentifier(table) === undefined) {
    throw new TypeError("PostgreSQL relation identifiers must be reviewed lowercase SQL identifiers.");
  }
  return `"${schema}"."${table}"`;
}

function leaseFromRow(row: Pick<PostgreSqlOutboxRow | PostgreSqlProcessingRow, "lease_owner" | "lease_fence" | "lease_acquired_at" | "lease_expires_at" | "attempt">) {
  if (row.lease_owner === null && row.lease_fence === null && row.lease_acquired_at === null && row.lease_expires_at === null) return undefined;
  if (row.lease_owner === null || row.lease_fence === null || row.lease_acquired_at === null || row.lease_expires_at === null) return undefined;
  const owner = platformPersistenceLeaseOwner(row.lease_owner);
  const fence = platformPersistenceFence(row.lease_fence);
  const attempt = platformPersistenceAttempt(row.attempt);
  if (!owner.ok || !fence.ok || !attempt.ok) return undefined;
  const lease = platformPersistenceLease({ owner: owner.value, fence: fence.value, attempt: attempt.value, acquiredAt: iso(row.lease_acquired_at), expiresAt: iso(row.lease_expires_at) });
  return lease.ok ? lease.value : undefined;
}

function iso(value: Date) {
  return isoDateTimeFromDate(value);
}
