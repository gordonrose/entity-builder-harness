// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-diagnostics
//   version: 1
//   status: active
//   created_on: "2026-10-30"
//   updated_on: "2026-10-30"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Own value-free acceptance request predicates separately from configuration and database diagnostics.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-app
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts

import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";

export const kanbienCoreAcceptanceRequestDiagnostic = defineDiagnostic({
  code: "kanbien-core-server.acceptance.request-invalid", version: 1,
  classification: { failureKind: "validation", failureSource: "app", severity: "warning", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["create", "read", "delete"] },
    source: { type: "enum", values: ["body", "query"] },
    field: { type: "enum", values: ["body", "record_id", "fact_digest"] },
    reason: { type: "enum", values: ["missing", "null", "array", "wrong-type", "invalid-format"] },
    effect: { type: "enum", values: ["persistence-not-invoked"] },
  } },
} as const);

export const kanbienCoreAcceptanceDiagnosticCatalog = {
  owner: "kanbien-core-server.acceptance", definitions: [kanbienCoreAcceptanceRequestDiagnostic],
} as const;

export function kanbienCoreAcceptanceRequestFailure(
  operation: "create" | "read" | "delete", source: "body" | "query",
  field: "body" | "record_id" | "fact_digest", reason: "missing" | "null" | "array" | "wrong-type" | "invalid-format",
) {
  const record = createDiagnosticRecord(kanbienCoreAcceptanceRequestDiagnostic, {
    operation, source, field, reason, effect: "persistence-not-invoked",
  });
  if (!record.ok) throw new TypeError("KANBIEN_CORE_ACCEPTANCE_DIAGNOSTIC_INVALID");
  return record.value;
}
