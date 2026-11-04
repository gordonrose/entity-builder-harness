// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-main
//   version: 4
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-11-02"
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

import { selectPersistenceImplementation } from "./kanbien-core-server-persistence-composition";
import type { Logger } from "@kanbien/core/logging";
import { coreDiagnosticCatalog } from "@kanbien/core";
import type { Metrics } from "@kanbien/core/monitoring";
import { createPlatformDiagnosticReporter, createPlatformReadinessObserver, createPlatformSafeLogger, platformObservabilityDiagnosticCatalog, reportPlatformDiagnostic } from "@kanbien/platform-observability";
import { persistenceDiagnosticCodes, platformPersistenceDiagnosticCatalog } from "@kanbien/platform-persistence";
import { persistenceConfigurationResult, persistenceCertificateAuthorityResult, persistenceTaskDiagnosticFields, persistenceStartupDiagnosticBinding } from "./kanbien-core-server-persistence-configuration";
import { platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformContractDiagnosticCatalog, type PlatformDiagnosticCatalog } from "@kanbien/platform-contracts";
import { persistenceIamAuthenticationResult } from "./kanbien-core-server-persistence-iam-authentication";
import { resolvePlatformReleaseIdentity } from "@kanbien/platform-server";
import { startPlatformServerProcess, type PlatformServerProcess } from "@kanbien/platform-server/main";
import { createKanbienCoreServerPersistenceApp } from "./kanbien-core-server-persistence.app";
import type { KanbienCorePersistenceRuntime } from "./kanbien-core-server-persistence.app";
import { observabilityConfigurationFromTargetEnvironment, createTargetObservabilityRuntime } from "./kanbien-platform-observability";

