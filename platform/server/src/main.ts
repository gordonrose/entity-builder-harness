import { recordConfigSource } from "@kanbien/core/config";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { platformRuntimeDiagnosticCatalog } from "@kanbien/platform-runtime";
import { selectDiagnosticEvidence } from "@kanbien/core/diagnostics";
import type { Logger, LogRecord } from "@kanbien/core/logging";
import { noopMetrics, type Metrics, type Tracer } from "@kanbien/core/monitoring";
import { systemClock, type Result } from "@kanbien/core/shared";
import { createPlatformDiagnosticReporter } from "@kanbien/platform-observability";
import { reportPlatformDiagnostic } from "@kanbien/platform-observability";
import {
  fixedFeatureFlagReader,
  type PlatformApp,
  type PlatformMountDeps,
  type PlatformDiagnosticCatalog,
} from "@kanbien/platform-contracts";
import {
  type PlatformAuthenticationHook,
  type PlatformRateLimiter,
} from "@kanbien/platform-security";
import {
  createPlatformServerShell,
  type PlatformServerError,
  type PlatformServerHandle,
  type PlatformClientAddressResolver,
  type PlatformServerShell,
  type PlatformServerTransportOptions,
} from "./index";
import { resolvePlatformServerRuntimeConfigurationWithDiagnostics } from "./configuration";
import { serverDiagnosticRecord, serverProcessBoundaryRecord, platformServerDiagnosticCatalog } from "./diagnostics";
import type { PlatformReleaseIdentity } from "./verification";

export interface PlatformServerProcessOptions {
  readonly securityDecisionDiagnostics?: boolean;
  readonly diagnosticCatalogs?: readonly PlatformDiagnosticCatalog[];
  readonly apps?: readonly PlatformApp[];
  readonly configKeys?: readonly string[];
  readonly env?: NodeJS.ProcessEnv;
  readonly logger?: Logger;
  readonly tracer?: Tracer;
  /**
   * Supplies a target-composed Core metrics sink without coupling the generic
   * server process to a provider, exporter, credential, or endpoint.
   */
  readonly metrics?: Metrics;
  readonly port?: number;
  readonly host?: string;
  readonly installSignalHandlers?: boolean;
  readonly auth?: PlatformAuthenticationHook;
  readonly rateLimiter?: PlatformRateLimiter;
  readonly clientAddressResolver?: PlatformClientAddressResolver;
  readonly transport?: PlatformServerTransportOptions;
}

export interface PlatformServerProcess {
  readonly shell: PlatformServerShell;
  readonly handle: PlatformServerHandle;
  readonly releaseIdentity: PlatformReleaseIdentity;
  close(): Promise<void>;
}

