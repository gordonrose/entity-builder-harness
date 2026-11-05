// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-operation-diagnostics
//   version: 1
//   status: draft
//   created_on: "2026-10-31"
//   updated_on: "2026-10-31"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Preserve bounded task-local predicate and boundary observations independently of selected source evidence.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-administration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts

import { coreDiagnosticCatalog } from "@kanbien/core";
import { createDiagnosticRecord, defineDiagnostic, parseRelatedDiagnosticRecords, selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformPersistenceDiagnosticCatalog, persistenceBoundaryDiagnosticRecord, observePlatformPersistenceDiagnostic, type PersistenceBoundaryDetail } from "@kanbien/platform-persistence";
import { platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import { platformObservabilityDiagnosticCatalog, createPlatformDiagnosticReporter, reportPlatformDiagnostic } from "@kanbien/platform-observability";
import type { PlatformDiagnosticCatalog } from "@kanbien/platform-contracts";
import { persistenceConfigurationDiagnosticCatalog, persistenceTaskDiagnosticFields } from "./kanbien-core-server-persistence-configuration";

const predicateClassification = { failureKind: "validation", failureSource: "app", severity: "error", recovery: "manual_investigation" } as const;
const boundaryClassification = { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" } as const;
const ordinal = { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER } as const;
const adminOperations = ["role-identifier", "role-facts", "bounded-role", "elevated-role", "ensure-login-role", "iam-membership", "revoke-runtime", "restore-runtime", "bootstrap-identities", "schema-bootstrap", "relation-ownership", "application-access", "migration-state", "runtime-privilege", "permission-probe", "administration"] as const;
const adminFields = ["identifier", "row", "exists", "can-login", "superuser", "create-role", "create-database", "replication", "bypass-rls", "inherit", "member", "terminated", "termination-result", "function-count", "migration-count", "migration-id", "migration-checksum", "read-count", "provider-code", "role-facts", "configuration", "schema", "relation-name", "relation-kind", "require-login"] as const;
export const persistenceAdministrationPredicateDiagnostic = defineDiagnostic({ code: "kanbien-core-server.operations.administration-predicate-rejected", version: 1, classification: predicateClassification,
  detail: { type: "object", properties: { task: { type: "enum", values: ["administration"] }, operation: { type: "enum", values: adminOperations }, field: { type: "enum", values: adminFields },
    condition: { type: "enum", values: ["pattern", "missing", "wrong-type", "false", "falsy", "truthy", "not-true", "not-zero", "not-one", "count-mismatch", "id-mismatch", "checksum-mismatch", "denial-code-mismatch", "permission-permitted", "predicate-rejected"] },
    effect: { type: "enum", values: ["predicate-rejected"] }, ordinal }, optional: ["ordinal"] },
} as const);
export const persistenceAdministrationBoundaryDiagnostic = defineDiagnostic({ code: "kanbien-core-server.operations.administration-boundary-failed", version: 1, classification: boundaryClassification,
  detail: { type: "object", properties: { task: { type: "enum", values: ["administration"] }, operation: { type: "enum", values: adminOperations },
    phase: { type: "enum", values: ["input-projection", "identifier-predicate", "role-facts-query", "role-facts-projection", "create-role", "set-noinherit", "bounded-role", "grant-iam", "iam-membership-query", "iam-membership-projection", "revoke-iam", "disable-login", "terminate-sessions", "termination-traversal", "enable-login", "configuration", "pool-construction", "identity-boundary", "iam-membership", "database-access", "schema-ownership", "begin", "create-schema", "migration-history", "relation-ownership", "runtime-boundary", "commit", "rollback", "relation-query", "relation-traversal", "function-count-query", "function-count-projection", "grant-runtime", "history-read", "history-traversal", "pool-connect", "runtime-insert", "runtime-read", "runtime-read-projection", "permission-history", "permission-schema", "permission-code", "runtime-role-query", "runtime-role-projection", "client-release", "pool-end", "task-body", "authentication-preflight", "failure-projection", "set-local-role", "pool-import", "result-projection"] },
    field: { type: "enum", values: adminFields }, condition: { type: "enum", values: ["threw"] }, effect: { type: "enum", values: ["unknown", "not-assessed", "not-started"] }, ordinal }, optional: ["field", "ordinal"] },
} as const);
const verifierFields = ["mode", "base-url", "record-id", "fact", "status", "body", "outcome", "record", "record-id-result", "fact-digest-result", "live-status", "ready-status", "ready-ok"] as const;
export const persistenceVerificationPredicateDiagnostic = defineDiagnostic({ code: "kanbien-core-server.operations.verification-predicate-rejected", version: 1, classification: predicateClassification,
  detail: { type: "object", properties: { task: { type: "enum", values: ["verification"] }, operation: { type: "enum", values: ["verification", "health"] }, field: { type: "enum", values: verifierFields },
    condition: { type: "enum", values: ["missing", "wrong-type", "unsupported", "pattern", "empty", "too-long", "status-mismatch", "wrong-outcome", "missing-record", "id-mismatch", "digest-mismatch", "unexpected-ok", "predicate-rejected"] }, effect: { type: "enum", values: ["predicate-rejected"] } } },
} as const);
export const persistenceVerificationBoundaryDiagnostic = defineDiagnostic({ code: "kanbien-core-server.operations.verification-boundary-failed", version: 1, classification: boundaryClassification,
  detail: { type: "object", properties: { task: { type: "enum", values: ["verification"] }, operation: { type: "enum", values: ["verification", "health"] }, field: { type: "enum", values: verifierFields },
    phase: { type: "enum", values: ["input-projection", "predicate", "fact-digest", "request-projection", "request-timeout", "fetch", "response-json", "response-predicate", "live-timeout", "live-fetch", "ready-timeout", "ready-fetch", "health-settlement", "health-predicate", "result-projection"] }, condition: { type: "enum", values: ["threw", "rejected"] }, effect: { type: "enum", values: ["unknown", "not-assessed", "not-started"] } }, optional: ["field"] },
} as const);
export const persistenceTaskOperationDiagnosticCatalog = { owner: "kanbien-core-server.operations", definitions: [persistenceAdministrationPredicateDiagnostic, persistenceAdministrationBoundaryDiagnostic, persistenceVerificationPredicateDiagnostic, persistenceVerificationBoundaryDiagnostic] } as const;
export type AdministrationPredicateDetail = NonNullable<typeof persistenceAdministrationPredicateDiagnostic.__detail>;
export type AdministrationBoundaryDetail = NonNullable<typeof persistenceAdministrationBoundaryDiagnostic.__detail>;
export type VerificationPredicateDetail = NonNullable<typeof persistenceVerificationPredicateDiagnostic.__detail>;
export type VerificationBoundaryDetail = NonNullable<typeof persistenceVerificationBoundaryDiagnostic.__detail>;
function required<T>(definition: DiagnosticDefinition<T>, detail: NoInfer<T>): DiagnosticRecord<T> { const result = createDiagnosticRecord(definition, detail); if (!result.ok) throw new TypeError("PERSISTENCE_TASK_DIAGNOSTIC_INVALID"); return result.value; }
export const administrationPredicateRecord = (detail: Omit<AdministrationPredicateDetail, "task" | "effect">) => required(persistenceAdministrationPredicateDiagnostic, { task: "administration", effect: "predicate-rejected", ...detail });
export const administrationBoundaryRecord = (detail: Omit<AdministrationBoundaryDetail, "task" | "condition">) => required(persistenceAdministrationBoundaryDiagnostic, { task: "administration", condition: "threw", ...detail });
export const verificationPredicateRecord = (detail: Omit<VerificationPredicateDetail, "task" | "effect">) => required(persistenceVerificationPredicateDiagnostic, { task: "verification", effect: "predicate-rejected", ...detail });
export const verificationBoundaryRecord = (detail: Omit<VerificationBoundaryDetail, "task">) => required(persistenceVerificationBoundaryDiagnostic, { task: "verification", ...detail });

export const persistenceAdministrationFailureCodes = ["PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID", "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED", "PERSISTENCE_ADMINISTRATION_ACCESS_DENIED", "PERSISTENCE_ADMINISTRATION_CREDENTIAL_REJECTED", "PERSISTENCE_ROLE_PRIVILEGE_BOUNDARY_NOT_CONFIRMED", "PERSISTENCE_RUNTIME_ROLE_MISSING", "PERSISTENCE_ROLE_STATE_UNAVAILABLE", "PERSISTENCE_ROLE_REACTIVATION_REQUIRES_EXPLICIT_RECOVERY", "PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED", "PERSISTENCE_RUNTIME_DML_NOT_CONFIRMED", "PERSISTENCE_RUNTIME_PERMISSION_DENIAL_NOT_CONFIRMED", "PERSISTENCE_RUNTIME_PERMISSION_UNEXPECTEDLY_PERMITTED", "PERSISTENCE_RUNTIME_ADMINISTRATION_UNEXPECTEDLY_PERMITTED", "PERSISTENCE_MIGRATION_STATE_ALREADY_APPLIED", "PERSISTENCE_MIGRATION_STATE_REVIEW_REQUIRED", "PERSISTENCE_RUNTIME_REVOCATION_IAM_MEMBERSHIP_NOT_CONFIRMED", "PERSISTENCE_RUNTIME_REVOCATION_LOGIN_DISABLED_NOT_CONFIRMED", "PERSISTENCE_RUNTIME_REVOCATION_SESSION_TERMINATION_NOT_CONFIRMED", "PERSISTENCE_RUNTIME_SESSION_TERMINATION_NOT_CONFIRMED", "PERSISTENCE_RUNTIME_RECOVERY_LOGIN_RESTORED_NOT_CONFIRMED", "PERSISTENCE_RUNTIME_RECOVERY_IAM_MEMBERSHIP_NOT_CONFIRMED"] as const;
export const persistenceVerificationFailureCodes = ["VERIFIER_CONFIGURATION_INVALID", "KANBIEN_CORE_PERSISTENCE_VERIFICATION_REJECTED", "KANBIEN_CORE_PERSISTENCE_VERIFICATION_UNAVAILABLE", "KANBIEN_CORE_PERSISTENCE_HEALTH_VERIFICATION_REJECTED", "KANBIEN_CORE_PERSISTENCE_HEALTH_VERIFICATION_UNAVAILABLE"] as const;
export const persistenceTaskFailureContract = { schema: "deploy/persistence-task-failure/v1", maxObservations: 8, maxSourceBundles: 8, maxOverflowCount: Number.MAX_SAFE_INTEGER, codes: { administration: persistenceAdministrationFailureCodes, verification: persistenceVerificationFailureCodes } } as const;
export type PersistenceTask = "administration" | "verification";
export interface PersistenceTaskSourceEvidence { readonly diagnosticRecord?: DiagnosticRecord; readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[]; }
export interface PersistenceTaskDiagnosticOptions { readonly onObservation?: (record: DiagnosticRecord, source: PersistenceTaskSourceEvidence) => unknown; }
const sourceDefinitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...platformPersistenceDiagnosticCatalog.definitions, ...persistenceConfigurationDiagnosticCatalog.definitions, ...platformSecurityDiagnosticCatalog.definitions, ...platformObservabilityDiagnosticCatalog.definitions];
const nativeThen = Promise.prototype.then;
/** Independent task body/cleanup evidence; existing result serializers stay unchanged. */
export function reportCoreServerPersistenceBoundary(operation: "migration" | "restore-verification", detail: PersistenceBoundaryDetail, cause: unknown): void {
  try {
    const catalogs: readonly PlatformDiagnosticCatalog[] = [coreDiagnosticCatalog, platformPersistenceDiagnosticCatalog, platformSecurityDiagnosticCatalog, platformObservabilityDiagnosticCatalog, persistenceConfigurationDiagnosticCatalog];
    const reporter = createPlatformDiagnosticReporter({ catalogs, clock: { now: () => new Date() }, logger: { write(record) { console.error(JSON.stringify(record)); } } });
    observePlatformPersistenceDiagnostic({ diagnosticDefinitions: catalogs.flatMap((catalog) => catalog.definitions),
      onDiagnostic: (record) => reportPlatformDiagnostic(reporter, record, { capability: "persistence", operation, stage: operation === "migration" ? "migration" : "recovery" }),
    }, persistenceBoundaryDiagnosticRecord(detail), cause);
  } catch { /* This optional channel cannot replace an existing outcome or throw. */ }
}
export function observePersistenceTask(options: PersistenceTaskDiagnosticOptions | undefined, record: DiagnosticRecord, cause?: unknown): void {
  try {
    const own = selectDiagnosticEvidence(persistenceTaskOperationDiagnosticCatalog.definitions, { diagnosticRecord: record }).diagnosticRecord;
    if (own === undefined) return;
    const selected = selectDiagnosticEvidence(sourceDefinitions, cause);
    const fields = persistenceTaskDiagnosticFields(selected.diagnosticRecord, selected.relatedDiagnosticRecords);
    const source = Object.freeze({ ...(fields.diagnostic === undefined ? {} : { diagnosticRecord: fields.diagnostic }), ...(fields.related_diagnostics === undefined ? {} : { relatedDiagnosticRecords: fields.related_diagnostics }) });
    const returned = options?.onObservation?.(own, source);
    if (returned !== undefined) try { Reflect.apply(nativeThen, returned, [undefined, () => undefined]); } catch { Reflect.apply(nativeThen, Promise.resolve(returned), [undefined, () => undefined]); }
  } catch { /* Diagnostic observers cannot replace the original work or throw. */ }
}

/** Only actual failure-unwind locations are retained, never statement history. */
export class PersistenceTaskObservations {
  readonly options: PersistenceTaskDiagnosticOptions;
  private readonly records: DiagnosticRecord[] = [];
  private firstSource: PersistenceTaskSourceEvidence = {};
  private readonly sources: PersistenceTaskSourceEvidence[] = [];
  private readonly overflow = { observations: 0, source_bundles: 0 };
  private published = false;
  private serializationReached = false;
  constructor(readonly task: PersistenceTask, options?: PersistenceTaskDiagnosticOptions) {
    this.options = { onObservation: (record, source) => {
      if (record.detail !== null && typeof record.detail === "object" && (record.detail as { task?: unknown }).task !== task) return;
      if (this.published) {
        try { console.error(JSON.stringify(this.envelope(undefined, source, [record]))); } catch { /* Independent late observation, never a business failure. */ }
      } else {
        if (this.records.length < persistenceTaskFailureContract.maxObservations) this.records.push(record);
        else this.overflow.observations = Math.min(persistenceTaskFailureContract.maxOverflowCount, this.overflow.observations + 1);
        this.retainSource(source);
      }
      observePersistenceTask(options, record, source);
    } };
  }
  private retainSource(source: PersistenceTaskSourceEvidence): void {
    if (source.diagnosticRecord === undefined) return;
    if (this.firstSource.diagnosticRecord === undefined) this.firstSource = source;
    else if (JSON.stringify(source) !== JSON.stringify(this.firstSource) && !this.sources.some((retained) => JSON.stringify(retained) === JSON.stringify(source))) {
      if (this.sources.length < persistenceTaskFailureContract.maxSourceBundles) this.sources.push(source);
      else this.overflow.source_bundles = Math.min(persistenceTaskFailureContract.maxOverflowCount, this.overflow.source_bundles + 1);
    }
  }
  markSerializationReached(): void { this.serializationReached = true; }
  markPublished(): void { this.serializationReached = true; this.published = true; }
  publishUncaught(): void {
    if (this.serializationReached) return;
    this.serializationReached = true;
    try { console.error(JSON.stringify(this.failure(this.task === "administration" ? "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED" : "KANBIEN_CORE_PERSISTENCE_VERIFICATION_UNAVAILABLE"))); } catch { /* Unavailable diagnostics never replace the raw throw. */ }
    this.published = true;
  }
  envelope(code?: string, source: PersistenceTaskSourceEvidence = this.firstSource, observations: readonly DiagnosticRecord[] = this.records) {
    const allowed: readonly string[] = persistenceTaskFailureContract.codes[this.task];
    const safeCode = code !== undefined && allowed.includes(code) ? code : this.task === "administration" ? "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED" : "KANBIEN_CORE_PERSISTENCE_VERIFICATION_UNAVAILABLE";
    const selected = selectDiagnosticEvidence(sourceDefinitions, source);
    const copied = parseRelatedDiagnosticRecords(persistenceTaskOperationDiagnosticCatalog.definitions, observations);
    const own = copied.ok && copied.value.every((record) => (record.detail as { task?: unknown }).task === this.task) ? copied.value : [];
    return { schema: persistenceTaskFailureContract.schema, task: this.task, verdict: "rejected" as const, code: safeCode,
      ...persistenceTaskDiagnosticFields(selected.diagnosticRecord, selected.relatedDiagnosticRecords), observations: own,
      ...(this.published || this.sources.length === 0 ? {} : { source_bundles: this.sources.map((bundle) => persistenceTaskDiagnosticFields(bundle.diagnosticRecord, bundle.relatedDiagnosticRecords)) }),
      ...(this.published || this.overflow.observations === 0 && this.overflow.source_bundles === 0 ? {} : { overflow: { ...this.overflow } }) };
  }
  failure(code: string, source?: PersistenceTaskSourceEvidence) {
    if (!this.published && source !== undefined) this.retainSource(selectDiagnosticEvidence(sourceDefinitions, source));
    return this.envelope(code);
  }
}

export class AdministrationObservation {
  private phase: AdministrationBoundaryDetail["phase"] = "input-projection";
  private field: AdministrationBoundaryDetail["field"] | undefined;
  private ordinal: number | undefined;
  private predicateError: unknown;
  private predicateFailed = false;
  constructor(readonly operation: AdministrationBoundaryDetail["operation"], readonly options?: PersistenceTaskDiagnosticOptions) {}
  location(phase: AdministrationBoundaryDetail["phase"], field?: AdministrationBoundaryDetail["field"], ordinal?: number): void { this.phase = phase; this.field = field; this.ordinal = ordinal; this.predicateFailed = false; }
  checkpoint(): () => void {
    const phase = this.phase, field = this.field, ordinal = this.ordinal, predicateFailed = this.predicateFailed, predicateError = this.predicateError;
    return () => { this.phase = phase; this.field = field; this.ordinal = ordinal; this.predicateFailed = predicateFailed; this.predicateError = predicateError; };
  }
  argument<T>(phase: AdministrationBoundaryDetail["phase"], field: AdministrationBoundaryDetail["field"] | undefined, value: T, ordinal?: number): T { this.location(phase, field, ordinal); return value; }
  rejected<T>(error: T, field: AdministrationPredicateDetail["field"], condition: AdministrationPredicateDetail["condition"], ordinal?: number, source?: unknown): T {
    this.predicateError = error; this.predicateFailed = true;
    observePersistenceTask(this.options, administrationPredicateRecord({ operation: this.operation, field, condition, ...(ordinal === undefined ? {} : { ordinal }) }), source);
    return error;
  }
  retained<T>(error: T): T { this.predicateError = error; this.predicateFailed = true; return error; }
  failed(cause: unknown, effect?: AdministrationBoundaryDetail["effect"]): void {
    if (this.predicateFailed && cause === this.predicateError) return;
    this.predicateFailed = true; this.predicateError = cause;
    const observedEffect = effect ?? (["input-projection", "identifier-predicate", "configuration", "pool-import", "authentication-preflight"].includes(this.phase) ? "not-started" : "unknown");
    observePersistenceTask(this.options, administrationBoundaryRecord({ operation: this.operation, phase: this.phase, effect: observedEffect,
      ...(this.field === undefined ? {} : { field: this.field }), ...(this.ordinal === undefined ? {} : { ordinal: this.ordinal }) }), cause);
  }
  run<T>(action: () => T): T { try { return action(); } catch (cause) { this.failed(cause); throw cause; } }
  at<T>(phase: AdministrationBoundaryDetail["phase"], field: AdministrationBoundaryDetail["field"] | undefined, action: () => T, ordinal?: number): T { this.location(phase, field, ordinal); return action(); }
  async runAsync<T>(action: () => Promise<T>): Promise<T> { try { return await action(); } catch (cause) { this.failed(cause); throw cause; } }
}

/** Invocation-local provenance; no old error record can suppress a new throw. */
export class VerificationObservation {
  private phase: VerificationBoundaryDetail["phase"] = "input-projection";
  private field: VerificationBoundaryDetail["field"] | undefined;
  private emitted = false;
  private emittedCause: unknown;
  private rejection: Omit<VerificationPredicateDetail, "task" | "effect" | "operation"> | undefined;
  constructor(readonly operation: VerificationBoundaryDetail["operation"], readonly options?: PersistenceTaskDiagnosticOptions) {}
  location(phase: VerificationBoundaryDetail["phase"], field?: VerificationBoundaryDetail["field"]): void { this.phase = phase; this.field = field; this.emitted = false; }
  at<T>(phase: VerificationBoundaryDetail["phase"], field: VerificationBoundaryDetail["field"] | undefined, action: () => T): T { this.location(phase, field); return action(); }
  invocationArgument<T>(phase: VerificationBoundaryDetail["phase"], value: T): T { this.location(phase); return value; }
  matches(field: VerificationPredicateDetail["field"], condition: VerificationPredicateDetail["condition"], action: () => boolean): boolean {
    const matched = this.at(this.operation === "health" ? "health-predicate" : "response-predicate", field, action);
    if (!matched && this.rejection === undefined) this.rejection = { field, condition };
    return matched;
  }
  rejected(field?: VerificationPredicateDetail["field"], condition?: VerificationPredicateDetail["condition"]): void {
    const detail = field === undefined || condition === undefined ? this.rejection ?? { field: "body" as const, condition: "predicate-rejected" as const } : { field, condition };
    observePersistenceTask(this.options, verificationPredicateRecord({ operation: this.operation, ...detail }));
  }
  failed(cause: unknown, condition: VerificationBoundaryDetail["condition"] = "threw", phase = this.phase): void {
    if (this.emitted && cause === this.emittedCause) return;
    this.emitted = true; this.emittedCause = cause;
    observePersistenceTask(this.options, verificationBoundaryRecord({ operation: this.operation, phase, condition, effect: phase === "input-projection" || phase === "predicate" || phase === "fact-digest" || phase.endsWith("timeout") || phase === "request-projection" ? "not-started" : "unknown", ...(this.field === undefined ? {} : { field: this.field }) }), cause);
  }
  invoke<T>(phase: VerificationBoundaryDetail["phase"], action: () => Promise<T>): Promise<T> {
    this.location(phase);
    let returned: Promise<T>;
    try { returned = action(); } catch (cause) { this.failed(cause); throw cause; }
    const settle = async (): Promise<T> => {
      try { return await returned; } catch (cause) { this.location(phase); this.failed(cause, "rejected"); throw cause; }
    };
    return settle();
  }
  async run<T>(action: () => Promise<T>): Promise<T> { try { return await action(); } catch (cause) { this.failed(cause); throw cause; } }
}
