/** Value-free evidence from the existing monitoring predicates, not exception text. */
export type MetricValidationField = "name" | "unit" | "label";
export const metricValidationReasons = ["empty", "untrimmed", "invalid-format", "unsafe-name", "not-finite", "too-long"] as const;
export type MetricValidationReason = typeof metricValidationReasons[number];
export interface MetricValidationObservation {
  readonly field: MetricValidationField;
  readonly reason: MetricValidationReason;
  readonly index?: number;
}
export type MetricValidationObserver = (observation: MetricValidationObservation) => void;

/** Internal constructor: retain TypeError compatibility without exposing input. */
export function metricValidationError(message: string, field: MetricValidationField,
  reason: MetricValidationReason, index?: number, observer?: MetricValidationObserver): TypeError {
  const error = new TypeError(message);
  const observation = Object.freeze({ field, reason, ...(index === undefined ? {} : { index }) });
  try { observer?.(observation); } catch { /* An observation cannot replace the existing validation failure. */ }
  return error;
}
