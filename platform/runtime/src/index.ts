import { recordConfigSource, type ConfigSource } from "@kanbien/core/config";
import { noopLogger, type Logger } from "@kanbien/core/logging";
import { noopMetrics, type Metrics } from "@kanbien/core/monitoring";
import type { QueueMessage } from "@kanbien/core/queues";
import {
  fixedClock,
  isoDateTimeFromDate,
  type Clock,
  type CorrelationId,
  type ISODateTime,
  type JsonValue,
  type Result,
} from "@kanbien/core/shared";
import {
  defaultReservedPlatformRoutePaths,
  duplicatePlatformRegistration,
  fixedFeatureFlagReader,
  platformAppId,
  unknownPlatformPermission,
  validatePlatformJobRegistration,
  validatePlatformPermissionDeclaration,
  validatePlatformRouteRegistration,
  type FeatureFlagReader,
  type PlatformApp,
  type PlatformAppRegistry,
  type PlatformContractError,
  type PlatformHealthRegistration,
  type PlatformJobContext,
  type PlatformJobName,
  type PlatformJobRegistration,
  type PlatformMountDeps,
  type PlatformPermissionDeclaration,
  type PlatformRequestContext,
  type PlatformRouteRegistration,
} from "@kanbien/platform-contracts";

export type PlatformRuntimeErrorCode =
  | "PLATFORM_RUNTIME_APP_MOUNT_FAILED"
  | "PLATFORM_RUNTIME_REGISTRY_INVALID"
  | "PLATFORM_RUNTIME_LIFECYCLE_FAILED"
  | "PLATFORM_RUNTIME_INVALID_STATE";

export interface PlatformRuntimeError {
  readonly code: PlatformRuntimeErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
  readonly cause?: unknown;
}

export interface PlatformRuntimeMountFailure extends PlatformRuntimeError {
  readonly code: "PLATFORM_RUNTIME_APP_MOUNT_FAILED" | "PLATFORM_RUNTIME_REGISTRY_INVALID";
  readonly contractErrors: readonly PlatformContractError[];
}

export interface PlatformRuntimeRegistry extends PlatformAppRegistry {
  permissions(): readonly PlatformPermissionDeclaration[];
  routes(): readonly PlatformRouteRegistration[];
  jobs(): readonly PlatformJobRegistration[];
  healthChecks(): readonly PlatformHealthRegistration[];
  errors(): readonly PlatformContractError[];
  validate(): readonly PlatformContractError[];
}

export interface PlatformRuntimeRegistryOptions {
  readonly reservedPaths?: readonly string[];
}

export interface PlatformRuntimeMountInput {
  readonly apps: readonly PlatformApp[];
  readonly deps: PlatformMountDeps;
  readonly registryOptions?: PlatformRuntimeRegistryOptions;
}

export interface PlatformRuntimeMountResult {
  readonly apps: readonly PlatformApp[];
  readonly registry: PlatformRuntimeRegistry;
  readonly permissions: readonly PlatformPermissionDeclaration[];
  readonly routes: readonly PlatformRouteRegistration[];
  readonly jobs: readonly PlatformJobRegistration[];
  readonly healthChecks: readonly PlatformHealthRegistration[];
}

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
  readonly method: PlatformRequestContext["method"];
  readonly path: string;
  readonly abortSignal?: AbortSignal;
}

export interface PlatformRuntimeJobContextInput extends PlatformRuntimeContextDepsInput {
  readonly jobName: PlatformJobName;
  readonly message: QueueMessage;
  readonly correlationId: CorrelationId;
  readonly now?: ISODateTime;
  readonly abortSignal?: AbortSignal;
}

export type PlatformRuntimeLifecycleState = "created" | "starting" | "ready" | "stopping" | "stopped" | "failed";

export type PlatformRuntimeLifecyclePhase =
  | "app.beforeStart"
  | "resource.start"
  | "app.afterStart"
  | "app.beforeStop"
  | "resource.drain"
  | "resource.close"
  | "telemetry.flush"
  | "app.afterStop";

export interface PlatformRuntimeLifecycleEvent {
  readonly phase: PlatformRuntimeLifecyclePhase;
  readonly name: string;
  readonly at: ISODateTime;
}

export interface PlatformRuntimeResource {
  readonly name: string;
  start?(): Promise<void> | void;
  drain?(): Promise<void> | void;
  close?(): Promise<void> | void;
}

export interface PlatformRuntimeTelemetry {
  readonly name: string;
  flush(): Promise<void> | void;
}

export interface PlatformRuntimeLifecycleInput {
  readonly apps: readonly PlatformApp[];
  readonly resources?: readonly PlatformRuntimeResource[];
  readonly telemetry?: readonly PlatformRuntimeTelemetry[];
  readonly clock?: Clock;
}