export async function startPlatformServerProcess(
  options: PlatformServerProcessOptions = {},
): Promise<Result<PlatformServerProcess, PlatformServerError>> {
  const env = options.env ?? process.env;
  const logger = options.logger ?? consoleJsonLogger;
  const observation = resolvePlatformServerRuntimeConfigurationWithDiagnostics({
    env,
    ...(options.configKeys === undefined ? {} : { extraConfigKeys: options.configKeys }),
    hasAuthentication: options.auth !== undefined,
    ...(options.host === undefined ? {} : { host: options.host }),
    ...(options.port === undefined ? {} : { port: options.port }),
  });
  const runtimeConfiguration = observation.configuration;
  const diagnostics = createPlatformDiagnosticReporter({ catalogs: [platformServerDiagnosticCatalog], logger, clock: systemClock });
  for (const record of observation.diagnosticRecords) {
    diagnostics.report(record, { capability: "platform-server", operation: "configure", stage: "configuration" });
  }
  const deps = createServerProcessMountDeps(runtimeConfiguration.config, logger, options.metrics ?? noopMetrics);
  const shell = await createPlatformServerShell({
    ...(options.diagnosticCatalogs === undefined ? {} : { diagnosticCatalogs: options.diagnosticCatalogs }),
    ...(options.securityDecisionDiagnostics === undefined ? {} : { securityDecisionDiagnostics: options.securityDecisionDiagnostics }),
    apps: options.apps ?? [],
    deps,
    ...(options.auth === undefined ? {} : { auth: options.auth }),
    ...(options.rateLimiter === undefined ? {} : { rateLimiter: options.rateLimiter }),
    ...(options.clientAddressResolver === undefined ? {} : { clientAddressResolver: options.clientAddressResolver }),
    ...(options.tracer === undefined ? {} : { tracer: options.tracer }),
    ...(options.transport === undefined ? {} : { transport: options.transport }),
    ...(runtimeConfiguration.corsOrigin === undefined ? {} : { corsOrigin: runtimeConfiguration.corsOrigin }),
    ...(runtimeConfiguration.corsAllowlist === undefined ? {} : { corsAllowlist: runtimeConfiguration.corsAllowlist }),
    healthExposure: runtimeConfiguration.healthExposure,
  });

  if (!shell.ok) {
    return shell;
  }

  const started = await shell.value.lifecycle.start();
  if (!started.ok) {
    return {
      ok: false,
      error: {
        code: "PLATFORM_SERVER_START_FAILED",
        defaultMessage: "Platform server lifecycle failed to start.",
        diagnosticRecord: started.error.diagnosticRecord ?? serverDiagnosticRecord("PLATFORM_SERVER_START_FAILED", "lifecycle"),
        ...(started.error.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: started.error.relatedDiagnosticRecords }),
        status: 500,
        details: { runtimeCode: started.error.code },
      },
    };
  }

  let handle: PlatformServerHandle;
  try {
    handle = await shell.value.listen({
      port: runtimeConfiguration.port,
      host: runtimeConfiguration.host,
    });
  } catch (error) {
    await shell.value.lifecycle.shutdown();
    let evidence = {};
    try { evidence = selectDiagnosticEvidence([
      ...coreDiagnosticCatalog.definitions,
      ...platformRuntimeDiagnosticCatalog.definitions,
      ...platformServerDiagnosticCatalog.definitions,
      ...shell.value.mounted.diagnosticCatalogs.flatMap((catalog) => catalog.definitions),
      ...(options.diagnosticCatalogs ?? []).flatMap((catalog) => catalog.definitions),
    ], error); } catch { /* Keep the historical startup failure if evidence is unavailable. */ }
    return {
      ok: false,
      error: {
        code: "PLATFORM_SERVER_START_FAILED",
        defaultMessage: "Platform server failed to listen.",
        diagnosticRecord: serverDiagnosticRecord("PLATFORM_SERVER_START_FAILED"),
        status: 500,
        ...evidence,
      },
    };
  }
  const processHandle = {
    shell: shell.value,
    handle,
    releaseIdentity: runtimeConfiguration.releaseIdentity,
    close: async () => {
      const draining = shell.value.lifecycle.beginDrain();
      if (!draining.ok) {
        try { logger.write({ level: "warn", message: "platform.server.drain_failed", fields: { code: draining.error.code } }); }
        catch (error) {
          reportPlatformDiagnostic(diagnostics, serverProcessBoundaryRecord("shutdown-log", "shutdown-not-completed"), { capability: "platform-server", operation: "shutdown", stage: "shutdown" });
          throw error;
        }
      }
      try {
        await handle.close();
      } finally {
        await shell.value.lifecycle.shutdown();
      }
    },
  };

  if (options.installSignalHandlers ?? true) {
    try { installShutdownHandlers(processHandle, logger, diagnostics); }
    catch (error) {
      reportPlatformDiagnostic(diagnostics, serverProcessBoundaryRecord("signal-registration", "process-not-returned"), { capability: "platform-server", operation: "start", stage: "startup" });
      throw error;
    }
  }

  try { logger.write({
    level: "info",
    message: "platform.server.started",
    fields: {
      port: handle.port,
      ...(runtimeConfiguration.releaseIdentity.sourceCommitSha === undefined
        ? {}
        : { sourceCommitSha: runtimeConfiguration.releaseIdentity.sourceCommitSha }),
    },
  }); } catch (error) {
    reportPlatformDiagnostic(diagnostics, serverProcessBoundaryRecord("startup-log", "process-not-returned"), { capability: "platform-server", operation: "start", stage: "startup" });
    throw error;
  }

  return { ok: true, value: processHandle };
}

export async function runPlatformServerMain(): Promise<void> {
  const started = await startPlatformServerProcess();
  if (!started.ok) {
    console.error(JSON.stringify({
      level: "error",
      message: "platform.server.start_failed",
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

function createServerProcessMountDeps(
  config: import("@kanbien/core/config").ConfigRecord,
  logger: Logger,
  metrics: Metrics,
): PlatformMountDeps {
  return {
    logger,
    metrics,
    config: recordConfigSource(config),
    flags: fixedFeatureFlagReader({}),
    clock: systemClock,
  };
}


function installShutdownHandlers(processHandle: PlatformServerProcess, logger: Logger, diagnostics: import("@kanbien/platform-contracts").PlatformDiagnosticReporter): void {
  let shuttingDown = false;
  const shutdown = async (signal: NodeJS.Signals) => {
    if (shuttingDown) {
      return;
    }
    shuttingDown = true;
    try { logger.write({ level: "info", message: "platform.server.shutdown", fields: { signal } }); }
    catch (error) {
      reportPlatformDiagnostic(diagnostics, serverProcessBoundaryRecord("shutdown-log", "shutdown-not-completed"), { capability: "platform-server", operation: "shutdown", stage: "shutdown" });
      throw error;
    }
    await processHandle.close();
  };

  process.once("SIGTERM", () => {
    void shutdown("SIGTERM");
  });
  process.once("SIGINT", () => {
    void shutdown("SIGINT");
  });
}

const consoleJsonLogger: Logger = {
  write: (record: LogRecord) => {
    const line = JSON.stringify(record);
    if (record.level === "error") {
      console.error(line);
      return;
    }

    console.log(line);
  },
};

if (typeof require !== "undefined" && require.main === module) {
  void runPlatformServerMain();
}
