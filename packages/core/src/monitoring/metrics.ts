import type { ISODateTime } from "../shared/index";
import type { MetricName, MetricUnit } from "./identifiers";
import { assertFiniteNumber, assertKnownValue, assertNonNegativeFiniteNumber, normalizeName } from "./validation";

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

export function metricLabels(input: MetricLabels, options: MetricLabelOptions = {}): MetricLabels {
  const unsafeLabels = new Set(
    [...defaultUnsafeMetricLabelNames, ...(options.additionalUnsafeLabelNames ?? [])].map(normalizeName),
  );
  const maxStringLength = options.maxStringLength ?? defaultMetricLabelStringLengthLimit;
  assertNonNegativeFiniteNumber("metric label maxStringLength", maxStringLength);

  const labels: Record<string, MetricLabelValue> = {};

  for (const [key, value] of Object.entries(input)) {
    assertMetricLabelName(key);

    if (unsafeLabels.has(normalizeName(key))) {
      throw new TypeError(`metric label "${key}" is unsafe or too high-cardinality.`);
    }

    labels[key] = copyMetricLabelValue(key, value, maxStringLength);
  }

  return labels;
}

export function metricPoint(input: {
  readonly name: MetricName;
  readonly kind: MetricKind;
  readonly value: number;
  readonly unit: MetricUnit;
  readonly recordedAt: ISODateTime;
  readonly labels?: MetricLabels;
}): MetricPoint {
  assertKnownValue("metric kind", input.kind, metricKinds);
  assertFiniteNumber("metric value", input.value);

  return {
    name: input.name,
    kind: input.kind,
    value: input.value,
    unit: input.unit,
    recordedAt: input.recordedAt,
    ...(input.labels === undefined ? {} : { labels: metricLabels(input.labels) }),
  };
}

function assertMetricLabelName(value: string): void {
  if (!/^[a-z][a-z0-9_]*$/.test(value)) {
    throw new TypeError(`metric label "${value}" must use lowercase snake_case.`);
  }
}

function copyMetricLabelValue(key: string, value: MetricLabelValue, maxStringLength: number): MetricLabelValue {
  if (typeof value === "number") {
    assertFiniteNumber(`metric label "${key}"`, value);
    return value;
  }

  if (typeof value === "string") {
    if (value.length === 0) {
      throw new TypeError(`metric label "${key}" must not be empty.`);
    }

    if (value.length > maxStringLength) {
      throw new TypeError(`metric label "${key}" must not exceed ${maxStringLength} characters.`);
    }
  }

  return value;
}
