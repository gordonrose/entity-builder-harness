import {
  type HealthCheckResult,
  type HealthStatus,
} from "@kanbien/core/monitoring";
import {
  isoDateTimeFromDate,
  type Clock,
  type ISODateTime,
  type JsonValue,
} from "@kanbien/core/shared";
import type { PlatformHealthRegistration } from "@kanbien/platform-contracts";
import { normalizePlatformValue } from "@kanbien/platform-observability";

export type PlatformHealthState = "live" | "ready" | "not-ready";

export interface PlatformLivenessSummary {
  readonly status: "live";
  readonly checkedAt: ISODateTime;
}

export interface PlatformReadinessSummary {
  readonly status: "ready" | "not-ready";
  readonly checkedAt: ISODateTime;
  readonly checks: readonly PlatformSafeHealthCheckResult[];
}

export interface PlatformSafeHealthCheckResult {
  readonly name: string;
  readonly type: HealthCheckResult["type"];
  readonly component: string;
  readonly status: HealthStatus;
  readonly checkedAt: ISODateTime;
  readonly durationMs?: number;
  readonly message?: string;
  readonly metadata?: Readonly<Record<string, JsonValue>>;
}

export interface PlatformReadinessInput {
  readonly lifecycleReady: boolean;
  readonly healthChecks: readonly PlatformHealthRegistration[];
  readonly clock: Clock;
}

export function platformLiveness(clock: Clock): PlatformLivenessSummary {
  return {
    status: "live",
    checkedAt: isoDateTimeFromDate(clock.now()),
  };
}

export async function platformReadiness(
  input: PlatformReadinessInput,
): Promise<PlatformReadinessSummary> {
  const checkedAt = isoDateTimeFromDate(input.clock.now());
  const checks = await Promise.all(input.healthChecks.map((registration) => runSafeHealthCheck(registration, checkedAt)));
  const checksReady = checks.every((check) => check.status === "healthy");

  return {
    status: input.lifecycleReady && checksReady ? "ready" : "not-ready",
    checkedAt,
    checks,
  };
}

export function platformHealthHttpStatus(status: PlatformHealthState): number {
  return status === "not-ready" ? 503 : 200;
}

async function runSafeHealthCheck(
  registration: PlatformHealthRegistration,
  checkedAt: ISODateTime,
): Promise<PlatformSafeHealthCheckResult> {
  try {
    return safeHealthCheckResult(await registration.check.check());
  } catch (error) {
    return {
      name: String(registration.name),
      type: "readiness",
      component: "runtime",
      status: "unhealthy",
      checkedAt,
      message: "Health check failed.",
      metadata: safeMetadata({ error }),
    };
  }
}

function safeHealthCheckResult(result: HealthCheckResult): PlatformSafeHealthCheckResult {
  return {
    name: String(result.name),
    type: result.type,
    component: String(result.component.name),
    status: result.status,
    checkedAt: result.checkedAt,
    ...(result.durationMs === undefined ? {} : { durationMs: result.durationMs }),
    ...(result.message === undefined ? {} : { message: result.message.defaultMessage }),
    ...(result.metadata === undefined ? {} : { metadata: safeMetadata(result.metadata) }),
  };
}

function safeMetadata(value: Readonly<Record<string, unknown>>): Readonly<Record<string, JsonValue>> {
  const normalized = normalizePlatformValue(value);

  if (isJsonObject(normalized)) {
    return normalized;
  }

  return { value: normalized };
}

function isJsonObject(value: JsonValue): value is Readonly<Record<string, JsonValue>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
