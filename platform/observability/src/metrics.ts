import {
  metricLabels,
  metricName,
  metricUnit,
  type MetricValidationObservation,
  type MetricKind,
  type MetricLabelValue,
  type Metrics,
} from "@kanbien/core/monitoring";
import { isoDateTimeFromDate, type Clock } from "@kanbien/core/shared";
import { platformOptionalErrorClassification, type PlatformErrorClassificationOptions } from "@kanbien/platform-contracts";
import { capturePlatformMetricDiagnostic, metricPreparationRecord, metricRecordingRecord, platformMetricFailureObservation, type PlatformMetricDiagnosticOptions } from "./metric-diagnostics";
import { reportPlatformObservationBoundary, reportPlatformObservationSources, type PlatformObservationDiagnostics } from "./boundary-observation";
import { platformObservationOperations, type PlatformObservationBoundaryDetail } from "./boundary-definitions";

const intrinsicPromiseThen = Promise.prototype.then;

export interface PlatformMetricInput {
  readonly name: string;
  readonly kind?: MetricKind;
  readonly value?: number;
  readonly unit?: string;
  readonly labels?: Readonly<Record<string, MetricLabelValue | undefined>>;
}

export function recordPlatformMetric(
  metrics: Metrics,
  clock: Clock,
  input: PlatformMetricInput,
  diagnostics?: PlatformMetricDiagnosticOptions,
  observations?: PlatformObservationDiagnostics,
): void {
  let phase: "recorder-access" | "name-access" | "kind-access" | "value-access" | "unit-access" | "label-access"
    | "name" | "unit" | "label" | "clock" | "timestamp" | "invoke" = "recorder-access";
  let observedDate: Date | undefined;
  let predicate: MetricValidationObservation | undefined;
  let primitiveInput: unknown;
  const observe = (observation: MetricValidationObservation) => { predicate = observation; };
  const report = (build: () => ReturnType<typeof metricRecordingRecord>) => {
    try { diagnostics?.binding.report(capturePlatformMetricDiagnostic(build), diagnostics.operation); } catch { /* Optional diagnostics remain isolated. */ }
  };
  try {
    const record = metrics.record; // Preserve original method-access ordering and this binding.
    phase = "name-access";
    const rawName = input.name;
    primitiveInput = rawName;
    phase = "name";
    const name = metricName(rawName, observe);
    phase = "kind-access";
    const kind = input.kind ?? "counter";
    phase = "value-access";
    const value = input.value ?? 1;
    phase = "unit-access";
    const rawUnit = input.unit ?? "count";
    primitiveInput = rawUnit;
    phase = "unit";
    const unit = metricUnit(rawUnit, observe);
    phase = "clock";
    observedDate = clock.now();
    phase = "timestamp";
    const recordedAt = isoDateTimeFromDate(observedDate);
    phase = "label-access";
    const compacted = input.labels === undefined ? undefined : compactLabels(input.labels);
    phase = "label";
    const labels = compacted === undefined ? undefined : metricLabels(compacted, {}, observe);
    phase = "invoke";
    const pending: ReturnType<Metrics["record"]> = Reflect.apply(record, metrics, [{ name, kind, value, unit, recordedAt, ...(labels === undefined ? {} : { labels }) }]);
    if (pending !== undefined) {
      const rejected = (error: unknown): void => {
        try { const known = platformMetricFailureObservation(metrics, error); report(() => known ?? metricRecordingRecord());
          if (known === undefined) reportPlatformObservationSources(observations, error); }
        catch { /* A rejection handler must not create another rejected promise. */ }
      };
      try {
        // Observe native promises without consulting a shadowed own `then`.
        Reflect.apply(intrinsicPromiseThen, pending, [undefined, rejected]);
      } catch {
        // Non-native thenables still use standard assimilation, including throwing getters.
        // Hostile native constructor/species hooks are outside portable isolation guarantees.
        Reflect.apply(intrinsicPromiseThen, Promise.resolve(pending), [undefined, rejected]);
      }
    }
  } catch (error) {
    if (phase === "invoke") { const known = platformMetricFailureObservation(metrics, error); report(() => known ?? metricRecordingRecord());
      if (known === undefined) reportPlatformObservationSources(observations, error); return; }
    const observed = predicate;
    if (observed !== undefined && observed.field === phase) {
      report(() => metricPreparationRecord(observed.field, observed.reason, observed.index));
    } else if ((phase === "name" || phase === "unit") && typeof primitiveInput !== "string") {
      const field = phase;
      report(() => metricPreparationRecord(field, "wrong-type"));
    } else if (phase === "clock") report(() => metricPreparationRecord("clock", "clock-threw"));
    else if (phase === "timestamp") {
      let invalidDate = false;
      try { invalidDate = Number.isNaN(Date.prototype.getTime.call(observedDate)); } catch { /* Non-date/access failure is not an invalid-date observation. */ }
      report(() => metricPreparationRecord("timestamp", invalidDate ? "invalid-date" : "unclassified-preparation-failure"));
    } else if (phase === "recorder-access" || phase === "name-access" || phase === "kind-access" || phase === "value-access" || phase === "unit-access" || phase === "label-access") {
      const field = phase === "recorder-access" ? "recorder" : phase === "name-access" ? "name" : phase === "kind-access" ? "kind"
        : phase === "value-access" ? "value" : phase === "unit-access" ? "unit" : "label";
      report(() => metricPreparationRecord(field, "access-failed"));
    } else {
      const field = phase;
      report(() => metricPreparationRecord(field, "unclassified-preparation-failure"));
    }
    reportPlatformObservationSources(observations, error);
  }
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
  diagnostics?: PlatformMetricDiagnosticOptions,
  classification?: PlatformErrorClassificationOptions,
  observations?: PlatformObservationDiagnostics,
): void {
  let field: PlatformObservationBoundaryDetail["field"] = "latency";
  try {
  recordPlatformMetric(metrics, clock, {
    name: "platform.server.request",
    kind: "timer",
    value: (field = "latency", input.latencyMs),
    unit: "ms",
    labels: {
      method: (field = "method", input.method),
      route: (field = "route", input.route),
      status: (field = "status", String(input.status)),
      outcome: input.status >= 500 ? "error" : input.status >= 400 ? "rejected" : "ok",
      error_class: (field = "error-class", platformOptionalErrorClassification(input.errorClass, classification)),
    },
  }, diagnostics, observations);
  } catch (error) { reportPlatformObservationBoundary(observations, { operation: "request-metric", phase: "input-projection", field, reason: "threw", effect: "not-attempted" }, error); throw error; }
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
  diagnostics?: PlatformMetricDiagnosticOptions,
  classification?: PlatformErrorClassificationOptions,
  observations?: PlatformObservationDiagnostics,
): void {
  let field: PlatformObservationBoundaryDetail["field"] = "job";
  try {
  recordPlatformMetric(metrics, clock, {
    name: "platform.worker.job.attempt",
    labels: {
      job: (field = "job", input.job),
      status: (field = "status", input.status),
      retry_count: (field = "retry-count", input.retryCount),
      error_class: (field = "error-class", platformOptionalErrorClassification(input.errorClass, classification)),
    },
  }, diagnostics, observations);
  } catch (error) { reportPlatformObservationBoundary(observations, { operation: "job-metric", phase: "input-projection", field, reason: "threw", effect: "not-attempted" }, error); throw error; }
}

