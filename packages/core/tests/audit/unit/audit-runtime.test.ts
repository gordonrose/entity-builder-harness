import { deepEqual, equal, throws, rejects } from "node:assert/strict";
import { principalId } from "../../../src/authn/index";
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
  type CoreAuditDiagnosticOptions,
} from "../../../src/audit/index";
import { diagnosticDescriptor, defineDiagnostic, createDiagnosticRecord, type DiagnosticRecord } from "../../../src/diagnostics/index";
import { correlationId, isErr, isOk, isoDateTime, messageDescriptor } from "../../../src/shared/index";
import { tenantId } from "../../../src/tenancy/index";

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
  await diagnosticCoverage(event);
}

async function diagnosticCoverage(event: AuditEvent): Promise<void> {
  const sourceDefinition = defineDiagnostic({ code: "fixture.audit-source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } } } as const);
  const sourceRecords = Array.from({ length: 9 }, (_, ordinal) => { const result = createDiagnosticRecord(sourceDefinition, { ordinal }); if (!result.ok) throw result.error; return result.value; });
  const source = Object.freeze(Object.assign(new Error("private-audit-canary@example.invalid"), { diagnosticRecord: sourceRecords[0], relatedDiagnosticRecords: sourceRecords.slice(1) }));
  const records: DiagnosticRecord[] = [];
  const diagnostics: CoreAuditDiagnosticOptions = { diagnosticDefinitions: [sourceDefinition], onDiagnostic(record, context) {
    equal(this, diagnostics); equal(Object.isFrozen(context), true); records.push(record);
  } };
  const literal = (code: string, detail: unknown) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
  const boundary = (detail: unknown): void => {
    deepEqual(records[0], literal("core.audit.boundary-failed", detail)); deepEqual(records.slice(1), sourceRecords);
    equal(records.length, 10); equal(JSON.stringify(records).includes("private-audit-canary"), false); records.length = 0;
  };
  for (const value of ["", "Audit.Updated", "single"]) {
    const result = auditEventType(value, diagnostics); if (result.ok) throw new Error("Expected type rejection");
    equal(result.error.code, "AUDIT_INVALID_TYPE"); deepEqual(result.error.params, { type: value });
    deepEqual(result.error.diagnosticRecord, literal("core.audit.validation-rejected", { operation: "event-type", field: "type", reason: "invalid-format", effect: "rejected" }));
    records.length = 0;
  }
  for (const value of [0, -1, 0.5, NaN, Infinity]) {
    const result = auditEventVersion(value, diagnostics); if (result.ok) throw new Error("Expected version rejection");
    equal(result.error.code, "AUDIT_INVALID_VERSION"); deepEqual(result.error.params, { version: String(value) });
    deepEqual(result.error.diagnosticRecord, literal("core.audit.validation-rejected", { operation: "event-version", field: "version", reason: Number.isInteger(value) ? "not-positive" : "not-integer", effect: "rejected" }));
    records.length = 0;
  }
  for (const [input, field, reason] of [[{ type: "Bad", id: "" }, "target-type", "invalid-format"], [{ type: "deal", id: "" }, "target-id", "empty"], [{ type: "deal", id: " untrimmed" }, "target-id", "untrimmed"]] as const) {
    const result = auditTarget(input, diagnostics); if (result.ok) throw new Error("Expected target rejection"); equal(result.error.code, "AUDIT_INVALID_TARGET");
    deepEqual(result.error.diagnosticRecord, literal("core.audit.validation-rejected", { operation: "target", field, reason, effect: "rejected" })); records.length = 0;
  }
  const reads: string[] = [];
  const target = { type: "deal", id: "target", parent: { type: "account", id: "parent" } };
  auditTarget(new Proxy(target, { get(value, key, receiver) { reads.push(String(key)); return Reflect.get(value, key, receiver); } }), diagnostics);
  deepEqual(reads, ["type", "id", "id", "id", "type", "id", "parent", "parent"]); equal(records.length, 0);
  const invalidOrder: string[] = [];
  auditTarget({ get type() { invalidOrder.push("type"); return "Bad"; }, get id() { invalidOrder.push("id"); return ""; } }, diagnostics);
  deepEqual(invalidOrder, ["type", "type"]); equal(records.length, 1); records.length = 0;
  throws(() => auditEventType({ toString() { throw source; } } as unknown as string, diagnostics), (error) => error === source);
  boundary({ operation: "event-type", phase: "predicate", field: "type", reason: "threw", effect: "result-not-returned" });
  throws(() => auditEventVersion({ toString() { throw source; } } as unknown as number, diagnostics), (error) => error === source);
  deepEqual(records.shift(), literal("core.audit.validation-rejected", { operation: "event-version", field: "version", reason: "not-integer", effect: "rejected" }));
  boundary({ operation: "event-version", phase: "parameter-formatting", field: "version", reason: "threw", effect: "result-not-returned" });
  throws(() => auditActor(Object.defineProperty({ type: "system" }, "subject", { get() { throw source; } }) as never, diagnostics), (error) => error === source);
  boundary({ operation: "actor", phase: "actor-copy", field: "subject", reason: "threw", effect: "result-not-returned" });
  throws(() => auditTarget({ type: "deal", id: "target", parent: Object.defineProperty({ type: "deal" }, "id", { get() { throw source; } }) as never }, diagnostics), (error) => error === source);
  boundary({ operation: "target", phase: "target-copy", field: "target-id", reason: "threw", effect: "result-not-returned" });
  const eventReads: string[] = [];
  auditEvent(new Proxy(event, { get(value, key, receiver) { eventReads.push(String(key)); return Reflect.get(value, key, receiver); } }), diagnostics);
  deepEqual(eventReads, ["id", "type", "version", "outcome", "actor", "tenantId", "tenantId", "occurredAt", "correlationId", "correlationId", "target", "reason", "reason", "metadata", "metadata"]); equal(records.length, 0);
  const entriesOrder: string[] = [];
  const metadata = Object.defineProperties({}, { first: { enumerable: true, get() { entriesOrder.push("first"); return NaN; } }, later: { enumerable: true, get() { entriesOrder.push("later"); throw source; } } });
  throws(() => auditEvent({ ...event, metadata }, diagnostics), (error) => error === source);
  deepEqual(entriesOrder, ["first", "later"]);
  boundary({ operation: "event", phase: "metadata-enumeration", field: "metadata", reason: "threw", effect: "result-not-returned" });
  throws(() => auditEvent({ ...event, metadata: { first: NaN } }, diagnostics), /finite numbers/);
  deepEqual(records, [literal("core.audit.boundary-failed", { operation: "event", phase: "metadata-copy", field: "metadata", reason: "threw", effect: "result-not-returned" }),
    literal("core.shared.json-invalid", { reason: "non-finite-number", depth: 0, path: [], pathTruncated: false })]); records.length = 0;
  let mapCalls = 0, visits = 0;
  const custom: unknown[] = [];
  Object.defineProperty(custom, "map", { value(callback: (value: unknown, position: number) => unknown) { equal(this, custom); mapCalls++; visits++; callback(1, 8192); throw source; } });
  throws(() => auditEvent({ ...event, metadata: { nested: custom as never } }, diagnostics), (error) => error === source);
  equal(mapCalls, 1); equal(visits, 1);
  boundary({ operation: "event", phase: "metadata-copy", field: "metadata", reason: "threw", effect: "result-not-returned" });
  const recorder = inMemoryAuditRecorder(diagnostics);
  const failedEvent = Object.defineProperty({ ...event }, "actor", { get() { throw source; } });
  await rejects(recorder.record(failedEvent), (error) => error === source);
  deepEqual(recorder.recordedEvents(), []);
  boundary({ operation: "record", phase: "input-projection", field: "actor", reason: "threw", effect: "append-not-reached" });
  // Controlled public Array port override proves append may mutate then throw.
  // Restore before any later fixture, with no global listener or prototype leak.
  const appendEvent = { ...event, id: auditEventId("append-uncertain") };
  const originalPush = Array.prototype.push;
  Array.prototype.push = function<T>(this: T[], ...values: T[]): number {
    const length = Reflect.apply(originalPush, this, values) as number;
    if (values.length === 1 && values[0] !== null && typeof values[0] === "object" && (values[0] as unknown as AuditEvent).id === appendEvent.id) throw source;
    return length;
  };
  try { await rejects(recorder.record(appendEvent), (error) => error === source); }
  finally { Array.prototype.push = originalPush; }
  equal(recorder.recordedEvents().length, 1);
  boundary({ operation: "record", phase: "record-append", reason: "threw", effect: "append-outcome-unknown" });
  const snapshotRecorder = inMemoryAuditRecorder(diagnostics);
  equal((await snapshotRecorder.record(event)).ok, true);
  let snapshotReads = 0;
  const snapshotNested = Object.defineProperty({}, "private-key", { enumerable: true, get() { snapshotReads++; throw source; } });
  const snapshotArray: unknown[] = []; Object.defineProperty(snapshotArray, "map", { value() { return [snapshotNested]; } });
  equal((await snapshotRecorder.record({ ...event, metadata: { nested: snapshotArray as never } })).ok, true); equal(records.length, 0);
  throws(() => snapshotRecorder.recordedEvents(), (error) => error === source); equal(snapshotReads, 1);
  boundary({ operation: "recorded-events", phase: "metadata-copy", field: "metadata", reason: "threw", effect: "snapshot-not-returned", ordinal: 1 });
  for (const raw of ["private-primitive", Object.freeze(new Error("private-frozen"))]) {
    await rejects(recorder.record(Object.defineProperty({ ...event }, "actor", { get() { throw raw; } })), (error) => error === raw);
    deepEqual(records, [literal("core.audit.boundary-failed", { operation: "record", phase: "input-projection", field: "actor", reason: "threw", effect: "append-not-reached" })]); records.length = 0;
  }
  let evidenceReads = 0;
  const accessor = Object.defineProperty(new Error("private"), "diagnosticRecord", { get() { evidenceReads++; throw source; } });
  await rejects(recorder.record(Object.defineProperty({ ...event }, "actor", { get() { throw accessor; } })), (error) => error === accessor);
  equal(evidenceReads, 0); equal(records.length, 2);
  deepEqual(records[1], literal("core.diagnostics.processing-failed", { reason: "evidence-inaccessible" })); records.length = 0;
  const unselected: DiagnosticRecord[] = [];
  await rejects(inMemoryAuditRecorder({ onDiagnostic(record) { unselected.push(record); } }).record(failedEvent), (error) => error === source); equal(unselected.length, 1);
  const malformed = Object.freeze(Object.assign(new Error("private-malformed"), { diagnosticRecord: { ...sourceRecords[0], detail: { secret: "private-malformed" } }, relatedDiagnosticRecords: sourceRecords.slice(1) }));
  await rejects(recorder.record(Object.defineProperty({ ...event }, "actor", { get() { throw malformed; } })), (error) => error === malformed);
  equal(records.length, 10); deepEqual(records.slice(1, 9), sourceRecords.slice(1));
  deepEqual(records[9], literal("core.diagnostics.processing-failed", { reason: "evidence-rejected" }));
  equal(JSON.stringify(records).includes("private-malformed"), false); records.length = 0;
  const unhandled: unknown[] = [], listener = (error: unknown): void => { unhandled.push(error); };
  process.on("unhandledRejection", listener);
  try {
    for (const mode of ["throw", "native", "shadowed", "thenable", "getter"] as const) {
      let sinkCalls = 0, thenReads = 0;
      const options: CoreAuditDiagnosticOptions = { diagnosticDefinitions: [sourceDefinition], onDiagnostic() {
        equal(this, options); sinkCalls++; if (mode === "throw") throw source;
        if (mode === "thenable") return { then(_resolve: unknown, reject: (value: unknown) => void) { reject(source); } };
        if (mode === "getter") return Object.defineProperty({}, "then", { get() { throw source; } });
        const pending = Promise.reject(source); if (mode === "shadowed") Object.defineProperty(pending, "then", { get() { thenReads++; throw source; } }); return pending;
      } };
      await rejects(inMemoryAuditRecorder(options).record(failedEvent), (error) => error === source);
      equal(sinkCalls, 10); equal(thenReads, 0);
    }
    await new Promise<void>((resolve) => setImmediate(resolve)); deepEqual(unhandled, []);
  } finally { process.off("unhandledRejection", listener); }
}

main()
  .then(() => {
    console.log("packages/core audit runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
