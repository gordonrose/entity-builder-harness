// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-server
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: infra.ci-cd
//   disciplines:
//   - architecture
//   - sre
//   kind: code
//   purpose: Start the platform server shell with the Kanbien Platform product app composition.
//   portability:
//     class: internal
//     targets: []
//   used_by:
//   - id: infra.04-deploy.03-product.image.dockerfile
//     path: infra/04.deploy/03.product/image/Dockerfile

import {
  kanbienPlatformApps,
  kanbienPlatformProductManifest,
} from "@kanbien/product-kanbien-platform";
import { startPlatformServerProcess } from "@kanbien/platform-server/main";

export async function runKanbienPlatformServerMain(): Promise<void> {
  const started = await startPlatformServerProcess({
    apps: kanbienPlatformApps,
    configKeys: productConfigKeys(),
  });

  if (!started.ok) {
    console.error(JSON.stringify({
      level: "error",
      message: "kanbien-platform.server.start_failed",
      error: {
        code: started.error.code,
        message: started.error.defaultMessage,
      },
    }));
    process.exitCode = 1;
    return;
  }

  if (process.env["PLATFORM_SERVER_EXIT_AFTER_START"] === "1") {
    await started.value.close();
  }
}

function productConfigKeys(): readonly string[] {
  return [...new Set(kanbienPlatformProductManifest.apps.flatMap((app) => app.requiredConfig))];
}

if (typeof require !== "undefined" && require.main === module) {
  void runKanbienPlatformServerMain();
}
