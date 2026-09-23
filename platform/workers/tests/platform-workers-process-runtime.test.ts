import { equal } from "node:assert/strict";
import { definePlatformApp, platformAppId } from "@kanbien/platform-contracts";
import { createPlatformTestLogger } from "@kanbien/platform-testing";
import { startPlatformWorkerProcess } from "../src/index";

async function main(): Promise<void> {
  const appId = platformAppId("worker-process-test");
  if (!appId.ok) throw new Error("Expected a valid app ID.");

  const logger = createPlatformTestLogger();
  const started = await startPlatformWorkerProcess({
    apps: [definePlatformApp({ id: appId.value, name: "Worker process test", mount: () => undefined })],
    logger,
    installSignalHandlers: false,
  });
  equal(started.ok, true);
  if (!started.ok) throw new Error("Expected worker process to start.");
  equal((await started.value.shell.health()).status, "ready");
  await started.value.close();
  equal((await started.value.shell.health()).status, "not-ready");
  equal(logger.records().some((record) => record.message === "platform.worker.started"), true);
  console.log("platform/workers process runtime test passed.");
}

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
