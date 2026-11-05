import type { Logger } from "@kanbien/core/logging";
import { coreDiagnosticCatalog } from "@kanbien/core";
import type { DiagnosticDefinition } from "@kanbien/core/diagnostics";
import { noopTracer, type Metrics, type Tracer } from "@kanbien/core/monitoring";
import type { Clock, Result } from "@kanbien/core/shared";
import {
  platformProfileAllowsSignal,
  platformErrorClassDeclarations,
  platformProfileLogFields,
  platformProfileMetricLabels,
  platformProfileTraceFields,
  validatePlatformCapabilityObservabilityProfile,
  type PlatformCapabilityAction,
  type PlatformCapabilityName,
  type PlatformCapabilityObservabilityProfile,
  type PlatformExecutionContext,
  type PlatformDiagnosticCatalog,
  validatePlatformDiagnosticCatalog,
  type PlatformDiagnosticReporter,
} from "@kanbien/platform-contracts";
import {
  endPlatformTraceSpan,
  platformErrorClass,
  recordPlatformMetric,
  startPlatformTraceSpan,
  writePlatformLog,
  createPlatformDiagnosticReporter,
  createPlatformMetricDiagnosticBinding,
  platformObservabilityDiagnosticCatalog,
  reportPlatformDiagnostic,
  reportPlatformObservationBoundary,
  reportPlatformObservationSources,
  type PlatformObservationDiagnostics,
  type PlatformObservationBoundaryDetail,
} from "@kanbien/platform-observability";
import type { PlatformPersistenceObservation, PlatformPersistenceObserver } from "./port";
import { platformPersistenceDiagnosticCatalog, selectPlatformPersistenceDiagnosticEvidence } from "../diagnostics";
import { platformPersistenceErrorClasses } from "../errors";

const platformPersistenceTransitionFieldNames = [
  "capability",
  "action",
  "execution_context",
  "outcome",
  "error_class",
] as const;

export interface PlatformPersistenceTransitionObserverOptions {
  readonly profile: PlatformCapabilityObservabilityProfile;
  readonly executionContext: PlatformExecutionContext;
  readonly logger: Logger;
  readonly metrics: Metrics;
  readonly tracer?: Tracer;
  readonly clock: Clock;
  /** Composition explicitly selects cross-cutting catalogs; no provider coupling. */
  readonly companionDiagnosticCatalogs?: readonly PlatformDiagnosticCatalog[];
  readonly diagnosticReporter?: PlatformDiagnosticReporter;
}

export function platformPersistenceTransitionProfile(input: {
  readonly name: PlatformCapabilityObservabilityProfile["name"];
  readonly capability: PlatformCapabilityName;
  readonly action?: PlatformCapabilityAction;
}): PlatformCapabilityObservabilityProfile {
  return {
    name: input.name,
    capability: input.capability,
    action: input.action ?? "execute",
    errorClasses: platformPersistenceErrorClasses,
    signals: ["operational_log", "metric", "trace"],
    logFieldNames: platformPersistenceTransitionFieldNames,
    metricDimensionFieldNames: platformPersistenceTransitionFieldNames,
    traceAttributeNames: platformPersistenceTransitionFieldNames,
  };
}