export interface PlatformRuntimeLifecycleController {
  state(): PlatformRuntimeLifecycleState;
  isReady(): boolean;
  events(): readonly PlatformRuntimeLifecycleEvent[];
  start(): Promise<Result<void, PlatformRuntimeError>>;
  shutdown(): Promise<Result<readonly PlatformRuntimeLifecycleEvent[], PlatformRuntimeError>>;
}

export function createPlatformRuntimeRegistry(options: PlatformRuntimeRegistryOptions = {}): PlatformRuntimeRegistry {
  const reservedPaths = options.reservedPaths ?? defaultReservedPlatformRoutePaths;
  const permissions: PlatformPermissionDeclaration[] = [];
  const routes: PlatformRouteRegistration[] = [];
  const jobs: PlatformJobRegistration[] = [];
  const healthChecks: PlatformHealthRegistration[] = [];
  const errors: PlatformContractError[] = [];

  function track(error: PlatformContractError): Result<void, PlatformContractError> {
    errors.push(error);
    return { ok: false, error };
  }

  return {
    registerPermission(permissionDeclaration) {
      const validation = validatePlatformPermissionDeclaration(permissionDeclaration);
      if (!validation.ok) {
        return track(validation.error);
      }

      if (permissions.some((registered) => registered.permission === permissionDeclaration.permission)) {
        return track(duplicatePlatformRegistration("permission", permissionDeclaration.permission));
      }

      permissions.push({ ...permissionDeclaration });
      return contractSuccess();
    },
    registerRoute(route) {
      const validation = validatePlatformRouteRegistration(route, { reservedPaths });
      if (!validation.ok) {
        return track(validation.error);
      }

      if (routes.some((registered) => registered.name === route.name || routeKey(registered) === routeKey(route))) {
        return track(duplicatePlatformRegistration("route", routeKey(route)));
      }

      routes.push(route);
      return contractSuccess();
    },
    registerJob(job) {
      const validation = validatePlatformJobRegistration(job);
      if (!validation.ok) {
        return track(validation.error);
      }

      if (jobs.some((registered) => registered.name === job.name || registered.messageType === job.messageType)) {
        return track(duplicatePlatformRegistration("job", String(job.name)));
      }

      jobs.push(job);
      return contractSuccess();
    },
    registerHealthCheck(healthCheck) {
      if (healthChecks.some((registered) => registered.name === healthCheck.name)) {
        return track(duplicatePlatformRegistration("health", String(healthCheck.name)));
      }

      healthChecks.push(healthCheck);
      return contractSuccess();
    },
    registerConfigSchema() {
      return contractSuccess();
    },
    permissions: () => permissions.map((permission) => ({ ...permission })),
    routes: () => [...routes],
    jobs: () => [...jobs],
    healthChecks: () => [...healthChecks],
    errors: () => [...errors],
    validate() {
      const validationErrors = [...errors];
      const declaredPermissions = permissions.map((permission) => permission.permission);

      for (const route of routes) {
        if (route.auth.kind !== "authenticated") {
          continue;
        }

        for (const permission of route.auth.permissions ?? []) {
          if (!declaredPermissions.includes(permission)) {
            validationErrors.push(unknownPlatformPermission(permission, declaredPermissions));
          }
        }
      }

      return validationErrors;
    },
  };
}

export async function mountPlatformRuntimeApps(
  input: PlatformRuntimeMountInput,
): Promise<Result<PlatformRuntimeMountResult, PlatformRuntimeMountFailure>> {
  const registry = createPlatformRuntimeRegistry(input.registryOptions);
  const appIds = new Set<string>();
  const mountedApps: PlatformApp[] = [];
  const contractErrors: PlatformContractError[] = [];

  for (const app of input.apps) {
    const appId = platformAppId(String(app.id));
    if (!appId.ok) {
      contractErrors.push(appId.error);
      continue;
    }

    if (appIds.has(app.id)) {
      contractErrors.push(duplicatePlatformRegistration("app", app.id));
      continue;
    }

    appIds.add(app.id);

    try {
      await app.mount(registry, input.deps);
      mountedApps.push(app);
    } catch (error) {
      return mountFailure("PLATFORM_RUNTIME_APP_MOUNT_FAILED", registry.errors(), { appId: app.id }, error);
    }
  }

  contractErrors.push(...registry.validate());
  if (contractErrors.length > 0) {
    return mountFailure("PLATFORM_RUNTIME_REGISTRY_INVALID", contractErrors);
  }

  return {
    ok: true,
    value: {
      apps: mountedApps,
      registry,
      permissions: registry.permissions(),
      routes: registry.routes(),
      jobs: registry.jobs(),
      healthChecks: registry.healthChecks(),
    },
  };
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
    ...(input.abortSignal === undefined ? {} : { abortSignal: input.abortSignal }),
  };
}

