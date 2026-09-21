// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-observability
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: infra.observability
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Translate reviewed target environment values into the AWS CloudWatch OTel metrics runtime.
//   portability:
//     class: target-specific
//     targets:
//     - kanbien/staging
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-platform-server
//     path: infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts

import { // Keep the AWS provider construction at the target composition boundary.
  createCloudWatchOtelMetricsRuntime, // Construct the reviewed Core-to-OTel metrics adapter.
  type CloudWatchOtelMetricSeries, // Describe the target-approved Core metric catalogue.
  type CloudWatchOtelMetricsRuntime, // Return lifecycle ownership to the target process.
} from "@kanbien/platform-adapter-aws-observability-cloudwatch"; // Do not expose this AWS adapter to generic platform modules.

export interface TargetObservabilityConfigurationError { // Return a safe startup error without echoing values from the process environment.
  readonly code: "KANBIEN_PLATFORM_TARGET_OBSERVABILITY_CONFIG_INVALID"; // Give operators one stable error category for target telemetry configuration.
  readonly defaultMessage: string; // Supply a non-sensitive human-readable summary.
  readonly details: Readonly<{ // Retain the configuration key and a safe validation reason for local diagnostics.
    readonly path: string; // Identify the reviewed target configuration field that needs correction.
    readonly reason: string; // Explain the expected shape without including its raw value.
  }>;
}

export function observabilityFromTargetEnvironment( // Construct optional target metrics only when this target selects a supported provider.
  env: NodeJS.ProcessEnv, // Read the task's deployment-owned environment, never app-controlled request data.
): { readonly ok: true; readonly value: CloudWatchOtelMetricsRuntime | undefined } | { readonly ok: false; readonly error: TargetObservabilityConfigurationError } {
  const provider = env["PLATFORM_OBSERVABILITY_METRICS_PROVIDER"]; // Read the target's reviewed metrics provider selection.
  if (provider === undefined || provider.length === 0 || provider === "none") { // Permit local/private targets that deliberately do not select metric delivery.
    return { ok: true, value: undefined }; // Keep metric delivery optional outside the staging target that explicitly enables it.
  }
  if (provider !== "cloudwatch-otel") { // Reject a provider that this target composition has not implemented.
    return targetObservabilityConfigurationError("PLATFORM_OBSERVABILITY_METRICS_PROVIDER", "Unsupported metrics provider."); // Fail before the server accepts traffic.
  }

  const endpoint = requiredString(env, "PLATFORM_OBSERVABILITY_METRICS_ENDPOINT"); // Require the adapter's reviewed task-local collector endpoint.
  if (!endpoint.ok) return endpoint; // Preserve the safe missing-value error.
  const region = requiredString(env, "PLATFORM_OBSERVABILITY_METRICS_REGION"); // Require the selected AWS region.
  if (!region.ok) return region; // Preserve the safe missing-value error.
  const serviceName = requiredString(env, "PLATFORM_OBSERVABILITY_SERVICE_NAME"); // Require a stable OTel resource service identity.
  if (!serviceName.ok) return serviceName; // Preserve the safe missing-value error.
  const serviceVersion = requiredString(env, "PLATFORM_SOURCE_COMMIT_SHA"); // Require the immutable build revision supplied by the image build.
  if (!serviceVersion.ok) return serviceVersion; // Preserve the safe missing-value error.
  const deploymentEnvironment = requiredString(env, "PLATFORM_OBSERVABILITY_DEPLOYMENT_ENVIRONMENT"); // Require a bounded target environment resource attribute.
  if (!deploymentEnvironment.ok) return deploymentEnvironment; // Preserve the safe missing-value error.
  const exportIntervalMs = positiveInteger(env, "PLATFORM_OBSERVABILITY_EXPORT_INTERVAL_MS"); // Parse the target's controlled batching cadence.
  if (!exportIntervalMs.ok) return exportIntervalMs; // Preserve the safe numeric configuration error.
  const exportTimeoutMs = positiveInteger(env, "PLATFORM_OBSERVABILITY_EXPORT_TIMEOUT_MS"); // Parse the target's controlled exporter deadline.
  if (!exportTimeoutMs.ok) return exportTimeoutMs; // Preserve the safe numeric configuration error.
  const series = metricSeriesFromEnvironment(env); // Parse the mechanical target-policy projection used by the adapter.
  if (!series.ok) return series; // Fail closed when the metric catalogue cannot be safely reconstructed.

  try { // Let the adapter enforce endpoint, region, label, cardinality, and histogram semantics in one place.
    return { // Return the provider runtime only after its complete target configuration has passed validation.
      ok: true, // Mark the result ready for target process composition.
      value: createCloudWatchOtelMetricsRuntime({ // Construct the AWS adapter without changing generic platform code.
        endpoint: endpoint.value, // Pass the reviewed local collector endpoint.
        region: region.value, // Pass the target-selected AWS region as a resource attribute.
        serviceName: serviceName.value, // Pass the stable service resource identity.
        serviceVersion: serviceVersion.value, // Pass the immutable build revision as a resource attribute.
        deploymentEnvironment: deploymentEnvironment.value, // Pass the bounded deployment environment as a resource attribute.
        exportIntervalMs: exportIntervalMs.value, // Pass the reviewed periodic export interval.
        exportTimeoutMs: exportTimeoutMs.value, // Pass the reviewed maximum export duration.
        series: series.value, // Pass only the catalogue mechanically projected from the target policy.
      }), // Keep OTel construction outside server routes, jobs, and Core.
    }; // Return the completed target metrics runtime.
  } catch (error) { // Convert adapter configuration failures into a safe startup result.
    return targetObservabilityConfigurationError( // Avoid exposing endpoints or raw environment values in the returned error.
      "PLATFORM_OBSERVABILITY_METRICS_*", // Point operators at the reviewed metrics configuration group.
      error instanceof Error ? error.message : "Metrics adapter configuration is invalid.", // Retain only the adapter's safe validation message.
    ); // Ensure the process remains fail-closed for a configured-but-invalid target metrics path.
  }
}

