import type { PrincipalId, PrincipalType } from "../authn/index";
import {
  brand,
  copyJsonValue,
  entityId,
  err,
  messageKey,
  ok,
  type Brand,
  type CoreError,
  type CorrelationId,
  type EntityId,
  type ISODateTime,
  type JsonValue,
  type MessageDescriptor,
  type MessageKey,
  type MessageParams,
  type Result,
} from "../shared/index";
import type { DiagnosticDescriptor } from "../diagnostics/index";
import type { TenantId } from "../tenancy/index";

export type AuditEventId = EntityId<"AuditEventId">;
export type AuditEventType = Brand<string, "AuditEventType">;
export type AuditEventVersion = Brand<number, "AuditEventVersion">;
export type AuditActorType = PrincipalType | "anonymous" | "system";
export type AuditOutcome = "succeeded" | "denied" | "failed";
export type AuditMetadataValue = JsonValue;
export type AuditMetadata = Readonly<Record<string, AuditMetadataValue>>;

export type AuditRecordErrorCode =
  | "AUDIT_INVALID_VERSION"
  | "AUDIT_INVALID_TARGET"
  | "AUDIT_INVALID_TYPE"
  | "AUDIT_RECORD_FAILED"
  | "AUDIT_UNAVAILABLE";

export interface AuditRecordError extends CoreError {
  readonly code: AuditRecordErrorCode;
}

export interface AuditActor {
  readonly type: AuditActorType;
  readonly id?: PrincipalId;
  readonly subject?: string;
}

export interface AuditTarget {
  readonly type: string;
  readonly id: string;
  readonly parent?: AuditTarget;
}

export interface AuditEvent<TMetadata extends AuditMetadata = AuditMetadata> {
  readonly id: AuditEventId;
  readonly type: AuditEventType;
  readonly version: AuditEventVersion;
  readonly outcome: AuditOutcome;
  readonly actor: AuditActor;
  readonly tenantId?: TenantId;
  readonly occurredAt: ISODateTime;
  readonly correlationId?: CorrelationId;
  readonly target: AuditTarget;
  readonly reason?: MessageDescriptor;
  readonly metadata?: TMetadata;
}

export interface AuditRecorder {
  record(event: AuditEvent): Promise<Result<void, AuditRecordError>>;
}

export interface InMemoryAuditRecorder extends AuditRecorder {
  recordedEvents(): readonly AuditEvent[];
}

export const currentAuditEventVersion: AuditEventVersion = brand<number, "AuditEventVersion">(1);

export function auditEventId(value: string): AuditEventId {
  return entityId<"AuditEventId">(value);
}

export function auditEventType(value: string): Result<AuditEventType, AuditRecordError> {
  if (!auditEventTypePattern.test(value)) {
    return err(
      auditRecordError({
        code: "AUDIT_INVALID_TYPE",
        defaultMessage: "Audit event type must use dot-separated lowercase segments.",
        messageKey: "audit.type.invalid",
        params: { type: value },
      }),
    );
  }

  return ok(brand<string, "AuditEventType">(value));
}

export function auditEventVersion(value: number): Result<AuditEventVersion, AuditRecordError> {
  if (!Number.isInteger(value) || value <= 0) {
    return err(
      auditRecordError({
        code: "AUDIT_INVALID_VERSION",
        defaultMessage: "Audit event version must be a positive integer.",
        messageKey: "audit.version.invalid",
        params: { version: String(value) },
      }),
    );
  }

  return ok(brand<number, "AuditEventVersion">(value));
}

export function auditActor(input: {
  readonly type: AuditActorType;
  readonly id?: PrincipalId;
  readonly subject?: string;
}): AuditActor {
  return {
    type: input.type,
    ...(input.id === undefined ? {} : { id: input.id }),
    ...(input.subject === undefined ? {} : { subject: input.subject }),
  };
}

