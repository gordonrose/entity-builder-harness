// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-observability
//   version: 2
//   status: active
//   created_on: "2026-09-21"
//   updated_on: "2026-10-30"
//   layer: 04.deploy
//   domain: infra.observability
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Translate reviewed target environment values into the AWS CloudWatch OTel metrics runtime.
//   portability:
//     class: internal
//     targets:
//     - kanbien/staging
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-platform-server
//     path: infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts

import { createCloudWatchOtelMetricsRuntime, validateCloudWatchOtelMetricsConfiguration,
  type CloudWatchOtelMetricsOptions, type CloudWatchOtelMetricsRuntime } from "@kanbien/platform-adapter-aws-observability-cloudwatch";
import { createConfigIssueCollector } from "@kanbien/core/config";
import { coreDiagnosticCatalog } from "@kanbien/core";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { createPlatformDiagnosticReporter, createPlatformSafeLogger, createPlatformMetricLifecycleDiagnosticBinding, reportPlatformErrorDiagnostic,
  mergeObservabilityConfigurationFailures, observabilityConfigurationField, observabilityConfigurationRecord, observabilityConstructionRecord,
  observabilityTextIssue, platformObservabilityDiagnosticCatalog, validatePlatformReadinessConfiguration,
  reportPlatformObservationBoundary,
  type ObservabilityConfigurationFailure, type ObservabilityConfigurationReason, type PlatformReadinessConfiguration,
  type PlatformMetricLifecycleDiagnosticBinding, type PlatformObservationDiagnostics } from "@kanbien/platform-observability";

export interface TargetObservabilityConfigurationError {
  readonly code: "KANBIEN_PLATFORM_TARGET_OBSERVABILITY_CONFIG_INVALID";
  readonly defaultMessage: string;
  readonly details: Readonly<{ readonly path: string; readonly reason: string }>;
  readonly diagnosticRecord: DiagnosticRecord;
}
export type TargetReadinessObservationConfiguration = PlatformReadinessConfiguration;
export const targetObservabilityBindings = {
  "metrics.provider": "PLATFORM_OBSERVABILITY_METRICS_PROVIDER", "metrics.endpoint": "PLATFORM_OBSERVABILITY_METRICS_ENDPOINT",
  "metrics.delivery-boundary": "PLATFORM_OBSERVABILITY_DELIVERY_BOUNDARY", "metrics.region": "PLATFORM_OBSERVABILITY_METRICS_REGION",
  "metrics.service-name": "PLATFORM_OBSERVABILITY_SERVICE_NAME", "metrics.service-version": "PLATFORM_SOURCE_COMMIT_SHA",
  "metrics.deployment-environment": "PLATFORM_OBSERVABILITY_DEPLOYMENT_ENVIRONMENT", "metrics.export-interval": "PLATFORM_OBSERVABILITY_EXPORT_INTERVAL_MS",
  "metrics.export-timeout": "PLATFORM_OBSERVABILITY_EXPORT_TIMEOUT_MS", "metrics.series": "PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON",
  "readiness.target": "PLATFORM_OBSERVABILITY_TARGET", "readiness.scope": "PLATFORM_OBSERVABILITY_SCOPE",
  "readiness.workload": "PLATFORM_OBSERVABILITY_WORKLOAD", "readiness.dependency": "PLATFORM_OBSERVABILITY_DEPENDENCY",
  "readiness.cadence": "PLATFORM_OBSERVABILITY_READINESS_CADENCE_MS", "readiness.timeout": "PLATFORM_OBSERVABILITY_READINESS_TIMEOUT_MS",
  "readiness.stale-after": "PLATFORM_OBSERVABILITY_READINESS_STALE_AFTER_MS",
} as const;
type Checked<T> = { readonly ok: true; readonly value: T } | { readonly ok: false; readonly error: TargetObservabilityConfigurationError };
const emptyFailure: ObservabilityConfigurationFailure = { issues: [], truncated: false };
const read = (env: NodeJS.ProcessEnv, setting: keyof typeof targetObservabilityBindings): unknown =>
  observabilityConfigurationField(env, targetObservabilityBindings[setting]);
/** Retain historical Number(...) acceptance (including whitespace, exponents and hexadecimal). */
const numberSource = (value: unknown): unknown => typeof value === "string" && value.trim() !== "" ? Number(value) : value;

