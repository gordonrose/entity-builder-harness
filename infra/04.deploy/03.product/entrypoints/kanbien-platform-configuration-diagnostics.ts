import { coreDiagnosticCatalog } from "@kanbien/core";
import { createDiagnosticRecord, defineDiagnostic, selectDiagnosticEvidence } from "@kanbien/core/diagnostics";
import { configurationDiagnostic, defineConfigurationDiagnostic, platformConfigDiagnosticCatalog } from "@kanbien/platform-config";
import { platformContractDiagnosticCatalog, type PlatformDiagnosticCatalog } from "@kanbien/platform-contracts";
import { createPlatformDiagnosticReporter, platformObservabilityDiagnosticCatalog, reportPlatformErrorDiagnostic } from "@kanbien/platform-observability";
import { platformPersistenceDiagnosticCatalog } from "@kanbien/platform-persistence";
import { platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import { platformServerDiagnosticCatalog } from "@kanbien/platform-server";
import { platformWorkerDiagnosticCatalog, workerConfigurationDiagnosticRecord } from "@kanbien/platform-workers";

/** Only target bindings live here. Values, arbitrary environment names and
 * provider references are never diagnostic detail. */
const environmentSettings = {
  PLATFORM_AUTH_PROVIDER: "authentication.provider",
  PLATFORM_DEPLOYMENT_EXPOSURE: "deployment.exposure",
  PLATFORM_RATE_LIMIT_PROVIDER: "rate-limit.provider",
  PLATFORM_PERSISTENCE_PROVIDER: "persistence.provider",
  PLATFORM_TRUSTED_INGRESS_MODE: "ingress.mode",
  PLATFORM_SERVER_MAX_REQUEST_BODY_BYTES: "transport.request-body-limit",
  PLATFORM_SERVER_MAX_HEADER_BYTES: "transport.header-limit",
  PLATFORM_SERVER_MAX_HEADERS_COUNT: "transport.header-count",
  PLATFORM_SERVER_HEADERS_TIMEOUT_MS: "transport.headers-timeout",
  PLATFORM_SERVER_REQUEST_TIMEOUT_MS: "transport.request-timeout",
  PLATFORM_SERVER_KEEP_ALIVE_TIMEOUT_MS: "transport.keep-alive-timeout",
  PLATFORM_SERVER_HANDLER_TIMEOUT_MS: "transport.handler-timeout",
  PLATFORM_SERVER_SHUTDOWN_DRAIN_TIMEOUT_MS: "transport.shutdown-drain-timeout",
  PLATFORM_SERVER_MAX_CONCURRENT_REQUESTS: "transport.concurrent-requests",
  PLATFORM_SERVER_MAX_REQUESTS_PER_SOCKET: "transport.requests-per-socket",
  PLATFORM_WORKER_QUEUE_PROVIDER: "worker.queue-provider",
  PLATFORM_WORKER_POLL_FAILURE_BACKOFF_MS: "worker.failure-backoff",
  PLATFORM_WORKER_EXIT_AFTER_SUCCESSFUL_DELIVERIES: "worker.exit-limit",
  PLATFORM_RELAY_QUEUE_PROVIDER: "relay.queue-provider",
  PLATFORM_RELAY_SQS_QUEUE_URL: "relay.queue-address",
  PLATFORM_RELAY_SQS_REGION: "relay.region",
  PLATFORM_RELAY_LEASE_DURATION_MS: "relay.lease-duration",
  HOSTNAME: "lease-owner.local-hostname",
  ECS_CONTAINER_METADATA_URI_V4: "lease-owner.metadata",
  RELATIONAL_SMOKE_QUEUE_URL: "relational.queue-address",
  RELATIONAL_RESTORE_HOST: "relational.restore-host",
} as const;
const relationalSettings = ["relational.configuration", "relational.database", "relational.schema", "relational.tls", "relational.runtime-reference", "relational.migration-reference",
  ...["master", "migration", "runtime", "generic"].flatMap((role) => ["value", "username", "password", "host", "port"].map((field) => `relational.secret.${role}.${field}`)),
  "relational.connection.host", "relational.connection.port", "relational.connection.schema", "relational.connection.reference", "relational.connection.configuration"];
export const targetConfigurationReasons = ["missing", "empty", "blank", "wrong-type", "invalid-json", "wrong-shape", "unsupported", "required-provider", "invalid-integer", "not-positive", "out-of-range", "above-maximum", "fixed-value-required", "invalid-format", "surrounding-whitespace", "malformed-url", "protocol-not-allowed", "host-not-allowed", "port-not-allowed", "username-not-allowed", "password-not-allowed", "owner-invalid"] as const;
export type TargetConfigurationReason = typeof targetConfigurationReasons[number];
export const kanbienPlatformConfigurationDiagnostic = defineConfigurationDiagnostic("kanbien-platform.configuration-invalid", [...Object.values(environmentSettings), ...relationalSettings], targetConfigurationReasons);
/** The source failed to supply an identity; its cause is not established by
 * the local startup error or a rejected fetch/JSON/property/hash invocation. */
export const kanbienPlatformLeaseOwnerSourceDiagnostic = defineDiagnostic({ code: "kanbien-platform.lease-owner-source-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["request", "response-json", "identity-read", "response-status", "owner-derivation"] },
    reason: { type: "enum", values: ["invocation-failed", "response-not-successful", "identity-missing", "identity-wrong-type", "identity-empty"] },
    effect: { type: "enum", values: ["not-assessed"] },
  } },
} as const);
export type LeaseOwnerSourcePhase = "request" | "response-json" | "identity-read" | "response-status" | "owner-derivation";
export type LeaseOwnerSourceReason = "invocation-failed" | "response-not-successful" | "identity-missing" | "identity-wrong-type" | "identity-empty";
export function targetLeaseOwnerSourceRecord(phase: LeaseOwnerSourcePhase, reason: LeaseOwnerSourceReason) {
  const checked = createDiagnosticRecord(kanbienPlatformLeaseOwnerSourceDiagnostic, { phase, reason, effect: "not-assessed" });
  if (!checked.ok) throw new TypeError("KANBIEN_PLATFORM_LEASE_OWNER_SOURCE_DIAGNOSTIC_INVALID");
  return checked.value;
}
export const kanbienPlatformConfigurationDiagnosticCatalog = { owner: "kanbien-platform", definitions: [kanbienPlatformConfigurationDiagnostic, kanbienPlatformLeaseOwnerSourceDiagnostic] } as const;

