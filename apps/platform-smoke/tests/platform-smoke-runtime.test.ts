import { deepEqual, equal } from "node:assert/strict";
import type { Permission } from "@kanbien/core/authz";
import type { QueueIdempotencyKey } from "@kanbien/core/queues";
import { createPlatformServerShell } from "@kanbien/platform-server";
import {
  createPlatformTestConfigSource,
  createPlatformTestLogger,
  createPlatformTestMetrics,
  createPlatformTestMountDeps,
  createPlatformTestQueueMessage,
  mountPlatformAppForTest,
  runPlatformTestHealthChecks,
  validatePlatformTestConfigSchemas,
} from "@kanbien/platform-testing";
import {
  createInMemoryPlatformWorkerIdempotencyStore,
  createPlatformWorkerShell,
} from "@kanbien/platform-workers";
import {
  platformSmokeApp,
  platformSmokeAppManifest,
  platformSmokeJobMessageType,
  platformSmokeReadPermission,
} from "../src/index";

async function main(): Promise<void> {
  const logger = createPlatformTestLogger();
  const metrics = createPlatformTestMetrics();
  const deps = createPlatformTestMountDeps({
    logger,
    metrics,
    config: createPlatformTestConfigSource({ PLATFORM_SMOKE_APP_NAME: "Smoke Test" }),
  });

  const mounted = await mountPlatformAppForTest(platformSmokeApp, { deps });
  equal(mounted.ok, true);
  if (!mounted.ok) {
    throw new Error("Expected platform-smoke app to mount.");
  }
  equal(mounted.value.permissions.length, 1);
  equal(mounted.value.routes.length, 1);
  equal(mounted.value.jobs.length, 1);
  equal(mounted.value.healthChecks.length, 1);
  equal(mounted.value.configSchemas.length, 1);
  equal(mounted.value.routes[0]?.path, "/smoke/:id");
  equal(mounted.value.jobs[0]?.messageType, platformSmokeJobMessageType);
  equal(typeof mounted.value.lifecycle?.beforeStart, "function");

  const config = validatePlatformTestConfigSchemas(mounted.value.configSchemas, deps.config);
  equal(config.ok, true);
  const health = await runPlatformTestHealthChecks(mounted.value.healthChecks);
  equal(health.ok, true);
  if (!health.ok) {
    throw new Error("Expected smoke health to pass.");
  }
  equal(health.value[0]?.status, "healthy");

  const auth = authHookForPermission(platformSmokeReadPermission);
  const server = await createPlatformServerShell({
    apps: [platformSmokeApp],
    deps,
    auth,
    corsAllowlist: ["https://staging.kanbien.example"],
  });
  equal(server.ok, true);
  if (!server.ok) {
    throw new Error("Expected server shell to mount platform-smoke.");
  }
  await server.value.lifecycle.start();

  const unauthenticated = await server.value.handle({ method: "GET", path: "/smoke/abc" });
  equal(unauthenticated.status, 401);
  const forbidden = await server.value.handle({
    method: "GET",
    path: "/smoke/abc",
    headers: { authorization: "Bearer no-permission" },
  });
  equal(forbidden.status, 403);
  const ok = await server.value.handle({
    method: "GET",
    path: "/smoke/abc",
    headers: { authorization: "Bearer ok", origin: "https://staging.kanbien.example" },
  });
  equal(ok.status, 200);
  deepEqual(ok.body, {
    app: platformSmokeAppManifest.appId,
    appName: "Smoke Test",
    id: "abc",
    ok: true,
  });
  equal(ok.headers["access-control-allow-origin"], "https://staging.kanbien.example");

  const worker = await createPlatformWorkerShell({
    apps: [platformSmokeApp],
    deps,
    idempotency: createInMemoryPlatformWorkerIdempotencyStore(),
  });
  equal(worker.ok, true);
  if (!worker.ok) {
    throw new Error("Expected worker shell to mount platform-smoke.");
  }
  equal((await worker.value.start()).ok, true);

  const message = {
    ...createPlatformTestQueueMessage({
      id: "platform-smoke-rebuild-1",
      type: platformSmokeJobMessageType,
      payload: { rebuild: true },
    }),
    idempotencyKey: "platform-smoke-rebuild-1" as QueueIdempotencyKey,
  };
  equal(worker.value.enqueue(message).ok, true);
  const job = await worker.value.runNext();
  equal(job.ok, true);
  if (!job.ok || job.value.status !== "succeeded") {
    throw new Error("Expected platform-smoke job to succeed.");
  }
  equal(job.value.idempotency, "processed");
  equal(logger.records().some((record) => record.message === "platform-smoke.job.handled"), true);
}

function authHookForPermission(permission: Permission) {
  return {
    grantedPermissions: () => [permission],
    authenticate: (request: { readonly headers?: Readonly<Record<string, string | readonly string[]>> }) => {
      if (request.headers?.authorization === "Bearer ok") {
        return {
          authenticated: true,
          permissions: [permission],
          subject: "smoke-user",
          rateLimitKey: "principal:smoke-user",
        };
      }
      if (request.headers?.authorization === "Bearer no-permission") {
        return {
          authenticated: true,
          permissions: [],
          subject: "smoke-limited",
          rateLimitKey: "principal:smoke-limited",
        };
      }
      return { authenticated: false, permissions: [] };
    },
  };
}

main()
  .then(() => {
    console.log("apps/platform-smoke runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
