import { equal } from "node:assert/strict";
import { configError, type ConfigSchema } from "@kanbien/core/config";
import type { QueueIdempotencyKey, QueueMessageType } from "@kanbien/core/queues";
import { validationIssue } from "@kanbien/core/validation";
import {
  definePlatformApp,
  platformAppId,
  platformJobName,
} from "@kanbien/platform-contracts";
import {
  createPlatformTestLogger,
  createPlatformTestMetrics,
  createPlatformTestMountDeps,
  createPlatformTestQueueMessage,
  validatorForTest,
} from "@kanbien/platform-testing";
import {
  createInMemoryPlatformWorkerIdempotencyStore,
  createPlatformWorkerShell,
} from "../src/index";

async function main(): Promise<void> {
  const appId = platformAppId("smoke");
  const jobName = platformJobName("smoke.rebuild");
  const failingJobName = platformJobName("smoke.failing");
  if (!appId.ok || !jobName.ok || !failingJobName.ok) {
    throw new Error("Expected valid worker test primitives.");
  }

  let handled = 0;
  let failingAttempts = 0;
  const logger = createPlatformTestLogger();
  const metrics = createPlatformTestMetrics();
  const deps = createPlatformTestMountDeps({ logger, metrics });
  const app = definePlatformApp({
    id: appId.value,
    name: "Smoke",
    mount(registry) {
      registry.registerJob({
        name: jobName.value,
        messageType: "smoke.rebuild" as QueueMessageType,
        validator: validatorForTest((value): value is { readonly rebuild: boolean } =>
          typeof value === "object"
          && value !== null
          && "rebuild" in value
          && typeof (value as { readonly rebuild?: unknown }).rebuild === "boolean"),
        handler: {
          handle: () => {
            handled += 1;
          },
        },
      });
      registry.registerJob({
        name: failingJobName.value,
        messageType: "smoke.failing" as QueueMessageType,
        handler: {
          handle: () => {
            failingAttempts += 1;
            throw new Error("fail");
          },
        },
      });
    },
  });

  const idempotency = createInMemoryPlatformWorkerIdempotencyStore();
  const shell = await createPlatformWorkerShell({ apps: [app], deps, idempotency, maxAttempts: 2, retryBackoffMs: () => 25 });
  equal(shell.ok, true);
  if (!shell.ok) {
    throw new Error("Expected worker shell to mount.");
  }

  const beforeStart = await shell.value.runNext();
  equal(beforeStart.ok, false);
  if (beforeStart.ok) {
    throw new Error("Expected run before start to fail.");
  }
  equal(beforeStart.error.code, "PLATFORM_WORKER_NOT_READY");

  equal((await shell.value.start()).ok, true);
  const ready = await shell.value.health();
  equal(ready.status, "ready");

  const successMessage = {
    ...createPlatformTestQueueMessage({
      id: "success-1",
      type: "smoke.rebuild" as QueueMessageType,
      payload: { rebuild: true },
    }),
    idempotencyKey: "idem-1" as QueueIdempotencyKey,
  };
  equal(shell.value.enqueue(successMessage).ok, true);
  const success = await shell.value.runNext();
  equal(success.ok, true);
  if (!success.ok) {
    throw new Error("Expected worker success.");
  }
  equal(success.value.status, "succeeded");
  if (success.value.status !== "succeeded") {
    throw new Error("Expected succeeded status.");
  }
  equal(success.value.idempotency, "processed");
  equal(handled, 1);

  equal(shell.value.enqueue(successMessage).ok, true);
  const skipped = await shell.value.runNext();
  equal(skipped.ok, true);
  if (!skipped.ok || skipped.value.status !== "succeeded") {
    throw new Error("Expected idempotency skip to succeed.");
  }
  equal(skipped.value.idempotency, "skipped");
  equal(handled, 1);

  equal(shell.value.enqueue(createPlatformTestQueueMessage({
    id: "invalid-1",
    type: "smoke.rebuild" as QueueMessageType,
    payload: { rebuild: "nope" },
  })).ok, true);
  const invalid = await shell.value.runNext();
  equal(invalid.ok, true);
  if (!invalid.ok || invalid.value.status !== "dead-lettered") {
    throw new Error("Expected invalid payload to dead-letter.");
  }
  equal(invalid.value.error.code, "PLATFORM_WORKER_INVALID_PAYLOAD");

  equal(shell.value.enqueue(createPlatformTestQueueMessage({
    id: "failing-1",
    type: "smoke.failing" as QueueMessageType,
    payload: { ok: true },
  })).ok, true);
  const retry = await shell.value.runNext();
  equal(retry.ok, true);
  if (!retry.ok || retry.value.status !== "retry") {
    throw new Error("Expected failing job to retry.");
  }
  equal(retry.value.nextAttempt, 2);
  equal(retry.value.delayMs, 25);

  const deadLetter = await shell.value.runNext();
  equal(deadLetter.ok, true);
  if (!deadLetter.ok || deadLetter.value.status !== "dead-lettered") {
    throw new Error("Expected failing job to dead-letter after retry.");
  }
  equal(deadLetter.value.error.code, "PLATFORM_WORKER_HANDLER_FAILED");
  equal(failingAttempts, 2);
  equal(shell.value.queue.deadLetters().length, 2);
  equal(metrics.points().length, 5);
  equal(logger.records().some((record) => record.message === "platform.worker.job.dead_lettered"), true);

  const idle = await shell.value.runUntilIdle();
  equal(idle.ok, true);
  if (!idle.ok) {
    throw new Error("Expected runUntilIdle to pass.");
  }
  equal(idle.value.at(-1)?.status, "idle");

  equal((await shell.value.shutdown()).ok, true);
  const notReady = await shell.value.health();
  equal(notReady.status, "not-ready");
  equal(shell.value.enqueue(createPlatformTestQueueMessage({
    id: "closed-1",
    type: "smoke.rebuild" as QueueMessageType,
    payload: { rebuild: true },
  })).ok, false);

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
  const invalidConfigShell = await createPlatformWorkerShell({
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
    equal(invalidConfigShell.error.code, "PLATFORM_WORKER_CONFIG_INVALID");
    equal(JSON.stringify(invalidConfigShell.error.details).includes("do-not-leak"), false);
  }
}

main()
  .then(() => {
    console.log("platform/workers runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
