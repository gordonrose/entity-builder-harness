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
  createNodePostgreSqlTokenConnectionPool,
} from "@kanbien/platform-adapter-aws-persistence-postgresql";
import type { Logger } from "@kanbien/core/logging";
import type { Metrics } from "@kanbien/core/monitoring";
import { createPlatformReadinessObserver, createPlatformSafeLogger } from "@kanbien/platform-observability";
import { persistenceConfiguration, persistenceCertificateAuthority } from "./kanbien-core-server-persistence-configuration";
import { persistenceIamAuthentication } from "./kanbien-core-server-persistence-iam-authentication";
import { resolvePlatformReleaseIdentity } from "@kanbien/platform-server";
import { startPlatformServerProcess, type PlatformServerProcess } from "@kanbien/platform-server/main";
import { createKanbienCoreServerPersistenceApp } from "./kanbien-core-server-persistence.app";
import { createKanbienCoreServerPostgreSqlPersistenceRuntime } from "./kanbien-core-server-persistence-postgresql";
import { observabilityFromTargetEnvironment, readinessObservationFromTargetEnvironment } from "./kanbien-platform-observability";

export async function runKanbienCoreServerPersistenceMain(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const configuration = persistenceConfiguration(env, "server");
  if (configuration === undefined) return startupFailed("configuration-invalid");
  const credentials = persistenceIamAuthentication(env, configuration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME");
  if (credentials === undefined) return startupFailed("runtime-iam-authentication-invalid");
  const certificateAuthority = persistenceCertificateAuthority(env);
  if (certificateAuthority === undefined) return startupFailed("tls-authority-unavailable");

  const pool = createNodePostgreSqlTokenConnectionPool(configuration, { ...credentials, certificateAuthority });
  const persistence = createKanbienCoreServerPostgreSqlPersistenceRuntime({ pool, schema: configuration.schema });
  const observability = persistenceObservabilityFromTargetEnvironment(env, persistence);
  if (!observability.ok) {
    await persistence.close();
    return startupFailed(observability.code);
  }
  const started = await startPlatformServerProcess({
    apps: [createKanbienCoreServerPersistenceApp(resolvePlatformReleaseIdentity(env["PLATFORM_SOURCE_COMMIT_SHA"]), persistence)],
    env,
    ...(observability.value.metrics === undefined ? {} : { metrics: observability.value.metrics }),
    installSignalHandlers: false,
  });
  if (!started.ok) {
    await persistence.close();
    await observability.value.close();
    return startupFailed(started.error.code);
  }
  await observability.value.start();
  if (env["PLATFORM_SERVER_EXIT_AFTER_START"] === "1") {
    await closeTargetProcess(started.value, observability.value);
    return;
  }
  installTargetShutdownHandlers(started.value, observability.value);
}

type PersistenceObservability = {
  readonly metrics?: Metrics;
  start(): Promise<void>;
  close(): Promise<void>;
};

function persistenceObservabilityFromTargetEnvironment(
  env: NodeJS.ProcessEnv,
  persistence: ReturnType<typeof createKanbienCoreServerPostgreSqlPersistenceRuntime>,
): { readonly ok: true; readonly value: PersistenceObservability } | { readonly ok: false; readonly code: string } {
  const metrics = observabilityFromTargetEnvironment(env);
  const schedule = readinessObservationFromTargetEnvironment(env);
  if (!metrics.ok || !schedule.ok) return { ok: false, code: "KANBIEN_PLATFORM_TARGET_OBSERVABILITY_CONFIG_INVALID" };
  if ((metrics.value === undefined) !== (schedule.value === undefined)) return { ok: false, code: "KANBIEN_PLATFORM_TARGET_OBSERVABILITY_CONFIG_INVALID" };
  if (metrics.value === undefined || schedule.value === undefined) return { ok: true, value: noObservability };
  const metricsRuntime = metrics.value;
  const readinessSchedule = schedule.value;

  const logger = createPlatformSafeLogger(consoleLogger);
  const observer = createPlatformReadinessObserver({
    identity: readinessSchedule.identity,
    probe: async () => ({
      readiness: await persistence.readiness(),
      // The server-side persistence seam deliberately hides raw driver errors.
      // Until a provider adapter supplies an allowlisted machine-code mapping,
      // retain that truth as a closed unclassified dependency failure.
      diagnosticCode: "persistence.unclassified-failure",
    }),
    logger,
    metrics: metrics.value.metrics,
    clock: { now: () => new Date() },
    timeoutMs: readinessSchedule.timeoutMs,
    allowedDiagnosticCodes: ["persistence.unclassified-failure"],
    defaultDiagnosticCode: "persistence.unclassified-failure",
  });
  let timer: NodeJS.Timeout | undefined;
  const observe = async (): Promise<void> => {
    try {
      await observer.observe();
    } catch {
      // A target telemetry delivery or instrumentation failure cannot turn an
      // otherwise live server into a business outage. The stale-signal alarm
      // owns detection of sustained missing observations.
      console.error(JSON.stringify({ level: "warn", message: "kanbien-core-server-persistence.readiness_observation_failed" }));
    }
  };
  return {
    ok: true,
    value: {
      metrics: metricsRuntime.metrics,
      start: async () => {
        await observe();
        timer = setInterval(() => { void observe(); }, readinessSchedule.cadenceMs);
      },
      close: async () => {
        if (timer !== undefined) clearInterval(timer);
        try { await metricsRuntime.shutdown(); } catch { console.error(JSON.stringify({ level: "warn", message: "kanbien-core-server-persistence.observability_shutdown_failed" })); }
      },
    },
  };
}

const noObservability: PersistenceObservability = {
  start: async () => undefined,
  close: async () => undefined,
};

function installTargetShutdownHandlers(server: PlatformServerProcess, observability: PersistenceObservability): void {
  let shuttingDown = false;
  const shutdown = async () => {
    if (shuttingDown) return;
    shuttingDown = true;
    await closeTargetProcess(server, observability);
  };
  process.once("SIGTERM", () => { void shutdown(); });
  process.once("SIGINT", () => { void shutdown(); });
}

async function closeTargetProcess(server: PlatformServerProcess, observability: PersistenceObservability): Promise<void> {
  try { await server.close(); } finally { await observability.close(); }
}

const consoleLogger: Logger = {
  write: (record) => {
    const line = JSON.stringify(record);
    if (record.level === "error") console.error(line); else console.log(line);
  },
};

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
