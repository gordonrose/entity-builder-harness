import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import { outboxEntryId } from "@kanbien/core/persistence";
import { isoDateTime, type ISODateTime, type Result } from "@kanbien/core/shared";
import { createInMemoryPlatformProcessingStore, platformPersistenceLeaseOwner,
  validatePlatformProcessingRetryAt, decodePlatformProcessingRetryAt } from "../../src/index";

const instant = (value: string) => accepted(isoDateTime(value));
const acquiredAt = instant("2026-11-26T12:00:00.000Z");
const releasedAt = instant("2026-11-26T12:00:00.100Z");
const retryAt = instant("2026-11-26T12:00:02.000Z");
const id = outboxEntryId("retry-fixture"), owner = accepted(platformPersistenceLeaseOwner("fixture.retry"));

async function main(): Promise<void> {
  const store = createInMemoryPlatformProcessingStore();
  const claimed = accepted(await store.claim({ outboxEntryId: id, owner, acquiredAt, leaseDurationMs: 1000 }));
  const fence = claimed.record.lease!.fence;
  const released = accepted(await store.release({ outboxEntryId: id, fence, releasedAt, retryAt }));
  equal(released.retryAt, retryAt); equal(released.attempt, 1);
  // The old lease has expired, but the persisted retry deadline still wins.
  const early = accepted(await store.claim({ outboxEntryId: id, owner, acquiredAt: instant("2026-11-26T12:00:01.500Z"), leaseDurationMs: 1000 }));
  equal(early.disposition, "retry-not-due"); equal(early.record.attempt, 1); equal(early.record.lease!.fence, fence);
  deepEqual(await store.get(id), released);
  const due = accepted(await store.claim({ outboxEntryId: id, owner, acquiredAt: retryAt, leaseDurationMs: 1000 }));
  equal(due.disposition, "claimed"); equal(due.record.attempt, 2); equal(due.record.retryAt, undefined);
  equal(Number(due.record.lease!.fence), Number(fence) + 1);

  // Legacy release remains immediately reclaimable, even with an unexpired lease.
  accepted(await store.release({ outboxEntryId: id, fence: due.record.lease!.fence, releasedAt: retryAt }));
  equal(accepted(await store.claim({ outboxEntryId: id, owner, acquiredAt: retryAt, leaseDurationMs: 1000 })).record.attempt, 3);

  for (const [value, reason] of [["PRIVATE-RETRY-CANARY", "invalid-timestamp"], [instant("2026-11-26T11:00:00.000Z"), "before-release"]] as const) {
    const before = await store.get(id); const observed: unknown[] = [];
    const rejected = validatePlatformProcessingRetryAt({ releasedAt, retryAt: value as ISODateTime }, { onDiagnostic(record) { observed.push(record); throw Error("private"); } });
    equal(rejected.ok, false);
    if (!rejected.ok) deepEqual(rejected.error.diagnosticRecord?.detail, { field: "retry-at", reason, effect: "not-started" });
    equal(JSON.stringify(observed).includes("PRIVATE-RETRY-CANARY"), false);
    const result = await store.release({ outboxEntryId: id, fence: before!.lease!.fence, releasedAt: retryAt, retryAt: value as ISODateTime });
    equal(result.ok, false); deepEqual(await store.get(id), before);
  }
  equal(accepted(validatePlatformProcessingRetryAt({ releasedAt, retryAt: releasedAt })), releasedAt);
  equal(accepted(validatePlatformProcessingRetryAt({ releasedAt })), undefined);
  for (const value of [null, false, 3, {}, "PRIVATE-RETRY-CANARY"]) throws(() => decodePlatformProcessingRetryAt(value), error => {
    equal(error instanceof TypeError, true);
    deepEqual((error as { diagnosticRecord: { detail: unknown } }).diagnosticRecord.detail, {
      field: "retry-at", reason: typeof value === "string" ? "invalid-timestamp" : "wrong-type", effect: "not-assessed",
    });
    equal(JSON.stringify(error).includes("PRIVATE-RETRY-CANARY"), false); return true;
  });
  equal(decodePlatformProcessingRetryAt(retryAt), retryAt);
  const original = Object.freeze(new Error("private-getter"));
  await rejects(store.release({ outboxEntryId: id, fence: due.record.lease!.fence, releasedAt,
    get retryAt(): never { throw original; } }), cause => cause === original);
  console.log("Persisted retry deadline, attempt/fence stability, legacy release and safe rejection tests passed.");
}
function accepted<T>(result: Result<T, unknown>): T { if (!result.ok) throw result.error; return result.value; }
void main().catch(error => { console.error(error); process.exitCode = 1; });
