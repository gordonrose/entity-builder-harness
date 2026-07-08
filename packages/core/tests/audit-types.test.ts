import { principalId } from "../src/authn/index";
import {
  auditActor,
  auditEvent,
  auditEventId,
  auditEventType,
  auditRecordError,
  auditTarget,
  inMemoryAuditRecorder,
  noopAuditRecorder,
  type AuditActor,
  type AuditEvent,
  type AuditEventId,
  type AuditEventType,
  type AuditMetadata,
  type AuditMetadataValue,
  type AuditOutcome,
  type AuditRecordError,
  type AuditRecordErrorCode,
  type AuditRecorder,
  type AuditTarget,
} from "../src/audit/index";
import { correlationId, isOk, isoDateTime, type Result } from "../src/shared/index";
import { tenantId } from "../src/tenancy/index";

const typeResult: Result<AuditEventType, AuditRecordError> = auditEventType("deal.deleted");
const targetResult: Result<AuditTarget, AuditRecordError> = auditTarget({ type: "deal", id: "deal-123" });
const timestamp = isoDateTime("2026-07-07T12:00:00.000Z");
const acceptedCode: AuditRecordErrorCode = "AUDIT_RECORD_FAILED";
const acceptedError: AuditRecordError = auditRecordError({
  code: acceptedCode,
  defaultMessage: "Audit record failed.",
  messageKey: "audit.record.failed",
});
const outcome: AuditOutcome = "succeeded";
const actor: AuditActor = auditActor({
  type: "user",
  id: principalId("principal-123"),
  subject: "oidc:test-idp:subject-123",
});
const systemActor: AuditActor = auditActor({ type: "system", subject: "system:importer" });
const metadataValue: AuditMetadataValue = {
  before: { stage: "qualified" },
  after: { stage: "won" },
  changedFields: ["stage"],
};
const metadata: AuditMetadata = {
  field: "stage",
  before: "qualified",
  after: "won",
};

if (!isOk(typeResult) || !isOk(targetResult) || !isOk(timestamp)) {
  throw new Error("Expected valid test primitives.");
}

const event: AuditEvent<AuditMetadata> = auditEvent({
  id: auditEventId("audit-123"),
  type: typeResult.value,
  outcome,
  actor,
  tenantId: tenantId("tenant-123"),
  occurredAt: timestamp.value,
  correlationId: correlationId("request-123"),
  target: targetResult.value,
  metadata,
});
const recorder: AuditRecorder = inMemoryAuditRecorder();
const noop: AuditRecorder = noopAuditRecorder;

void acceptedError;
void systemActor;
void metadataValue;
void event;
void recorder;
void noop;

recorder.record(event);
noop.record(event);

// @ts-expect-error audit event ids must be explicitly branded.
const invalidAuditId: AuditEventId = "audit-123";
void invalidAuditId;

// @ts-expect-error audit event types must be explicitly created and branded.
const invalidAuditType: AuditEventType = "deal.deleted";
void invalidAuditType;

// @ts-expect-error audit outcomes are intentionally constrained.
const invalidOutcome: AuditOutcome = "unknown";
void invalidOutcome;

// @ts-expect-error audit metadata must stay plain and serializable.
const invalidMetadataValue: AuditMetadataValue = new Date();
void invalidMetadataValue;

// @ts-expect-error audit actors that carry an id must use a PrincipalId.
auditActor({ type: "user", id: "principal-123" });

auditEvent({
  // @ts-expect-error audit events require a branded audit id.
  id: "audit-123",
  type: typeResult.value,
  outcome,
  occurredAt: timestamp.value,
});

auditEvent({
  id: auditEventId("audit-123"),
  // @ts-expect-error audit events require a branded audit type.
  type: "deal.deleted",
  outcome,
  occurredAt: timestamp.value,
});

auditEvent({
  id: auditEventId("audit-123"),
  type: typeResult.value,
  // @ts-expect-error audit event outcome must use the constrained vocabulary.
  outcome: "unknown",
  occurredAt: timestamp.value,
});

auditEvent({
  id: auditEventId("audit-123"),
  type: typeResult.value,
  outcome,
  // @ts-expect-error audit event tenant context must receive a TenantId.
  tenantId: "tenant-123",
  occurredAt: timestamp.value,
  actor,
  target: targetResult.value,
});

// @ts-expect-error audit events require an explicit actor.
auditEvent({
  id: auditEventId("audit-123"),
  type: typeResult.value,
  outcome,
  occurredAt: timestamp.value,
  target: targetResult.value,
});

// @ts-expect-error audit events require an explicit target.
auditEvent({
  id: auditEventId("audit-123"),
  type: typeResult.value,
  outcome,
  actor,
  occurredAt: timestamp.value,
});

// @ts-expect-error audit record error codes are constrained.
auditRecordError({ code: "AUDIT_DATABASE_LOCKED", defaultMessage: "Audit database locked." });
