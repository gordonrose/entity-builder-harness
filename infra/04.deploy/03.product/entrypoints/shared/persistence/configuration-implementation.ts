// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.shared.persistence-configuration-implementation
//   version: 2
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.persistence
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Select shared PostgreSQL configuration requirements without importing a workload application or runtime constructor.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.shared-persistence-configuration
//     path: infra/04.deploy/03.product/entrypoints/shared/persistence/configuration.ts
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-composition
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-composition.ts

import { assemblePostgreSqlPersistenceConfiguration, postgreSqlPersistenceRequirements } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";

// Keep the published identifier and definition unchanged. Shared source ownership
// does not grant permission to rewrite retained diagnostic contracts.
export const persistenceImplementationDiagnostic = defineDiagnostic({
  code: "kanbien-core-server.persistence-implementation-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["implementation-selection"] },
    reason: { type: "enum", values: ["wrong-type", "blank", "surrounding-whitespace", "unsupported"] },
    effect: { type: "enum", values: ["not-started"] },
  } },
} as const);

export const postgresqlConfigurationImplementation = Object.freeze({
  id: "postgresql" as const,
  requirements: postgreSqlPersistenceRequirements,
  assembleConfiguration: assemblePostgreSqlPersistenceConfiguration,
});
export type PersistenceConfigurationImplementation = typeof postgresqlConfigurationImplementation;

export function selectPersistenceConfigurationImplementation(value: unknown) {
  if (value === undefined || value === "postgresql") return { ok: true as const, value: postgresqlConfigurationImplementation };
  const reason = typeof value !== "string" ? "wrong-type" : value.trim() === "" ? "blank"
    : value.trim() !== value ? "surrounding-whitespace" : "unsupported";
  const record = createDiagnosticRecord(persistenceImplementationDiagnostic, { phase: "implementation-selection", reason, effect: "not-started" });
  if (!record.ok) throw new TypeError("PERSISTENCE_IMPLEMENTATION_DIAGNOSTIC_INVALID");
  return { ok: false as const, error: { code: "CONFIGURATION_INVALID" as const, diagnostic: record.value } };
}
