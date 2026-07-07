import { deepEqual, equal, throws } from "node:assert/strict";
import { isoDateTimeFromDate, messageDescriptor } from "../src/shared/index";
import {
  defaultMetricLabelStringLengthLimit,
  defaultUnsafeMetricLabelNames,
  fixedHealthCheck,
  healthCheckName,
  healthCheckResult,
  metricLabels,
  metricName,
  metricPoint,
  metricUnit,
  monitoringComponent,
  monitoringMetadata,
  monitoringSignalDefinition,
  monitoringSignalName,
  noopMetrics,
  type HealthCheckResult,
  type MetricPoint,
  type Metrics,
} from "../src/monitoring/index";

async function main(): Promise<void> {
  const checkedAt = isoDateTimeFromDate(new Date("2026-07-07T10:00:00Z"));
  const apiComponent = monitoringComponent({ type: "api", name: "public-api" });
  deepEqual(apiComponent, { type: "api", name: "public-api" });
  throws(
    () => monitoringComponent({ type: "database" as "api", name: "Primary Database" }),
    /monitoring component name must use lowercase dot-separated segments/,
  );

  const metadata = {
    dependency: "postgres",
    attempts: 1,
    nested: { reachable: true },
  };
  const result = healthCheckResult({
    name: healthCheckName("api.readiness"),
    type: "readiness",
    component: apiComponent,
    status: "degraded",
    checkedAt,
    durationMs: 42,
    message: messageDescriptor({
      code: "DEPENDENCY_DEGRADED",
      defaultMessage: "A dependency is reachable but degraded.",
      messageKey: "monitoring.health.degraded",
    }),
    metadata,
  });
  metadata.nested.reachable = false;
  deepEqual(result.metadata, {
    dependency: "postgres",
    attempts: 1,
    nested: { reachable: true },
  });
  throws(
    () =>
      healthCheckResult({
        name: healthCheckName("api.readiness"),
        type: "readiness",
        component: apiComponent,
        status: "healthy",
        checkedAt,
        durationMs: -1,
      }),
    /health check durationMs must be non-negative/,
  );
  throws(
    () =>
      healthCheckResult({
        name: healthCheckName("api.readiness"),
        type: "dependency",
        component: apiComponent,
        status: "healthy",
        checkedAt,
        metadata: {
          checkedAt: new Date() as never,
        },
      }),
    /monitoring metadata must contain only plain objects/,
  );

  const check = fixedHealthCheck(result);
  const checked = await check.check();
  deepEqual(checked, result);

  const safeLabels = metricLabels({
    service: "api",
    route: "deals.list",
    status_code: 200,
    cached: false,
  });
  deepEqual(safeLabels, {
    service: "api",
    route: "deals.list",
    status_code: 200,
    cached: false,
  });
  throws(() => metricLabels({ user_id: "user-123" }), /unsafe or too high-cardinality/);
  throws(() => metricLabels({ http_path: "/deals/123" }), /unsafe or too high-cardinality/);
  throws(() => metricLabels({ "http-method": "GET" }), /must use lowercase snake_case/);
  throws(() => metricLabels({ status_code: Number.NaN }), /metric label "status_code" must be a finite number/);
  throws(
    () =>
      metricLabels({
        route: "a".repeat(defaultMetricLabelStringLengthLimit + 1),
      }),
    /must not exceed/,
  );
  equal(defaultUnsafeMetricLabelNames.includes("token"), true);

  const point: MetricPoint = metricPoint({
    name: metricName("api.requests.total"),
    kind: "counter",
    value: 1,
    unit: metricUnit("count"),
    recordedAt: checkedAt,
    labels: safeLabels,
  });
  deepEqual(point, {
    name: "api.requests.total",
    kind: "counter",
    value: 1,
    unit: "count",
    recordedAt: checkedAt,
    labels: safeLabels,
  });
  throws(
    () =>
      metricPoint({
        name: metricName("api.requests.total"),
        kind: "counter",
        value: Number.POSITIVE_INFINITY,
        unit: metricUnit("count"),
        recordedAt: checkedAt,
      }),
    /metric value must be a finite number/,
  );
  throws(() => metricName("Api Requests"), /metric name must use lowercase dot-separated segments/);
  throws(() => metricUnit("milliseconds per request"), /metric unit must use lowercase token characters/);

  const signal = monitoringSignalDefinition({
    name: monitoringSignalName("api.request.latency"),
    category: "latency",
    owner: "platform-runtime",
    intents: ["alerting", "service-level-indicator"],
    component: apiComponent,
    metric: {
      name: metricName("api.request.duration_ms"),
      kind: "timer",
      unit: metricUnit("milliseconds"),
    },
  });
  deepEqual(signal, {
    name: "api.request.latency",
    category: "latency",
    owner: "platform-runtime",
    intents: ["alerting", "service-level-indicator"],
    component: apiComponent,
    metric: {
      name: "api.request.duration_ms",
      kind: "timer",
      unit: "milliseconds",
    },
  });
  throws(
    () =>
      monitoringSignalDefinition({
        name: monitoringSignalName("api.request.latency"),
        category: "latency",
        owner: "",
        intents: ["alerting"],
      }),
    /monitoring signal owner must be non-empty and trimmed/,
  );
  throws(
    () =>
      monitoringSignalDefinition({
        name: monitoringSignalName("api.request.latency"),
        category: "latency",
        owner: "platform-runtime",
        intents: [],
      }),
    /monitoring signal intents must include at least one intent/,
  );

  deepEqual(monitoringMetadata({ safe: true, nested: { value: 1 } }), {
    safe: true,
    nested: { value: 1 },
  });

  const written: MetricPoint[] = [];
  const metrics: Metrics = {
    record: (entry) => {
      written.push(entry);
    },
  };
  await metrics.record(point);
  deepEqual(written, [point]);
  await noopMetrics.record(point);

  const healthResult: HealthCheckResult = checked;
  void healthResult;
}

main()
  .then(() => {
    console.log("packages/core monitoring runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
