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
import { platformOptionalErrorClassification, type PlatformErrorClassificationOptions } from "@kanbien/platform-contracts";
import { observePlatformSinkCompletion } from "./diagnostics";
import { reportPlatformObservationBoundary, type PlatformObservationDiagnostics } from "./boundary-observation";
import type { PlatformObservationBoundaryDetail } from "./boundary-definitions";

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

export function platformTraceFields(input: PlatformTraceFieldsInput, classification?: PlatformErrorClassificationOptions, observations?: PlatformObservationDiagnostics): PlatformSafeLogFields {
  let phase: PlatformObservationBoundaryDetail["phase"] = "input-projection";
  let field: PlatformObservationBoundaryDetail["field"] = "fields";
  try { const projected = {
    requestId: input.requestId,
    correlationId: (field = "correlation-id", input.correlationId),
    tenant: (field = "fields", input.tenant),
    route: (field = "route", input.route),
    job: (field = "job", input.job),
    errorClass: (field = "error-class", platformOptionalErrorClassification(input.errorClass, classification)),
    latencyMs: (field = "latency", input.latencyMs),
    retryCount: (field = "retry-count", input.retryCount),
    healthState: (field = "health-state", input.healthState),
    method: (field = "method", input.method),
    status: (field = "status", input.status),
    outcome: (field = "outcome", input.outcome),
  }; phase = "field-normalization"; field = "fields"; return normalizePlatformLogFields(projected); } catch (error) {
    reportPlatformObservationBoundary(observations, { operation: "trace-fields", phase, field, reason: "threw", effect: "not-attempted" }, error); throw error;
  }
}

export interface PlatformTraceAttributesInput {
  readonly capability?: string;
  readonly action?: string;
  readonly actor_type?: string;
  readonly interaction_source?: string;
  readonly execution_context?: string;
  readonly http_method?: string;
  readonly http_status_code?: number;
  readonly job_delivery_disposition?: string;
  readonly route?: string;
  readonly job?: string;
  readonly errorClass?: string;
  readonly error_class?: string;
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

export function platformTraceAttributes(input: PlatformTraceAttributesInput, classification?: PlatformErrorClassificationOptions, observations?: PlatformObservationDiagnostics): TraceAttributes {
  let phase: PlatformObservationBoundaryDetail["phase"] = "input-projection";
  let field: PlatformObservationBoundaryDetail["field"] = "attributes";
  try {
  const projected = {
    capability: input.capability,
    action: input.action,
    actor_type: input.actor_type,
    interaction_source: input.interaction_source,
    execution_context: input.execution_context,
    http_method: input.http_method,
    http_status_code: input.http_status_code,
    job_delivery_disposition: input.job_delivery_disposition,
    route: (field = "route", input.route),
    job: (field = "job", input.job),
    errorClass: (field = "error-class", platformOptionalErrorClassification(input.errorClass, classification)),
    error_class: platformOptionalErrorClassification(input.error_class, classification),
    latencyMs: (field = "latency", input.latencyMs),
    retryCount: (field = "retry-count", input.retryCount),
    healthState: (field = "health-state", input.healthState),
    method: (field = "method", input.method),
    status: (field = "status", input.status),
    outcome: (field = "outcome", input.outcome),
  };
  phase = "field-normalization"; field = "attributes";
  const fields = normalizePlatformLogFields(projected);
  return Object.fromEntries(
    Object.entries(fields).filter((entry): entry is [string, string | number | boolean] =>
      typeof entry[1] === "string" || typeof entry[1] === "number" || typeof entry[1] === "boolean"),
  );
  } catch (error) { reportPlatformObservationBoundary(observations, { operation: "trace-fields", phase, field, reason: "threw", effect: "not-attempted" }, error); throw error; }
}

export function startPlatformTraceSpan(tracer: Tracer, input: PlatformTraceSpanInput, classification?: PlatformErrorClassificationOptions, observations?: PlatformObservationDiagnostics): TraceSpan {
  let phase: PlatformObservationBoundaryDetail["phase"] = "sink-selection";
  let field: PlatformObservationBoundaryDetail["field"] = "provider";
  let prepared: Parameters<Tracer["startSpan"]>[0];
  let rawName: string;
  let rawAttributes: PlatformTraceAttributesInput;
  try {
    const span = tracer.startSpan((phase = "input-projection", prepared = {
      name: (field = "name", rawName = input.name, phase = "field-normalization", traceSpanName(rawName)),
      ...(phase = "input-projection", field = "parent", input.parent === undefined ? {} : { parent: input.parent }),
      ...(field = "attributes", input.attributes === undefined ? {} : { attributes: (rawAttributes = input.attributes, phase = "field-normalization", platformTraceAttributes(rawAttributes, classification)) }),
    }, phase = "span-invocation", field = "provider", prepared));
    phase = "span-validation"; field = "result";
    if (isTraceSpan(span)) return span;
    reportPlatformObservationBoundary(observations, { operation: "trace-start", phase, field: "result", reason: "invalid-span", effect: "unknown" }, span);
    observePlatformSinkCompletion(span, (error) => reportPlatformObservationBoundary(observations,
      { operation: "trace-start", phase: "span-completion", field: "result", reason: "rejected", effect: "unknown" }, error));
    phase = "fallback"; field = "parent";
    return noopPlatformTraceSpan(input.parent);
  } catch (error) {
    reportPlatformObservationBoundary(observations, { operation: "trace-start", phase, field, reason: "threw",
      effect: phase === "fallback" ? "fallback-threw" : phase === "span-invocation" || phase === "span-validation" ? "unknown" : "not-attempted" }, error);
    try { return noopPlatformTraceSpan(input.parent); }
    catch (fallbackError) {
      reportPlatformObservationBoundary(observations, { operation: "trace-start", phase: "fallback", field: "parent", reason: "threw", effect: "fallback-threw" }, fallbackError);
      throw fallbackError;
    }
  }
}

export function endPlatformTraceSpan(span: TraceSpan, input: {
  readonly outcome: TraceSpanEndInput["outcome"];
  readonly attributes?: PlatformTraceAttributesInput;
}, classification?: PlatformErrorClassificationOptions, observations?: PlatformObservationDiagnostics): void {
  let phase: PlatformObservationBoundaryDetail["phase"] = "sink-selection";
  let field: PlatformObservationBoundaryDetail["field"] = "provider";
  let prepared: TraceSpanEndInput;
  let rawAttributes: PlatformTraceAttributesInput;
  try {
    const pending: unknown = span.end((phase = "input-projection", prepared = {
      outcome: (field = "outcome", input.outcome),
      ...(field = "attributes", input.attributes === undefined ? {} : { attributes: (rawAttributes = input.attributes, phase = "field-normalization", platformTraceAttributes(rawAttributes, classification)) }),
    }, phase = "span-end", field = "provider", prepared));
    observePlatformSinkCompletion(pending, (error) => reportPlatformObservationBoundary(observations,
      { operation: "trace-end", phase: "span-completion", field: "provider", reason: "rejected", effect: "unknown" }, error));
  } catch (error) {
    reportPlatformObservationBoundary(observations, { operation: "trace-end", phase, field, reason: "threw", effect: phase === "span-end" ? "unknown" : "not-attempted" }, error);
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
