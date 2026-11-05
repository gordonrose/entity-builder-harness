import { runtimeBoundaryEvidence, type PlatformRuntimeDiagnosticOptions, type RuntimeBoundaryDetail } from "./diagnostics";
import type { ConfigSchema } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";
import { validatePlatformDiagnosticCatalog, type PlatformDiagnosticCatalog } from "@kanbien/platform-contracts";
import { inspectPlatformErrorClassDeclaration, malformedPlatformObservabilityProfile, platformContractClassificationDiagnosticRecord } from "@kanbien/platform-contracts";
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
  diagnosticCatalogs(): readonly PlatformDiagnosticCatalog[];
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

export interface PlatformRuntimeMountInput extends PlatformRuntimeDiagnosticOptions {
  readonly apps: readonly PlatformApp[];
  readonly deps: PlatformMountDeps;
  readonly registryOptions?: PlatformRuntimeRegistryOptions;
}

export interface PlatformRuntimeMountResult {
  readonly diagnosticCatalogs: readonly PlatformDiagnosticCatalog[];
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
  const diagnosticCatalogs: PlatformDiagnosticCatalog[] = [];
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
    registerDiagnosticCatalog(catalog) {
      const checked = validatePlatformDiagnosticCatalog(catalog, diagnosticCatalogs);
      if (!checked.ok) return track(checked.error);
      diagnosticCatalogs.push(checked.value);
      return contractSuccess();
    },
    registerPermission(permissionDeclaration) {
      const validation = validatePlatformPermissionDeclaration(permissionDeclaration);
      if (!validation.ok) {
        return track(validation.error);
      }

      if (permissions.some((registered) => registered.permission === permissionDeclaration.permission)) {
        return track(duplicatePlatformRegistration("permission", permissionDeclaration.permission, "duplicate-permission"));
      }

      permissions.push({ ...permissionDeclaration });
      return contractSuccess();
    },
    registerRoute(route) {
      const validation = validatePlatformRouteRegistration(route, { reservedPaths });
      if (!validation.ok) {
        return track(validation.error);
      }

      let dimension: "duplicate-name" | "duplicate-route-key" = "duplicate-name";
      if (routes.some((registered) => registered.name === route.name || (routeKey(registered) === routeKey(route) && (dimension = "duplicate-route-key", true)))) {
        return track(duplicatePlatformRegistration("route", routeKey(route), dimension));
      }

      routes.push(route);
      return contractSuccess();
    },
    registerJob(job) {
      const validation = validatePlatformJobRegistration(job);
      if (!validation.ok) {
        return track(validation.error);
      }

      let dimension: "duplicate-name" | "duplicate-message-type" = "duplicate-name";
      if (jobs.some((registered) => registered.name === job.name || (registered.messageType === job.messageType && (dimension = "duplicate-message-type", true)))) {
        return track(duplicatePlatformRegistration("job", String(job.name), dimension));
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
        return track(duplicatePlatformRegistration("observability-profile", String(profile.name), "duplicate-name"));
      }

      const classes = inspectPlatformErrorClassDeclaration(profile);
      if (classes.issue !== undefined) return track({ ...malformedPlatformObservabilityProfile("Observability profile error classes must be distinct bounded data declarations."),
        diagnosticRecord: platformContractClassificationDiagnosticRecord(classes.issue) });
      const snapshot = {
        ...profile,
        signals: [...profile.signals],
        ...(profile.logFieldNames === undefined ? {} : { logFieldNames: [...profile.logFieldNames] }),
        ...(profile.metricDimensionFieldNames === undefined ? {} : { metricDimensionFieldNames: [...profile.metricDimensionFieldNames] }),
        ...(profile.traceAttributeNames === undefined ? {} : { traceAttributeNames: [...profile.traceAttributeNames] }),
        ...(profile.nfrObjectives === undefined ? {} : { nfrObjectives: profile.nfrObjectives.map((objective) => ({ ...objective })) }),
      };
      // Never retain a raw value copied by spread when the descriptor snapshot is absent.
      delete snapshot.errorClasses;
      if (classes.values !== undefined) snapshot.errorClasses = classes.values;
      observabilityProfiles.push(snapshot);
      return contractSuccess();
    },
    registerHealthCheck(healthCheck) {
      if (healthChecks.some((registered) => registered.name === healthCheck.name)) {
        return track(duplicatePlatformRegistration("health", String(healthCheck.name), "duplicate-name"));
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
        registerDiagnosticCatalog(catalog) {
          return registerInAppNamespace(appId, "diagnostic-catalog", `${catalog.owner}.catalog`, () => registry.registerDiagnosticCatalog(catalog));
        },
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
    diagnosticCatalogs: () => JSON.parse(JSON.stringify(diagnosticCatalogs)) as PlatformDiagnosticCatalog[],
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
          validationErrors.push(unknownPlatformPermission(route.resourceAuthorization.permission, declaredPermissions, "resourceAuthorization.permission"));
        }
      }

