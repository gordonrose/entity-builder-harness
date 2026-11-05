import type { Permission } from "@kanbien/core/authz";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { captureServerDiagnostic, serverDiagnosticRecord, serverRequestPredicateRecord, serverRequestBoundaryRecord, platformServerDiagnosticCatalog, serverDiagnosticErrorCodes, type serverObservedPhases } from "./diagnostics";
import { diagnosticProcessingDefinition, diagnosticProcessingRecord, selectDiagnosticEvidenceWithReport, selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { validationDiagnostic } from "@kanbien/core/validation";
export { platformServerDiagnostic, platformServerDiagnosticCatalog, serverClientAddressTrustConfigurationRecord, serverClientAddressFallbackRecord, observeServerDiagnostic } from "./diagnostics";
export { serverDiagnosticErrorCodes } from "./diagnostics";
import type { Logger } from "@kanbien/core/logging";
import { noopTracer, type TraceSpan, type Tracer } from "@kanbien/core/monitoring";
import { type CorrelationId, type JsonValue, type Result } from "@kanbien/core/shared";
import type { TenantContext } from "@kanbien/core/tenancy";
import {
  platformProfileAllowsSignal,
  platformErrorClassDeclarations,
  platformProfileLogFields,
  platformProfileMeasuresLatency,
  platformProfileMetricLabels,
  platformProfileTraceFields,
  platformContractDiagnosticCatalog,
  type PlatformApp,
  type PlatformCapabilityObservabilityProfile,
  type PlatformDiagnosticReporter,
  type PlatformDiagnosticCatalog,
  type PlatformMountDeps,
  type PlatformOperationalNomenclature,
  type PlatformOperationalOutcome,
  type PlatformRequest,
  type PlatformResourceAuthorizationResolution,
  type PlatformResponse,
  type PlatformRouteRegistration,
  type PlatformTenantResolver,
} from "@kanbien/platform-contracts";
import {
  createPlatformRuntimeLifecycle,
  createPlatformRuntimeRequestContext,
  platformRuntimeDiagnosticCatalog,
  mountPlatformRuntimeApps,
  type PlatformRuntimeLifecycleController,
  type PlatformRuntimeMountResult,
} from "@kanbien/platform-runtime";
import { assertPlatformConfigValid, platformConfigDiagnosticCatalog } from "@kanbien/platform-config";
import { platformHealthDiagnosticCatalog, platformHealthHttpStatus, platformLiveness, platformReadiness } from "@kanbien/platform-health";
import {
  elapsedMilliseconds,
  endPlatformTraceSpan,
  platformErrorClass,
  platformTraceFields,
  recordPlatformHealthMetric,
  recordPlatformMetric,
  recordPlatformRequestMetric,
  startPlatformTraceSpan,
  writePlatformLog,
  createPlatformDiagnosticReporter,
  createPlatformMetricDiagnosticBinding,
  platformObservabilityDiagnosticCatalog,
  type PlatformMetricDiagnosticBinding,
  reportPlatformErrorDiagnostic,
  reportPlatformDiagnostic,
  reportPlatformObservationBoundary,
  reportPlatformObservationSources,
  type PlatformObservationDiagnostics,
  type PlatformObservationBoundaryDetail,
} from "@kanbien/platform-observability";
import {
  authorizePlatformPermissions,
  corsPolicyForRequestOrigin,
  createInMemoryPlatformRateLimiter,
  createPlatformSecurityHeaders,
  denyByDefaultAuthenticationResult,
  platformRateLimitKey,
  platformRateLimitError,
  principalFromPlatformAuthenticationResult,
  validateAuthzMappingPermissions,
  platformSecurityDiagnosticCatalog,
  securityOperationDiagnosticRecord,
  securityFailureDiagnosticRecord,
  securityDiagnosticRecordsFrom,
  observePlatformRateLimitCheck,
  observeCorsPolicyForRequestOrigin,
  securityOwnedHeaderReferences,
  type PlatformAuthenticationHook,
  type PlatformAuthenticationResult,
  type PlatformRateLimiter,
} from "@kanbien/platform-security";
import {
  listenNodePlatformServer,
  platformServerRequestId,
  resolvePlatformServerTransportOptions,
  type PlatformClientAddressResolver,
  type PlatformClientAddressResolverInput,
  type PlatformServerHandle,
  type PlatformServerListenOptions,
  type PlatformServerTransportAdmission,
  type PlatformServerTransportFailure,
  type PlatformServerTransportOptions,
  type ResolvedPlatformServerTransportOptions,
} from "./transport";

export type {
  PlatformClientAddressResolver,
  PlatformClientAddressResolverInput,
  PlatformServerHandle,
  PlatformServerListenOptions,
  PlatformServerTransportOptions,
  ResolvedPlatformServerTransportOptions,
} from "./transport";
export { resolvePlatformServerTransportOptions } from "./transport";

export { resolvePlatformServerRuntimeConfiguration, resolvePlatformServerRuntimeConfigurationWithDiagnostics } from "./configuration";
export type {
  PlatformServerHealthEndpointExposure,
  PlatformServerRuntimeConfiguration,
  PlatformServerRuntimeConfigurationInput,
  PlatformServerRuntimeConfigurationObservation,
} from "./configuration";

export {
  platformReleaseVerificationResponse,
  resolvePlatformReleaseIdentity,
} from "./verification";
export type {
  PlatformReleaseIdentity,
  PlatformReleaseVerificationResponse,
} from "./verification";

export type PlatformServerMiddlewareStep =
  | "request-id"
  | "request-logging"
  | "cors"
  | "security-headers"
  | "rate-limit"
  | "parse"
  | "auth"
  | "context"
  | "authorization"
  | "validation"
  | "handler"
  | "error-mapping"
  | "response-logging";

export type PlatformServerErrorCode =
  | "PLATFORM_SERVER_MOUNT_FAILED"
  | "PLATFORM_SERVER_CONFIG_INVALID"
  | "PLATFORM_SERVER_START_FAILED"
  | "PLATFORM_SERVER_ROUTE_NOT_FOUND"
  | "PLATFORM_SERVER_METHOD_NOT_ALLOWED"
  | "PLATFORM_SERVER_RATE_LIMITED"
  | "PLATFORM_SERVER_UNAUTHENTICATED"
  | "PLATFORM_SERVER_FORBIDDEN"
  | "PLATFORM_SERVER_RESOURCE_NOT_FOUND"
  | "PLATFORM_SERVER_TENANT_RESOLVER_REQUIRED"
  | "PLATFORM_SERVER_AUTHORIZER_REQUIRED"
  | "PLATFORM_SERVER_AUTHZ_MAPPING_INVALID"
  | "PLATFORM_SERVER_TRANSPORT_CONFIG_INVALID"
  | "PLATFORM_SERVER_INVALID_REQUEST"
  | "PLATFORM_SERVER_PAYLOAD_TOO_LARGE"
  | "PLATFORM_SERVER_UNSUPPORTED_MEDIA_TYPE"
  | "PLATFORM_SERVER_REQUEST_TIMEOUT"
  | "PLATFORM_SERVER_SERVICE_UNAVAILABLE"
  | "PLATFORM_SERVER_HANDLER_FAILED";

export interface PlatformServerError {
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
  readonly code: PlatformServerErrorCode;
  readonly defaultMessage: string;
  readonly status: number;
  readonly details?: Readonly<Record<string, JsonValue>>;
}

export interface PlatformServerRequest {
  readonly method: PlatformRouteRegistration["method"] | "OPTIONS";
  readonly path: string;
  readonly headers?: Readonly<Record<string, string | readonly string[]>>;
  readonly query?: Readonly<Record<string, string | readonly string[]>>;
  readonly body?: unknown;
  readonly clientAddress?: string;
  readonly requestId?: CorrelationId;
  readonly abortSignal?: AbortSignal;
  readonly transportAdmissionApplied?: boolean;
}

export interface PlatformServerResponse {
  readonly status: number;
  readonly body?: unknown;
  readonly headers: Readonly<Record<string, string>>;
  readonly middleware: readonly PlatformServerMiddlewareStep[];
}

export interface PlatformServerAuthResult extends PlatformAuthenticationResult {
}

export type PlatformServerAuthHook = PlatformAuthenticationHook;

export type PlatformHealthEndpointExposure = "public" | "authenticated";

export interface PlatformHealthExposurePolicy {
  readonly liveness?: PlatformHealthEndpointExposure;
  readonly readiness?: PlatformHealthEndpointExposure;
}

export interface PlatformServerOptions {
  /** Explicit target-owned dependency catalogs, validated with built-ins/apps. */
  readonly diagnosticCatalogs?: readonly PlatformDiagnosticCatalog[];
  /** Opt-in bounded policy decisions; route signal opt-outs still apply. */
  readonly securityDecisionDiagnostics?: boolean;
  readonly apps: readonly PlatformApp[];
  readonly deps: PlatformMountDeps;
  readonly auth?: PlatformServerAuthHook;
  readonly tenantResolver?: PlatformTenantResolver;
  readonly logger?: Logger;
  readonly tracer?: Tracer;
  readonly corsOrigin?: string;
  readonly corsAllowlist?: readonly string[];
  readonly healthExposure?: PlatformHealthExposurePolicy;
  readonly rateLimiter?: PlatformRateLimiter;
  readonly clientAddressResolver?: PlatformClientAddressResolver;
  readonly transport?: PlatformServerTransportOptions;
}

export interface PlatformServerShell {
  readonly mounted: PlatformRuntimeMountResult;
  readonly lifecycle: PlatformRuntimeLifecycleController;
  handle(request: PlatformServerRequest): Promise<PlatformServerResponse>;
  listen(options?: PlatformServerListenOptions): Promise<PlatformServerHandle>;
}

interface CompiledRoute {
  readonly registration: PlatformRouteRegistration;
  readonly pattern: RegExp;
  readonly params: readonly string[];
}

interface PlatformServerRequestHandlingInput {
  readonly selectDiagnosticDefinitions: () => readonly DiagnosticDefinition[];
  readonly metricDiagnostics: PlatformMetricDiagnosticBinding;
  readonly securityDecisionDiagnostics?: boolean;
  readonly routes: readonly CompiledRoute[];
  readonly profilesByName: ReadonlyMap<string, PlatformCapabilityObservabilityProfile>;
  readonly auth?: PlatformServerAuthHook;
  readonly tenantResolver?: PlatformTenantResolver;
  readonly deps: PlatformMountDeps;
  readonly logger: Logger;
  readonly tracer: Tracer;
  readonly corsOrigin?: string;
  readonly corsAllowlist?: readonly string[];
  readonly healthExposure?: PlatformHealthExposurePolicy;
  readonly rateLimiter: PlatformRateLimiter;
  readonly lifecycle: PlatformRuntimeLifecycleController;
  readonly healthChecks: PlatformRuntimeMountResult["healthChecks"];
}

const serverBuiltinDiagnosticCatalogs = Object.freeze([coreDiagnosticCatalog, platformContractDiagnosticCatalog,
  platformRuntimeDiagnosticCatalog, platformServerDiagnosticCatalog, platformConfigDiagnosticCatalog,
  platformSecurityDiagnosticCatalog, platformObservabilityDiagnosticCatalog, platformHealthDiagnosticCatalog]);

export async function createPlatformServerShell(options: PlatformServerOptions): Promise<Result<PlatformServerShell, PlatformServerError>> {
  let startupCatalogs: readonly PlatformDiagnosticCatalog[] = [];
  function diagnosticDefinitions(): readonly DiagnosticDefinition[] {
    return [...serverBuiltinDiagnosticCatalogs, ...(options.diagnosticCatalogs ?? []), ...startupCatalogs].flatMap((catalog) => catalog.definitions);
  }
  let selectedStartupReporter: PlatformDiagnosticReporter | undefined;
  // Laziness preserves healthy startup ordering: diagnostics initialize only
  // when a failed configuration/registration actually needs reporting.
  const startupDiagnostics: PlatformDiagnosticReporter = { report(record, context) {
    if (selectedStartupReporter === undefined) {
      const builtins = serverBuiltinDiagnosticCatalogs;
      try { selectedStartupReporter = options.deps.diagnostics ?? createPlatformDiagnosticReporter({
        catalogs: [...builtins, ...(options.diagnosticCatalogs ?? []), ...startupCatalogs],
        logger: options.logger ?? options.deps.logger, clock: options.deps.clock,
      }); } catch (error) {
        try {
          selectedStartupReporter = createPlatformDiagnosticReporter({ catalogs: builtins, logger: options.logger ?? options.deps.logger, clock: options.deps.clock });
          reportPlatformErrorDiagnostic(selectedStartupReporter, error, { capability: "platform-contracts", operation: "select-diagnostic-catalog", stage: "configuration" });
        } catch { return { status: "unavailable" }; }
      }
    }
    try { return selectedStartupReporter.report(record, context); } catch { return { status: "unavailable" }; }
  } };
  const transport = resolvePlatformServerTransportOptions(options.transport);
  if (!transport.ok) {
    const error = { ...serverError(
        "PLATFORM_SERVER_TRANSPORT_CONFIG_INVALID",
        500,
        "Platform server transport configuration is invalid.",
        { reason: transport.reason },
      ), diagnosticRecord: transport.diagnosticRecord };
    reportPlatformErrorDiagnostic(startupDiagnostics, error, { capability: "platform-server", operation: "configure-transport", stage: "configuration" });
    return { ok: false, error };
  }

  const mounted = await mountPlatformRuntimeApps({
    apps: options.apps,
    deps: options.deps,
    get diagnosticDefinitions() { return diagnosticDefinitions(); },
    onDiagnostic(record, context, catalogs) {
      if (catalogs !== undefined) startupCatalogs = catalogs;
      reportPlatformDiagnostic(startupDiagnostics, record, context);
    },
  });

  if (!mounted.ok) {
    for (const error of mounted.error.contractErrors) reportPlatformErrorDiagnostic(startupDiagnostics, error,
      { capability: "platform-contracts", operation: "register", stage: "configuration" });
    return {
      ok: false,
      error: {
        code: "PLATFORM_SERVER_MOUNT_FAILED",
        ...(mounted.error.diagnosticRecord === undefined ? { diagnosticRecord: captureServerDiagnostic(() => serverDiagnosticRecord("PLATFORM_SERVER_MOUNT_FAILED")) } : { diagnosticRecord: mounted.error.diagnosticRecord }),
        ...(mounted.error.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: mounted.error.relatedDiagnosticRecords }),
        defaultMessage: "Platform server failed to mount apps.",
        status: 500,
        details: { runtimeCode: mounted.error.code },
      },
    };
  }

  startupCatalogs = mounted.value.diagnosticCatalogs;

  const authzMapping = validateServerAuthzMapping(options.auth, mounted.value.permissions.map((permission) => permission.permission));
  if (!authzMapping.ok) {
    reportPlatformErrorDiagnostic(startupDiagnostics, authzMapping.error, { capability: "security", operation: "configure-authorization", stage: "configuration" });
    return authzMapping;
  }

  const richerAuthorizationConfiguration = validateRicherAuthorizationConfiguration({
    routes: mounted.value.routes,
    hasAuthorizer: options.deps.authorizer !== undefined,
    ...(options.tenantResolver === undefined ? {} : { tenantResolver: options.tenantResolver }),
  });
  if (!richerAuthorizationConfiguration.ok) {
    reportPlatformErrorDiagnostic(startupDiagnostics, richerAuthorizationConfiguration.error, { capability: "platform-server", operation: "configure-authorization", stage: "configuration" });
    return richerAuthorizationConfiguration;
  }

  const config = assertPlatformConfigValid({
    source: options.deps.config,
    schemas: mounted.value.configSchemas,
    get diagnosticDefinitions() { return diagnosticDefinitions(); },
    onDiagnostic: (record) => reportPlatformDiagnostic(startupDiagnostics, record, { capability: "platform-config", operation: "validate-schema", stage: "configuration" }),
  });
  if (!config.ok) {
    return {
      ok: false,
      error: {
        code: "PLATFORM_SERVER_CONFIG_INVALID",
        ...(config.error.diagnosticRecord === undefined ? {} : { diagnosticRecord: config.error.diagnosticRecord }),
        ...(config.error.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: config.error.relatedDiagnosticRecords }),
        defaultMessage: "Platform server config validation failed before listen.",
        status: 500,
        details: config.error.details,
      },
    };
  }

  const lifecycle = createPlatformRuntimeLifecycle({ apps: mounted.value.apps,
    get diagnosticDefinitions() { return diagnosticDefinitions(); },
    onDiagnostic: (record, context) => reportPlatformDiagnostic(startupDiagnostics, record, context),
  });
  const routes = mounted.value.routes.map(compileRoute);
  const profilesByName = new Map(mounted.value.observabilityProfiles.map((profile) => [String(profile.name), profile]));
  const logger = options.logger ?? options.deps.logger;
  let diagnostics: PlatformDiagnosticReporter;
  try {
    diagnostics = options.deps.diagnostics ?? createPlatformDiagnosticReporter({
      catalogs: [...serverBuiltinDiagnosticCatalogs, ...(options.diagnosticCatalogs ?? []), ...mounted.value.diagnosticCatalogs],
      logger, clock: options.deps.clock,
    });
  } catch (error) {
    // The invalid selected catalog cannot validate its own failure. Deliver the
    // contract-owned observation through the fixed contract catalog instead.
    try { reportPlatformErrorDiagnostic(createPlatformDiagnosticReporter({ catalogs: [platformContractDiagnosticCatalog], logger, clock: options.deps.clock }), error,
      { capability: "platform-contracts", operation: "select-diagnostic-catalog", stage: "configuration" }); } catch { /* Optional delivery only. */ }
    return { ok: false, error: serverError("PLATFORM_SERVER_MOUNT_FAILED", 500, "Platform server diagnostic catalog selection is invalid.") };
  }
  const tracer = options.tracer ?? noopTracer;
  const rateLimiter = options.rateLimiter ?? createInMemoryPlatformRateLimiter({ clock: options.deps.clock });
  const requestInput: PlatformServerRequestHandlingInput = {
    selectDiagnosticDefinitions: diagnosticDefinitions,
    metricDiagnostics: createPlatformMetricDiagnosticBinding(diagnostics, { capability: "platform-server", stage: "request" }),
    routes,
    profilesByName,
    deps: { ...options.deps, diagnostics },
    logger,
    tracer,
    rateLimiter,
    lifecycle,
    healthChecks: mounted.value.healthChecks,
    ...(options.securityDecisionDiagnostics === undefined ? {} : { securityDecisionDiagnostics: options.securityDecisionDiagnostics }),
    ...(options.corsOrigin === undefined ? {} : { corsOrigin: options.corsOrigin }),
    ...(options.corsAllowlist === undefined ? {} : { corsAllowlist: options.corsAllowlist }),
    ...(options.healthExposure === undefined ? {} : { healthExposure: options.healthExposure }),
    ...(options.auth === undefined ? {} : { auth: options.auth }),
    ...(options.tenantResolver === undefined ? {} : { tenantResolver: options.tenantResolver }),
  };

  return {
    ok: true,
    value: {
      mounted: mounted.value,
      lifecycle,
      handle: (request) => handlePlatformServerRequest({ request, ...requestInput }),
      listen: (listenOptions = {}) => listenNodePlatformServer({
        handle: (request) => handlePlatformServerRequest({ request, ...requestInput }),
        admit: (request) => admitPlatformServerTransportRequest({ request, ...requestInput }),
        failure: (failure) => handlePlatformServerTransportFailure({ failure, ...requestInput }),
        onServerError: (error) => writePlatformLog(logger, {
          level: "error",
          message: "platform.server.transport_error",
          error,
        }),
        onDiagnostic(record, request) {
          if (request !== undefined) reportServerRequestObservation(requestInput, request, record);
          else reportPlatformDiagnostic(diagnostics, record, { capability: "platform-server", operation: "transport", stage:
            record.detail !== null && typeof record.detail === "object" && "phase" in record.detail && record.detail.phase === "listen" ? "startup"
              : record.detail !== null && typeof record.detail === "object" && "phase" in record.detail && (record.detail.phase === "shutdown" || record.detail.phase === "close-callback" || record.detail.phase === "close-invocation") ? "shutdown" : "runtime" });
        },
        ...(options.securityDecisionDiagnostics ? { onRequestMetadata(request: PlatformServerRequest, records: readonly DiagnosticRecord[]) {
          for (const record of records) reportServerRequestObservation(requestInput, request, record);
        } } : {}),
        options: listenOptions,
        transport: transport.value,
        ...(options.clientAddressResolver === undefined ? {} : { clientAddressResolver: options.clientAddressResolver }),
      }),
    },
  };
}

