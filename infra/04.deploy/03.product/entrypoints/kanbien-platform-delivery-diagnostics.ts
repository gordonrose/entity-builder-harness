import { coreDiagnosticCatalog } from "@kanbien/core";
import {
  createDiagnosticRecord, defineDiagnostic, selectDiagnosticEvidence,
  type DiagnosticRecord,
} from "@kanbien/core/diagnostics";
import type { CoreQueueDiagnosticContext } from "@kanbien/core/queues";
import { coreQueueValidationDiagnostic, coreQueueBoundaryDiagnostic, coreQueueReceiveReductionDiagnostic } from "@kanbien/core/queues";
import {
  platformContractDiagnosticCatalog,
  platformProfileAllowsSignal,
  type PlatformCapabilityObservabilityProfile,
  type PlatformDiagnosticCatalog,
  type PlatformDiagnosticContext,
  type PlatformDiagnosticReporter,
} from "@kanbien/platform-contracts";
import {
  createPlatformDiagnosticReporter, platformObservabilityDiagnosticCatalog,
  reportPlatformDiagnostic,
} from "@kanbien/platform-observability";
import { platformPersistenceDiagnosticCatalog } from "@kanbien/platform-persistence";
import { platformWorkerDiagnosticCatalog } from "@kanbien/platform-workers";
import { platformRuntimeDiagnosticCatalog } from "@kanbien/platform-runtime";
import { platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import { kanbienPlatformSmokeWorkItemDeliveryObservabilityProfile } from "@kanbien/product-kanbien-platform";

/** Target coordination facts, not provider causes or changes to delivery policy. */
export const kanbienPlatformDeliveryBoundaryDiagnostic = defineDiagnostic({
  code: "kanbien-platform.delivery.boundary-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    workload: { type: "enum", values: ["worker", "relay", "relational-worker", "relational-relay"] },
    boundary: { type: "enum", values: ["receive", "delivery-selection", "enqueue", "run-next", "acknowledge", "release", "flush", "summary", "run-once", "acceptance", "identity-check", "owner-validation", "claim", "claim-result", "complete", "completion-result"] },
    condition: { type: "enum", values: ["threw", "returned-failure", "unexpected-disposition", "missing-lease", "payload-not-record", "payload-null", "payload-array", "payload-id-missing", "payload-id-wrong-type", "payload-id-mismatch", "not-delivery", "invalid-owner"] },
    disposition: { type: "enum", values: ["empty", "invalid", "delivery", "claimed", "already-completed", "lease-active", "completed", "released", "already-published", "idle", "contended", "published", "queue-send-failed", "publish-marker-failed", "unrecognized"] },
    effect: { type: "enum", values: ["work-not-invoked", "work-outcome-unknown", "work-success-acknowledgement-unknown", "work-success-acknowledgement-returned"] },
  }, optional: ["disposition"] },
} as const);
export type KanbienPlatformDeliveryBoundaryDetail = NonNullable<typeof kanbienPlatformDeliveryBoundaryDiagnostic.__detail>;
export const kanbienPlatformDeliveryDiagnosticCatalog = Object.freeze({
  owner: "kanbien-platform.delivery", definitions: Object.freeze([kanbienPlatformDeliveryBoundaryDiagnostic]),
});

export interface KanbienPlatformDeliveryDiagnosticOptions {
  readonly profile?: PlatformCapabilityObservabilityProfile;
  readonly diagnosticReporter?: PlatformDiagnosticReporter;
  readonly companionDiagnosticCatalogs?: readonly PlatformDiagnosticCatalog[];
}

function catalogs(options: KanbienPlatformDeliveryDiagnosticOptions): readonly PlatformDiagnosticCatalog[] {
  return [coreDiagnosticCatalog, platformPersistenceDiagnosticCatalog, platformWorkerDiagnosticCatalog,
    platformRuntimeDiagnosticCatalog, platformSecurityDiagnosticCatalog, platformObservabilityDiagnosticCatalog, platformContractDiagnosticCatalog,
    kanbienPlatformDeliveryDiagnosticCatalog, ...(options.companionDiagnosticCatalogs ?? [])];
}

