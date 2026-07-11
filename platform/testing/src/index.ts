import { recordConfigSource, type ConfigRecord, type ConfigSchema, type ConfigSource } from "@kanbien/core/config";
import { defaultSensitiveLogFieldNames, type LogRecord, type Logger } from "@kanbien/core/logging";
import type { HealthCheckResult, MetricPoint, Metrics } from "@kanbien/core/monitoring";
import type { QueueMessage, QueueMessageType, QueueMessageVersion } from "@kanbien/core/queues";
import { fixedClock, type Clock, type CorrelationId, type ISODateTime, type JsonValue, type Result } from "@kanbien/core/shared";
import type { Validator } from "@kanbien/core/validation";
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

export type PlatformTestErrorCode =
  | "PLATFORM_TEST_MOUNT_FAILED"
  | "PLATFORM_TEST_INVALID_CONFIG"
  | "PLATFORM_TEST_UNSAFE_HEALTH_OUTPUT";

export interface PlatformTestError {
  readonly code: PlatformTestErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
}

export interface PlatformTestMountFailure extends PlatformTestError {
  readonly code: "PLATFORM_TEST_MOUNT_FAILED";
  readonly contractErrors: readonly PlatformContractError[];
}

export interface PlatformTestLogger extends Logger {
  records(): readonly LogRecord[];
}

export interface PlatformTestMetrics extends Metrics {
  points(): readonly MetricPoint[];
}

export interface PlatformTestRegistry extends PlatformAppRegistry {
  permissions(): readonly PlatformPermissionDeclaration[];
  routes(): readonly PlatformRouteRegistration[];
  jobs(): readonly PlatformJobRegistration[];
  healthChecks(): readonly PlatformHealthRegistration[];
  configSchemas(): readonly ConfigSchema<unknown>[];
  errors(): readonly PlatformContractError[];
  validate(): readonly PlatformContractError[];
}

export interface PlatformTestRegistryOptions {
  readonly reservedPaths?: readonly string[];
}

export interface PlatformTestMountOptions extends PlatformTestRegistryOptions {
  readonly deps?: PlatformMountDeps;
}

export interface PlatformTestMountResult {
  readonly app: PlatformApp;
  readonly deps: PlatformMountDeps;
  readonly registry: PlatformTestRegistry;
  readonly permissions: readonly PlatformPermissionDeclaration[];
  readonly routes: readonly PlatformRouteRegistration[];
  readonly jobs: readonly PlatformJobRegistration[];
  readonly healthChecks: readonly PlatformHealthRegistration[];
  readonly configSchemas: readonly ConfigSchema<unknown>[];
  readonly lifecycle: PlatformApp["lifecycle"];
}

export interface PlatformTestRequestContextInput {
  readonly requestId?: CorrelationId;
  readonly correlationId?: CorrelationId;
  readonly now?: ISODateTime;
  readonly method?: PlatformRequestContext["method"];
  readonly path?: string;
  readonly logger?: Logger;
  readonly metrics?: Metrics;
  readonly config?: ConfigSource;
  readonly flags?: FeatureFlagReader;
  readonly clock?: Clock;
  readonly abortSignal?: AbortSignal;
}

export interface PlatformTestJobContextInput {
  readonly jobName: PlatformJobName;
  readonly message: QueueMessage;
  readonly correlationId?: CorrelationId;
  readonly now?: ISODateTime;
  readonly logger?: Logger;
  readonly metrics?: Metrics;
  readonly config?: ConfigSource;
  readonly flags?: FeatureFlagReader;
  readonly clock?: Clock;
  readonly abortSignal?: AbortSignal;
}

export interface PlatformTestQueueMessageInput<TPayload extends JsonValue = Readonly<Record<string, JsonValue>>> {
  readonly id?: string;
  readonly type: QueueMessageType;
  readonly version?: QueueMessageVersion;
  readonly enqueuedAt?: ISODateTime;
  readonly payload?: TPayload;
}

export function createPlatformTestLogger(): PlatformTestLogger {
  const records: LogRecord[] = [];

  return {
    write: (record) => {
      records.push(record);
    },
    records: () => [...records],
  };
}

export function createPlatformTestMetrics(): PlatformTestMetrics {
  const points: MetricPoint[] = [];

  return {
    record: (point) => {
      points.push(point);
    },
    points: () => [...points],
  };
}

