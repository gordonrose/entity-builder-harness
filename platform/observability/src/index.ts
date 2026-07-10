import type { Logger, LogFields, LogLevel } from "@kanbien/core/logging";
import { defaultRedactedValue, defaultSensitiveLogFieldNames } from "@kanbien/core/logging";
import {
  metricLabels,
  metricName,
  metricUnit,
  type MetricKind,
  type MetricLabelValue,
  type Metrics,
} from "@kanbien/core/monitoring";
import {
  isoDateTimeFromDate,
  type Clock,
  type CorrelationId,
  type JsonValue,
} from "@kanbien/core/shared";

export type PlatformSafeLogFields = Readonly<Record<string, JsonValue>>;

export interface PlatformValueNormalizationOptions {
  readonly additionalSensitiveKeys?: readonly string[];
  readonly redactedValue?: string;
  readonly maxDepth?: number;
  readonly maxArrayItems?: number;
  readonly maxObjectKeys?: number;
  readonly maxStringLength?: number;
}

export interface PlatformLogInput {
  readonly level: LogLevel;
  readonly message: string;
  readonly correlationId?: CorrelationId;
  readonly fields?: Readonly<Record<string, unknown>>;
  readonly error?: unknown;
}

export interface PlatformMetricInput {
  readonly name: string;
  readonly kind?: MetricKind;
  readonly value?: number;
  readonly unit?: string;
  readonly labels?: Readonly<Record<string, MetricLabelValue | undefined>>;
}

export interface PlatformTraceFieldsInput {
  readonly requestId?: string;
  readonly correlationId?: string;
  readonly tenant?: string;
  readonly route?: string;
  readonly job?: string;
  readonly errorClass?: string;
  readonly latencyMs?: number;
  readonly retryCount?: number;
  readonly healthState?: string;
}

interface NormalizationState {
  readonly options: Required<PlatformValueNormalizationOptions>;
  readonly sensitiveKeys: ReadonlySet<string>;
  readonly seen: WeakSet<object>;
}

export function normalizePlatformLogFields(
  fields: Readonly<Record<string, unknown>>,
  options: PlatformValueNormalizationOptions = {},
): PlatformSafeLogFields {
  const state = createNormalizationState(options);
  const normalized = normalizeRecord(fields, state, 0);

  return normalized;
}

export function normalizePlatformValue(
  value: unknown,
  options: PlatformValueNormalizationOptions = {},
): JsonValue {
  return normalizeUnknown(value, createNormalizationState(options), 0);
}

export function normalizePlatformError(error: unknown): PlatformSafeLogFields {
  if (error instanceof Error) {
    return {
      name: error.name,
      message: error.message,
      ...(hasStringProperty(error, "code") ? { code: error["code"] } : {}),
    };
  }

  if (isObjectLike(error)) {
    return normalizePlatformLogFields(error as Readonly<Record<string, unknown>>);
  }

  return { message: String(error) };
}

export function platformErrorClass(error: unknown): string {
  if (hasStringProperty(error, "code")) {
    return String(error["code"]);
  }

  if (error instanceof Error && error.name.length > 0) {
    return error.name;
  }

  return "unknown";
}

export function createPlatformSafeLogger(
  inner: Logger,
  options: PlatformValueNormalizationOptions = {},
): Logger {
  return {
    write: (record) => {
      writePlatformLog(inner, {
        level: record.level,
        message: record.message,
        ...(record.correlationId === undefined ? {} : { correlationId: record.correlationId }),
        ...(record.fields === undefined ? {} : { fields: record.fields }),
      }, options);
    },
  };
}

export function writePlatformLog(
  logger: Logger,
  input: PlatformLogInput,
  options: PlatformValueNormalizationOptions = {},
): void {
  const fields = {
    ...(input.fields ?? {}),
    ...(input.error === undefined ? {} : { error: normalizePlatformError(input.error) }),
  };

  logger.write({
    level: input.level,
    message: input.message,
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    ...(Object.keys(fields).length === 0 ? {} : { fields: normalizePlatformLogFields(fields, options) as LogFields }),
  });
}

export function recordPlatformMetric(
  metrics: Metrics,
  clock: Clock,
  input: PlatformMetricInput,
): void {
  metrics.record({
    name: metricName(input.name),
    kind: input.kind ?? "counter",
    value: input.value ?? 1,
    unit: metricUnit(input.unit ?? "count"),
    recordedAt: isoDateTimeFromDate(clock.now()),
    ...(input.labels === undefined ? {} : { labels: metricLabels(compactLabels(input.labels)) }),
  });
}

export function recordPlatformRequestMetric(
  metrics: Metrics,
  clock: Clock,
  input: {
    readonly method: string;
    readonly route: string;
    readonly status: number;
    readonly latencyMs: number;
    readonly errorClass?: string;
  },
): void {
  recordPlatformMetric(metrics, clock, {
    name: "platform.server.request",
    kind: "timer",
    value: input.latencyMs,
    unit: "ms",
    labels: {
      method: input.method,
      route: input.route,
      status: String(input.status),
      outcome: input.status >= 500 ? "error" : input.status >= 400 ? "rejected" : "ok",
      error_class: input.errorClass,
    },
  });
}

