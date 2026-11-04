import type { ISODateTime } from "../shared/index";
import type { MetricName, MetricUnit } from "./identifiers";
import { assertFiniteNumber, assertKnownValue, assertNonNegativeFiniteNumber, normalizeName } from "./validation";
import { metricValidationError, type MetricValidationObserver } from "./diagnostics";
import type { CoreMonitoringDiagnosticOptions } from "./boundary-diagnostics";
import { MonitoringObservation } from "./observations";

export const metricKinds = ["counter", "gauge", "histogram", "timer"] as const;
export type MetricKind = (typeof metricKinds)[number];

export const defaultUnsafeMetricLabelNames = [
  "password",
  "passphrase",
  "passwd",
  "pwd",
  "secret",
  "clientSecret",
  "token",
  "accessToken",
  "refreshToken",
  "idToken",
  "sessionToken",
  "apiKey",
  "authorization",
  "cookie",
  "setCookie",
  "privateKey",
  "credential",
  "credentials",
  "email",
  "phone",
  "userId",
  "principalId",
  "tenant",
  "tenantId",
  "requestId",
  "correlationId",
  "traceId",
  "sessionId",
  "ipAddress",
  "httpPath",
  "url",
  "path",
] as const;

export const defaultMetricLabelStringLengthLimit = 128;

export type MetricLabelValue = string | number | boolean;
export type MetricLabels = Readonly<Record<string, MetricLabelValue>>;

export interface MetricPoint {
  readonly name: MetricName;
  readonly kind: MetricKind;
  readonly value: number;
  readonly unit: MetricUnit;
  readonly recordedAt: ISODateTime;
  readonly labels?: MetricLabels;
}

export interface Metrics {
  record(point: MetricPoint): Promise<void> | void;
}

export interface MonitoringMetricDefinition {
  readonly name: MetricName;
  readonly kind: MetricKind;
  readonly unit: MetricUnit;
}

export interface MetricLabelOptions {
  readonly additionalUnsafeLabelNames?: readonly string[];
  readonly maxStringLength?: number;
}

export const noopMetrics: Metrics = {
  record: () => undefined,
};

export function metricLabels(input: MetricLabels, options: MetricLabelOptions = {}, observer?: MetricValidationObserver, diagnostics?: CoreMonitoringDiagnosticOptions): MetricLabels {
  const observation = new MonitoringObservation("metric-labels", diagnostics);
  return observation.run(() => {
  const unsafeLabels = observation.at("label-options", "additional-unsafe-label-names", () => new Set(
    [...defaultUnsafeMetricLabelNames, ...(options.additionalUnsafeLabelNames ?? [])].map((name) => {
      const normalized = observation.at("label-normalization", "additional-unsafe-label-names", () => normalizeName(name));
      return observation.at("label-options", "additional-unsafe-label-names", () => normalized);
    }),
  ));
  const maxStringLength = observation.at("label-options", "max-string-length", () => options.maxStringLength ?? defaultMetricLabelStringLengthLimit);
  observation.at("predicate-invocation", "max-string-length", () => assertNonNegativeFiniteNumber("metric label maxStringLength", maxStringLength, (message, reason) => observation.reject(message, "max-string-length", reason)));

  const labels: Record<string, MetricLabelValue> = {};

  let index = 0;
  for (const [key, value] of observation.at("label-enumeration", "labels", () => Object.entries(input))) {
    observation.at("label-copy", "labels", () => {
    assertMetricLabelName(key, index, observer, (error) => observation.existingRejection(error));

    if (unsafeLabels.has(normalizeName(key))) {
      throw observation.existingRejection(metricValidationError(`metric label "${key}" is unsafe or too high-cardinality.`, "label", "unsafe-name", index, observer));
    }

    labels[key] = copyMetricLabelValue(key, value, maxStringLength, index, observer, (error) => observation.existingRejection(error));
    });
    index++;
    observation.at("label-enumeration", "labels", () => undefined);
  }

  return labels;
  });
}

export function metricPoint(input: {
  readonly name: MetricName;
  readonly kind: MetricKind;
  readonly value: number;
  readonly unit: MetricUnit;
  readonly recordedAt: ISODateTime;
  readonly labels?: MetricLabels;
}, diagnostics?: CoreMonitoringDiagnosticOptions): MetricPoint {
  const observation = new MonitoringObservation("metric-point", diagnostics);
  return observation.run(() => {
    const kind = observation.at("input-projection", "metric-kind", () => input.kind);
    observation.at("predicate-invocation", "metric-kind", () => assertKnownValue("metric kind", kind, metricKinds, (message, reason) => observation.reject(message, "metric-kind", reason)));
    const value = observation.at("input-projection", "metric-value", () => input.value);
    observation.at("predicate-invocation", "metric-value", () => assertFiniteNumber("metric value", value, (message, reason) => observation.reject(message, "metric-value", reason)));
    return {
      name: observation.at("result-copy", "name", () => input.name),
      kind: observation.at("result-copy", "metric-kind", () => input.kind),
      value: observation.at("result-copy", "metric-value", () => input.value),
      unit: observation.at("result-copy", "unit", () => input.unit),
      recordedAt: observation.at("result-copy", "recorded-at", () => input.recordedAt),
      ...(observation.at("input-projection", "labels", () => input.labels) === undefined ? {} : { labels: observation.at("label-copy", "labels", () => metricLabels(input.labels!)) }),
    };
  });
}

function assertMetricLabelName(value: string, index: number, observer?: MetricValidationObserver, retain: (error: TypeError) => TypeError = (error) => error): void {
  if (!/^[a-z][a-z0-9_]*$/.test(value)) {
    throw retain(metricValidationError(`metric label "${value}" must use lowercase snake_case.`, "label", "invalid-format", index, observer));
  }
}

function copyMetricLabelValue(key: string, value: MetricLabelValue, maxStringLength: number, index: number, observer?: MetricValidationObserver, retain: (error: TypeError) => TypeError = (error) => error): MetricLabelValue {
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw retain(metricValidationError(`metric label "${key}" must be a finite number.`, "label", "not-finite", index, observer));
    return value;
  }

  if (typeof value === "string") {
    if (value.length === 0) {
      throw retain(metricValidationError(`metric label "${key}" must not be empty.`, "label", "empty", index, observer));
    }

    if (value.length > maxStringLength) {
      throw retain(metricValidationError(`metric label "${key}" must not exceed ${maxStringLength} characters.`, "label", "too-long", index, observer));
    }
  }

  return value;
}
