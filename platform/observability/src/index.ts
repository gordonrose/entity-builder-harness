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

export { platformTraceFields } from "./tracing";
export type { PlatformTraceFieldsInput } from "./tracing";
