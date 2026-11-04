// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-app
//   version: 2
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-30"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Compose the future persistence-capable core server with a provider-neutral runtime dependency and private acceptance operations.
//   portability:
//     class: internal
//     targets: []
//   used_by:
//   - id: deploy.test.core-server-persistence-composition
//     path: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh

import {
  definePlatformApp,
  platformAppId,
  platformCapabilityName,
  platformHealthName,
  platformObservabilityProfileName,
  platformRouteName,
  type PlatformApp,
  type PlatformCapabilityObservabilityProfile,
} from "@kanbien/platform-contracts";
import type { PlatformPersistenceDiagnosticOptions } from "@kanbien/platform-persistence";
import { kanbienCoreAcceptanceDiagnosticCatalog, kanbienCoreAcceptanceRequestFailure } from "./kanbien-core-server-persistence-diagnostics";
import {
  healthCheckName,
  healthCheckResult,
  monitoringComponent,
} from "@kanbien/core/monitoring";
import {
  isoDateTimeFromDate,
  systemClock,
} from "@kanbien/core/shared";
import {
  platformReleaseVerificationResponse,
  serverDiagnosticErrorCodes,
  type PlatformReleaseIdentity,
} from "@kanbien/platform-server";

const coreServerAppId = requiredPlatformName(platformAppId("kanbien-core-server"));
const persistenceHealthName = healthCheckName("kanbien-core-server.persistence");
const persistencePlatformHealthName = requiredPlatformName(platformHealthName("kanbien-core-server.persistence"));
const persistenceHealthComponent = monitoringComponent({ type: "database", name: "persistence" });
const releaseVerificationRouteName = requiredPlatformName(platformRouteName("kanbien-core-server.release.verify"));
const createRouteName = requiredPlatformName(platformRouteName("kanbien-core-server.persistence.acceptance.create"));
const readRouteName = requiredPlatformName(platformRouteName("kanbien-core-server.persistence.acceptance.read"));
const releaseVerificationProfileName = requiredPlatformName(
  platformObservabilityProfileName("kanbien-core-server.release.verify"),
);
const persistenceProfileName = requiredPlatformName(
  platformObservabilityProfileName("kanbien-core-server.persistence.acceptance"),
);

/**
 * This is the target-composition seam, not a PostgreSQL API. The later
 * PostgreSQL composition supplies this capability; local proof supplies a
 * fake. The verifier can observe only stable outcomes through the server.
 */
export interface KanbienCorePersistenceRuntime {
  /** Additive internal observation; old fake implementations remain valid. */
  readonly readinessObservation?: () => Promise<import("@kanbien/platform-observability").PlatformReadinessProbeResult>;
  readonly readiness: () => Promise<"ready" | "not-ready">;
  readonly createAcceptanceRecord: (record: KanbienPersistenceAcceptanceRecord, onDiagnostic?: PlatformPersistenceDiagnosticOptions["onDiagnostic"]) => Promise<"created" | "already-exists" | "conflict" | "unavailable" | "uncertain">;
  readonly readAcceptanceRecord: (recordId: string, onDiagnostic?: PlatformPersistenceDiagnosticOptions["onDiagnostic"]) => Promise<KanbienPersistenceAcceptanceReadResult>;
  readonly deleteAcceptanceRecord: (recordId: string, onDiagnostic?: PlatformPersistenceDiagnosticOptions["onDiagnostic"]) => Promise<"deleted" | "not-found" | "unavailable" | "uncertain">;
  readonly close: () => Promise<void>;
}

export interface KanbienCoreServerPersistenceLifecycle {
  /** Target composition can stop target-owned observers before the pool closes. */
  readonly beforeStop?: () => Promise<void>;
}

export interface KanbienPersistenceAcceptanceRecord {
  readonly id: string;
  readonly factDigest: string;
}

export type KanbienPersistenceAcceptanceReadResult =
  | { readonly outcome: "found"; readonly record: KanbienPersistenceAcceptanceRecord }
  | { readonly outcome: "not-found" | "unavailable" };

const persistenceProfile: PlatformCapabilityObservabilityProfile = {
  name: persistenceProfileName,
  capability: requiredPlatformName(platformCapabilityName("kanbien-core-server.persistence")),
  action: "verify",
  errorClasses: [...serverDiagnosticErrorCodes, "persistence_record_conflict", "persistence_outcome_uncertain", "persistence_unavailable", "persistence_acceptance_request_invalid"],
  signals: ["operational_log", "metric", "trace"],
  logFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  metricDimensionFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  traceAttributeNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  nfrObjectives: [{ nfrClass: "interactive_read", measurement: "request_response_latency" }],
};

const releaseVerificationProfile: PlatformCapabilityObservabilityProfile = {
  name: releaseVerificationProfileName,
  capability: requiredPlatformName(platformCapabilityName("kanbien-core-server.release")),
  action: "verify",
  errorClasses: serverDiagnosticErrorCodes,
  signals: ["operational_log", "metric", "trace"],
  logFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  metricDimensionFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  traceAttributeNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  nfrObjectives: [{ nfrClass: "interactive_read", measurement: "request_response_latency" }],
};