export function recordPlatformHealthMetric(
  metrics: Metrics,
  clock: Clock,
  input: {
    readonly healthState: string;
  },
  diagnostics?: PlatformMetricDiagnosticOptions,
  observations?: PlatformObservationDiagnostics,
): void {
  try {
  recordPlatformMetric(metrics, clock, {
    name: "platform.health.state",
    labels: { health_state: input.healthState },
  }, diagnostics, observations);
  } catch (error) { reportPlatformObservationBoundary(observations, { operation: "health-metric", phase: "input-projection", field: "health-state", reason: "threw", effect: "not-attempted" }, error); throw error; }
}

export function elapsedMilliseconds(startedAt: Date, finishedAt: Date, observations?: PlatformObservationDiagnostics): number {
  try { return Math.max(0, finishedAt.getTime() - startedAt.getTime()); }
  catch (error) {
    let operation: PlatformObservationBoundaryDetail["operation"] = "request-observation";
    try { const candidate = observations?.context.operation; if (platformObservationOperations.some((value) => value === candidate)) operation = candidate as typeof operation; } catch { /* Optional context cannot replace original computation. */ }
    reportPlatformObservationBoundary(observations, { operation, phase: "elapsed-computation", field: "latency", reason: "threw", effect: "observation-incomplete" }, error); throw error;
  }
}

function compactLabels(labels: Readonly<Record<string, MetricLabelValue | undefined>>): Readonly<Record<string, MetricLabelValue>> {
  return Object.fromEntries(
    Object.entries(labels).filter((entry): entry is [string, MetricLabelValue] => entry[1] !== undefined),
  );
}
