import { createHash } from "node:crypto";
import type { Clock } from "@kanbien/core";
import type { PlatformAuthenticationResult } from "./authentication";
import type { PlatformSecurityError } from "./errors";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { observeSecurityFailure, securityDiagnosticRecordsFrom, securityFailureDiagnosticRecord, securityOperationDiagnosticRecord, securityRateLimitClockFailureRecord } from "./diagnostics";

import { assertPlatformRateLimitPositiveInteger } from "./rate-limit-configuration";

export interface PlatformRateLimitDecision {
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly allowed: boolean;
  readonly retryAfterMs?: number;
}

export interface PlatformRateLimiter {
  check(key: string): PlatformRateLimitDecision | Promise<PlatformRateLimitDecision>;
}

export interface InMemoryPlatformRateLimiter extends PlatformRateLimiter {
  check(key: string): PlatformRateLimitDecision;
}

export interface InMemoryPlatformRateLimiterOptions {
  readonly limit?: number;
  readonly windowMs?: number;
  readonly maxBuckets?: number;
  readonly clock?: Clock;
}

export interface PlatformRateLimitKeyInput {
  readonly authentication?: PlatformAuthenticationResult;
  readonly bearerToken?: string;
  readonly clientAddress?: string;
}

interface RateLimitBucket {
  readonly windowStartedAtMs: number;
  readonly count: number;
}

export function createInMemoryPlatformRateLimiter(
  options: InMemoryPlatformRateLimiterOptions = {},
): InMemoryPlatformRateLimiter {
  const limit = options.limit ?? 1000;
  const windowMs = options.windowMs ?? 60_000;
  const maxBuckets = options.maxBuckets ?? 10_000;
  assertPlatformRateLimitPositiveInteger("limit", limit);
  assertPlatformRateLimitPositiveInteger("windowMs", windowMs);
  assertPlatformRateLimitPositiveInteger("maxBuckets", maxBuckets);
  const clock = options.clock ?? { now: () => new Date() };
  const buckets = new Map<string, RateLimitBucket>();

  return {
    check(key) {
      let nowMs: number;
      try { nowMs = clock.now().getTime(); }
      catch (error) {
        // Private retention works for frozen objects, without wrapping primitives.
        if (typeof error === "object" && error !== null) observeSecurityFailure(error, securityRateLimitClockFailureRecord());
        throw error;
      }
      const current = buckets.get(key);
      if (current === undefined || nowMs - current.windowStartedAtMs >= windowMs) {
        pruneExpiredBuckets(buckets, nowMs, windowMs);
        if (buckets.size >= maxBuckets && current === undefined) {
          return { allowed: false, retryAfterMs: windowMs, diagnosticRecord: securityOperationDiagnosticRecord("rate-limit", "bucket-capacity-exhausted") };
        }
        buckets.set(key, { windowStartedAtMs: nowMs, count: 1 });
        return { allowed: true };
      }

      if (current.count >= limit) {
        return {
          allowed: false,
          diagnosticRecord: securityOperationDiagnosticRecord("rate-limit", "quota-exhausted"),
          retryAfterMs: Math.max(0, windowMs - (nowMs - current.windowStartedAtMs)),
        };
      }

      buckets.set(key, { ...current, count: current.count + 1 });
      return { allowed: true };
    },
  };
}

export function platformRateLimitKey(input: PlatformRateLimitKeyInput): string {
  if (input.authentication?.rateLimitKey !== undefined) {
    return input.authentication.rateLimitKey;
  }

  const bearerToken = input.bearerToken;
  if (bearerToken !== undefined) {
    return `token:${sha256(bearerToken)}`;
  }

  if (input.clientAddress !== undefined && input.clientAddress.length > 0) {
    return `ip:${input.clientAddress}`;
  }

  return "anonymous";
}

function pruneExpiredBuckets(
  buckets: Map<string, RateLimitBucket>,
  nowMs: number,
  windowMs: number,
): void {
  for (const [key, bucket] of buckets) {
    if (nowMs - bucket.windowStartedAtMs >= windowMs) {
      buckets.delete(key);
    }
  }
}


/** Record the actual limiter invocation, never derive category by inspecting its key. */
export async function observePlatformRateLimitCheck(limiter: PlatformRateLimiter, key: string, context: { readonly boundary: "transport" | "principal"; readonly keyCategory: "client-address" | "principal" | "anonymous" }): Promise<PlatformRateLimitDecision> {
  try {
    const decision = await limiter.check(key);
    if (decision.allowed) return decision;
    const retained = securityFailureDiagnosticRecord(decision);
    const reason = retained?.code === "security.rate-limit.quota-exhausted" ? "quota-exhausted" : retained?.code === "security.rate-limit.bucket-capacity-exhausted" ? "bucket-capacity-exhausted" : "rejected-unclassified";
    const retryAfterMs = decision.retryAfterMs;
    return { allowed: false, ...(retryAfterMs === undefined ? {} : { retryAfterMs }), diagnosticRecord: securityOperationDiagnosticRecord("rate-limit", reason, context) };
  } catch (error) {
    const companions = securityDiagnosticRecordsFrom(error).filter((record) => record.code.startsWith("security.peer-")
      || record.code === "security.rate-limit-clock-failed" && record.definitionVersion === 1);
    throw observeSecurityFailure(error, securityOperationDiagnosticRecord("rate-limit", "dependency-failed", context), companions);
  }
}

export function platformRateLimitError(retryAfterMs?: number): PlatformSecurityError {
  return {
    code: "PLATFORM_SECURITY_RATE_LIMITED",
    defaultMessage: "Request rate limit exceeded.",
    ...(retryAfterMs === undefined ? {} : { details: { retryAfterMs } }),
  };
}

function sha256(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}
