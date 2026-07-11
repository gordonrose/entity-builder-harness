import { deepEqual, equal } from "node:assert/strict";
import { configError } from "@kanbien/core/config";
import { healthCheckName, monitoringComponent, healthCheckResult } from "@kanbien/core/monitoring";
import type { QueueMessageType } from "@kanbien/core/queues";
import { validationIssue } from "@kanbien/core/validation";
import {
  definePlatformApp,
  platformAppId,
  platformHealthName,
  platformJobName,
  platformRouteName,
} from "@kanbien/platform-contracts";
import {
  createPlatformTestJobContext,
  createPlatformTestQueueMessage,
  createPlatformTestRequestContext,
  mountPlatformAppForTest,
  runPlatformTestHealthChecks,
  validatePlatformTestConfigSchemas,
} from "../src/index";

async function main(): Promise<void> {
  const appId = platformAppId("smoke");
  const routeName = platformRouteName("smoke.echo");
  const jobName = platformJobName("smoke.rebuild");
  const healthName = platformHealthName("smoke.readiness");

  if (!appId.ok || !routeName.ok || !jobName.ok || !healthName.ok) {
    throw new Error("Expected valid platform test primitives.");
  }

  const lifecycleCalls: string[] = [];
  const permission = "smoke:read";
  const app = definePlatformApp({
    id: appId.value,
    name: "Smoke",
    lifecycle: {
      beforeStart: () => {
        lifecycleCalls.push("beforeStart");
      },
    },
    mount(registry) {
      registry.registerPermission({ permission });
      registry.registerRoute({
        name: routeName.value,
        method: "GET",
        path: "/echo",
        auth: { kind: "authenticated", permissions: [permission] },
        handler: { handle: () => ({ status: 200, body: { ok: true } }) },
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
              metadata: { dependency: "ready" },
            }),
        },
      });
      registry.registerConfigSchema({
        parse: () => ({ ok: true, value: { enabled: true } }),
      });
    },
  });

  const mounted = await mountPlatformAppForTest(app);
  equal(mounted.ok, true);
  if (!mounted.ok) {
    throw new Error("Expected smoke app to mount.");
  }
  equal(mounted.value.permissions.length, 1);
  equal(mounted.value.routes.length, 1);
  equal(mounted.value.jobs.length, 1);
  equal(mounted.value.healthChecks.length, 1);
  equal(mounted.value.configSchemas.length, 1);
  equal(typeof mounted.value.lifecycle?.beforeStart, "function");

  mounted.value.lifecycle?.beforeStart?.();
  deepEqual(lifecycleCalls, ["beforeStart"]);

  const config = validatePlatformTestConfigSchemas(mounted.value.configSchemas);
  equal(config.ok, true);

  const health = await runPlatformTestHealthChecks(mounted.value.healthChecks);
  equal(health.ok, true);
  if (!health.ok) {
    throw new Error("Expected safe health output.");
  }
  equal(health.value[0]?.status, "healthy");

  const requestContext = createPlatformTestRequestContext({ path: "/echo" });
  equal(requestContext.path, "/echo");

  const message = createPlatformTestQueueMessage({
    type: "smoke.rebuild" as QueueMessageType,
    payload: { rebuild: true },
  });
  const jobContext = createPlatformTestJobContext({ jobName: jobName.value, message });
  equal(jobContext.message.payload.rebuild, true);

  await assertMountContractError(
    definePlatformApp({
      id: appId.value,
      name: "Duplicate Route",
      mount(registry) {
        registry.registerRoute({
          name: routeName.value,
          method: "GET",
          path: "/echo",
          auth: { kind: "public" },
          handler: { handle: () => ({ status: 200 }) },
        });
        registry.registerRoute({
          name: routeName.value,
          method: "GET",
          path: "/echo-again",
          auth: { kind: "public" },
          handler: { handle: () => ({ status: 200 }) },
        });
      },
    }),
    "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION",
  );

  await assertMountContractError(
    definePlatformApp({
      id: appId.value,
      name: "Unknown Permission",
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
    "PLATFORM_CONTRACT_UNKNOWN_PERMISSION",
  );

  await assertMountContractError(
    definePlatformApp({
      id: appId.value,
      name: "Reserved Path",
      mount(registry) {
        registry.registerRoute({
          name: routeName.value,
          method: "GET",
          path: "/readyz",
          auth: { kind: "public" },
          handler: { handle: () => ({ status: 200 }) },
        });
      },
    }),
    "PLATFORM_CONTRACT_RESERVED_PATH",
  );

  await assertMountContractError(
    definePlatformApp({
      id: appId.value,
      name: "Duplicate Job",
      mount(registry) {
        registry.registerJob({
          name: jobName.value,
          messageType: "smoke.rebuild" as QueueMessageType,
          handler: { handle: () => undefined },
        });
        registry.registerJob({
          name: jobName.value,
          messageType: "smoke.refresh" as QueueMessageType,
          handler: { handle: () => undefined },
        });
      },
    }),
    "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION",
  );

  const invalidConfig = validatePlatformTestConfigSchemas([
    {
      parse: () => ({
        ok: false,
        error: configError("CONFIG_INVALID", [
          validationIssue({
            path: ["config", "smoke"],
            code: "SMOKE_CONFIG_INVALID",
            defaultMessage: "Smoke config is invalid.",
          }),
        ]),
      }),
    },
  ]);
  equal(invalidConfig.ok, false);
  if (invalidConfig.ok) {
    throw new Error("Expected invalid config to fail.");
  }
  equal(invalidConfig.error.code, "PLATFORM_TEST_INVALID_CONFIG");

  const unsafeHealth = await runPlatformTestHealthChecks([
    {
      name: healthName.value,
      check: {
        check: () =>
          healthCheckResult({
            name: healthCheckName("smoke.readiness"),
            type: "readiness",
            component: monitoringComponent({ type: "runtime", name: "smoke" }),
            status: "healthy",
            checkedAt: "2026-07-10T00:00:00.000Z" as never,
            metadata: { token: "do-not-log" },
          }),
      },
    },
  ]);
  equal(unsafeHealth.ok, false);
  if (unsafeHealth.ok) {
    throw new Error("Expected unsafe health output to fail.");
  }
  equal(unsafeHealth.error.code, "PLATFORM_TEST_UNSAFE_HEALTH_OUTPUT");
}

async function assertMountContractError(
  app: Parameters<typeof mountPlatformAppForTest>[0],
  code: string,
): Promise<void> {
  const mounted = await mountPlatformAppForTest(app);
  equal(mounted.ok, false);
  if (mounted.ok) {
    throw new Error(`Expected mount to fail with ${code}.`);
  }
  equal(mounted.error.contractErrors.some((error) => error.code === code), true);
}

main()
  .then(() => {
    console.log("platform/testing runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
