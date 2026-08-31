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
import { createCognitoJwtBearerAuthenticationHookFromEnv } from "@kanbien/platform-adapter-aws-auth-cognito";
import { startPlatformServerProcess } from "@kanbien/platform-server/main";

export async function runKanbienPlatformServerMain(): Promise<void> {
  const authentication = authenticationFromTargetEnvironment(process.env);
  if (!authentication.ok) {
    console.error(JSON.stringify({ level: "error", message: "kanbien-platform.server.auth_configuration_invalid", error: authentication.error }));
    process.exitCode = 1;
    return;
  }

  const started = await startPlatformServerProcess({
    apps: kanbienPlatformApps,
    configKeys: productConfigKeys(),
    ...(authentication.value === undefined ? {} : { auth: authentication.value }),
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

function authenticationFromTargetEnvironment(env: NodeJS.ProcessEnv) {
  const provider = env["PLATFORM_AUTH_PROVIDER"];
  if (provider === undefined || provider.length === 0 || provider === "none") {
    return { ok: true as const, value: undefined };
  }
  if (provider === "cognito") {
    return createCognitoJwtBearerAuthenticationHookFromEnv(env);
  }

  return {
    ok: false as const,
    error: {
      code: "KANBIEN_PLATFORM_TARGET_AUTH_PROVIDER_INVALID",
      defaultMessage: "The Kanbien platform target selected an unsupported authentication provider.",
      details: { path: "PLATFORM_AUTH_PROVIDER", reason: "The target composition does not have an adapter for this provider." },
    },
  };
}

if (typeof require !== "undefined" && require.main === module) {
  void runKanbienPlatformServerMain();
}
