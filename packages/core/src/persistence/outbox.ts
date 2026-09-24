import type { TenantId } from "../tenancy/index";
import { recordReference, type RecordReference } from "./lineage";
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

export type OutboxEntryId = EntityId<"OutboxEntryId">;
export type OutboxMessageType = Brand<string, "OutboxMessageType">;
export type OutboxMessageVersion = Brand<number, "OutboxMessageVersion">;
export type OutboxDeliveryPolicy = Brand<string, "OutboxDeliveryPolicy">;

export interface OutboxEntry {
  readonly id: OutboxEntryId;
  readonly subject: RecordReference;
  readonly messageType: OutboxMessageType;
  readonly messageVersion: OutboxMessageVersion;
  readonly deliveryPolicy: OutboxDeliveryPolicy;
  readonly createdAt: ISODateTime;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly causationId?: CausationId;
}

export const currentOutboxMessageVersion: OutboxMessageVersion = brand<number, "OutboxMessageVersion">(1);

export function outboxEntryId(value: string): OutboxEntryId {
  return entityId<"OutboxEntryId">(value);
}

export function outboxMessageType(value: string): Result<OutboxMessageType, PersistenceError> {
  if (!outboxNamePattern.test(value)) {
    return err(
      persistenceError({
        code: "PERSISTENCE_INVALID_OUTBOX_MESSAGE_TYPE",
        defaultMessage: "Outbox message type must use dot-separated lowercase segments.",
        messageKey: "persistence.outbox.message_type.invalid",
        params: { messageType: value },
      }),
    );
  }

  return ok(brand<string, "OutboxMessageType">(value));
}

export function outboxMessageVersion(value: number): Result<OutboxMessageVersion, PersistenceError> {
  if (!Number.isInteger(value) || value <= 0) {
    return err(
      persistenceError({
        code: "PERSISTENCE_INVALID_OUTBOX_MESSAGE_VERSION",
        defaultMessage: "Outbox message version must be a positive integer.",
        messageKey: "persistence.outbox.message_version.invalid",
        params: { version: String(value) },
      }),
    );
  }

  return ok(brand<number, "OutboxMessageVersion">(value));
}

export function outboxDeliveryPolicy(value: string): Result<OutboxDeliveryPolicy, PersistenceError> {
  if (!outboxNamePattern.test(value)) {
    return err(
      persistenceError({
        code: "PERSISTENCE_INVALID_OUTBOX_DELIVERY_POLICY",
        defaultMessage: "Outbox delivery policy must use dot-separated lowercase segments.",
        messageKey: "persistence.outbox.delivery_policy.invalid",
        params: { deliveryPolicy: value },
      }),
    );
  }

  return ok(brand<string, "OutboxDeliveryPolicy">(value));
}

export function outboxEntry(input: {
  readonly id: OutboxEntryId;
  readonly subject: RecordReference;
  readonly messageType: OutboxMessageType;
  readonly messageVersion?: OutboxMessageVersion;
  readonly deliveryPolicy: OutboxDeliveryPolicy;
  readonly createdAt: ISODateTime;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly causationId?: CausationId;
}): OutboxEntry {
  return {
    id: input.id,
    subject: recordReference(input.subject),
    messageType: input.messageType,
    messageVersion: input.messageVersion ?? currentOutboxMessageVersion,
    deliveryPolicy: input.deliveryPolicy,
    createdAt: input.createdAt,
    ...(input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    ...(input.causationId === undefined ? {} : { causationId: input.causationId }),
  };
}

const outboxNamePattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$/;
