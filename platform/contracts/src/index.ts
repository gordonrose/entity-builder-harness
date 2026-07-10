import type { AuditRecorder } from "@kanbien/core/audit";
import type { Authenticator, Principal } from "@kanbien/core/authn";
import type { Authorizer, Permission } from "@kanbien/core/authz";
import type { ConfigSchema, ConfigSource } from "@kanbien/core/config";
import type { EventBus } from "@kanbien/core/events";
import type { LocaleTag } from "@kanbien/core/i18n";
import type { Logger } from "@kanbien/core/logging";
import type { HealthCheck, Metrics } from "@kanbien/core/monitoring";
import type { QueueDelivery, QueueMessage, QueueMessageType } from "@kanbien/core/queues";
import type {
  Brand,
  Clock,
  CorrelationId,
  CausationId,
  ISODateTime,
  JsonValue,
  Result,
} from "@kanbien/core/shared";
import type { TenantContext } from "@kanbien/core/tenancy";
import type { Validator } from "@kanbien/core/validation";

export type PlatformAppId = Brand<string, "PlatformAppId">;
export type PlatformRouteName = Brand<string, "PlatformRouteName">;
export type PlatformJobName = Brand<string, "PlatformJobName">;
export type PlatformHealthName = Brand<string, "PlatformHealthName">;
export type PlatformApiVersion = Brand<string, "PlatformApiVersion">;
export type FeatureFlagName = Brand<string, "FeatureFlagName">;

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
export type PlatformRegistrationKind = "app" | "route" | "permission" | "job" | "health" | "config";
export type PlatformContractErrorCode =
  | "PLATFORM_CONTRACT_INVALID_NAME"
  | "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION"
  | "PLATFORM_CONTRACT_RESERVED_PATH"
  | "PLATFORM_CONTRACT_UNKNOWN_PERMISSION"
  | "PLATFORM_CONTRACT_MALFORMED_PERMISSION"
  | "PLATFORM_CONTRACT_MALFORMED_ROUTE"
  | "PLATFORM_CONTRACT_MALFORMED_JOB";

export interface PlatformContractError {
  readonly code: PlatformContractErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
}

export const defaultReservedPlatformRoutePaths: readonly string[] = ["/", "/livez", "/readyz", "/health", "/metrics", "/admin"];

export interface FeatureFlagContext {
  readonly tenant?: TenantContext;
  readonly principal?: Principal;
  readonly correlationId?: CorrelationId;
  readonly facts?: Readonly<Record<string, JsonValue>>;
}

export interface FeatureFlagReader {
  isEnabled(name: FeatureFlagName, context?: FeatureFlagContext): Promise<boolean> | boolean;
}

export interface PlatformRuntimeContext {
  readonly correlationId: CorrelationId;
  readonly causationId?: CausationId;
  readonly now: ISODateTime;
  readonly tenant?: TenantContext;
  readonly principal?: Principal;
  readonly locale?: LocaleTag;
  readonly logger: Logger;
  readonly metrics: Metrics;
  readonly config: ConfigSource;
  readonly flags: FeatureFlagReader;
  readonly clock: Clock;
  readonly abortSignal?: AbortSignal;
}

export interface PlatformRequestContext extends PlatformRuntimeContext {
  readonly requestId: CorrelationId;
  readonly method: HttpMethod;
  readonly path: string;
}

export interface PlatformJobContext extends PlatformRuntimeContext {
  readonly jobName: PlatformJobName;
  readonly message: QueueMessage;
  readonly delivery?: QueueDelivery;
}

export type RouteAuthRequirement =
  | {
      readonly kind: "public";
    }
  | {
      readonly kind: "authenticated";
      readonly permissions?: readonly Permission[];
    };

export interface PlatformPermissionDeclaration {
  readonly permission: Permission;
  readonly description?: string;
}

export interface PlatformRequest<TBody = unknown> {
  readonly params: Readonly<Record<string, string>>;
  readonly query: Readonly<Record<string, string | readonly string[]>>;
  readonly headers: Readonly<Record<string, string | readonly string[]>>;
  readonly body?: TBody;
}

