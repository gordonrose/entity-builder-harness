import { deepEqual, equal, throws } from "node:assert/strict";
import { principalId } from "../src/authn/index";
import {
  auditActor,
  auditEvent,
  auditEventId,
  auditEventType,
  auditEventVersion,
  auditRecordError,
  auditTarget,
  inMemoryAuditRecorder,
  noopAuditRecorder,
  type AuditEvent,
  type AuditMetadata,
} from "../src/audit/index";
import { diagnosticDescriptor } from "../src/diagnostics/index";
import { correlationId, isErr, isOk, isoDateTime, messageDescriptor } from "../src/shared/index";
import { tenantId } from "../src/tenancy/index";

async function main(): Promise<void> {
  const validType = auditEventType("deal.deleted");
  equal(isOk(validType), true);
  if (!isOk(validType)) {
    throw new Error("Expected audit event type to be valid.");
  }
  equal(validType.value, "deal.deleted");

  const invalidType = auditEventType("Deal Deleted");
  equal(isErr(invalidType), true);
  if (!isErr(invalidType)) {
    throw new Error("Expected audit event type to be invalid.");
  }
  equal(invalidType.error.code, "AUDIT_INVALID_TYPE");
  equal(invalidType.error.messageKey, "audit.type.invalid");

  const validVersion = auditEventVersion(1);
  equal(isOk(validVersion), true);
  if (!isOk(validVersion)) {
    throw new Error("Expected audit event version to be valid.");
  }
  equal(validVersion.value, 1);

  const invalidVersion = auditEventVersion(0);
  equal(isErr(invalidVersion), true);
  if (!isErr(invalidVersion)) {
    throw new Error("Expected audit event version to be invalid.");
  }
  equal(invalidVersion.error.code, "AUDIT_INVALID_VERSION");
  equal(invalidVersion.error.messageKey, "audit.version.invalid");

  const parentTarget = auditTarget({ type: "account", id: "account-123" });
  equal(isOk(parentTarget), true);
  if (!isOk(parentTarget)) {
    throw new Error("Expected parent target to be valid.");
  }

  const target = auditTarget({ type: "deal", id: "deal-123", parent: parentTarget.value });
  equal(isOk(target), true);
  if (!isOk(target)) {
    throw new Error("Expected target to be valid.");
  }
  deepEqual(target.value, {
    type: "deal",
    id: "deal-123",
    parent: { type: "account", id: "account-123" },
  });

  const invalidTargetType = auditTarget({ type: "Deal", id: "deal-123" });
  equal(isErr(invalidTargetType), true);
  if (!isErr(invalidTargetType)) {
    throw new Error("Expected invalid target type.");
  }
  equal(invalidTargetType.error.messageKey, "audit.target.invalid_type");

  const invalidTargetId = auditTarget({ type: "deal", id: " deal-123" });
  equal(isErr(invalidTargetId), true);
  if (!isErr(invalidTargetId)) {
    throw new Error("Expected invalid target id.");
  }
  equal(invalidTargetId.error.messageKey, "audit.target.invalid_id");

  const occurredAt = isoDateTime("2026-07-07T12:00:00.000Z");
  equal(isOk(occurredAt), true);
  if (!isOk(occurredAt)) {
    throw new Error("Expected timestamp to be valid.");
  }

  const metadata = {
    before: { stage: "qualified" },
    after: { stage: "won" },
    fields: ["stage"],
  } satisfies AuditMetadata;
  const event = auditEvent({
    id: auditEventId("audit-123"),
    type: validType.value,
    version: validVersion.value,
    outcome: "succeeded",
    actor: auditActor({
      type: "user",
      id: principalId("principal-123"),
      subject: "oidc:test-idp:subject-123",
    }),
    tenantId: tenantId("tenant-123"),
    occurredAt: occurredAt.value,
    correlationId: correlationId("request-123"),
    target: target.value,
    reason: messageDescriptor({
      code: "AUDIT_DEAL_DELETED",
      defaultMessage: "Deal was deleted.",
      messageKey: "audit.deal.deleted",
    }),
    metadata,
  });

  deepEqual(event, {
    id: "audit-123",
    type: "deal.deleted",
    version: 1,
    outcome: "succeeded",
    actor: {
      type: "user",
      id: "principal-123",
      subject: "oidc:test-idp:subject-123",
    },
    tenantId: "tenant-123",
    occurredAt: "2026-07-07T12:00:00.000Z",
    correlationId: "request-123",
    target: {
      type: "deal",
      id: "deal-123",
      parent: { type: "account", id: "account-123" },
    },
    reason: {
      code: "AUDIT_DEAL_DELETED",
      defaultMessage: "Deal was deleted.",
      messageKey: "audit.deal.deleted",
    },
    metadata: {
      before: { stage: "qualified" },
      after: { stage: "won" },
      fields: ["stage"],
    },
  });

  metadata.before.stage = "mutated-before";
  metadata.after.stage = "mutated-after";
  metadata.fields.push("mutated-field");
  deepEqual(event.metadata, {
    before: { stage: "qualified" },
    after: { stage: "won" },
    fields: ["stage"],
  });

  const invalidMetadataEvent = () =>
    auditEvent({
      id: auditEventId("audit-invalid-metadata"),
      type: validType.value,
      outcome: "failed",
      actor: auditActor({ type: "system", subject: "system:test" }),
      occurredAt: occurredAt.value,
      target: target.value,
      metadata: { score: Number.NaN },
    });
  throws(invalidMetadataEvent, /finite numbers/);

  const explicitError = auditRecordError({
    code: "AUDIT_RECORD_FAILED",
    defaultMessage: "Audit record failed.",
    messageKey: "audit.record.failed",
    diagnostic: diagnosticDescriptor({
      failureKind: "dependency_unavailable",
      failureSource: "platform",
      severity: "error",
      recovery: "manual_investigation",
      action: "escalate",
    }),
  });
  equal(explicitError.code, "AUDIT_RECORD_FAILED");
  equal(explicitError.messageKey, "audit.record.failed");
  equal(explicitError.diagnostic?.recovery, "manual_investigation");

  const recorder = inMemoryAuditRecorder();
  const recordResult = await recorder.record(event);
  equal(isOk(recordResult), true);
  deepEqual(recorder.recordedEvents(), [event]);

  const recordedEvents = recorder.recordedEvents() as AuditEvent<NonNullable<typeof event.metadata>>[];
  const recordedMetadata = recordedEvents[0]?.metadata;
  if (recordedMetadata === undefined) {
    throw new Error("Expected recorded event metadata.");
  }
  recordedMetadata.fields.push("mutated-recorded-field");
  deepEqual(recorder.recordedEvents()[0]?.metadata, {
    before: { stage: "qualified" },
    after: { stage: "won" },
    fields: ["stage"],
  });

  const noopResult = await noopAuditRecorder.record(event);
  equal(isOk(noopResult), true);
}

main()
  .then(() => {
    console.log("packages/core audit runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