export function targetConfigurationDiagnosticRecord(setting: string, reason: TargetConfigurationReason) {
  const checked = configurationDiagnostic(kanbienPlatformConfigurationDiagnostic, [{ setting, reason }]);
  if (!checked.ok) throw new TypeError("KANBIEN_PLATFORM_CONFIGURATION_DIAGNOSTIC_INVALID");
  return checked.value;
}
export function targetEnvironmentConfigurationRecord(path: keyof typeof environmentSettings, reason: TargetConfigurationReason) {
  return targetConfigurationDiagnosticRecord(environmentSettings[path], reason);
}

// These catalogs correspond to actual startup and configuration producers.
// Selection is local to this composition, never a global unknown-code fallback.
const targetConfigurationCatalogs: readonly PlatformDiagnosticCatalog[] = [coreDiagnosticCatalog, platformConfigDiagnosticCatalog, platformContractDiagnosticCatalog,
  platformSecurityDiagnosticCatalog, platformObservabilityDiagnosticCatalog, platformServerDiagnosticCatalog, platformWorkerDiagnosticCatalog,
  platformPersistenceDiagnosticCatalog, kanbienPlatformConfigurationDiagnosticCatalog];
const selectedDefinitions = targetConfigurationCatalogs.flatMap((catalog) => catalog.definitions);
export function selectTargetConfigurationEvidence(error: unknown) {
  return selectDiagnosticEvidence(selectedDefinitions, error);
}
/** SQS depends only on Core; its positively observed fixed facts cross this
 * target binding before becoming a capability-owned checked record. */
export function workerQueueConfigurationEvidence(error: unknown) {
  try {
    if (typeof error !== "object" || error === null) return {};
    const issue = Object.getOwnPropertyDescriptor(error, "configurationIssue");
    if (!issue || !("value" in issue) || typeof issue.value !== "object" || issue.value === null) return {};
    const fields = Object.getOwnPropertyDescriptors(issue.value);
    if (Reflect.ownKeys(fields).sort().join(",") !== "reason,setting") return {};
    const setting = fields["setting"]; const reason = fields["reason"];
    if (!setting || !("value" in setting) || !reason || !("value" in reason) || typeof setting.value !== "string" || typeof reason.value !== "string") return {};
    // The selected worker catalog also owns durable lease configuration. This
    // SQS binding admits only the facts its actual adapter guards can supply.
    if (!["queue-address", "region", "receive-wait", "visibility-timeout"].includes(setting.value)
      || !["missing", "empty", "blank", "wrong-type", "not-finite", "invalid-integer", "out-of-range"].includes(reason.value)) return {};
    return { diagnosticRecord: workerConfigurationDiagnosticRecord(setting.value, reason.value) };
  } catch { return {}; }
}
export function reportTargetConfigurationError(error: unknown, stage: "configuration" | "startup" = "configuration"): void {
  try {
    const reporter = createPlatformDiagnosticReporter({ catalogs: targetConfigurationCatalogs, clock: { now: () => new Date() },
      logger: { write: (record) => { console.error(JSON.stringify(record)); } } });
    reportPlatformErrorDiagnostic(reporter, selectTargetConfigurationEvidence(error), { capability: "configuration", operation: "target-configuration", stage });
  } catch { /* Reporting does not change the existing startup/task outcome. */ }
}

export function relationalSecretSetting(name: string, field: "value" | "username" | "password" | "host" | "port"): string {
  const role = name === "RELATIONAL_MASTER_SECRET_JSON" ? "master" : name === "RELATIONAL_MIGRATION_SECRET_JSON" ? "migration" : name === "RELATIONAL_RUNTIME_SECRET_JSON" ? "runtime" : "generic";
  return `relational.secret.${role}.${field}`;
}
