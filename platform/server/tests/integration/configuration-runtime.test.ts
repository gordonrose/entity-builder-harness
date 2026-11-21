import { deepEqual, equal, ok } from "node:assert/strict";
import { createDiagnosticRecord, parseDiagnosticRecord, type DiagnosticRecord, type DiagnosticDefinition } from "@kanbien/core/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import { definePlatformApp, platformAppId } from "@kanbien/platform-contracts";
import { createPlatformSafeLogger } from "@kanbien/platform-observability";
import { platformServerDiagnosticCatalog, resolvePlatformServerRuntimeConfiguration, resolvePlatformServerRuntimeConfigurationWithDiagnostics } from "../../src/index";
import { startPlatformServerProcess } from "../../src/main";

const canary = "synthetic-private-listener.internal";
const details = (records: readonly DiagnosticRecord[]) => records.map((record) => record.detail as Record<string, unknown>);

/** Independent pre-slice oracle; do not share production predicates with this proof. */
function legacy(env: NodeJS.ProcessEnv, auth: boolean) {
  const text = (value: string | undefined) => value === undefined || value.length === 0 ? undefined : value;
  const port = env["PORT"] === undefined || env["PORT"].length === 0 ? undefined : Number(env["PORT"]);
  const exposure = (value: string | undefined, fallback: "public" | "authenticated") => value === "public" || value === "authenticated" ? value : fallback;
  const corsOrigin = text(env["PLATFORM_CORS_ORIGIN"]);
  const corsAllowlist = (env["PLATFORM_CORS_ALLOWLIST"] ?? "").split(",").map((value) => value.trim()).filter((value) => value.length > 0);
  return {
    config: Object.fromEntries(Object.entries(env).filter(([key, value]) => value !== undefined && ["NODE_ENV", "HOST", "PORT", "PLATFORM_CORS_ORIGIN", "PLATFORM_CORS_ALLOWLIST", "PLATFORM_HEALTH_LIVEZ_EXPOSURE", "PLATFORM_HEALTH_READYZ_EXPOSURE", "PLATFORM_SOURCE_COMMIT_SHA", "EXTRA"].includes(key))),
    host: text(env["HOST"]) ?? "0.0.0.0",
    port: port !== undefined && Number.isInteger(port) && port > 0 && port <= 65535 ? port : 3000,
    ...(corsOrigin === undefined ? {} : { corsOrigin }), ...(corsAllowlist.length === 0 ? {} : { corsAllowlist }),
    healthExposure: { liveness: exposure(env["PLATFORM_HEALTH_LIVEZ_EXPOSURE"], "public"), readiness: exposure(env["PLATFORM_HEALTH_READYZ_EXPOSURE"], auth ? "authenticated" : "public") },
    releaseIdentity: { sourceCommitSha: "configuration-proof" },
  };
}

