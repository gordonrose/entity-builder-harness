import { createServer as createNodeServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import type { AddressInfo } from "node:net";
import type { Permission } from "@kanbien/core/authz";
import type { Logger } from "@kanbien/core/logging";
import { correlationId, type CorrelationId, type JsonValue, type Result } from "@kanbien/core/shared";
import {
  type PlatformApp,
  type PlatformMountDeps,
  type PlatformRequest,
  type PlatformResponse,
  type PlatformRouteRegistration,
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
  corsPolicyForOrigin,
  createInMemoryPlatformRateLimiter,
  createPlatformSecurityHeaders,
  denyByDefaultAuthenticationResult,
  platformRateLimitError,
  type PlatformRateLimiter,
} from "@kanbien/platform-security";

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
  | "PLATFORM_SERVER_ROUTE_NOT_FOUND"
  | "PLATFORM_SERVER_METHOD_NOT_ALLOWED"
  | "PLATFORM_SERVER_RATE_LIMITED"
  | "PLATFORM_SERVER_UNAUTHENTICATED"
  | "PLATFORM_SERVER_FORBIDDEN"
  | "PLATFORM_SERVER_INVALID_REQUEST"
  | "PLATFORM_SERVER_HANDLER_FAILED";

export interface PlatformServerError {
  readonly code: PlatformServerErrorCode;
  readonly defaultMessage: string;
  readonly status: number;
  readonly details?: Readonly<Record<string, JsonValue>>;
}

export interface PlatformServerRequest {
  readonly method: PlatformRouteRegistration["method"];
  readonly path: string;
  readonly headers?: Readonly<Record<string, string | readonly string[]>>;
  readonly query?: Readonly<Record<string, string | readonly string[]>>;
  readonly body?: unknown;
}

export interface PlatformServerResponse {
  readonly status: number;
  readonly body?: unknown;
  readonly headers: Readonly<Record<string, string>>;
  readonly middleware: readonly PlatformServerMiddlewareStep[];
}

export interface PlatformServerAuthResult {
  readonly authenticated: boolean;
  readonly permissions?: readonly Permission[];
}

export interface PlatformServerAuthHook {
  authenticate(request: PlatformServerRequest): Promise<PlatformServerAuthResult> | PlatformServerAuthResult;
}

export interface PlatformServerOptions {
  readonly apps: readonly PlatformApp[];
  readonly deps: PlatformMountDeps;
  readonly auth?: PlatformServerAuthHook;
  readonly logger?: Logger;
  readonly corsOrigin?: string;
  readonly rateLimiter?: PlatformRateLimiter;
}

export interface PlatformServerShell {
  readonly mounted: PlatformRuntimeMountResult;
  readonly lifecycle: PlatformRuntimeLifecycleController;
  handle(request: PlatformServerRequest): Promise<PlatformServerResponse>;
  listen(options?: PlatformServerListenOptions): Promise<PlatformServerHandle>;
}

export interface PlatformServerListenOptions {
  readonly port?: number;
  readonly host?: string;
}

export interface PlatformServerHandle {
  readonly port: number;
  readonly host?: string;
  close(): Promise<void>;
}

interface CompiledRoute {
  readonly registration: PlatformRouteRegistration;
  readonly pattern: RegExp;
  readonly params: readonly string[];
}

export async function createPlatformServerShell(options: PlatformServerOptions): Promise<Result<PlatformServerShell, PlatformServerError>> {
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

  return {
    ok: true,
    value: {
      mounted: mounted.value,
      lifecycle,
      handle: (request) => handlePlatformServerRequest({
        request,
        routes,
        deps: options.deps,
        logger,
        rateLimiter,
        lifecycle,
        healthChecks: mounted.value.healthChecks,
        ...(options.corsOrigin === undefined ? {} : { corsOrigin: options.corsOrigin }),
        ...(options.auth === undefined ? {} : { auth: options.auth }),
      }),
      listen: (listenOptions = {}) => listenPlatformServer({
        handle: (request) => handlePlatformServerRequest({
          request,
          routes,
          deps: options.deps,
          logger,
          rateLimiter,
          lifecycle,
          healthChecks: mounted.value.healthChecks,
          ...(options.corsOrigin === undefined ? {} : { corsOrigin: options.corsOrigin }),
          ...(options.auth === undefined ? {} : { auth: options.auth }),
        }),
        options: listenOptions,
      }),
    },
  };
}

async function handlePlatformServerRequest(input: {
  readonly request: PlatformServerRequest;
  readonly routes: readonly CompiledRoute[];
  readonly auth?: PlatformServerAuthHook;
  readonly deps: PlatformMountDeps;
  readonly logger: Logger;
  readonly corsOrigin?: string;
  readonly rateLimiter: PlatformRateLimiter;
  readonly lifecycle: PlatformRuntimeLifecycleController;
  readonly healthChecks: PlatformRuntimeMountResult["healthChecks"];
}): Promise<PlatformServerResponse> {
  const middleware: PlatformServerMiddlewareStep[] = [];
  const startedAt = input.deps.clock.now();
  const requestId = requestIdFromHeaders(input.request.headers ?? {});
  const headers = createPlatformSecurityHeaders({ cors: corsPolicyForOrigin(input.corsOrigin) });

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

    const rateLimit = input.rateLimiter.check("global");
    if (!rateLimit.allowed) {
      middleware.push("error-mapping", "response-logging");
      const error = platformRateLimitError(rateLimit.retryAfterMs);
      return finish(
        errorResponse(serverError("PLATFORM_SERVER_RATE_LIMITED", 429, error.defaultMessage, error.details), headers, middleware),
        "platform.rate-limit",
        error,
      );
    }

    if (input.request.path === "/livez") {
      middleware.push("handler", "response-logging");
      const live = platformLiveness(input.deps.clock);
      recordPlatformHealthMetric(input.deps.metrics, input.deps.clock, { healthState: live.status });
      return finish(response(200, { status: live.status }, headers, middleware), "platform.livez");
    }

    if (input.request.path === "/readyz") {
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
      const error = serverError("PLATFORM_SERVER_ROUTE_NOT_FOUND", 404, "No platform route matched the request.");
      return finish(errorResponse(error, headers, middleware), "unknown", error);
    }

    const { route, params } = routeMatch;
    const routeName = String(route.registration.name);
    middleware.push("auth");
    const auth = await authenticateRequest(input.auth, input.request);
    if (route.registration.auth.kind === "authenticated" && !auth.authenticated) {
      middleware.push("error-mapping", "response-logging");
      const error = serverError("PLATFORM_SERVER_UNAUTHENTICATED", 401, "Authentication is required.");
      return finish(errorResponse(error, headers, middleware), routeName, error);
    }

    middleware.push("context", "authorization");
    if (route.registration.auth.kind === "authenticated") {
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

    middleware.push("validation");
    if (route.registration.validator !== undefined && !route.registration.validator.validate(input.request.body)) {
      middleware.push("error-mapping", "response-logging");
      const error = serverError("PLATFORM_SERVER_INVALID_REQUEST", 400, "Request body failed route validation.");
      return finish(errorResponse(error, headers, middleware), routeName, error);
    }

    middleware.push("handler");
    const context = createPlatformRuntimeRequestContext({
      requestId,
      method: input.request.method,
      path: input.request.path,
      logger: input.deps.logger,
      metrics: input.deps.metrics,
      config: input.deps.config,
      flags: input.deps.flags,
      clock: input.deps.clock,
    });
    const platformRequest: PlatformRequest = {
      params,
      query: input.request.query ?? {},
      headers: input.request.headers ?? {},
      ...(input.request.body === undefined ? {} : { body: input.request.body }),
    };
    const handled = await route.registration.handler.handle(platformRequest, context);

    middleware.push("response-logging");
    return finish(response(handled.status, handled.body, { ...headers, ...(handled.headers ?? {}) }, middleware), routeName);
  } catch (error) {
    middleware.push("error-mapping", "response-logging");
    return finish(
      errorResponse(serverError("PLATFORM_SERVER_HANDLER_FAILED", 500, "Platform route handler failed."), headers, middleware),
      "unknown",
      error,
    );
  }
}

async function listenPlatformServer(input: {
  readonly handle: (request: PlatformServerRequest) => Promise<PlatformServerResponse>;
  readonly options: PlatformServerListenOptions;
}): Promise<PlatformServerHandle> {
  const server = createNodeServer(async (req, res) => {
    const request = await nodeRequestToPlatformRequest(req);
    const platformResponse = await input.handle(request);
    writeNodeResponse(res, platformResponse);
  });

  await new Promise<void>((resolve) => {
    server.listen(input.options.port ?? 0, input.options.host, () => resolve());
  });

  const address = server.address() as AddressInfo;

  return {
    port: address.port,
    ...(input.options.host === undefined ? {} : { host: input.options.host }),
    close: () => closeServer(server),
  };
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

function requestIdFromHeaders(headers: Readonly<Record<string, string | readonly string[]>>): CorrelationId {
  const value = headers["x-request-id"];
  if (typeof value === "string") {
    return correlationId(value);
  }

  return correlationId(value?.[0] ?? defaultRequestId);
}

async function nodeRequestToPlatformRequest(req: IncomingMessage): Promise<PlatformServerRequest> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(typeof chunk === "string" ? Buffer.from(chunk) : chunk);
  }

  const rawBody = Buffer.concat(chunks).toString("utf8");
  const parsedUrl = new URL(req.url ?? "/", "http://localhost");
  const headers = Object.fromEntries(
    Object.entries(req.headers).flatMap(([key, value]) => {
      if (value === undefined) {
        return [];
      }

      return [[key, typeof value === "string" ? value : [...value]]];
    }),
  ) as Readonly<Record<string, string | readonly string[]>>;

  return {
    method: normalizeMethod(req.method),
    path: parsedUrl.pathname,
    headers,
    query: Object.fromEntries(parsedUrl.searchParams.entries()),
    ...(rawBody.length === 0 ? {} : { body: JSON.parse(rawBody) }),
  };
}

function writeNodeResponse(res: ServerResponse, platformResponse: PlatformServerResponse): void {
  for (const [key, value] of Object.entries(platformResponse.headers)) {
    res.setHeader(key, value);
  }

  res.statusCode = platformResponse.status;
  res.end(JSON.stringify(platformResponse.body ?? null));
}

function normalizeMethod(method: string | undefined): PlatformRouteRegistration["method"] {
  switch (method) {
    case "GET":
    case "POST":
    case "PUT":
    case "PATCH":
    case "DELETE":
      return method;
    default:
      return "GET";
  }
}

async function closeServer(server: Server): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    server.close((error) => {
      if (error === undefined) {
        resolve();
        return;
      }

      reject(error);
    });
  });
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const defaultRequestId = "platform-server-request";
