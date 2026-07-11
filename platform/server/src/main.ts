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
  createCognitoAccessTokenVerifier,
  createJwtBearerAuthenticationHook,
  type PlatformClaimPermissionMapping,
  type PlatformAuthzPermissionMapping,
} from "@kanbien/platform-security";
import {
  createPlatformServerShell,
  type PlatformServerError,
  type PlatformServerAuthHook,
  type PlatformServerHandle,
  type PlatformServerShell,
} from "./index";

export interface PlatformServerProcessOptions {
  readonly apps?: readonly PlatformApp[];
  readonly configKeys?: readonly string[];
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
  const deps = createServerProcessMountDeps(env, logger, options.configKeys ?? []);
  const auth = createServerProcessAuthHook(env, deps.clock);
  if (!auth.ok) {
    return auth;
  }
  const shell = await createPlatformServerShell({
    apps: options.apps ?? [],
    deps,
    ...(auth.value === undefined ? {} : { auth: auth.value }),
    ...(env["PLATFORM_CORS_ORIGIN"] === undefined ? {} : { corsOrigin: env["PLATFORM_CORS_ORIGIN"] }),
    ...(env["PLATFORM_CORS_ALLOWLIST"] === undefined ? {} : { corsAllowlist: csvEnv(env["PLATFORM_CORS_ALLOWLIST"]) }),
    healthExposure: {
      liveness: healthExposureFromEnv(env["PLATFORM_HEALTH_LIVEZ_EXPOSURE"], "public"),
      readiness: healthExposureFromEnv(env["PLATFORM_HEALTH_READYZ_EXPOSURE"], auth.value === undefined ? "public" : "authenticated"),
    },
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

function createServerProcessAuthHook(
  env: NodeJS.ProcessEnv,
  clock: PlatformMountDeps["clock"],
): Result<PlatformServerAuthHook | undefined, PlatformServerError> {
  const provider = env["PLATFORM_AUTH_PROVIDER"];
  if (provider === undefined || provider.length === 0 || provider === "none") {
    return { ok: true, value: undefined };
  }

  if (provider !== "cognito") {
    return serverConfigError({
      path: "PLATFORM_AUTH_PROVIDER",
      reason: "Unsupported platform auth provider.",
    });
  }

  const region = requiredEnv(env, "PLATFORM_AUTH_COGNITO_REGION");
  const userPoolId = requiredEnv(env, "PLATFORM_AUTH_COGNITO_USER_POOL_ID");
  const appClientId = requiredEnv(env, "PLATFORM_AUTH_COGNITO_APP_CLIENT_ID");
  if (!region.ok) {
    return region;
  }
  if (!userPoolId.ok) {
    return userPoolId;
  }
  if (!appClientId.ok) {
    return appClientId;
  }

  const authz = authzMappingFromEnv(env);
  if (!authz.ok) {
    return authz;
  }

  return {
    ok: true,
    value: createJwtBearerAuthenticationHook({
      verifier: createCognitoAccessTokenVerifier({
        region: region.value,
        userPoolId: userPoolId.value,
        appClientId: appClientId.value,
        clock,
      }),
      authz: authz.value,
    }),
  };
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
  env: NodeJS.ProcessEnv,
  logger: Logger,
  extraConfigKeys: readonly string[],
): PlatformMountDeps {
  return {
    logger,
    metrics: noopMetrics,
    config: recordConfigSource(configRecordFromEnv(env, extraConfigKeys)),
    flags: fixedFeatureFlagReader({}),
    clock: systemClock,
  };
}

function configRecordFromEnv(env: NodeJS.ProcessEnv, extraConfigKeys: readonly string[]): ConfigRecord {
  const values: Record<string, string> = {};

  for (const key of [...platformConfigEnvKeys, ...extraConfigKeys]) {
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

function authzMappingFromEnv(env: NodeJS.ProcessEnv): Result<PlatformAuthzPermissionMapping, PlatformServerError> {
  const groups = permissionMapFromJsonEnv(env, "PLATFORM_AUTHZ_GROUP_PERMISSIONS");
  const scopes = permissionMapFromJsonEnv(env, "PLATFORM_AUTHZ_SCOPE_PERMISSIONS");
  const claims = claimPermissionMappingsFromJsonEnv(env, "PLATFORM_AUTHZ_CLAIM_PERMISSIONS");

  if (!groups.ok) {
    return groups;
  }
  if (!scopes.ok) {
    return scopes;
  }
  if (!claims.ok) {
    return claims;
  }

  return {
    ok: true,
    value: {
      groups: groups.value,
      scopes: scopes.value,
      claims: claims.value,
    },
  };
}

function permissionMapFromJsonEnv(
  env: NodeJS.ProcessEnv,
  key: string,
): Result<Readonly<Record<string, readonly `${string}:${string}`[]>>, PlatformServerError> {
  const raw = env[key];
  if (raw === undefined || raw.length === 0) {
    return { ok: true, value: {} };
  }

  const parsed = parseJsonEnv(raw, key);
  if (!parsed.ok) {
    return parsed;
  }

  if (typeof parsed.value !== "object" || parsed.value === null || Array.isArray(parsed.value)) {
    return serverConfigError({ path: key, reason: "Expected a JSON object mapping strings to permission arrays." });
  }

  const value: Record<string, `${string}:${string}`[]> = {};
  for (const [mappingKey, permissions] of Object.entries(parsed.value)) {
    if (!Array.isArray(permissions) || !permissions.every(isPermissionString)) {
      return serverConfigError({ path: key, reason: "Expected every mapped value to be an array of permission strings." });
    }
    value[mappingKey] = permissions;
  }

  return { ok: true, value };
}

function claimPermissionMappingsFromJsonEnv(
  env: NodeJS.ProcessEnv,
  key: string,
): Result<readonly PlatformClaimPermissionMapping[], PlatformServerError> {
  const raw = env[key];
  if (raw === undefined || raw.length === 0) {
    return { ok: true, value: [] };
  }

  const parsed = parseJsonEnv(raw, key);
  if (!parsed.ok) {
    return parsed;
  }

  if (!Array.isArray(parsed.value)) {
    return serverConfigError({ path: key, reason: "Expected a JSON array of claim permission mappings." });
  }

  const claims: PlatformClaimPermissionMapping[] = [];
  for (const item of parsed.value) {
    if (
      typeof item !== "object"
      || item === null
      || Array.isArray(item)
      || typeof item["claim" as keyof typeof item] !== "string"
      || !isClaimEqualsValue(item["equals" as keyof typeof item])
      || !Array.isArray(item["permissions" as keyof typeof item])
      || !(item["permissions" as keyof typeof item] as unknown[]).every(isPermissionString)
    ) {
      return serverConfigError({ path: key, reason: "Expected claim, equals, and permissions fields for every claim mapping." });
    }

    claims.push({
      claim: item["claim" as keyof typeof item] as string,
      equals: item["equals" as keyof typeof item] as string | number | boolean,
      permissions: item["permissions" as keyof typeof item] as `${string}:${string}`[],
    });
  }

  return { ok: true, value: claims };
}

function requiredEnv(env: NodeJS.ProcessEnv, key: string): Result<string, PlatformServerError> {
  const value = env[key];
  if (value !== undefined && value.length > 0) {
    return { ok: true, value };
  }

  return serverConfigError({ path: key, reason: "Required environment value is missing." });
}

function parseJsonEnv(raw: string, key: string): Result<unknown, PlatformServerError> {
  try {
    return { ok: true, value: JSON.parse(raw) as unknown };
  } catch {
    return serverConfigError({ path: key, reason: "Expected valid JSON." });
  }
}

function serverConfigError(input: { readonly path: string; readonly reason: string }): Result<never, PlatformServerError> {
  return {
    ok: false,
    error: {
      code: "PLATFORM_SERVER_CONFIG_INVALID",
      defaultMessage: "Platform server config validation failed before listen.",
      status: 500,
      details: {
        issues: [
          {
            path: [input.path],
            code: "PLATFORM_SERVER_CONFIG_INVALID",
            defaultMessage: input.reason,
          },
        ],
      },
    },
  };
}

function isPermissionString(value: unknown): value is `${string}:${string}` {
  return typeof value === "string" && /^[^:\s]+:[^:\s]+$/.test(value);
}

function isClaimEqualsValue(value: unknown): value is string | number | boolean {
  return typeof value === "string" || typeof value === "number" || typeof value === "boolean";
}

function csvEnv(value: string): readonly string[] {
  return value.split(",").map((item) => item.trim()).filter((item) => item.length > 0);
}

function healthExposureFromEnv(
  value: string | undefined,
  fallback: "public" | "authenticated",
): "public" | "authenticated" {
  return value === "authenticated" || value === "public" ? value : fallback;
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
  "PLATFORM_CORS_ALLOWLIST",
  "PLATFORM_AUTH_PROVIDER",
  "PLATFORM_AUTH_COGNITO_REGION",
  "PLATFORM_AUTH_COGNITO_USER_POOL_ID",
  "PLATFORM_AUTH_COGNITO_APP_CLIENT_ID",
  "PLATFORM_AUTHZ_GROUP_PERMISSIONS",
  "PLATFORM_AUTHZ_SCOPE_PERMISSIONS",
  "PLATFORM_AUTHZ_CLAIM_PERMISSIONS",
  "PLATFORM_HEALTH_LIVEZ_EXPOSURE",
  "PLATFORM_HEALTH_READYZ_EXPOSURE",
  "PLATFORM_SOURCE_COMMIT_SHA",
] as const;

if (typeof require !== "undefined" && require.main === module) {
  void runPlatformServerMain();
}
