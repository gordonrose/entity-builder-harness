// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-postgresql-operation-diagnostics
//   version: 1
//   status: draft
//   created_on: "2026-10-31"
//   updated_on: "2026-10-31"
//   layer: 04.deploy
//   domain: persistence
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Own value-free PostgreSQL smoke composition observations without coupling task or configuration catalogs.
//   portability: { class: internal, targets: [kanbien/staging] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-platform-postgresql-persistence
//     path: infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-persistence.ts

import { coreDiagnosticCatalog } from "@kanbien/core";
import { createDiagnosticRecord, defineDiagnostic, selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { PlatformDiagnosticCatalog, PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { createPlatformDiagnosticReporter, platformObservabilityDiagnosticCatalog, reportPlatformDiagnostic } from "@kanbien/platform-observability";
import { platformPersistenceDiagnosticCatalog, observePlatformPersistenceDiagnostic, persistenceBoundaryDiagnosticRecord } from "@kanbien/platform-persistence";
import { postgreSqlPersistenceOperationError } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import { platformConfigDiagnosticCatalog } from "@kanbien/platform-config";
import { platformContractDiagnosticCatalog } from "@kanbien/platform-contracts";
import { kanbienPlatformConfigurationDiagnosticCatalog } from "./kanbien-platform-configuration-diagnostics";

export const persistenceCompositionBoundaryDiagnostic = defineDiagnostic({ code: "kanbien-platform.postgresql.composition-boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { operation: { type: "enum", values: ["migration", "compose", "create"] },
    phase: { type: "enum", values: ["schema-predicate", "configuration", "writer-construction", "input-projection", "work-item-id", "work-item-state", "work-item-revision", "work-item-accepted-at", "statement-staging", "staging-result"] },
    condition: { type: "enum", values: ["predicate-rejected", "threw", "returned-failure"] }, effect: { type: "enum", values: ["not-started", "not-staged", "unknown"] } } },
} as const);
export const kanbienPlatformPostgreSqlOperationDiagnosticCatalog = { owner: "kanbien-platform.postgresql", definitions: [persistenceCompositionBoundaryDiagnostic] } as const;
export type CompositionBoundaryDetail = NonNullable<typeof persistenceCompositionBoundaryDiagnostic.__detail>;
export type KanbienPlatformPostgreSqlDiagnosticContext = Pick<CompositionBoundaryDetail, "operation" | "phase">;
export interface KanbienPlatformPostgreSqlDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: KanbienPlatformPostgreSqlDiagnosticContext) => unknown;
}
const catalogs: readonly PlatformDiagnosticCatalog[] = [coreDiagnosticCatalog, platformPersistenceDiagnosticCatalog, platformSecurityDiagnosticCatalog, platformObservabilityDiagnosticCatalog, platformConfigDiagnosticCatalog, platformContractDiagnosticCatalog, kanbienPlatformConfigurationDiagnosticCatalog, kanbienPlatformPostgreSqlOperationDiagnosticCatalog];
const nativeThen = Promise.prototype.then;
function isolate(value: unknown): void {
  if (value === undefined) return;
  try { Reflect.apply(nativeThen, value, [undefined, () => undefined]); }
  catch { try { Reflect.apply(nativeThen, Promise.resolve(value), [undefined, () => undefined]); } catch { /* Optional observer. */ } }
}
export function observeKanbienPlatformPostgreSql(options: KanbienPlatformPostgreSqlDiagnosticOptions | undefined, detail: CompositionBoundaryDetail, cause?: unknown): void {
  try {
    let definitions: readonly DiagnosticDefinition[] = catalogs.flatMap((catalog) => catalog.definitions);
    try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { /* Optional selection. */ }
    const record = compositionBoundaryRecord(detail);
    const context = Object.freeze({ operation: detail.operation, phase: detail.phase });
    const source = selectDiagnosticEvidence(definitions, cause);
    const deliver = (record: DiagnosticRecord): void => { try { isolate(options?.onDiagnostic?.(record, context)); } catch { /* Preserve original result/throw. */ } };
    deliver(record);
    if (source.diagnosticRecord !== undefined) deliver(source.diagnosticRecord);
    for (const record of source.relatedDiagnosticRecords ?? []) deliver(record);
  } catch { /* Diagnostic construction cannot replace work. */ }
}
export function reportKanbienPlatformPostgreSqlDiagnostic(record: DiagnosticRecord, context?: KanbienPlatformPostgreSqlDiagnosticContext,
  options: { readonly diagnosticReporter?: PlatformDiagnosticReporter; readonly companionDiagnosticCatalogs?: readonly PlatformDiagnosticCatalog[] } = {}): void {
  try {
    const selectedCatalogs = [...catalogs, ...(options.companionDiagnosticCatalogs ?? [])];
    const selected = selectDiagnosticEvidence(selectedCatalogs.flatMap((catalog) => catalog.definitions), { diagnosticRecord: record }).diagnosticRecord;
    if (selected === undefined) return;
    const checkedContext = context === undefined ? undefined : compositionBoundaryRecord({ operation: context.operation, phase: context.phase, condition: "threw", effect: "unknown" }).detail;
    const reporter = options.diagnosticReporter ?? createPlatformDiagnosticReporter({ catalogs: selectedCatalogs, clock: { now: () => new Date() }, logger: { write(record) { console.error(JSON.stringify(record)); } } });
    const operation = checkedContext?.operation ?? "compose";
    reportPlatformDiagnostic(reporter, selected, { capability: "kanbien-platform.postgresql", operation, stage: operation === "migration" ? "migration" : operation === "create" ? "runtime" : "configuration" });
  } catch { /* Optional selected reporting never changes work. */ }
}
export function compositionBoundaryRecord(detail: CompositionBoundaryDetail) {
  const checked = createDiagnosticRecord(persistenceCompositionBoundaryDiagnostic, detail);
  if (!checked.ok) throw new TypeError("POSTGRESQL_COMPOSITION_DIAGNOSTIC_INVALID");
  return checked.value;
}