/** One invocation owns this selection; no mutable request, queue or process context. */
function deliver(own: DiagnosticRecord | undefined, cause: unknown, context: PlatformDiagnosticContext,
  options: KanbienPlatformDeliveryDiagnosticOptions): void {
  try {
    if (context.stage !== "startup" && !platformProfileAllowsSignal(
      options.profile ?? kanbienPlatformSmokeWorkItemDeliveryObservabilityProfile, "operational_log")) return;
    const selectedCatalogs = catalogs(options);
    const definitions = selectedCatalogs.flatMap((catalog) => catalog.definitions);
    const selectedOwn = own === undefined ? undefined : selectDiagnosticEvidence(definitions, { diagnosticRecord: own }).diagnosticRecord;
    const source = selectDiagnosticEvidence(definitions, cause);
    const defaultReporter = createPlatformDiagnosticReporter({
      catalogs: selectedCatalogs, clock: { now: () => new Date() },
      logger: { write(record) { console.error(JSON.stringify(record)); } },
    });
    const reporter = options.diagnosticReporter ?? defaultReporter;
    if (selectedOwn !== undefined) reportPlatformDiagnostic(reporter, selectedOwn, context);
    if (source.diagnosticRecord !== undefined) reportPlatformDiagnostic(reporter, source.diagnosticRecord, context);
    for (const record of source.relatedDiagnosticRecords ?? []) reportPlatformDiagnostic(reporter, record, context);
  } catch { /* Optional evidence must not replace a task outcome or raw throw. */ }
}

/** The adapter supplies its actual operation for every independently selected source. */
export function reportKanbienPlatformQueueDiagnostic(
  workload: KanbienPlatformDeliveryBoundaryDetail["workload"], record: DiagnosticRecord,
  observed?: CoreQueueDiagnosticContext, options: KanbienPlatformDeliveryDiagnosticOptions = {},
): void {
  try {
    if (!allowedEnum(kanbienPlatformDeliveryBoundaryDiagnostic, "workload", workload)) return;
    let operation = "queue-observation";
    if (observed !== undefined) {
      const field = Object.getOwnPropertyDescriptor(observed, "operation");
      if (field === undefined || !("value" in field) || typeof field.value !== "string"
        || ![coreQueueValidationDiagnostic, coreQueueBoundaryDiagnostic, coreQueueReceiveReductionDiagnostic]
          .some((definition) => allowedEnum(definition, "operation", field.value))) return;
      operation = field.value;
    }
    deliver(record, undefined, { capability: "queue", operation: `${workload}.${operation}`,
      stage: operation === "client-initialization" ? "startup" : "runtime" }, options);
  } catch { /* Optional context is copied only from its closed code-owned values. */ }
}

function allowedEnum(definition: import("@kanbien/core/diagnostics").DiagnosticDefinition, field: string, value: unknown): boolean {
  const schema = definition.detail;
  if (schema.type !== "object") return false;
  const property = schema.properties[field];
  return property?.type === "enum" && property.values.some((allowed) => allowed === value);
}

export function reportKanbienPlatformDeliveryFailure(detail: KanbienPlatformDeliveryBoundaryDetail,
  cause?: unknown, options: KanbienPlatformDeliveryDiagnosticOptions = {}): void {
  try {
    const record = createDiagnosticRecord(kanbienPlatformDeliveryBoundaryDiagnostic, detail);
    if (record.ok) deliver(record.value, cause,
      { capability: "kanbien-platform.delivery", operation: detail.boundary, stage: "runtime" }, options);
  } catch { /* No raw submitted/provider values enter this bounded target record. */ }
}

/** Optional evidence must not add an error accessor to the workload's reads. */
export function targetDeliveryErrorSource(result: unknown): unknown {
  try {
    if ((typeof result !== "object" || result === null) && typeof result !== "function") return undefined;
    const field = Object.getOwnPropertyDescriptor(result, "error");
    return field !== undefined && "value" in field ? field.value : undefined;
  } catch { return undefined; }
}

export function targetDeliveryDisposition(value: unknown): NonNullable<KanbienPlatformDeliveryBoundaryDetail["disposition"]> {
  switch (value) {
    case "empty": case "invalid": case "delivery": case "claimed": case "already-completed":
    case "lease-active": case "completed": case "released": case "already-published": case "idle":
    case "contended": case "published": case "queue-send-failed": case "publish-marker-failed": return value;
    default: return "unrecognized";
  }
}

export function reportKanbienPlatformPersistenceDeliveryDiagnostic(record: DiagnosticRecord,
  operation: "acceptance" | "claim" | "complete" | "relay",
  options: KanbienPlatformDeliveryDiagnosticOptions = {}): void {
  switch (operation) {
    case "acceptance": case "claim": case "complete": case "relay":
      deliver(record, undefined, { capability: "persistence", operation, stage: "runtime" }, options);
  }
}
