import {
  brand,
  copyJsonValue,
  type Brand,
  type ISODateTime,
  type JsonValue,
  type MessageDescriptor,
} from "../shared/index";

export type MonitoringComponentName = Brand<string, "MonitoringComponentName">;
export type HealthCheckName = Brand<string, "HealthCheckName">;
export type MetricName = Brand<string, "MetricName">;
export type MetricUnit = Brand<string, "MetricUnit">;
export type MonitoringSignalName = Brand<string, "MonitoringSignalName">;

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

export const healthCheckTypes = ["liveness", "readiness", "dependency", "capability"] as const;
export type HealthCheckType = (typeof healthCheckTypes)[number];

export const healthStatuses = ["healthy", "degraded", "unhealthy"] as const;
export type HealthStatus = (typeof healthStatuses)[number];

export const metricKinds = ["counter", "gauge", "histogram", "timer"] as const;
export type MetricKind = (typeof metricKinds)[number];

export const monitoringSignalCategories = [
  "traffic",
  "latency",
  "errors",
  "saturation",
  "dependency",
  "queue",
  "job",
  "business-critical-path",
  "security",
  "cost",
] as const;
export type MonitoringSignalCategory = (typeof monitoringSignalCategories)[number];

export const monitoringSignalIntents = [
  "health-detection",
  "alerting",
  "capacity-planning",
  "debugging",
  "service-level-indicator",
  "cost-control",
] as const;
export type MonitoringSignalIntent = (typeof monitoringSignalIntents)[number];

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

export type MonitoringMetadataValue = JsonValue;
export type MonitoringMetadata = Readonly<Record<string, MonitoringMetadataValue>>;
export type MetricLabelValue = string | number | boolean;
export type MetricLabels = Readonly<Record<string, MetricLabelValue>>;

export interface MonitoringComponentRef {
  readonly type: MonitoringComponentType;
  readonly name: MonitoringComponentName;
}

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

export interface MonitoringSignalDefinition {
  readonly name: MonitoringSignalName;
  readonly category: MonitoringSignalCategory;
  readonly owner: string;
  readonly intents: readonly MonitoringSignalIntent[];
  readonly component?: MonitoringComponentRef;
  readonly metric?: MonitoringMetricDefinition;
  readonly description?: MessageDescriptor;
}

export interface MetricLabelOptions {
  readonly additionalUnsafeLabelNames?: readonly string[];
  readonly maxStringLength?: number;
}

export const noopMetrics: Metrics = {
  record: () => undefined,
};

export function monitoringComponentName(value: string): MonitoringComponentName {
  assertDottedName("monitoring component name", value, false);
  return brand<string, "MonitoringComponentName">(value);
}

export function monitoringComponent(input: {
  readonly type: MonitoringComponentType;
  readonly name: string | MonitoringComponentName;
}): MonitoringComponentRef {
  assertKnownValue("monitoring component type", input.type, monitoringComponentTypes);

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

export function metricLabels(input: MetricLabels, options: MetricLabelOptions = {}): MetricLabels {
  const unsafeLabels = new Set(
    [...defaultUnsafeMetricLabelNames, ...(options.additionalUnsafeLabelNames ?? [])].map(normalizeLabelName),
  );
  const maxStringLength = options.maxStringLength ?? defaultMetricLabelStringLengthLimit;
  assertNonNegativeFiniteNumber("metric label maxStringLength", maxStringLength);

  const labels: Record<string, MetricLabelValue> = {};

  for (const [key, value] of Object.entries(input)) {
    assertMetricLabelName(key);

    if (unsafeLabels.has(normalizeLabelName(key))) {
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

export function monitoringSignalDefinition(input: {
  readonly name: MonitoringSignalName;
  readonly category: MonitoringSignalCategory;
  readonly owner: string;
  readonly intents: readonly MonitoringSignalIntent[];
  readonly component?: MonitoringComponentRef;
  readonly metric?: MonitoringMetricDefinition;
  readonly description?: MessageDescriptor;
}): MonitoringSignalDefinition {
  assertKnownValue("monitoring signal category", input.category, monitoringSignalCategories);
  assertNonEmpty("monitoring signal owner", input.owner);

  if (input.intents.length === 0) {
    throw new TypeError("monitoring signal intents must include at least one intent.");
  }

  for (const intent of input.intents) {
    assertKnownValue("monitoring signal intent", intent, monitoringSignalIntents);
  }

  if (input.metric !== undefined) {
    assertKnownValue("metric kind", input.metric.kind, metricKinds);
  }

  return {
    name: input.name,
    category: input.category,
    owner: input.owner,
    intents: [...input.intents],
    ...(input.component === undefined ? {} : { component: { ...input.component } }),
    ...(input.metric === undefined ? {} : { metric: { ...input.metric } }),
    ...(input.description === undefined ? {} : { description: input.description }),
  };
}

function copyMonitoringMetadata<TValue extends MonitoringMetadata>(value: TValue): TValue {
  return Object.fromEntries(
    Object.entries(value).map(([key, nestedValue]) => [key, copyJsonValue(nestedValue, "monitoring metadata")]),
  ) as TValue;
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

function assertDottedName(label: string, value: string, requireDot: boolean): void {
  assertNonEmpty(label, value);

  const pattern = requireDot
    ? /^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)+$/
    : /^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)*$/;

  if (!pattern.test(value)) {
    throw new TypeError(`${label} must use lowercase dot-separated segments.`);
  }
}

function assertMetricLabelName(value: string): void {
  if (!/^[a-z][a-z0-9_]*$/.test(value)) {
    throw new TypeError(`metric label "${value}" must use lowercase snake_case.`);
  }
}

function assertToken(label: string, value: string): void {
  assertNonEmpty(label, value);

  if (!/^[a-z][a-z0-9_-]*$/.test(value)) {
    throw new TypeError(`${label} must use lowercase token characters.`);
  }
}

function assertNonEmpty(label: string, value: string): void {
  if (value.length === 0 || value.trim() !== value) {
    throw new TypeError(`${label} must be non-empty and trimmed.`);
  }
}

function assertFiniteNumber(label: string, value: number): void {
  if (!Number.isFinite(value)) {
    throw new TypeError(`${label} must be a finite number.`);
  }
}

function assertNonNegativeFiniteNumber(label: string, value: number): void {
  assertFiniteNumber(label, value);

  if (value < 0) {
    throw new TypeError(`${label} must be non-negative.`);
  }
}

function assertKnownValue<TValue extends string>(
  label: string,
  value: string,
  allowedValues: readonly TValue[],
): asserts value is TValue {
  if (!allowedValues.includes(value as TValue)) {
    throw new TypeError(`${label} must be one of: ${allowedValues.join(", ")}.`);
  }
}

function normalizeLabelName(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}
