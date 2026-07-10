import { deepEqual, equal } from "node:assert/strict";
import type { Permission } from "@kanbien/core/authz";
import {
  definePlatformApp,
  platformAppId,
  platformRouteName,
} from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps, validatorForTest } from "@kanbien/platform-testing";
import { createPlatformServerShell } from "../src/index";

async function main(): Promise<void> {
  const appId = platformAppId("smoke");
  const routeName = platformRouteName("smoke.echo");
  if (!appId.ok || !routeName.ok) {
    throw new Error("Expected valid server test primitives.");
  }

  const permission = "smoke:read" as Permission;
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
    deps: createPlatformTestMountDeps(),
    auth: {
      authenticate: (request) => request.headers?.authorization === "Bearer ok"
        ? { authenticated: true, permissions: [permission] }
        : { authenticated: false, permissions: [] },
    },
  });
  equal(shell.ok, true);
  if (!shell.ok) {
    throw new Error("Expected server shell to mount.");
  }

  const live = await shell.value.handle({ method: "GET", path: "/livez" });
  equal(live.status, 200);
  deepEqual(live.body, { status: "live" });
  equal(live.headers["x-content-type-options"], "nosniff");

  const notReady = await shell.value.handle({ method: "GET", path: "/readyz" });
  equal(notReady.status, 503);
  await shell.value.lifecycle.start();
  const ready = await shell.value.handle({ method: "GET", path: "/readyz" });
  equal(ready.status, 200);

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
}

main()
  .then(() => {
    console.log("platform/server runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