function providerSelection(env: NodeJS.ProcessEnv): Checked<"disabled" | "enabled"> {
  const provider = read(env, "metrics.provider");
  if (provider === undefined || provider === "" || provider === "none") return { ok: true, value: "disabled" };
  if (provider === "cloudwatch-otel") return { ok: true, value: "enabled" };
  return configurationFailure({ issues: [{ setting: "metrics.provider", reason: typeof provider !== "string" ? "wrong-type" : provider.trim() === "" ? "blank" : "unsupported" }], truncated: false });
}

/** Pure target composition, including independent series and optional readiness checks. */
export function observabilityConfigurationFromTargetEnvironment(env: NodeJS.ProcessEnv, includeReadiness = false):
  Checked<{ readonly options: CloudWatchOtelMetricsOptions | undefined; readonly readiness: PlatformReadinessConfiguration | undefined }> {
  const selection = providerSelection(env);
  if (!selection.ok) return selection;
  if (selection.value === "disabled") return { ok: true, value: { options: undefined, readiness: undefined } };
  const collector = createConfigIssueCollector<ObservabilityConfigurationReason>();
  const rawSeries = read(env, "metrics.series");
  let series: unknown;
  const seriesReason = observabilityTextIssue(rawSeries);
  if (seriesReason) collector.add({ setting: "metrics.series", reason: seriesReason });
  else try { series = JSON.parse(rawSeries as string); }
  catch { collector.add({ setting: "metrics.series", reason: "invalid-json" }); }
  const options = {
    endpoint: read(env, "metrics.endpoint"), region: read(env, "metrics.region"), serviceName: read(env, "metrics.service-name"),
    serviceVersion: read(env, "metrics.service-version"), deploymentEnvironment: read(env, "metrics.deployment-environment"),
    exportIntervalMs: numberSource(read(env, "metrics.export-interval")), exportTimeoutMs: numberSource(read(env, "metrics.export-timeout")), series,
  };
  const metrics = validateCloudWatchOtelMetricsConfiguration(options);
  // The JSON boundary already explains missing/syntax failures; do not duplicate its derived missing-series issue.
  const metricFailure = metrics.ok ? emptyFailure : { ...metrics.error,
    issues: series === undefined ? metrics.error.issues.filter((issue) => issue.setting !== "metrics.series") : metrics.error.issues };
  const boundary = read(env, "metrics.delivery-boundary") ?? "task-local";
  if (typeof boundary !== "string") collector.add({ setting: "metrics.delivery-boundary", reason: "wrong-type" });
  else if (boundary !== "task-local" && boundary !== "private-collector-service") collector.add({ setting: "metrics.delivery-boundary", reason: boundary.trim() === "" ? "blank" : "unsupported" });
  else if (!observabilityTextIssue(options.endpoint)) {
    // Preserve the stricter target task-local spelling and private-service selection policy.
    if (boundary === "task-local" && options.endpoint !== "http://127.0.0.1:4318/v1/metrics") collector.add({ setting: "metrics.delivery-boundary", reason: "boundary-mismatch" });
    if (boundary === "private-collector-service") {
      try { if (new URL(options.endpoint as string).hostname === "127.0.0.1") collector.add({ setting: "metrics.delivery-boundary", reason: "boundary-mismatch" }); }
      catch { /* The provider validator retains the malformed URL predicate. */ }
    }
  }
  const readiness = includeReadiness ? readinessConfiguration(env) : { ok: true as const, value: undefined };
  const failure = mergeObservabilityConfigurationFailures(collector.finish(), metricFailure, readiness.ok ? emptyFailure : readiness.error);
  if (failure.issues.length) return configurationFailure(failure);
  if (!metrics.ok) throw new TypeError("TARGET_OBSERVABILITY_VALIDATION_INVARIANT");
  return { ok: true, value: { options: metrics.value, readiness: readiness.ok ? readiness.value : undefined } };
}

export function readinessObservationFromTargetEnvironment(env: NodeJS.ProcessEnv): Checked<PlatformReadinessConfiguration | undefined> {
  const selection = providerSelection(env);
  if (!selection.ok) return selection;
  if (selection.value === "disabled") return { ok: true, value: undefined };
  const checked = readinessConfiguration(env);
  return checked.ok ? checked : configurationFailure(checked.error);
}
function readinessConfiguration(env: NodeJS.ProcessEnv) {
  return validatePlatformReadinessConfiguration({ target: read(env, "readiness.target"), scope: read(env, "readiness.scope"),
    workload: read(env, "readiness.workload"), dependency: read(env, "readiness.dependency"),
    cadenceMs: numberSource(read(env, "readiness.cadence")), timeoutMs: numberSource(read(env, "readiness.timeout")), staleAfterMs: numberSource(read(env, "readiness.stale-after")) });
}

