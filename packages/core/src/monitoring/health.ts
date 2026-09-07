import {
  copyJsonValue,
  type ISODateTime,
  type JsonValue,
  type MessageDescriptor,
} from "../shared/index";
import type { HealthCheckName, MonitoringComponentRef } from "./identifiers";
import { assertKnownValue, assertNonNegativeFiniteNumber } from "./validation";

export const healthCheckTypes = ["liveness", "readiness", "dependency", "capability"] as const;
export type HealthCheckType = (typeof healthCheckTypes)[number];

export const healthStatuses = ["healthy", "degraded", "unhealthy"] as const;
export type HealthStatus = (typeof healthStatuses)[number];

export type MonitoringMetadataValue = JsonValue;
export type MonitoringMetadata = Readonly<Record<string, MonitoringMetadataValue>>;

export interface HealthCheckResult {
  readonly name: HealthCheckName;
  readonly type: HealthCheckType;
  readonly component: MonitoringComponentRef;
  readonly status: HealthStatus;
  readonly checkedAt: ISODateTime;
  readonly durationMs?: number;
  readonly message?: MessageDescriptor;
  readonly metadata?: MonitoringMetadata;
}

export interface HealthCheck<TResult extends HealthCheckResult = HealthCheckResult> {
  check(): Promise<TResult> | TResult;
}

export function monitoringMetadata<TValue extends MonitoringMetadata>(value: TValue): TValue {
  return copyMonitoringMetadata(value);
}

export function healthCheckResult(input: {
  readonly name: HealthCheckName;
  readonly type: HealthCheckType;
  readonly component: MonitoringComponentRef;
  readonly status: HealthStatus;
  readonly checkedAt: ISODateTime;
  readonly durationMs?: number;
  readonly message?: MessageDescriptor;
  readonly metadata?: MonitoringMetadata;
}): HealthCheckResult {
  assertKnownValue("health check type", input.type, healthCheckTypes);
  assertKnownValue("health status", input.status, healthStatuses);

  if (input.durationMs !== undefined) {
    assertNonNegativeFiniteNumber("health check durationMs", input.durationMs);
  }

  return {
    name: input.name,
    type: input.type,
    component: { ...input.component },
    status: input.status,
    checkedAt: input.checkedAt,
    ...(input.durationMs === undefined ? {} : { durationMs: input.durationMs }),
    ...(input.message === undefined ? {} : { message: input.message }),
    ...(input.metadata === undefined ? {} : { metadata: copyMonitoringMetadata(input.metadata) }),
  };
}

export function fixedHealthCheck<TResult extends HealthCheckResult>(result: TResult): HealthCheck<TResult> {
  return {
    check: () => healthCheckResult(result) as TResult,
  };
}

function copyMonitoringMetadata<TValue extends MonitoringMetadata>(value: TValue): TValue {
  return Object.fromEntries(
    Object.entries(value).map(([key, nestedValue]) => [key, copyJsonValue(nestedValue, "monitoring metadata")]),
  ) as TValue;
}
