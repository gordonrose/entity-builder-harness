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
import { parseRelatedDiagnosticRecords, type DiagnosticDescriptor, type DiagnosticRecord } from "../diagnostics/index";
import type { TenantId } from "../tenancy/index";
import { AuditObservation } from "./observations";
import type { CoreAuditDiagnosticOptions, CoreAuditErrorEvidence } from "./diagnostics";
export { coreAuditDiagnosticDefinitions, coreAuditValidationDiagnostic, coreAuditBoundaryDiagnostic } from "./diagnostics";
export type { CoreAuditDiagnosticOptions, CoreAuditDiagnosticContext, CoreAuditErrorEvidence, CoreAuditValidationDetail, CoreAuditBoundaryDetail } from "./diagnostics";

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

export function auditEventType(value: string, diagnostics?: CoreAuditDiagnosticOptions): Result<AuditEventType, AuditRecordError> {
  const observation = new AuditObservation("event-type", diagnostics);
  return observation.run(() => {
  if (!observation.at("predicate", "type", () => auditEventTypePattern.test(value))) {
    const diagnosticRecord = observation.validation({ operation: "event-type", field: "type", reason: "invalid-format" });
    return err(
      auditRecordError({
        code: "AUDIT_INVALID_TYPE",
        defaultMessage: "Audit event type must use dot-separated lowercase segments.",
        messageKey: "audit.type.invalid",
        params: { type: value },
        ...(diagnosticRecord === undefined ? {} : { diagnosticRecord }),
      }),
    );
  }

  return ok(brand<string, "AuditEventType">(value));
  });
}

export function auditEventVersion(value: number, diagnostics?: CoreAuditDiagnosticOptions): Result<AuditEventVersion, AuditRecordError> {
  const observation = new AuditObservation("event-version", diagnostics);
  return observation.run(() => {
  let reason: "not-integer" | "not-positive" = "not-integer";
  if (observation.at("predicate", "version", () => (!Number.isInteger(value) && (reason = "not-integer", true)) || (value <= 0 && (reason = "not-positive", true)))) {
    const diagnosticRecord = observation.validation({ operation: "event-version", field: "version", reason });
    return err(
      auditRecordError({
        code: "AUDIT_INVALID_VERSION",
        defaultMessage: "Audit event version must be a positive integer.",
        messageKey: "audit.version.invalid",
        params: { version: observation.at("parameter-formatting", "version", () => String(value)) },
        ...(diagnosticRecord === undefined ? {} : { diagnosticRecord }),
      }),
    );
  }

  return ok(brand<number, "AuditEventVersion">(value));
  });
}

export function auditActor(input: {
  readonly type: AuditActorType;
  readonly id?: PrincipalId;
  readonly subject?: string;
}, diagnostics?: CoreAuditDiagnosticOptions): AuditActor {
  const observation = new AuditObservation("actor", diagnostics);
  return observation.run(() => copyAuditActor(input, observation));
}