async function handlePlatformServerRequest(input: PlatformServerRequestHandlingInput & {
  readonly request: PlatformServerRequest;
}): Promise<PlatformServerResponse> {
  const middleware: PlatformServerMiddlewareStep[] = [];
  let failurePhase: (typeof serverObservedPhases)[number] = "admission";
  let routeFailure: DiagnosticRecord | undefined;
  const beforeRequest = <T>(phase: "request-clock" | "request-identity" | "route-selection", action: () => T): T => {
    try { return action(); }
    catch (error) {
      reportServerRequestObservation(input, input.request, phase === "route-selection" && routeFailure !== undefined ? routeFailure : captureServerDiagnostic(() => serverRequestBoundaryRecord(phase, "handler-not-invoked")));
      reportServerRequestEvidence(input, input.request, error);
      throw error;
    }
  };
  const startedAt = beforeRequest("request-clock", () => input.deps.clock.now());
  const requestId = beforeRequest("request-identity", () => input.request.requestId ?? platformServerRequestId(firstHeaderValue(input.request.headers ?? {}, "x-request-id")));
  const routeMatch = beforeRequest("route-selection", () => findRoute(input.routes, input.request, (record) => {
    routeFailure = record;
  }));
  const profile = routeMatch === undefined
    ? undefined
    : serverProfileForRoute(routeMatch.route.registration, input.profilesByName);
  const observations = serverObservationDiagnostics(input, input.request, profile);
  const traceSpan = profile === undefined
    ? routeMatch === undefined
      ? startPlatformTraceSpan(input.tracer, {
        name: "platform.server.request",
        attributes: serverObservationProjection(observations, "trace-projection", () => ({ method: input.request.method })),
      }, undefined, observations)
      : undefined
    : platformProfileAllowsSignal(profile, "trace")
      ? startPlatformTraceSpan(input.tracer, { name: "platform.server.request" }, profile, observations)
      : undefined;
  const requestOrigin = firstHeaderValue(input.request.headers ?? {}, "origin");
  const securityObservations: DiagnosticRecord[] = [];
  if (input.securityDecisionDiagnostics) securityObservations.push(observeCorsPolicyForRequestOrigin({
    ...(requestOrigin === undefined ? {} : { requestOrigin }),
    allowedOrigins: input.corsAllowlist ?? (input.corsOrigin === undefined ? [] : [input.corsOrigin]),
  }).diagnosticRecord);
  const headers = platformResponseHeaders({
    requestId,
    ...(requestOrigin === undefined ? {} : { requestOrigin }),
    ...(input.corsOrigin === undefined ? {} : { corsOrigin: input.corsOrigin }),
    ...(input.corsAllowlist === undefined ? {} : { corsAllowlist: input.corsAllowlist }),
  });
  let routeName = "unknown";
  const boundaryObservations: DiagnosticRecord[] = [];
  let handlerInvoked = false;
  let handlerCompleted = false;
  let contextDiagnostic: DiagnosticRecord | undefined;
  let requestBoundaryPhase: "resource-resolution" | "authorization" | undefined;

  const finish = (
    platformResponse: PlatformServerResponse,
    route: string,
    error?: unknown,
  ): PlatformServerResponse => {
    if (serverObservationProjection(observations, "profile-projection", () => profile === undefined ? routeMatch === undefined && unmatchedSecurityPathAllowsDiagnostics(input, input.request.path) : platformProfileAllowsSignal(profile, "operational_log"), error)) {
      for (const record of securityObservations) reportPlatformErrorDiagnostic(diagnosticsFor(input), { diagnosticRecord: record }, { capability: "security", operation: "request", stage: "request", correlationId: requestId });
      for (const record of boundaryObservations) reportPlatformDiagnostic(diagnosticsFor(input), record, { capability: "platform-server", operation: "request", stage: "request", correlationId: requestId });
    }
    const latencyMs = serverObservationElapsed(observations, startedAt,
      serverObservationProjection(observations, "clock", () => input.deps.clock.now(), error), error);
    const errorClass = error === undefined ? undefined : serverObservationProjection(observations, "error-class", () => platformErrorClass(error, profile ?? { errorClasses: serverDiagnosticErrorCodes }), error);
    if (profile !== undefined && routeMatch !== undefined) {
      if (error !== undefined && platformProfileAllowsSignal(profile, "operational_log")) {
        reportPlatformErrorDiagnostic(diagnosticsFor(input), error, { capability: "platform-server", operation: "request", stage: "request", correlationId: requestId });
      }
      recordServerProfileObservation({
        observations,
        metricDiagnostics: input.metricDiagnostics,
        deps: input.deps,
        logger: input.logger,
        profile,
        method: routeMatch.route.registration.method,
        response: platformResponse,
        startedAt,
        ...(error === undefined ? {} : { error }),
      });
      endServerProfileTrace({
        observations,
        profile,
        span: traceSpan,
        method: routeMatch.route.registration.method,
        response: platformResponse,
        ...(error === undefined ? {} : { error }),
      });
    } else if (routeMatch === undefined && traceSpan !== undefined) {
      if (error !== undefined && unmatchedSecurityPathAllowsDiagnostics(input, input.request.path)) {
        reportPlatformErrorDiagnostic(diagnosticsFor(input), error, { capability: "platform-server", operation: "request", stage: "request", correlationId: requestId });
      }
      serverObservationProjection(observations, "metric-projection", () => recordPlatformRequestMetric(input.deps.metrics, input.deps.clock, {
        method: input.request.method,
        route,
        status: platformResponse.status,
        latencyMs,
        ...(errorClass === undefined ? {} : { errorClass }),
      }, unmatchedSecurityPathAllowsDiagnostics(input, input.request.path) ? { binding: input.metricDiagnostics, operation: "request" } : undefined, { errorClasses: serverDiagnosticErrorCodes }, observations), error);
      serverObservationProjection(observations, "log-projection", () => writePlatformLog(input.logger, {
        level: platformResponse.status >= 500 ? "error" : platformResponse.status >= 400 ? "warn" : "info",
        message: "platform.server.request",
        correlationId: requestId,
        fields: {
          ...platformTraceFields({
            requestId,
            correlationId: requestId,
            route,
            latencyMs,
            ...(errorClass === undefined ? {} : { errorClass }),
          }, { errorClasses: serverDiagnosticErrorCodes }, observations),
          method: input.request.method,
          status: platformResponse.status,
        },
        ...(error === undefined ? {} : { error }),
      }, { errorClasses: serverDiagnosticErrorCodes }, observations), error);
      serverObservationProjection(observations, "trace-projection", () => endPlatformTraceSpan(traceSpan, {
        outcome: traceOutcomeForResponse(platformResponse.status),
        attributes: {
          method: input.request.method,
          route,
          status: platformResponse.status,
          latencyMs,
          ...(errorClass === undefined ? {} : { errorClass }),
        },
      }, { errorClasses: serverDiagnosticErrorCodes }, observations), error);
    }

    return platformResponse;
  };

  try {
    middleware.push("request-id", "request-logging", "cors", "security-headers", "rate-limit", "parse");

    if (!input.request.transportAdmissionApplied) {
      const rateLimit = await observePlatformRateLimitCheck(input.rateLimiter, platformRateLimitKey({
        ...(input.request.clientAddress === undefined ? {} : { clientAddress: input.request.clientAddress }),
      }), { boundary: "transport", keyCategory: input.request.clientAddress === undefined || input.request.clientAddress.length === 0 ? "anonymous" : "client-address" });
      if (!rateLimit.allowed) {
        securityObservations.push(...securityDiagnosticRecordsFrom(rateLimit));
        middleware.push("error-mapping", "response-logging");
        const error = platformRateLimitError(rateLimit.retryAfterMs);
        return finish(
          rateLimitErrorResponse(error, headers, middleware),
          "platform.rate-limit",
          error,
        );
      }
    }

    if (input.request.method === "OPTIONS") {
      const allowedMethods = allowedMethodsForPath(input.routes, input.request.path);
      if (input.securityDecisionDiagnostics) securityObservations.push(securityOperationDiagnosticRecord("cors", allowedMethods.length === 0 ? "preflight-path-missing" : "preflight-path-present"));
      if (allowedMethods.length === 0) {
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_ROUTE_NOT_FOUND", 404, "No platform route matched the request.");
        return finish(errorResponse(error, headers, middleware), routeName, error);
      }

      middleware.push("handler", "response-logging");
      return finish(response(204, undefined, {
        ...headers,
        allow: [...allowedMethods, "OPTIONS"].join(", "),
        "access-control-allow-methods": [...allowedMethods, "OPTIONS"].join(", "),
      }, middleware), "platform.cors-preflight");
    }

    if (input.request.path === "/livez" && input.request.method === "GET") {
      failurePhase = "authentication";
      const auth = await authenticateHealthEndpoint(input.auth, input.request, input.healthExposure?.liveness ?? "public", middleware);
      if (!auth.authenticated && (input.healthExposure?.liveness ?? "public") === "authenticated") {
        securityObservations.push(...securityDiagnosticRecordsFrom(auth));
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_UNAUTHENTICATED", 401, "Authentication is required.");
        return finish(errorResponse(error, headers, middleware), "platform.livez", error);
      }
      middleware.push("handler", "response-logging");
      const live = platformLiveness(input.deps.clock);
      recordPlatformHealthMetric(input.deps.metrics, input.deps.clock, { healthState: live.status }, { binding: input.metricDiagnostics, operation: "health" });
      return finish(response(200, { status: live.status }, headers, middleware), "platform.livez");
    }

    if (input.request.path === "/readyz" && input.request.method === "GET") {
      failurePhase = "authentication";
      const auth = await authenticateHealthEndpoint(input.auth, input.request, input.healthExposure?.readiness ?? "public", middleware);
      if (!auth.authenticated && (input.healthExposure?.readiness ?? "public") === "authenticated") {
        securityObservations.push(...securityDiagnosticRecordsFrom(auth));
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_UNAUTHENTICATED", 401, "Authentication is required.");
        return finish(errorResponse(error, headers, middleware), "platform.readyz", error);
      }
      middleware.push("handler", "response-logging");
      failurePhase = "readiness";
      const ready = await platformReadiness({
        ...(input.deps.diagnostics === undefined ? {} : { diagnostics: input.deps.diagnostics }),
        lifecycleReady: input.lifecycle.isReady(),
        healthChecks: input.healthChecks,
        clock: input.deps.clock,
      });
      recordPlatformHealthMetric(input.deps.metrics, input.deps.clock, { healthState: ready.status }, { binding: input.metricDiagnostics, operation: "health" });
      return finish(response(platformHealthHttpStatus(ready.status), ready, headers, middleware), "platform.readyz");
    }

    if (routeMatch === undefined) {
      middleware.push("error-mapping", "response-logging");
      const allowedMethods = allowedMethodsForPath(input.routes, input.request.path);
      const error = allowedMethods.length === 0
        ? serverError("PLATFORM_SERVER_ROUTE_NOT_FOUND", 404, "No platform route matched the request.")
        : serverError("PLATFORM_SERVER_METHOD_NOT_ALLOWED", 405, "The request method is not allowed.");
      boundaryObservations.push(captureServerDiagnostic(() => serverRequestPredicateRecord("route", allowedMethods.length === 0 ? "path-not-registered" : "method-not-registered", "routing")));
      return finish(
        errorResponse(error, allowedMethods.length === 0 ? headers : {
          ...headers,
          allow: [...allowedMethods, "OPTIONS"].join(", "),
        }, middleware),
        routeName,
        error,
      );
    }

    const { route, params } = routeMatch;
    routeName = String(route.registration.name);
    const platformRequest: PlatformRequest = {
      params,
      query: input.request.query ?? {},
      headers: input.request.headers ?? {},
      ...(input.request.body === undefined ? {} : { body: input.request.body }),
    };
    middleware.push("auth");
    failurePhase = "authentication";
    const auth = await authenticateRequest(input.auth, input.request);
    let capturedMissingPrincipalAttribute: "principal-id" | "principal-type" | "subject" | undefined;
    const principal = route.registration.auth.kind === "authenticated"
      ? principalFromPlatformAuthenticationResult(auth, {
        get diagnosticDefinitions() { return input.selectDiagnosticDefinitions(); },
        onMissingAttribute(attribute) {
          capturedMissingPrincipalAttribute = attribute;
          // Retain this actual guard before any legacy reread can change or
          // throw. Later checks still execute, but do not repeat this fact.
          securityObservations.push(securityOperationDiagnosticRecord("authentication", "principal-attribute-missing", { attribute }));
        },
        onDiagnostic(record, context) {
          // The outer request catch already retains selected source9. Buffer
          // only independent owned locations here, through the same profile.
          if (context.evidence === "owned" && record.code !== "security.authentication.principal-attribute-missing") boundaryObservations.push(record);
        },
      })
      : undefined;
    if (route.registration.auth.kind === "authenticated" && (!auth.authenticated || principal === undefined)) {
      securityObservations.push(...securityDiagnosticRecordsFrom(auth));
      const missingPrincipalAttribute = (attribute: "principal-id" | "principal-type" | "subject"): void => {
        if (attribute !== capturedMissingPrincipalAttribute) securityObservations.push(securityOperationDiagnosticRecord("authentication", "principal-attribute-missing", { attribute }));
      };
      if (auth.authenticated && principal === undefined) {
        if (auth.principalId === undefined) missingPrincipalAttribute("principal-id");
        if (auth.principalType === undefined) missingPrincipalAttribute("principal-type");
        if (auth.subject === undefined) missingPrincipalAttribute("subject");
      }
      middleware.push("error-mapping", "response-logging");
      const error = serverError("PLATFORM_SERVER_UNAUTHENTICATED", 401, "Authentication is required.");
      return finish(errorResponse(error, headers, middleware), routeName, error);
    }

    if (route.registration.auth.kind === "authenticated") {
      if (auth.rateLimitKey !== undefined) {
        failurePhase = "admission";
        const principalRateLimit = await observePlatformRateLimitCheck(input.rateLimiter, platformRateLimitKey({ authentication: auth }), { boundary: "principal", keyCategory: "principal" });
        if (!principalRateLimit.allowed) {
          securityObservations.push(...securityDiagnosticRecordsFrom(principalRateLimit));
          middleware.push("error-mapping", "response-logging");
          const error = platformRateLimitError(principalRateLimit.retryAfterMs);
          return finish(rateLimitErrorResponse(error, headers, middleware), routeName, error);
        }
      }

      middleware.push("authorization");
      failurePhase = "authorization";
      const authorized = authorizePlatformPermissions(route.registration.auth.permissions ?? [], auth.permissions ?? []);
      if (!authorized.ok) {
        securityObservations.push(...securityDiagnosticRecordsFrom(authorized.error), ...securityDiagnosticRecordsFrom(auth));
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_FORBIDDEN", 403, authorized.error.defaultMessage, authorized.error.details);
        return finish(
          errorResponse(error, headers, middleware),
          routeName,
          error,
        );
      }
    }

    failurePhase = "tenant-resolution";
    const tenantResolution = route.registration.tenant === undefined || input.tenantResolver === undefined || principal === undefined
      ? undefined
      : await input.tenantResolver.resolve({
        route: {
          name: route.registration.name,
          method: route.registration.method,
          path: route.registration.path,
          ...(route.registration.apiVersion === undefined ? {} : { apiVersion: route.registration.apiVersion }),
        },
        request: platformRequest,
        principal,
      });
    let tenantFailure = captureServerDiagnostic(() => serverRequestPredicateRecord("tenant-result", "tenant-unavailable", "tenant-resolution"));
    const tenant = isTenantContext(tenantResolution, (field, condition) => {
      tenantFailure = captureServerDiagnostic(() => serverRequestPredicateRecord(field, condition, "tenant-resolution"));
    }) ? tenantResolution : undefined;
    if (route.registration.tenant === "required" && (tenant === null || tenant === undefined)) {
      boundaryObservations.push(tenantFailure);
      middleware.push("error-mapping", "response-logging");
      const error = serverError("PLATFORM_SERVER_FORBIDDEN", 403, "Access to this route is forbidden.");
      return finish(errorResponse(error, headers, middleware), routeName, error);
    }

    middleware.push("context");
    failurePhase = "context";
    const context = { ...createPlatformRuntimeRequestContext({
      requestId,
      method: input.request.method,
      path: input.request.path,
      ...(principal === undefined ? {} : { principal }),
      ...(tenant === undefined || tenant === null ? {} : { tenant }),
      ...(input.request.abortSignal === undefined ? {} : { abortSignal: input.request.abortSignal }),
      logger: input.deps.logger,
      metrics: input.deps.metrics,
      config: input.deps.config,
      flags: input.deps.flags,
      clock: input.deps.clock,
      onDiagnostic: (record) => { contextDiagnostic = record; },
    }), ...(profile !== undefined && platformProfileAllowsSignal(profile, "operational_log") ? {
      onDiagnostic: (record: DiagnosticRecord): void => {
        // App-owned observations use the same selected catalogs and sink as
        // thrown failures, including injected/unavailable reporters. Do not
        // put independent observations into error-shaped response metadata.
        try {
          const checked = selectedServerEvidence(input, { diagnosticRecord: record }, notice => reportPlatformDiagnostic(diagnosticsFor(input), notice, {
            capability: profile.capability, operation: "request-observation", stage: "request", correlationId: requestId,
          })).diagnosticRecord;
          if (checked !== undefined) reportPlatformDiagnostic(diagnosticsFor(input), checked, {
            capability: profile.capability, operation: "request-observation", stage: "request", correlationId: requestId,
          });
        } catch { /* Observation cannot change handler or response behavior. */ }
      },
    } : {}) };

    middleware.push("validation");
    failurePhase = "request-validation";
    if (route.registration.validator !== undefined && !route.registration.validator.validate(input.request.body)) {
      middleware.push("error-mapping", "response-logging");
      const detail = validationDiagnostic(route.registration.validator, input.request.body);
      const error = { ...serverError("PLATFORM_SERVER_INVALID_REQUEST", 400, "Request body failed route validation."),
        ...(detail === undefined ? {} : { diagnosticRecord: detail }) };
      boundaryObservations.push(captureServerDiagnostic(() => serverRequestPredicateRecord("request-body", "validator-rejected", "request-validation")));
      return finish(errorResponse(error, headers, middleware), routeName, error);
    }

    if (route.registration.resourceAuthorization !== undefined) {
      middleware.push("authorization");
      failurePhase = "authorization";
      requestBoundaryPhase = "resource-resolution";
      const resourceResolution = await route.registration.resourceAuthorization.resolve({
        request: platformRequest,
        context,
      });
      let resourceFailure = captureServerDiagnostic(() => serverRequestPredicateRecord("resource-result", "object-required", "resource-resolution"));
      if (!isPlatformResourceAuthorizationResolution(resourceResolution, (field, condition) => {
        resourceFailure = captureServerDiagnostic(() => serverRequestPredicateRecord(field, condition, "resource-resolution"));
      })) {
        boundaryObservations.push(resourceFailure);
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_FORBIDDEN", 403, "Access to this resource is forbidden.");
        return finish(errorResponse(error, headers, middleware), routeName, error);
      }
      if (resourceResolution.kind === "not-found") {
        middleware.push("error-mapping", "response-logging");
        const forbiddenDisclosure = resourceResolution.disclosure === "forbidden";
        const error = forbiddenDisclosure
          ? serverError("PLATFORM_SERVER_FORBIDDEN", 403, "Access to this resource is forbidden.")
          : serverError("PLATFORM_SERVER_RESOURCE_NOT_FOUND", 404, "The requested resource was not found.");
        boundaryObservations.push(captureServerDiagnostic(() => serverRequestPredicateRecord("resource", forbiddenDisclosure ? "forbidden-disclosure" : "not-found", "resource-resolution")));
        return finish(errorResponse(error, headers, middleware), routeName, error);
      }

      requestBoundaryPhase = "authorization";
      const authorizer = input.deps.authorizer;
      if (authorizer === undefined || principal === undefined) {
        boundaryObservations.push(captureServerDiagnostic(() => serverRequestPredicateRecord(authorizer === undefined ? "authorizer" : "principal", "unavailable", "authorization")));
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_FORBIDDEN", 403, "Access to this resource is forbidden.");
        return finish(errorResponse(error, headers, middleware), routeName, error);
      }

      const decision = await authorizer.decide({
        principal,
        permission: route.registration.resourceAuthorization.permission,
        ...(context.tenant === undefined ? {} : { tenantId: context.tenant.tenantId }),
        ...(resourceResolution.resource === undefined ? {} : { resource: resourceResolution.resource }),
        ...(resourceResolution.relations === undefined ? {} : { relations: resourceResolution.relations }),
        ...(resourceResolution.attributes === undefined ? {} : { attributes: resourceResolution.attributes }),
        ...(resourceResolution.facts === undefined ? {} : { facts: resourceResolution.facts }),
      });
      if (!decision.allowed) {
        securityObservations.push(securityOperationDiagnosticRecord("authorization", "resource-denied"));
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_FORBIDDEN", 403, "Access to this resource is forbidden.");
        return finish(errorResponse(error, headers, middleware), routeName, error);
      }
    }

    middleware.push("handler");
    requestBoundaryPhase = undefined;
    failurePhase = "handler";
    handlerInvoked = true;
    const handled = await route.registration.handler.handle(platformRequest, context);
    handlerCompleted = true;

    middleware.push("response-logging");
    failurePhase = "response";
    const observabilityError = handled.observability === undefined ? undefined : {
      ...(handled.observability.errorClass === undefined ? {} : { code: handled.observability.errorClass }),
      ...(handled.observability.diagnosticRecord === undefined ? {} : { diagnosticRecord: handled.observability.diagnosticRecord }),
    };
    if (input.securityDecisionDiagnostics) {
      if (auth.authenticated) securityObservations.push(...securityDiagnosticRecordsFrom(auth));
      for (const name of Object.keys(handled.headers ?? {})) {
        const headerReference = securityOwnedHeaderReferences.find((item) => item === name.toLowerCase());
        if (headerReference !== undefined) securityObservations.push(securityOperationDiagnosticRecord("response-header", "platform-owned-override-ignored", { headerReference }));
      }
    }
    return finish(
      response(handled.status, handled.body, mergeApplicationResponseHeaders(headers, handled.headers), middleware),
      routeName,
      observabilityError,
    );
  } catch (error) {
    const retainedSecurity = securityFailureDiagnosticRecord(error);
    if (retainedSecurity !== undefined) securityObservations.push(...securityDiagnosticRecordsFrom(error));
    else if (failurePhase === "authentication" || failurePhase === "authorization") securityObservations.push(securityOperationDiagnosticRecord(failurePhase, "component-failed"));
    middleware.push("error-mapping", "response-logging");
    const failure = { ...serverError("PLATFORM_SERVER_HANDLER_FAILED", 500, "Platform route handler failed."),
      diagnosticRecord: captureServerDiagnostic(() => serverDiagnosticRecord("PLATFORM_SERVER_HANDLER_FAILED", failurePhase)) };
    let boundary: DiagnosticRecord | undefined;
    if (failurePhase === "tenant-resolution" || failurePhase === "context" || failurePhase === "request-validation" || failurePhase === "handler" || failurePhase === "response" || failurePhase === "authorization") {
      const boundaryPhase = requestBoundaryPhase ?? failurePhase;
      boundary = contextDiagnostic ?? captureServerDiagnostic(() => serverRequestBoundaryRecord(boundaryPhase,
        handlerCompleted ? "handler-completed-response-not-returned" : handlerInvoked ? "handler-invocation-outcome-unknown" : "handler-not-invoked"));
    }
    const selected = selectedServerEvidence(input, error, record => boundaryObservations.push(record));
    if (selected.diagnosticRecord !== undefined && boundary !== undefined) boundaryObservations.push(boundary);
    const observedFailure = { ...failure, ...(boundary === undefined ? {} : { diagnosticRecord: boundary }), ...selected };
    return finish(
      errorResponse(failure, headers, middleware),
      routeName,
      selected.diagnosticRecord === undefined ? observedFailure : error,
    );
  }
}

