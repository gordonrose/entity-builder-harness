import { deepEqual, equal, throws } from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as sharedConfiguration from "../../src/rate-limit-configuration";
import { parseDiagnosticRecord, type DiagnosticDefinition } from "@kanbien/core/diagnostics";
import {
  createInMemoryPlatformRateLimiter, platformSecurityDiagnosticCatalog,
  assertPlatformRateLimitPositiveInteger, securityRateLimitPositiveIntegerFailureRecord,
  securityConfigurationPredicateRecord, securityDiagnosticRecordsFrom, securityFailureDiagnosticRecord,
  type InMemoryPlatformRateLimiterOptions,
} from "../../src/index";

const canary = "synthetic-private-rate-limit-canary";
const primary = (reference: string) => ({ schema: "core/diagnostic-record/v1", code: "security.rate-limit.configuration-invalid", definitionVersion: 1,
  detail: { phase: "rate-limit", reason: "configuration-invalid", effect: "not-assessed", reference } });
const companion = (field: string, reason: string) => ({ schema: "core/diagnostic-record/v1", code: "security.configuration-predicate-invalid", definitionVersion: 1,
  detail: { field, reason, phase: "configuration", effect: "rejected" } });
const fields = [["limit", "limit"], ["windowMs", "window"], ["maxBuckets", "bucket-capacity"]] as const;
const invalids: readonly (readonly [unknown, string])[] = [[NaN, "not-finite"], [Infinity, "not-finite"], [-Infinity, "not-finite"], [1.5, "not-integer"], [-1.5, "not-integer"],
  [0, "not-positive"], [-1, "not-positive"], [canary, "wrong-type"], [false, "wrong-type"], [{}, "wrong-type"], [[], "wrong-type"], [1n, "wrong-type"], [Symbol(canary), "wrong-type"]];
for (const [option, field] of fields) for (const [value, reason] of invalids) {
  const reads: string[] = [];
  let clockReads = 0, clockCalls = 0;
  const options = {
    get limit() { reads.push("limit"); return option === "limit" ? value : 1; },
    get windowMs() { reads.push("windowMs"); return option === "windowMs" ? value : 1000; },
    get maxBuckets() { reads.push("maxBuckets"); return option === "maxBuckets" ? value : 1; },
    get clock() { clockReads++; return { now() { clockCalls++; return new Date(0); } }; },
  } as unknown as InMemoryPlatformRateLimiterOptions;
  throws(() => createInMemoryPlatformRateLimiter(options), (error: unknown) => {
    equal(error instanceof RangeError, true);
    equal((error as Error).message, `${option} must be a positive integer.`);
    deepEqual(securityFailureDiagnosticRecord(error), primary(field), "historical primary is unchanged");
    deepEqual(securityDiagnosticRecordsFrom(error), [primary(field), companion(field, reason)]);
    equal(JSON.stringify(securityDiagnosticRecordsFrom(error)).includes(canary), false);
    return true;
  });
  deepEqual(reads, ["limit", "windowMs", "maxBuckets"], "all three option snapshots retain original once-only read order");
  deepEqual([clockReads, clockCalls], [0, 0], "constructor rejection precedes clock capture and invocation");
}
let coercionReads = 0;
const noCoercion = { get valueOf() { coercionReads++; throw new Error(canary); } };
throws(() => createInMemoryPlatformRateLimiter({ limit: noCoercion as never }), (error: unknown) => {
  deepEqual(securityDiagnosticRecordsFrom(error), [primary("limit"), companion("limit", "wrong-type")]);
  return true;
});
equal(coercionReads, 0);
throws(() => createInMemoryPlatformRateLimiter({ limit: 0, windowMs: 0, maxBuckets: 0 }), (error: unknown) => {
  equal((error as Error).message, "limit must be a positive integer.");
  deepEqual(securityDiagnosticRecordsFrom(error), [primary("limit"), companion("limit", "not-positive")]);
  return true;
});
throws(() => createInMemoryPlatformRateLimiter({ limit: 1, windowMs: 0, maxBuckets: 0 }), (error: unknown) => {
  equal((error as Error).message, "windowMs must be a positive integer.");
  deepEqual(securityDiagnosticRecordsFrom(error), [primary("window"), companion("window", "not-positive")]);
  return true;
});
for (const [option] of fields) for (const value of [undefined, null, 1, 2, Number.MAX_SAFE_INTEGER + 1]) {
  let clockCalls = 0;
  const limiter = createInMemoryPlatformRateLimiter({ [option]: value, clock: { now() { clockCalls++; return new Date(0); } } } as InMemoryPlatformRateLimiterOptions);
  equal(clockCalls, 0);
  deepEqual(limiter.check(canary), { allowed: true }, "nullish defaults and existing positive integer acceptance remain");
  equal(clockCalls, 1);
}
for (const limit of [undefined, null]) {
  const limiter = createInMemoryPlatformRateLimiter({ limit, clock: { now: () => new Date(0) } } as unknown as InMemoryPlatformRateLimiterOptions);
  for (let index = 0; index < 1000; index++) deepEqual(limiter.check("same-key"), { allowed: true });
  deepEqual(limiter.check("same-key"), { allowed: false, retryAfterMs: 60_000, diagnosticRecord: {
    schema: "core/diagnostic-record/v1", code: "security.rate-limit.quota-exhausted", definitionVersion: 1,
    detail: { phase: "rate-limit", reason: "quota-exhausted", effect: "not-assessed" },
  } });
}
for (const windowMs of [undefined, null]) {
  let now = 0;
  const limiter = createInMemoryPlatformRateLimiter({ limit: 1, windowMs, clock: { now: () => new Date(now) } } as unknown as InMemoryPlatformRateLimiterOptions);
  deepEqual(limiter.check("same-key"), { allowed: true });
  now = 59_999;
  equal(limiter.check("same-key").retryAfterMs, 1);
  now = 60_000;
  deepEqual(limiter.check("same-key"), { allowed: true });
}
const definition = platformSecurityDiagnosticCatalog.definitions.find((candidate) => candidate.code === "security.configuration-predicate-invalid") as DiagnosticDefinition | undefined;
if (!definition) throw new Error("Expected selected predicate definition.");
for (const field of ["table", "region", "limit", "window", "bucket-capacity"] as const) for (const reason of ["empty", "wrong-type", "not-finite", "not-integer", "not-positive"] as const) {
  deepEqual(securityConfigurationPredicateRecord(field, reason), companion(field, reason));
}
throws(() => securityConfigurationPredicateRecord(canary as never, "empty"), { name: "TypeError", message: "PLATFORM_SECURITY_DIAGNOSTIC_INVALID" });
throws(() => securityConfigurationPredicateRecord("table", canary as never), { name: "TypeError", message: "PLATFORM_SECURITY_DIAGNOSTIC_INVALID" });
const valid = companion("limit", "not-positive");
equal(parseDiagnosticRecord(definition, { ...valid, detail: { ...valid.detail, value: canary } }).ok, false);
equal(parseDiagnosticRecord(definition, { ...valid, detail: { ...valid.detail, phase: canary } }).ok, false);
equal(parseDiagnosticRecord(definition, { ...valid, detail: { ...valid.detail, effect: "unknown" } }).ok, false);
console.log("Security configuration predicates retain legacy RangeErrors, exact companions, defaults and option/clock read order.");

