import { deepEqual, equal } from "node:assert/strict";
import { healthCheckName, healthCheckResult, monitoringComponent } from "@kanbien/core/monitoring";
import type { QueueMessageType } from "@kanbien/core/queues";
import type { CorrelationId } from "@kanbien/core/shared";
import {
  definePlatformApp,
  platformAppId,
  platformHealthName,
  platformJobName,
  platformRouteName,
} from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps, createPlatformTestQueueMessage } from "@kanbien/platform-testing";
import {
  createPlatformRuntimeJobContext,
  createPlatformRuntimeLifecycle,
  createPlatformRuntimeRequestContext,
  mountPlatformRuntimeApps,
} from "../src/index";

async function main(): Promise<void> {
  const appId = platformAppId("smoke");
  const routeName = platformRouteName("smoke.echo");
  const jobName = platformJobName("smoke.rebuild");
  const healthName = platformHealthName("smoke.readiness");

  if (!appId.ok || !routeName.ok || !jobName.ok || !healthName.ok) {
    throw new Error("Expected valid platform runtime primitives.");
  }

  const permission = "smoke:read";
  const lifecycleOrder: string[] = [];
  const app = definePlatformApp({
    id: appId.value,
    name: "Smoke",
    lifecycle: {
      beforeStart: () => {
        lifecycleOrder.push("app.beforeStart");
      },
      afterStart: () => {
        lifecycleOrder.push("app.afterStart");
      },
      beforeStop: () => {
        lifecycleOrder.push("app.beforeStop");
      },
      afterStop: () => {
        lifecycleOrder.push("app.afterStop");
      },
    },
    mount(registry) {
      registry.registerPermission({ permission });
      registry.registerRoute({
        name: routeName.value,
        method: "GET",
        path: "/echo",
        auth: { kind: "authenticated", permissions: [permission] },
        handler: { handle: () => ({ status: 200 }) },
      });
      registry.registerJob({
        name: jobName.value,
        messageType: "smoke.rebuild" as QueueMessageType,
        handler: { handle: () => undefined },
      });
      registry.registerHealthCheck({
        name: healthName.value,
        check: {
          check: () =>
            healthCheckResult({
              name: healthCheckName("smoke.readiness"),
              type: "readiness",
              component: monitoringComponent({ type: "runtime", name: "smoke" }),
              status: "healthy",
              checkedAt: "2026-07-10T00:00:00.000Z" as never,
            }),
        },
      });
    },
  });

  const mounted = await mountPlatformRuntimeApps({
    apps: [app],
    deps: createPlatformTestMountDeps(),
  });
  equal(mounted.ok, true);
  if (!mounted.ok) {
    throw new Error("Expected runtime app mount to pass.");
  }
  equal(mounted.value.routes.length, 1);
  equal(mounted.value.jobs.length, 1);
  equal(mounted.value.healthChecks.length, 1);

  const invalidMount = await mountPlatformRuntimeApps({
    apps: [
      definePlatformApp({
        id: appId.value,
        name: "Invalid",
        mount(registry) {
          registry.registerRoute({
            name: routeName.value,
            method: "GET",
            path: "/echo",
            auth: { kind: "authenticated", permissions: ["smoke:missing"] },
            handler: { handle: () => ({ status: 200 }) },
          });
        },
      }),
    ],
    deps: createPlatformTestMountDeps(),
  });
  equal(invalidMount.ok, false);
  if (invalidMount.ok) {
    throw new Error("Expected invalid mount to fail.");
  }
  equal(invalidMount.error.code, "PLATFORM_RUNTIME_REGISTRY_INVALID");
  equal(invalidMount.error.contractErrors.some((error) => error.code === "PLATFORM_CONTRACT_UNKNOWN_PERMISSION"), true);

  const duplicateApp = await mountPlatformRuntimeApps({
    apps: [app, app],
    deps: createPlatformTestMountDeps(),
  });
  equal(duplicateApp.ok, false);
  if (duplicateApp.ok) {
    throw new Error("Expected duplicate app mount to fail.");
  }
  equal(duplicateApp.error.contractErrors.some((error) => error.code === "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION"), true);

  const requestContext = createPlatformRuntimeRequestContext({
    requestId: "request-1" as CorrelationId,
    method: "GET",
    path: "/echo",
  });
  equal(requestContext.correlationId, "request-1");
  equal(requestContext.now, "2026-07-10T00:00:00.000Z");

  const message = createPlatformTestQueueMessage({
    type: "smoke.rebuild" as QueueMessageType,
    payload: { rebuild: true },
  });
  const jobContext = createPlatformRuntimeJobContext({
    jobName: jobName.value,
    message,
    correlationId: "job-1" as CorrelationId,
  });
  equal(jobContext.message.payload.rebuild, true);
  equal(jobContext.now, "2026-07-10T00:00:00.000Z");

  const resourceOrder: string[] = [];
  const lifecycle = createPlatformRuntimeLifecycle({
    apps: [app],
    resources: [
      {
        name: "primary",
        start: () => {
          resourceOrder.push("primary.start");
        },
        drain: () => {
          resourceOrder.push("primary.drain");
        },
        close: () => {
          resourceOrder.push("primary.close");
        },
      },
      {
        name: "secondary",
        start: () => {
          resourceOrder.push("secondary.start");
        },
        drain: () => {
          resourceOrder.push("secondary.drain");
        },
        close: () => {
          resourceOrder.push("secondary.close");
        },
      },
    ],
    telemetry: [
      {
        name: "metrics",
        flush: () => {
          resourceOrder.push("telemetry.flush");
        },
      },
    ],
  });
  equal(lifecycle.isReady(), false);
  equal((await lifecycle.start()).ok, true);
  equal(lifecycle.isReady(), true);
  const stopped = await lifecycle.shutdown();
  equal(stopped.ok, true);
  equal(lifecycle.isReady(), false);
  equal(lifecycle.state(), "stopped");
  deepEqual(lifecycleOrder, ["app.beforeStart", "app.afterStart", "app.beforeStop", "app.afterStop"]);
  deepEqual(resourceOrder, [
    "primary.start",
    "secondary.start",
    "primary.drain",
    "secondary.drain",
    "secondary.close",
    "primary.close",
    "telemetry.flush",
  ]);
  if (!stopped.ok) {
    throw new Error("Expected shutdown to pass.");
  }
  deepEqual(stopped.value.map((event) => event.phase), [
    "app.beforeStart",
    "resource.start",
    "resource.start",
    "app.afterStart",
    "app.beforeStop",
    "resource.drain",
    "resource.drain",
    "resource.close",
    "resource.close",
    "telemetry.flush",
    "app.afterStop",
  ]);

  const failedLifecycle = createPlatformRuntimeLifecycle({
    apps: [app],
    resources: [
      {
        name: "broken",
        start: () => {
          throw new Error("nope");
        },
      },
    ],
  });
  const failedStart = await failedLifecycle.start();
  equal(failedStart.ok, false);
  if (failedStart.ok) {
    throw new Error("Expected failed lifecycle start.");
  }
  equal(failedStart.error.code, "PLATFORM_RUNTIME_LIFECYCLE_FAILED");
  equal(failedLifecycle.isReady(), false);
}

main()
  .then(() => {
    console.log("platform/runtime runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
