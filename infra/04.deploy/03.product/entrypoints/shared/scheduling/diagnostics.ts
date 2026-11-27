// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.shared-scheduling-diagnostics
//   version: 1
//   status: draft
//   created_on: "2026-11-27"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.scheduling
//   disciplines: [security, sre]
//   kind: code
//   purpose: Define safe target-owned scheduling configuration and invocation evidence.
//   portability: { class: internal, targets: [kanbien-core-platform, entity-smoke] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.shared-scheduling-invocation
//     path: infra/04.deploy/03.product/entrypoints/shared/scheduling/invocation.ts

import { captureDiagnosticRecord, createDiagnosticRecord, defineDiagnostic, requireDiagnosticRecord } from "@kanbien/core/diagnostics";
import { configReasonNames } from "@kanbien/core/config";
import { defineConfigurationDiagnostic } from "@kanbien/platform-config";

export const schedulingTargetConfigurationDiagnostic = defineConfigurationDiagnostic("scheduling-target.configuration-invalid",
  ["queue.arn", "queue.region", "database.schema", "authentication.username", "authentication.reference", "queue.address"],
  [configReasonNames.missing, configReasonNames.wrongType, configReasonNames.blank, configReasonNames.surroundingWhitespace,
    configReasonNames.invalidFormat, configReasonNames.inconsistentSettings]);
export const schedulingTargetInvocationDiagnostic = defineDiagnostic({ code: "scheduling-target.invocation-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["dispatch", "worker"] },
    phase: { type: "enum", values: ["configuration", "resources", "composition", "execution", "shutdown"] },
    effect: { type: "enum", values: ["not-started", "earlier-effects-possible", "completion-preserved"] },
  } },
} as const);
export const schedulingTargetPreflightDiagnostic = defineDiagnostic({ code: "scheduling-target.preflight-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["dispatch", "worker"] },
    check: { type: "enum", values: ["request-shape", "source-revision", "request-identity", "function-identity", "operation-identity",
      "time-budget", "database-connection", "database-identity", "database-user", "database-session",
      "database-privileges", "database-rollback", "queue-dns", "queue-identity", "cleanup"] },
    observation: { type: "enum", values: ["predicate-rejected", "dependency-threw"] },
  } },
} as const);
export const schedulingTargetDiagnosticCatalog = { owner: "scheduling-target", definitions: [
  schedulingTargetConfigurationDiagnostic, schedulingTargetInvocationDiagnostic, schedulingTargetPreflightDiagnostic,
] } as const;
export type SchedulingPreflightDetail = NonNullable<typeof schedulingTargetPreflightDiagnostic.__detail>;
export function schedulingPreflightRecord(detail: SchedulingPreflightDetail) {
  return requireDiagnosticRecord(schedulingTargetDiagnosticCatalog.definitions, captureDiagnosticRecord(() => {
    const result = createDiagnosticRecord(schedulingTargetPreflightDiagnostic, detail);
    return result.ok ? result.value : undefined;
  }));
}
export type SchedulingInvocationDetail = NonNullable<typeof schedulingTargetInvocationDiagnostic.__detail>;
export function schedulingInvocationRecord(detail: SchedulingInvocationDetail) {
  return requireDiagnosticRecord(schedulingTargetDiagnosticCatalog.definitions, captureDiagnosticRecord(() => {
    const result = createDiagnosticRecord(schedulingTargetInvocationDiagnostic, detail);
    return result.ok ? result.value : undefined;
  }));
}