export function createPlatformRuntimeLifecycle(
  input: PlatformRuntimeLifecycleInput,
): PlatformRuntimeLifecycleController {
  const resources = [...(input.resources ?? [])];
  const telemetry = [...(input.telemetry ?? [])];
  const apps = [...input.apps];
  const clock = input.clock ?? fixedClock(new Date(defaultPlatformRuntimeDateTime));
  const events: PlatformRuntimeLifecycleEvent[] = [];
  let state: PlatformRuntimeLifecycleState = "created";

  function record(phase: PlatformRuntimeLifecyclePhase, name: string): void {
    events.push({ phase, name, at: isoDateTimeFromDate(clock.now()) });
  }

  async function runStep(phase: PlatformRuntimeLifecyclePhase, name: string, step: () => Promise<void> | void): Promise<void> {
    await step();
    record(phase, name);
  }

  return {
    state: () => state,
    isReady: () => state === "ready",
    events: () => [...events],
    async start() {
      if (state !== "created") {
        return runtimeFailure("PLATFORM_RUNTIME_INVALID_STATE", "Runtime lifecycle can only start from the created state.", { state });
      }

      state = "starting";

      try {
        for (const app of apps) {
          if (app.lifecycle?.beforeStart !== undefined) {
            await runStep("app.beforeStart", app.id, app.lifecycle.beforeStart);
          }
        }

        for (const resource of resources) {
          if (resource.start !== undefined) {
            await runStep("resource.start", resource.name, resource.start);
          }
        }

        for (const app of apps) {
          if (app.lifecycle?.afterStart !== undefined) {
            await runStep("app.afterStart", app.id, app.lifecycle.afterStart);
          }
        }

        state = "ready";
        return { ok: true, value: undefined };
      } catch (error) {
        state = "failed";
        return runtimeFailure("PLATFORM_RUNTIME_LIFECYCLE_FAILED", "Runtime startup lifecycle failed.", { state: "starting" }, error);
      }
    },
    async shutdown() {
      if (state === "created") {
        state = "stopped";
        return { ok: true, value: [...events] };
      }

      if (state === "stopped") {
        return { ok: true, value: [...events] };
      }

      if (state !== "ready" && state !== "failed") {
        return runtimeFailure("PLATFORM_RUNTIME_INVALID_STATE", "Runtime lifecycle cannot shut down from the current state.", { state });
      }

      state = "stopping";

      try {
        for (const app of apps) {
          if (app.lifecycle?.beforeStop !== undefined) {
            await runStep("app.beforeStop", app.id, app.lifecycle.beforeStop);
          }
        }

        for (const resource of resources) {
          if (resource.drain !== undefined) {
            await runStep("resource.drain", resource.name, resource.drain);
          }
        }

        for (const resource of [...resources].reverse()) {
          if (resource.close !== undefined) {
            await runStep("resource.close", resource.name, resource.close);
          }
        }

        for (const sink of telemetry) {
          await runStep("telemetry.flush", sink.name, sink.flush);
        }

        for (const app of apps) {
          if (app.lifecycle?.afterStop !== undefined) {
            await runStep("app.afterStop", app.id, app.lifecycle.afterStop);
          }
        }

        state = "stopped";
        return { ok: true, value: [...events] };
      } catch (error) {
        state = "failed";
        return runtimeFailure("PLATFORM_RUNTIME_LIFECYCLE_FAILED", "Runtime shutdown lifecycle failed.", { state: "stopping" }, error);
      }
    },
  };
}

function contractSuccess(): Result<void, PlatformContractError> {
  return { ok: true, value: undefined };
}

function routeKey(route: PlatformRouteRegistration): string {
  return `${route.method} ${route.path}`;
}

function mountFailure(
  code: PlatformRuntimeMountFailure["code"],
  contractErrors: readonly PlatformContractError[],
  details?: Readonly<Record<string, JsonValue>>,
  cause?: unknown,
): Result<never, PlatformRuntimeMountFailure> {
  return {
    ok: false,
    error: {
      code,
      defaultMessage: code === "PLATFORM_RUNTIME_REGISTRY_INVALID"
        ? "Platform runtime registry failed validation."
        : "Platform app failed during runtime mount.",
      contractErrors: [...contractErrors],
      ...(details === undefined ? {} : { details }),
      ...(cause === undefined ? {} : { cause }),
    },
  };
}

function runtimeFailure(
  code: PlatformRuntimeErrorCode,
  defaultMessage: string,
  details?: Readonly<Record<string, JsonValue>>,
  cause?: unknown,
): Result<never, PlatformRuntimeError> {
  return {
    ok: false,
    error: {
      code,
      defaultMessage,
      ...(details === undefined ? {} : { details }),
      ...(cause === undefined ? {} : { cause }),
    },
  };
}

const defaultPlatformRuntimeDateTime = "2026-07-10T00:00:00.000Z";
