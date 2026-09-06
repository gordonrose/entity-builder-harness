import type { AuditRecorder } from "@kanbien/core/audit";
import type { Authenticator } from "@kanbien/core/authn";
import type { Authorizer, Permission } from "@kanbien/core/authz";
import type { ConfigSchema, ConfigSource } from "@kanbien/core/config";
import type { EventBus } from "@kanbien/core/events";
import type { Logger } from "@kanbien/core/logging";
import type { HealthCheck, Metrics } from "@kanbien/core/monitoring";
import type { Clock, Result } from "@kanbien/core/shared";
import type { PlatformContractError } from "./errors";
import type { FeatureFlagReader } from "./flags";
import type { PlatformAppId, PlatformHealthName } from "./identifiers";
import type { PlatformJobRegistration } from "./jobs";
import type { PlatformRouteRegistration } from "./routes";

export interface PlatformPermissionDeclaration {
  readonly permission: Permission;
  readonly description?: string;
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
