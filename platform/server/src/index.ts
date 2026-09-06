import type { Permission } from "@kanbien/core/authz";
import type { Logger } from "@kanbien/core/logging";
import { type CorrelationId, type JsonValue, type Result } from "@kanbien/core/shared";
import type { TenantContext } from "@kanbien/core/tenancy";
import {
  type PlatformApp,
  type PlatformMountDeps,
  type PlatformRequest,
  type PlatformResourceAuthorizationResolution,
  type PlatformResponse,
  type PlatformRouteRegistration,
  type PlatformTenantResolver,
} from "@kanbien/platform-contracts";
import {
  createPlatformRuntimeLifecycle,
  createPlatformRuntimeRequestContext,
  mountPlatformRuntimeApps,
  type PlatformRuntimeLifecycleController,
  type PlatformRuntimeMountResult,
} from "@kanbien/platform-runtime";
import { assertPlatformConfigValid } from "@kanbien/platform-config";
import { platformHealthHttpStatus, platformLiveness, platformReadiness } from "@kanbien/platform-health";
import {
  elapsedMilliseconds,
  platformErrorClass,
  platformTraceFields,
  recordPlatformHealthMetric,
  recordPlatformRequestMetric,
  writePlatformLog,
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
  readonly apps: readonly PlatformApp[];
  readonly deps: PlatformMountDeps;
  readonly auth?: PlatformServerAuthHook;
  readonly tenantResolver?: PlatformTenantResolver;
  readonly logger?: Logger;
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
  readonly routes: readonly CompiledRoute[];
  readonly auth?: PlatformServerAuthHook;
  readonly tenantResolver?: PlatformTenantResolver;
  readonly deps: PlatformMountDeps;
  readonly logger: Logger;
  readonly corsOrigin?: string;
  readonly corsAllowlist?: readonly string[];
  readonly healthExposure?: PlatformHealthExposurePolicy;
  readonly rateLimiter: PlatformRateLimiter;
  readonly lifecycle: PlatformRuntimeLifecycleController;
  readonly healthChecks: PlatformRuntimeMountResult["healthChecks"];
}

