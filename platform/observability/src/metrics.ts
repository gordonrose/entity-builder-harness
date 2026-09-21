import {
  metricLabels,
  metricName,
  metricUnit,
  type MetricKind,
  type MetricLabelValue,
  type Metrics,
} from "@kanbien/core/monitoring";
import { isoDateTimeFromDate, type Clock } from "@kanbien/core/shared";

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
): void {
  try { // Isolate metric-name, label, clock, and provider failures from the work being measured.
    metrics.record({ // Deliver one provider-neutral Core metric point through the injected metrics port.
      name: metricName(input.name), // Validate the stable metric identity before it reaches a provider.
      kind: input.kind ?? "counter", // Default to a counter when the caller did not select a measurement kind.
      value: input.value ?? 1, // Default to one occurrence when the caller did not supply a numeric value.
      unit: metricUnit(input.unit ?? "count"), // Validate the unit while keeping count as the normal counter default.
      recordedAt: isoDateTimeFromDate(clock.now()), // Stamp the point through the injected clock for deterministic local proof.
      ...(input.labels === undefined ? {} : { labels: metricLabels(compactLabels(input.labels)) }), // Remove absent labels before the bounded Core-label guard validates them.
    });
  } catch { // Treat metrics as best-effort operational evidence rather than a business-path dependency.
    // Observability must never turn a completed request or job into a failure.
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

export function elapsedMilliseconds(startedAt: Date, finishedAt: Date): number {
  return Math.max(0, finishedAt.getTime() - startedAt.getTime());
}

function compactLabels(labels: Readonly<Record<string, MetricLabelValue | undefined>>): Readonly<Record<string, MetricLabelValue>> {
  return Object.fromEntries(
    Object.entries(labels).filter((entry): entry is [string, MetricLabelValue] => entry[1] !== undefined),
  );
}
