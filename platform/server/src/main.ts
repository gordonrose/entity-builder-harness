import { recordConfigSource } from "@kanbien/core/config";
import type { Logger, LogRecord } from "@kanbien/core/logging";
import { noopMetrics, type Metrics, type Tracer } from "@kanbien/core/monitoring";
import { systemClock, type Result } from "@kanbien/core/shared";
import {
  fixedFeatureFlagReader,
  type PlatformApp,
  type PlatformMountDeps,
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
import { resolvePlatformServerRuntimeConfiguration } from "./configuration";
import type { PlatformReleaseIdentity } from "./verification";

export interface PlatformServerProcessOptions {
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
  const runtimeConfiguration = resolvePlatformServerRuntimeConfiguration({
    env,
    ...(options.configKeys === undefined ? {} : { extraConfigKeys: options.configKeys }),
    hasAuthentication: options.auth !== undefined,
  });
  const deps = createServerProcessMountDeps(runtimeConfiguration.config, logger, options.metrics ?? noopMetrics);
  const shell = await createPlatformServerShell({
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
        status: 500,
        details: { runtimeCode: started.error.code },
      },
    };
  }

  let handle: PlatformServerHandle;
  try {
    handle = await shell.value.listen({
      port: options.port ?? runtimeConfiguration.port,
      host: options.host ?? runtimeConfiguration.host,
    });
  } catch {
    await shell.value.lifecycle.shutdown();
    return {
      ok: false,
      error: {
        code: "PLATFORM_SERVER_START_FAILED",
        defaultMessage: "Platform server failed to listen.",
        status: 500,
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
        logger.write({ level: "warn", message: "platform.server.drain_failed", fields: { code: draining.error.code } });
      }
      try {
        await handle.close();
      } finally {
        await shell.value.lifecycle.shutdown();
      }
    },
  };

  if (options.installSignalHandlers ?? true) {
    installShutdownHandlers(processHandle, logger);
  }

  logger.write({
    level: "info",
    message: "platform.server.started",
    fields: {
      port: handle.port,
      host: handle.host ?? "0.0.0.0",
      ...(runtimeConfiguration.releaseIdentity.sourceCommitSha === undefined
        ? {}
        : { sourceCommitSha: runtimeConfiguration.releaseIdentity.sourceCommitSha }),
    },
  });

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


function installShutdownHandlers(processHandle: PlatformServerProcess, logger: Logger): void {
  let shuttingDown = false;
  const shutdown = async (signal: NodeJS.Signals) => {
    if (shuttingDown) {
      return;
    }
    shuttingDown = true;
    logger.write({ level: "info", message: "platform.server.shutdown", fields: { signal } });
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
