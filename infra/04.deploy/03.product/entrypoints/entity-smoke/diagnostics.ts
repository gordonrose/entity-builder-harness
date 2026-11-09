// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.diagnostics
//   version: 1
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Own safe target-local configuration and boundary reports without provider values.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { createDiagnosticRecord, defineDiagnostic, selectDiagnosticEvidence, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { testEntityDiagnosticCatalog } from "@kanbien/app-entity-smoke";
import { platformPersistenceDiagnosticCatalog } from "@kanbien/platform-persistence";
import { platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import { platformServerDiagnosticCatalog } from "@kanbien/platform-server";
import { platformRuntimeDiagnosticCatalog } from "@kanbien/platform-runtime";
import { platformContractDiagnosticCatalog } from "@kanbien/platform-contracts";
import { platformConfigDiagnosticCatalog } from "@kanbien/platform-config";
import { platformObservabilityDiagnosticCatalog } from "@kanbien/platform-observability";
import { platformHealthDiagnosticCatalog } from "@kanbien/platform-health";
import { defineConfigurationDiagnostic, configurationDiagnostic } from "@kanbien/core/config";
import { persistenceConfigurationDiagnosticCatalog } from "../kanbien-core-server-persistence-configuration";
import { persistenceTaskOperationDiagnosticCatalog } from "../kanbien-core-server-persistence-operation-diagnostics";
import { entitySmokeProofDiagnostic } from "./verification";

export const entitySmokeTargetDiagnostic = defineDiagnostic({
  code: "entity-smoke-target.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["startup", "migration", "administration", "readiness", "close", "verification"] },
    effect: { type: "enum", values: ["not-started", "unknown", "not-assessed"] },
  } },
} as const);
export const entitySmokeConfigurationDiagnostic = defineDiagnostic({
  code: "entity-smoke-target.configuration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["database", "schema", "identity", "region", "authority", "exposure", "operation"] },
    reason: { type: "enum", values: ["invalid", "mismatch", "unavailable"] },
    effect: { type: "enum", values: ["not-started"] },
  } },
} as const);
export const entitySmokeDatabaseConfigurationDiagnostic = defineConfigurationDiagnostic("entity-smoke-target.database-configuration-invalid",
  ["database.host", "database.port", "database.name", "database.schema", "authentication.reference", "region", "database"]);
export const entitySmokeDependencyStateDiagnostic = defineDiagnostic({
  code: "entity-smoke-target.dependency-state-rejected", version: 1,
  classification: { failureKind: "data_integrity", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["bootstrap", "grant-runtime", "observe-permissions", "observe-migration-state", "revoke-runtime", "restore-runtime"] },
    field: { type: "enum", values: ["schema-owner", "history-count", "history-id", "history-checksum", "table-state", "migration-lock", "privileges", "memberships", "sessions", "access-state"] },
    condition: { type: "enum", values: ["missing", "count-mismatch", "mismatch", "not-confirmed", "already-running"] },
    effect: { type: "enum", values: ["unknown", "not-assessed"] },
  } },
} as const);
export const entitySmokeDatabaseProofDiagnostic = defineDiagnostic({
  code: "entity-smoke-target.database-proof-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["permissions", "collision", "restore-read"] },
    step: { type: "enum", values: ["configuration", "identity", "read", "collision", "delete", "truncate", "create-table", "alter-table", "drop-table", "history-write", "rollback"] },
    condition: { type: "enum", values: ["invalid-input", "not-confirmed", "unexpectedly-allowed", "unexpected-failure", "missing-record", "multiple-records", "digest-mismatch"] },
    effect: { type: "enum", values: ["not-started", "not-assessed", "unknown"] },
  } },
} as const);
export const entitySmokePreflightDiagnostic = defineDiagnostic({
  code: "entity-smoke-target.preflight-rejected", version: 1,
  classification: { failureKind: "configuration", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    identity: { type: "enum", values: ["administration", "migration", "runtime"] },
    field: { type: "enum", values: ["configuration", "identity", "database", "authority", "schema", "rollback"] },
    condition: { type: "enum", values: ["invalid-input", "count-mismatch", "wrong-type", "mismatch", "not-confirmed"] },
    effect: { type: "enum", values: ["not-started"] },
  } },
} as const);
export const entitySmokeTargetDiagnosticCatalog = { owner: "entity-smoke-target", definitions: [entitySmokeTargetDiagnostic, entitySmokeConfigurationDiagnostic, entitySmokeDatabaseConfigurationDiagnostic, entitySmokeProofDiagnostic, entitySmokeDependencyStateDiagnostic, entitySmokeDatabaseProofDiagnostic, entitySmokePreflightDiagnostic] } as const;
export const entitySmokeDiagnosticCatalogs = [coreDiagnosticCatalog, testEntityDiagnosticCatalog, platformPersistenceDiagnosticCatalog, platformSecurityDiagnosticCatalog,
  persistenceConfigurationDiagnosticCatalog, persistenceTaskOperationDiagnosticCatalog, entitySmokeTargetDiagnosticCatalog] as const;
