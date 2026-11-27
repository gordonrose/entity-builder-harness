import { strict as assert } from "node:assert";
import { test } from "node:test";
import { createPlatformLambdaContinuation, createPlatformLambdaDispatcherHandler, lambdaRuntimeDiagnosticCatalog } from "../../src/index";
import type { PlatformScheduleDispatcher, PlatformScheduleDispatchRunResult, PlatformPersistenceError } from "@kanbien/platform-persistence";

const quiet = (stopReason: PlatformScheduleDispatchRunResult["stopReason"]): PlatformScheduleDispatchRunResult =>
  ({ delivery: null, relayAttempts: 0, published: 0, stopReason });
const context = { getRemainingTimeInMillis: () => 60_000 };
const handler = (dispatcher: PlatformScheduleDispatcher) => createPlatformLambdaDispatcherHandler({ dispatcher, minimumRemainingMs: 2_000, minimumDeliveryRemainingMs: 15_000 });
const record = (cause: unknown) => (cause as { diagnosticRecord: { code: string; definitionVersion: number; detail: Record<string, unknown> } }).diagnosticRecord;

test("construction checks and captures both margins before any dependency work", async () => {
  let calls = 0;
  const dispatcher: PlatformScheduleDispatcher = { runOnce: async () => { calls++; return { ok: true, value: quiet("idle") }; } };
  for (const margin of [0, 100, 101]) {
    assert.throws(() => createPlatformLambdaDispatcherHandler({ dispatcher, minimumRemainingMs: 101, minimumDeliveryRemainingMs: margin }));
  }
  assert.equal(calls, 0);
  const supplied = { dispatcher, minimumRemainingMs: 100, minimumDeliveryRemainingMs: 200 };
  const invoke = createPlatformLambdaDispatcherHandler(supplied);
  supplied.minimumRemainingMs = -1;
  supplied.minimumDeliveryRemainingMs = -1;
  assert.equal((await invoke({}, context)).stopReason, "idle");
  assert.equal(calls, 1);
});

test("fixed invocation passes independent total/due budgets and does not use event contents", async () => {
  let calls = 0, remaining = 10_000;
  const invoke = handler({ runOnce: async options => {
    calls += 1;
    assert.equal(options?.shouldContinue?.(), true);
    assert.equal(options?.shouldContinueDelivery?.(), false);
    remaining = 2_000;
    assert.equal(options?.shouldContinue?.(), false);
    return { ok: true, value: quiet("requested-stop") };
  } });
  const result = await invoke({ token: "sensitive-canary", jobs: ["wrong-scope"] }, { getRemainingTimeInMillis: () => remaining });
  assert.equal(result.stopReason, "requested-stop");
  assert.equal(calls, 1);
  assert.equal(JSON.stringify(result).includes("sensitive-canary"), false);
});

for (const status of ["idle", "contended", "requested-stop", "attempt-limit"] as const) {
  test(`bounded ${status} returns the exact established invocation outcome`, async () => {
    const result = quiet(status);
    assert.equal(await handler({ runOnce: async () => ({ ok: true, value: result }) })({}, context), result);
  });
}
for (const status of ["queue-send-failed", "publish-marker-failed"] as const) {
  test(`${status} never becomes a successful managed invocation`, async () => {
    let calls = 0;
    await assert.rejects(handler({ runOnce: async () => { calls += 1; return { ok: true, value: quiet(status) }; } })({}, context), cause => {
      assert.equal(record(cause).code, "aws-lambda.dispatch-outcome-failed");
      assert.deepEqual(record(cause).detail, { status, effect: "earlier-effects-possible" });
      return true;
    });
    assert.equal(calls, 1);
  });
}
test("returned and thrown dependency causes remain the original object without replay", async () => {
  const cause: PlatformPersistenceError = { code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: "synthetic" };
  let calls = 0;
  await assert.rejects(handler({ runOnce: async () => { calls += 1; return { ok: false, error: cause }; } })({}, context), error => error === cause);
  await assert.rejects(handler({ runOnce: async () => { calls += 1; throw cause; } })({}, context), error => error === cause);
  assert.equal(calls, 2);
});

for (const [value, reason] of [[undefined, "missing"], ["secret-canary", "wrong-type"], [NaN, "not-finite"], [Infinity, "not-finite"], [1.5, "not-integer"], [0, "not-positive"], [-1, "not-positive"]] as const) {
  test(`budget rejects ${reason} before reading the provider clock`, () => {
    let reads = 0;
    assert.throws(() => createPlatformLambdaContinuation({ getRemainingTimeInMillis: () => { reads += 1; return 100; } }, value as number), error => {
      assert.equal(record(error).code, "aws-lambda.invocation-budget-invalid");
      assert.equal(record(error).detail.reason, reason);
      assert.equal(JSON.stringify(record(error)).includes("secret-canary"), false);
      return true;
    });
    assert.equal(reads, 0);
  });
}
for (const [value, reason] of [[undefined, "missing"], ["secret-canary", "wrong-type"], [Infinity, "not-finite"], [-1, "negative"]] as const) {
  test(`provider remaining-time ${reason} is not permission to start work`, () => {
    const next = createPlatformLambdaContinuation({ getRemainingTimeInMillis: () => value as number }, 100);
    assert.throws(next, error => { assert.equal(record(error).detail.reason, reason); assert.equal(record(error).detail.field, "remaining-time"); return true; });
  });
}
test("provider clock throw preserves identity and exhausted budget returns false", () => {
  const cause = { private: "do-not-log" };
  assert.throws(createPlatformLambdaContinuation({ getRemainingTimeInMillis() { throw cause; } }, 100), error => error === cause);
  assert.equal(createPlatformLambdaContinuation({ getRemainingTimeInMillis: () => 0 }, 100)(), false);
  assert.equal(createPlatformLambdaContinuation({ getRemainingTimeInMillis: () => 101 }, 100)(), true);
  assert.deepEqual(lambdaRuntimeDiagnosticCatalog.definitions.map(item => `${item.code}@${item.version}`), ["aws-lambda.invocation-budget-invalid@1", "aws-lambda.dispatch-outcome-failed@1"]);
});
