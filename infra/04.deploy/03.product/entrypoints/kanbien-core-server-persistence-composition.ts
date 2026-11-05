// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-composition
//   version: 1
//   status: draft
//   created_on: "2026-11-02"
//   updated_on: "2026-11-02"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Select and connect the supported persistence implementation without changing operation semantics.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-main
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts

import { assemblePostgreSqlPersistenceConfiguration, postgreSqlPersistenceRequirements, createNodePostgreSqlTokenConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";
import type { KanbienCorePersistenceRuntime } from "./kanbien-core-server-persistence.app";
import { createKanbienCoreServerPostgreSqlPersistenceRuntime } from "./kanbien-core-server-persistence-postgresql";

export const persistenceImplementationDiagnostic = defineDiagnostic({
  code: "kanbien-core-server.persistence-implementation-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["implementation-selection"] },
    reason: { type: "enum", values: ["wrong-type", "blank", "surrounding-whitespace", "unsupported"] },
    effect: { type: "enum", values: ["not-started"] },
  } },
} as const);

const postgresql = Object.freeze({
  id: "postgresql" as const,
  requirements: postgreSqlPersistenceRequirements,
  assembleConfiguration: assemblePostgreSqlPersistenceConfiguration,
  createPool: createNodePostgreSqlTokenConnectionPool,
  createRuntime: (options: Parameters<typeof createKanbienCoreServerPostgreSqlPersistenceRuntime>[0]): KanbienCorePersistenceRuntime =>
    createKanbienCoreServerPostgreSqlPersistenceRuntime(options),
});
export type KanbienCorePersistenceImplementation = typeof postgresql;

export function selectPersistenceImplementation(value: unknown) {
  if (value === undefined || value === "postgresql") return { ok: true as const, value: postgresql };
  const reason = typeof value !== "string" ? "wrong-type" : value.trim() === "" ? "blank"
    : value.trim() !== value ? "surrounding-whitespace" : "unsupported";
  const record = createDiagnosticRecord(persistenceImplementationDiagnostic, { phase: "implementation-selection", reason, effect: "not-started" });
  if (!record.ok) throw new TypeError("PERSISTENCE_IMPLEMENTATION_DIAGNOSTIC_INVALID");
  return { ok: false as const, error: { code: "CONFIGURATION_INVALID" as const, diagnostic: record.value } };
}
