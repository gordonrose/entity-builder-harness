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
export type PlatformContractErrorCode = "PLATFORM_CONTRACT_INVALID_NAME" | "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION";

export interface PlatformContractError {
  readonly code: PlatformContractErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
}

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

function brandedName<TName extends string>(
  value: string,
  brandName: TName,
  label: string,
): Result<Brand<string, TName>, PlatformContractError> {
  if (!contractNamePattern.test(value)) {
    return {
      ok: false,
      error: {
        code: "PLATFORM_CONTRACT_INVALID_NAME",
        defaultMessage: `${label} must use dot-separated lowercase segments.`,
        details: { value },
      },
    };
  }

  return {
    ok: true,
    value: value as Brand<string, TName>,
  };
}

const contractNamePattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*$/;