for (const [option, field] of fields) {
  for (const value of [1, 2, Number.MAX_SAFE_INTEGER + 1]) {
    equal(securityRateLimitPositiveIntegerFailureRecord(field, value), undefined);
    equal(assertPlatformRateLimitPositiveInteger(option, value), undefined);
  }
  for (const [value, reason] of [[undefined, "wrong-type"], [null, "wrong-type"], ...invalids] as const) {
    deepEqual(securityRateLimitPositiveIntegerFailureRecord(field, value), companion(field, reason));
    throws(() => assertPlatformRateLimitPositiveInteger(option, value), (error: unknown) => {
      equal(error instanceof RangeError, true);
      equal((error as Error).message, option + " must be a positive integer.");
      deepEqual(securityDiagnosticRecordsFrom(error), [primary(field), companion(field, reason)]);
      return true;
    });
  }
}
throws(() => securityRateLimitPositiveIntegerFailureRecord(canary as never, 1), {
  name: "TypeError", message: "PLATFORM_SECURITY_RATE_LIMIT_FIELD_INVALID",
});
throws(() => assertPlatformRateLimitPositiveInteger(canary as never, 1), {
  name: "TypeError", message: "PLATFORM_SECURITY_RATE_LIMIT_SETTING_INVALID",
});

// Execute the real compiled consumer with only its shared configuration dependency replaced.
const filename = require.resolve("../../src/rate-limiting"), localRequire = createRequire(filename);
const fixture = { exports: {} as typeof import("../../src/rate-limiting") };
const sharedCalls: unknown[] = [];
const forcedFailure = new Error("fixture-shared-guard-stop");
let stopAtWindow = false, dependentClockReads = 0;
new Function("require", "module", "exports", readFileSync(filename, "utf8"))(
  (name: string) => name === "./rate-limit-configuration" ? { ...sharedConfiguration,
    assertPlatformRateLimitPositiveInteger: (option: Parameters<typeof assertPlatformRateLimitPositiveInteger>[0], value: unknown) => {
      sharedCalls.push([option, value]);
      if (stopAtWindow && option === "windowMs") throw forcedFailure;
      return sharedConfiguration.assertPlatformRateLimitPositiveInteger(option, value);
    },
  } : localRequire(name), fixture, fixture.exports,
);
fixture.exports.createInMemoryPlatformRateLimiter({ limit: 3, windowMs: 4, maxBuckets: 5 });
deepEqual(sharedCalls, [["limit", 3], ["windowMs", 4], ["maxBuckets", 5]], "copied local checks cannot satisfy actual shared-call wiring");
sharedCalls.length = 0;
stopAtWindow = true;
throws(() => fixture.exports.createInMemoryPlatformRateLimiter({ limit: 1, windowMs: 1, maxBuckets: 1,
  get clock(): never { dependentClockReads++; throw new Error("Unexpected clock capture."); },
}), (error: unknown) => error === forcedFailure);
deepEqual(sharedCalls, [["limit", 1], ["windowMs", 1]]);
equal(dependentClockReads, 0, "the real caller honours shared rejection before dependent work");