      for (const [kind, registration] of [...routes.map((route) => ["route", route] as const), ...jobs.map((job) => ["job", job] as const)]) {
        if (registration.observability.kind !== "profile") {
          continue;
        }

        if (!declaredObservabilityProfiles.includes(String(registration.observability.profile))) {
          validationErrors.push(
            unknownPlatformObservabilityProfile(String(registration.observability.profile), declaredObservabilityProfiles, kind),
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
  let registry: PlatformRuntimeRegistry | undefined;
  let tracking: RuntimeBoundaryDetail = { operation: "mount", phase: "registry-construction", subject: "runtime", boundary: "selection", effect: "boundary-outcome-unknown" };
  let pendingFailure: { detail: RuntimeBoundaryDetail; cause: unknown } | undefined;
  const catalogs = (): readonly PlatformDiagnosticCatalog[] => {
    try { return registry?.diagnosticCatalogs() ?? []; } catch { return []; }
  };
  try {
    registry = createPlatformRuntimeRegistry(input.registryOptions);
    const appIds = new Set<string>();
    const mountedApps: PlatformApp[] = [];
    const contractErrors: PlatformContractError[] = [];
    let ordinal = 0;
    tracking = { operation: "mount", phase: "app-iteration", subject: "app", boundary: "iteration", effect: "boundary-outcome-unknown" };
    for (const app of input.apps) {
      const position = ordinal++;
      tracking = { operation: "mount", phase: "app-identity", subject: "app", boundary: "selection", effect: "step-not-invoked", ordinal: position };
      const appId = platformAppId(String(app.id));
      if (!appId.ok) {
        contractErrors.push(appId.error);
        tracking = { operation: "mount", phase: "app-iteration", subject: "app", boundary: "iteration", effect: "boundary-outcome-unknown" };
        continue;
      }
      tracking = { ...tracking, phase: "app-uniqueness" };
      if (appIds.has(app.id)) {
        contractErrors.push(duplicatePlatformRegistration("app", app.id, "duplicate-name"));
        tracking = { operation: "mount", phase: "app-iteration", subject: "app", boundary: "iteration", effect: "boundary-outcome-unknown" };
        continue;
      }
      appIds.add(app.id);
      tracking = { operation: "mount", phase: "app-mount", subject: "app", boundary: "selection", effect: "step-not-invoked", ordinal: position };
      try {
        let deps: PlatformMountDeps;
        let completion: Promise<void> | void;
        await (completion = app.mount(registry.forApp(appId.value), (
          deps = input.deps, tracking = { ...tracking, boundary: "invocation", effect: "step-completion-unobserved" }, deps
        )), tracking = { ...tracking, boundary: "completion" }, completion);
        tracking = { ...tracking, boundary: "projection", effect: "mount-completed-result-not-returned" };
        mountedApps.push(app);
      } catch (error) {
        pendingFailure = { detail: tracking, cause: error };
        tracking = { ...tracking, phase: "mount-error-projection", boundary: "projection", effect: "boundary-outcome-unknown" };
        const failure = platformRuntimeMountFailure("PLATFORM_RUNTIME_APP_MOUNT_FAILED", registry.errors(), { appId: app.id }, error);
        const evidence = runtimeBoundaryEvidence(input, pendingFailure.detail, error, catalogs());
        if (failure.ok) return failure;
        return { ok: false, error: { ...failure.error, ...evidence } };
      }
      tracking = { operation: "mount", phase: "app-iteration", subject: "app", boundary: "iteration", effect: "boundary-outcome-unknown" };
    }
    tracking = { operation: "mount", phase: "registry-validation", subject: "runtime", boundary: "invocation", effect: "boundary-outcome-unknown" };
    contractErrors.push(...registry.validate());
    if (contractErrors.length > 0) return platformRuntimeMountFailure("PLATFORM_RUNTIME_REGISTRY_INVALID", contractErrors);
    tracking = { operation: "mount", phase: "mount-projection", subject: "runtime", boundary: "projection", effect: "mount-completed-result-not-returned" };
    return {
      ok: true,
      value: {
        apps: mountedApps,
        diagnosticCatalogs: registry.diagnosticCatalogs(),
        registry,
        permissions: registry.permissions(),
        routes: registry.routes(),
        jobs: registry.jobs(),
        observabilityProfiles: registry.observabilityProfiles(),
        healthChecks: registry.healthChecks(),
        configSchemas: registry.configSchemas(),
      },
    };
  } catch (error) {
    const registered = catalogs();
    if (pendingFailure !== undefined) runtimeBoundaryEvidence(input, pendingFailure.detail, pendingFailure.cause, registered);
    runtimeBoundaryEvidence(input, tracking, error, registered);
    throw error;
  }
}

function contractSuccess(): Result<void, PlatformContractError> {
  return { ok: true, value: undefined };
}

function routeKey(route: PlatformRouteRegistration): string {
  return `${route.method} ${route.path}`;
}
