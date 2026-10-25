// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-main
//   version: 2
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-25"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Start the persistence-capable core server with the reviewed PostgreSQL adapter and injected runtime credentials.
//   portability:
//     class: internal
//     targets:
//     - kanbien-core-platform
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import {
  createNodePostgreSqlConnectionPool,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { persistenceConfiguration, persistenceCredentials, persistenceCertificateAuthority } from "./kanbien-core-server-persistence-configuration";
import { resolvePlatformReleaseIdentity } from "@kanbien/platform-server";
import { startPlatformServerProcess } from "@kanbien/platform-server/main";
import { createKanbienCoreServerPersistenceApp } from "./kanbien-core-server-persistence.app";
import { createKanbienCoreServerPostgreSqlPersistenceRuntime } from "./kanbien-core-server-persistence-postgresql";

export async function runKanbienCoreServerPersistenceMain(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const configuration = persistenceConfiguration(env, "server");
  if (configuration === undefined) return startupFailed("configuration-invalid");
  const credentials = persistenceCredentials(env["PERSISTENCE_RUNTIME_CREDENTIALS"]);
  if (credentials === undefined) return startupFailed("runtime-credentials-invalid");
  const certificateAuthority = persistenceCertificateAuthority(env);
  if (certificateAuthority === undefined) return startupFailed("tls-authority-unavailable");

  const pool = createNodePostgreSqlConnectionPool(configuration, { ...credentials, certificateAuthority });
  const persistence = createKanbienCoreServerPostgreSqlPersistenceRuntime({ pool, schema: configuration.schema });
  const started = await startPlatformServerProcess({
    apps: [createKanbienCoreServerPersistenceApp(resolvePlatformReleaseIdentity(env["PLATFORM_SOURCE_COMMIT_SHA"]), persistence)],
    env,
  });
  if (!started.ok) {
    await persistence.close();
    return startupFailed(started.error.code);
  }
  if (env["PLATFORM_SERVER_EXIT_AFTER_START"] === "1") await started.value.close();
}

function startupFailed(code: string): void {
  console.error(JSON.stringify({
    level: "error",
    message: "kanbien-core-server-persistence.start_failed",
    error: { code, message: "The persistence-capable core server could not start safely." },
  }));
  process.exitCode = 1;
}

if (typeof require !== "undefined" && require.main === module) {
  void runKanbienCoreServerPersistenceMain();
}
