import { metricValidationError, type MetricValidationField, type MetricValidationObserver } from "./diagnostics";
import type { CoreMonitoringValidationDetail } from "./boundary-diagnostics";
export type MonitoringReject = (message: string, reason: CoreMonitoringValidationDetail["reason"]) => TypeError;

export function assertDottedName(label: string, value: string, requireDot: boolean, metricField?: MetricValidationField, observer?: MetricValidationObserver, reject?: MonitoringReject): void {
  assertNonEmpty(label, value, metricField, observer, reject);

  const pattern = requireDot
    ? /^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)+$/
    : /^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)*$/;

  if (!pattern.test(value)) {
    throw validationError(`${label} must use lowercase dot-separated segments.`, metricField, "invalid-format", observer, reject);
  }
}

export function assertToken(label: string, value: string, metricField?: MetricValidationField, observer?: MetricValidationObserver): void {
  assertNonEmpty(label, value, metricField, observer);

  if (!/^[a-z][a-z0-9_-]*$/.test(value)) {
    throw validationError(`${label} must use lowercase token characters.`, metricField, "invalid-format", observer);
  }
}

export function assertNonEmpty(label: string, value: string, metricField?: MetricValidationField, observer?: MetricValidationObserver, reject?: MonitoringReject): void {
  if (value.length === 0) {
    throw validationError(`${label} must be non-empty and trimmed.`, metricField, "empty", observer, reject);
  }
  if (value.trim() !== value) {
    throw validationError(`${label} must be non-empty and trimmed.`, metricField, "untrimmed", observer, reject);
  }
}

function validationError(message: string, field: MetricValidationField | undefined,
  reason: "empty" | "untrimmed" | "invalid-format", observer?: MetricValidationObserver, reject?: MonitoringReject): TypeError {
  return field === undefined ? (reject?.(message, reason) ?? new TypeError(message)) : metricValidationError(message, field, reason, undefined, observer);
}

export function assertFiniteNumber(label: string, value: number, reject?: MonitoringReject): void {
  if (!Number.isFinite(value)) {
    throw reject?.(`${label} must be a finite number.`, "not-finite") ?? new TypeError(`${label} must be a finite number.`);
  }
}

export function assertNonNegativeFiniteNumber(label: string, value: number, reject?: MonitoringReject): void {
  assertFiniteNumber(label, value, reject);

  if (value < 0) {
    throw reject?.(`${label} must be non-negative.`, "negative") ?? new TypeError(`${label} must be non-negative.`);
  }
}

export function assertKnownValue<TValue extends string>(
  label: string,
  value: string,
  allowedValues: readonly TValue[],
  reject?: MonitoringReject,
): asserts value is TValue {
  if (!allowedValues.includes(value as TValue)) {
    const message = `${label} must be one of: ${allowedValues.join(", ")}.`;
    throw reject?.(message, "closed-value-rejected") ?? new TypeError(message);
  }
}

export function normalizeName(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}
