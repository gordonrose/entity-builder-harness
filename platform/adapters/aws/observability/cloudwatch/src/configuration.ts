import { createConfigIssueCollector } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";
import { mergeObservabilityConfigurationFailures, observabilityConfigurationField, observabilityConfigurationObject, observabilityIntegerIssue, observabilityTextIssue,
  validatePlatformMetricSeries, type ObservabilityConfigurationFailure, type ObservabilityConfigurationReason } from "@kanbien/platform-observability";
import type { CloudWatchOtelMetricsOptions } from "./index";

/** Pure provider validation. It cannot create an exporter, reader, pool or network call. */
export function validateCloudWatchOtelMetricsConfiguration(value: unknown): Result<CloudWatchOtelMetricsOptions, ObservabilityConfigurationFailure> {
  const collector = createConfigIssueCollector<ObservabilityConfigurationReason>();
  if (!observabilityConfigurationObject(value)) { collector.add({ setting: "metrics.configuration", reason: "wrong-shape" }); return { ok: false, error: collector.finish() }; }
  const values: Record<string, unknown> = {};
  for (const [key, setting] of [["endpoint", "metrics.endpoint"], ["region", "metrics.region"], ["serviceName", "metrics.service-name"],
    ["serviceVersion", "metrics.service-version"], ["deploymentEnvironment", "metrics.deployment-environment"]] as const) {
    const raw = observabilityConfigurationField(value, key); values[key] = raw;
    const reason = observabilityTextIssue(raw);
    if (reason) collector.add({ setting, reason });
    else if (key === "region" && !/^[a-z]{2}(?:-gov)?-[a-z]+-\d+$/.test(raw as string)) collector.add({ setting, reason: "invalid-format" });
    if (key === "endpoint" && !reason) {
      let route: URL | undefined;
      try { route = new URL(raw as string); } catch { collector.add({ setting, reason: "malformed-url" }); }
      if (route) {
        for (const [rejected, endpointReason] of [[route.protocol !== "http:", "protocol-not-allowed"], [route.port !== "4318", "port-not-allowed"],
          [route.pathname !== "/v1/metrics", "path-not-allowed"], [route.username !== "" || route.password !== "", "credentials-not-allowed"],
          [route.search !== "", "query-not-allowed"], [route.hash !== "", "fragment-not-allowed"],
          [route.hostname !== "127.0.0.1" && !/^[a-z][a-z0-9-]{1,63}(?:\.[a-z][a-z0-9-]{1,63})+\.internal$/.test(route.hostname), "host-not-allowed"]] as const) {
          if (rejected) collector.add({ setting, reason: endpointReason });
        }
      }
    }
  }
  for (const key of ["exportIntervalMs", "exportTimeoutMs"] as const) {
    const raw = observabilityConfigurationField(value, key); values[key] = raw;
    const reason = observabilityIntegerIssue(raw);
    if (reason) collector.add({ setting: key === "exportIntervalMs" ? "metrics.export-interval" : "metrics.export-timeout", reason });
  }
  if (!observabilityIntegerIssue(values["exportIntervalMs"]) && (values["exportIntervalMs"] as number) < 1000) collector.add({ setting: "metrics.export-interval", reason: "interval-too-short" });
  if (!observabilityIntegerIssue(values["exportIntervalMs"]) && !observabilityIntegerIssue(values["exportTimeoutMs"])
    && (values["exportTimeoutMs"] as number) > (values["exportIntervalMs"] as number)) collector.add({ setting: "metrics.export-timeout", reason: "timeout-exceeds-interval" });
  const series = validatePlatformMetricSeries(observabilityConfigurationField(value, "series"));
  const failure = mergeObservabilityConfigurationFailures(collector.finish(), ...(series.ok ? [] : [series.error]));
  if (failure.issues.length) return { ok: false, error: failure };
  return { ok: true, value: { endpoint: values["endpoint"] as string, region: values["region"] as string, serviceName: values["serviceName"] as string,
    serviceVersion: values["serviceVersion"] as string, deploymentEnvironment: values["deploymentEnvironment"] as string,
    exportIntervalMs: values["exportIntervalMs"] as number, exportTimeoutMs: values["exportTimeoutMs"] as number, series: series.ok ? series.value : [] } };
}
