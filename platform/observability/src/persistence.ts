import type { Logger } from "@kanbien/core/logging"; // Receive the existing provider-neutral structured logging port.
import { noopTracer, type Metrics, type Tracer } from "@kanbien/core/monitoring"; // Reuse Core telemetry ports without selecting a provider.
import type { Clock, Result } from "@kanbien/core/shared"; // Reuse the deterministic clock and explicit-result primitives.
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
} from "@kanbien/platform-contracts"; // Apply the same reviewed profile and safe-field policy already used by servers and workers.
import type {
  PlatformPersistenceObservation,
  PlatformPersistenceObserver,
} from "@kanbien/platform-persistence"; // Adapt the persistence-owned no-payload transition port without taking ownership of persistence state.
import { writePlatformLog } from "./logging"; // Deliver profile-projected structured records through the existing safe logger helper.
import { platformErrorClass } from "./normalization"; // Reduce errors to bounded stable classifications before telemetry emission.
import { recordPlatformMetric } from "./metrics"; // Emit provider-neutral aggregate points through the existing metrics helper.
import { endPlatformTraceSpan, startPlatformTraceSpan } from "./tracing"; // Emit optional profile-governed diagnostic spans without exposing provider SDKs.

const platformPersistenceTransitionFieldNames = [ // Declare the small fixed safe-field policy for reusable persistence transition profiles.
  "capability", // State which stable capability selected the persistence action.
  "action", // State the controlled capability verb, normally `execute` for coordination work.
  "execution_context", // State where the relay or worker transition ran.
  "outcome", // State the bounded transition outcome.
  "error_class", // State only a bounded error classification when a transition failed.
] as const; // Preserve literals so the returned profile remains fully typed and reviewable.

export interface PlatformPersistenceTransitionObserverOptions { // Describe target composition inputs for profile-governed persistence transition evidence.
  readonly profile: PlatformCapabilityObservabilityProfile; // Supply the registered or otherwise reviewed capability profile that permits these signals.
  readonly executionContext: PlatformExecutionContext; // State whether the selected relay or processing operation runs as a worker, scheduler, CLI, or server.
  readonly logger: Logger; // Receive the selected structured logging port.
  readonly metrics: Metrics; // Receive the selected aggregate metrics port.
  readonly tracer?: Tracer; // Optionally receive the selected tracing port; no tracer selects a safe no-op tracer.
  readonly clock: Clock; // Receive the selected clock so metrics remain deterministic in tests.
}

export function platformPersistenceTransitionProfile(input: { // Construct the standard safe profile shape that an app may register for one persistence capability.
  readonly name: PlatformCapabilityObservabilityProfile["name"]; // Preserve the caller-owned, checked profile registry identity.
  readonly capability: PlatformCapabilityName; // Preserve the caller-owned stable capability identity.
  readonly action?: PlatformCapabilityAction; // Allow a caller to use a more precise controlled verb when `execute` is not truthful.
}): PlatformCapabilityObservabilityProfile { // Return a declaration suitable for ordinary runtime registry validation.
  return {
    name: input.name, // Retain the checked profile identity chosen by the owning app.
    capability: input.capability, // Retain the checked capability identity chosen by the owning app.
    action: input.action ?? "execute", // Use `execute` as the truthful default for coordination work.
    signals: ["operational_log", "metric", "trace"], // Permit all three ordinary operational signal families for the explicitly selected profile.
    logFieldNames: platformPersistenceTransitionFieldNames, // Allow only the standard bounded facts in persistence transition logs.
    metricDimensionFieldNames: platformPersistenceTransitionFieldNames, // Allow only the same bounded facts as low-cardinality metric labels.
    traceAttributeNames: platformPersistenceTransitionFieldNames, // Allow only the same bounded facts as trace attributes.
  };
}

