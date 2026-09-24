import { recordConfigSource, type ConfigRecord } from "@kanbien/core/config";
import type { Logger, LogRecord } from "@kanbien/core/logging";
import { noopMetrics, type Metrics, type Tracer } from "@kanbien/core/monitoring";
import { systemClock, type Result } from "@kanbien/core/shared";
import { fixedFeatureFlagReader, type PlatformApp, type PlatformMountDeps } from "@kanbien/platform-contracts";
import type { PlatformWorkerError } from "./errors";
import type { PlatformWorkerDurableOutboxProcessingOptions, PlatformWorkerShell } from "./types";
import { createPlatformWorkerShell } from "./worker";

export interface PlatformWorkerProcessOptions {
  readonly apps?: readonly PlatformApp[];
  readonly configKeys?: readonly string[];
  readonly env?: NodeJS.ProcessEnv;
  readonly logger?: Logger;
  readonly tracer?: Tracer;
  readonly metrics?: Metrics;
  readonly durableOutboxProcessing?: PlatformWorkerDurableOutboxProcessingOptions;
  readonly maxAttempts?: number;
  readonly retryBackoffMs?: (attempt: number) => number;
  readonly installSignalHandlers?: boolean;
}

export interface PlatformWorkerProcess {
  readonly shell: PlatformWorkerShell;
  close(): Promise<void>;
}

export async function startPlatformWorkerProcess(
  options: PlatformWorkerProcessOptions = {},
): Promise<Result<PlatformWorkerProcess, PlatformWorkerError>> {
  const env = options.env ?? process.env;
  const logger = options.logger ?? consoleJsonLogger;
  const shell = await createPlatformWorkerShell({
    apps: options.apps ?? [],
    deps: createWorkerProcessMountDeps(env, logger, options.configKeys ?? [], options.metrics ?? noopMetrics),
    ...(options.durableOutboxProcessing === undefined ? {} : { durableOutboxProcessing: options.durableOutboxProcessing }),
    ...(options.tracer === undefined ? {} : { tracer: options.tracer }),
    ...(options.maxAttempts === undefined ? {} : { maxAttempts: options.maxAttempts }),
    ...(options.retryBackoffMs === undefined ? {} : { retryBackoffMs: options.retryBackoffMs }),
  });
  if (!shell.ok) return shell;

  const started = await shell.value.start();
  if (!started.ok) return started;

  const processHandle: PlatformWorkerProcess = {
    shell: shell.value,
    close: async () => {
      await shell.value.shutdown();
    },
  };

  if (options.installSignalHandlers ?? true) {
    installShutdownHandlers(processHandle, logger);
  }

  logger.write({ level: "info", message: "platform.worker.started" });
  return { ok: true, value: processHandle };
}

export async function runPlatformWorkerMain(): Promise<void> {
  const started = await startPlatformWorkerProcess();
  if (!started.ok) {
    console.error(JSON.stringify({
      level: "error",
      message: "platform.worker.start_failed",
      error: { code: started.error.code, message: started.error.defaultMessage },
    }));
    process.exitCode = 1;
    return;
  }

  if (process.env["PLATFORM_WORKER_EXIT_AFTER_START"] === "1") {
    await started.value.close();
  }
}

function createWorkerProcessMountDeps(
  env: NodeJS.ProcessEnv,
  logger: Logger,
  extraConfigKeys: readonly string[],
  metrics: Metrics,
): PlatformMountDeps {
  return {
    logger,
    metrics,
    config: recordConfigSource(configRecordFromEnv(env, extraConfigKeys)),
    flags: fixedFeatureFlagReader({}),
    clock: systemClock,
  };
}

function configRecordFromEnv(env: NodeJS.ProcessEnv, extraConfigKeys: readonly string[]): ConfigRecord {
  const values: Record<string, string> = {};
  for (const key of [...platformWorkerConfigEnvKeys, ...extraConfigKeys]) {
    const value = env[key];
    if (value !== undefined) values[key] = value;
  }
  return values;
}

function installShutdownHandlers(processHandle: PlatformWorkerProcess, logger: Logger): void {
  let shuttingDown = false;
  const shutdown = async (signal: NodeJS.Signals) => {
    if (shuttingDown) return;
    shuttingDown = true;
    logger.write({ level: "info", message: "platform.worker.shutdown", fields: { signal } });
    await processHandle.close();
  };
  process.once("SIGTERM", () => { void shutdown("SIGTERM"); });
  process.once("SIGINT", () => { void shutdown("SIGINT"); });
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

const platformWorkerConfigEnvKeys = [
  "NODE_ENV",
  "PLATFORM_SOURCE_COMMIT_SHA",
] as const;

if (typeof require !== "undefined" && require.main === module) {
  void runPlatformWorkerMain();
}