async function admitPlatformServerTransportRequest(
  input: PlatformServerRequestHandlingInput & { readonly request: PlatformServerRequest },
): Promise<PlatformServerTransportAdmission> {
  const requestId = input.request.requestId ?? platformServerRequestId(firstHeaderValue(input.request.headers ?? {}, "x-request-id"));
  try {
    const rateLimit = await observePlatformRateLimitCheck(input.rateLimiter, platformRateLimitKey({
      ...(input.request.clientAddress === undefined ? {} : { clientAddress: input.request.clientAddress }),
    }), { boundary: "transport", keyCategory: input.request.clientAddress === undefined || input.request.clientAddress.length === 0 ? "anonymous" : "client-address" });
    if (rateLimit.allowed) {
      return { requestId };
    }

    const error = platformRateLimitError(rateLimit.retryAfterMs);
    const response = handlePlatformServerTransportFailure({
      ...input,
      failure: {
        method: input.request.method,
        path: input.request.path,
        headers: input.request.headers ?? {},
        requestId,
        status: 429,
        code: "PLATFORM_SERVER_RATE_LIMITED",
        message: error.defaultMessage,
        error: { diagnosticRecord: securityFailureDiagnosticRecord(rateLimit) },
        ...(rateLimit.retryAfterMs === undefined ? {} : { retryAfterMs: rateLimit.retryAfterMs }),
      },
    });
    return { requestId, response };
  } catch (error) {
    return {
      requestId,
      response: handlePlatformServerTransportFailure({
        ...input,
        failure: {
          method: input.request.method,
          path: input.request.path,
          headers: input.request.headers ?? {},
          requestId,
          status: 503,
          code: "PLATFORM_SERVER_SERVICE_UNAVAILABLE",
          message: "The platform rate-limit service is unavailable.",
          error,
        },
      }),
    };
  }
}

