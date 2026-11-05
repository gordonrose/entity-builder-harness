import { brand, type Brand } from "../shared/index";
import { assertDottedName, assertNonEmpty, assertToken } from "./validation";
import type { MetricValidationObserver } from "./diagnostics";
import type { CoreMonitoringDiagnosticOptions, CoreMonitoringValidationDetail } from "./boundary-diagnostics";
import { MonitoringObservation } from "./observations";

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

export function monitoringComponentName(value: string, diagnostics?: CoreMonitoringDiagnosticOptions): MonitoringComponentName {
  return observedName("monitoring component name", "component-name", value, false, diagnostics) as MonitoringComponentName;
}

export function monitoringComponent(input: {
  readonly type: MonitoringComponentType;
  readonly name: string | MonitoringComponentName;
}, diagnostics?: CoreMonitoringDiagnosticOptions): MonitoringComponentRef {
  const observation = new MonitoringObservation("component", diagnostics);
  return observation.run(() => {
    if (!observation.at("predicate-invocation", "component-type", () => monitoringComponentTypes.includes(input.type))) {
      throw observation.reject(`monitoring component type must be one of: ${monitoringComponentTypes.join(", ")}.`, "component-type", "closed-value-rejected");
    }
    return {
      type: observation.at("result-copy", "component-type", () => input.type),
      name: observation.at("input-projection", "component-name", () => {
        const value = input.name;
        observation.at("predicate-invocation", "component-name", () => assertDottedName("monitoring component name", value, false, undefined, undefined, (message, reason) => observation.reject(message, "component-name", reason)));
        return brand<string, "MonitoringComponentName">(value);
      }),
    };
  });
}

export function healthCheckName(value: string, diagnostics?: CoreMonitoringDiagnosticOptions): HealthCheckName {
  return observedName("health check name", "health-name", value, true, diagnostics) as HealthCheckName;
}

export function metricName(value: string, observer?: MetricValidationObserver): MetricName {
  assertDottedName("metric name", value, true, "name", observer);
  return brand<string, "MetricName">(value);
}

export function metricUnit(value: string, observer?: MetricValidationObserver): MetricUnit {
  assertToken("metric unit", value, "unit", observer);
  return brand<string, "MetricUnit">(value);
}

export function monitoringSignalName(value: string, diagnostics?: CoreMonitoringDiagnosticOptions): MonitoringSignalName {
  return observedName("monitoring signal name", "signal-name", value, true, diagnostics) as MonitoringSignalName;
}

export function traceSpanName(value: string, diagnostics?: CoreMonitoringDiagnosticOptions): TraceSpanName {
  return observedName("trace span name", "span-name", value, true, diagnostics) as TraceSpanName;
}

export function traceId(value: string, diagnostics?: CoreMonitoringDiagnosticOptions): TraceId {
  return observedTraceIdentifier("trace ID", "trace-id", value, diagnostics) as TraceId;
}

export function spanId(value: string, diagnostics?: CoreMonitoringDiagnosticOptions): SpanId {
  return observedTraceIdentifier("span ID", "span-id", value, diagnostics) as SpanId;
}

function observedName(label: string, field: CoreMonitoringValidationDetail["field"], value: string, requireDot: boolean, diagnostics?: CoreMonitoringDiagnosticOptions): string {
  const observation = new MonitoringObservation("identifier", diagnostics);
  return observation.run(() => observation.at("predicate-invocation", field, () => {
    assertDottedName(label, value, requireDot, undefined, undefined, (message, reason) => observation.reject(message, field, reason));
    return value;
  }));
}
function observedTraceIdentifier(label: string, field: "trace-id" | "span-id", value: string, diagnostics?: CoreMonitoringDiagnosticOptions): string {
  const observation = new MonitoringObservation("identifier", diagnostics);
  return observation.run(() => observation.at("predicate-invocation", field, () => {
    assertNonEmpty(label, value, undefined, undefined, (message, reason) => observation.reject(message, field, reason));
    if (!/^[A-Za-z0-9._-]{1,128}$/.test(value)) throw observation.reject(`${label} must use 1 to 128 safe identifier characters.`, field, "invalid-format");
    return value;
  }));
}