/**
 * The private target route is selected by a later scope binding. This app has
 * no database host, credential, provider SDK, or direct verifier connection.
 */
export function createKanbienCoreServerPersistenceApp(
  releaseIdentity: PlatformReleaseIdentity,
  persistence: KanbienCorePersistenceRuntime,
  lifecycle: KanbienCoreServerPersistenceLifecycle = {},
): PlatformApp {
  return definePlatformApp({
    id: coreServerAppId,
    name: "Kanbien Core Server Persistence Candidate",
    lifecycle: {
      beforeStop: async () => {
        await lifecycle.beforeStop?.();
        await persistence.close();
      },
    },
    mount(registry) {
      registry.registerDiagnosticCatalog(kanbienCoreAcceptanceDiagnosticCatalog);
      registry.registerObservabilityProfile(releaseVerificationProfile);
      registry.registerObservabilityProfile(persistenceProfile);
      registry.registerRoute({
        name: releaseVerificationRouteName,
        method: "GET",
        path: "/internal/release-verification",
        auth: { kind: "public" },
        observability: { kind: "profile", profile: releaseVerificationProfileName },
        handler: {
          handle: () => ({
            status: 200,
            body: platformReleaseVerificationResponse(releaseIdentity),
          }),
        },
      });
      registry.registerHealthCheck({
        name: persistencePlatformHealthName,
        check: {
          check: async () => {
            const observation = await persistenceHealthObservation(persistence);
            return { ...healthCheckResult({
            name: persistenceHealthName,
            type: "dependency",
            component: persistenceHealthComponent,
            status: observation.readiness === "ready" ? "healthy" : "unhealthy",
            checkedAt: isoDateTimeFromDate(systemClock.now()),
            }), ...healthDiagnosticEvidence(observation) };
          },
        },
      });
      registry.registerRoute({
        name: createRouteName,
        method: "POST",
        path: "/internal/persistence-acceptance",
        auth: { kind: "public" },
        observability: { kind: "profile", profile: persistenceProfileName },
        handler: {
          handle: async (request, context) => {
            const record = acceptanceRecordFromBody(request.body, (field, reason) =>
              observeInvalidAcceptance(context, "create", "body", field, reason));
            if (record === undefined) return invalidAcceptanceRequestResponse();
            return createAcceptanceResponse(await persistence.createAcceptanceRecord(record, context.onDiagnostic));
          },
        },
      });
      registry.registerRoute({
        name: readRouteName,
        method: "GET",
        path: "/internal/persistence-acceptance",
        auth: { kind: "public" },
        observability: { kind: "profile", profile: persistenceProfileName },
        handler: {
          handle: async (request, context) => {
            const recordId = acceptanceRecordIdFromQuery(request.query["record_id"], (reason) =>
              observeInvalidAcceptance(context, "read", "query", "record_id", reason));
            if (recordId === undefined) return invalidAcceptanceRequestResponse();
            return readAcceptanceResponse(await persistence.readAcceptanceRecord(recordId, context.onDiagnostic), releaseIdentity);
          },
        },
      });
      registry.registerRoute({
        name: requiredPlatformName(platformRouteName("kanbien-core-server.persistence.acceptance.delete")),
        method: "DELETE",
        path: "/internal/persistence-acceptance",
        auth: { kind: "public" },
        observability: { kind: "profile", profile: persistenceProfileName },
        handler: {
          handle: async (request, context) => {
            const recordId = acceptanceRecordIdFromQuery(request.query["record_id"], (reason) =>
              observeInvalidAcceptance(context, "delete", "query", "record_id", reason));
            if (recordId === undefined) return invalidAcceptanceRequestResponse();
            return deleteAcceptanceResponse(await persistence.deleteAcceptanceRecord(recordId, context.onDiagnostic));
          },
        },
      });
    },
  });
}

async function persistenceHealthObservation(
  persistence: KanbienCorePersistenceRuntime,
): Promise<import("@kanbien/platform-observability").PlatformReadinessProbeResult> {
  try {
    const observe = persistence.readinessObservation;
    return observe === undefined
      ? { readiness: await persistence.readiness() }
      : await observe.call(persistence);
  } catch (error) {
    return { readiness: "not-ready", ...healthDiagnosticEvidence(error) };
  }
}

/** HealthCheck supports typed structural subtypes; the public projector omits
 * these fields, while the internal reporter validates their owning catalogs.
 */
function healthDiagnosticEvidence(value: unknown): Pick<import("@kanbien/platform-observability").PlatformReadinessProbeResult, "diagnosticRecord" | "relatedDiagnosticRecords"> {
  try {
    if (typeof value !== "object" || value === null) return {};
    const primary = Object.getOwnPropertyDescriptor(value, "diagnosticRecord");
    const related = Object.getOwnPropertyDescriptor(value, "relatedDiagnosticRecords");
    return { ...(primary && "value" in primary && primary.value !== undefined ? { diagnosticRecord: primary.value } : {}),
      ...(related && "value" in related && related.value !== undefined ? { relatedDiagnosticRecords: related.value } : {}) };
  } catch { return {}; }
}