export function createPlatformPersistenceTransitionObserver( // Build a provider-neutral observer that translates persistence transitions through one reviewed profile.
  options: PlatformPersistenceTransitionObserverOptions, // Receive target-selected dependencies and the profile that governs their use.
): Result<PlatformPersistenceObserver, import("@kanbien/platform-contracts").PlatformContractError> { // Return an explicit error when an untrusted profile cannot safely govern telemetry.
  const validation = validatePlatformCapabilityObservabilityProfile(options.profile); // Validate the full signal and field allowlist before any persistence operation begins.
  if (!validation.ok) { // Reject malformed or incoherent profile input.
    return validation; // Preserve the established platform-contract error for the composition root to handle.
  }

  return { // Return the narrow persistence observer after profile validation succeeds.
    ok: true, // Mark the composition result as valid.
    value: {
      record(observation) { // Translate one already safe persistence transition request.
        const nomenclature = persistenceNomenclature(options, observation); // Build only the controlled fields understood by profile projection.
        const message = `platform.persistence.${observation.transition}`; // Use a fixed transition-derived event name rather than an arbitrary log message.

        if (platformProfileAllowsSignal(options.profile, "operational_log")) { // Emit a structured log only when the profile expressly permits it.
          writePlatformLog(options.logger, { // Reuse safe normalisation and best-effort logging behaviour.
            level: persistenceLogLevel(observation.outcome), // Map the bounded transition outcome to one bounded log level.
            message, // Preserve the static event name for operator search and alert rules.
            ...(observation.correlationId === undefined ? {} : { correlationId: observation.correlationId }), // Carry correlation only in the log envelope and only when supplied by the caller.
            fields: platformProfileLogFields(options.profile, nomenclature), // Project exactly the profile-allowlisted scalar facts.
          }); // Finish the safe log request.
        }

        if (platformProfileAllowsSignal(options.profile, "metric")) { // Emit an aggregate point only when the profile expressly permits it.
          recordPlatformMetric(options.metrics, options.clock, { // Reuse the best-effort provider-neutral metrics helper.
            name: `${message}.outcome`, // Give every closed transition its own stable metric series rather than using a high-cardinality transition label.
            labels: platformProfileMetricLabels(options.profile, nomenclature), // Project only bounded profile-approved metric dimensions.
          }); // Finish the safe metric request.
        }

        if (platformProfileAllowsSignal(options.profile, "trace")) { // Emit a short diagnostic span only when the profile expressly permits it.
          const span = startPlatformTraceSpan(options.tracer ?? noopTracer, { // Start a child span when the transition supplied existing trace continuity.
            name: message, // Use the same stable name as the log event and metric series root.
            ...(observation.traceParent === undefined ? {} : { parent: observation.traceParent }), // Keep causal traces connected without promoting trace IDs to labels.
            attributes: platformProfileTraceFields(options.profile, nomenclature), // Project only profile-approved trace attributes.
          }); // Finish the best-effort trace start.
          endPlatformTraceSpan(span, { // End the zero-work transition span with the same bounded outcome facts.
            outcome: traceOutcome(observation.outcome), // Translate persistence outcome into the Core tracing outcome vocabulary.
            attributes: platformProfileTraceFields(options.profile, nomenclature), // Preserve the same safe attributes at span completion.
          }); // Finish the best-effort trace end.
        }
      },
    },
  };
}

function persistenceNomenclature( // Convert a persistence-local transition event into the shared profile projection vocabulary.
  options: PlatformPersistenceTransitionObserverOptions, // Read the profile and execution context selected by composition.
  observation: PlatformPersistenceObservation, // Read one bounded persistence transition event.
): import("@kanbien/platform-contracts").PlatformOperationalNomenclature { // Return only shared controlled operational terms.
  return {
    capability: options.profile.capability, // Carry the stable capability identity approved by the profile.
    action: options.profile.action, // Carry the controlled action approved by the profile.
    executionContext: options.executionContext, // Carry the target-selected execution location.
    outcome: observation.outcome, // Reuse the shared compatible outcome literal.
    ...(observation.error === undefined ? {} : { errorClass: platformErrorClass(observation.error) }), // Emit only a normalised stable error class when a failure was supplied.
  };
}

function persistenceLogLevel(outcome: PlatformPersistenceObservation["outcome"]): "info" | "warn" | "error" { // Map one controlled transition outcome to a deliberate operational severity.
  if (outcome === "succeeded") { // Treat a completed persistence transition as routine evidence.
    return "info"; // Keep successful transition records searchable without implying an incident.
  }

  if (outcome === "rejected") { // Treat a contention or validation rejection as a warning-worthy condition.
    return "warn"; // Avoid calling a controlled rejection an unhandled platform error.
  }

  return "error"; // Treat a failed durable transition as error evidence.
}

function traceOutcome(outcome: PlatformPersistenceObservation["outcome"]): "succeeded" | "rejected" | "failed" { // Translate the compatible persistence outcome union into the Core trace-end union.
  return outcome; // The persistence observer deliberately uses the same three literal values.
}
