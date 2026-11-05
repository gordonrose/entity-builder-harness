import { deepEqual, equal, match, rejects, throws } from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as sharedSecurity from "@kanbien/platform-security";
import { securityFailureDiagnosticRecord, securityDiagnosticRecordsFrom, observePlatformRateLimitCheck } from "@kanbien/platform-security";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import type { Clock } from "@kanbien/core/shared";
import {
  createDynamoDbFixedWindowPlatformRateLimiter,
  createDynamoDbFixedWindowPlatformRateLimiterFromEnv,
  createAwsSdkDynamoDbFixedWindowStore,
  dynamoDbRateLimitKeyHash,
  type DynamoDbFixedWindowIncrement,
  type DynamoDbFixedWindowPlatformRateLimiterOptions,
} from "../src/index";

async function main(): Promise<void> {
  sharedConfigurationWiring();
  await configurationPredicates();
  await clockObservations();
  const increments: DynamoDbFixedWindowIncrement[] = [];
  const limiter = createDynamoDbFixedWindowPlatformRateLimiter({
    tableName: "kanbien-staging-platform-shell-rate-limits",
    limit: 3,
    windowMs: 60_000,
    clock: { now: () => new Date("2026-09-06T00:00:45.000Z") },
    store: {
      increment: async (input) => {
        increments.push(input);
        return increments.length === 1 ? "allowed" : "limited";
      },
    },
  });

  const first = await limiter.check("principal:operator-123");
  deepEqual(first, { allowed: true });
  const second = await limiter.check("principal:operator-123");
  deepEqual({ allowed: second.allowed, retryAfterMs: second.retryAfterMs }, { allowed: false, retryAfterMs: 15_000 });
  deepEqual(second.diagnosticRecord?.detail, { phase: "rate-limit", reason: "quota-exhausted", effect: "not-assessed" });
  equal(JSON.stringify(second).includes("operator-123"), false);
  equal(increments[0]?.keyHash.includes("operator-123"), false);
  match(increments[0]?.keyHash ?? "", /^[a-f0-9]{64}$/);
  equal(increments[0]?.windowStartedAtMs, Date.parse("2026-09-06T00:00:00.000Z"));
  equal(increments[0]?.expiresAtEpochSeconds, Date.parse("2026-09-06T00:02:00.000Z") / 1_000);
  equal(dynamoDbRateLimitKeyHash("principal:operator-123"), increments[0]?.keyHash);

  const configured = createDynamoDbFixedWindowPlatformRateLimiterFromEnv({
    PLATFORM_RATE_LIMIT_DYNAMODB_TABLE: "kanbien-staging-platform-shell-rate-limits",
    PLATFORM_RATE_LIMIT_DYNAMODB_REGION: "eu-west-1",
    PLATFORM_RATE_LIMIT_LIMIT: "60",
    PLATFORM_RATE_LIMIT_WINDOW_MS: "60000",
  }, {
    store: { increment: async () => "allowed" },
  });
  equal(configured.ok, true);

  const missing = createDynamoDbFixedWindowPlatformRateLimiterFromEnv({});
  equal(missing.ok, false);
  if (!missing.ok) {
    equal(missing.error.code, "PLATFORM_ADAPTER_AWS_DYNAMODB_RATE_LIMIT_CONFIG_INVALID");
    equal(missing.error.details.path, "PLATFORM_RATE_LIMIT_DYNAMODB_TABLE");
    deepEqual(missing.error.diagnosticRecord?.detail, { phase: "adapter-configuration", reason: "missing", effect: "not-assessed", reference: "table" });
  }

  const failing = createDynamoDbFixedWindowPlatformRateLimiter({ tableName: "private-table-canary", limit: 1, windowMs: 1000,
    store: { increment: async () => { throw new Error("private-store-canary"); } } });
  await rejects(() => observePlatformRateLimitCheck(failing, "private-key-canary", { boundary: "principal", keyCategory: "principal" }), (error: unknown) => {
    const record = securityFailureDiagnosticRecord(error);
    deepEqual(record?.detail, { phase: "rate-limit", reason: "dependency-failed", effect: "not-assessed", boundary: "principal", keyCategory: "principal" });
    equal(JSON.stringify(record).includes("private-"), false); return true;
  });
  throws(() => createDynamoDbFixedWindowPlatformRateLimiter({ tableName: "", limit: 1, windowMs: 1000, store: { increment: async () => "allowed" } }), (error: unknown) => {
    deepEqual(securityFailureDiagnosticRecord(error)?.detail, { phase: "rate-limit", reason: "configuration-invalid", effect: "not-assessed", reference: "table" });
    deepEqual(securityDiagnosticRecordsFrom(error).slice(1), [{ schema: "core/diagnostic-record/v1", code: "security.configuration-predicate-invalid", definitionVersion: 1,
      detail: { field: "table", reason: "empty", phase: "configuration", effect: "rejected" } }]); return true;
  });
  for (const [key, reference] of [["PLATFORM_RATE_LIMIT_DYNAMODB_TABLE", "table"], ["PLATFORM_RATE_LIMIT_DYNAMODB_REGION", "region"], ["PLATFORM_RATE_LIMIT_LIMIT", "limit"], ["PLATFORM_RATE_LIMIT_WINDOW_MS", "window"]] as const) for (const value of [undefined, ""]) {
    const env = { PLATFORM_RATE_LIMIT_DYNAMODB_TABLE: "private-table", PLATFORM_RATE_LIMIT_DYNAMODB_REGION: "region", PLATFORM_RATE_LIMIT_LIMIT: "1", PLATFORM_RATE_LIMIT_WINDOW_MS: "1000", [key]: value };
    const result = createDynamoDbFixedWindowPlatformRateLimiterFromEnv(env);
    equal(result.ok, false); if (!result.ok) deepEqual(result.error.diagnosticRecord?.detail, { phase: "adapter-configuration", reason: value === undefined ? "missing" : "empty", effect: "not-assessed", reference });
  }
  const invalid = createDynamoDbFixedWindowPlatformRateLimiterFromEnv({ PLATFORM_RATE_LIMIT_DYNAMODB_TABLE: "table", PLATFORM_RATE_LIMIT_DYNAMODB_REGION: "region", PLATFORM_RATE_LIMIT_LIMIT: "private-canary", PLATFORM_RATE_LIMIT_WINDOW_MS: "1000" });
  equal(invalid.ok, false); if (!invalid.ok) deepEqual(invalid.error.diagnosticRecord?.detail, { phase: "adapter-configuration", reason: "invalid-positive-integer", effect: "not-assessed", reference: "limit" });
  const originalSend = DynamoDBClient.prototype.send;
  try {
    DynamoDBClient.prototype.send = (async () => { throw Object.assign(new Error("native-private-canary"), { cause: Object.assign(new Error("peer-private-canary"), { code: "CERT_HAS_EXPIRED" }) }); }) as typeof originalSend;
    const sdkLimiter = createDynamoDbFixedWindowPlatformRateLimiter({ tableName: "private-table", limit: 1, windowMs: 1000, store: createAwsSdkDynamoDbFixedWindowStore({ region: "eu-west-1" }) });
    await rejects(() => observePlatformRateLimitCheck(sdkLimiter, "private-key", { boundary: "transport", keyCategory: "client-address" }), (error: unknown) => {
      equal((error as Error).message, "DynamoDB shared rate-limit operation failed.");
      const records = securityDiagnosticRecordsFrom(error);
      deepEqual(records.map((record) => (record.detail as { reason: string }).reason), ["dependency-failed", "expired"]);
      equal(JSON.stringify(records).includes("private-"), false); return true;
    });
  } finally { DynamoDBClient.prototype.send = originalSend; }

  console.log("DynamoDB shared rate-limit adapter runtime test passed.");
}