export interface PlatformResponse<TBody = unknown> {
  readonly status: number;
  readonly body?: TBody;
  readonly headers?: Readonly<Record<string, string>>;
}

export interface PlatformRouteHandler<TBody = unknown, TResponse = unknown> {
  handle(
    request: PlatformRequest<TBody>,
    context: PlatformRequestContext,
  ): Promise<PlatformResponse<TResponse>> | PlatformResponse<TResponse>;
}

export interface PlatformRouteRegistration<TBody = unknown, TResponse = unknown> {
  readonly name: PlatformRouteName;
  readonly method: HttpMethod;
  readonly path: string;
  readonly apiVersion?: PlatformApiVersion;
  readonly auth: RouteAuthRequirement;
  readonly validator?: Validator<TBody>;
  readonly handler: PlatformRouteHandler<TBody, TResponse>;
}

export interface PlatformJobHandler<TMessage extends QueueMessage = QueueMessage> {
  handle(message: TMessage, context: PlatformJobContext): Promise<void> | void;
}

export interface PlatformJobRegistration<TMessage extends QueueMessage = QueueMessage> {
  readonly name: PlatformJobName;
  readonly messageType: QueueMessageType;
  readonly validator?: Validator<TMessage["payload"]>;
  readonly handler: PlatformJobHandler<TMessage>;
}

export interface PlatformHealthRegistration {
  readonly name: PlatformHealthName;
  readonly check: HealthCheck;
}

export interface PlatformLifecycleHooks {
  beforeStart?(): Promise<void> | void;
  afterStart?(): Promise<void> | void;
  beforeStop?(): Promise<void> | void;
  afterStop?(): Promise<void> | void;
}

export interface PlatformAppRegistry {
  registerPermission(permission: PlatformPermissionDeclaration): Result<void, PlatformContractError>;
  registerRoute(route: PlatformRouteRegistration): Result<void, PlatformContractError>;
  registerJob(job: PlatformJobRegistration): Result<void, PlatformContractError>;
  registerHealthCheck(healthCheck: PlatformHealthRegistration): Result<void, PlatformContractError>;
  registerConfigSchema<TConfig>(schema: ConfigSchema<TConfig>): Result<void, PlatformContractError>;
}

export interface PlatformMountDeps {
  readonly logger: Logger;
  readonly metrics: Metrics;
  readonly config: ConfigSource;
  readonly flags: FeatureFlagReader;
  readonly clock: Clock;
  readonly events?: EventBus;
  readonly audit?: AuditRecorder;
  readonly authorizer?: Authorizer;
  readonly authenticator?: Authenticator<unknown>;
}

export interface PlatformApp {
  readonly id: PlatformAppId;
  readonly name: string;
  readonly version?: string;
  readonly lifecycle?: PlatformLifecycleHooks;
  mount(registry: PlatformAppRegistry, deps: PlatformMountDeps): Promise<void> | void;
}

export function definePlatformApp(app: PlatformApp): PlatformApp {
  return app;
}

export function platformAppId(value: string): Result<PlatformAppId, PlatformContractError> {
  return brandedName(value, "PlatformAppId", "platform app id");
}

export function platformRouteName(value: string): Result<PlatformRouteName, PlatformContractError> {
  return brandedName(value, "PlatformRouteName", "platform route name");
}

export function platformJobName(value: string): Result<PlatformJobName, PlatformContractError> {
  return brandedName(value, "PlatformJobName", "platform job name");
}

export function platformHealthName(value: string): Result<PlatformHealthName, PlatformContractError> {
  return brandedName(value, "PlatformHealthName", "platform health name");
}

export function platformApiVersion(value: string): Result<PlatformApiVersion, PlatformContractError> {
  return brandedName(value, "PlatformApiVersion", "platform api version");
}

export function featureFlagName(value: string): Result<FeatureFlagName, PlatformContractError> {
  return brandedName(value, "FeatureFlagName", "feature flag name");
}

export function fixedFeatureFlagReader(flags: Readonly<Record<string, boolean>>, defaultEnabled = false): FeatureFlagReader {
  const snapshot = { ...flags };

  return {
    isEnabled: (name) => snapshot[name] ?? defaultEnabled,
  };
}

