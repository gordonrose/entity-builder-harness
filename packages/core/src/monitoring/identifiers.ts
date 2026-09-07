import { brand, type Brand } from "../shared/index";
import { assertDottedName, assertNonEmpty, assertToken } from "./validation";

export type MonitoringComponentName = Brand<string, "MonitoringComponentName">;
export type HealthCheckName = Brand<string, "HealthCheckName">;
export type MetricName = Brand<string, "MetricName">;
export type MetricUnit = Brand<string, "MetricUnit">;
export type MonitoringSignalName = Brand<string, "MonitoringSignalName">;
export type TraceSpanName = Brand<string, "TraceSpanName">;
export type TraceId = Brand<string, "TraceId">;
export type SpanId = Brand<string, "SpanId">;

export const monitoringComponentTypes = [
  "api",
  "worker",
  "database",
  "queue",
  "event-bus",
  "cache",
  "object-storage",
  "external-service",
  "platform-adapter",
  "runtime",
  "custom",
] as const;
export type MonitoringComponentType = (typeof monitoringComponentTypes)[number];

export interface MonitoringComponentRef {
  readonly type: MonitoringComponentType;
  readonly name: MonitoringComponentName;
}

export function monitoringComponentName(value: string): MonitoringComponentName {
  assertDottedName("monitoring component name", value, false);
  return brand<string, "MonitoringComponentName">(value);
}

export function monitoringComponent(input: {
  readonly type: MonitoringComponentType;
  readonly name: string | MonitoringComponentName;
}): MonitoringComponentRef {
  if (!monitoringComponentTypes.includes(input.type)) {
    throw new TypeError(`monitoring component type must be one of: ${monitoringComponentTypes.join(", ")}.`);
  }

  return {
    type: input.type,
    name: monitoringComponentName(input.name),
  };
}

export function healthCheckName(value: string): HealthCheckName {
  assertDottedName("health check name", value, true);
  return brand<string, "HealthCheckName">(value);
}

export function metricName(value: string): MetricName {
  assertDottedName("metric name", value, true);
  return brand<string, "MetricName">(value);
}

export function metricUnit(value: string): MetricUnit {
  assertToken("metric unit", value);
  return brand<string, "MetricUnit">(value);
}

export function monitoringSignalName(value: string): MonitoringSignalName {
  assertDottedName("monitoring signal name", value, true);
  return brand<string, "MonitoringSignalName">(value);
}

export function traceSpanName(value: string): TraceSpanName {
  assertDottedName("trace span name", value, true);
  return brand<string, "TraceSpanName">(value);
}

export function traceId(value: string): TraceId {
  assertTraceIdentifier("trace ID", value);
  return brand<string, "TraceId">(value);
}

export function spanId(value: string): SpanId {
  assertTraceIdentifier("span ID", value);
  return brand<string, "SpanId">(value);
}

function assertTraceIdentifier(label: string, value: string): void {
  assertNonEmpty(label, value);

  if (!/^[A-Za-z0-9._-]{1,128}$/.test(value)) {
    throw new TypeError(`${label} must use 1 to 128 safe identifier characters.`);
  }
}