function sharedConfigurationWiring(): void {
  const filename = require.resolve("../src/rate-limiter"), localRequire = createRequire(filename);
  const fixture = { exports: {} as typeof import("../src/rate-limiter") };
  const calls: unknown[] = [];
  const forcedFailure = new Error("fixture-shared-guard-stop");
  let stopDirect = false, rejectParsed = false, dependentReads = 0;
  new Function("require", "module", "exports", readFileSync(filename, "utf8"))(
    (name: string) => name === "@kanbien/platform-security" ? { ...sharedSecurity,
      assertPlatformRateLimitPositiveInteger: (option: Parameters<typeof sharedSecurity.assertPlatformRateLimitPositiveInteger>[0], value: unknown) => {
        calls.push(["assert", option, value]);
        if (stopDirect) throw forcedFailure;
        return sharedSecurity.assertPlatformRateLimitPositiveInteger(option, value);
      },
      securityRateLimitPositiveIntegerFailureRecord: (field: Parameters<typeof sharedSecurity.securityRateLimitPositiveIntegerFailureRecord>[0], value: unknown) => {
        calls.push(["observe", field, value]);
        return rejectParsed ? sharedSecurity.securityConfigurationPredicateRecord(field, "not-positive")
          : sharedSecurity.securityRateLimitPositiveIntegerFailureRecord(field, value);
      },
    } : localRequire(name), fixture, fixture.exports,
  );
  fixture.exports.createDynamoDbFixedWindowPlatformRateLimiter({ tableName: "fixture", limit: 3, windowMs: 4,
    store: { increment: async () => "allowed" },
  });
  deepEqual(calls, [["assert", "limit", 3], ["assert", "windowMs", 4]], "real direct adapter uses the shared assertion");
  calls.length = 0;
  stopDirect = true;
  throws(() => fixture.exports.createDynamoDbFixedWindowPlatformRateLimiter({ tableName: "fixture", limit: 1, windowMs: 1,
    get clock(): never { dependentReads++; throw new Error("Unexpected clock."); },
    get store(): never { dependentReads++; throw new Error("Unexpected store."); },
  }), (error: unknown) => error === forcedFailure);
  deepEqual(calls, [["assert", "limit", 1]]);
  equal(dependentReads, 0);
  calls.length = 0;
  stopDirect = false;
  const env = { PLATFORM_RATE_LIMIT_DYNAMODB_TABLE: "fixture", PLATFORM_RATE_LIMIT_DYNAMODB_REGION: "fixture",
    PLATFORM_RATE_LIMIT_LIMIT: "0x10", PLATFORM_RATE_LIMIT_WINDOW_MS: "1e2" };
  equal(fixture.exports.createDynamoDbFixedWindowPlatformRateLimiterFromEnv(env, { store: { increment: async () => "allowed" } }).ok, true);
  deepEqual(calls, [["observe", "limit", 16], ["observe", "window", 100], ["assert", "limit", 16], ["assert", "windowMs", 100]],
    "environment conversion stays local but both paths use the shared numeric check");
  calls.length = 0;
  rejectParsed = true;
  const rejected = fixture.exports.createDynamoDbFixedWindowPlatformRateLimiterFromEnv(env, {
    get store(): never { dependentReads++; throw new Error("Unexpected store."); },
    get clock(): never { dependentReads++; throw new Error("Unexpected clock."); },
  });
  equal(rejected.ok, false, "a caller ignoring the returned shared failure must fail this assertion");
  if (rejected.ok) throw new Error("Expected forced shared rejection.");
  deepEqual(rejected.error.relatedDiagnosticRecords, [sharedSecurity.securityConfigurationPredicateRecord("limit", "not-positive")]);
  deepEqual(calls, [["observe", "limit", 16], ["observe", "window", 100]], "all original environment numeric reads remain before the first returned failure");
  equal(dependentReads, 0);
}

