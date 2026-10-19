import { type ConfigRecord } from "@kanbien/core/config";
import { resolvePlatformReleaseIdentity, type PlatformReleaseIdentity } from "../verification";

export type PlatformServerHealthEndpointExposure = "public" | "authenticated";

export interface PlatformServerRuntimeConfiguration {
  readonly config: ConfigRecord;
  readonly host: string;
  readonly port: number;
  readonly corsOrigin?: string;
  readonly corsAllowlist?: readonly string[];
  readonly healthExposure: {
    readonly liveness: PlatformServerHealthEndpointExposure;
    readonly readiness: PlatformServerHealthEndpointExposure;
  };
  readonly releaseIdentity: PlatformReleaseIdentity;
}

export function resolvePlatformServerRuntimeConfiguration(input: {
  readonly env: NodeJS.ProcessEnv;
  readonly extraConfigKeys?: readonly string[];
  readonly hasAuthentication?: boolean;
}): PlatformServerRuntimeConfiguration {
  const env = input.env;
  const hasAuthentication = input.hasAuthentication ?? false;
  const corsOrigin = nonEmptyValue(env["PLATFORM_CORS_ORIGIN"]);
  const corsAllowlist = csvEnv(env["PLATFORM_CORS_ALLOWLIST"]);

  return {
    config: configRecordFromEnv(env, input.extraConfigKeys ?? []),
    host: nonEmptyValue(env["HOST"]) ?? "0.0.0.0",
    port: positivePort(env["PORT"]) ?? 3_000,
    ...(corsOrigin === undefined ? {} : { corsOrigin }),
    ...(corsAllowlist.length === 0 ? {} : { corsAllowlist }),
    healthExposure: {
      liveness: healthExposureFromEnv(env["PLATFORM_HEALTH_LIVEZ_EXPOSURE"], "public"),
      readiness: healthExposureFromEnv(
        env["PLATFORM_HEALTH_READYZ_EXPOSURE"],
        hasAuthentication ? "authenticated" : "public",
      ),
    },
    releaseIdentity: resolvePlatformReleaseIdentity(env["PLATFORM_SOURCE_COMMIT_SHA"]),
  };
}

const platformServerConfigEnvKeys = [
  "NODE_ENV",
  "HOST",
  "PORT",
  "PLATFORM_CORS_ORIGIN",
  "PLATFORM_CORS_ALLOWLIST",
  "PLATFORM_HEALTH_LIVEZ_EXPOSURE",
  "PLATFORM_HEALTH_READYZ_EXPOSURE",
  "PLATFORM_SOURCE_COMMIT_SHA",
] as const;

function configRecordFromEnv(env: NodeJS.ProcessEnv, extraConfigKeys: readonly string[]): ConfigRecord {
  const values: Record<string, string> = {};
  for (const key of [...platformServerConfigEnvKeys, ...extraConfigKeys]) {
    const value = env[key];
    if (value !== undefined) {
      values[key] = value;
    }
  }
  return values;
}

function positivePort(value: string | undefined): number | undefined {
  if (value === undefined || value.length === 0) {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 && parsed <= 65_535 ? parsed : undefined;
}

function csvEnv(value: string | undefined): readonly string[] {
  if (value === undefined) {
    return [];
  }
  return value.split(",").map((item) => item.trim()).filter((item) => item.length > 0);
}

function healthExposureFromEnv(
  value: string | undefined,
  fallback: PlatformServerHealthEndpointExposure,
): PlatformServerHealthEndpointExposure {
  return value === "authenticated" || value === "public" ? value : fallback;
}

function nonEmptyValue(value: string | undefined): string | undefined {
  return value === undefined || value.length === 0 ? undefined : value;
}
