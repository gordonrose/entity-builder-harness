import { deepEqual, equal, rejects, ok as assertOk } from "node:assert/strict";
import { outboxEntry, outboxEntryId, outboxDeliveryPolicy, outboxMessageType, recordReference, recordId, recordKind } from "@kanbien/core/persistence";
import { isoDateTimeFromDate, type Result } from "@kanbien/core/shared";
import { tenantId } from "@kanbien/core/tenancy";
import { queueMessageVersion, type QueueMessage } from "@kanbien/core/queues";
import { platformAppId, platformJobName, platformCapabilityName, platformObservabilityProfileName } from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createInMemoryPlatformOutboxStore, createInMemoryPlatformProcessingStore, platformOutboxQueueMessage, platformPersistenceLeaseOwner,
  type PlatformProcessingStore } from "@kanbien/platform-persistence";
import { createPlatformWorkerShell, type PlatformWorkerShellOptions } from "../../src/index";

const privateValue = "PRIVATE-EXTERNAL-DELIVERY-CANARY";
const start = Date.parse("2026-11-26T12:00:00.000Z");
const appId = accepted(platformAppId("externalfixture"));
const jobName = accepted(platformJobName("externalfixture.cleanup"));
const messageType = accepted(outboxMessageType("externalfixture.cleanup.requested"));
const owner = accepted(platformPersistenceLeaseOwner("fixture.external"));
const profile = accepted(platformObservabilityProfileName("externalfixture.cleanup"));
const capability = accepted(platformCapabilityName("externalfixture.cleanup"));

async function fixture(handle: () => void | Promise<void>, extra: Partial<PlatformWorkerShellOptions> = {}) {
  let now = start;
  const records: unknown[] = [];
  const clock = { now: () => new Date(now) };
  const outbox = createInMemoryPlatformOutboxStore();
  const processing = createInMemoryPlatformProcessingStore();
  const entry = outboxEntry({ id: outboxEntryId("external-fixture"),
    subject: recordReference({ kind: accepted(recordKind("platform.schedule")), id: accepted(recordId("fixture")) }),
    messageType, deliveryPolicy: accepted(outboxDeliveryPolicy("fixture.delivery")), createdAt: isoDateTimeFromDate(clock.now()) });
  accepted(await outbox.create(entry));
  const message = accepted(platformOutboxQueueMessage(entry, isoDateTimeFromDate(clock.now())));
  const options: PlatformWorkerShellOptions = { apps: [{ id: appId, name: "External fixture", mount(registry) {
    registry.registerObservabilityProfile({ name: profile, capability, action: "execute", signals: ["operational_log"] });
    registry.registerJob({ name: jobName, messageType: message.type, observability: { kind: "profile", profile }, handler: { handle } });
  } }], deps: { ...createPlatformTestMountDeps({ clock }), diagnostics: { report(record) { records.push(record); return { status: "written" }; } } },
    durableOutboxProcessing: { processingStore: processing, outbox, owner, leaseDurationMs: 1000 }, maxAttempts: 2, retryBackoffMs: () => 500,
    ...extra };
  const shell = accepted(await createPlatformWorkerShell(options));
  accepted(await shell.start());
  return { shell, options, message, processing, outbox, records, advance(ms: number) { now += ms; }, clock };
}

