import { type ConfigRecord } from "@kanbien/core/config";
import { createDiagnosticRecord, type DiagnosticRecord, type DiagnosticDefinition } from "@kanbien/core/diagnostics";
import { serverListenerConfigurationDiagnostic, serverPortConfigurationFallbackDiagnostic, serverHealthExposureSelectionDiagnostic, serverHealthExposureFallbackDiagnostic, serverConfigurationOmissionRecord, type serverPortFallbackReasons } from "../diagnostics";
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

export interface PlatformServerRuntimeConfigurationInput {
  readonly env: NodeJS.ProcessEnv;
  readonly extraConfigKeys?: readonly string[];
  readonly hasAuthentication?: boolean;
}

export interface PlatformServerRuntimeConfigurationObservation {
  readonly configuration: PlatformServerRuntimeConfiguration;
  readonly diagnosticRecords: readonly DiagnosticRecord[];
}

/** Compatibility projection: no new fields, logging or rejection semantics. */
export function resolvePlatformServerRuntimeConfiguration(input: PlatformServerRuntimeConfigurationInput): PlatformServerRuntimeConfiguration {
  return resolvePlatformServerRuntimeConfigurationWithDiagnostics({
    env: input.env,
    extraConfigKeys: input.extraConfigKeys ?? [],
    hasAuthentication: input.hasAuthentication ?? false,
  }).configuration;
}

/** Resolve each choice and its evidence together; supplied values never enter records. */
export function resolvePlatformServerRuntimeConfigurationWithDiagnostics(input: PlatformServerRuntimeConfigurationInput & {
  readonly host?: string;
  readonly port?: number;
}): PlatformServerRuntimeConfigurationObservation {
  const env = input.env;
  const hasAuthentication = input.hasAuthentication ?? false;
  const rawCorsOrigin = env["PLATFORM_CORS_ORIGIN"];
  const corsOrigin = nonEmptyValue(rawCorsOrigin);
  const rawCorsAllowlist = env["PLATFORM_CORS_ALLOWLIST"];
  const corsAllowlist = csvEnv(rawCorsAllowlist);
  const records: DiagnosticRecord[] = [];
  const rawHost = env["HOST"];
  const rawPort = env["PORT"];
  const host = input.host ?? nonEmptyValue(rawHost) ?? "0.0.0.0";
  let port: number;
  records.push(listenerSelection("http.host", input.host, rawHost));
  if (input.port != null) {
    port = input.port;
    records.push(listenerSelection("http.port", input.port, rawPort));
  } else {
    const parsed = portSelection(rawPort);
    port = parsed.port;
    records.push(parsed.reason === undefined ? listenerSelection("http.port", undefined, rawPort)
      : configurationRecord(serverPortConfigurationFallbackDiagnostic, { phase: "configuration", setting: "http.port", source: "default", reason: parsed.reason, effect: "default-selected" }));
  }
  const liveness = healthSelection("http.health.liveness-exposure", env["PLATFORM_HEALTH_LIVEZ_EXPOSURE"], "public", records);
  const readiness = healthSelection("http.health.readiness-exposure", env["PLATFORM_HEALTH_READYZ_EXPOSURE"], hasAuthentication ? "authenticated" : "public", records);

  const configuration: PlatformServerRuntimeConfiguration = {
    config: configRecordFromEnv(env, input.extraConfigKeys ?? []),
    host,
    port,
    ...(corsOrigin === undefined ? omittedCorsSetting("http.cors-origin", rawCorsOrigin, records) : { corsOrigin }),
    ...(corsAllowlist.length === 0 ? omittedCorsSetting("http.cors-allowlist", rawCorsAllowlist, records) : { corsAllowlist }),
    healthExposure: {
      liveness,
      readiness,
    },
    releaseIdentity: resolvePlatformReleaseIdentity(env["PLATFORM_SOURCE_COMMIT_SHA"], (record) => { records.push(record); }),
  };
  return { configuration, diagnosticRecords: Object.freeze(records) };
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

function portSelection(value: string | undefined): { readonly port: number; readonly reason?: typeof serverPortFallbackReasons[number] } {
  if (value === undefined || value.length === 0) {
    return { port: 3_000 };
  }
  const parsed = Number(value);
  const reason = Number.isNaN(parsed) ? "not-numeric" : !Number.isFinite(parsed) ? "not-finite"
    : !Number.isInteger(parsed) ? "not-integer" : parsed < 1 ? "below-minimum" : parsed > 65_535 ? "above-maximum" : undefined;
  return reason === undefined ? { port: parsed } : { port: 3_000, reason };
}

function listenerSelection(setting: "http.host" | "http.port", override: string | number | undefined, value: string | undefined) {
  const reason = override != null ? "explicit-override" : value === undefined ? "missing" : value.length === 0 ? "empty" : "provided";
  const source = override != null ? "process-option" : reason === "provided" ? "environment" : "default";
  return configurationRecord(serverListenerConfigurationDiagnostic, { phase: "configuration", setting, source, reason,
    effect: source === "default" ? "default-selected" : "selected" });
}

function configurationRecord<T>(definition: DiagnosticDefinition<T>, detail: NoInfer<T>): DiagnosticRecord<T> {
  const checked = createDiagnosticRecord(definition, detail);
  if (!checked.ok) throw new TypeError("PLATFORM_SERVER_CONFIGURATION_DIAGNOSTIC_INVALID");
  return checked.value;
}

function csvEnv(value: string | undefined): readonly string[] {
  if (value === undefined) {
    return [];
  }
  return value.split(",").map((item) => item.trim()).filter((item) => item.length > 0);
}

function omittedCorsSetting(setting: "http.cors-origin" | "http.cors-allowlist", value: string | undefined, records: DiagnosticRecord[]): Record<string, never> {
  records.push(serverConfigurationOmissionRecord(setting, value === undefined ? "missing"
    : typeof value === "string" && value.length === 0 ? "empty" : "normalization-empty"));
  return {};
}

function healthSelection(
  setting: "http.health.liveness-exposure" | "http.health.readiness-exposure",
  value: string | undefined,
  fallback: PlatformServerHealthEndpointExposure,
  records: DiagnosticRecord[],
): PlatformServerHealthEndpointExposure {
  const provided = value === "authenticated" || value === "public";
  const exposure = provided ? value : fallback;
  const source = provided ? "environment" : fallback === "authenticated" ? "authentication-default" : "default";
  const reason = provided ? "provided" : value === undefined ? "missing" : value.length === 0 ? "empty" : "unsupported";
  if (reason === "unsupported") records.push(configurationRecord(serverHealthExposureFallbackDiagnostic,
    { phase: "configuration", setting, source: fallback === "authenticated" ? "authentication-default" : "default", exposure, reason, effect: "default-selected" }));
  else records.push(configurationRecord(serverHealthExposureSelectionDiagnostic,
    { phase: "configuration", setting, source, exposure, reason, effect: provided ? "selected" : "default-selected" }));
  return exposure;
}

function nonEmptyValue(value: string | undefined): string | undefined {
  return value === undefined || value.length === 0 ? undefined : value;
}