export function createPlatformPersistenceTransitionObserver(
  options: PlatformPersistenceTransitionObserverOptions,
): Result<PlatformPersistenceObserver, import("@kanbien/platform-contracts").PlatformContractError> {
  const validation = validatePlatformCapabilityObservabilityProfile(options.profile);
  if (!validation.ok) {
    return validation;
  }
  options = { ...options, profile: { ...options.profile,
    errorClasses: Object.freeze([...new Set([...platformPersistenceErrorClasses, ...(platformErrorClassDeclarations(options.profile) ?? [])])]) } };
  let diagnostics: ReturnType<typeof createPlatformDiagnosticReporter>;
  let selectedDefinitions: readonly DiagnosticDefinition[];
  try {
    const builtins: readonly PlatformDiagnosticCatalog[] = [coreDiagnosticCatalog, platformPersistenceDiagnosticCatalog, platformObservabilityDiagnosticCatalog];
    const catalogs: PlatformDiagnosticCatalog[] = [...builtins];
    const explicitBuiltins = new Set<string>();
    for (const catalog of options.companionDiagnosticCatalogs ?? []) {
      const checked = validatePlatformDiagnosticCatalog(catalog);
      if (!checked.ok) throw new TypeError("PERSISTENCE_COMPANION_DIAGNOSTIC_CATALOG_INVALID");
      const builtin = builtins.find((item) => item.owner === checked.value.owner);
      if (builtin !== undefined) {
        if (canonicalCatalog(checked.value) !== canonicalCatalog(builtin)) throw new TypeError("PERSISTENCE_COMPANION_DIAGNOSTIC_CATALOG_CONFLICT");
        if (explicitBuiltins.has(builtin.owner)) throw new TypeError("PERSISTENCE_COMPANION_DIAGNOSTIC_CATALOG_DUPLICATE");
        explicitBuiltins.add(builtin.owner);
      } else catalogs.push(checked.value);
    }
    const defaultReporter = createPlatformDiagnosticReporter({ catalogs, logger: options.logger, clock: options.clock });
    selectedDefinitions = catalogs.flatMap((catalog) => catalog.definitions);
    diagnostics = options.diagnosticReporter ?? defaultReporter;
  } catch {
    return { ok: false, error: { code: "PLATFORM_CONTRACT_MALFORMED_DIAGNOSTIC_CATALOG", defaultMessage: "Persistence companion diagnostic catalog is invalid." } };
  }

  const metricDiagnostics = createPlatformMetricDiagnosticBinding(diagnostics, { capability: "persistence", stage: "request" });
  const observationDiagnostics: PlatformObservationDiagnostics = { reporter: diagnostics, definitions: selectedDefinitions,
    context: { capability: "persistence", operation: "persistence-observation", stage: "request" } };
  const permittedObservations = (): PlatformObservationDiagnostics | undefined => {
    try { return platformProfileAllowsSignal(options.profile, "operational_log") ? observationDiagnostics : undefined; }
    catch { return undefined; }
  };
  return {
    ok: true,
    value: {
      onDiagnostic(record, operation = "store-observation") {
        if (!platformProfileAllowsSignal(options.profile, "operational_log")) return;
        const selected = selectPlatformPersistenceDiagnosticEvidence({ diagnosticDefinitions: selectedDefinitions }, { diagnosticRecord: record });
        if (selected.diagnosticRecord !== undefined) reportPlatformDiagnostic(diagnostics, selected.diagnosticRecord,
          { capability: "persistence", operation, stage: "runtime" });
      },
      record(observation) {
        let phase: PlatformObservationBoundaryDetail["phase"] = "profile-projection";
        let traceHelperEntered = false;
        try {
        const nomenclature = persistenceNomenclature(options, observation, () => { phase = "error-class"; });
        phase = "log-projection";
        const message = `platform.persistence.${observation.transition}`;

        phase = "profile-projection";
        if (platformProfileAllowsSignal(options.profile, "operational_log")) {
          phase = "log-projection";
          const context = { capability: "persistence", operation: "transition", stage: "request" as const,
            ...(observation.correlationId === undefined ? {} : { correlationId: observation.correlationId }) };
          const selectionOptions = { diagnosticDefinitions: selectedDefinitions };
          const independent = selectPlatformPersistenceDiagnosticEvidence(selectionOptions, observation);
          const source = selectPlatformPersistenceDiagnosticEvidence(selectionOptions, observation.error);
          if (independent.diagnosticRecord !== undefined) reportPlatformDiagnostic(diagnostics, independent.diagnosticRecord, context);
          if (source.diagnosticRecord !== undefined) reportPlatformDiagnostic(diagnostics, source.diagnosticRecord, context);
          for (const record of source.relatedDiagnosticRecords ?? []) reportPlatformDiagnostic(diagnostics, record, context);
          writePlatformLog(options.logger, {
            level: persistenceLogLevel(observation.outcome),
            message,
            ...(observation.correlationId === undefined ? {} : { correlationId: observation.correlationId }),
            fields: platformProfileLogFields(options.profile, nomenclature),
          }, options.profile, permittedObservations());
        }

        phase = "profile-projection";
        if (platformProfileAllowsSignal(options.profile, "metric")) {
          phase = "metric-projection";
          recordPlatformMetric(options.metrics, options.clock, {
            name: `${message}.outcome`,
            labels: platformProfileMetricLabels(options.profile, nomenclature),
          }, platformProfileAllowsSignal(options.profile, "operational_log") ? { binding: metricDiagnostics, operation: "persistence-transition" } : undefined, permittedObservations());
        }

        phase = "profile-projection";
        if (platformProfileAllowsSignal(options.profile, "trace")) {
          phase = "trace-projection";
          const span = startPlatformTraceSpan(options.tracer ?? noopTracer, {
            name: message,
            ...(observation.traceParent === undefined ? {} : { parent: observation.traceParent }),
            attributes: platformProfileTraceFields(options.profile, nomenclature),
          }, options.profile, (traceHelperEntered = true, permittedObservations()));
          traceHelperEntered = false;
          endPlatformTraceSpan(span, {
            outcome: traceOutcome(observation.outcome),
            attributes: platformProfileTraceFields(options.profile, nomenclature),
          }, options.profile, permittedObservations());
        }
        } catch (error) {
          const reporting = permittedObservations();
          if (!traceHelperEntered) reportPlatformObservationBoundary(reporting,
            { operation: "persistence-observation", phase, reason: "threw", effect: "observation-incomplete" }, error);
          else reportPlatformObservationSources(reporting, error); // The trace helper already owns its escaping fallback boundary.
          // Never reread an error accessor merely to salvage the original selected evidence.
          try {
            const source = Object.getOwnPropertyDescriptor(observation, "error");
            if (source !== undefined && "value" in source && source.value !== error) reportPlatformObservationSources(reporting, source.value);
          } catch { /* The independent observation below remains selectable. */ }
          reportPlatformObservationSources(reporting, observation);
          throw error;
        }
      },
    },
  };
}

