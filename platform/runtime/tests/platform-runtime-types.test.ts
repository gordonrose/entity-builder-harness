import type { QueueMessageType } from "@kanbien/core/queues";
import type { CorrelationId } from "@kanbien/core/shared";
import {
  definePlatformApp,
  platformAppId,
  platformJobName,
  type PlatformJobContext,
  type PlatformRequestContext,
} from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps, createPlatformTestQueueMessage } from "@kanbien/platform-testing";
import {
  createPlatformRuntimeContextDeps,
  createPlatformRuntimeJobContext,
  createPlatformRuntimeLifecycle,
  createPlatformRuntimeRegistry,
  createPlatformRuntimeRequestContext,
  mountPlatformRuntimeApps,
  type PlatformRuntimeLifecycleController,
  type PlatformRuntimeMountResult,
} from "../src/index";

const appId = platformAppId("smoke");
const jobName = platformJobName("smoke.rebuild");
if (!appId.ok || !jobName.ok) {
  throw new Error("Expected valid runtime type primitives.");
}

const deps = createPlatformRuntimeContextDeps();
void deps;

const registry = createPlatformRuntimeRegistry();
void registry.routes();

const requestContext: PlatformRequestContext = createPlatformRuntimeRequestContext({
  requestId: "request-1" as CorrelationId,
  method: "POST",
  path: "/smoke",
});
void requestContext;

const message = createPlatformTestQueueMessage({
  type: "smoke.rebuild" as QueueMessageType,
  payload: { rebuild: true },
});
const jobContext: PlatformJobContext = createPlatformRuntimeJobContext({
  jobName: jobName.value,
  message,
  correlationId: "job-1" as CorrelationId,
});
void jobContext;

const app = definePlatformApp({
  id: appId.value,
  name: "Smoke",
  mount: () => undefined,
});

const mounted: Promise<import("@kanbien/core/shared").Result<PlatformRuntimeMountResult, unknown>> = mountPlatformRuntimeApps({
  apps: [app],
  deps: createPlatformTestMountDeps(),
});
void mounted;

const lifecycle: PlatformRuntimeLifecycleController = createPlatformRuntimeLifecycle({ apps: [app] });
void lifecycle.state();

// @ts-expect-error request context method is constrained to known HTTP methods.
createPlatformRuntimeRequestContext({ requestId: "request-1" as CorrelationId, method: "TRACE", path: "/smoke" });

// @ts-expect-error lifecycle resources require a stable resource name.
createPlatformRuntimeLifecycle({ apps: [app], resources: [{ start: () => undefined }] });
