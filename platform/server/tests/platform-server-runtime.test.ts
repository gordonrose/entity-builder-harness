import { deepEqual, equal, notEqual } from "node:assert/strict";
import { request as nodeHttpRequest } from "node:http";
import type { Principal } from "@kanbien/core/authn";
import {
  allow,
  deny,
  resourceRef,
  type AuthorizationRequest,
  type Permission,
} from "@kanbien/core/authz";
import { configError, type ConfigSchema } from "@kanbien/core/config";
import { createInMemoryTracer } from "@kanbien/core/monitoring";
import { messageDescriptor } from "@kanbien/core/shared";
import { tenantContext, tenantId, type TenantContext } from "@kanbien/core/tenancy";
import { validationIssue } from "@kanbien/core/validation";
import {
  definePlatformApp,
  platformAppId,
  platformCapabilityName,
  platformObservabilityProfileName,
  platformRouteName,
} from "@kanbien/platform-contracts";
import {
  createPlatformTestLogger,
  createPlatformTestMetrics,
  createPlatformTestMountDeps,
  validatorForTest,
} from "@kanbien/platform-testing";
import { createPlatformServerShell } from "../src/index";
import { startPlatformServerProcess } from "../src/main";

async function main(): Promise<void> {
  const appId = platformAppId("smoke");
  const routeName = platformRouteName("smoke.echo");
  const publicRouteName = platformRouteName("smoke.public");
  const failedRouteName = platformRouteName("smoke.operation-failed");
  const slowRouteName = platformRouteName("smoke.slow");
  const optOutRouteName = platformRouteName("smoke.opt-out");
  const tenantRouteName = platformRouteName("smoke.tenant");
  const resourceRouteName = platformRouteName("smoke.resource");
  const observabilityProfileName = platformObservabilityProfileName("smoke.request");
  const capabilityName = platformCapabilityName("smoke.request");
  if (!appId.ok || !routeName.ok || !publicRouteName.ok || !failedRouteName.ok || !slowRouteName.ok || !optOutRouteName.ok || !tenantRouteName.ok || !resourceRouteName.ok || !observabilityProfileName.ok || !capabilityName.ok) {
    throw new Error("Expected valid server test primitives.");
  }

  const permission = "smoke.smoke:read" as Permission;
  const tenantPermission = "smoke.tenant:read" as Permission;
  const resourcePermission = "smoke.record:read" as Permission;
  const testObservability = { kind: "profile", profile: observabilityProfileName.value } as const;
  const optOutObservability = { kind: "opt_out", reason: "non_user_workload_path", justification: "The opt-out fixture proves an explicit exception does not emit capability telemetry." } as const;
  const logger = createPlatformTestLogger();
  const metrics = createPlatformTestMetrics();
  const tracer = createInMemoryTracer();
  let authenticatedPrincipal: Principal | undefined;
  let publicRoutePrincipal: Principal | undefined;
  let requiredTenantContext: TenantContext | undefined;
  let resourceTenantContext: TenantContext | undefined;
  let resourcePrincipal: Principal | undefined;
  let protectedHandlerCalls = 0;
  let requiredTenantHandlerCalls = 0;
  let resourceHandlerCalls = 0;
  let tenantResolverCalls = 0;
  let resourceResolutionCalls = 0;
  let resolveSlowHandler: (() => void) | undefined;
  const authorizationRequests: AuthorizationRequest[] = [];
  const deps = {
    ...createPlatformTestMountDeps({ logger, metrics }),
    authorizer: {
      decide: async (request: AuthorizationRequest) => {
        authorizationRequests.push(request);
        if (request.resource?.id === "denied") {
          return deny({
            reason: messageDescriptor({ code: "authorization.denied", defaultMessage: "Access is denied." }),
            evidence: { internal: "do-not-return" },
          });
        }

        return allow({ evidence: { internal: "do-not-return" } });
      },
    },
  };
  const tenantResolver = {
    resolve: async ({ principal }: { readonly principal: Principal }) => {
      tenantResolverCalls += 1;
      if (principal.subject === "subject-tenantless") {
        return null;
      }
      if (principal.subject === "subject-malformed-tenant") {
        return {} as never;
      }

      return tenantContext({ tenantId: tenantId("tenant-benelux") });
    },
  };
  const app = definePlatformApp({
    id: appId.value,
    name: "Smoke",
    mount(registry) {
      registry.registerObservabilityProfile({
        name: observabilityProfileName.value,
        capability: capabilityName.value,
        action: "execute",
        signals: ["operational_log", "metric", "trace"],
        logFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
        metricDimensionFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
        traceAttributeNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
        nfrObjectives: [{ nfrClass: "interactive_command", measurement: "request_response_latency" }],
      });
      registry.registerPermission({ permission });
      registry.registerPermission({ permission: tenantPermission });
      registry.registerPermission({ permission: resourcePermission });
      registry.registerRoute({
        name: publicRouteName.value,
        method: "GET",
        path: "/public",
        auth: { kind: "public" },
        observability: testObservability,
        handler: {
          handle: (_request, context) => {
            publicRoutePrincipal = context.principal;
            return {
              status: 200,
              body: { public: true },
              headers: {
                "content-security-policy": "default-src *",
                "x-app-visible": "allowed",
                "x-request-id": "app-must-not-control-this",
              },
            };
          },
        },
      });
      registry.registerRoute({
        name: failedRouteName.value,
        method: "POST",
        path: "/operation-failed",
        auth: { kind: "public" },
        observability: testObservability,
        handler: {
          handle: () => ({
            status: 503,
            body: { status: "not-accepted" },
            observability: { errorClass: "SMOKE_OPERATION_NOT_ACCEPTED" },
          }),
        },
      });
      registry.registerRoute({
        name: slowRouteName.value,
        method: "GET",
        path: "/slow",
        auth: { kind: "public" },
        observability: testObservability,
        handler: {
          handle: () => new Promise((resolve) => {
            resolveSlowHandler = () => {
              resolve({ status: 200, body: { slow: "settled" } });
            };
          }),
        },
      });
      registry.registerRoute({
        name: optOutRouteName.value,
        method: "GET",
        path: "/opt-out",
        auth: { kind: "public" },
        observability: optOutObservability,
        handler: {
          handle: () => ({ status: 204 }),
        },
      });
      registry.registerRoute({
        name: routeName.value,
        method: "POST",
        path: "/echo/:id",
        auth: { kind: "authenticated", permissions: [permission] },
        observability: testObservability,
        validator: validatorForTest((value): value is { readonly message: string } =>
          typeof value === "object"
          && value !== null
          && "message" in value
          && typeof (value as { readonly message?: unknown }).message === "string"),
        handler: {
          handle: (request, context) => {
            protectedHandlerCalls += 1;
            authenticatedPrincipal = context.principal;
            return {
              status: 200,
              body: { id: request.params["id"], message: (request.body as { readonly message: string }).message },
            };
          },
        },
      });
      registry.registerRoute({
        name: tenantRouteName.value,
        method: "GET",
        path: "/tenant",
        auth: { kind: "authenticated", permissions: [tenantPermission] },
        observability: testObservability,
        tenant: "required",
        handler: {
          handle: (_request, context) => {
            requiredTenantHandlerCalls += 1;
            requiredTenantContext = context.tenant;
            return { status: 200, body: { tenant: String(context.tenant?.tenantId) } };
          },
        },
      });
      registry.registerRoute({
        name: resourceRouteName.value,
        method: "GET",
        path: "/records/:id",
        auth: { kind: "authenticated", permissions: [resourcePermission] },
        observability: testObservability,
        tenant: "required",
        resourceAuthorization: {
          permission: resourcePermission,
          resolve: ({ request }) => {
            resourceResolutionCalls += 1;
            const id = request.params["id"] ?? "";
            if (id === "missing") {
              return { kind: "not-found", disclosure: "not-found" };
            }
            if (id === "hidden") {
              return { kind: "not-found", disclosure: "forbidden" };
            }
            if (id === "malformed") {
              return { kind: "malformed" } as never;
            }

            return {
              kind: "authorize",
              resource: resourceRef({ type: "record", id }),
              facts: { source: "test" },
            };
          },
        },
        handler: {
          handle(_request, context) {
            resourceHandlerCalls += 1;
            resourceTenantContext = context.tenant;
            resourcePrincipal = context.principal;
            return { status: 200, body: { allowed: true } };
          },
        },
      });
    },
  });

  const auth = {
    grantedPermissions: () => [permission, tenantPermission, resourcePermission],
    authenticate: (request: { readonly headers?: Readonly<Record<string, string | readonly string[]>> }) => {
      if (request.headers?.authorization === "Bearer ok") {
        return {
          authenticated: true,
          permissions: [permission, tenantPermission, resourcePermission],
          principalId: "principal-ok",
          principalType: "user" as const,
          subject: "subject-ok",
          claims: { sub: "subject-ok", "custom:role": "operator" },
          scopes: ["openid", "platform-smoke/read"],
          rateLimitKey: "principal:subject-ok",
        };
      }
      if (request.headers?.authorization === "Bearer tenantless") {
        return {
          authenticated: true,
          permissions: [tenantPermission],
          principalId: "principal-tenantless",
          principalType: "user" as const,
          subject: "subject-tenantless",
        };
      }
      if (request.headers?.authorization === "Bearer malformed-tenant") {
        return {
          authenticated: true,
          permissions: [tenantPermission],
          principalId: "principal-malformed-tenant",
          principalType: "user" as const,
          subject: "subject-malformed-tenant",
        };
      }
      if (request.headers?.authorization === "Bearer no-permission") {
        return {
          authenticated: true,
          permissions: [],
          principalId: "principal-no-permission",
          principalType: "user" as const,
          subject: "subject-no-permission",
          rateLimitKey: "principal:subject-no-permission",
        };
      }
      return { authenticated: false, permissions: [] };
    },
  };

  const shell = await createPlatformServerShell({
    apps: [app],
    deps,
    tracer,
    auth,
    tenantResolver,
    corsAllowlist: ["https://app.example.test"],
  });
  equal(shell.ok, true);
  if (!shell.ok) {
    throw new Error("Expected server shell to mount.");
  }

  const missingTenantResolverShell = await createPlatformServerShell({
    apps: [app],
    deps,
    auth,
  });
  equal(missingTenantResolverShell.ok, false);
  if (!missingTenantResolverShell.ok) {
    equal(missingTenantResolverShell.error.code, "PLATFORM_SERVER_TENANT_RESOLVER_REQUIRED");
  }

  const missingAuthorizerShell = await createPlatformServerShell({
    apps: [app],
    deps: createPlatformTestMountDeps(),
    auth,
    tenantResolver,
  });
  equal(missingAuthorizerShell.ok, false);
  if (!missingAuthorizerShell.ok) {
    equal(missingAuthorizerShell.error.code, "PLATFORM_SERVER_AUTHORIZER_REQUIRED");
  }

  const live = await shell.value.handle({ method: "GET", path: "/livez" });
  equal(live.status, 200);
  deepEqual(live.body, { status: "live" });
  equal(live.headers["x-content-type-options"], "nosniff");
  equal(live.headers["content-security-policy"], "default-src 'none'; frame-ancestors 'none'; base-uri 'none'");
  equal(live.headers["access-control-allow-origin"], undefined);
  const corsAllowed = await shell.value.handle({
    method: "GET",
    path: "/livez",
    headers: { origin: "https://app.example.test" },
  });
  equal(corsAllowed.headers["access-control-allow-origin"], "https://app.example.test");
  const corsDenied = await shell.value.handle({
    method: "GET",
    path: "/livez",
    headers: { origin: "https://evil.example.test" },
  });
  equal(corsDenied.headers["access-control-allow-origin"], undefined);

  const notReady = await shell.value.handle({ method: "GET", path: "/readyz" });
  equal(notReady.status, 503);
  await shell.value.lifecycle.start();
  const ready = await shell.value.handle({ method: "GET", path: "/readyz" });
  equal(ready.status, 200);
  equal((ready.body as { readonly status: string }).status, "ready");

  const publicRoute = await shell.value.handle({ method: "GET", path: "/public" });
  equal(publicRoute.status, 200);
  deepEqual(publicRoute.body, { public: true });
  equal(publicRoute.headers["content-security-policy"], "default-src 'none'; frame-ancestors 'none'; base-uri 'none'");
  equal(publicRoute.headers["x-app-visible"], "allowed");
  equal(typeof publicRoute.headers["x-request-id"], "string");
  notEqual(publicRoute.headers["x-request-id"], "app-must-not-control-this");
  equal(publicRoute.headers["access-control-max-age"], undefined);
  equal(publicRoutePrincipal, undefined);
  const publicRouteWithCredentials = await shell.value.handle({
    method: "GET",
    path: "/public",
    headers: { authorization: "Bearer ok" },
  });
  equal(publicRouteWithCredentials.status, 200);
  equal(publicRoutePrincipal, undefined);

  const reportedFailure = await shell.value.handle({ method: "POST", path: "/operation-failed" });
  equal(reportedFailure.status, 503);
  equal("observability" in reportedFailure, false);
  const reportedFailureLog = logger.records().find((record) =>
    record.message === "platform.server.request"
      && record.fields?.["http_status_code"] === 503
      && record.fields?.["error_class"] === "SMOKE_OPERATION_NOT_ACCEPTED");
  deepEqual(reportedFailureLog?.fields, {
    capability: "smoke.request",
    action: "execute",
    execution_context: "server",
    http_method: "POST",
    http_status_code: 503,
    outcome: "failed",
    error_class: "SMOKE_OPERATION_NOT_ACCEPTED",
  });
  equal(metrics.points().some((point) =>
    point.name === "platform.server.request.outcome"
      && point.labels?.["http_status_code"] === 503
      && point.labels?.["error_class"] === "SMOKE_OPERATION_NOT_ACCEPTED"), true);
  const reportedFailureTrace = tracer.spans().find((span) =>
    span.name === "platform.server.request"
      && span.end?.attributes?.["http_status_code"] === 503
      && span.end.attributes["error_class"] === "SMOKE_OPERATION_NOT_ACCEPTED");
  equal(reportedFailureTrace?.end?.attributes?.["error_class"], "SMOKE_OPERATION_NOT_ACCEPTED");

  const denied = await shell.value.handle({
    method: "POST",
    path: "/echo/123",
    body: { message: "hello" },
  });
  equal(denied.status, 401);
  equal((denied.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_UNAUTHENTICATED");
  equal(protectedHandlerCalls, 0);
  deepEqual(logger.records().at(-1)?.fields, {
    capability: "smoke.request",
    action: "execute",
    execution_context: "server",
    http_method: "POST",
    http_status_code: 401,
    outcome: "denied",
    error_class: "PLATFORM_SERVER_UNAUTHENTICATED",
  });

  const invalid = await shell.value.handle({
    method: "POST",
    path: "/echo/123",
    headers: { authorization: "Bearer ok", "x-request-id": "request-123" },
    body: { nope: true },
  });
  equal(invalid.status, 400);
  equal((invalid.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_INVALID_REQUEST");

  const forbidden = await shell.value.handle({
    method: "POST",
    path: "/echo/123",
    headers: { authorization: "Bearer no-permission", "x-request-id": "request-123" },
    body: { message: "hello" },
  });
  equal(forbidden.status, 403);
  equal((forbidden.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_FORBIDDEN");
  equal(protectedHandlerCalls, 0);

  const tenantCallsBeforePermissionDenied = tenantResolverCalls;
  const resourceCallsBeforePermissionDenied = resourceResolutionCalls;
  const resourcePermissionDenied = await shell.value.handle({
    method: "GET",
    path: "/records/record-123",
    headers: { authorization: "Bearer no-permission" },
  });
  equal(resourcePermissionDenied.status, 403);
  equal((resourcePermissionDenied.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_FORBIDDEN");
  equal(tenantResolverCalls, tenantCallsBeforePermissionDenied);
  equal(resourceResolutionCalls, resourceCallsBeforePermissionDenied);
  equal(resourceHandlerCalls, 0);

  const tenantless = await shell.value.handle({
    method: "GET",
    path: "/tenant",
    headers: { authorization: "Bearer tenantless" },
  });
  equal(tenantless.status, 403);
  equal((tenantless.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_FORBIDDEN");
  equal(requiredTenantHandlerCalls, 0);

  const malformedTenant = await shell.value.handle({
    method: "GET",
    path: "/tenant",
    headers: { authorization: "Bearer malformed-tenant" },
  });
  equal(malformedTenant.status, 403);
  equal((malformedTenant.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_FORBIDDEN");
  equal(requiredTenantHandlerCalls, 0);

  const tenantAllowed = await shell.value.handle({
    method: "GET",
    path: "/tenant",
    headers: { authorization: "Bearer ok" },
  });
  equal(tenantAllowed.status, 200);
  equal(requiredTenantHandlerCalls, 1);
  equal(requiredTenantContext?.tenantId, "tenant-benelux");

  const resourceAllowed = await shell.value.handle({
    method: "GET",
    path: "/records/record-123",
    headers: { authorization: "Bearer ok" },
  });
  equal(resourceAllowed.status, 200);
  equal(resourceHandlerCalls, 1);
  equal(resourceTenantContext?.tenantId, "tenant-benelux");
  equal(resourcePrincipal?.subject, "subject-ok");
  const allowedAuthorizationRequest = authorizationRequests.at(-1);
  equal(allowedAuthorizationRequest?.principal.subject, "subject-ok");
  equal(allowedAuthorizationRequest?.tenantId, "tenant-benelux");
  equal(allowedAuthorizationRequest?.permission, resourcePermission);
  equal(allowedAuthorizationRequest?.resource?.id, "record-123");
  deepEqual(allowedAuthorizationRequest?.facts, { source: "test" });

  const missingResource = await shell.value.handle({
    method: "GET",
    path: "/records/missing",
    headers: { authorization: "Bearer ok" },
  });
  equal(missingResource.status, 404);
  equal((missingResource.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_RESOURCE_NOT_FOUND");
  equal(resourceHandlerCalls, 1);

  const hiddenResource = await shell.value.handle({
    method: "GET",
    path: "/records/hidden",
    headers: { authorization: "Bearer ok" },
  });
  equal(hiddenResource.status, 403);
  equal((hiddenResource.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_FORBIDDEN");
  equal(resourceHandlerCalls, 1);

  const malformedResource = await shell.value.handle({
    method: "GET",
    path: "/records/malformed",
    headers: { authorization: "Bearer ok" },
  });
  equal(malformedResource.status, 403);
  equal((malformedResource.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_FORBIDDEN");
  equal(resourceHandlerCalls, 1);

  const deniedResource = await shell.value.handle({
    method: "GET",
    path: "/records/denied",
    headers: { authorization: "Bearer ok" },
  });
  equal(deniedResource.status, 403);
  equal((deniedResource.body as { readonly error: { readonly code: string; readonly details: unknown } }).error.code, "PLATFORM_SERVER_FORBIDDEN");
  equal(JSON.stringify(deniedResource.body).includes("do-not-return"), false);
  equal(resourceHandlerCalls, 1);

  const ok = await shell.value.handle({
    method: "POST",
    path: "/echo/123",
    headers: { authorization: "Bearer ok", "x-request-id": "request-123" },
    body: { message: "hello" },
  });
  equal(ok.status, 200);
  deepEqual(ok.body, { id: "123", message: "hello" });
  equal(protectedHandlerCalls, 1);
  if (authenticatedPrincipal === undefined) {
    throw new Error("Expected an authenticated route handler to receive a principal.");
  }
  equal(authenticatedPrincipal.id, "principal-ok");
  equal(authenticatedPrincipal.type, "user");
  equal(authenticatedPrincipal.subject, "subject-ok");
  deepEqual(authenticatedPrincipal.claims, { sub: "subject-ok", "custom:role": "operator" });
  deepEqual(authenticatedPrincipal.scopes, ["openid", "platform-smoke/read"]);
  deepEqual(ok.middleware, [
    "request-id",
    "request-logging",
    "cors",
    "security-headers",
    "rate-limit",
    "parse",
    "auth",
    "authorization",
    "context",
    "validation",
    "handler",
    "response-logging",
  ]);

  const notFound = await shell.value.handle({ method: "GET", path: "/missing" });
  equal(notFound.status, 404);
  equal((notFound.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_ROUTE_NOT_FOUND");

  equal(metrics.points().some((point) =>
    point.name === "platform.server.request.outcome"
      && point.labels?.["capability"] === "smoke.request"
      && point.labels?.["action"] === "execute"), true);
  equal(metrics.points().some((point) =>
    point.name === "platform.server.request_response_latency"
      && point.labels?.["capability"] === "smoke.request"), true);
  const completedEchoLog = logger.records().find((record) =>
    record.message === "platform.server.request"
      && record.fields?.["http_method"] === "POST"
      && record.fields?.["http_status_code"] === 200);
  deepEqual(completedEchoLog?.fields, {
    capability: "smoke.request",
    action: "execute",
    execution_context: "server",
    http_method: "POST",
    http_status_code: 200,
    outcome: "succeeded",
  });
  equal("requestId" in (completedEchoLog?.fields ?? {}), false);
  equal("route" in (completedEchoLog?.fields ?? {}), false);
  const completedEchoTrace = tracer.spans().find((span) =>
    span.name === "platform.server.request"
      && span.end?.attributes?.["capability"] === "smoke.request"
      && span.end.attributes["http_method"] === "POST"
      && span.end.attributes["http_status_code"] === 200);
  equal(completedEchoTrace?.attributes, undefined);
  deepEqual(completedEchoTrace?.end, {
    outcome: "succeeded",
    attributes: {
      capability: "smoke.request",
      action: "execute",
      execution_context: "server",
      http_method: "POST",
      http_status_code: 200,
      outcome: "succeeded",
    },
  });
  equal("requestId" in (completedEchoTrace?.end?.attributes ?? {}), false);
  equal("correlationId" in (completedEchoTrace?.end?.attributes ?? {}), false);

  const observabilityCountsBeforeOptOut = {
    logs: logger.records().length,
    metrics: metrics.points().length,
    traces: tracer.spans().length,
  };
  const optOutRoute = await shell.value.handle({ method: "GET", path: "/opt-out" });
  equal(optOutRoute.status, 204);
  deepEqual({
    logs: logger.records().length,
    metrics: metrics.points().length,
    traces: tracer.spans().length,
  }, observabilityCountsBeforeOptOut);

  const rateLimitKeys: string[] = [];
  const keyedRateLimitShell = await createPlatformServerShell({
    apps: [app],
    deps,
    tenantResolver,
    rateLimiter: {
      check: (key) => {
        rateLimitKeys.push(key);
        return { allowed: true };
      },
    },
  });
  equal(keyedRateLimitShell.ok, true);
  if (!keyedRateLimitShell.ok) {
    throw new Error("Expected keyed rate-limit shell to mount.");
  }
  await keyedRateLimitShell.value.handle({
    method: "GET",
    path: "/livez",
    headers: { "x-forwarded-for": "203.0.113.10, 10.0.0.1" },
    clientAddress: "198.51.100.10",
  });
  equal(rateLimitKeys[0], "ip:198.51.100.10");

  const forwardedAddressKeys: string[] = [];
  const forwardedAddressShell = await createPlatformServerShell({
    apps: [app],
    deps,
    tenantResolver,
    clientAddressResolver: {
      resolve: ({ socketPeerAddress, headers }) => {
        if (socketPeerAddress === undefined) {
          throw new Error("Expected the Node transport to supply a socket peer address.");
        }
        equal(headers["x-forwarded-for"], "198.51.100.55, 203.0.113.9");
        return "203.0.113.9";
      },
    },
    rateLimiter: {
      check: (key) => {
        forwardedAddressKeys.push(key);
        return { allowed: true };
      },
    },
  });
  equal(forwardedAddressShell.ok, true);
  if (!forwardedAddressShell.ok) {
    throw new Error("Expected forwarded-address shell to mount.");
  }
  await forwardedAddressShell.value.lifecycle.start();
  const forwardedAddressHandle = await forwardedAddressShell.value.listen();
  try {
    const response = await fetch("http://127.0.0.1:" + forwardedAddressHandle.port + "/public", {
      headers: { "x-forwarded-for": "198.51.100.55, 203.0.113.9" },
    });
    equal(response.status, 200);
    equal(forwardedAddressKeys[0], "ip:203.0.113.9");
  } finally {
    forwardedAddressShell.value.lifecycle.beginDrain();
    await forwardedAddressHandle.close();
    await forwardedAddressShell.value.lifecycle.shutdown();
  }

  const privateHealthShell = await createPlatformServerShell({
    apps: [app],
    deps,
    tenantResolver,
    auth: {
      grantedPermissions: () => [permission],
      authenticate: (request) => request.headers?.authorization === "Bearer ok"
        ? { authenticated: true, permissions: [permission], subject: "subject-ok", rateLimitKey: "principal:subject-ok" }
        : { authenticated: false, permissions: [] },
    },
    healthExposure: { liveness: "public", readiness: "authenticated" },
  });
  equal(privateHealthShell.ok, true);
  if (!privateHealthShell.ok) {
    throw new Error("Expected private-health shell to mount.");
  }
  const privateReadyDenied = await privateHealthShell.value.handle({ method: "GET", path: "/readyz" });
  equal(privateReadyDenied.status, 401);
  await privateHealthShell.value.lifecycle.start();
  const privateReadyOk = await privateHealthShell.value.handle({
    method: "GET",
    path: "/readyz",
    headers: { authorization: "Bearer ok" },
  });
  equal(privateReadyOk.status, 200);

  const rateLimitedShell = await createPlatformServerShell({
    apps: [app],
    deps,
    tenantResolver,
    rateLimiter: { check: () => ({ allowed: false, retryAfterMs: 10 }) },
  });
  equal(rateLimitedShell.ok, true);
  if (!rateLimitedShell.ok) {
    throw new Error("Expected rate-limited shell to mount.");
  }
  const limited = await rateLimitedShell.value.handle({ method: "GET", path: "/livez" });
  equal(limited.status, 429);
  equal((limited.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_RATE_LIMITED");

  const invalidAuthzShell = await createPlatformServerShell({
    apps: [app],
    deps: createPlatformTestMountDeps(),
    auth: {
      grantedPermissions: () => ["other:read" as Permission],
      authenticate: () => ({ authenticated: true, permissions: [] }),
    },
  });
  equal(invalidAuthzShell.ok, false);
  if (!invalidAuthzShell.ok) {
    equal(invalidAuthzShell.error.code, "PLATFORM_SERVER_AUTHZ_MAPPING_INVALID");
  }

  const invalidConfigSchema: ConfigSchema<never> = {
    parse: () => ({
      ok: false,
      error: configError("CONFIG_INVALID", [
        validationIssue({
          path: ["config", "SMOKE_SECRET"],
          code: "CONFIG_INVALID_SECRET",
          defaultMessage: "Smoke config is invalid.",
          params: { secret: "do-not-leak" },
        }),
      ]),
    }),
  };
  const invalidConfigShell = await createPlatformServerShell({
    apps: [definePlatformApp({
      id: appId.value,
      name: "Invalid Config",
      mount(registry) {
        registry.registerConfigSchema(invalidConfigSchema);
      },
    })],
    deps: createPlatformTestMountDeps(),
  });
  equal(invalidConfigShell.ok, false);
  if (!invalidConfigShell.ok) {
    equal(invalidConfigShell.error.code, "PLATFORM_SERVER_CONFIG_INVALID");
    const issues = invalidConfigShell.error.details?.["issues"] as readonly unknown[];
    equal(JSON.stringify(issues).includes("do-not-leak"), false);
  }

  const invalidTransportShell = await createPlatformServerShell({
    apps: [app],
    deps,
    auth,
    tenantResolver,
    transport: { headersTimeoutMs: 31_000, requestTimeoutMs: 30_000 },
  });
  equal(invalidTransportShell.ok, false);
  if (!invalidTransportShell.ok) {
    equal(invalidTransportShell.error.code, "PLATFORM_SERVER_TRANSPORT_CONFIG_INVALID");
  }

  const transportShell = await createPlatformServerShell({
    apps: [app],
    deps,
    auth,
    tenantResolver,
    corsAllowlist: ["https://app.example.test"],
    transport: { maxRequestBodyBytes: 32, maxConcurrentRequests: 2 },
  });
  equal(transportShell.ok, true);
  if (!transportShell.ok) {
    throw new Error("Expected transport shell to mount.");
  }
  await transportShell.value.lifecycle.start();
  const transportHandle = await transportShell.value.listen();
  const transportBaseUrl = `http://127.0.0.1:${transportHandle.port}`;
  try {
    const responseWithGeneratedId = await fetch(`${transportBaseUrl}/public`);
    equal(responseWithGeneratedId.status, 200);
    const generatedRequestId = responseWithGeneratedId.headers.get("x-request-id");
    equal(typeof generatedRequestId, "string");
    notEqual(generatedRequestId, "app-must-not-control-this");
    const responseWithUpstreamId = await fetch(`${transportBaseUrl}/public`, {
      headers: { "x-request-id": "upstream-123" },
    });
    equal(responseWithUpstreamId.headers.get("x-request-id"), "upstream-123");

    const preflight = await fetch(`${transportBaseUrl}/echo/123`, {
      method: "OPTIONS",
      headers: { origin: "https://app.example.test" },
    });
    equal(preflight.status, 204);
    equal(preflight.headers.get("access-control-allow-origin"), "https://app.example.test");
    equal(preflight.headers.get("access-control-allow-methods"), "POST, OPTIONS");
    equal(preflight.headers.get("vary"), "Origin");

    const malformedJson = await fetch(`${transportBaseUrl}/echo/123`, {
      method: "POST",
      headers: { authorization: "Bearer ok", "content-type": "application/json" },
      body: "{",
    });
    equal(malformedJson.status, 400);
    equal((await malformedJson.json() as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_INVALID_REQUEST");
    equal(logger.records().some((record) =>
      record.message === "platform.server.request"
        && record.fields?.["capability"] === "smoke.request"
        && record.fields?.["http_method"] === "POST"
        && record.fields?.["http_status_code"] === 400
        && record.fields?.["outcome"] === "rejected"), true);

    const oversizedPayload = await fetch(`${transportBaseUrl}/echo/123`, {
      method: "POST",
      headers: { authorization: "Bearer ok", "content-type": "application/json" },
      body: JSON.stringify({ message: "this payload is deliberately over the thirty-two byte limit" }),
    });
    equal(oversizedPayload.status, 413);
    equal((await oversizedPayload.json() as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_PAYLOAD_TOO_LARGE");

    const unsupportedMethod = await rawHttpRequest({
      port: transportHandle.port,
      method: "TRACE",
      path: "/public",
    });
    equal(unsupportedMethod.status, 405);
    equal(unsupportedMethod.headers["allow"], "GET, OPTIONS");
  } finally {
    transportShell.value.lifecycle.beginDrain();
    await transportHandle.close();
    await transportShell.value.lifecycle.shutdown();
  }

  const timeoutShell = await createPlatformServerShell({
    apps: [app],
    deps,
    auth,
    tenantResolver,
    transport: { handlerTimeoutMs: 10, maxConcurrentRequests: 1 },
  });
  equal(timeoutShell.ok, true);
  if (!timeoutShell.ok) {
    throw new Error("Expected timeout shell to mount.");
  }
  await timeoutShell.value.lifecycle.start();
  const timeoutHandle = await timeoutShell.value.listen();
  try {
    const timedOut = await fetch(`http://127.0.0.1:${timeoutHandle.port}/slow`);
    equal(timedOut.status, 504);
    const capacityStillHeld = await fetch(`http://127.0.0.1:${timeoutHandle.port}/public`);
    equal(capacityStillHeld.status, 503);
    if (resolveSlowHandler === undefined) {
      throw new Error("Expected slow handler to be running.");
    }
    resolveSlowHandler();
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    const capacityReleased = await fetch(`http://127.0.0.1:${timeoutHandle.port}/public`);
    equal(capacityReleased.status, 200);
  } finally {
    if (resolveSlowHandler !== undefined) {
      resolveSlowHandler();
    }
    timeoutShell.value.lifecycle.beginDrain();
    await timeoutHandle.close();
    await timeoutShell.value.lifecycle.shutdown();
  }

  const earlyRateLimitedShell = await createPlatformServerShell({
    apps: [app],
    deps,
    tenantResolver,
    rateLimiter: { check: () => ({ allowed: false }) },
    transport: { maxRequestBodyBytes: 1 },
  });
  equal(earlyRateLimitedShell.ok, true);
  if (!earlyRateLimitedShell.ok) {
    throw new Error("Expected early-rate-limited shell to mount.");
  }
  await earlyRateLimitedShell.value.lifecycle.start();
  const earlyRateLimitedHandle = await earlyRateLimitedShell.value.listen();
  try {
    const rateLimitedBeforeParse = await fetch(`http://127.0.0.1:${earlyRateLimitedHandle.port}/public`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ a: "body is much larger than one byte" }),
    });
    equal(rateLimitedBeforeParse.status, 429);
    equal((await rateLimitedBeforeParse.json() as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_RATE_LIMITED");
  } finally {
    earlyRateLimitedShell.value.lifecycle.beginDrain();
    await earlyRateLimitedHandle.close();
    await earlyRateLimitedShell.value.lifecycle.shutdown();
  }

  const processAppId = platformAppId("processmetrics");
  const processRouteName = platformRouteName("processmetrics.read");
  const processProfileName = platformObservabilityProfileName("processmetrics.read");
  const processCapabilityName = platformCapabilityName("processmetrics.read");
  if (!processAppId.ok || !processRouteName.ok || !processProfileName.ok || !processCapabilityName.ok) {
    throw new Error("Expected valid process metrics test primitives.");
  }
  const processMetrics = createPlatformTestMetrics();
  const processApp = definePlatformApp({
    id: processAppId.value,
    name: "Process metrics",
    mount(registry) {
      registry.registerObservabilityProfile({
        name: processProfileName.value,
        capability: processCapabilityName.value,
        action: "read",
        signals: ["metric"],
        metricDimensionFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
        nfrObjectives: [{ nfrClass: "interactive_read", measurement: "request_response_latency" }],
      });
      registry.registerRoute({
        name: processRouteName.value,
        method: "GET",
        path: "/process-metrics",
        auth: { kind: "public" },
        observability: { kind: "profile", profile: processProfileName.value },
        handler: { handle: () => ({ status: 200, body: { source: "process" } }) },
      });
    },
  });
  const startedProcess = await startPlatformServerProcess({
    apps: [processApp],
    host: "127.0.0.1",
    port: 39557,
    installSignalHandlers: false,
    metrics: processMetrics,
  });
  if (!startedProcess.ok) {
    throw new Error(`Expected the server process to accept a target-composed metrics port: ${startedProcess.error.code}`);
  }
  equal(startedProcess.ok, true);
  try {
    const response = await fetch(`http://127.0.0.1:${startedProcess.value.handle.port}/process-metrics`);
    equal(response.status, 200);
    equal(processMetrics.points().some((point) => point.name === "platform.server.request.outcome" && point.labels?.["capability"] === "processmetrics.read"), true);
    equal(processMetrics.points().some((point) => point.name === "platform.server.request_response_latency" && point.labels?.["capability"] === "processmetrics.read"), true);
  } finally {
    await startedProcess.value.close();
  }
}

async function rawHttpRequest(input: {
  readonly port: number;
  readonly method: string;
  readonly path: string;
}): Promise<{ readonly status: number; readonly headers: Readonly<Record<string, string | readonly string[] | undefined>> }> {
  return new Promise((resolve, reject) => {
    const request = nodeHttpRequest({
      host: "127.0.0.1",
      port: input.port,
      method: input.method,
      path: input.path,
    }, (response) => {
      response.resume();
      response.on("end", () => {
        resolve({ status: response.statusCode ?? 0, headers: response.headers });
      });
    });
    request.once("error", reject);
    request.end();
  });
}

main()
  .then(() => {
    console.log("platform/server runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