export function auditTarget(input: {
  readonly type: string;
  readonly id: string;
  readonly parent?: AuditTarget;
}): Result<AuditTarget, AuditRecordError> {
  if (!auditTargetTypePattern.test(input.type)) {
    return err(
      auditRecordError({
        code: "AUDIT_INVALID_TARGET",
        defaultMessage: "Audit target type must be a non-empty lowercase identifier.",
        messageKey: "audit.target.invalid_type",
        params: { type: input.type },
      }),
    );
  }

  if (input.id.length === 0 || input.id.trim() !== input.id) {
    return err(
      auditRecordError({
        code: "AUDIT_INVALID_TARGET",
        defaultMessage: "Audit target id must be a non-empty trimmed string.",
        messageKey: "audit.target.invalid_id",
      }),
    );
  }

  return ok({
    type: input.type,
    id: input.id,
    ...(input.parent === undefined ? {} : { parent: copyAuditTarget(input.parent) }),
  });
}

export function auditEvent<TMetadata extends AuditMetadata>(input: {
  readonly id: AuditEventId;
  readonly type: AuditEventType;
  readonly version?: AuditEventVersion;
  readonly outcome: AuditOutcome;
  readonly actor: AuditActor;
  readonly tenantId?: TenantId;
  readonly occurredAt: ISODateTime;
  readonly correlationId?: CorrelationId;
  readonly target: AuditTarget;
  readonly reason?: MessageDescriptor;
  readonly metadata?: TMetadata;
}): AuditEvent<TMetadata> {
  return {
    id: input.id,
    type: input.type,
    version: input.version ?? currentAuditEventVersion,
    outcome: input.outcome,
    actor: copyAuditActor(input.actor),
    ...(input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
    occurredAt: input.occurredAt,
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    target: copyAuditTarget(input.target),
    ...(input.reason === undefined ? {} : { reason: input.reason }),
    ...(input.metadata === undefined ? {} : { metadata: copyAuditMetadata(input.metadata) }),
  };
}

export function auditRecordError(input: {
  readonly code: AuditRecordErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  readonly details?: Readonly<Record<string, unknown>>;
}): AuditRecordError {
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
    ...(input.diagnostic === undefined ? {} : { diagnostic: input.diagnostic }),
    ...(input.details === undefined ? {} : { details: input.details }),
  };
}

export function inMemoryAuditRecorder(): InMemoryAuditRecorder {
  const recorded: AuditEvent[] = [];

  return {
    async record(event) {
      recorded.push(copyAuditEvent(event));
      return ok(undefined);
    },

    recordedEvents() {
      return recorded.map(copyAuditEvent);
    },
  };
}

export const noopAuditRecorder: AuditRecorder = {
  record: async () => ok(undefined),
};

const auditEventTypePattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$/;
const auditTargetTypePattern = /^[a-z][a-z0-9-]*$/;

function copyAuditEvent<TMetadata extends AuditMetadata>(event: AuditEvent<TMetadata>): AuditEvent<TMetadata> {
  return auditEvent(event);
}

function copyAuditActor(actor: AuditActor): AuditActor {
  return {
    type: actor.type,
    ...(actor.id === undefined ? {} : { id: actor.id }),
    ...(actor.subject === undefined ? {} : { subject: actor.subject }),
  };
}

function copyAuditTarget(target: AuditTarget): AuditTarget {
  return {
    type: target.type,
    id: target.id,
    ...(target.parent === undefined ? {} : { parent: copyAuditTarget(target.parent) }),
  };
}

function copyAuditMetadata<TMetadata extends AuditMetadata>(metadata: TMetadata): TMetadata {
  return Object.fromEntries(
    Object.entries(metadata).map(([key, value]) => [key, copyAuditMetadataValue(value)]),
  ) as TMetadata;
}

function copyAuditMetadataValue(value: AuditMetadataValue): AuditMetadataValue {
  return copyJsonValue(value, "audit metadata");
}