function createAcceptanceResponse(outcome: Awaited<ReturnType<KanbienCorePersistenceRuntime["createAcceptanceRecord"]>>) {
  if (outcome === "created") return { status: 201, body: { outcome } };
  if (outcome === "already-exists") return { status: 200, body: { outcome } };
  if (outcome === "conflict") return { status: 409, body: { outcome }, observability: { errorClass: "persistence_record_conflict" } };
  return {
    status: 503,
    body: { outcome: "not-confirmed" },
    observability: { errorClass: outcome === "uncertain" ? "persistence_outcome_uncertain" : "persistence_unavailable" },
  };
}

function readAcceptanceResponse(
  outcome: Awaited<ReturnType<KanbienCorePersistenceRuntime["readAcceptanceRecord"]>>,
  releaseIdentity: PlatformReleaseIdentity,
) {
  if (outcome.outcome === "found") return { status: 200, body: { outcome: outcome.outcome, record: outcome.record, release: releaseIdentity } };
  if (outcome.outcome === "not-found") return { status: 404, body: { outcome: outcome.outcome } };
  return {
    status: 503,
    body: { outcome: "not-confirmed" },
    observability: { errorClass: "persistence_unavailable" },
  };
}

function deleteAcceptanceResponse(outcome: Awaited<ReturnType<KanbienCorePersistenceRuntime["deleteAcceptanceRecord"]>>) {
  if (outcome === "deleted") return { status: 200, body: { outcome } };
  if (outcome === "not-found") return { status: 404, body: { outcome } };
  return {
    status: 503,
    body: { outcome: "not-confirmed" },
    observability: { errorClass: outcome === "uncertain" ? "persistence_outcome_uncertain" : "persistence_unavailable" },
  };
}

function invalidAcceptanceRequestResponse() {
  return {
    status: 400,
    body: { outcome: "invalid-request" },
    observability: { errorClass: "persistence_acceptance_request_invalid" },
  };
}

type AcceptanceRequestReason = Parameters<typeof kanbienCoreAcceptanceRequestFailure>[3];
const diagnosticPromiseThen = Promise.prototype.then;

function observeInvalidAcceptance(
  context: { readonly onDiagnostic?: PlatformPersistenceDiagnosticOptions["onDiagnostic"] },
  operation: "create" | "read" | "delete", source: "body" | "query",
  field: "body" | "record_id" | "fact_digest", reason: AcceptanceRequestReason,
): void {
  try {
    const result = context.onDiagnostic?.(kanbienCoreAcceptanceRequestFailure(operation, source, field, reason));
    if (result !== undefined) {
      const ignore = (): void => undefined;
      try { Reflect.apply(diagnosticPromiseThen, result, [undefined, ignore]); }
      catch { Reflect.apply(diagnosticPromiseThen, Promise.resolve(result), [undefined, ignore]); }
    }
  } catch { /* Diagnostics do not replace the existing 400 response. */ }
}

function acceptanceRecordFromBody(value: unknown,
  invalid: (field: "body" | "record_id" | "fact_digest", reason: AcceptanceRequestReason) => void,
): KanbienPersistenceAcceptanceRecord | undefined {
  if (!isRecord(value)) {
    invalid("body", value === undefined ? "missing" : value === null ? "null" : Array.isArray(value) ? "array" : "wrong-type");
    return undefined;
  }
  const id = value["record_id"];
  const factDigest = value["fact_digest"];
  if (!isAcceptanceRecordValue(id)) {
    invalid("record_id", id === undefined ? "missing" : typeof id !== "string" ? "wrong-type" : "invalid-format");
    return undefined;
  }
  if (!isFactDigest(factDigest)) {
    invalid("fact_digest", factDigest === undefined ? "missing" : typeof factDigest !== "string" ? "wrong-type" : "invalid-format");
    return undefined;
  }
  return { id, factDigest };
}

function acceptanceRecordIdFromQuery(value: string | readonly string[] | undefined,
  invalid: (reason: AcceptanceRequestReason) => void,
): string | undefined {
  if (typeof value === "string" && isAcceptanceRecordValue(value)) return value;
  invalid(value === undefined ? "missing" : Array.isArray(value) ? "array" : typeof value !== "string" ? "wrong-type" : "invalid-format");
  return undefined;
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isAcceptanceRecordValue(value: unknown): value is string {
  return typeof value === "string" && /^[a-z0-9][a-z0-9-]{7,95}$/.test(value);
}

function isFactDigest(value: unknown): value is string {
  return typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
}

function requiredPlatformName<T>(result: { readonly ok: true; readonly value: T } | { readonly ok: false }): T {
  if (!result.ok) throw new Error("KANBIEN_CORE_SERVER_PERSISTENCE_DECLARATION_INVALID");
  return result.value;
}
