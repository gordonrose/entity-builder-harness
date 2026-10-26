// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-main
//   version: 2
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-26"
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

import { systemClock } from "@kanbien/core/shared";
import type { Logger } from "@kanbien/core/logging";
import { createPlatformReadinessObserver } from "@kanbien/platform-observability";
import { observabilityFromTargetEnvironment, readinessObservationFromTargetEnvironment } from "./kanbien-platform-observability";
import {
  createNodePostgreSqlTokenConnectionPool,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { persistenceConfiguration, persistenceCertificateAuthority } from "./kanbien-core-server-persistence-configuration";
import { persistenceIamAuthentication } from "./kanbien-core-server-persistence-iam-authentication";
import { resolvePlatformReleaseIdentity } from "@kanbien/platform-server";
import { startPlatformServerProcess } from "@kanbien/platform-server/main";
import { createKanbienCoreServerPersistenceApp } from "./kanbien-core-server-persistence.app";
import { createKanbienCoreServerPostgreSqlPersistenceRuntime } from "./kanbien-core-server-persistence-postgresql";

export async function runKanbienCoreServerPersistenceMain(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const configuration = persistenceConfiguration(env, "server");
  if (configuration === undefined) return startupFailed("configuration-invalid");
  const credentials = persistenceIamAuthentication(env, configuration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME");
  if (credentials === undefined) return startupFailed("runtime-iam-authentication-invalid");
  const certificateAuthority = persistenceCertificateAuthority(env);
  if (certificateAuthority === undefined) return startupFailed("tls-authority-unavailable");

  const observation = readinessObservationFromTargetEnvironment(env);
  if (!observation.ok) return startupFailed(observation.error.code);
  const observability = observabilityFromTargetEnvironment(env);
  if (!observability.ok) return startupFailed(observability.error.code);
  const logger: Logger = { write: (record) => console.log(JSON.stringify(record)) };
  const pool = createNodePostgreSqlTokenConnectionPool(configuration, { ...credentials, certificateAuthority });
  const persistence = createKanbienCoreServerPostgreSqlPersistenceRuntime({ pool, schema: configuration.schema });
  const started = await startPlatformServerProcess({
    apps: [createKanbienCoreServerPersistenceApp(resolvePlatformReleaseIdentity(env["PLATFORM_SOURCE_COMMIT_SHA"]), persistence)],
    env,
    logger,
    ...(observability.value === undefined ? {} : { metrics: observability.value.metrics }),
    installSignalHandlers: false,
  });
  if (!started.ok) {
    await persistence.close();
    await observability.value?.shutdown();
    return startupFailed(started.error.code);
  }
  // The composition owns this timer and exporter together with the server.
  // No request traffic is needed to prove that the dependency remains ready.
  let timer: ReturnType<typeof setTimeout> | undefined;
  let stopped = false;
  let observing: Promise<unknown> = Promise.resolve();
  if (observation.value !== undefined && observability.value !== undefined) {
    const options = observation.value;
    const observer = createPlatformReadinessObserver({
      identity: options.identity,
      probe: async () => ({ readiness: await persistence.readiness() }),
      logger, metrics: observability.value.metrics, clock: systemClock,
      timeoutMs: options.timeoutMs,
      allowedDiagnosticCodes: ["persistence.readiness-not-ready"],
      defaultDiagnosticCode: "persistence.readiness-not-ready",
    });
    const observe = () => {
      observing = observer.observe().catch(() => {
        console.error(JSON.stringify({ level: "warn", message: "persistence.readiness_observation_failed" }));
      }).finally(() => { if (!stopped) timer = setTimeout(observe, options.cadenceMs); });
    };
    observe();
  }
  const close = async () => {
    if (stopped) return;
    stopped = true;
    if (timer !== undefined) clearTimeout(timer);
    await observing;
    try { await started.value.close(); }
    finally { await observability.value?.shutdown(); }
  };
  if (env["PLATFORM_SERVER_EXIT_AFTER_START"] === "1") await close();
  else {
    process.once("SIGTERM", () => { void close(); });
    process.once("SIGINT", () => { void close(); });
  }
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