export async function createPlatformServerShell(options: PlatformServerOptions): Promise<Result<PlatformServerShell, PlatformServerError>> {
  const transport = resolvePlatformServerTransportOptions(options.transport);
  if (!transport.ok) {
    return {
      ok: false,
      error: serverError(
        "PLATFORM_SERVER_TRANSPORT_CONFIG_INVALID",
        500,
        "Platform server transport configuration is invalid.",
        { reason: transport.reason },
      ),
    };
  }

  const mounted = await mountPlatformRuntimeApps({
    apps: options.apps,
    deps: options.deps,
  });

  if (!mounted.ok) {
    return {
      ok: false,
      error: {
        code: "PLATFORM_SERVER_MOUNT_FAILED",
        defaultMessage: "Platform server failed to mount apps.",
        status: 500,
        details: { runtimeCode: mounted.error.code },
      },
    };
  }

  const authzMapping = validateServerAuthzMapping(options.auth, mounted.value.permissions.map((permission) => permission.permission));
  if (!authzMapping.ok) {
    return authzMapping;
  }

  const richerAuthorizationConfiguration = validateRicherAuthorizationConfiguration({
    routes: mounted.value.routes,
    hasAuthorizer: options.deps.authorizer !== undefined,
    ...(options.tenantResolver === undefined ? {} : { tenantResolver: options.tenantResolver }),
  });
  if (!richerAuthorizationConfiguration.ok) {
    return richerAuthorizationConfiguration;
  }

  const config = assertPlatformConfigValid({
    source: options.deps.config,
    schemas: mounted.value.configSchemas,
  });
  if (!config.ok) {
    return {
      ok: false,
      error: {
        code: "PLATFORM_SERVER_CONFIG_INVALID",
        defaultMessage: "Platform server config validation failed before listen.",
        status: 500,
        details: config.error.details,
      },
    };
  }

  const lifecycle = createPlatformRuntimeLifecycle({ apps: mounted.value.apps });
  const routes = mounted.value.routes.map(compileRoute);
  const logger = options.logger ?? options.deps.logger;
  const rateLimiter = options.rateLimiter ?? createInMemoryPlatformRateLimiter({ clock: options.deps.clock });
  const requestInput: PlatformServerRequestHandlingInput = {
    routes,
    deps: options.deps,
    logger,
    rateLimiter,
    lifecycle,
    healthChecks: mounted.value.healthChecks,
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
  const startedAt = input.deps.clock.now();
  const requestId = input.request.requestId ?? platformServerRequestId(firstHeaderValue(input.request.headers ?? {}, "x-request-id"));
  const requestOrigin = firstHeaderValue(input.request.headers ?? {}, "origin");
  const headers = platformResponseHeaders({
    requestId,
    ...(requestOrigin === undefined ? {} : { requestOrigin }),
    ...(input.corsOrigin === undefined ? {} : { corsOrigin: input.corsOrigin }),
    ...(input.corsAllowlist === undefined ? {} : { corsAllowlist: input.corsAllowlist }),
  });
  let routeName = "unknown";

  const finish = (
    platformResponse: PlatformServerResponse,
    route: string,
    error?: unknown,
  ): PlatformServerResponse => {
    const latencyMs = elapsedMilliseconds(startedAt, input.deps.clock.now());
    const errorClass = error === undefined ? undefined : platformErrorClass(error);
    recordPlatformRequestMetric(input.deps.metrics, input.deps.clock, {
      method: input.request.method,
      route,
      status: platformResponse.status,
      latencyMs,
      ...(errorClass === undefined ? {} : { errorClass }),
    });
    writePlatformLog(input.logger, {
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
        }),
        method: input.request.method,
        status: platformResponse.status,
      },
      ...(error === undefined ? {} : { error }),
    });

    return platformResponse;
  };

  try {
    middleware.push("request-id", "request-logging", "cors", "security-headers", "rate-limit", "parse");

    if (!input.request.transportAdmissionApplied) {
      const rateLimit = await input.rateLimiter.check(platformRateLimitKey({
        ...(input.request.clientAddress === undefined ? {} : { clientAddress: input.request.clientAddress }),
      }));
      if (!rateLimit.allowed) {
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
      const auth = await authenticateHealthEndpoint(input.auth, input.request, input.healthExposure?.liveness ?? "public", middleware);
      if (!auth.authenticated && (input.healthExposure?.liveness ?? "public") === "authenticated") {
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_UNAUTHENTICATED", 401, "Authentication is required.");
        return finish(errorResponse(error, headers, middleware), "platform.livez", error);
      }
      middleware.push("handler", "response-logging");
      const live = platformLiveness(input.deps.clock);
      recordPlatformHealthMetric(input.deps.metrics, input.deps.clock, { healthState: live.status });
      return finish(response(200, { status: live.status }, headers, middleware), "platform.livez");
    }

    if (input.request.path === "/readyz" && input.request.method === "GET") {
      const auth = await authenticateHealthEndpoint(input.auth, input.request, input.healthExposure?.readiness ?? "public", middleware);
      if (!auth.authenticated && (input.healthExposure?.readiness ?? "public") === "authenticated") {
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_UNAUTHENTICATED", 401, "Authentication is required.");
        return finish(errorResponse(error, headers, middleware), "platform.readyz", error);
      }
      middleware.push("handler", "response-logging");
      const ready = await platformReadiness({
        lifecycleReady: input.lifecycle.isReady(),
        healthChecks: input.healthChecks,
        clock: input.deps.clock,
      });
      recordPlatformHealthMetric(input.deps.metrics, input.deps.clock, { healthState: ready.status });
      return finish(response(platformHealthHttpStatus(ready.status), ready, headers, middleware), "platform.readyz");
    }

    const routeMatch = findRoute(input.routes, input.request);
    if (routeMatch === undefined) {
      middleware.push("error-mapping", "response-logging");
      const allowedMethods = allowedMethodsForPath(input.routes, input.request.path);
      const error = allowedMethods.length === 0
        ? serverError("PLATFORM_SERVER_ROUTE_NOT_FOUND", 404, "No platform route matched the request.")
        : serverError("PLATFORM_SERVER_METHOD_NOT_ALLOWED", 405, "The request method is not allowed.");
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
    const auth = await authenticateRequest(input.auth, input.request);
    const principal = route.registration.auth.kind === "authenticated"
      ? principalFromPlatformAuthenticationResult(auth)
      : undefined;
    if (route.registration.auth.kind === "authenticated" && (!auth.authenticated || principal === undefined)) {
      middleware.push("error-mapping", "response-logging");
      const error = serverError("PLATFORM_SERVER_UNAUTHENTICATED", 401, "Authentication is required.");
      return finish(errorResponse(error, headers, middleware), routeName, error);
    }

    if (route.registration.auth.kind === "authenticated") {
      if (auth.rateLimitKey !== undefined) {
        const principalRateLimit = await input.rateLimiter.check(platformRateLimitKey({ authentication: auth }));
        if (!principalRateLimit.allowed) {
          middleware.push("error-mapping", "response-logging");
          const error = platformRateLimitError(principalRateLimit.retryAfterMs);
          return finish(rateLimitErrorResponse(error, headers, middleware), routeName, error);
        }
      }

      middleware.push("authorization");
      const authorized = authorizePlatformPermissions(route.registration.auth.permissions ?? [], auth.permissions ?? []);
      if (!authorized.ok) {
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_FORBIDDEN", 403, authorized.error.defaultMessage, authorized.error.details);
        return finish(
          errorResponse(error, headers, middleware),
          routeName,
          error,
        );
      }
    }

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
    const tenant = isTenantContext(tenantResolution) ? tenantResolution : undefined;
    if (route.registration.tenant === "required" && (tenant === null || tenant === undefined)) {
      middleware.push("error-mapping", "response-logging");
      const error = serverError("PLATFORM_SERVER_FORBIDDEN", 403, "Access to this route is forbidden.");
      return finish(errorResponse(error, headers, middleware), routeName, error);
    }

    middleware.push("context");
    const context = createPlatformRuntimeRequestContext({
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
    });

    middleware.push("validation");
    if (route.registration.validator !== undefined && !route.registration.validator.validate(input.request.body)) {
      middleware.push("error-mapping", "response-logging");
      const error = serverError("PLATFORM_SERVER_INVALID_REQUEST", 400, "Request body failed route validation.");
      return finish(errorResponse(error, headers, middleware), routeName, error);
    }

    if (route.registration.resourceAuthorization !== undefined) {
      middleware.push("authorization");
      const resourceResolution = await route.registration.resourceAuthorization.resolve({
        request: platformRequest,
        context,
      });
      if (!isPlatformResourceAuthorizationResolution(resourceResolution)) {
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_FORBIDDEN", 403, "Access to this resource is forbidden.");
        return finish(errorResponse(error, headers, middleware), routeName, error);
      }
      if (resourceResolution.kind === "not-found") {
        middleware.push("error-mapping", "response-logging");
        const error = resourceResolution.disclosure === "forbidden"
          ? serverError("PLATFORM_SERVER_FORBIDDEN", 403, "Access to this resource is forbidden.")
          : serverError("PLATFORM_SERVER_RESOURCE_NOT_FOUND", 404, "The requested resource was not found.");
        return finish(errorResponse(error, headers, middleware), routeName, error);
      }

      const authorizer = input.deps.authorizer;
      if (authorizer === undefined || principal === undefined) {
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
        middleware.push("error-mapping", "response-logging");
        const error = serverError("PLATFORM_SERVER_FORBIDDEN", 403, "Access to this resource is forbidden.");
        return finish(errorResponse(error, headers, middleware), routeName, error);
      }
    }

    middleware.push("handler");
    const handled = await route.registration.handler.handle(platformRequest, context);

    middleware.push("response-logging");
    return finish(response(handled.status, handled.body, mergeApplicationResponseHeaders(headers, handled.headers), middleware), routeName);
  } catch (error) {
    middleware.push("error-mapping", "response-logging");
    return finish(
      errorResponse(serverError("PLATFORM_SERVER_HANDLER_FAILED", 500, "Platform route handler failed."), headers, middleware),
      routeName,
      error,
    );
  }
}

async function admitPlatformServerTransportRequest(
  input: PlatformServerRequestHandlingInput & { readonly request: PlatformServerRequest },
): Promise<PlatformServerTransportAdmission> {
  const requestId = input.request.requestId ?? platformServerRequestId(firstHeaderValue(input.request.headers ?? {}, "x-request-id"));
  try {
    const rateLimit = await input.rateLimiter.check(platformRateLimitKey({
      ...(input.request.clientAddress === undefined ? {} : { clientAddress: input.request.clientAddress }),
    }));
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
  const startedAt = input.deps.clock.now();
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
  const errorClass = input.failure.error === undefined ? input.failure.code : platformErrorClass(input.failure.error);
  const latencyMs = elapsedMilliseconds(startedAt, input.deps.clock.now());
  recordPlatformRequestMetric(input.deps.metrics, input.deps.clock, {
    method: input.failure.method,
    route: "platform.transport",
    status: response.status,
    latencyMs,
    errorClass,
  });
  writePlatformLog(input.logger, {
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
      }),
      method: input.failure.method,
      status: response.status,
    },
    ...(input.failure.error === undefined ? {} : { error: input.failure.error }),
  });
  return response;
}

function findRoute(routes: readonly CompiledRoute[], request: PlatformServerRequest): { readonly route: CompiledRoute; readonly params: Readonly<Record<string, string>> } | undefined {
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
      params: Object.fromEntries(route.params.map((name, index) => [name, decodeURIComponent(match[index + 1] ?? "")])),
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
    ...(details === undefined ? {} : { details }),
  };
}

async function authenticateRequest(auth: PlatformServerAuthHook | undefined, request: PlatformServerRequest): Promise<PlatformServerAuthResult> {
  if (auth === undefined) {
    return denyByDefaultAuthenticationResult;
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

function isTenantContext(value: unknown): value is TenantContext {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Readonly<Record<string, unknown>>;
  return typeof candidate["tenantId"] === "string"
    && candidate["tenantId"].length > 0
    && typeof candidate["isolationKey"] === "string"
    && candidate["isolationKey"].length > 0;
}

function isPlatformResourceAuthorizationResolution(value: unknown): value is PlatformResourceAuthorizationResolution {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Readonly<Record<string, unknown>>;
  if (candidate["kind"] === "authorize") {
    return true;
  }

  return candidate["kind"] === "not-found"
    && (candidate["disclosure"] === "not-found" || candidate["disclosure"] === "forbidden");
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
