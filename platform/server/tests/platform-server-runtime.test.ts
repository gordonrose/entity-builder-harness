import { deepEqual, equal } from "node:assert/strict";
import type { Principal } from "@kanbien/core/authn";
import {
  allow,
  deny,
  resourceRef,
  type AuthorizationRequest,
  type Permission,
} from "@kanbien/core/authz";
import { configError, type ConfigSchema } from "@kanbien/core/config";
import { messageDescriptor } from "@kanbien/core/shared";
import { tenantContext, tenantId, type TenantContext } from "@kanbien/core/tenancy";
import { validationIssue } from "@kanbien/core/validation";
import {
  definePlatformApp,
  platformAppId,
  platformRouteName,
} from "@kanbien/platform-contracts";
import {
  createPlatformTestLogger,
  createPlatformTestMetrics,
  createPlatformTestMountDeps,
  validatorForTest,
} from "@kanbien/platform-testing";
import { createPlatformServerShell } from "../src/index";

async function main(): Promise<void> {
  const appId = platformAppId("smoke");
  const routeName = platformRouteName("smoke.echo");
  const publicRouteName = platformRouteName("smoke.public");
  const tenantRouteName = platformRouteName("smoke.tenant");
  const resourceRouteName = platformRouteName("smoke.resource");
  if (!appId.ok || !routeName.ok || !publicRouteName.ok || !tenantRouteName.ok || !resourceRouteName.ok) {
    throw new Error("Expected valid server test primitives.");
  }

  const permission = "smoke.smoke:read" as Permission;
  const tenantPermission = "smoke.tenant:read" as Permission;
  const resourcePermission = "smoke.record:read" as Permission;
  const logger = createPlatformTestLogger();
  const metrics = createPlatformTestMetrics();
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
      registry.registerPermission({ permission });
      registry.registerPermission({ permission: tenantPermission });
      registry.registerPermission({ permission: resourcePermission });
      registry.registerRoute({
        name: publicRouteName.value,
        method: "GET",
        path: "/public",
        auth: { kind: "public" },
        handler: {
          handle: (_request, context) => {
            publicRoutePrincipal = context.principal;
            return { status: 200, body: { public: true } };
          },
        },
      });
      registry.registerRoute({
        name: routeName.value,
        method: "POST",
        path: "/echo/:id",
        auth: { kind: "authenticated", permissions: [permission] },
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
  equal(publicRoutePrincipal, undefined);
  const publicRouteWithCredentials = await shell.value.handle({
    method: "GET",
    path: "/public",
    headers: { authorization: "Bearer ok" },
  });
  equal(publicRouteWithCredentials.status, 200);
  equal(publicRoutePrincipal, undefined);

  const denied = await shell.value.handle({
    method: "POST",
    path: "/echo/123",
    body: { message: "hello" },
  });
  equal(denied.status, 401);
  equal((denied.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_UNAUTHENTICATED");
  equal(protectedHandlerCalls, 0);

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

  equal(metrics.points().some((point) => point.name === "platform.server.request"), true);
  equal(logger.records().some((record) => record.message === "platform.server.request"), true);

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
  });
  equal(rateLimitKeys[0], "ip:203.0.113.10");

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
}

main()
  .then(() => {
    console.log("platform/server runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
