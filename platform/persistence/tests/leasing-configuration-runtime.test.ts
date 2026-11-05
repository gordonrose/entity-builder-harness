import { deepEqual, equal, throws } from "node:assert/strict";
import { inMemoryQueue } from "@kanbien/core/queues";
import { isoDateTimeFromDate, type Result } from "@kanbien/core/shared";
import { parseDiagnosticRecord } from "@kanbien/core/diagnostics";
import { outboxEntry, outboxEntryId, outboxMessageType, outboxDeliveryPolicy, recordReference, recordKind, recordId } from "@kanbien/core/persistence";
import { validatePersistenceLeaseDuration, createPlatformOutboxRelay, createInMemoryPlatformOutboxStore,
  persistenceRelayConfigurationDiagnostic, nextPlatformPersistenceLease, platformPersistenceAttempt,
  platformPersistenceLeaseOwner, type PlatformOutboxRelayOptions, type PlatformOutboxQueuePayload } from "../src/index";

function accepted<T>(result: Result<T, unknown>): T { if (!result.ok) throw new Error("Invalid fixture"); return result.value; }
const canary = "private-lease-canary", at = isoDateTimeFromDate(new Date("2026-01-01T00:00:00Z"));
const owner = accepted(platformPersistenceLeaseOwner("relay-fixture"));
const packet = (reason: string) => ({ schema: "core/diagnostic-record/v1", code: "persistence.relay-configuration-invalid", definitionVersion: 1,
  detail: { operation: "configure-relay", phase: "configuration", setting: "lease-duration", reason, effect: "relay-not-created" } });

async function main() {
  for (const [value, reason] of [[undefined, "missing"], [null, "wrong-type"], [canary, "wrong-type"], [false, "wrong-type"], [{ toString() { throw new Error("No coercion"); } }, "wrong-type"],
    [NaN, "not-finite"], [Infinity, "not-finite"], [-Infinity, "not-finite"], [0.5, "invalid-integer"], [0, "not-positive"], [-0, "not-positive"], [-1, "not-positive"]] as const) {
    deepEqual(validatePersistenceLeaseDuration(value), { ok: false, error: { reason } });
    let calls = 0;
    const options = { leaseDurationMs: value, get clock() { calls++; throw canary; }, get outbox() { calls++; throw canary; }, get queue() { calls++; throw canary; } } as unknown as PlatformOutboxRelayOptions;
    throws(() => createPlatformOutboxRelay(options), (error: unknown) => {
      equal(error instanceof TypeError, true);
      const record = (error as { diagnosticRecord: unknown }).diagnosticRecord;
      deepEqual(record, packet(reason)); equal(JSON.stringify(record).includes(canary), false); return true;
    });
    equal(calls, 0);
  }
  for (const value of [1, 30000, Number.MAX_SAFE_INTEGER]) deepEqual(validatePersistenceLeaseDuration(value), { ok: true, value });
  const raw = Object.freeze(new Error(canary));
  throws(() => createPlatformOutboxRelay({ get leaseDurationMs() { throw raw; } } as unknown as PlatformOutboxRelayOptions), error => error === raw);
  for (const change of [{ definitionVersion: 2 }, { detail: { ...packet("missing").detail, raw: canary } }, { detail: { ...packet("missing").detail, reason: canary } }]) {
    equal(parseDiagnosticRecord(persistenceRelayConfigurationDiagnostic, { ...packet("missing"), ...change }).ok, false);
  }
  const outbox = createInMemoryPlatformOutboxStore(), queue = inMemoryQueue<PlatformOutboxQueuePayload>();
  const send = queue.send.bind(queue);
  queue.send = async message => {
    const leased = await outbox.get(outboxEntryId("lease-fixture"));
    equal(leased?.lease?.expiresAt, "2026-01-01T00:00:01.000Z");
    return send(message);
  };
  const entry = outboxEntry({ id: outboxEntryId("lease-fixture"), subject: recordReference({ kind: accepted(recordKind("fixture.record")), id: accepted(recordId("record-1")) }),
    messageType: accepted(outboxMessageType("fixture.work")), deliveryPolicy: accepted(outboxDeliveryPolicy("fixture.delivery")), createdAt: at });
  accepted(await outbox.create(entry)); let reads = 0, clocks = 0;
  const options = { outbox, queue, owner, clock: { now() { clocks++; return new Date(at); } }, get leaseDurationMs() { reads++; return reads === 1 ? 1000 : 0; } };
  const relay = createPlatformOutboxRelay(options); deepEqual([reads, clocks], [1, 0]);
  equal(accepted(await relay.runOnce()).status, "published"); equal(reads, 1); equal(queue.acceptedMessages().length, 1);
  const stored = await outbox.get(entry.id); equal(stored?.lease, undefined);

  // Test-only substitution distinguishes shared result use from copied bounds.
  const shared = require("../src/leasing/domain/validation/duration") as { validatePersistenceLeaseDuration: typeof validatePersistenceLeaseDuration };
  const original = shared.validatePersistenceLeaseDuration;
  try {
    shared.validatePersistenceLeaseDuration = () => ({ ok: false, error: { reason: "not-positive" } });
    throws(() => createPlatformOutboxRelay({ ...options, leaseDurationMs: 1000 }), error => { deepEqual((error as { diagnosticRecord: unknown }).diagnosticRecord, packet("not-positive")); return true; });
    equal(nextPlatformPersistenceLease({ owner, priorAttempt: accepted(platformPersistenceAttempt(0)), acquiredAt: at, durationMs: 1000 }).ok, false);
    shared.validatePersistenceLeaseDuration = () => ({ ok: true, value: 2000 });
    const lease = accepted(nextPlatformPersistenceLease({ owner, priorAttempt: accepted(platformPersistenceAttempt(0)), acquiredAt: at, durationMs: 1000 }));
    equal(lease.expiresAt, "2026-01-01T00:00:02.000Z");
  } finally { shared.validatePersistenceLeaseDuration = original; }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