/** Server builtins and the mounted app already register their own catalogs. */
export const entitySmokeServerDiagnosticCatalogs = [platformPersistenceDiagnosticCatalog, persistenceConfigurationDiagnosticCatalog,
  persistenceTaskOperationDiagnosticCatalog, entitySmokeTargetDiagnosticCatalog] as const;
const definitions = entitySmokeDiagnosticCatalogs.flatMap(catalog => [...catalog.definitions]);
// Startup consumes Server's returned errors as well as target/database errors.
// Select its public built-in owners here, without widening SQL-only mappings or
// re-registering those catalogs in the already composed server.
const startupDefinitions = [...definitions, ...[platformServerDiagnosticCatalog, platformRuntimeDiagnosticCatalog,
  platformContractDiagnosticCatalog, platformConfigDiagnosticCatalog, platformObservabilityDiagnosticCatalog,
  platformHealthDiagnosticCatalog].flatMap(catalog => [...catalog.definitions])];

export function entitySmokeConfigurationError(field: "database" | "schema" | "identity" | "region" | "authority" | "exposure" | "operation", reason: "invalid" | "mismatch" | "unavailable") {
  const checked = createDiagnosticRecord(entitySmokeConfigurationDiagnostic, { field, reason, effect: "not-started" });
  if (!checked.ok) throw new TypeError("ENTITY_SMOKE_DIAGNOSTIC_INVALID");
  return { code: "ENTITY_SMOKE_CONFIGURATION_INVALID", defaultMessage: "The isolated feature configuration is invalid.", diagnosticRecord: checked.value };
}

export function entitySmokeDatabaseConfigurationError(issues: readonly { readonly setting: string; readonly reason: string }[]) {
  const checked = configurationDiagnostic(entitySmokeDatabaseConfigurationDiagnostic, issues);
  if (!checked.ok) throw new TypeError("ENTITY_SMOKE_DIAGNOSTIC_INVALID");
  return { code: "ENTITY_SMOKE_CONFIGURATION_INVALID", defaultMessage: "The isolated database configuration is invalid.", diagnosticRecord: checked.value };
}

export function entitySmokeDependencyStateError(
  operation: "bootstrap" | "grant-runtime" | "observe-permissions" | "observe-migration-state" | "revoke-runtime" | "restore-runtime",
  field: "schema-owner" | "history-count" | "history-id" | "history-checksum" | "table-state" | "migration-lock" | "privileges" | "memberships" | "sessions" | "access-state",
  condition: "missing" | "count-mismatch" | "mismatch" | "not-confirmed" | "already-running",
) {
  const checked = createDiagnosticRecord(entitySmokeDependencyStateDiagnostic, {
    operation, field, condition, effect: operation.startsWith("observe-") ? "not-assessed" : "unknown",
  });
  if (!checked.ok) throw new TypeError("ENTITY_SMOKE_DIAGNOSTIC_INVALID");
  return { code: "ENTITY_SMOKE_DEPENDENCY_STATE_REJECTED", defaultMessage: "The observed feature dependency state does not permit this operation.", diagnosticRecord: checked.value };
}

export function reportEntitySmokeFailure(operation: "startup" | "migration" | "administration" | "readiness" | "close" | "verification", effect: "not-started" | "unknown" | "not-assessed", cause?: unknown): void {
  try {
  const selected = selectDiagnosticEvidence(operation === "startup" ? startupDefinitions : definitions, cause);
  const own = createDiagnosticRecord(entitySmokeTargetDiagnostic, { operation, effect });
  const diagnostic: DiagnosticRecord | undefined = selected.diagnosticRecord ?? (own.ok ? own.value : undefined);
  console.error(JSON.stringify({ verdict: "failed", code: "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED",
    ...(diagnostic === undefined ? {} : { diagnostic }), ...(selected.relatedDiagnosticRecords === undefined ? {} : { related_diagnostics: selected.relatedDiagnosticRecords }) }));
  } catch { /* Observation cannot replace the original outcome or replay work. */ }
}

