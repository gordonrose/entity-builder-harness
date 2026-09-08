import type { ConfigSchema } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";
import {
  defaultReservedPlatformRoutePaths,
  duplicatePlatformRegistration,
  platformAppId,
  platformRegistrationNamespaceMismatch,
  unknownPlatformObservabilityProfile,
  unknownPlatformPermission,
  validatePlatformCapabilityObservabilityProfile,
  validatePlatformJobRegistration,
  validatePlatformPermissionDeclaration,
  validatePlatformRouteRegistration,
  type PlatformApp,
  type PlatformAppRegistry,
  type PlatformAppId,
  type PlatformContractError,
  type PlatformHealthRegistration,
  type PlatformJobRegistration,
  type PlatformMountDeps,
  type PlatformCapabilityObservabilityProfile,
  type PlatformPermissionDeclaration,
  type PlatformRegistrationKind,
  type PlatformRouteRegistration,
} from "@kanbien/platform-contracts";
import {
  platformRuntimeMountFailure,
  type PlatformRuntimeMountFailure,
} from "./errors";

export interface PlatformRuntimeRegistry extends PlatformAppRegistry {
  forApp(appId: PlatformAppId): PlatformAppRegistry;
  permissions(): readonly PlatformPermissionDeclaration[];
  routes(): readonly PlatformRouteRegistration[];
  jobs(): readonly PlatformJobRegistration[];
  observabilityProfiles(): readonly PlatformCapabilityObservabilityProfile[];
  healthChecks(): readonly PlatformHealthRegistration[];
  configSchemas(): readonly ConfigSchema<unknown>[];
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
  readonly observabilityProfiles: readonly PlatformCapabilityObservabilityProfile[];
  readonly healthChecks: readonly PlatformHealthRegistration[];
  readonly configSchemas: readonly ConfigSchema<unknown>[];
}