function handlePlatformServerTransportFailure(
  input: PlatformServerRequestHandlingInput & { readonly failure: PlatformServerTransportFailure },
): PlatformServerResponse {
  let startedAt: Date;
  try { startedAt = input.deps.clock.now(); }
  catch (error) { reportServerObservationFailure(serverObservationDiagnostics(input, input.failure, undefined), "clock", error); throw error; }
  const routeMatch = routeMatchForTransportFailure(input.routes, input.failure);
  const profile = routeMatch === undefined
    ? undefined
    : serverProfileForRoute(routeMatch.route.registration, input.profilesByName);
  const observations = serverObservationDiagnostics(input, input.failure, profile);
  const traceSpan = profile === undefined
    ? routeMatch === undefined
      ? startPlatformTraceSpan(input.tracer, {
        name: "platform.server.request",
        attributes: serverObservationProjection(observations, "trace-projection", () => ({ method: input.failure.method })),
      }, undefined, observations)
      : undefined
    : platformProfileAllowsSignal(profile, "trace")
      ? startPlatformTraceSpan(input.tracer, { name: "platform.server.request" }, profile, observations)
      : undefined;
  const requestOrigin = firstHeaderValue(input.failure.headers, "origin");
  const headers = platformResponseHeaders({
    requestId: input.failure.requestId,
    ...(requestOrigin === undefined ? {} : { requestOrigin }),
    ...(input.corsOrigin === undefined ? {} : { corsOrigin: input.corsOrigin }),
    ...(input.corsAllowlist === undefined ? {} : { corsAllowlist: input.corsAllowlist }),
  });
  const allowedMethods = input.failure.allow
    ?? (input.failure.code === "PLATFORM_SERVER_METHOD_NOT_ALLOWED"
      ? allowedMethodsForPath(input.routes, input.failure.path)
      : undefined);
  const responseHeaders = {
    ...headers,
    ...(allowedMethods === undefined || allowedMethods.length === 0 ? {} : { allow: [...allowedMethods, "OPTIONS"].join(", ") }),
    ...(input.failure.retryAfterMs === undefined ? {} : { "retry-after": String(Math.max(1, Math.ceil(input.failure.retryAfterMs / 1_000)) ) }),
  };
  const error = serverError(input.failure.code, input.failure.status, input.failure.message);
  if (profile === undefined ? routeMatch === undefined && unmatchedSecurityPathAllowsDiagnostics(input, input.failure.path) : platformProfileAllowsSignal(profile, "operational_log")) {
    if (input.failure.diagnosticRecord !== undefined) reportPlatformDiagnostic(diagnosticsFor(input), input.failure.diagnosticRecord, { capability: "platform-server", operation: "transport", stage: "request", correlationId: input.failure.requestId });
    const retained = securityFailureDiagnosticRecord(input.failure.error);
    if (retained !== undefined) reportPlatformErrorDiagnostic(diagnosticsFor(input), { diagnosticRecord: retained, relatedDiagnosticRecords: securityDiagnosticRecordsFrom(input.failure.error).slice(1) }, { capability: "security", operation: "transport-admission", stage: "request", correlationId: input.failure.requestId });
    else {
      const evidence = selectedServerEvidence(input, input.failure.error, record => reportPlatformDiagnostic(diagnosticsFor(input), record,
        { capability: "platform-server", operation: "transport", stage: "request", correlationId: input.failure.requestId }));
      if (evidence.diagnosticRecord !== undefined || evidence.relatedDiagnosticRecords !== undefined) reportPlatformErrorDiagnostic(diagnosticsFor(input), evidence, { capability: "platform-server", operation: "transport", stage: "request", correlationId: input.failure.requestId });
    }
  }
  const response = errorResponse(error, responseHeaders, [
    "request-id",
    "request-logging",
    "cors",
    "security-headers",
    "rate-limit",
    "parse",
    "error-mapping",
    "response-logging",
  ]);
  if (profile !== undefined && routeMatch !== undefined) {
    recordServerProfileObservation({
      observations,
      metricDiagnostics: input.metricDiagnostics,
      deps: input.deps,
      logger: input.logger,
      profile,
      method: routeMatch.route.registration.method,
      response,
      startedAt,
      error: input.failure.error ?? error,
    });
    endServerProfileTrace({
      observations,
      profile,
      span: traceSpan,
      method: routeMatch.route.registration.method,
      response,
      error: input.failure.error ?? error,
    });
  } else if (routeMatch === undefined && traceSpan !== undefined) {
    const errorClass = serverObservationProjection(observations, "error-class", () => input.failure.error === undefined ? input.failure.code : platformErrorClass(input.failure.error, { errorClasses: serverDiagnosticErrorCodes }));
    const latencyMs = serverObservationElapsed(observations, startedAt, serverObservationProjection(observations, "clock", () => input.deps.clock.now()));
    serverObservationProjection(observations, "metric-projection", () => recordPlatformRequestMetric(input.deps.metrics, input.deps.clock, {
      method: input.failure.method,
      route: "platform.transport",
      status: response.status,
      latencyMs,
      errorClass,
    }, unmatchedSecurityPathAllowsDiagnostics(input, input.failure.path) ? { binding: input.metricDiagnostics, operation: "request" } : undefined, { errorClasses: serverDiagnosticErrorCodes }, observations));
    serverObservationProjection(observations, "log-projection", () => writePlatformLog(input.logger, {
      level: response.status >= 500 ? "error" : "warn",
      message: "platform.server.request",
      correlationId: input.failure.requestId,
      fields: {
        ...platformTraceFields({
          requestId: input.failure.requestId,
          correlationId: input.failure.requestId,
          route: "platform.transport",
          latencyMs,
          errorClass,
        }, { errorClasses: serverDiagnosticErrorCodes }, observations),
        method: input.failure.method,
        status: response.status,
      },
      ...(input.failure.error === undefined ? {} : { error: input.failure.error }),
    }, { errorClasses: serverDiagnosticErrorCodes }, observations));
    serverObservationProjection(observations, "trace-projection", () => endPlatformTraceSpan(traceSpan, {
      outcome: traceOutcomeForResponse(response.status),
      attributes: {
        method: input.failure.method,
        route: "platform.transport",
        status: response.status,
        latencyMs,
        errorClass,
      },
    }, { errorClasses: serverDiagnosticErrorCodes }, observations));
  }
  return response;
}

