import { createHash } from "node:crypto";
import type { Clock } from "@kanbien/core";
import type { PlatformAuthenticationResult } from "./authentication";
import type { PlatformSecurityError } from "./errors";

export interface PlatformRateLimitDecision {
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
  assertPositiveInteger("limit", limit);
  assertPositiveInteger("windowMs", windowMs);
  assertPositiveInteger("maxBuckets", maxBuckets);
  const clock = options.clock ?? { now: () => new Date() };
  const buckets = new Map<string, RateLimitBucket>();

  return {
    check(key) {
      const nowMs = clock.now().getTime();
      const current = buckets.get(key);
      if (current === undefined || nowMs - current.windowStartedAtMs >= windowMs) {
        pruneExpiredBuckets(buckets, nowMs, windowMs);
        if (buckets.size >= maxBuckets && current === undefined) {
          return { allowed: false, retryAfterMs: windowMs };
        }
        buckets.set(key, { windowStartedAtMs: nowMs, count: 1 });
        return { allowed: true };
      }

      if (current.count >= limit) {
        return {
          allowed: false,
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

function assertPositiveInteger(name: string, value: number): void {
  if (!Number.isInteger(value) || value <= 0) {
    throw new RangeError(`${name} must be a positive integer.`);
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
