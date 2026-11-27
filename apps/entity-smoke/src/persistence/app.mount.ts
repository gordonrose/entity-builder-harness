import { definePlatformApp, platformAppId, platformHealthName, platformJobName, platformRouteName,
  platformCapabilityName, platformObservabilityProfileName, type PlatformApp } from "@kanbien/platform-contracts";
import { healthCheckName, healthCheckResult, monitoringComponent } from "@kanbien/core/monitoring";
import { isoDateTimeFromDate } from "@kanbien/core/shared";
import type { QueueMessageType } from "@kanbien/core/queues";
import type { CoreError } from "@kanbien/core/shared";
import { testEntityDiagnosticCatalog } from "../../features/test-entity/contract/diagnostics";
import { handleTestEntityCommand } from "../../features/test-entity/transport/http";
import type { TestEntityServiceDependencies } from "../../features/test-entity/domain/services/dependencies";
import { handleTestEntityRetentionJob, type TestEntityRetentionDelivery } from "../../features/test-entity/transport/retention-job";

export const entitySmokeExpiredPurgeJobName = required(platformJobName("entity-smoke.test-entity.purge-expired"));
export const entitySmokeExpiredPurgeMessageType = "entity-smoke.test-entity.purge-expired" as QueueMessageType;

export interface EntitySmokePersistenceAppOptions {
  readonly services: TestEntityServiceDependencies;
  readonly readiness: () => Promise<{ readonly readiness: "ready" | "not-ready"; readonly diagnosticRecord?: CoreError["diagnosticRecord"]; readonly relatedDiagnosticRecords?: CoreError["relatedDiagnosticRecords"] }>;
  readonly close: () => Promise<void>;
  readonly retentionDelivery?: TestEntityRetentionDelivery;
}

/** An explicit durable composition; the existing local static app is unchanged. */
export function createEntitySmokePersistenceApp(options: EntitySmokePersistenceAppOptions): PlatformApp {
  const profile = required(platformObservabilityProfileName("entity-smoke.test-entity.commands"));
  return definePlatformApp({
    id: required(platformAppId("entity-smoke")), name: "Entity Smoke Persistence",
    lifecycle: { beforeStop: options.close },
    mount(registry) {
      required(registry.registerDiagnosticCatalog(testEntityDiagnosticCatalog));
      required(registry.registerObservabilityProfile({ name: profile, capability: required(platformCapabilityName("entity-smoke.test-entity")),
        action: "verify", signals: ["operational_log"], logFieldNames: ["capability", "action", "outcome", "error_class"],
        errorClasses: ["test_entity_operation_failed", "test_entity_request_invalid"] }));
      required(registry.registerHealthCheck({ name: required(platformHealthName("entity-smoke.readiness")), check: { check: async () => {
        const observation = await options.readiness();
        return { ...healthCheckResult({
        name: healthCheckName("entity-smoke.readiness"), type: "dependency", component: monitoringComponent({ type: "database", name: "test-entity" }),
        status: observation.readiness === "ready" ? "healthy" : "unhealthy", checkedAt: isoDateTimeFromDate(options.services.clock.now()),
        }), ...(observation.diagnosticRecord === undefined ? {} : { diagnosticRecord: observation.diagnosticRecord }),
        ...(observation.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: observation.relatedDiagnosticRecords }) };
      } } }));
      required(registry.registerRoute({ name: required(platformRouteName("entity-smoke.test-entity.command")), method: "POST", path: "/entity-smoke/test-entity",
        auth: { kind: "public" }, observability: { kind: "profile", profile },
        handler: { handle: (request, context) => handleTestEntityCommand(request.body, options.services, context.onDiagnostic) } }));
      required(registry.registerJob({ name: entitySmokeExpiredPurgeJobName, messageType: entitySmokeExpiredPurgeMessageType,
        observability: { kind: "profile", profile },
        handler: { handle: message => handleTestEntityRetentionJob(message, options.services, options.retentionDelivery,
          entitySmokeExpiredPurgeJobName, entitySmokeExpiredPurgeMessageType) } }));
    },
  });
}

function required<T>(result: { readonly ok: true; readonly value: T } | { readonly ok: false; readonly error: unknown }): T {
  if (!result.ok) throw result.error;
  return result.value;
}