function serverProfileForRoute(
  route: PlatformRouteRegistration,
  profilesByName: ReadonlyMap<string, PlatformCapabilityObservabilityProfile>,
): PlatformCapabilityObservabilityProfile | undefined {
  if (route.observability.kind !== "profile") {
    return undefined;
  }

  const profile = profilesByName.get(String(route.observability.profile));
  return profile === undefined ? undefined : { ...profile,
    errorClasses: Object.freeze([...new Set([...serverDiagnosticErrorCodes, ...(platformErrorClassDeclarations(profile) ?? [])])]) };
}

function routeMatchForTransportFailure(
  routes: readonly CompiledRoute[],
  failure: PlatformServerTransportFailure,
): { readonly route: CompiledRoute; readonly params: Readonly<Record<string, string>> } | undefined {
  if (!isPlatformRouteMethod(failure.method)) {
    return undefined;
  }

  return findRoute(routes, { method: failure.method, path: failure.path });
}

function isPlatformRouteMethod(value: string): value is PlatformRouteRegistration["method"] {
  return value === "GET"
    || value === "POST"
    || value === "PUT"
    || value === "PATCH"
    || value === "DELETE";
}

function recordServerProfileObservation(input: {
  readonly observations: PlatformObservationDiagnostics | undefined;
  readonly metricDiagnostics: PlatformMetricDiagnosticBinding;
  readonly deps: PlatformMountDeps;
  readonly logger: Logger;
  readonly profile: PlatformCapabilityObservabilityProfile;
  readonly method: PlatformRouteRegistration["method"];
  readonly response: PlatformServerResponse;
  readonly startedAt: Date;
  readonly error?: unknown;
}): void {
  let phase: PlatformObservationBoundaryDetail["phase"] = "profile-projection";
  try {
  const nomenclature = serverNomenclature(input.profile, input.method, input.response.status, input.error, () => { phase = "error-class"; });
  phase = "profile-projection";
  if (platformProfileAllowsSignal(input.profile, "operational_log")) {
    phase = "log-projection";
    writePlatformLog(input.logger, {
      level: serverLogLevel(input.response.status),
      message: "platform.server.request",
      fields: platformProfileLogFields(input.profile, nomenclature),
    }, input.profile, input.observations);
  }

  phase = "profile-projection";
  if (!platformProfileAllowsSignal(input.profile, "metric")) {
    return;
  }

  phase = "metric-projection";
  const labels = platformProfileMetricLabels(input.profile, nomenclature);
  const diagnostics = platformProfileAllowsSignal(input.profile, "operational_log") ? input.metricDiagnostics : undefined;
  recordPlatformMetric(input.deps.metrics, input.deps.clock, {
    name: "platform.server.request.outcome",
    labels,
  }, diagnostics === undefined ? undefined : { binding: diagnostics, operation: "request-outcome" }, input.observations);

  phase = "profile-projection";
  if (platformProfileMeasuresLatency(input.profile, "request_response_latency")) {
    phase = "metric-projection";
    recordPlatformMetric(input.deps.metrics, input.deps.clock, {
      name: "platform.server.request_response_latency",
      kind: "timer",
      value: elapsedMilliseconds(input.startedAt, (() => { phase = "clock"; const finished = input.deps.clock.now(); phase = "elapsed-computation"; return finished; })()),
      unit: "ms",
      labels,
    }, diagnostics === undefined ? undefined : { binding: diagnostics, operation: "request-latency" }, input.observations);
  }
  } catch (error) {
    reportServerObservationFailure(input.observations, phase, error, input.error);
    throw error;
  }
}