export function recordPlatformJobMetric(
  metrics: Metrics,
  clock: Clock,
  input: {
    readonly job: string;
    readonly status: string;
    readonly retryCount?: number;
    readonly errorClass?: string;
  },
): void {
  recordPlatformMetric(metrics, clock, {
    name: "platform.worker.job.attempt",
    labels: {
      job: input.job,
      status: input.status,
      retry_count: input.retryCount,
      error_class: input.errorClass,
    },
  });
}

export function recordPlatformHealthMetric(
  metrics: Metrics,
  clock: Clock,
  input: {
    readonly healthState: string;
  },
): void {
  recordPlatformMetric(metrics, clock, {
    name: "platform.health.state",
    labels: { health_state: input.healthState },
  });
}

export function platformTraceFields(input: PlatformTraceFieldsInput): PlatformSafeLogFields {
  return normalizePlatformLogFields({
    requestId: input.requestId,
    correlationId: input.correlationId,
    tenant: input.tenant,
    route: input.route,
    job: input.job,
    errorClass: input.errorClass,
    latencyMs: input.latencyMs,
    retryCount: input.retryCount,
    healthState: input.healthState,
  });
}

export function elapsedMilliseconds(startedAt: Date, finishedAt: Date): number {
  return Math.max(0, finishedAt.getTime() - startedAt.getTime());
}

function compactLabels(labels: Readonly<Record<string, MetricLabelValue | undefined>>): Readonly<Record<string, MetricLabelValue>> {
  return Object.fromEntries(
    Object.entries(labels).filter((entry): entry is [string, MetricLabelValue] => entry[1] !== undefined),
  );
}

function createNormalizationState(options: PlatformValueNormalizationOptions): NormalizationState {
  const normalizedOptions: Required<PlatformValueNormalizationOptions> = {
    additionalSensitiveKeys: options.additionalSensitiveKeys ?? [],
    redactedValue: options.redactedValue ?? defaultRedactedValue,
    maxDepth: options.maxDepth ?? 4,
    maxArrayItems: options.maxArrayItems ?? 20,
    maxObjectKeys: options.maxObjectKeys ?? 50,
    maxStringLength: options.maxStringLength ?? 256,
  };

  return {
    options: normalizedOptions,
    sensitiveKeys: new Set(
      [...defaultSensitiveLogFieldNames, ...normalizedOptions.additionalSensitiveKeys].map(normalizeKey),
    ),
    seen: new WeakSet<object>(),
  };
}

function normalizeRecord(
  record: Readonly<Record<string, unknown>>,
  state: NormalizationState,
  depth: number,
): PlatformSafeLogFields {
  const result: Record<string, JsonValue> = {};
  const entries = Object.entries(record).slice(0, state.options.maxObjectKeys);

  for (const [key, value] of entries) {
    result[key] = isSensitiveKey(key, state)
      ? state.options.redactedValue
      : normalizeUnknown(value, state, depth + 1);
  }

  if (Object.keys(record).length > state.options.maxObjectKeys) {
    result["truncatedKeys"] = Object.keys(record).length - state.options.maxObjectKeys;
  }

  return result;
}

function normalizeUnknown(value: unknown, state: NormalizationState, depth: number): JsonValue {
  if (value === undefined) {
    return null;
  }

  if (value === null || typeof value === "boolean") {
    return value;
  }

  if (typeof value === "string") {
    return value.length > state.options.maxStringLength
      ? `${value.slice(0, state.options.maxStringLength)}...[truncated]`
      : value;
  }

  if (typeof value === "number") {
    return Number.isFinite(value) ? value : String(value);
  }

  if (typeof value === "bigint" || typeof value === "symbol" || typeof value === "function") {
    return `[${typeof value}]`;
  }

  if (value instanceof Date) {
    return value.toISOString();
  }

  if (value instanceof Error) {
    return normalizePlatformError(value);
  }

  if (depth > state.options.maxDepth) {
    return "[MaxDepth]";
  }

  if (Array.isArray(value)) {
    return value.slice(0, state.options.maxArrayItems).map((item) => normalizeUnknown(item, state, depth + 1));
  }

  if (!isObjectLike(value)) {
    return String(value);
  }

  if (state.seen.has(value)) {
    return "[Circular]";
  }

  state.seen.add(value);
  const normalized = normalizeRecord(value as Readonly<Record<string, unknown>>, state, depth);
  state.seen.delete(value);

  return normalized;
}

function isSensitiveKey(key: string, state: NormalizationState): boolean {
  const normalized = normalizeKey(key);

  for (const sensitiveKey of state.sensitiveKeys) {
    if (normalized === sensitiveKey || normalized.includes(sensitiveKey)) {
      return true;
    }
  }

  return false;
}

function normalizeKey(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function isObjectLike(value: unknown): value is object {
  return typeof value === "object" && value !== null;
}

function hasStringProperty(value: unknown, key: string): value is Readonly<Record<string, string>> {
  return isObjectLike(value) && typeof (value as Readonly<Record<string, unknown>>)[key] === "string";
}
