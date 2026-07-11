import type { QueueMessageType } from "@kanbien/core/queues";
import {
  definePlatformApp,
  platformAppId,
  platformJobName,
  type PlatformJobContext,
  type PlatformRequestContext,
} from "@kanbien/platform-contracts";
import {
  createPlatformTestConfigSource,
  createPlatformTestJobContext,
  createPlatformTestLogger,
  createPlatformTestMetrics,
  createPlatformTestMountDeps,
  createPlatformTestQueueMessage,
  createPlatformTestRegistry,
  createPlatformTestRequestContext,
  mountPlatformAppForTest,
  type PlatformTestMountResult,
} from "../src/index";

const appId = platformAppId("smoke");
const jobName = platformJobName("smoke.rebuild");
if (!appId.ok || !jobName.ok) {
  throw new Error("Expected valid testing type primitives.");
}

const logger = createPlatformTestLogger();
logger.write({ level: "info", message: "hello" });
const records = logger.records();
void records;

const metrics = createPlatformTestMetrics();
void metrics.points();

const config = createPlatformTestConfigSource({ ENABLED: true });
const deps = createPlatformTestMountDeps({ logger, metrics, config });
void deps;

const registry = createPlatformTestRegistry();
registry.registerPermission({ permission: "smoke:read" });
void registry.permissions();

const requestContext: PlatformRequestContext = createPlatformTestRequestContext({ path: "/smoke" });
void requestContext;

const message = createPlatformTestQueueMessage({
  type: "smoke.rebuild" as QueueMessageType,
  payload: { rebuild: true },
});
const jobContext: PlatformJobContext = createPlatformTestJobContext({ jobName: jobName.value, message });
void jobContext;

const app = definePlatformApp({
  id: appId.value,
  name: "Smoke",
  mount: () => undefined,
});

const mounted: Promise<import("@kanbien/core/shared").Result<PlatformTestMountResult, unknown>> = mountPlatformAppForTest(app);
void mounted;

// @ts-expect-error platform test queue messages require a branded queue message type.
createPlatformTestQueueMessage({ type: "smoke.rebuild" });

// @ts-expect-error test mount deps still require the platform contract shape.
createPlatformTestMountDeps({ logger: { write: "not-a-function" } });