function endServerProfileTrace(input: {
  readonly observations: PlatformObservationDiagnostics | undefined;
  readonly profile: PlatformCapabilityObservabilityProfile;
  readonly span: TraceSpan | undefined;
  readonly method: PlatformRouteRegistration["method"];
  readonly response: PlatformServerResponse;
  readonly error?: unknown;
}): void {
  if (input.span === undefined) {
    return;
  }

  let phase: PlatformObservationBoundaryDetail["phase"] = "profile-projection";
  try {
  const nomenclature = serverNomenclature(input.profile, input.method, input.response.status, input.error, () => { phase = "error-class"; });
  phase = "trace-projection";
  endPlatformTraceSpan(input.span, {
    outcome: traceOutcomeForOperationalOutcome(nomenclature.outcome),
    attributes: platformProfileTraceFields(input.profile, nomenclature),
  }, input.profile, input.observations);
  } catch (error) {
    reportServerObservationFailure(input.observations, phase, error, input.error);
    throw error;
  }
}

function serverNomenclature(
  profile: PlatformCapabilityObservabilityProfile,
  method: PlatformRouteRegistration["method"],
  status: number,
  error: unknown | undefined,
  beforeErrorClass?: () => void,
): PlatformOperationalNomenclature {
  return {
    capability: profile.capability,
    action: profile.action,
    executionContext: "server",
    httpMethod: method,
    httpStatusCode: status,
    outcome: operationalOutcomeForResponse(status),
    ...(error === undefined ? {} : { errorClass: (beforeErrorClass?.(), platformErrorClass(error, profile)) }),
  };
}