export function auditTarget(input: {
  readonly type: string;
  readonly id: string;
  readonly parent?: AuditTarget;
}, diagnostics?: CoreAuditDiagnosticOptions): Result<AuditTarget, AuditRecordError> {
  const observation = new AuditObservation("target", diagnostics);
  return observation.run(() => {
  if (!observation.at("predicate", "target-type", () => auditTargetTypePattern.test(input.type))) {
    const diagnosticRecord = observation.validation({ operation: "target", field: "target-type", reason: "invalid-format" });
    return err(
      auditRecordError({
        code: "AUDIT_INVALID_TARGET",
        defaultMessage: "Audit target type must be a non-empty lowercase identifier.",
        messageKey: "audit.target.invalid_type",
        params: { type: observation.at("input-projection", "target-type", () => input.type) },
        ...(diagnosticRecord === undefined ? {} : { diagnosticRecord }),
      }),
    );
  }

  let reason: "empty" | "untrimmed" = "empty";
  if (observation.at("predicate", "target-id", () => (input.id.length === 0 && (reason = "empty", true)) || (input.id.trim() !== input.id && (reason = "untrimmed", true)))) {
    const diagnosticRecord = observation.validation({ operation: "target", field: "target-id", reason });
    return err(
      auditRecordError({
        code: "AUDIT_INVALID_TARGET",
        defaultMessage: "Audit target id must be a non-empty trimmed string.",
        messageKey: "audit.target.invalid_id",
        ...(diagnosticRecord === undefined ? {} : { diagnosticRecord }),
      }),
    );
  }

  return ok({
    type: observation.at("input-projection", "target-type", () => input.type),
    id: observation.at("input-projection", "target-id", () => input.id),
    ...observation.at("input-projection", "parent", () => input.parent === undefined ? {} : { parent: copyAuditTarget(input.parent, observation) }),
  });
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
}, diagnostics?: CoreAuditDiagnosticOptions): AuditEvent<TMetadata> {
  const observation = new AuditObservation("event", diagnostics);
  return observation.run(() => projectAuditEvent(input, observation));
}

function projectAuditEvent<TMetadata extends AuditMetadata>(input: Omit<AuditEvent<TMetadata>, "version"> & { readonly version?: AuditEventVersion }, observation: AuditObservation): AuditEvent<TMetadata> {
  return {
    id: observation.at("input-projection", "id", () => input.id),
    type: observation.at("input-projection", "type", () => input.type),
    version: observation.at("input-projection", "version", () => input.version ?? currentAuditEventVersion),
    outcome: observation.at("input-projection", "outcome", () => input.outcome),
    actor: observation.at("input-projection", "actor", () => copyAuditActor(input.actor, observation)),
    ...observation.at("input-projection", "tenant-id", () => input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
    occurredAt: observation.at("input-projection", "occurred-at", () => input.occurredAt),
    ...observation.at("input-projection", "correlation-id", () => input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    target: observation.at("input-projection", "target", () => copyAuditTarget(input.target, observation)),
    ...observation.at("input-projection", "reason", () => input.reason === undefined ? {} : { reason: input.reason }),
    ...observation.at("input-projection", "metadata", () => input.metadata === undefined ? {} : { metadata: copyAuditMetadata(input.metadata, observation) }),
  };
}

export function auditRecordError(input: {
  readonly code: AuditRecordErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  readonly diagnosticRecord?: CoreError["diagnosticRecord"];
  readonly details?: Readonly<Record<string, unknown>>;
}, evidence?: CoreAuditErrorEvidence): AuditRecordError {
  const related = auditRelatedEvidence(evidence);
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
    ...(input.diagnostic === undefined ? {} : { diagnostic: input.diagnostic }),
    ...(input.diagnosticRecord === undefined ? {} : { diagnosticRecord: input.diagnosticRecord }),
    ...(related === undefined ? {} : { relatedDiagnosticRecords: related }),
    ...(input.details === undefined ? {} : { details: input.details }),
  };
}

export function inMemoryAuditRecorder(diagnostics?: CoreAuditDiagnosticOptions): InMemoryAuditRecorder {
  const recorded: AuditEvent[] = [];

  return {
    async record(event) {
      const observation = new AuditObservation("record", diagnostics);
      observation.effectIs("append-not-reached");
      observation.location("record-append");
      let copied: AuditEvent;
      observation.run(() => recorded.push((copied = observation.at("record-copy", undefined, () => projectAuditEvent(event, observation)), observation.effectIs("append-outcome-unknown"), observation.location("record-append"), copied)));
      return ok(undefined);
    },

    recordedEvents() {
      const observation = new AuditObservation("recorded-events", diagnostics);
      observation.effectIs("snapshot-not-returned");
      let ordinal = 0;
      return observation.run(() => observation.at("snapshot-copy", undefined, () => recorded.map((event) => observation.duringItem(ordinal++, () => projectAuditEvent(event, observation)))));
    },
  };
}

export const noopAuditRecorder: AuditRecorder = {
  record: async () => ok(undefined),
};

const auditEventTypePattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$/;
const auditTargetTypePattern = /^[a-z][a-z0-9-]*$/;

function copyAuditActor(actor: AuditActor, observation: AuditObservation): AuditActor {
  return {
    type: observation.at("actor-copy", "actor-type", () => actor.type),
    ...observation.at("actor-copy", "actor-id", () => actor.id === undefined ? {} : { id: actor.id }),
    ...observation.at("actor-copy", "subject", () => actor.subject === undefined ? {} : { subject: actor.subject }),
  };
}

function copyAuditTarget(target: AuditTarget, observation: AuditObservation): AuditTarget {
  return {
    type: observation.at("target-copy", "target-type", () => target.type),
    id: observation.at("target-copy", "target-id", () => target.id),
    ...observation.at("target-copy", "parent", () => target.parent === undefined ? {} : { parent: copyAuditTarget(target.parent, observation) }),
  };
}

function copyAuditMetadata<TMetadata extends AuditMetadata>(metadata: TMetadata, observation: AuditObservation): TMetadata {
  return observation.at("metadata-enumeration", "metadata", () => Object.fromEntries(
    Object.entries(metadata).map(([key, value]) => observation.at("metadata-copy", "metadata", () => [key, copyAuditMetadataValue(value)])),
  )) as TMetadata;
}

function copyAuditMetadataValue(value: AuditMetadataValue): AuditMetadataValue {
  return copyJsonValue(value, "audit metadata");
}

function auditRelatedEvidence(evidence: CoreAuditErrorEvidence | undefined): readonly DiagnosticRecord[] | undefined {
  if (evidence === undefined) return undefined;
  try {
    const records = Object.getOwnPropertyDescriptor(evidence, "relatedDiagnosticRecords");
    if (records === undefined || !("value" in records) || records.value === undefined) return undefined;
    const definitions = Object.getOwnPropertyDescriptor(evidence, "relatedDiagnosticDefinitions");
    if (definitions !== undefined && !("value" in definitions)) return undefined;
    const checked = parseRelatedDiagnosticRecords(definitions?.value ?? [], records.value);
    return checked.ok ? checked.value : undefined;
  } catch { return undefined; }
}
