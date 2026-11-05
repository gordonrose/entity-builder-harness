import { runtimeBoundaryEvidence, type PlatformRuntimeDiagnosticOptions, type RuntimeBoundaryDetail } from "./diagnostics";
import { recordConfigSource, type ConfigSource } from "@kanbien/core/config";
import type { Principal } from "@kanbien/core/authn";
import { noopLogger, type Logger } from "@kanbien/core/logging";
import { noopMetrics, type Metrics } from "@kanbien/core/monitoring";
import type { QueueMessage } from "@kanbien/core/queues";
import type { TenantContext } from "@kanbien/core/tenancy";
import {
  fixedClock,
  isoDateTimeFromDate,
  type CausationId,
  type Clock,
  type CorrelationId,
  type ISODateTime,
} from "@kanbien/core/shared";
import {
  fixedFeatureFlagReader,
  type FeatureFlagReader,
  type PlatformJobContext,
  type PlatformJobName,
  type PlatformRequestContext,
} from "@kanbien/platform-contracts";

export interface PlatformRuntimeContextDeps {
  readonly logger: Logger;
  readonly metrics: Metrics;
  readonly config: ConfigSource;
  readonly flags: FeatureFlagReader;
  readonly clock: Clock;
}

export interface PlatformRuntimeContextDepsInput extends PlatformRuntimeDiagnosticOptions {
  readonly logger?: Logger;
  readonly metrics?: Metrics;
  readonly config?: ConfigSource;
  readonly flags?: FeatureFlagReader;
  readonly clock?: Clock;
}

export interface PlatformRuntimeRequestContextInput extends PlatformRuntimeContextDepsInput {
  readonly requestId: CorrelationId;
  readonly correlationId?: CorrelationId;
  readonly now?: ISODateTime;
  readonly tenant?: TenantContext;
  readonly principal?: Principal;
  readonly method: PlatformRequestContext["method"];
  readonly path: string;
  readonly abortSignal?: AbortSignal;
}

export interface PlatformRuntimeJobContextInput extends PlatformRuntimeContextDepsInput {
  readonly jobName: PlatformJobName;
  readonly message: QueueMessage;
  readonly correlationId: CorrelationId;
  readonly causationId?: CausationId;
  readonly now?: ISODateTime;
  readonly tenant?: TenantContext;
  readonly abortSignal?: AbortSignal;
}

export function createPlatformRuntimeContextDeps(input: PlatformRuntimeContextDepsInput = {}): PlatformRuntimeContextDeps {
  try { return contextDeps(input); }
  catch (error) {
    runtimeBoundaryEvidence(input, { operation: "context-deps", phase: "dependency-selection", subject: "context", boundary: "selection", effect: "context-not-returned" }, error, undefined, false);
    throw error;
  }
}
function contextDeps(input: PlatformRuntimeContextDepsInput): PlatformRuntimeContextDeps {
  return {
    logger: input.logger ?? noopLogger,
    metrics: input.metrics ?? noopMetrics,
    config: input.config ?? recordConfigSource({}),
    flags: input.flags ?? fixedFeatureFlagReader({}),
    clock: input.clock ?? fixedClock(new Date(defaultPlatformRuntimeDateTime)),
  };
}

export function createPlatformRuntimeRequestContext(input: PlatformRuntimeRequestContextInput): PlatformRequestContext {
  let phase: RuntimeBoundaryDetail["phase"] = "dependency-selection";
  try {
  const deps = contextDeps(input);
  phase = "timestamp-selection";
  let date: Date;
  const now = input.now ?? (phase = "clock-read", date = deps.clock.now(), phase = "timestamp-normalization", isoDateTimeFromDate(date));
  phase = "context-projection";
  const correlationId = input.correlationId ?? input.requestId;

  return {
    requestId: input.requestId,
    correlationId,
    now,
    logger: deps.logger,
    metrics: deps.metrics,
    config: deps.config,
    flags: deps.flags,
    clock: deps.clock,
    ...(input.tenant === undefined ? {} : { tenant: input.tenant }),
    ...(input.principal === undefined ? {} : { principal: input.principal }),
    method: input.method,
    path: input.path,
    ...(input.abortSignal === undefined ? {} : { abortSignal: input.abortSignal }),
  };
  } catch (error) {
    runtimeBoundaryEvidence(input, { operation: "request-context", phase, subject: "context",
      boundary: phase === "clock-read" || phase === "timestamp-normalization" ? "invocation" : phase === "context-projection" ? "projection" : "selection",
      effect: "context-not-returned" }, error, undefined, false);
    throw error;
  }
}

export function createPlatformRuntimeJobContext(input: PlatformRuntimeJobContextInput): PlatformJobContext {
  let phase: RuntimeBoundaryDetail["phase"] = "dependency-selection";
  try {
  const deps = contextDeps(input);
  phase = "timestamp-selection";
  let date: Date;
  const now = input.now ?? (phase = "clock-read", date = deps.clock.now(), phase = "timestamp-normalization", isoDateTimeFromDate(date));
  phase = "context-projection";

  return {
    jobName: input.jobName,
    message: input.message,
    correlationId: input.correlationId,
    ...(input.causationId === undefined ? {} : { causationId: input.causationId }),
    now,
    logger: deps.logger,
    metrics: deps.metrics,
    config: deps.config,
    flags: deps.flags,
    clock: deps.clock,
    ...(input.tenant === undefined ? {} : { tenant: input.tenant }),
    ...(input.abortSignal === undefined ? {} : { abortSignal: input.abortSignal }),
  };
  } catch (error) {
    runtimeBoundaryEvidence(input, { operation: "job-context", phase, subject: "context",
      boundary: phase === "clock-read" || phase === "timestamp-normalization" ? "invocation" : phase === "context-projection" ? "projection" : "selection",
      effect: "context-not-returned" }, error, undefined, false);
    throw error;
  }
}

const defaultPlatformRuntimeDateTime = "2026-07-10T00:00:00.000Z";
