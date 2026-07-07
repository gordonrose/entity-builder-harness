import { isoDateTimeFromDate, messageDescriptor } from "../src/shared/index";
import {
  fixedHealthCheck,
  healthCheckName,
  healthCheckResult,
  metricLabels,
  metricName,
  metricPoint,
  metricUnit,
  monitoringComponent,
  monitoringSignalDefinition,
  monitoringSignalName,
  noopMetrics,
  type HealthCheck,
  type HealthCheckName,
  type HealthCheckResult,
  type HealthCheckType,
  type HealthStatus,
  type MetricKind,
  type MetricLabelValue,
  type MetricLabels,
  type MetricName,
  type MetricPoint,
  type Metrics,
  type MetricUnit,
  type MonitoringComponentName,
  type MonitoringComponentRef,
  type MonitoringComponentType,
  type MonitoringMetadata,
  type MonitoringMetadataValue,
  type MonitoringMetricDefinition,
  type MonitoringSignalCategory,
  type MonitoringSignalDefinition,
  type MonitoringSignalIntent,
  type MonitoringSignalName,
} from "../src/monitoring/index";

const checkedAt = isoDateTimeFromDate(new Date("2026-07-07T10:00:00Z"));
const componentType: MonitoringComponentType = "api";
const component: MonitoringComponentRef = monitoringComponent({ type: componentType, name: "public-api" });
const healthName: HealthCheckName = healthCheckName("api.readiness");
const healthType: HealthCheckType = "readiness";
const status: HealthStatus = "healthy";
const metadataValue: MonitoringMetadataValue = { dependency: "postgres", attempts: 1 };
const metadata: MonitoringMetadata = { result: metadataValue };
const health: HealthCheckResult = healthCheckResult({
  name: healthName,
  type: healthType,
  component,
  status,
  checkedAt,
  metadata,
});
const check: HealthCheck = fixedHealthCheck(health);

const labelValue: MetricLabelValue = "api";
const labels: MetricLabels = metricLabels({
  service: labelValue,
  route: "deals.list",
  status_code: 200,
});
const metricKind: MetricKind = "counter";
const metric: MetricPoint = metricPoint({
  name: metricName("api.requests.total"),
  kind: metricKind,
  value: 1,
  unit: metricUnit("count"),
  recordedAt: checkedAt,
  labels,
});
const metrics: Metrics = noopMetrics;
void metrics.record(metric);

const metricDefinition: MonitoringMetricDefinition = {
  name: metricName("api.request.duration_ms"),
  kind: "timer",
  unit: metricUnit("milliseconds"),
};
const category: MonitoringSignalCategory = "latency";
const intent: MonitoringSignalIntent = "service-level-indicator";
const signalName: MonitoringSignalName = monitoringSignalName("api.request.latency");
const signal: MonitoringSignalDefinition = monitoringSignalDefinition({
  name: signalName,
  category,
  owner: "platform-runtime",
  intents: ["alerting", intent],
  component,
  metric: metricDefinition,
  description: messageDescriptor({
    code: "API_REQUEST_LATENCY",
    defaultMessage: "API request latency.",
  }),
});

void check;
void signal;

// @ts-expect-error monitoring component names must be explicitly branded.
const invalidComponentName: MonitoringComponentName = "public-api";
void invalidComponentName;

// @ts-expect-error health check names must be explicitly branded.
const invalidHealthName: HealthCheckName = "api.readiness";
void invalidHealthName;

// @ts-expect-error metric names must be explicitly branded.
const invalidMetricName: MetricName = "api.requests.total";
void invalidMetricName;

// @ts-expect-error metric units must be explicitly branded.
const invalidMetricUnit: MetricUnit = "count";
void invalidMetricUnit;

// @ts-expect-error monitoring signal names must be explicitly branded.
const invalidSignalName: MonitoringSignalName = "api.request.latency";
void invalidSignalName;

// @ts-expect-error health statuses are constrained.
const invalidStatus: HealthStatus = "unknown";
void invalidStatus;

// @ts-expect-error health check types are constrained.
const invalidHealthType: HealthCheckType = "startup";
void invalidHealthType;

// @ts-expect-error metric kinds are constrained.
const invalidMetricKind: MetricKind = "summary";
void invalidMetricKind;

// @ts-expect-error monitoring signal categories are constrained.
const invalidCategory: MonitoringSignalCategory = "uptime";
void invalidCategory;

// @ts-expect-error monitoring signal intents are constrained.
const invalidIntent: MonitoringSignalIntent = "dashboard";
void invalidIntent;

// @ts-expect-error metric labels must stay primitive.
const invalidLabelValue: MetricLabelValue = { route: "deals.list" };
void invalidLabelValue;

// @ts-expect-error monitoring metadata must stay plain and serializable.
const invalidMetadataValue: MonitoringMetadataValue = new Date();
void invalidMetadataValue;

// @ts-expect-error health checks must return health results.
const invalidHealthCheck: HealthCheck = { check: () => "healthy" };
void invalidHealthCheck;

// @ts-expect-error metric points require a branded metric name.
metricPoint({ name: "api.requests.total", kind: "counter", value: 1, unit: metricUnit("count"), recordedAt: checkedAt });

// @ts-expect-error signal definitions require at least a typed intent array.
monitoringSignalDefinition({ name: signalName, category, owner: "platform-runtime" });