/** Compare validated plain catalogue data without making object-key order policy. */
function canonicalCatalog(catalog: PlatformDiagnosticCatalog): string {
  return JSON.stringify(catalog, (_key, value: unknown) => typeof value === "object" && value !== null && !Array.isArray(value)
    ? Object.fromEntries(Object.keys(value).sort().map((key) => [key, (value as Record<string, unknown>)[key]])) : value);
}

function persistenceNomenclature(
  options: PlatformPersistenceTransitionObserverOptions,
  observation: PlatformPersistenceObservation,
  beforeErrorClass?: () => void,
): import("@kanbien/platform-contracts").PlatformOperationalNomenclature {
  return {
    capability: options.profile.capability,
    action: options.profile.action,
    executionContext: options.executionContext,
    outcome: observation.outcome,
    ...((beforeErrorClass?.(), observation.error) === undefined ? {} : { errorClass: platformErrorClass(observation.error, options.profile) }),
  };
}

function persistenceLogLevel(outcome: PlatformPersistenceObservation["outcome"]): "info" | "warn" | "error" {
  if (outcome === "succeeded") {
    return "info";
  }

  if (outcome === "rejected") {
    return "warn";
  }

  return "error";
}

function traceOutcome(outcome: PlatformPersistenceObservation["outcome"]): "succeeded" | "rejected" | "failed" {
  return outcome;
}