function serverLogLevel(status: number): "info" | "warn" | "error" {
  return status >= 500 ? "error" : status >= 400 ? "warn" : "info";
}

function operationalOutcomeForResponse(status: number): PlatformOperationalOutcome {
  if (status === 202) {
    return "accepted";
  }

  if (status === 401 || status === 403) {
    return "denied";
  }

  if (status === 408 || status === 504) {
    return "timed_out";
  }

  if (status >= 500) {
    return "failed";
  }

  if (status >= 400) {
    return "rejected";
  }

  return "succeeded";
}

function traceOutcomeForOperationalOutcome(outcome: PlatformOperationalOutcome): "succeeded" | "rejected" | "failed" {
  if (outcome === "succeeded" || outcome === "accepted") {
    return "succeeded";
  }

  if (outcome === "denied" || outcome === "rejected" || outcome === "cancelled") {
    return "rejected";
  }

  return "failed";
}

function traceOutcomeForResponse(status: number): "succeeded" | "rejected" | "failed" {
  return traceOutcomeForOperationalOutcome(operationalOutcomeForResponse(status));
}

function findRoute(routes: readonly CompiledRoute[], request: PlatformServerRequest, onDiagnostic?: (record: DiagnosticRecord) => void): { readonly route: CompiledRoute; readonly params: Readonly<Record<string, string>> } | undefined {
  for (const route of routes) {
    if (route.registration.method !== request.method) {
      continue;
    }

    const match = route.pattern.exec(request.path);
    if (match === null) {
      continue;
    }

    return {
      route,
      params: Object.fromEntries(route.params.map((name, index) => {
        try { return [name, decodeURIComponent(match[index + 1] ?? "")]; }
        catch (error) {
          onDiagnostic?.(captureServerDiagnostic(() => serverRequestBoundaryRecord("route-parameter-decoding", "handler-not-invoked", index)));
          throw error;
        }
      })),
    };
  }

  return undefined;
}

function allowedMethodsForPath(routes: readonly CompiledRoute[], path: string): readonly PlatformRouteRegistration["method"][] {
  if (path === "/livez" || path === "/readyz") {
    return ["GET"];
  }

  return routes
    .filter((route) => route.pattern.test(path))
    .map((route) => route.registration.method)
    .filter((method, index, methods) => methods.indexOf(method) === index);
}

function compileRoute(route: PlatformRouteRegistration): CompiledRoute {
  const params: string[] = [];
  const pattern = route.path
    .split("/")
    .map((segment) => {
      if (segment.startsWith(":")) {
        params.push(segment.slice(1));
        return "([^/]+)";
      }

      return escapeRegExp(segment);
    })
    .join("/");

  return {
    registration: route,
    pattern: new RegExp(`^${pattern}$`),
    params,
  };
}

function response(
  status: number,
  body: unknown,
  headers: Readonly<Record<string, string>>,
  middleware: readonly PlatformServerMiddlewareStep[],
): PlatformServerResponse {
  return {
    status,
    body,
    headers,
    middleware: [...middleware],
  };
}

function errorResponse(
  error: PlatformServerError,
  headers: Readonly<Record<string, string>>,
  middleware: readonly PlatformServerMiddlewareStep[],
): PlatformServerResponse {
  return response(error.status, { error: { code: error.code, message: error.defaultMessage, details: error.details ?? {} } }, headers, middleware);
}

function rateLimitErrorResponse(
  error: ReturnType<typeof platformRateLimitError>,
  headers: Readonly<Record<string, string>>,
  middleware: readonly PlatformServerMiddlewareStep[],
): PlatformServerResponse {
  return errorResponse(
    serverError("PLATFORM_SERVER_RATE_LIMITED", 429, error.defaultMessage, error.details),
    {
      ...headers,
      ...(error.details?.["retryAfterMs"] === undefined
        ? {}
        : { "retry-after": String(Math.max(1, Math.ceil(Number(error.details["retryAfterMs"]) / 1_000))) }),
    },
    middleware,
  );
}

function platformResponseHeaders(input: {
  readonly requestId: CorrelationId;
  readonly requestOrigin?: string;
  readonly corsOrigin?: string;
  readonly corsAllowlist?: readonly string[];
}): Readonly<Record<string, string>> {
  return {
    ...createPlatformSecurityHeaders({
      cors: corsPolicyForRequestOrigin({
        ...(input.requestOrigin === undefined ? {} : { requestOrigin: input.requestOrigin }),
        allowedOrigins: input.corsAllowlist ?? (input.corsOrigin === undefined ? [] : [input.corsOrigin]),
      }),
    }),
    "x-request-id": input.requestId,
  };
}

function mergeApplicationResponseHeaders(
  platformHeaders: Readonly<Record<string, string>>,
  applicationHeaders: Readonly<Record<string, string>> | undefined,
): Readonly<Record<string, string>> {
  if (applicationHeaders === undefined) {
    return platformHeaders;
  }

  return {
    ...platformHeaders,
    ...Object.fromEntries(
      Object.entries(applicationHeaders).filter(([name]) => !platformOwnedResponseHeaders.has(name.toLowerCase())),
    ),
  };
}

function serverError(
  code: PlatformServerErrorCode,
  status: number,
  defaultMessage: string,
  details?: Readonly<Record<string, JsonValue>>,
): PlatformServerError {
  return {
    code,
    status,
    defaultMessage,
    diagnosticRecord: captureServerDiagnostic(() => serverDiagnosticRecord(code)),
    ...(details === undefined ? {} : { details }),
  };
}

function diagnosticsFor(input: PlatformServerRequestHandlingInput) {
  // Shell construction always injects this; the guard also supports direct test helpers.
  return input.deps.diagnostics ?? { report: () => ({ status: "unavailable" as const }) };
}

function serverObservationDiagnostics(input: PlatformServerRequestHandlingInput, requestInput: ServerDiagnosticRequest,
  profile: PlatformCapabilityObservabilityProfile | undefined): PlatformObservationDiagnostics | undefined {
  try {
    const request = diagnosticRequestData(requestInput);
    if (request === undefined) return undefined;
    if (profile === undefined ? !unmatchedSecurityPathAllowsDiagnostics(input, request.path) : !platformProfileAllowsSignal(profile, "operational_log")) return undefined;
    return { reporter: diagnosticsFor(input), get definitions() { return input.selectDiagnosticDefinitions(); },
      context: { capability: "platform-server", operation: "request-observation", stage: "request",
        ...(request.requestId === undefined ? {} : { correlationId: request.requestId }) } };
  } catch { return undefined; }
}

function reportServerObservationFailure(options: PlatformObservationDiagnostics | undefined,
  phase: PlatformObservationBoundaryDetail["phase"], error: unknown, original?: unknown): void {
  reportPlatformObservationBoundary(options, { operation: "request-observation", phase, reason: "threw", effect: "observation-incomplete" }, error);
  if (original !== undefined && original !== error) reportPlatformObservationSources(options, original);
}

function serverObservationProjection<T>(options: PlatformObservationDiagnostics | undefined,
  phase: PlatformObservationBoundaryDetail["phase"], action: () => T, original?: unknown): T {
  try { return action(); }
  catch (error) { reportServerObservationFailure(options, phase, error, original); throw error; }
}

function serverObservationElapsed(options: PlatformObservationDiagnostics | undefined, startedAt: Date, finishedAt: Date, original?: unknown): number {
  return serverObservationProjection(options, "elapsed-computation", () => elapsedMilliseconds(startedAt, finishedAt), original);
}