export interface PlatformRouteValidationOptions {
  readonly declaredPermissions?: readonly Permission[];
  readonly reservedPaths?: readonly string[];
}

export function duplicatePlatformRegistration(kind: PlatformRegistrationKind, key: string): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION",
    defaultMessage: `Duplicate platform ${kind} registration.`,
    details: { kind, key },
  };
}

export function reservedPlatformPath(path: string, reservedPath: string): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_RESERVED_PATH",
    defaultMessage: "Route path uses a reserved platform path.",
    details: { path, reservedPath },
  };
}

export function unknownPlatformPermission(permission: Permission, declaredPermissions: readonly Permission[]): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_UNKNOWN_PERMISSION",
    defaultMessage: "Route references a permission that has not been declared.",
    details: { permission, declaredPermissions: [...declaredPermissions] },
  };
}

export function malformedPlatformPermission(reason: string, details?: Readonly<Record<string, JsonValue>>): PlatformContractError {
  return platformContractError("PLATFORM_CONTRACT_MALFORMED_PERMISSION", reason, details);
}

export function malformedPlatformRoute(reason: string, details?: Readonly<Record<string, JsonValue>>): PlatformContractError {
  return platformContractError("PLATFORM_CONTRACT_MALFORMED_ROUTE", reason, details);
}

export function malformedPlatformJob(reason: string, details?: Readonly<Record<string, JsonValue>>): PlatformContractError {
  return platformContractError("PLATFORM_CONTRACT_MALFORMED_JOB", reason, details);
}

export function validatePlatformPermissionDeclaration(
  declaration: PlatformPermissionDeclaration,
): Result<void, PlatformContractError> {
  if (!isRecord(declaration)) {
    return contractFailure(malformedPlatformPermission("Permission declaration must be an object."));
  }

  const declaredPermission = declaration["permission"];
  if (!isPermission(declaredPermission)) {
    return contractFailure(
      malformedPlatformPermission("Permission declarations must use core resource:action permission strings.", {
        permission: stringifyDetail(declaredPermission),
      }),
    );
  }

  return contractSuccess();
}

export function validatePlatformRouteRegistration(
  route: PlatformRouteRegistration,
  options: PlatformRouteValidationOptions = {},
): Result<void, PlatformContractError> {
  if (!isRecord(route)) {
    return contractFailure(malformedPlatformRoute("Route registration must be an object."));
  }

  const routeName = route["name"];
  if (!isContractName(routeName)) {
    return contractFailure(invalidContractName("platform route name", routeName));
  }

  const method = route["method"];
  if (!isHttpMethod(method)) {
    return contractFailure(malformedPlatformRoute("Route method must be a supported HTTP method.", { method: stringifyDetail(method) }));
  }

  const path = route["path"];
  if (!isRoutePath(path)) {
    return contractFailure(malformedPlatformRoute("Route path must be an absolute path without whitespace or URL scheme.", { path: stringifyDetail(path) }));
  }

  const reservedPath = findReservedPlatformRoutePath(path, options.reservedPaths ?? defaultReservedPlatformRoutePaths);
  if (reservedPath !== undefined) {
    return contractFailure(reservedPlatformPath(path, reservedPath));
  }

  const auth = route["auth"];
  if (!isRouteAuthRequirement(auth)) {
    return contractFailure(malformedPlatformRoute("Route auth requirement must be public or authenticated."));
  }

  if (auth.kind === "authenticated") {
    const routePermissions = auth.permissions ?? [];
    for (const routePermission of routePermissions) {
      if (!isPermission(routePermission)) {
        return contractFailure(
          malformedPlatformRoute("Route permissions must use core resource:action permission strings.", {
            permission: stringifyDetail(routePermission),
          }),
        );
      }

      if (options.declaredPermissions !== undefined && !options.declaredPermissions.includes(routePermission)) {
        return contractFailure(unknownPlatformPermission(routePermission, options.declaredPermissions));
      }
    }
  }

  const validator = route["validator"];
  if (validator !== undefined && !isValidator(validator)) {
    return contractFailure(malformedPlatformRoute("Route validator must implement the core Validator contract."));
  }

  if (!isHandler(route["handler"])) {
    return contractFailure(malformedPlatformRoute("Route handler must expose a handle function."));
  }

  return contractSuccess();
}

