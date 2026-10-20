// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server
//   version: 1
//   status: draft
//   layer: 04.deploy
//   domain: deployment.bootstrap-runtime
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Start the dependency-free Kanbien core bootstrap server and expose only its safe release-verification operation.
//   portability:
//     class: internal
//     targets: []
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoints.runnable-program-index
//     path: infra/04.deploy/03.product/entrypoints/runnable-program-index.yml

import {
  definePlatformApp,
  platformAppId,
  platformCapabilityName,
  platformObservabilityProfileName,
  platformRouteName,
  type PlatformApp,
  type PlatformCapabilityObservabilityProfile,
} from "@kanbien/platform-contracts";
import {
  platformReleaseVerificationResponse,
  resolvePlatformReleaseIdentity,
  type PlatformReleaseIdentity,
} from "@kanbien/platform-server";
import { startPlatformServerProcess } from "@kanbien/platform-server/main";

const coreServerAppId = requiredPlatformName(platformAppId("kanbien-core-server"));
const releaseVerificationRouteName = requiredPlatformName(platformRouteName("kanbien-core-server.release.verify"));
const releaseVerificationProfileName = requiredPlatformName(
  platformObservabilityProfileName("kanbien-core-server.release.verify"),
);

const releaseVerificationProfile: PlatformCapabilityObservabilityProfile = {
  name: releaseVerificationProfileName,
  capability: requiredPlatformName(platformCapabilityName("kanbien-core-server.release")),
  action: "verify",
  signals: ["operational_log", "metric", "trace"],
  logFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  metricDimensionFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  traceAttributeNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  nfrObjectives: [{ nfrClass: "interactive_read", measurement: "request_response_latency" }],
};

/**
 * The later target scope makes this route private. The program deliberately
 * supplies no application authentication, product application, provider
 * adapter, persistence service, queue, or public-ingress composition.
 */
export function createKanbienCoreServerVerificationApp(
  releaseIdentity: PlatformReleaseIdentity,
): PlatformApp {
  return definePlatformApp({
    id: coreServerAppId,
    name: "Kanbien Core Server",
    mount(registry) {
      registry.registerObservabilityProfile(releaseVerificationProfile);
      registry.registerRoute({
        name: releaseVerificationRouteName,
        method: "GET",
        path: "/internal/release-verification",
        auth: { kind: "public" },
        observability: { kind: "profile", profile: releaseVerificationProfileName },
        handler: {
          handle: () => ({
            status: 200,
            body: platformReleaseVerificationResponse(releaseIdentity),
          }),
        },
      });
    },
  });
}

export async function runKanbienCoreServerMain(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const releaseIdentity = resolvePlatformReleaseIdentity(env["PLATFORM_SOURCE_COMMIT_SHA"]);
  const started = await startPlatformServerProcess({
    apps: [createKanbienCoreServerVerificationApp(releaseIdentity)],
    env,
  });

  if (!started.ok) {
    console.error(JSON.stringify({
      level: "error",
      message: "kanbien-core-server.start_failed",
      error: {
        code: started.error.code,
        message: started.error.defaultMessage,
      },
    }));
    process.exitCode = 1;
    return;
  }

  if (env["PLATFORM_SERVER_EXIT_AFTER_START"] === "1") {
    await started.value.close();
  }
}

function requiredPlatformName<T>(result: { readonly ok: true; readonly value: T } | { readonly ok: false }): T {
  if (!result.ok) {
    throw new Error("KANBIEN_CORE_SERVER_DECLARATION_INVALID");
  }
  return result.value;
}

if (typeof require !== "undefined" && require.main === module) {
  void runKanbienCoreServerMain();
}