function selectedServerEvidence(input: PlatformServerRequestHandlingInput, value: unknown, onProcessing?: (record: DiagnosticRecord) => unknown) {
  let definitions: readonly DiagnosticDefinition[] = serverBuiltinDiagnosticCatalogs.flatMap(catalog => catalog.definitions);
  try { definitions = [...input.selectDiagnosticDefinitions()]; }
  catch { onProcessing?.(diagnosticProcessingRecord("definition-selection-failed")); }
  return selectDiagnosticEvidenceWithReport(definitions, value, record => onProcessing?.(record));
}

/** Only checked patterns, never an additional parameter decode or business call. */
type ServerDiagnosticRequest = { readonly method: string; readonly path: string; readonly requestId?: CorrelationId };
function diagnosticRequestData(value: ServerDiagnosticRequest): ServerDiagnosticRequest | undefined {
  try {
    const method = Object.getOwnPropertyDescriptor(value, "method");
    const path = Object.getOwnPropertyDescriptor(value, "path");
    const requestId = Object.getOwnPropertyDescriptor(value, "requestId");
    if (method === undefined || !("value" in method) || typeof method.value !== "string"
      || path === undefined || !("value" in path) || typeof path.value !== "string") return undefined;
    return { method: method.value, path: path.value,
      ...(requestId !== undefined && "value" in requestId && typeof requestId.value === "string" ? { requestId: requestId.value as CorrelationId } : {}) };
  } catch { return undefined; }
}
function reportServerRequestObservation(input: PlatformServerRequestHandlingInput, requestInput: ServerDiagnosticRequest, record: DiagnosticRecord): void {
  try {
    const request = diagnosticRequestData(requestInput);
    if (request === undefined) return;
    const route = input.routes.find((candidate) => candidate.registration.method === request.method && candidate.pattern.test(request.path));
    const profile = route === undefined ? undefined : serverProfileForRoute(route.registration, input.profilesByName);
    if (profile === undefined ? route === undefined && unmatchedSecurityPathAllowsDiagnostics(input, request.path) : platformProfileAllowsSignal(profile, "operational_log")) {
      const checked = selectDiagnosticEvidence([...platformServerDiagnosticCatalog.definitions, diagnosticProcessingDefinition()], { diagnosticRecord: record }).diagnosticRecord;
      if (checked !== undefined) reportPlatformDiagnostic(diagnosticsFor(input), checked, { capability: "platform-server", operation: "transport", stage: "request",
        ...(request.requestId === undefined ? {} : { correlationId: request.requestId }) });
    }
  } catch { /* Optional observation cannot affect parsing, admission or routing. */ }
}

function reportServerRequestEvidence(input: PlatformServerRequestHandlingInput, requestInput: ServerDiagnosticRequest, error: unknown): void {
  try {
    const request = diagnosticRequestData(requestInput);
    if (request === undefined) return;
    const route = input.routes.find((candidate) => candidate.registration.method === request.method && candidate.pattern.test(request.path));
    const profile = route === undefined ? undefined : serverProfileForRoute(route.registration, input.profilesByName);
    if (profile === undefined ? route === undefined && unmatchedSecurityPathAllowsDiagnostics(input, request.path) : platformProfileAllowsSignal(profile, "operational_log")) {
      const notices: DiagnosticRecord[] = [];
      reportPlatformErrorDiagnostic(diagnosticsFor(input), selectedServerEvidence(input, error, record => notices.push(record)), { capability: "platform-server", operation: "request", stage: "request",
        ...(request.requestId === undefined ? {} : { correlationId: request.requestId }) });
      for (const record of notices) reportPlatformDiagnostic(diagnosticsFor(input), record, { capability: "platform-server", operation: "request", stage: "request",
        ...(request.requestId === undefined ? {} : { correlationId: request.requestId }) });
    }
  } catch { /* Observation must not replace the original synchronous failure. */ }
}

/** Method-independent requests (including OPTIONS) cannot override a path's opt-out.
 * Mixed-profile paths require every matching route to permit operational logs.
 */
function unmatchedSecurityPathAllowsDiagnostics(input: PlatformServerRequestHandlingInput, path: string): boolean {
  return input.routes.filter((route) => route.pattern.test(path)).every((route) => {
    const profile = serverProfileForRoute(route.registration, input.profilesByName);
    return profile !== undefined && platformProfileAllowsSignal(profile, "operational_log");
  });
}

async function authenticateRequest(auth: PlatformServerAuthHook | undefined, request: PlatformServerRequest): Promise<PlatformServerAuthResult> {
  if (auth === undefined) {
    return { ...denyByDefaultAuthenticationResult, diagnosticRecord: securityOperationDiagnosticRecord("authentication", "hook-unavailable") };
  }

  return auth.authenticate(request);
}

async function authenticateHealthEndpoint(
  auth: PlatformServerAuthHook | undefined,
  request: PlatformServerRequest,
  exposure: PlatformHealthEndpointExposure,
  middleware: PlatformServerMiddlewareStep[],
): Promise<PlatformServerAuthResult> {
  if (exposure === "public") {
    return denyByDefaultAuthenticationResult;
  }

  middleware.push("auth");
  return authenticateRequest(auth, request);
}

function validateServerAuthzMapping(
  auth: PlatformServerAuthHook | undefined,
  declaredPermissions: readonly Permission[],
): Result<void, PlatformServerError> {
  const grantedPermissions = auth?.grantedPermissions?.() ?? [];
  const validation = validateAuthzMappingPermissions(
    {
      claims: [
        {
          claim: "platform:authz-map",
          equals: true,
          permissions: grantedPermissions,
        },
      ],
    },
    declaredPermissions,
  );
  if (validation.ok) {
    return { ok: true, value: undefined };
  }

  return {
    ok: false,
    error: {
      code: "PLATFORM_SERVER_AUTHZ_MAPPING_INVALID",
      defaultMessage: validation.error.defaultMessage,
      status: 500,
      ...(validation.error.diagnosticRecord === undefined ? {} : { diagnosticRecord: validation.error.diagnosticRecord }),
      ...(validation.error.details === undefined ? {} : { details: validation.error.details }),
    },
  };
}

function validateRicherAuthorizationConfiguration(input: {
  readonly routes: readonly PlatformRouteRegistration[];
  readonly tenantResolver?: PlatformTenantResolver;
  readonly hasAuthorizer: boolean;
}): Result<void, PlatformServerError> {
  if (input.tenantResolver === undefined && input.routes.some((route) => route.tenant === "required")) {
    return {
      ok: false,
      error: serverError(
        "PLATFORM_SERVER_TENANT_RESOLVER_REQUIRED",
        500,
        "A tenant resolver is required by a registered route.",
      ),
    };
  }

  if (!input.hasAuthorizer && input.routes.some((route) => route.resourceAuthorization !== undefined)) {
    return {
      ok: false,
      error: serverError(
        "PLATFORM_SERVER_AUTHORIZER_REQUIRED",
        500,
        "An authorizer is required by a registered route.",
      ),
    };
  }

  return { ok: true, value: undefined };
}

function isTenantContext(value: unknown, observe?: (field: "tenant-result" | "tenantId" | "isolationKey", condition: "object-required" | "string-required" | "nonempty-required") => void): value is TenantContext {
  if (typeof value !== "object" || value === null) {
    observe?.("tenant-result", "object-required");
    return false;
  }

  const candidate = value as Readonly<Record<string, unknown>>;
  if (!(typeof candidate["tenantId"] === "string")) { observe?.("tenantId", "string-required"); return false; }
  if (!(candidate["tenantId"].length > 0)) { observe?.("tenantId", "nonempty-required"); return false; }
  if (!(typeof candidate["isolationKey"] === "string")) { observe?.("isolationKey", "string-required"); return false; }
  if (!(candidate["isolationKey"].length > 0)) { observe?.("isolationKey", "nonempty-required"); return false; }
  return true;
}

function isPlatformResourceAuthorizationResolution(value: unknown, observe?: (field: "resource-result" | "resource.kind" | "resource.disclosure", condition: "object-required" | "kind-rejected" | "disclosure-rejected") => void): value is PlatformResourceAuthorizationResolution {
  if (typeof value !== "object" || value === null) {
    observe?.("resource-result", "object-required");
    return false;
  }

  const candidate = value as Readonly<Record<string, unknown>>;
  if (candidate["kind"] === "authorize") {
    return true;
  }

  if (!(candidate["kind"] === "not-found")) { observe?.("resource.kind", "kind-rejected"); return false; }
  if (!(candidate["disclosure"] === "not-found" || candidate["disclosure"] === "forbidden")) { observe?.("resource.disclosure", "disclosure-rejected"); return false; }
  return true;
}

function firstHeaderValue(headers: Readonly<Record<string, string | readonly string[]>>, name: string): string | undefined {
  const entry = Object.entries(headers).find(([key]) => key.toLowerCase() === name.toLowerCase());
  const value = entry?.[1];
  return typeof value === "string" ? value : value?.[0];
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const platformOwnedResponseHeaders = new Set([
  "access-control-allow-credentials",
  "access-control-allow-headers",
  "access-control-allow-methods",
  "access-control-allow-origin",
  "access-control-max-age",
  "allow",
  "content-security-policy",
  "content-type",
  "permissions-policy",
  "referrer-policy",
  "retry-after",
  "vary",
  "x-content-type-options",
  "x-frame-options",
  "x-request-id",
]);
