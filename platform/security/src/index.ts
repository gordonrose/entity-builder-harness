import type { Permission } from "@kanbien/core/authz";
import type { Clock, JsonValue, Result } from "@kanbien/core/shared";

export type PlatformSecurityErrorCode =
  | "PLATFORM_SECURITY_FORBIDDEN"
  | "PLATFORM_SECURITY_RATE_LIMITED";

export interface PlatformSecurityError {
  readonly code: PlatformSecurityErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
}

export interface PlatformAuthenticationResult {
  readonly authenticated: boolean;
  readonly permissions: readonly Permission[];
}

export interface PlatformCorsPolicy {
  readonly allowedOrigin?: string;
  readonly allowedMethods?: readonly string[];
  readonly allowedHeaders?: readonly string[];
  readonly allowCredentials?: boolean;
}

export interface PlatformSecurityHeadersOptions {
  readonly cors?: PlatformCorsPolicy;
}

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

interface RateLimitBucket {
  readonly windowStartedAtMs: number;
  readonly count: number;
}

export const denyByDefaultAuthenticationResult: PlatformAuthenticationResult = {
  authenticated: false,
  permissions: [],
};

export function createPlatformSecurityHeaders(
  options: PlatformSecurityHeadersOptions = {},
): Readonly<Record<string, string>> {
  return {
    "content-type": "application/json; charset=utf-8",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    ...(options.cors?.allowedOrigin === undefined ? {} : { "access-control-allow-origin": options.cors.allowedOrigin }),
    ...(options.cors?.allowedMethods === undefined ? {} : { "access-control-allow-methods": options.cors.allowedMethods.join(", ") }),
    ...(options.cors?.allowedHeaders === undefined ? {} : { "access-control-allow-headers": options.cors.allowedHeaders.join(", ") }),
    ...(options.cors?.allowCredentials === undefined ? {} : { "access-control-allow-credentials": String(options.cors.allowCredentials) }),
  };
}

export function corsPolicyForOrigin(origin: string | undefined): PlatformCorsPolicy {
  if (origin === undefined || origin.length === 0) {
    return {};
  }

  return {
    allowedOrigin: origin,
    allowedMethods: ["GET", "POST", "PUT", "PATCH", "DELETE"],
    allowedHeaders: ["authorization", "content-type", "x-request-id"],
  };
}

export function authorizePlatformPermissions(
  required: readonly Permission[],
  actual: readonly Permission[],
): Result<void, PlatformSecurityError> {
  const missingPermission = required.find((permission) => !actual.includes(permission));
  if (missingPermission !== undefined) {
    return {
      ok: false,
      error: {
        code: "PLATFORM_SECURITY_FORBIDDEN",
        defaultMessage: "A required route permission is missing.",
        details: { permission: missingPermission },
      },
    };
  }

  return { ok: true, value: undefined };
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

export function platformRateLimitError(retryAfterMs?: number): PlatformSecurityError {
  return {
    code: "PLATFORM_SECURITY_RATE_LIMITED",
    defaultMessage: "Request rate limit exceeded.",
    ...(retryAfterMs === undefined ? {} : { details: { retryAfterMs } }),
  };
}