async function configurationPredicates(): Promise<void> {
  const canary = "synthetic-private-adapter-config-canary";
  const primary = (reference: string) => ({ schema: "core/diagnostic-record/v1", code: "security.rate-limit.configuration-invalid", definitionVersion: 1,
    detail: { phase: "rate-limit", reason: "configuration-invalid", effect: "not-assessed", reference } });
  const companion = (field: string, reason: string) => ({ schema: "core/diagnostic-record/v1", code: "security.configuration-predicate-invalid", definitionVersion: 1,
    detail: { field, reason, phase: "configuration", effect: "rejected" } });
  const numeric: readonly (readonly [unknown, string])[] = [[undefined, "wrong-type"], [null, "wrong-type"], [canary, "wrong-type"], [false, "wrong-type"], [{}, "wrong-type"],
    [NaN, "not-finite"], [Infinity, "not-finite"], [-Infinity, "not-finite"], [1.5, "not-integer"], [-1.5, "not-integer"], [0, "not-positive"], [-1, "not-positive"]];
  const send = DynamoDBClient.prototype.send;
  let sdkCalls = 0;
  try {
    DynamoDBClient.prototype.send = (() => { sdkCalls++; throw new Error("Unexpected SDK call."); }) as typeof send;
    for (const [option, field] of [["limit", "limit"], ["windowMs", "window"]] as const) for (const [value, reason] of numeric) {
      const reads: string[] = [];
      let clockReads = 0, clockCalls = 0, storeReads = 0, storeCalls = 0;
      const options = {
        get tableName() { reads.push("tableName"); return canary; },
        get limit() { reads.push("limit"); return option === "limit" ? value : 1; },
        get windowMs() { reads.push("windowMs"); return option === "windowMs" ? value : 1000; },
        get clock() { clockReads++; return { now() { clockCalls++; return new Date(0); } }; },
        get store() { storeReads++; return { async increment() { storeCalls++; return "allowed" as const; } }; },
      } as unknown as DynamoDbFixedWindowPlatformRateLimiterOptions;
      throws(() => createDynamoDbFixedWindowPlatformRateLimiter(options), (error: unknown) => {
        equal(error instanceof RangeError, true);
        equal((error as Error).message, `${option} must be a positive integer.`);
        deepEqual(securityFailureDiagnosticRecord(error), primary(field), "historical primary code/version/detail are unchanged");
        deepEqual(securityDiagnosticRecordsFrom(error), [primary(field), companion(field, reason)]);
        equal(JSON.stringify(securityDiagnosticRecordsFrom(error)).includes(canary), false);
        return true;
      });
      deepEqual(reads, option === "limit" ? ["tableName", "limit"] : ["tableName", "limit", "windowMs"]);
      deepEqual([clockReads, clockCalls, storeReads, storeCalls, sdkCalls], [0, 0, 0, 0, 0]);
    }
    let tableReads = 0, laterReads = 0;
    throws(() => createDynamoDbFixedWindowPlatformRateLimiter({ get tableName() { tableReads++; return ""; },
      get limit(): never { laterReads++; throw new Error("Unexpected later field."); }, get windowMs(): never { laterReads++; throw new Error("Unexpected later field."); },
      get store(): never { laterReads++; throw new Error("Unexpected store."); }, get clock(): never { laterReads++; throw new Error("Unexpected clock."); },
    }), (error: unknown) => {
      equal(error instanceof RangeError, true); equal((error as Error).message, "tableName must not be empty.");
      deepEqual(securityDiagnosticRecordsFrom(error), [primary("table"), companion("table", "empty")]); return true;
    });
    deepEqual([tableReads, laterReads, sdkCalls], [1, 0, 0]);
    let regionReads = 0;
    throws(() => createAwsSdkDynamoDbFixedWindowStore({ get region() { regionReads++; return ""; } }), (error: unknown) => {
      equal(error instanceof RangeError, true); equal((error as Error).message, "region must not be empty.");
      deepEqual(securityDiagnosticRecordsFrom(error), [primary("region"), companion("region", "empty")]); return true;
    });
    deepEqual([regionReads, sdkCalls], [1, 0]);
    for (const tableName of [undefined, null]) throws(() => createDynamoDbFixedWindowPlatformRateLimiter({ tableName, limit: 1, windowMs: 1, store: { increment: async () => "allowed" } } as unknown as DynamoDbFixedWindowPlatformRateLimiterOptions), (error: unknown) => {
      equal(error instanceof TypeError, true);
      deepEqual(securityDiagnosticRecordsFrom(error), [], "native length-access failures do not invent an empty-string observation"); return true;
    });
    for (const region of [undefined, null]) throws(() => createAwsSdkDynamoDbFixedWindowStore({ region } as never), (error: unknown) => {
      equal(error instanceof TypeError, true); deepEqual(securityDiagnosticRecordsFrom(error), []); return true;
    });
    const acceptedTable = createDynamoDbFixedWindowPlatformRateLimiter({ tableName: 1 as never, limit: 1, windowMs: 1, store: { increment: async () => "allowed" } });
    equal(typeof acceptedTable.check, "function", "no new direct table type policy beyond the original length guard");
    for (const field of ["limit", "windowMs"] as const) for (const value of [1, Number.MAX_SAFE_INTEGER + 1]) {
      let calls = 0;
      const accepted = createDynamoDbFixedWindowPlatformRateLimiter({ tableName: " ", limit: 1, windowMs: 1, [field]: value,
        clock: { now() { calls++; return new Date(0); } }, store: { increment: async () => "allowed" } });
      equal(typeof accepted.check, "function"); equal(calls, 0, "constructor keeps integer and whitespace acceptance without invoking the clock");
    }
    let validRegionReads = 0;
    createAwsSdkDynamoDbFixedWindowStore({ get region() { validRegionReads++; return " "; } });
    deepEqual([validRegionReads, sdkCalls], [2, 0], "nonempty region retains guard and SDK-option reads without an SDK operation");
    throws(() => createDynamoDbFixedWindowPlatformRateLimiter({ tableName: "table", limit: 0, windowMs: 0, store: { increment: async () => "allowed" } }), (error: unknown) => {
      equal((error as Error).message, "limit must be a positive integer.");
      deepEqual(securityDiagnosticRecordsFrom(error), [primary("limit"), companion("limit", "not-positive")]); return true;
    });

    for (const [key, field] of [["PLATFORM_RATE_LIMIT_LIMIT", "limit"], ["PLATFORM_RATE_LIMIT_WINDOW_MS", "window"]] as const) for (const [value, reason] of [[canary, "not-finite"], ["NaN", "not-finite"], ["Infinity", "not-finite"], ["-Infinity", "not-finite"], ["1.5", "not-integer"], ["-1.5", "not-integer"], ["0", "not-positive"], ["-1", "not-positive"], [" ", "not-positive"]] as const) {
      const envReads: string[] = [];
      let storeReads = 0, clockReads = 0;
      const base = { PLATFORM_RATE_LIMIT_DYNAMODB_TABLE: "private-table", PLATFORM_RATE_LIMIT_DYNAMODB_REGION: "region", PLATFORM_RATE_LIMIT_LIMIT: "1", PLATFORM_RATE_LIMIT_WINDOW_MS: "1000", [key]: value };
      const env = Object.fromEntries(Object.entries(base).map(([name, entry]) => [name, entry]));
      const observedEnv = new Proxy(env, { get(target, property, receiver) { envReads.push(String(property)); return Reflect.get(target, property, receiver); } });
      const result = createDynamoDbFixedWindowPlatformRateLimiterFromEnv(observedEnv, { get store(): never { storeReads++; throw new Error("Unexpected store."); }, get clock(): never { clockReads++; throw new Error("Unexpected clock."); } });
      deepEqual(result, { ok: false, error: { code: "PLATFORM_ADAPTER_AWS_DYNAMODB_RATE_LIMIT_CONFIG_INVALID", defaultMessage: "DynamoDB shared rate-limit adapter configuration is invalid.",
        details: { path: key, reason: "Expected a positive integer environment value." },
        diagnosticRecord: { schema: "core/diagnostic-record/v1", code: "security.adapter-configuration.invalid-positive-integer", definitionVersion: 1,
          detail: { phase: "adapter-configuration", reason: "invalid-positive-integer", effect: "not-assessed", reference: field } },
        relatedDiagnosticRecords: [companion(field, reason)],
      } });
      deepEqual(envReads, ["PLATFORM_RATE_LIMIT_DYNAMODB_TABLE", "PLATFORM_RATE_LIMIT_DYNAMODB_REGION", "PLATFORM_RATE_LIMIT_LIMIT", "PLATFORM_RATE_LIMIT_WINDOW_MS"]);
      deepEqual([storeReads, clockReads, sdkCalls], [0, 0, 0]);
      equal(JSON.stringify(result).includes(canary), false, "parsed NaN does not expose or label a raw text cause");
    }
    for (const [key, field] of [["PLATFORM_RATE_LIMIT_LIMIT", "limit"], ["PLATFORM_RATE_LIMIT_WINDOW_MS", "windowMs"]] as const) for (const [value, expected] of [["1", 1], [" 2 ", 2], ["0x10", 16], ["1e2", 100], ["+3", 3], ["03", 3], ["9007199254740992", 9007199254740992]] as const) {
      const increments: DynamoDbFixedWindowIncrement[] = [];
      const result = createDynamoDbFixedWindowPlatformRateLimiterFromEnv({ PLATFORM_RATE_LIMIT_DYNAMODB_TABLE: "private-table", PLATFORM_RATE_LIMIT_DYNAMODB_REGION: "region", PLATFORM_RATE_LIMIT_LIMIT: "1", PLATFORM_RATE_LIMIT_WINDOW_MS: "1000", [key]: value }, {
        clock: { now: () => new Date(0) }, store: { increment: async (input) => { increments.push(input); return "allowed"; } },
      });
      equal(result.ok, true, "historical Number conversion grammar and integer bounds stay accepted");
      if (!result.ok) throw new Error("Expected accepted environment number.");
      deepEqual(await result.value.check("private-key"), { allowed: true });
      equal(increments.length, 1);
      equal(increments[0]!.limit, field === "limit" ? expected : 1);
      equal(increments[0]!.expiresAtEpochSeconds, field === "windowMs" ? Math.ceil((2 * expected) / 1000) : 2);
    }
    equal(sdkCalls, 0);
  } finally { DynamoDBClient.prototype.send = send; }
}