export function createPlatformTestConfigSource(values: ConfigRecord = {}): ConfigSource {
  return recordConfigSource(values);
}

export function createPlatformTestMountDeps(input: Partial<PlatformMountDeps> = {}): PlatformMountDeps {
  return {
    logger: input.logger ?? createPlatformTestLogger(),
    metrics: input.metrics ?? createPlatformTestMetrics(),
    config: input.config ?? createPlatformTestConfigSource(),
    flags: input.flags ?? fixedFeatureFlagReader({}),
    clock: input.clock ?? fixedClock(new Date(defaultPlatformTestDateTime)),
    ...(input.events === undefined ? {} : { events: input.events }),
    ...(input.audit === undefined ? {} : { audit: input.audit }),
    ...(input.authorizer === undefined ? {} : { authorizer: input.authorizer }),
    ...(input.authenticator === undefined ? {} : { authenticator: input.authenticator }),
  };
}

export function createPlatformTestRegistry(options: PlatformTestRegistryOptions = {}): PlatformTestRegistry {
  const reservedPaths = options.reservedPaths ?? defaultReservedPlatformRoutePaths;
  const permissions: PlatformPermissionDeclaration[] = [];
  const routes: PlatformRouteRegistration[] = [];
  const jobs: PlatformJobRegistration[] = [];
  const healthChecks: PlatformHealthRegistration[] = [];
  const configSchemas: ConfigSchema<unknown>[] = [];
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
    registerConfigSchema(schema) {
      configSchemas.push(schema as ConfigSchema<unknown>);
      return contractSuccess();
    },
    permissions: () => permissions.map((permission) => ({ ...permission })),
    routes: () => [...routes],
    jobs: () => [...jobs],
    healthChecks: () => [...healthChecks],
    configSchemas: () => [...configSchemas],
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

export async function mountPlatformAppForTest(
  app: PlatformApp,
  options: PlatformTestMountOptions = {},
): Promise<Result<PlatformTestMountResult, PlatformTestMountFailure>> {
  const registry = createPlatformTestRegistry(options);
  const deps = options.deps ?? createPlatformTestMountDeps();
  const appId = platformAppId(String(app.id));

  if (!appId.ok) {
    return mountFailure([appId.error]);
  }

  try {
    await app.mount(registry, deps);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown app mount failure.";
    return mountFailure(registry.errors(), { reason: message });
  }

  const contractErrors = registry.validate();
  if (contractErrors.length > 0) {
    return mountFailure(contractErrors);
  }

  return {
    ok: true,
    value: {
      app,
      deps,
      registry,
      permissions: registry.permissions(),
      routes: registry.routes(),
      jobs: registry.jobs(),
      healthChecks: registry.healthChecks(),
      configSchemas: registry.configSchemas(),
      lifecycle: app.lifecycle,
    },
  };
}

export function createPlatformTestRequestContext(input: PlatformTestRequestContextInput = {}): PlatformRequestContext {
  const correlationId = input.correlationId ?? defaultCorrelationId;
  const clock = input.clock ?? fixedClock(new Date(defaultPlatformTestDateTime));

  return {
    requestId: input.requestId ?? correlationId,
    correlationId,
    now: input.now ?? defaultNow,
    logger: input.logger ?? createPlatformTestLogger(),
    metrics: input.metrics ?? createPlatformTestMetrics(),
    config: input.config ?? createPlatformTestConfigSource(),
    flags: input.flags ?? fixedFeatureFlagReader({}),
    clock,
    method: input.method ?? "GET",
    path: input.path ?? "/test",
    ...(input.abortSignal === undefined ? {} : { abortSignal: input.abortSignal }),
  };
}

export function createPlatformTestQueueMessage<TPayload extends JsonValue = Readonly<Record<string, JsonValue>>>(
  input: PlatformTestQueueMessageInput<TPayload>,
): QueueMessage<TPayload> {
  return {
    id: (input.id ?? "queue-message-test") as QueueMessage<TPayload>["id"],
    type: input.type,
    version: input.version ?? (1 as QueueMessageVersion),
    enqueuedAt: input.enqueuedAt ?? defaultNow,
    payload: input.payload ?? ({} as TPayload),
  };
}

export function createPlatformTestJobContext(input: PlatformTestJobContextInput): PlatformJobContext {
  const clock = input.clock ?? fixedClock(new Date(defaultPlatformTestDateTime));

  return {
    jobName: input.jobName,
    message: input.message,
    correlationId: input.correlationId ?? defaultCorrelationId,
    now: input.now ?? defaultNow,
    logger: input.logger ?? createPlatformTestLogger(),
    metrics: input.metrics ?? createPlatformTestMetrics(),
    config: input.config ?? createPlatformTestConfigSource(),
    flags: input.flags ?? fixedFeatureFlagReader({}),
    clock,
    ...(input.abortSignal === undefined ? {} : { abortSignal: input.abortSignal }),
  };
}

export function validatePlatformTestConfigSchemas(
  schemas: readonly ConfigSchema<unknown>[],
  source: ConfigSource = createPlatformTestConfigSource(),
): Result<readonly unknown[], PlatformTestError> {
  const parsedValues: unknown[] = [];

  for (const [schemaIndex, schema] of schemas.entries()) {
    const parsed = schema.parse(source);
    if (!parsed.ok) {
      return {
        ok: false,
        error: {
          code: "PLATFORM_TEST_INVALID_CONFIG",
          defaultMessage: "A platform test config schema rejected the supplied config source.",
          details: { schemaIndex, configCode: parsed.error.code },
        },
      };
    }

    parsedValues.push(parsed.value);
  }

  return { ok: true, value: parsedValues };
}

export async function runPlatformTestHealthChecks(
  healthChecks: readonly PlatformHealthRegistration[],
): Promise<Result<readonly HealthCheckResult[], PlatformTestError>> {
  const results: HealthCheckResult[] = [];

  for (const healthCheck of healthChecks) {
    const result = await healthCheck.check.check();
    const unsafePath = firstUnsafeMetadataPath(result.metadata);
    if (unsafePath !== undefined) {
      return {
        ok: false,
        error: {
          code: "PLATFORM_TEST_UNSAFE_HEALTH_OUTPUT",
          defaultMessage: "Health check metadata contains a sensitive field name.",
          details: { healthCheck: String(healthCheck.name), path: unsafePath },
        },
      };
    }

    results.push(result);
  }

  return { ok: true, value: results };
}

export function validatorForTest<TValue>(isValue: (value: unknown) => value is TValue): Validator<TValue> {
  return {
    validate: isValue,
    explain: (value) =>
      isValue(value)
        ? { valid: true, issues: [] }
        : {
            valid: false,
            issues: [
              {
                path: [],
                code: "PLATFORM_TEST_VALIDATION_FAILED",
                defaultMessage: "Value failed the platform test validator.",
              },
            ],
          },
  };
}

function mountFailure(
  contractErrors: readonly PlatformContractError[],
  details?: Readonly<Record<string, JsonValue>>,
): Result<never, PlatformTestMountFailure> {
  return {
    ok: false,
    error: {
      code: "PLATFORM_TEST_MOUNT_FAILED",
      defaultMessage: "Platform app failed to mount in the test registry.",
      contractErrors: [...contractErrors],
      ...(details === undefined ? {} : { details }),
    },
  };
}

function contractSuccess(): Result<void, PlatformContractError> {
  return { ok: true, value: undefined };
}

function routeKey(route: PlatformRouteRegistration): string {
  return `${route.method} ${route.path}`;
}

function firstUnsafeMetadataPath(value: unknown, path: readonly string[] = []): string | undefined {
  if (!isRecord(value)) {
    return undefined;
  }

  for (const [key, nestedValue] of Object.entries(value)) {
    const nestedPath = [...path, key];
    if (unsafeHealthMetadataKeys.has(normalizeKey(key))) {
      return nestedPath.join(".");
    }

    const nestedUnsafePath = firstUnsafeMetadataPath(nestedValue, nestedPath);
    if (nestedUnsafePath !== undefined) {
      return nestedUnsafePath;
    }
  }

  return undefined;
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null;
}

function normalizeKey(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

const defaultPlatformTestDateTime = "2026-07-10T00:00:00.000Z";
const defaultNow = defaultPlatformTestDateTime as ISODateTime;
const defaultCorrelationId = "platform-test-correlation" as CorrelationId;
const unsafeHealthMetadataKeys = new Set(
  [...defaultSensitiveLogFieldNames, "connectionString"].map((key) => normalizeKey(key)),
);