export function createPlatformRuntimeRegistry(options: PlatformRuntimeRegistryOptions = {}): PlatformRuntimeRegistry {
  const reservedPaths = options.reservedPaths ?? defaultReservedPlatformRoutePaths;
  const permissions: PlatformPermissionDeclaration[] = [];
  const routes: PlatformRouteRegistration[] = [];
  const jobs: PlatformJobRegistration[] = [];
  const observabilityProfiles: PlatformCapabilityObservabilityProfile[] = [];
  const healthChecks: PlatformHealthRegistration[] = [];
  const configSchemas: ConfigSchema<unknown>[] = [];
  const errors: PlatformContractError[] = [];

  function track(error: PlatformContractError): Result<void, PlatformContractError> {
    errors.push(error);
    return { ok: false, error };
  }

  const registry: PlatformRuntimeRegistry = {
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
    registerObservabilityProfile(profile) {
      const validation = validatePlatformCapabilityObservabilityProfile(profile);
      if (!validation.ok) {
        return track(validation.error);
      }

      if (observabilityProfiles.some((registered) => registered.name === profile.name)) {
        return track(duplicatePlatformRegistration("observability-profile", String(profile.name)));
      }

      observabilityProfiles.push({
        ...profile,
        signals: [...profile.signals],
        ...(profile.logFieldNames === undefined ? {} : { logFieldNames: [...profile.logFieldNames] }),
        ...(profile.metricDimensionFieldNames === undefined ? {} : { metricDimensionFieldNames: [...profile.metricDimensionFieldNames] }),
        ...(profile.traceAttributeNames === undefined ? {} : { traceAttributeNames: [...profile.traceAttributeNames] }),
        ...(profile.nfrObjectives === undefined ? {} : { nfrObjectives: profile.nfrObjectives.map((objective) => ({ ...objective })) }),
      });
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
    forApp(appId) {
      return {
        registerPermission(permissionDeclaration) {
          return registerInAppNamespace(appId, "permission", permissionDeclaration.permission, () =>
            registry.registerPermission(permissionDeclaration));
        },
        registerRoute(route) {
          return registerInAppNamespace(appId, "route", String(route.name), () => registry.registerRoute(route));
        },
        registerJob(job) {
          return registerInAppNamespace(appId, "job", String(job.name), () => registry.registerJob(job));
        },
        registerObservabilityProfile(profile) {
          return registerInAppNamespace(appId, "observability-profile", String(profile.name), () =>
            registry.registerObservabilityProfile(profile));
        },
        registerHealthCheck(healthCheck) {
          return registerInAppNamespace(appId, "health", String(healthCheck.name), () =>
            registry.registerHealthCheck(healthCheck));
        },
        registerConfigSchema(schema) {
          return registry.registerConfigSchema(schema);
        },
      };
    },
    permissions: () => permissions.map((permission) => ({ ...permission })),
    routes: () => [...routes],
    jobs: () => [...jobs],
    observabilityProfiles: () => observabilityProfiles.map((profile) => ({
      ...profile,
      signals: [...profile.signals],
      ...(profile.logFieldNames === undefined ? {} : { logFieldNames: [...profile.logFieldNames] }),
      ...(profile.metricDimensionFieldNames === undefined ? {} : { metricDimensionFieldNames: [...profile.metricDimensionFieldNames] }),
      ...(profile.traceAttributeNames === undefined ? {} : { traceAttributeNames: [...profile.traceAttributeNames] }),
      ...(profile.nfrObjectives === undefined ? {} : { nfrObjectives: profile.nfrObjectives.map((objective) => ({ ...objective })) }),
    })),
    healthChecks: () => [...healthChecks],
    configSchemas: () => [...configSchemas],
    errors: () => [...errors],
    validate() {
      const validationErrors = [...errors];
      const declaredPermissions = permissions.map((permission) => permission.permission);
      const declaredObservabilityProfiles = observabilityProfiles.map((profile) => String(profile.name));

      for (const route of routes) {
        if (route.auth.kind !== "authenticated") {
          continue;
        }

        for (const permission of route.auth.permissions ?? []) {
          if (!declaredPermissions.includes(permission)) {
            validationErrors.push(unknownPlatformPermission(permission, declaredPermissions));
          }
        }

        if (
          route.resourceAuthorization !== undefined
          && !declaredPermissions.includes(route.resourceAuthorization.permission)
        ) {
          validationErrors.push(unknownPlatformPermission(route.resourceAuthorization.permission, declaredPermissions));
        }
      }

      for (const registration of [...routes, ...jobs]) {
        if (registration.observability.kind !== "profile") {
          continue;
        }

        if (!declaredObservabilityProfiles.includes(String(registration.observability.profile))) {
          validationErrors.push(
            unknownPlatformObservabilityProfile(String(registration.observability.profile), declaredObservabilityProfiles),
          );
        }
      }

      return validationErrors;
    },
  };

  function registerInAppNamespace(
    appId: PlatformAppId,
    kind: PlatformRegistrationKind,
    name: string,
    register: () => Result<void, PlatformContractError>,
  ): Result<void, PlatformContractError> {
    if (!name.startsWith(`${appId}.`)) {
      return track(platformRegistrationNamespaceMismatch(kind, appId, name));
    }

    return register();
  }

  return registry;
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
      await app.mount(registry.forApp(appId.value), input.deps);
      mountedApps.push(app);
    } catch (error) {
      return platformRuntimeMountFailure("PLATFORM_RUNTIME_APP_MOUNT_FAILED", registry.errors(), { appId: app.id }, error);
    }
  }

  contractErrors.push(...registry.validate());
  if (contractErrors.length > 0) {
    return platformRuntimeMountFailure("PLATFORM_RUNTIME_REGISTRY_INVALID", contractErrors);
  }

  return {
    ok: true,
    value: {
      apps: mountedApps,
      registry,
      permissions: registry.permissions(),
      routes: registry.routes(),
      jobs: registry.jobs(),
      observabilityProfiles: registry.observabilityProfiles(),
      healthChecks: registry.healthChecks(),
      configSchemas: registry.configSchemas(),
    },
  };
}

function contractSuccess(): Result<void, PlatformContractError> {
  return { ok: true, value: undefined };
}

function routeKey(route: PlatformRouteRegistration): string {
  return `${route.method} ${route.path}`;
}
