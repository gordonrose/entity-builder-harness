// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-app
//   version: 1
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-23"
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
  readonly readiness: () => Promise<"ready" | "not-ready">;
  readonly createAcceptanceRecord: () => Promise<"created" | "already-exists" | "unavailable" | "uncertain">;
  readonly readAcceptanceRecord: () => Promise<"found" | "not-found" | "unavailable">;
  readonly close: () => Promise<void>;
}

const persistenceProfile: PlatformCapabilityObservabilityProfile = {
  name: persistenceProfileName,
  capability: requiredPlatformName(platformCapabilityName("kanbien-core-server.persistence")),
  action: "verify",
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
): PlatformApp {
  return definePlatformApp({
    id: coreServerAppId,
    name: "Kanbien Core Server Persistence Candidate",
    lifecycle: {
      beforeStop: () => persistence.close(),
    },
    mount(registry) {
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
          check: async () => healthCheckResult({
            name: persistenceHealthName,
            type: "dependency",
            component: persistenceHealthComponent,
            status: await persistenceHealthStatus(persistence),
            checkedAt: isoDateTimeFromDate(systemClock.now()),
          }),
        },
      });
      registry.registerRoute({
        name: createRouteName,
        method: "POST",
        path: "/internal/persistence-acceptance",
        auth: { kind: "public" },
        observability: { kind: "profile", profile: persistenceProfileName },
        handler: {
          handle: async () => createAcceptanceResponse(await persistence.createAcceptanceRecord()),
        },
      });
      registry.registerRoute({
        name: readRouteName,
        method: "GET",
        path: "/internal/persistence-acceptance",
        auth: { kind: "public" },
        observability: { kind: "profile", profile: persistenceProfileName },
        handler: {
          handle: async () => readAcceptanceResponse(await persistence.readAcceptanceRecord(), releaseIdentity),
        },
      });
    },
  });
}

async function persistenceHealthStatus(
  persistence: KanbienCorePersistenceRuntime,
): Promise<"healthy" | "unhealthy"> {
  try {
    return await persistence.readiness() === "ready" ? "healthy" : "unhealthy";
  } catch {
    return "unhealthy";
  }
}

function createAcceptanceResponse(outcome: Awaited<ReturnType<KanbienCorePersistenceRuntime["createAcceptanceRecord"]>>) {
  if (outcome === "created") return { status: 201, body: { outcome } };
  if (outcome === "already-exists") return { status: 200, body: { outcome } };
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
  if (outcome === "found") return { status: 200, body: { outcome, release: releaseIdentity } };
  if (outcome === "not-found") return { status: 404, body: { outcome } };
  return {
    status: 503,
    body: { outcome: "not-confirmed" },
    observability: { errorClass: "persistence_unavailable" },
  };
}

function requiredPlatformName<T>(result: { readonly ok: true; readonly value: T } | { readonly ok: false }): T {
  if (!result.ok) throw new Error("KANBIEN_CORE_SERVER_PERSISTENCE_DECLARATION_INVALID");
  return result.value;
}