function requiredString( // Read one mandatory non-empty target configuration string.
  env: NodeJS.ProcessEnv, // Receive the task environment selected by CloudFormation.
  key: string, // Name the exact reviewed environment key.
): { readonly ok: true; readonly value: string } | { readonly ok: false; readonly error: TargetObservabilityConfigurationError } {
  const value = env[key]; // Read the configuration value once.
  if (value === undefined || value.trim().length === 0) { // Reject absent and whitespace-only values before adapter construction.
    return targetObservabilityConfigurationError(key, "A non-empty value is required when cloudwatch-otel metrics are enabled."); // Avoid ambiguous default behaviour for a configured provider.
  }
  return { ok: true, value }; // Return the reviewed raw string only to the local composition function.
}

function positiveInteger( // Parse one mandatory positive integer target configuration value.
  env: NodeJS.ProcessEnv, // Receive the task environment selected by CloudFormation.
  key: string, // Name the exact reviewed numeric environment key.
): { readonly ok: true; readonly value: number } | { readonly ok: false; readonly error: TargetObservabilityConfigurationError } {
  const raw = env[key]; // Read the string representation supplied by ECS.
  const value = raw === undefined ? Number.NaN : Number(raw); // Convert it once while preserving missing-value failure semantics.
  if (!Number.isInteger(value) || value <= 0) { // Reject fractions, zero, negatives, and non-numeric values.
    return targetObservabilityConfigurationError(key, "A positive integer is required when cloudwatch-otel metrics are enabled."); // Keep batch scheduling and deadlines bounded.
  }
  return { ok: true, value }; // Return the parsed integer to the adapter constructor.
}

function metricSeriesFromEnvironment( // Parse the reviewed target catalogue projection supplied by ECS task configuration.
  env: NodeJS.ProcessEnv, // Receive the task environment selected by CloudFormation.
): { readonly ok: true; readonly value: readonly CloudWatchOtelMetricSeries[] } | { readonly ok: false; readonly error: TargetObservabilityConfigurationError } {
  const raw = env["PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON"]; // Read the one JSON representation of the reviewed series catalogue.
  if (raw === undefined || raw.length === 0) { // Reject an enabled metrics path with no declared series.
    return targetObservabilityConfigurationError("PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON", "A non-empty metric-series catalogue is required when cloudwatch-otel metrics are enabled."); // Prevent silent metric loss.
  }
  try { // Parse before structural validation so malformed JSON never reaches the adapter.
    const parsed: unknown = JSON.parse(raw); // Treat environment JSON as untrusted deployment input until checked.
    if (!Array.isArray(parsed)) { // Require an explicit ordered array of metric mappings.
      return targetObservabilityConfigurationError("PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON", "Expected a JSON array of metric-series definitions."); // Keep the target catalogue scanable and deterministic.
    }
    const series: CloudWatchOtelMetricSeries[] = []; // Accumulate only structurally valid mappings for the adapter.
    for (const [index, item] of parsed.entries()) { // Validate each JSON item while preserving its safe array position.
      const definition = metricSeriesDefinition(item, index); // Check the untyped mapping before using it as an adapter contract.
      if (!definition.ok) return definition; // Stop at the first safe configuration error without creating a partial runtime.
      series.push(definition.value); // Retain the structurally valid mapping in the reviewed catalogue order.
    }
    return { ok: true, value: series }; // Return only structurally valid target series to the adapter.
  } catch { // Treat parsing failures as ordinary target configuration errors.
    return targetObservabilityConfigurationError("PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON", "Expected valid JSON metric-series definitions."); // Do not echo raw JSON into process logs.
  }
}

