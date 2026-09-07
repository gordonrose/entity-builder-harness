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

export function elapsedMilliseconds(startedAt: Date, finishedAt: Date): number {
  return Math.max(0, finishedAt.getTime() - startedAt.getTime());
}

function compactLabels(labels: Readonly<Record<string, MetricLabelValue | undefined>>): Readonly<Record<string, MetricLabelValue>> {
  return Object.fromEntries(
    Object.entries(labels).filter((entry): entry is [string, MetricLabelValue] => entry[1] !== undefined),
  );
}