/** Runtime construction is a separate boundary; an exception message is not configuration evidence. */
export function createTargetObservabilityRuntime(options: CloudWatchOtelMetricsOptions | undefined,
  construct: typeof createCloudWatchOtelMetricsRuntime = createCloudWatchOtelMetricsRuntime,
  diagnostics?: PlatformMetricLifecycleDiagnosticBinding | false,
  observations?: PlatformObservationDiagnostics | false): Checked<CloudWatchOtelMetricsRuntime | undefined> {
  if (options === undefined) return { ok: true, value: undefined };
  let observationBinding: PlatformObservationDiagnostics | undefined;
  try {
    // Process-owned lifecycle evidence is independent of any route signal profile.
    // Disabled metrics never construct a reporter; explicit false disables this binding.
    const defaults = diagnostics === undefined || (observations === undefined && diagnostics !== false) ? targetMetricDiagnosticBindings() : undefined;
    const binding = diagnostics === false ? undefined : diagnostics ?? defaults?.lifecycle;
    observationBinding = observations === false ? undefined : observations ?? (diagnostics === false ? undefined : defaults?.observations);
    return { ok: true, value: observationBinding === undefined ? construct(options, binding) : construct(options, binding, observationBinding) };
  }
  catch (error) {
    reportPlatformObservationBoundary(observationBinding, { operation: "metric-runtime-construction", phase: "runtime-construction", reason: "threw", effect: "unknown" }, error);
    return { ok: false, error: {
    code: "KANBIEN_PLATFORM_TARGET_OBSERVABILITY_CONFIG_INVALID", defaultMessage: "Kanbien platform target observability configuration is invalid.",
    details: { path: "PLATFORM_OBSERVABILITY_METRICS_*", reason: "Runtime construction did not complete; its cause is unclassified." },
    diagnosticRecord: observabilityConstructionRecord(),
  } }; }
}
export function observabilityFromTargetEnvironment(env: NodeJS.ProcessEnv,
  construct: typeof createCloudWatchOtelMetricsRuntime = createCloudWatchOtelMetricsRuntime,
  diagnostics?: PlatformMetricLifecycleDiagnosticBinding | false,
  observations?: PlatformObservationDiagnostics | false): Checked<CloudWatchOtelMetricsRuntime | undefined> {
  const checked = observabilityConfigurationFromTargetEnvironment(env);
  return checked.ok ? createTargetObservabilityRuntime(checked.value.options, construct, diagnostics, observations) : checked;
}

function targetMetricDiagnosticBindings(): { readonly lifecycle: PlatformMetricLifecycleDiagnosticBinding; readonly observations: PlatformObservationDiagnostics } | undefined {
  try {
    const reporter = createPlatformDiagnosticReporter({ catalogs: [coreDiagnosticCatalog, platformObservabilityDiagnosticCatalog], clock: { now: () => new Date() },
      logger: createPlatformSafeLogger({ write(record) { console.error(JSON.stringify(record)); } }) });
    return { lifecycle: createPlatformMetricLifecycleDiagnosticBinding(reporter, { capability: "observability" }),
      observations: { reporter, context: { capability: "observability", operation: "metrics", stage: "startup" } } };
  } catch { return undefined; } // Optional diagnostic setup cannot prevent the selected metrics runtime.
}

function configurationFailure(failure: ObservabilityConfigurationFailure): { readonly ok: false; readonly error: TargetObservabilityConfigurationError } {
  const first = failure.issues[0];
  const binding = first === undefined ? undefined : targetObservabilityBindings[first.setting as keyof typeof targetObservabilityBindings];
  return { ok: false, error: {
    code: "KANBIEN_PLATFORM_TARGET_OBSERVABILITY_CONFIG_INVALID", defaultMessage: "Kanbien platform target observability configuration is invalid.",
    details: { path: binding ?? "PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON", reason: first?.reason ?? "configuration-rejected" },
    diagnosticRecord: observabilityConfigurationRecord(failure),
  } };
}

/** Startup delivery uses the same validated internal reporter as other configuration boundaries. */
export function reportTargetObservabilityConfiguration(error: TargetObservabilityConfigurationError): void {
  const reporter = createPlatformDiagnosticReporter({ catalogs: [platformObservabilityDiagnosticCatalog], clock: { now: () => new Date() },
    logger: createPlatformSafeLogger({ write(record) { console.error(JSON.stringify(record)); } }) });
  reportPlatformErrorDiagnostic(reporter, error, { capability: "observability", operation: "configure", stage: "configuration" });
}
