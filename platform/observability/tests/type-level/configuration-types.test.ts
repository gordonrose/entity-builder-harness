import type { ConfigCheckIssue } from "@kanbien/core/config";
import { validatePlatformMetricSeries, validatePlatformReadinessConfiguration, type ObservabilityConfigurationReason, type PlatformMetricSeries } from "../../src/index";
const checked = validatePlatformMetricSeries([]);
if (checked.ok) { const series: readonly PlatformMetricSeries[] = checked.value; void series; }
else {
  const issue: ConfigCheckIssue<ObservabilityConfigurationReason> | undefined = checked.error.issues[0]; void issue;
  // @ts-expect-error failed validation does not expose submitted values
  checked.value;
}
// @ts-expect-error diagnostic reasons are owned and closed
const unknownReason: ObservabilityConfigurationReason = "arbitrary-provider-message"; void unknownReason;
const readiness = validatePlatformReadinessConfiguration({ target: "target", scope: "scope", workload: "workload", dependency: "dependency", cadenceMs: 1000, timeoutMs: 100, staleAfterMs: 1100 });
if (readiness.ok) {
  // @ts-expect-error configuration is readonly
  readiness.value.timeoutMs = 0;
}