async function main() {
  let comparisons = 0;
  for (const host of [undefined, "", " ", canary]) {
    for (const port of [undefined, "", " ", "0", "-1", "1", "65535", "65536", "1.5", "-1.5", "Infinity", "NaN", canary, " 3000 ", "3e3", "0xbb8", "+3000", "03000"]) {
      for (const exposure of [undefined, "", "public", "authenticated", canary]) {
        for (const hasAuthentication of [false, true]) {
          const env = { HOST: host, PORT: port, PLATFORM_HEALTH_LIVEZ_EXPOSURE: exposure, PLATFORM_HEALTH_READYZ_EXPOSURE: exposure,
            PLATFORM_CORS_ORIGIN: " ", PLATFORM_CORS_ALLOWLIST: " https://one.example.test, , https://two.example.test ", PLATFORM_SOURCE_COMMIT_SHA: "configuration-proof", EXTRA: "retained", UNRELATED: canary };
          const input = { env, hasAuthentication, extraConfigKeys: ["EXTRA"] };
          deepEqual(resolvePlatformServerRuntimeConfiguration(input), legacy(env, hasAuthentication));
          const observation = resolvePlatformServerRuntimeConfigurationWithDiagnostics(input);
          deepEqual(observation.configuration, legacy(env, hasAuthentication));
          equal(observation.diagnosticRecords.length, 4);
          deepEqual(details(observation.diagnosticRecords).map((detail) => detail["setting"]), ["http.host", "http.port", "http.health.liveness-exposure", "http.health.readiness-exposure"]);
          equal(JSON.stringify(observation.diagnosticRecords).includes(canary), false);
          comparisons++;
        }
      }
    }
  }
  const portCases = [[undefined, "missing"], ["", "empty"], ["x", "not-numeric"], ["NaN", "not-numeric"], ["Infinity", "not-finite"], ["-Infinity", "not-finite"], ["1.5", "not-integer"], ["-1.5", "not-integer"], ["0", "below-minimum"], [" ", "below-minimum"], ["-1", "below-minimum"], ["65536", "above-maximum"]] as const;
  for (const [value, reason] of portCases) {
    const observation = resolvePlatformServerRuntimeConfigurationWithDiagnostics({ env: { PORT: value } });
    const record = observation.diagnosticRecords[1]!;
    deepEqual(record.detail, { phase: "configuration", setting: "http.port", source: "default", reason, effect: "default-selected" });
    equal(record.code, reason === "missing" || reason === "empty" ? "platform-server.listener-configuration-selected" : "platform-server.port-configuration-fallback");
    const definition: DiagnosticDefinition = platformServerDiagnosticCatalog.definitions.find((candidate) => candidate.code === record.code)!;
    equal(definition.classification.severity, reason === "missing" || reason === "empty" ? "info" : "warning");
  }
  for (const [value, expectedPort] of [["3000", 3000], ["1", 1], ["65535", 65535], [" 3000 ", 3000], ["3e3", 3000], ["0xbb8", 3000], ["+3000", 3000], ["03000", 3000]] as const) {
    const observation = resolvePlatformServerRuntimeConfigurationWithDiagnostics({ env: { PORT: value } });
    equal(observation.configuration.port, expectedPort);
    const record = observation.diagnosticRecords[1]!;
    equal(record.code, "platform-server.listener-configuration-selected");
    equal(record.definitionVersion, 1);
    deepEqual(record.detail, { phase: "configuration", setting: "http.port", source: "environment", reason: "provided", effect: "selected" },
      `accepted environment port ${JSON.stringify(value)} must report its actual selection`);
  }
  for (const hasAuthentication of [false, true]) {
    for (const value of [undefined, "", "public", "authenticated", canary]) {
      const observation = resolvePlatformServerRuntimeConfigurationWithDiagnostics({ env: { PLATFORM_HEALTH_LIVEZ_EXPOSURE: value, PLATFORM_HEALTH_READYZ_EXPOSURE: value }, hasAuthentication });
      for (const index of [2, 3]) {
        const provided = value === "public" || value === "authenticated";
        const exposure = provided ? value : index === 3 && hasAuthentication ? "authenticated" : "public";
        const reason = provided ? "provided" : value === undefined ? "missing" : value === "" ? "empty" : "unsupported";
        const record = observation.diagnosticRecords[index]!;
        deepEqual(record.detail, { phase: "configuration", setting: index === 2 ? "http.health.liveness-exposure" : "http.health.readiness-exposure",
          source: provided ? "environment" : exposure === "authenticated" ? "authentication-default" : "default", exposure, reason, effect: provided ? "selected" : "default-selected" });
        equal(record.code, reason === "unsupported" ? "platform-server.health-exposure-fallback" : "platform-server.health-exposure-selected");
      }
    }
  }
  for (const host of [undefined, "", canary]) {
    const observation = resolvePlatformServerRuntimeConfigurationWithDiagnostics({ env: { HOST: host } });
    deepEqual(observation.diagnosticRecords[0]!.detail, { phase: "configuration", setting: "http.host", source: host ? "environment" : "default",
      reason: host === undefined ? "missing" : host === "" ? "empty" : "provided", effect: host ? "selected" : "default-selected" });
  }
  const overridden = resolvePlatformServerRuntimeConfigurationWithDiagnostics({ env: { HOST: canary, PORT: canary }, host: "", port: 0 });
  const oldInputWithExtraProperties = { env: { HOST: "legacy-host", PORT: "3100" }, host: "ignored-host", port: 0 };
  equal(resolvePlatformServerRuntimeConfiguration(oldInputWithExtraProperties).host, "legacy-host");
  equal(resolvePlatformServerRuntimeConfiguration(oldInputWithExtraProperties).port, 3100, "legacy resolver must continue ignoring structurally extra process-option properties");
  equal(overridden.configuration.host, ""); equal(overridden.configuration.port, 0);
  for (const detail of details(overridden.diagnosticRecords).slice(0, 2)) {
    equal(detail["reason"], "explicit-override"); equal(detail["source"], "process-option"); equal(detail["effect"], "selected");
  }
  const simultaneous = resolvePlatformServerRuntimeConfigurationWithDiagnostics({ env: { PORT: "1.5", PLATFORM_HEALTH_LIVEZ_EXPOSURE: canary, PLATFORM_HEALTH_READYZ_EXPOSURE: canary } });
  equal(simultaneous.diagnosticRecords.filter((record) => record.code.endsWith("fallback")).length, 3);
  for (const record of [...simultaneous.diagnosticRecords, ...overridden.diagnosticRecords]) {
    const definition: DiagnosticDefinition = platformServerDiagnosticCatalog.definitions.find((candidate) => candidate.code === record.code)!;
    equal(parseDiagnosticRecord(definition, record).ok, true);
    for (const field of ["host", "value", "raw", "environment", "message"]) {
      equal(parseDiagnosticRecord(definition, { ...record, detail: { ...(record.detail as object), [field]: canary } }).ok, false);
    }
    equal(parseDiagnosticRecord(definition, { ...record, definitionVersion: 999 }).ok, false);
    equal(parseDiagnosticRecord(definition, { ...record, detail: { ...(record.detail as object), reason: canary } }).ok, false);
    let accessed = false;
    const hostile = Object.defineProperty({}, "setting", { enumerable: true, get() { accessed = true; throw new Error(canary); } });
    equal(createDiagnosticRecord(definition, hostile).ok, false); equal(accessed, false);
  }
  equal(platformServerDiagnosticCatalog.definitions[0].code, "platform-server.operation-failed", "retain historical definition first and unchanged");
  const failedMountLogs: LogRecord[] = [];
  let recordsAtMount: readonly LogRecord[] | undefined;
  const failedAppId = platformAppId("configuration-mount-failure");
  ok(failedAppId.ok);
  const failedMount = await startPlatformServerProcess({
    env: { HOST: canary, PORT: "1.5", PLATFORM_HEALTH_LIVEZ_EXPOSURE: "public", PLATFORM_HEALTH_READYZ_EXPOSURE: canary },
    installSignalHandlers: false,
    auth: { authenticate: () => ({ authenticated: false, permissions: [] }) },
    logger: createPlatformSafeLogger({ write(record) { failedMountLogs.push(record); } }),
    apps: [definePlatformApp({ id: failedAppId.value, name: "Configuration mount failure", mount() {
      recordsAtMount = failedMountLogs.filter((record) => record.message === "platform.diagnostic.observed");
      throw new Error(canary);
    } })],
  });
  // Assert outside mount: its exception boundary would otherwise swallow assertion failures.
  ok(recordsAtMount, "the deliberate failing mount callback must run");
  equal(recordsAtMount.length, 7, "all selections and omissions must be delivered before mounting");
  deepEqual(recordsAtMount.map((record) => ({
    level: record.level,
    capability: record.fields?.["capability"], operation: record.fields?.["operation"], stage: record.fields?.["stage"],
    diagnostic: record.fields?.["diagnostic"],
  })), [
    { level: "info", diagnostic: { code: "platform-server.listener-configuration-selected", definitionVersion: 1,
      detail: { phase: "configuration", setting: "http.host", source: "environment", reason: "provided", effect: "selected" } } },
    { level: "warn", diagnostic: { code: "platform-server.port-configuration-fallback", definitionVersion: 1,
      detail: { phase: "configuration", setting: "http.port", source: "default", reason: "not-integer", effect: "default-selected" } } },
    { level: "info", diagnostic: { code: "platform-server.health-exposure-selected", definitionVersion: 1,
      detail: { phase: "configuration", setting: "http.health.liveness-exposure", source: "environment", exposure: "public", reason: "provided", effect: "selected" } } },
    { level: "warn", diagnostic: { code: "platform-server.health-exposure-fallback", definitionVersion: 1,
      detail: { phase: "configuration", setting: "http.health.readiness-exposure", source: "authentication-default", exposure: "authenticated", reason: "unsupported", effect: "default-selected" } } },
    ...["http.cors-origin", "http.cors-allowlist", "release.source-commit"].map((setting) => ({ level: "info", diagnostic: {
      code: "platform-server.configuration-omitted", definitionVersion: 1,
      detail: { phase: "configuration", setting, reason: "missing", effect: "omitted" },
    } })),
  ].map((record) => ({ ...record, diagnostic: { schema: "core/diagnostic-record/v1", ...record.diagnostic },
    capability: "platform-server", operation: "configure", stage: "configuration" })));
  deepEqual(failedMount, { ok: false, error: {
    code: "PLATFORM_SERVER_MOUNT_FAILED", defaultMessage: "Platform server failed to mount apps.", status: 500,
    details: { runtimeCode: "PLATFORM_RUNTIME_APP_MOUNT_FAILED" },
    diagnosticRecord: { schema: "core/diagnostic-record/v1", code: "platform-runtime.boundary-failed", definitionVersion: 1,
      detail: { operation: "mount", phase: "app-mount", subject: "app", boundary: "invocation", effect: "step-completion-unobserved", ordinal: 0 } },
  } });
  const afterMount = failedMountLogs.filter((record) => record.message === "platform.diagnostic.observed");
  deepEqual(afterMount.slice(0, 7), recordsAtMount, "configuration observations are not delayed or duplicated after failed mount");
  equal(afterMount.length, 8, "the actual mount failure adds one Runtime boundary observation");
  deepEqual(afterMount[7]?.fields?.["diagnostic"], failedMount.ok ? undefined : failedMount.error.diagnosticRecord);
  equal(failedMountLogs.some((record) => record.message === "platform.server.started"), false);
  equal(JSON.stringify({ failedMount, failedMountLogs }).includes(canary), false);
  for (const hasAuthentication of [false, true]) {
    for (const sinkThrows of [false, true]) {
      const logs: LogRecord[] = [];
      const started = await startPlatformServerProcess({ env: { HOST: canary, PORT: canary, PLATFORM_HEALTH_READYZ_EXPOSURE: canary },
        host: "127.0.0.1", port: 0, installSignalHandlers: false,
        ...(hasAuthentication ? { auth: { authenticate: () => ({ authenticated: false, permissions: [] }) } } : {}),
        logger: createPlatformSafeLogger({ write(record) {
          if (sinkThrows && record.message === "platform.diagnostic.observed") throw new Error(canary);
          logs.push(record);
        } }),
      });
      ok(started.ok, "diagnostic delivery failure must not prevent startup");
      try {
        const base = `http://127.0.0.1:${started.value.handle.port}`;
        for (const [route, status] of [["/livez", 200], ["/readyz", hasAuthentication ? 401 : 200]] as const) {
          const response = await fetch(`${base}${route}`);
          equal(response.status, status);
          const body = await response.text();
          equal(body.includes("diagnostic"), false); equal(body.includes(canary), false);
        }
        const observed = logs.filter((record) => record.message === "platform.diagnostic.observed");
        equal(observed.length, sinkThrows ? 0 : hasAuthentication ? 8 : 7);
        if (!sinkThrows) {
          equal(observed[0]?.fields?.["stage"], "configuration");
          equal(observed[3]?.level, "warn");
          deepEqual((observed[0]?.fields?.["diagnostic"] as unknown as DiagnosticRecord).detail,
            { phase: "configuration", setting: "http.host", source: "process-option", reason: "explicit-override", effect: "selected" });
          if (hasAuthentication) deepEqual(observed[7]?.fields?.["diagnostic"], {
            schema: "core/diagnostic-record/v1", code: "platform-server.operation-failed", definitionVersion: 1,
            detail: { errorCode: "PLATFORM_SERVER_UNAUTHENTICATED", phase: "authentication", reason: "rejected", effect: "rejected" },
          });
        }
        const startedLog = logs.find((record) => record.message === "platform.server.started");
        ok(startedLog); equal(Object.hasOwn(startedLog.fields ?? {}, "host"), false);
        equal(JSON.stringify(logs).includes(canary), false);
      } finally { await started.value.close(); }
    }
  }
  console.log(`HTTP configuration: ${comparisons} legacy comparisons; exact selection/fallback, safe delivery, override, health and sink-failure proofs passed.`);
}

void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
