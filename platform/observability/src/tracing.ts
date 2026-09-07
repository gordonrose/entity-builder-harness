import {
  normalizePlatformLogFields,
  type PlatformSafeLogFields,
} from "./normalization";

export interface PlatformTraceFieldsInput {
  readonly requestId?: string;
  readonly correlationId?: string;
  readonly tenant?: string;
  readonly route?: string;
  readonly job?: string;
  readonly errorClass?: string;
  readonly latencyMs?: number;
  readonly retryCount?: number;
  readonly healthState?: string;
}

export function platformTraceFields(input: PlatformTraceFieldsInput): PlatformSafeLogFields {
  return normalizePlatformLogFields({
    requestId: input.requestId,
    correlationId: input.correlationId,
    tenant: input.tenant,
    route: input.route,
    job: input.job,
    errorClass: input.errorClass,
    latencyMs: input.latencyMs,
    retryCount: input.retryCount,
    healthState: input.healthState,
  });
}
