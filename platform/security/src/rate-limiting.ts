import { createHash } from "node:crypto";
import type { Clock } from "@kanbien/core";
import {
  bearerTokenFromHeaders,
  firstHeaderValue,
  type PlatformAuthenticationResult,
} from "./authentication";
import type { PlatformSecurityError } from "./errors";

export interface PlatformRateLimitDecision {
  readonly allowed: boolean;
  readonly retryAfterMs?: number;
}

export interface PlatformRateLimiter {
  check(key: string): PlatformRateLimitDecision;
}

export interface InMemoryPlatformRateLimiterOptions {
  readonly limit?: number;
  readonly windowMs?: number;
  readonly clock?: Clock;
}

export interface PlatformRateLimitKeyInput {
  readonly headers?: Readonly<Record<string, string | readonly string[]>>;
  readonly authentication?: PlatformAuthenticationResult;
}

interface RateLimitBucket {
  readonly windowStartedAtMs: number;
  readonly count: number;
}

export function createInMemoryPlatformRateLimiter(
  options: InMemoryPlatformRateLimiterOptions = {},
): PlatformRateLimiter {
  const limit = options.limit ?? 1000;
  const windowMs = options.windowMs ?? 60_000;
  const clock = options.clock ?? { now: () => new Date() };
  const buckets = new Map<string, RateLimitBucket>();

  return {
    check(key) {
      const nowMs = clock.now().getTime();
      const current = buckets.get(key);
      if (current === undefined || nowMs - current.windowStartedAtMs >= windowMs) {
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

  const bearerToken = bearerTokenFromHeaders(input.headers ?? {});
  if (bearerToken !== undefined) {
    return `token:${sha256(bearerToken)}`;
  }

  const forwardedFor = firstHeaderValue(input.headers ?? {}, "x-forwarded-for");
  if (forwardedFor !== undefined && forwardedFor.length > 0) {
    return `ip:${forwardedFor.split(",")[0]?.trim() ?? forwardedFor}`;
  }

  const realIp = firstHeaderValue(input.headers ?? {}, "x-real-ip");
  if (realIp !== undefined && realIp.length > 0) {
    return `ip:${realIp}`;
  }

  return "anonymous";
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