export function validatePlatformJobRegistration(job: PlatformJobRegistration): Result<void, PlatformContractError> {
  if (!isRecord(job)) {
    return contractFailure(malformedPlatformJob("Job registration must be an object."));
  }

  const jobName = job["name"];
  if (!isContractName(jobName)) {
    return contractFailure(invalidContractName("platform job name", jobName));
  }

  const messageType = job["messageType"];
  if (!isContractName(messageType)) {
    return contractFailure(
      malformedPlatformJob("Job message type must use dot-separated lowercase segments.", {
        messageType: stringifyDetail(messageType),
      }),
    );
  }

  const validator = job["validator"];
  if (validator !== undefined && !isValidator(validator)) {
    return contractFailure(malformedPlatformJob("Job validator must implement the core Validator contract."));
  }

  if (!isHandler(job["handler"])) {
    return contractFailure(malformedPlatformJob("Job handler must expose a handle function."));
  }

  return contractSuccess();
}

function brandedName<TName extends string>(
  value: string,
  brandName: TName,
  label: string,
): Result<Brand<string, TName>, PlatformContractError> {
  if (!contractNamePattern.test(value)) {
    return {
      ok: false,
      error: invalidContractName(label, value),
    };
  }

  return {
    ok: true,
    value: value as Brand<string, TName>,
  };
}

const contractNamePattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*$/;
const permissionPattern = /^[^\s:]+:[^\s:]+$/;
const httpMethods: readonly HttpMethod[] = ["GET", "POST", "PUT", "PATCH", "DELETE"];

function platformContractError(
  code: PlatformContractErrorCode,
  defaultMessage: string,
  details?: Readonly<Record<string, JsonValue>>,
): PlatformContractError {
  return {
    code,
    defaultMessage,
    ...(details === undefined ? {} : { details }),
  };
}

function invalidContractName(label: string, value: unknown): PlatformContractError {
  return {
    code: "PLATFORM_CONTRACT_INVALID_NAME",
    defaultMessage: `${label} must use dot-separated lowercase segments.`,
    details: { value: stringifyDetail(value) },
  };
}

function contractSuccess(): Result<void, PlatformContractError> {
  return { ok: true, value: undefined };
}

function contractFailure(error: PlatformContractError): Result<void, PlatformContractError> {
  return { ok: false, error };
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null;
}

function isContractName(value: unknown): value is string {
  return typeof value === "string" && contractNamePattern.test(value);
}

function isPermission(value: unknown): value is Permission {
  return typeof value === "string" && permissionPattern.test(value);
}

function isHttpMethod(value: unknown): value is HttpMethod {
  return typeof value === "string" && httpMethods.includes(value as HttpMethod);
}

function isRoutePath(value: unknown): value is string {
  return typeof value === "string" && value.startsWith("/") && !/\s/.test(value) && !value.includes("://");
}

function findReservedPlatformRoutePath(path: string, reservedPaths: readonly string[]): string | undefined {
  return reservedPaths.find((reservedPath) => pathMatchesReservedPath(path, reservedPath));
}

function pathMatchesReservedPath(path: string, reservedPath: string): boolean {
  if (reservedPath === "/") {
    return path === "/";
  }

  return path === reservedPath || path.startsWith(`${reservedPath}/`);
}

function isRouteAuthRequirement(value: unknown): value is RouteAuthRequirement {
  if (!isRecord(value)) {
    return false;
  }

  if (value["kind"] === "public") {
    return value["permissions"] === undefined;
  }

  if (value["kind"] !== "authenticated") {
    return false;
  }

  const permissions = value["permissions"];
  return permissions === undefined || Array.isArray(permissions);
}

function isValidator(value: unknown): value is Validator<unknown> {
  return isRecord(value) && typeof value["validate"] === "function" && typeof value["explain"] === "function";
}

function isHandler(value: unknown): value is { readonly handle: (...args: readonly unknown[]) => unknown } {
  return isRecord(value) && typeof value["handle"] === "function";
}

function stringifyDetail(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }

  return String(value);
}
