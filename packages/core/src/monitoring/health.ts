import {
  copyJsonValue,
  type ISODateTime,
  type JsonValue,
  type MessageDescriptor,
} from "../shared/index";
import type { HealthCheckName, MonitoringComponentRef } from "./identifiers";
import { assertKnownValue, assertNonNegativeFiniteNumber } from "./validation";
import type { CoreMonitoringDiagnosticOptions } from "./boundary-diagnostics";
import { MonitoringObservation } from "./observations";

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

export function monitoringMetadata<TValue extends MonitoringMetadata>(value: TValue, diagnostics?: CoreMonitoringDiagnosticOptions): TValue {
  const observation = new MonitoringObservation("metadata", diagnostics);
  return observation.run(() => copyMonitoringMetadata(value, observation));
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
}, diagnostics?: CoreMonitoringDiagnosticOptions): HealthCheckResult {
  const observation = new MonitoringObservation("health-result", diagnostics);
  return observation.run(() => {
    const type = observation.at("input-projection", "health-type", () => input.type);
    observation.at("predicate-invocation", "health-type", () => assertKnownValue("health check type", type, healthCheckTypes, (message, reason) => observation.reject(message, "health-type", reason)));
    const status = observation.at("input-projection", "health-status", () => input.status);
    observation.at("predicate-invocation", "health-status", () => assertKnownValue("health status", status, healthStatuses, (message, reason) => observation.reject(message, "health-status", reason)));
    if (observation.at("input-projection", "duration", () => input.durationMs) !== undefined) {
      const duration = observation.at("input-projection", "duration", () => input.durationMs);
      observation.at("predicate-invocation", "duration", () => assertNonNegativeFiniteNumber("health check durationMs", duration!, (message, reason) => observation.reject(message, "duration", reason)));
    }
    return {
      name: observation.at("result-copy", "name", () => input.name),
      type: observation.at("result-copy", "health-type", () => input.type),
      component: observation.at("component-copy", "component", () => ({ ...input.component })),
      status: observation.at("result-copy", "health-status", () => input.status),
      checkedAt: observation.at("result-copy", "checked-at", () => input.checkedAt),
      ...(observation.at("input-projection", "duration", () => input.durationMs) === undefined ? {} : { durationMs: observation.at("result-copy", "duration", () => input.durationMs) }),
      ...(observation.at("input-projection", "message", () => input.message) === undefined ? {} : { message: observation.at("result-copy", "message", () => input.message) }),
      ...(observation.at("input-projection", "metadata", () => input.metadata) === undefined ? {} : { metadata: copyMonitoringMetadata(observation.at("input-projection", "metadata", () => input.metadata)!, observation) }),
    };
  });
}

export function fixedHealthCheck<TResult extends HealthCheckResult>(result: TResult, diagnostics?: CoreMonitoringDiagnosticOptions): HealthCheck<TResult> {
  return {
    check: () => healthCheckResult(result, diagnostics) as TResult,
  };
}

function copyMonitoringMetadata<TValue extends MonitoringMetadata>(value: TValue, observation: MonitoringObservation): TValue {
  return observation.at("metadata-enumeration", "metadata", () => Object.fromEntries(
    Object.entries(value).map(([key, nestedValue]) => {
      const copied = [key, observation.at("metadata-copy", "metadata", () => copyJsonValue(nestedValue, "monitoring metadata"))];
      return observation.at("metadata-enumeration", "metadata", () => copied);
    }),
  )) as TValue;
}
