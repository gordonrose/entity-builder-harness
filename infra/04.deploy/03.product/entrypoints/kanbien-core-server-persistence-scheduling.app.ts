// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-scheduling-app
//   version: 1
//   status: draft
//   created_on: "2026-11-26"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Register a harmless durable scheduler proof job using the existing acceptance-record capability.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: deploy.test.core-server-persistence-composition
//     path: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh

import { createHash } from "node:crypto";
import { queueMessageType } from "@kanbien/core/queues";
import { isoDateTimeFromDate, type Clock, type Result } from "@kanbien/core/shared";
import { definePlatformApp, platformAppId, platformCapabilityName, platformJobName, platformObservabilityProfileName,
  type PlatformApp } from "@kanbien/platform-contracts";
import { loadPlatformScheduleDelivery, type PlatformOutboxStore, type PlatformScheduleStore, type PlatformPersistenceDiagnosticOptions } from "@kanbien/platform-persistence";
import type { KanbienCorePersistenceRuntime } from "./kanbien-core-server-persistence.app";
import { kanbienCoreAcceptanceDiagnosticCatalog, kanbienCoreScheduledProofFailure } from "./kanbien-core-server-persistence-diagnostics";

export const kanbienCoreScheduledProofJobName = required(platformJobName("kanbien-core-server.persistence.scheduling.verify"));
export const kanbienCoreScheduledProofMessageType = required(queueMessageType("kanbien-core-server.persistence.scheduling.verify"));

export interface KanbienCoreSchedulingAppOptions extends PlatformPersistenceDiagnosticOptions {
  readonly persistence: Pick<KanbienCorePersistenceRuntime, "createAcceptanceRecord">;
  readonly schedules: Pick<PlatformScheduleStore, "get">;
  readonly outbox: Pick<PlatformOutboxStore, "get">;
  readonly clock: Clock;
}

/** Independent baseline proof, not an application-specific cleanup implementation. */
export function createKanbienCoreServerSchedulingApp(options: KanbienCoreSchedulingAppOptions): PlatformApp {
  const profile = required(platformObservabilityProfileName("kanbien-core-server.persistence.scheduling"));
  return definePlatformApp({
    id: required(platformAppId("kanbien-core-server")), name: "Kanbien Core Scheduler Proof",
    mount(registry) {
      required(registry.registerDiagnosticCatalog(kanbienCoreAcceptanceDiagnosticCatalog));
      required(registry.registerObservabilityProfile({ name: profile,
        capability: required(platformCapabilityName("kanbien-core-server.persistence.scheduling")), action: "verify",
        signals: ["operational_log"], logFieldNames: ["capability", "action", "outcome", "error_class"],
        errorClasses: ["scheduled_proof_failed"] }));
      required(registry.registerJob({ name: kanbienCoreScheduledProofJobName, messageType: kanbienCoreScheduledProofMessageType,
        observability: { kind: "profile", profile }, handler: { async handle(message) {
          const schedule = required(await loadPlatformScheduleDelivery(message, {
            outbox: options.outbox, schedules: options.schedules,
            jobName: kanbienCoreScheduledProofJobName, messageType: kanbienCoreScheduledProofMessageType,
            asOf: isoDateTimeFromDate(options.clock.now()),
            ...(options.onDiagnostic === undefined ? {} : { onDiagnostic: options.onDiagnostic }),
          }));
          const factDigest = createHash("sha256").update(JSON.stringify([schedule.id, schedule.jobName, schedule.dueAt])).digest("hex");
          const outcome = await options.persistence.createAcceptanceRecord({ id: String(schedule.id), factDigest }, options.onDiagnostic);
          if (outcome !== "created" && outcome !== "already-exists") throw kanbienCoreScheduledProofFailure(outcome);
        } } }));
    },
  });
}

function required<T>(result: Result<T, unknown>): T { if (!result.ok) throw result.error; return result.value; }
