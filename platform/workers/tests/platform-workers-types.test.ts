import type { QueueMessageType } from "@kanbien/core/queues";
import {
  definePlatformApp,
  platformAppId,
  type PlatformApp,
} from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps, createPlatformTestQueueMessage } from "@kanbien/platform-testing";
import {
  createInMemoryPlatformWorkerQueue,
  createPlatformWorkerShell,
  type PlatformWorkerQueue,
  type PlatformWorkerRunNextResult,
  type PlatformWorkerShell,
} from "../src/index";

const appId = platformAppId("smoke");
if (!appId.ok) {
  throw new Error("Expected valid worker type primitives.");
}

const app: PlatformApp = definePlatformApp({
  id: appId.value,
  name: "Smoke",
  mount: () => undefined,
});

const queue: PlatformWorkerQueue = createInMemoryPlatformWorkerQueue();
const message = createPlatformTestQueueMessage({
  type: "smoke.rebuild" as QueueMessageType,
  payload: { rebuild: true },
});
queue.enqueue(message);
void queue.pending();

const shell: Promise<import("@kanbien/core/shared").Result<PlatformWorkerShell, unknown>> = createPlatformWorkerShell({
  apps: [app],
  deps: createPlatformTestMountDeps(),
  queue,
});
void shell;

const result: PlatformWorkerRunNextResult = { status: "idle" };
void result;

const healthResult: ReturnType<PlatformWorkerShell["health"]> = Promise.resolve({
  status: "ready",
  checkedAt: "2026-07-10T00:00:00.000Z" as never,
  checks: [],
});
void healthResult;

// @ts-expect-error worker queues accept core QueueMessage values, not arbitrary objects.
queue.enqueue({ type: "smoke.rebuild" });

// @ts-expect-error maxAttempts must be numeric.
createPlatformWorkerShell({ apps: [app], deps: createPlatformTestMountDeps(), maxAttempts: "two" });