async function clockObservations(): Promise<void> {
  const canary = "synthetic-private-limiter-clock-canary";
  const clockRecord = { schema: "core/diagnostic-record/v1", code: "security.rate-limit-clock-failed", definitionVersion: 1,
    detail: { phase: "clock-evaluation", reason: "evaluation-threw", effect: "decision-not-returned" } };
  const primary = { schema: "core/diagnostic-record/v1", code: "security.rate-limit.dependency-failed", definitionVersion: 1,
    detail: { phase: "rate-limit", reason: "dependency-failed", effect: "not-assessed", boundary: "transport", keyCategory: "client-address" } };
  const context = { boundary: "transport", keyCategory: "client-address" } as const;
  const caught = async (run: () => unknown): Promise<unknown> => { try { await run(); } catch (error) { return error; } throw new Error("Expected clock failure."); };
  type Stage = "now-accessor" | "now-call" | "time-accessor" | "time-call";
  function fixture(stage: Stage, failure: unknown) {
    const counts = [0, 0, 0, 0];
    const date = Object.defineProperty({}, "getTime", { get() {
      counts[2]!++;
      if (stage === "time-accessor") throw failure;
      return function(this: unknown) { counts[3]!++; equal(this, date); throw failure; };
    } });
    const clock = Object.defineProperty({}, "now", { get() {
      counts[0]!++;
      if (stage === "now-accessor") throw failure;
      return function(this: unknown) { counts[1]!++; equal(this, clock); if (stage === "now-call") throw failure; return date; };
    } }) as Clock;
    let storeReads = 0, storeCalls = 0;
    const limiter = createDynamoDbFixedWindowPlatformRateLimiter({ tableName: canary, limit: 1, windowMs: 1000, clock,
      get store() { storeReads++; return { async increment() { storeCalls++; return "allowed" as const; } }; },
    });
    return { limiter, counts, storeCounts: () => [storeReads, storeCalls] };
  }
  const failures = [new Error(canary), Object.freeze(new Error(canary)), { privateValue: canary }, null, undefined, canary, 7, function privateFailure() {}];
  for (const [stage, expected] of [["now-accessor", [1, 0, 0, 0]], ["now-call", [1, 1, 0, 0]], ["time-accessor", [1, 1, 1, 0]], ["time-call", [1, 1, 1, 1]]] as const) for (const failure of failures) {
    const direct = fixture(stage, failure);
    deepEqual(direct.counts, [0, 0, 0, 0]);
    equal(await caught(() => direct.limiter.check(canary)), failure, "producer keeps object/frozen/primitive/function rejection identity");
    deepEqual(direct.counts, expected); deepEqual(direct.storeCounts(), [0, 0]);
    const objectFailure = typeof failure === "object" && failure !== null;
    deepEqual(securityDiagnosticRecordsFrom(failure), objectFailure ? [clockRecord] : []);
    const wrapped = fixture(stage, failure);
    await rejects(() => observePlatformRateLimitCheck(wrapped.limiter, canary, context), (error: unknown) => {
      if (objectFailure) equal(error, failure);
      else { equal(error instanceof Error, true); equal((error as Error).message, "Security component failed."); }
      deepEqual(securityDiagnosticRecordsFrom(error), objectFailure ? [primary, clockRecord] : [primary]);
      equal(JSON.stringify(securityDiagnosticRecordsFrom(error)).includes(canary), false);
      return true;
    });
    deepEqual(wrapped.counts, expected); deepEqual(wrapped.storeCounts(), [0, 0]);
  }
  for (const returned of [null, {}]) {
    const clock = { now: () => returned } as unknown as Clock;
    const legacy = await caught(() => clock.now().getTime()) as Error;
    const current = await caught(() => createDynamoDbFixedWindowPlatformRateLimiter({ tableName: canary, limit: 1, windowMs: 1, clock, store: { increment: async () => "allowed" } }).check(canary)) as Error;
    equal(current.constructor, legacy.constructor); equal(current.message, legacy.message);
    deepEqual(securityDiagnosticRecordsFrom(current), [clockRecord]);
  }
  let nativeReads = 0, storeCalls = 0;
  const nativeLooking = Object.defineProperties(new Error(canary), {
    code: { get() { nativeReads++; return "CERT_HAS_EXPIRED"; } }, cause: { get() { nativeReads++; throw new Error(canary); } },
  });
  await rejects(() => observePlatformRateLimitCheck(createDynamoDbFixedWindowPlatformRateLimiter({ tableName: canary, limit: 1, windowMs: 1,
    clock: { now() { throw nativeLooking; } }, store: { increment: async () => { storeCalls++; return "allowed"; } },
  }), canary, context), (error: unknown) => { equal(error, nativeLooking); deepEqual(securityDiagnosticRecordsFrom(error), [primary, clockRecord]); return true; });
  deepEqual([nativeReads, storeCalls], [0, 0], "clock failure cannot fabricate provider or peer evidence");
  const originalSend = DynamoDBClient.prototype.send;
  let sdkCalls = 0, clockCalls = 0;
  const sdkClockFailure = Object.freeze(new Error(canary));
  try {
    DynamoDBClient.prototype.send = (() => { sdkCalls++; throw new Error("Unexpected SDK call."); }) as typeof originalSend;
    const limiter = createDynamoDbFixedWindowPlatformRateLimiter({ tableName: canary, limit: 1, windowMs: 1,
      clock: { now() { clockCalls++; throw sdkClockFailure; } }, store: createAwsSdkDynamoDbFixedWindowStore({ region: "eu-west-1" }),
    });
    equal(await caught(() => limiter.check(canary)), sdkClockFailure);
    deepEqual([clockCalls, sdkCalls], [1, 0]);
    deepEqual(securityDiagnosticRecordsFrom(sdkClockFailure), [clockRecord]);
  } finally { DynamoDBClient.prototype.send = originalSend; }
  const increments: DynamoDbFixedWindowIncrement[] = [];
  let nanClockCalls = 0;
  const nanClock = createDynamoDbFixedWindowPlatformRateLimiter({ tableName: canary, limit: 1, windowMs: 1000,
    clock: { now() { nanClockCalls++; return new Date(NaN); } }, store: { increment: async (input) => { increments.push(input); return "allowed"; } },
  });
  deepEqual(await nanClock.check(canary), { allowed: true }, "successful NaN projection retains historical behavior");
  equal(nanClockCalls, 1); equal(increments.length, 1);
  equal(Number.isNaN(increments[0]!.windowStartedAtMs), true); equal(Number.isNaN(increments[0]!.expiresAtEpochSeconds), true);
}

main()
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