export async function runKanbienCoreServerPersistenceMain(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const selected = selectPersistenceImplementation(env["PERSISTENCE_IMPLEMENTATION"]);
  if (!selected.ok) return startupFailed("configuration-invalid", selected.error.diagnostic);
  const parsed = persistenceConfigurationResult(env, "server", selected.value);
  if (!parsed.ok) return startupFailed("configuration-invalid", parsed.error.diagnostic);
  const configuration = parsed.value;
  const authentication = persistenceIamAuthenticationResult(env, configuration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME");
  if (!authentication.ok) return startupFailed("runtime-iam-authentication-invalid", authentication.error.diagnostic);
  const credentials = authentication.value;
  const authority = persistenceCertificateAuthorityResult(env);
  if (!authority.ok) return startupFailed("tls-authority-unavailable", authority.error.diagnostic);
  const certificateAuthority = authority.value;

  const telemetry = observabilityConfigurationFromTargetEnvironment(env, true);
  if (!telemetry.ok) return startupFailed(telemetry.error.code, telemetry.error.diagnosticRecord);

  const logger = createPlatformSafeLogger(consoleLogger);
  const resourceDiagnostics = createPlatformDiagnosticReporter({ catalogs: [coreDiagnosticCatalog, platformPersistenceDiagnosticCatalog, platformSecurityDiagnosticCatalog],
    logger, clock: { now: () => new Date() } });
  const pool = selected.value.createPool(configuration, { ...credentials, certificateAuthority }, {
    diagnosticDefinitions: platformSecurityDiagnosticCatalog.definitions,
    onDiagnostic: (record) => reportPlatformDiagnostic(resourceDiagnostics, record, { capability: "persistence", operation: "connection-resource", stage: "runtime" }),
  });
  const persistence = selected.value.createRuntime({ pool, schema: configuration.schema });
  const observability = persistenceObservabilityFromTargetEnvironment(telemetry.value, persistence);
  if (!observability.ok) {
    await persistence.close();
    return startupFailed(observability.code, observability.diagnostic);
  }
  const started = await startPlatformServerProcess({
    diagnosticCatalogs: [platformPersistenceDiagnosticCatalog],
    apps: [createKanbienCoreServerPersistenceApp(resolvePlatformReleaseIdentity(env["PLATFORM_SOURCE_COMMIT_SHA"]), persistence)],
    env,
    logger,
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
  stop(): Promise<void>;
  close(): Promise<void>;
};

function persistenceObservabilityFromTargetEnvironment(
  configuration: Extract<ReturnType<typeof observabilityConfigurationFromTargetEnvironment>, { ok: true }>["value"],
  persistence: KanbienCorePersistenceRuntime,
): { readonly ok: true; readonly value: PersistenceObservability } | { readonly ok: false; readonly code: string; readonly diagnostic: DiagnosticRecord } {
  const metrics = createTargetObservabilityRuntime(configuration.options);
  if (!metrics.ok) return { ok: false, code: metrics.error.code, diagnostic: metrics.error.diagnosticRecord };
  if (metrics.value === undefined || configuration.readiness === undefined) return { ok: true, value: noObservability };
  const metricsRuntime = metrics.value;
  const readinessSchedule = configuration.readiness;

  const logger = createPlatformSafeLogger(consoleLogger);
  const readinessCatalogs: readonly PlatformDiagnosticCatalog[] = [coreDiagnosticCatalog, platformPersistenceDiagnosticCatalog, platformSecurityDiagnosticCatalog, platformObservabilityDiagnosticCatalog, platformContractDiagnosticCatalog];
  const readinessDiagnostics = createPlatformDiagnosticReporter({ catalogs: readinessCatalogs, logger, clock: { now: () => new Date() } });
  const observer = createPlatformReadinessObserver({
    identity: readinessSchedule.identity,
    probe: async () => persistence.readinessObservation !== undefined ? persistence.readinessObservation() : ({
      readiness: await persistence.readiness(), diagnosticCode: "persistence.unclassified-failure",
    }),
    diagnostics: readinessDiagnostics,
    observations: { reporter: readinessDiagnostics, definitions: readinessCatalogs.flatMap((catalog) => catalog.definitions),
      context: { capability: "observability", operation: "readiness-observation", stage: "readiness" } },
    logger,
    metrics: metrics.value.metrics,
    clock: { now: () => new Date() },
    timeoutMs: readinessSchedule.timeoutMs,
    allowedDiagnosticCodes: persistenceDiagnosticCodes,
    defaultDiagnosticCode: "persistence.unclassified-failure",
  });
  let timer: NodeJS.Timeout | undefined;
  let stopped = false;
  let started = false;
  let closed = false;
  let observing: Promise<void> = Promise.resolve();
  const observe = (): Promise<void> => {
    observing = observer.observe().then(() => undefined).catch(() => {
      console.error(JSON.stringify({ level: "warn", message: "kanbien-core-server-persistence.readiness_observation_failed" }));
    }).finally(() => {
      if (!stopped) timer = setTimeout(() => { void observe(); }, readinessSchedule.cadenceMs);
    });
    return observing;
  };
  const stop = async (): Promise<void> => {
    stopped = true;
    if (timer !== undefined) clearTimeout(timer);
    await observing;
  };
  return {
    ok: true,
    value: {
      metrics: metricsRuntime.metrics,
      start: async () => {
        if (started || stopped) return;
        started = true;
        await observe();
      },
      stop,
      close: async () => {
        if (closed) return;
        closed = true;
        await stop();
        try { await metricsRuntime.shutdown(); } catch { console.error(JSON.stringify({ level: "warn", message: "kanbien-core-server-persistence.observability_shutdown_failed" })); }
      },
    },
  };
}

const noObservability: PersistenceObservability = {
  start: async () => undefined,
  stop: async () => undefined,
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
  await observability.stop();
  try { await server.close(); } finally { await observability.close(); }
}

const consoleLogger: Logger = {
  write: (record) => {
    const line = JSON.stringify(record);
    if (record.level === "error") console.error(line); else console.log(line);
  },
};

function startupFailed(code: string, diagnostic?: DiagnosticRecord): void {
  process.exitCode = 1;
  const context = diagnostic === undefined ? undefined : persistenceStartupDiagnosticBinding.select(diagnostic)?.context;
  try { console.error(JSON.stringify({
    level: "error",
    message: "kanbien-core-server-persistence.start_failed",
    error: { code, message: "The persistence-capable core server could not start safely." },
    ...persistenceTaskDiagnosticFields(diagnostic),
    ...(context === undefined ? {} : { diagnostic_context: context }),
  })); } catch { /* Failed diagnostic output does not change startup failure or retry work. */ }
}

if (typeof require !== "undefined" && require.main === module) {
  void runKanbienCoreServerPersistenceMain();
}