/** Actual one-shot task/resource evidence, not a composition-stage inference. */
export function reportKanbienPlatformPostgreSqlTaskDiagnostic(operation: "migration" | "connection-resource", record: DiagnosticRecord, cause?: unknown): void {
  try {
    const reporter = createPlatformDiagnosticReporter({ catalogs, clock: { now: () => new Date() }, logger: { write(record) { console.error(JSON.stringify(record)); } } });
    observePlatformPersistenceDiagnostic({ diagnosticDefinitions: catalogs.flatMap((catalog) => catalog.definitions),
      onDiagnostic: (record) => reportPlatformDiagnostic(reporter, record, { capability: "persistence", operation, stage: operation === "migration" ? "migration" : "runtime" }),
    }, record, cause);
  } catch { /* Never alter the existing task outcome, cleanup or raw throw. */ }
}

/** The unchanged outer catch owns source9; this bridge owns only new native/location facts. */
export function reportKanbienPlatformPostgreSqlMigrationInvocationFailure(cause: unknown): void {
  let generated = false;
  try {
    postgreSqlPersistenceOperationError("migration", cause, {
      diagnosticDefinitions: catalogs.flatMap((catalog) => catalog.definitions),
      onDiagnostic(record) {
        // Generation is not a claim that an optional sink successfully wrote.
        generated = true;
        reportKanbienPlatformPostgreSqlTaskDiagnostic("migration", record);
      },
    }, undefined, "native-only");
  } catch { /* Classification/reporting cannot replace the original throw. */ }
  if (!generated) try {
    reportKanbienPlatformPostgreSqlTaskDiagnostic("migration", persistenceBoundaryDiagnosticRecord({ operation: "migration", phase: "invocation", boundary: "body", condition: "threw", effect: "unknown" }));
  } catch { /* No native fact was available; do not invent a provider cause. */ }
}
