import { deepEqual, equal } from "node:assert/strict";
import type { Permission } from "@kanbien/core/authz";
import { configError, type ConfigSchema } from "@kanbien/core/config";
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
  if (!appId.ok || !routeName.ok) {
    throw new Error("Expected valid server test primitives.");
  }

  const permission = "smoke:read" as Permission;
  const logger = createPlatformTestLogger();
  const metrics = createPlatformTestMetrics();
  const deps = createPlatformTestMountDeps({ logger, metrics });
  const app = definePlatformApp({
    id: appId.value,
    name: "Smoke",
    mount(registry) {
      registry.registerPermission({ permission });
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
          handle: (request) => ({
            status: 200,
            body: { id: request.params["id"], message: (request.body as { readonly message: string }).message },
          }),
        },
      });
    },
  });

  const shell = await createPlatformServerShell({
    apps: [app],
    deps,
    auth: {
      grantedPermissions: () => [permission],
      authenticate: (request) => {
        if (request.headers?.authorization === "Bearer ok") {
          return { authenticated: true, permissions: [permission], subject: "subject-ok", rateLimitKey: "principal:subject-ok" };
        }
        if (request.headers?.authorization === "Bearer no-permission") {
          return { authenticated: true, permissions: [], subject: "subject-no-permission", rateLimitKey: "principal:subject-no-permission" };
        }
        return { authenticated: false, permissions: [] };
      },
    },
    corsAllowlist: ["https://app.example.test"],
  });
  equal(shell.ok, true);
  if (!shell.ok) {
    throw new Error("Expected server shell to mount.");
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

  const denied = await shell.value.handle({
    method: "POST",
    path: "/echo/123",
    body: { message: "hello" },
  });
  equal(denied.status, 401);
  equal((denied.body as { readonly error: { readonly code: string } }).error.code, "PLATFORM_SERVER_UNAUTHENTICATED");

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

  const ok = await shell.value.handle({
    method: "POST",
    path: "/echo/123",
    headers: { authorization: "Bearer ok", "x-request-id": "request-123" },
    body: { message: "hello" },
  });
  equal(ok.status, 200);
  deepEqual(ok.body, { id: "123", message: "hello" });
  deepEqual(ok.middleware, [
    "request-id",
    "request-logging",
    "cors",
    "security-headers",
    "rate-limit",
    "parse",
    "auth",
    "context",
    "authorization",
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
    deps: createPlatformTestMountDeps(),
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
    deps: createPlatformTestMountDeps(),
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
    deps: createPlatformTestMountDeps(),
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