async function main(): Promise<void> {
  let handled = 0;
  const good = await fixture(() => { handled++; });
  const first = accepted(await good.shell.runDelivery(good.message));
  equal(first.status, "succeeded");
  if (first.status !== "succeeded") throw Error("Expected completion");
  equal(first.idempotency, "durable-processed"); equal(first.attempt, 1);
  equal((await good.processing.get(outboxEntryId("external-fixture")))?.completion?.outcome, "succeeded");
  const fresh = accepted(await createPlatformWorkerShell(good.options)); accepted(await fresh.start());
  const duplicate = accepted(await fresh.runDelivery(good.message));
  equal(duplicate.status, "succeeded");
  if (duplicate.status === "succeeded") equal(duplicate.idempotency, "durable-skipped");
  equal(duplicate.attempt, 1, "durable duplicates retain the persisted attempt across process restarts");
  equal(handled, 1, "a fresh process after lost acknowledgement does not rerun completed work");
  deepEqual(good.shell.queue.pending(), []); deepEqual(good.shell.queue.deadLetters(), []);
  accepted(await fresh.shutdown()); accepted(await good.shell.shutdown());
  equal((await good.shell.runDelivery(good.message)).ok, false, "shutdown forbids new direct execution");

  let failedHandlers = 0;
  const flaky = await fixture(() => { failedHandlers++; throw Error(privateValue); });
  const retry = accepted(await flaky.shell.runDelivery(flaky.message));
  equal(retry.status, "retry");
  if (retry.status !== "retry") throw Error("Expected retry");
  equal(retry.attempt, 1); equal(retry.delayMs, 500);
  const released = await flaky.processing.get(outboxEntryId("external-fixture"));
  equal(released?.state, "retry-eligible"); equal(released?.retryAt, "2026-11-26T12:00:00.500Z");
  deepEqual(flaky.shell.queue.pending(), []);
  const restarted = accepted(await createPlatformWorkerShell(flaky.options)); accepted(await restarted.start());
  const tooEarly = await restarted.runDelivery(flaky.message);
  equal(tooEarly.ok, false); if (!tooEarly.ok) equal(tooEarly.error.diagnosticRecord?.code, "platform-worker.external-delivery-rejected");
  equal(failedHandlers, 1); equal((await flaky.processing.get(outboxEntryId("external-fixture")))?.attempt, 1);
  flaky.advance(500);
  const terminal = accepted(await restarted.runDelivery(flaky.message));
  equal(terminal.status, "terminal"); equal(terminal.attempt, 2);
  equal((await flaky.processing.get(outboxEntryId("external-fixture")))?.completion?.outcome, "terminal-failure");
  equal(accepted(await restarted.runDelivery(flaky.message)).status, "terminal");
  equal(failedHandlers, 2, "terminal redelivery waits for transport redrive without invoking business logic");
  deepEqual(restarted.queue.deadLetters(), []); deepEqual(restarted.queue.pending(), []);
  equal(JSON.stringify(flaky.records).includes(privateValue), false);

  let busyHandlers = 0;
  const busy = await fixture(() => { busyHandlers++; });
  accepted(await busy.processing.claim({ outboxEntryId: outboxEntryId("external-fixture"), owner, acquiredAt: isoDateTimeFromDate(busy.clock.now()), leaseDurationMs: 1000 }));
  equal((await busy.shell.runDelivery(busy.message)).ok, false);
  equal(busyHandlers, 0); equal((await busy.processing.get(outboxEntryId("external-fixture")))?.attempt, 1);
  busy.advance(1000);
  const afterExpiry = accepted(await busy.shell.runDelivery(busy.message));
  equal(afterExpiry.status, "succeeded"); equal(afterExpiry.attempt, 2); equal(busyHandlers, 1);

  for (const mutation of [
    (message: QueueMessage) => ({ ...message, version: accepted(queueMessageVersion(2)) }),
    (message: QueueMessage) => ({ ...message, tenantId: tenantId(privateValue) }),
    (message: QueueMessage) => ({ ...message, payload: { ...message.payload, privateValue } }),
  ]) {
    let calls = 0; const rejected = await fixture(() => { calls++; });
    const result = accepted(await rejected.shell.runDelivery(mutation(rejected.message)));
    equal(result.status, "terminal"); equal(calls, 0);
    equal(await rejected.processing.get(outboxEntryId("external-fixture")), null);
    equal(JSON.stringify(rejected.records).includes(privateValue), false);
    assertOk(rejected.records.some(record => (record as { code?: string }).code === "platform-worker.external-delivery-rejected"));
  }
  const absent = await fixture(() => { throw Error("Must not execute"); });
  const noOutbox = accepted(await createPlatformWorkerShell({ ...absent.options, durableOutboxProcessing: { processingStore: absent.processing, owner, leaseDurationMs: 1000 } }));
  accepted(await noOutbox.start()); equal(accepted(await noOutbox.runDelivery(absent.message)).status, "terminal");
  equal(await absent.processing.get(outboxEntryId("external-fixture")), null);
  const foreign = accepted(await createPlatformWorkerShell({ ...absent.options, durableOutboxProcessing: { processingStore: absent.processing, outbox: createInMemoryPlatformOutboxStore(), owner, leaseDurationMs: 1000 } }));
  accepted(await foreign.start()); equal(accepted(await foreign.runDelivery(absent.message)).status, "terminal");
  equal(await absent.processing.get(outboxEntryId("external-fixture")), null);

  let effects = 0;
  const uncertain = await fixture(() => { effects++; });
  const original = uncertain.processing.complete;
  const completionFailure = { ok: false as const, error: { code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED" as const, defaultMessage: privateValue } };
  uncertain.processing.complete = async () => completionFailure;
  const failedCompletion = await uncertain.shell.runDelivery(uncertain.message);
  equal(failedCompletion.ok, false);
  if (!failedCompletion.ok) equal(failedCompletion.error.cause, completionFailure.error, "the durable failure is preserved as the worker cause");
  equal(effects, 1); equal((await uncertain.processing.get(outboxEntryId("external-fixture")))?.state, "claimed");
  equal((await uncertain.shell.runDelivery(uncertain.message)).ok, false); equal(effects, 1);
  uncertain.processing.complete = original;
  uncertain.advance(1000);
  equal(accepted(await uncertain.shell.runDelivery(uncertain.message)).status, "succeeded");
  equal(effects, 2, "crash after effect but before completion permits at-least-once re-execution");

  const completionThrow = Object.freeze(new Error(privateValue));
  let throwEffects = 0, completionCalls = 0, releases = 0;
  const thrown = await fixture(() => { throwEffects++; }, { maxAttempts: 1 });
  thrown.processing.complete = async () => { completionCalls++; throw completionThrow; };
  thrown.processing.release = async () => { releases++; throw Error("must not release after uncertain completion"); };
  const thrownResult = await thrown.shell.runDelivery(thrown.message);
  equal(thrownResult.ok, false); if (!thrownResult.ok) equal(thrownResult.error.cause, completionThrow);
  equal(throwEffects, 1); equal(completionCalls, 1, "completion uncertainty must not trigger a second terminal-completion write");
  equal(releases, 0); equal((await thrown.processing.get(outboxEntryId("external-fixture")))?.state, "claimed");

  const wrongCompletion = await fixture(() => undefined);
  const complete = wrongCompletion.processing.complete;
  wrongCompletion.processing.complete = input => complete({ ...input, outcome: "terminal-failure" });
  const mismatched = await wrongCompletion.shell.runDelivery(wrongCompletion.message);
  equal(mismatched.ok, false);
  if (!mismatched.ok) deepEqual(mismatched.error.diagnosticRecord?.detail, { field: "completion-outcome", reason: "mismatch", effect: "completion-not-established" });

  const terminalConflict = await fixture(() => { throw Error(privateValue); }, { maxAttempts: 1 });
  const terminalComplete = terminalConflict.processing.complete;
  terminalConflict.processing.complete = input => terminalComplete({ ...input, outcome: "succeeded" });
  const notTerminal = await terminalConflict.shell.runDelivery(terminalConflict.message);
  equal(notTerminal.ok, false, "a conflicting completion is not reported as a terminal outcome");
  if (!notTerminal.ok) deepEqual(notTerminal.error.diagnosticRecord?.detail, { field: "completion-outcome", reason: "mismatch", effect: "completion-not-established" });
  equal(accepted(await terminalConflict.shell.runDelivery(terminalConflict.message)).status, "succeeded", "a later delivery may acknowledge the independently established durable success");

  const exhausted = await fixture(() => { throw Error("Budget must prevent handler"); });
  for (let index = 0; index < 2; index++) {
    accepted(await exhausted.processing.claim({ outboxEntryId: outboxEntryId("external-fixture"), owner, acquiredAt: isoDateTimeFromDate(exhausted.clock.now()), leaseDurationMs: 1000 }));
    exhausted.advance(1000);
  }
  equal(accepted(await exhausted.shell.runDelivery(exhausted.message)).status, "terminal");

  const raw = Object.freeze(new Error(privateValue));
  const invalidDelay = await fixture(() => { throw raw; }, { retryBackoffMs: () => { throw raw; } });
  await rejects(invalidDelay.shell.runDelivery(invalidDelay.message), cause => cause === raw);
  equal((await invalidDelay.processing.get(outboxEntryId("external-fixture")))?.state, "claimed", "failed retry instruction leaves the lease recoverable");
  console.log("External worker delivery, durable attempts/deadlines, scoped envelope and uncertain completion tests passed.");
}
function accepted<T>(result: Result<T, unknown>): T { if (!result.ok) throw result.error; return result.value; }
void main().catch(error => { console.error(error); process.exitCode = 1; });
