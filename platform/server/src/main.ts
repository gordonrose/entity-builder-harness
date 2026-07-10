import { recordConfigSource, type ConfigRecord } from "@kanbien/core/config";
import type { Logger, LogRecord } from "@kanbien/core/logging";
import { noopMetrics } from "@kanbien/core/monitoring";
import { systemClock, type Result } from "@kanbien/core/shared";
import {
  fixedFeatureFlagReader,
  type PlatformApp,
  type PlatformMountDeps,
} from "@kanbien/platform-contracts";
import {
  createPlatformServerShell,
  type PlatformServerError,
  type PlatformServerHandle,
  type PlatformServerShell,
} from "./index";

export interface PlatformServerProcessOptions {
  readonly apps?: readonly PlatformApp[];
  readonly env?: NodeJS.ProcessEnv;
  readonly logger?: Logger;
  readonly port?: number;
  readonly host?: string;
  readonly installSignalHandlers?: boolean;
}

export interface PlatformServerProcess {
  readonly shell: PlatformServerShell;
  readonly handle: PlatformServerHandle;
  close(): Promise<void>;
}

export async function startPlatformServerProcess(
  options: PlatformServerProcessOptions = {},
): Promise<Result<PlatformServerProcess, PlatformServerError>> {
  const env = options.env ?? process.env;
  const logger = options.logger ?? consoleJsonLogger;
  const deps = createServerProcessMountDeps(env, logger);
  const shell = await createPlatformServerShell({
    apps: options.apps ?? [],
    deps,
    ...(env["PLATFORM_CORS_ORIGIN"] === undefined ? {} : { corsOrigin: env["PLATFORM_CORS_ORIGIN"] }),
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

  const handle = await shell.value.listen({
    port: options.port ?? numberFromEnv(env, "PORT", 3000),
    host: options.host ?? env["HOST"] ?? "0.0.0.0",
  });
  const processHandle = {
    shell: shell.value,
    handle,
    close: async () => {
      await handle.close();
      await shell.value.lifecycle.shutdown();
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

function createServerProcessMountDeps(env: NodeJS.ProcessEnv, logger: Logger): PlatformMountDeps {
  return {
    logger,
    metrics: noopMetrics,
    config: recordConfigSource(configRecordFromEnv(env)),
    flags: fixedFeatureFlagReader({}),
    clock: systemClock,
  };
}

function configRecordFromEnv(env: NodeJS.ProcessEnv): ConfigRecord {
  const values: Record<string, string> = {};

  for (const key of platformConfigEnvKeys) {
    const value = env[key];
    if (value !== undefined) {
      values[key] = value;
    }
  }

  return values;
}

function numberFromEnv(env: NodeJS.ProcessEnv, key: string, fallback: number): number {
  const value = env[key];
  if (value === undefined || value.length === 0) {
    return fallback;
  }

  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 && parsed <= 65_535 ? parsed : fallback;
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

const platformConfigEnvKeys = [
  "NODE_ENV",
  "HOST",
  "PORT",
  "PLATFORM_CORS_ORIGIN",
  "PLATFORM_SOURCE_COMMIT_SHA",
] as const;

if (typeof require !== "undefined" && require.main === module) {
  void runPlatformServerMain();
}
