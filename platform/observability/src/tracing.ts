import {
  noopTracer,
  traceSpanName,
  type TraceAttributes,
  type TraceContext,
  type TraceSpan,
  type TraceSpanEndInput,
  type Tracer,
} from "@kanbien/core/monitoring";
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
  readonly method?: string;
  readonly status?: number;
  readonly outcome?: string;
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
    method: input.method,
    status: input.status,
    outcome: input.outcome,
  });
}

export interface PlatformTraceAttributesInput {
  readonly route?: string;
  readonly job?: string;
  readonly errorClass?: string;
  readonly latencyMs?: number;
  readonly retryCount?: number;
  readonly healthState?: string;
  readonly method?: string;
  readonly status?: number;
  readonly outcome?: string;
}

export interface PlatformTraceSpanInput {
  readonly name: string;
  readonly parent?: TraceContext;
  readonly attributes?: PlatformTraceAttributesInput;
}

export function platformTraceAttributes(input: PlatformTraceAttributesInput): TraceAttributes {
  const fields = normalizePlatformLogFields({
    route: input.route,
    job: input.job,
    errorClass: input.errorClass,
    latencyMs: input.latencyMs,
    retryCount: input.retryCount,
    healthState: input.healthState,
    method: input.method,
    status: input.status,
    outcome: input.outcome,
  });
  return Object.fromEntries(
    Object.entries(fields).filter((entry): entry is [string, string | number | boolean] =>
      typeof entry[1] === "string" || typeof entry[1] === "number" || typeof entry[1] === "boolean"),
  );
}

export function startPlatformTraceSpan(tracer: Tracer, input: PlatformTraceSpanInput): TraceSpan {
  try {
    const span = tracer.startSpan({
      name: traceSpanName(input.name),
      ...(input.parent === undefined ? {} : { parent: input.parent }),
      ...(input.attributes === undefined ? {} : { attributes: platformTraceAttributes(input.attributes) }),
    });
    return isTraceSpan(span) ? span : noopPlatformTraceSpan(input.parent);
  } catch {
    return noopPlatformTraceSpan(input.parent);
  }
}

export function endPlatformTraceSpan(span: TraceSpan, input: {
  readonly outcome: TraceSpanEndInput["outcome"];
  readonly attributes?: PlatformTraceAttributesInput;
}): void {
  try {
    span.end({
      outcome: input.outcome,
      ...(input.attributes === undefined ? {} : { attributes: platformTraceAttributes(input.attributes) }),
    });
  } catch {
    // Observability must never turn a completed request into a failure.
  }
}

function noopPlatformTraceSpan(parent: TraceContext | undefined): TraceSpan {
  return noopTracer.startSpan({
    name: traceSpanName("platform.observability.noop"),
    ...(parent === undefined ? {} : { parent }),
  });
}

function isTraceSpan(value: unknown): value is TraceSpan {
  return typeof value === "object"
    && value !== null
    && "context" in value
    && "end" in value
    && typeof value.end === "function";
}
