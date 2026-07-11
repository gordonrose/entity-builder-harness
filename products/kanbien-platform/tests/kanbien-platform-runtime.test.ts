import { deepEqual, equal } from "node:assert/strict";
import type { Permission } from "@kanbien/core/authz";
import type { QueueIdempotencyKey } from "@kanbien/core/queues";
import {
  platformSmokeAppManifest,
  platformSmokeJobMessageType,
  platformSmokeReadPermission,
} from "@kanbien/app-platform-smoke";
import { createPlatformServerShell } from "@kanbien/platform-server";
import {
  createPlatformTestConfigSource,
  createPlatformTestMountDeps,
  createPlatformTestQueueMessage,
} from "@kanbien/platform-testing";
import {
  createInMemoryPlatformWorkerIdempotencyStore,
  createPlatformWorkerShell,
} from "@kanbien/platform-workers";
import {
  kanbienPlatformApps,
  kanbienPlatformProductManifest,
} from "../src/index";

async function main(): Promise<void> {
  equal(kanbienPlatformProductManifest.productId, "kanbien-platform");
  equal(kanbienPlatformProductManifest.apps.length, 1);
  deepEqual(kanbienPlatformProductManifest.apps[0], {
    appId: platformSmokeAppManifest.appId,
    packageName: "@kanbien/app-platform-smoke",
    mountModule: "@kanbien/app-platform-smoke",
    routeBasePath: "/smoke",
    permissions: [platformSmokeReadPermission],
    jobs: ["platform-smoke.rebuild"],
    healthChecks: ["platform-smoke.readiness"],
    requiredConfig: ["PLATFORM_SMOKE_APP_NAME"],
  });

  const deps = createPlatformTestMountDeps({
    config: createPlatformTestConfigSource({ PLATFORM_SMOKE_APP_NAME: "Kanbien Platform Smoke" }),
  });
  const server = await createPlatformServerShell({
    apps: kanbienPlatformApps,
    deps,
    auth: authHookForPermission(platformSmokeReadPermission),
  });
  equal(server.ok, true);
  if (!server.ok) {
    throw new Error("Expected Kanbien Platform server shell to mount.");
  }
  await server.value.lifecycle.start();
  const ok = await server.value.handle({
    method: "GET",
    path: "/smoke/product",
    headers: { authorization: "Bearer ok" },
  });
  equal(ok.status, 200);
  deepEqual(ok.body, {
    app: "platform-smoke",
    appName: "Kanbien Platform Smoke",
    id: "product",
    ok: true,
  });

  const worker = await createPlatformWorkerShell({
    apps: kanbienPlatformApps,
    deps,
    idempotency: createInMemoryPlatformWorkerIdempotencyStore(),
  });
  equal(worker.ok, true);
  if (!worker.ok) {
    throw new Error("Expected Kanbien Platform worker shell to mount.");
  }
  equal((await worker.value.start()).ok, true);
  equal(worker.value.enqueue({
    ...createPlatformTestQueueMessage({
      id: "kanbien-platform-smoke-1",
      type: platformSmokeJobMessageType,
      payload: { rebuild: true },
    }),
    idempotencyKey: "kanbien-platform-smoke-1" as QueueIdempotencyKey,
  }).ok, true);
  const job = await worker.value.runNext();
  equal(job.ok, true);
  if (!job.ok || job.value.status !== "succeeded") {
    throw new Error("Expected Kanbien Platform smoke job to succeed.");
  }
}

function authHookForPermission(permission: Permission) {
  return {
    grantedPermissions: () => [permission],
    authenticate: (request: { readonly headers?: Readonly<Record<string, string | readonly string[]>> }) => request.headers?.authorization === "Bearer ok"
      ? {
        authenticated: true,
        permissions: [permission],
        subject: "kanbien-platform-user",
        rateLimitKey: "principal:kanbien-platform-user",
      }
      : { authenticated: false, permissions: [] },
  };
}

main()
  .then(() => {
    console.log("products/kanbien-platform runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