function metricSeriesDefinition( // Validate one JSON metric-series mapping before the adapter checks deeper semantic rules.
  value: unknown, // Receive one untyped JSON array item.
  index: number, // Retain the item index for a safe configuration-path diagnostic.
): { readonly ok: true; readonly value: CloudWatchOtelMetricSeries } | { readonly ok: false; readonly error: TargetObservabilityConfigurationError } {
  if (!isRecord(value)) { // Require every metric series to be a JSON object.
    return targetObservabilityConfigurationError(`PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON[${index}]`, "Each metric-series definition must be an object."); // Avoid property access on malformed deployment input.
  }
  const sourceName = stringField(value, "sourceName"); // Read the Core metric identity.
  const sourceKind = stringField(value, "sourceKind"); // Read the Core metric kind.
  const sourceUnit = stringField(value, "sourceUnit"); // Read the Core metric unit.
  const instrumentName = stringField(value, "instrumentName"); // Read the exported OTel instrument identity.
  const description = stringField(value, "description"); // Read the operator-facing series meaning.
  const allowedLabelNames = stringArrayField(value, "allowedLabelNames"); // Read the reviewed label allowlist.
  const cardinalityLimit = numberField(value, "cardinalityLimit"); // Read the in-process combination cap.
  const histogramBucketBoundaries = optionalNumberArrayField(value, "histogramBucketBoundaries"); // Read optional distribution boundaries.
  if (sourceName === undefined || sourceKind === undefined || sourceUnit === undefined || instrumentName === undefined || description === undefined || allowedLabelNames === undefined || cardinalityLimit === undefined || histogramBucketBoundaries === "invalid") { // Reject incomplete or wrongly typed mappings.
    return targetObservabilityConfigurationError(`PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON[${index}]`, "Each metric-series definition must use the reviewed adapter field types."); // Leave deeper policy semantics to the adapter.
  }
  if (sourceKind !== "counter" && sourceKind !== "gauge" && sourceKind !== "histogram" && sourceKind !== "timer") { // Restrict the untyped JSON string to the Core metric-kind vocabulary.
    return targetObservabilityConfigurationError(`PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON[${index}].sourceKind`, "Expected a Core metric kind."); // Prevent unsafe type assertion at the adapter boundary.
  }
  return { // Reconstruct the adapter's typed mapping from validated JSON fields.
    ok: true, // Mark this individual series structurally valid.
    value: { // Return the target-approved Core-to-OTel mapping.
      sourceName, // Preserve the Core metric identity.
      sourceKind, // Preserve the validated Core metric kind.
      sourceUnit, // Preserve the Core metric unit.
      instrumentName, // Preserve the OTel instrument identity.
      description, // Preserve the operator-facing meaning.
      allowedLabelNames, // Preserve the reviewed target label allowlist.
      cardinalityLimit, // Preserve the reviewed target series cap.
      ...(histogramBucketBoundaries === undefined ? {} : { histogramBucketBoundaries }), // Include buckets only for an explicitly supplied distribution policy.
    }, // Finish the typed metric-series mapping.
  }; // Return the validated mapping.
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> { // Narrow untyped JSON safely to an object with string keys.
  return typeof value === "object" && value !== null && !Array.isArray(value); // Exclude null and arrays before property inspection.
}

function stringField(value: Readonly<Record<string, unknown>>, key: string): string | undefined { // Read one required non-empty JSON string field.
  const field = value[key]; // Look up the field once.
  return typeof field === "string" && field.trim().length > 0 ? field : undefined; // Reject empty or non-string deployment values.
}

function numberField(value: Readonly<Record<string, unknown>>, key: string): number | undefined { // Read one required finite JSON number field.
  const field = value[key]; // Look up the field once.
  return typeof field === "number" && Number.isFinite(field) ? field : undefined; // Reject strings, NaN, infinity, and absent values.
}

function stringArrayField(value: Readonly<Record<string, unknown>>, key: string): readonly string[] | undefined { // Read one required string-array JSON field.
  const field = value[key]; // Look up the field once.
  return Array.isArray(field) && field.every((item) => typeof item === "string") ? field : undefined; // Reject mixed arrays before adapter validation.
}

function optionalNumberArrayField(value: Readonly<Record<string, unknown>>, key: string): readonly number[] | undefined | "invalid" { // Read one optional finite-number-array field.
  const field = value[key]; // Look up the optional field once.
  if (field === undefined) return undefined; // Preserve the difference between absent optional buckets and malformed buckets.
  return Array.isArray(field) && field.every((item) => typeof item === "number" && Number.isFinite(item)) ? field : "invalid"; // Reject non-numeric bucket values.
}

function targetObservabilityConfigurationError( // Construct one stable safe target-observability startup error.
  path: string, // Name the target-owned key or JSON position needing correction.
  reason: string, // Explain the expected safe shape.
): { readonly ok: false; readonly error: TargetObservabilityConfigurationError } {
  return { // Keep the result shape consistent with the target entrypoint's other configuration parsers.
    ok: false, // Mark target metrics construction as unavailable.
    error: { // Return only safe operational diagnostic data.
      code: "KANBIEN_PLATFORM_TARGET_OBSERVABILITY_CONFIG_INVALID", // Give logs and runbooks a stable error code.
      defaultMessage: "Kanbien platform target observability configuration is invalid.", // Avoid logging environment values.
      details: { path, reason }, // Record the reviewed field name and safe reason.
    }, // Finish the error record.
  }; // Return the failed result.
}
