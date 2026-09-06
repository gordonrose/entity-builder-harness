import { recordConfigSource, type ConfigSource } from "@kanbien/core/config";
import type { Principal } from "@kanbien/core/authn";
import { noopLogger, type Logger } from "@kanbien/core/logging";
import { noopMetrics, type Metrics } from "@kanbien/core/monitoring";
import type { QueueMessage } from "@kanbien/core/queues";
import type { TenantContext } from "@kanbien/core/tenancy";
import {
  fixedClock,
  isoDateTimeFromDate,
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

export interface PlatformRuntimeContextDepsInput {
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
  readonly now?: ISODateTime;
  readonly tenant?: TenantContext;
  readonly abortSignal?: AbortSignal;
}

export function createPlatformRuntimeContextDeps(input: PlatformRuntimeContextDepsInput = {}): PlatformRuntimeContextDeps {
  return {
    logger: input.logger ?? noopLogger,
    metrics: input.metrics ?? noopMetrics,
    config: input.config ?? recordConfigSource({}),
    flags: input.flags ?? fixedFeatureFlagReader({}),
    clock: input.clock ?? fixedClock(new Date(defaultPlatformRuntimeDateTime)),
  };
}

export function createPlatformRuntimeRequestContext(input: PlatformRuntimeRequestContextInput): PlatformRequestContext {
  const deps = createPlatformRuntimeContextDeps(input);
  const now = input.now ?? isoDateTimeFromDate(deps.clock.now());
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
}

export function createPlatformRuntimeJobContext(input: PlatformRuntimeJobContextInput): PlatformJobContext {
  const deps = createPlatformRuntimeContextDeps(input);
  const now = input.now ?? isoDateTimeFromDate(deps.clock.now());

  return {
    jobName: input.jobName,
    message: input.message,
    correlationId: input.correlationId,
    now,
    logger: deps.logger,
    metrics: deps.metrics,
    config: deps.config,
    flags: deps.flags,
    clock: deps.clock,
    ...(input.tenant === undefined ? {} : { tenant: input.tenant }),
    ...(input.abortSignal === undefined ? {} : { abortSignal: input.abortSignal }),
  };
}

const defaultPlatformRuntimeDateTime = "2026-07-10T00:00:00.000Z";
