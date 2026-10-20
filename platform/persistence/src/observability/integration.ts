import type { Logger } from "@kanbien/core/logging";
import { noopTracer, type Metrics, type Tracer } from "@kanbien/core/monitoring";
import type { Clock, Result } from "@kanbien/core/shared";
import {
  platformProfileAllowsSignal,
  platformProfileLogFields,
  platformProfileMetricLabels,
  platformProfileTraceFields,
  validatePlatformCapabilityObservabilityProfile,
  type PlatformCapabilityAction,
  type PlatformCapabilityName,
  type PlatformCapabilityObservabilityProfile,
  type PlatformExecutionContext,
} from "@kanbien/platform-contracts";
import {
  endPlatformTraceSpan,
  platformErrorClass,
  recordPlatformMetric,
  startPlatformTraceSpan,
  writePlatformLog,
} from "@kanbien/platform-observability";
import type { PlatformPersistenceObservation, PlatformPersistenceObserver } from "./port";

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

  return {
    ok: true,
    value: {
      record(observation) {
        const nomenclature = persistenceNomenclature(options, observation);
        const message = `platform.persistence.${observation.transition}`;

        if (platformProfileAllowsSignal(options.profile, "operational_log")) {
          writePlatformLog(options.logger, {
            level: persistenceLogLevel(observation.outcome),
            message,
            ...(observation.correlationId === undefined ? {} : { correlationId: observation.correlationId }),
            fields: platformProfileLogFields(options.profile, nomenclature),
          });
        }

        if (platformProfileAllowsSignal(options.profile, "metric")) {
          recordPlatformMetric(options.metrics, options.clock, {
            name: `${message}.outcome`,
            labels: platformProfileMetricLabels(options.profile, nomenclature),
          });
        }

        if (platformProfileAllowsSignal(options.profile, "trace")) {
          const span = startPlatformTraceSpan(options.tracer ?? noopTracer, {
            name: message,
            ...(observation.traceParent === undefined ? {} : { parent: observation.traceParent }),
            attributes: platformProfileTraceFields(options.profile, nomenclature),
          });
          endPlatformTraceSpan(span, {
            outcome: traceOutcome(observation.outcome),
            attributes: platformProfileTraceFields(options.profile, nomenclature),
          });
        }
      },
    },
  };
}

function persistenceNomenclature(
  options: PlatformPersistenceTransitionObserverOptions,
  observation: PlatformPersistenceObservation,
): import("@kanbien/platform-contracts").PlatformOperationalNomenclature {
  return {
    capability: options.profile.capability,
    action: options.profile.action,
    executionContext: options.executionContext,
    outcome: observation.outcome,
    ...(observation.error === undefined ? {} : { errorClass: platformErrorClass(observation.error) }),
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
