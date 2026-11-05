export { metricPreparationDiagnostic, metricRejectionDiagnostic, metricCreationDiagnostic, metricRecordingDiagnostic,
  metricPreparationRecord, metricRejectionRecord, metricCreationRecord, metricRecordingRecord,
  attachPlatformMetricDiagnostic, capturePlatformMetricDiagnostic, createPlatformMetricDiagnosticBinding, platformMetricDiagnosticLimit } from "./metric-diagnostics";
export type { PlatformMetricDiagnosticBinding, PlatformMetricDiagnosticOptions, PlatformMetricOperation } from "./metric-diagnostics";
export { createPlatformMetricLifecycleDiagnosticBinding } from "./metric-diagnostics";
export type { PlatformMetricLifecycleDiagnosticBinding, PlatformMetricLifecycleOperation } from "./metric-diagnostics";
export { metricCollectionDiagnostic, metricCollectionFailureDiagnostic, metricExportDiagnostic, metricFlushDiagnostic, metricShutdownDiagnostic,
  metricCollectionIssuesRecord, metricCollectionFailureRecord, metricExportFailureRecord, metricLifecycleFailureRecord } from "./metric-lifecycle-diagnostics";

export { createPlatformDiagnosticReporter, reportPlatformDiagnostic, reportPlatformErrorDiagnostic } from "./diagnostics";
export { reportPlatformObservationBoundary, reportPlatformObservationSources } from "./boundary-observation";
export type { PlatformObservationDiagnostics } from "./boundary-observation";
export { platformObservationBoundaryDiagnostic, platformDiagnosticReportingSuppressedDiagnostic } from "./boundary-definitions";
export type { PlatformObservationBoundaryDetail } from "./boundary-definitions";
export { platformReadinessDiagnosticDefinitions } from "./readiness-diagnostics";
export { observabilityConfigurationDiagnostic, observabilityConstructionDiagnostic, platformObservabilityDiagnosticCatalog,
  observabilityConfigurationRecord, observabilityConstructionRecord, observabilityConfigurationReasons, observabilityConfigurationSettings,
  validatePlatformReadinessConfiguration, mergeObservabilityConfigurationFailures,
  observabilityConfigurationObject, observabilityConfigurationField, observabilityTextIssue, observabilityIntegerIssue } from "./configuration";
export type { ObservabilityConfigurationReason, ObservabilityConfigurationIssue, ObservabilityConfigurationFailure, PlatformReadinessConfiguration } from "./configuration";
export { validatePlatformMetricSeries } from "./metric-series-configuration";
export type { PlatformMetricSeries } from "./metric-series-configuration";
export {
  normalizePlatformError,
  normalizePlatformLogFields,
  normalizePlatformValue,
  platformErrorClass,
} from "./normalization";
export type {
  PlatformSafeLogFields,
  PlatformValueNormalizationOptions,
} from "./normalization";
export type { PlatformErrorClassificationOptions } from "@kanbien/platform-contracts";

export {
  createPlatformSafeLogger,
  writePlatformLog,
} from "./logging";
export type { PlatformLogInput } from "./logging";

export {
  elapsedMilliseconds,
  recordPlatformHealthMetric,
  recordPlatformJobMetric,
  recordPlatformMetric,
  recordPlatformRequestMetric,
} from "./metrics";
export type { PlatformMetricInput } from "./metrics";

export {
  createPlatformReadinessObserver,
  emitPlatformReadinessObservation,
} from "./readiness-observation";
export type {
  PlatformReadinessObserver,
  PlatformReadinessObserverIdentity,
  PlatformReadinessObserverOptions,
  PlatformReadinessProbeResult,
} from "./readiness-observation";

export {
  endPlatformTraceSpan,
  platformTraceAttributes,
  platformTraceFields,
  startPlatformTraceSpan,
} from "./tracing";
export type {
  PlatformTraceAttributesInput,
  PlatformTraceFieldsInput,
  PlatformTraceSpanInput,
} from "./tracing";
