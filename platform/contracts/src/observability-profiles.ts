import type { Brand, Result } from "@kanbien/core/shared"; // Reuse the shared branded-name and explicit-result primitives.
import { // Import only contract-level errors because this declaration must not choose a runtime provider.
  malformedPlatformObservabilityProfile, // Describe a malformed profile without throwing during app registration.
  type PlatformContractError, // Preserve the platform-wide stable contract-error type.
} from "./errors"; // Keep error ownership in the dedicated errors topic.
import { // Reuse the checked dotted-name rule that already governs app, route, and job names.
  brandedPlatformContractName, // Brand a validated profile name instead of accepting an ordinary string.
  isPlatformContractName, // Defensively validate names supplied through untyped runtime boundaries.
} from "./identifiers"; // Keep identifier policy in its focused source topic.
import { // Reuse the controlled operational vocabulary rather than creating parallel strings for profiles.
  isPlatformCapabilityAction, // Validate one declared business action.
  isPlatformOperationalFieldName, // Validate one canonical emitted field name.
  type PlatformCapabilityAction, // Describe a reviewed business action.
  type PlatformCapabilityName, // Describe a checked stable capability identity.
  type PlatformOperationalFieldName, // Describe a canonical safe observability fact name.
} from "./observability"; // Keep vocabulary ownership separate from profile ownership.

export const platformObservabilitySignalKinds = [ // Declare the provider-neutral operational signal families a profile may permit.
  "operational_log", // Permit structured short-retention diagnostic records.
  "metric", // Permit aggregate low-cardinality measurements.
  "trace", // Permit timed diagnostic spans and safe attributes.
] as const; // Preserve literal values so TypeScript forms a closed union.

export type PlatformObservabilitySignalKind = (typeof platformObservabilitySignalKinds)[number]; // Represent one permitted operational signal family.

export const platformNfrClasses = [ // Declare the named workload classes whose target values remain central policy rather than feature-local literals.
  "interactive_read", // A user-facing retrieval path where responsiveness is the primary concern.
  "interactive_command", // A user-facing state-changing request where acknowledgement matters.
  "async_acceptance", // A quick request-path acknowledgement that durable background work was accepted.
  "async_completion", // Background work whose meaningful completion is measured separately from acceptance.
  "async_queue_delay", // Time spent waiting for worker capacity before background work begins.
  "health_probe", // A liveness, readiness, or dependency-health check.
] as const; // Preserve literal values so TypeScript forms a closed NFR-class union.

export type PlatformNfrClass = (typeof platformNfrClasses)[number]; // Represent a named central NFR-policy class without embedding thresholds.

export const platformLatencyMeasurements = [ // Declare the distinct latency intervals that a future metrics adapter may observe.
  "request_response_latency", // Measure server receipt through response completion.
  "job_execution_latency", // Measure worker start through job-handler completion.
  "queue_wait_latency", // Measure enqueue through worker handling start.
  "end_to_end_completion_latency", // Measure an accepted operation through its declared final outcome.
  "health_check_latency", // Measure a health check start through its result.
] as const; // Preserve literal values so TypeScript forms a closed measurement union.

export type PlatformLatencyMeasurement = (typeof platformLatencyMeasurements)[number]; // Represent one meaningful latency interval rather than an ambiguous generic duration.

export const platformMetricDimensionFieldNames = [ // Declare canonical operational fields that remain bounded enough for aggregate metric dimensions.
  "capability", // Group aggregates by stable capability rather than raw URL or resource identifier.
  "action", // Group aggregates by controlled business action.
  "actor_type", // Group aggregates by a small accountable-actor category.
  "interaction_source", // Group aggregates by a bounded initiation channel.
  "execution_context", // Group aggregates by server, worker, scheduler, or CLI execution.
  "http_method", // Group server aggregates by a bounded transport method when useful.
  "http_status_code", // Group server aggregates by numeric HTTP outcome without a free-form status field.
  "job_delivery_disposition", // Group worker aggregates by retry, success, or dead-letter decision.
  "outcome", // Group aggregates by the controlled logical outcome.
  "error_class", // Group aggregates by a stable bounded error classification, never an error message.
] as const satisfies readonly PlatformOperationalFieldName[]; // Prove every permitted metric dimension is a canonical emitted operational field.

export type PlatformMetricDimensionFieldName = (typeof platformMetricDimensionFieldNames)[number]; // Represent one reviewed low-cardinality metric dimension.

export const platformObservabilityOptOutReasons = [ // Declare the limited reasons a route or job may deliberately avoid a profile.
  "covered_by_parent_capability", // The registered parent capability emits the only meaningful operational evidence.
  "externally_observed", // An approved external boundary owns the operational evidence for this thin adapter path.
  "non_user_workload_path", // The registration exists for platform mechanics rather than a user or workload capability.
] as const; // Preserve literal values so TypeScript forms a closed opt-out-reason union.

export type PlatformObservabilityOptOutReason = (typeof platformObservabilityOptOutReasons)[number]; // Represent one reviewed reason instead of a free-form opt-out category.

export type PlatformObservabilityProfileName = Brand<string, "PlatformObservabilityProfileName">; // Keep a profile identity distinct from the capability it describes.

export interface PlatformNfrObjectiveReference { // Reference one central NFR class and the exact interval that it measures.
  readonly nfrClass: PlatformNfrClass; // Select the named policy class without putting thresholds in an app declaration.
  readonly measurement: PlatformLatencyMeasurement; // Name the start and finish points that future telemetry must use.
}

export interface PlatformCapabilityObservabilityProfile { // Declare the provider-neutral operational evidence permitted for one app-owned capability.
  readonly name: PlatformObservabilityProfileName; // Give the profile a stable app-namespaced registry identity.
  readonly capability: PlatformCapabilityName; // Identify the business capability rather than a transport route or provider operation.
  readonly action: PlatformCapabilityAction; // Identify the controlled business action performed by that capability.
  readonly signals: readonly PlatformObservabilitySignalKind[]; // Declare which operational signal families the capability may emit.
  readonly logFieldNames?: readonly PlatformOperationalFieldName[]; // Allowlist canonical safe facts for ordinary operational logs.
  readonly metricDimensionFieldNames?: readonly PlatformMetricDimensionFieldName[]; // Allowlist bounded dimensions for aggregate metrics.
  readonly traceAttributeNames?: readonly PlatformOperationalFieldName[]; // Allowlist canonical safe facts for diagnostic trace attributes.
  readonly nfrObjectives?: readonly PlatformNfrObjectiveReference[]; // Reference central NFR classes without embedding provider, threshold, alert, or retention policy.
}

export type PlatformObservabilityRequirement = // Require every route and job to select a profile or explain a deliberately narrow exception.
  | { // Describe the ordinary case where a capability profile governs the registration.
      readonly kind: "profile"; // Identify this requirement as a profile reference.
      readonly profile: PlatformObservabilityProfileName; // Reference a profile that the mounting app registered.
    }
  | { // Describe an exception that the complete registry can preserve and review.
      readonly kind: "opt_out"; // Identify this requirement as an explicit opt-out rather than an omitted field.
      readonly reason: PlatformObservabilityOptOutReason; // Use a controlled reason category.
      readonly justification: string; // Supply a concise human-reviewable explanation for this individual registration.
    };

export function platformObservabilityProfileName(value: string): Result<PlatformObservabilityProfileName, PlatformContractError> { // Validate and brand one profile registry identity.
  return brandedPlatformContractName(value, "PlatformObservabilityProfileName", "platform observability profile name") as Result<PlatformObservabilityProfileName, PlatformContractError>; // Reuse the established dotted-name rule while preserving a distinct type.
}

export function validatePlatformCapabilityObservabilityProfile( // Validate untrusted or dynamically assembled profile declarations before registry acceptance.
  profile: PlatformCapabilityObservabilityProfile, // Accept the declared profile whose safe operational surface must be checked.
): Result<void, PlatformContractError> { // Return an explicit contract result rather than throwing during mounting.
  if (!isRecord(profile)) { // Reject absent, primitive, or malformed profile declarations.
    return profileFailure("Observability profiles must be objects."); // Explain the first structural defect without exposing data.
  }

  if (!isPlatformContractName(profile.name)) { // Require a checked dotted profile name at runtime as well as compile time.
    return profileFailure("Observability profile names must use dot-separated lowercase segments."); // Keep registry keys semantically scanable.
  }

  if (!isPlatformContractName(profile.capability)) { // Require a stable checked capability identity rather than a free-form label.
    return profileFailure("Observability profile capabilities must use dot-separated lowercase segments."); // Keep capability grouping stable across signals.
  }

  if (!isPlatformCapabilityAction(profile.action)) { // Reject an unreviewed verb such as an ad-hoc synonym.
    return profileFailure("Observability profiles must use a controlled capability action."); // Preserve the shared action vocabulary.
  }

  if (!isNonEmptyUniqueArray(profile.signals, isPlatformObservabilitySignalKind)) { // Require at least one distinct signal family.
    return profileFailure("Observability profiles must declare one or more distinct signal kinds."); // Prevent a meaningless empty profile or duplicate declarations.
  }

  if (!validateFieldNames(profile.logFieldNames, isPlatformOperationalFieldName)) { // Check optional log allowlists against the canonical operational field vocabulary.
    return profileFailure("Observability profile log fields must be distinct canonical operational field names."); // Prevent arbitrary log-field declarations.
  }

  if (!validateFieldNames(profile.metricDimensionFieldNames, isPlatformMetricDimensionFieldName)) { // Check optional metric dimensions against the stricter low-cardinality allowlist.
    return profileFailure("Observability profile metric dimensions must be distinct approved metric field names."); // Prevent tenant, user, raw path, and other unsafe dimensions.
  }

  if (!validateFieldNames(profile.traceAttributeNames, isPlatformOperationalFieldName)) { // Check optional trace attribute allowlists against the canonical operational field vocabulary.
    return profileFailure("Observability profile trace attributes must be distinct canonical operational field names."); // Prevent arbitrary trace payload declarations.
  }

  if (!validateNfrObjectives(profile.nfrObjectives)) { // Check every declared NFR class and latency interval together.
    return profileFailure("Observability profile NFR objectives must use distinct compatible central classes and latency measurements."); // Prevent an app from declaring an incoherent target reference.
  }

  if ((profile.metricDimensionFieldNames !== undefined || profile.nfrObjectives !== undefined) && !profile.signals.includes("metric")) { // Require metric intent before declaring metric dimensions or latency objectives.
    return profileFailure("Metric dimensions and NFR objectives require the metric signal kind."); // Keep declared measurement intent internally coherent.
  }

  if (profile.logFieldNames !== undefined && !profile.signals.includes("operational_log")) { // Require log intent before declaring log fields.
    return profileFailure("Log fields require the operational_log signal kind."); // Keep declared log intent internally coherent.
  }

  if (profile.traceAttributeNames !== undefined && !profile.signals.includes("trace")) { // Require trace intent before declaring trace fields.
    return profileFailure("Trace attributes require the trace signal kind."); // Keep declared trace intent internally coherent.
  }

  return { ok: true, value: undefined }; // Accept the fully coherent provider-neutral declaration.
}

export function isPlatformObservabilityRequirement(value: unknown): value is PlatformObservabilityRequirement { // Validate a route or job's profile reference or explicit opt-out.
  if (!isRecord(value)) { // Reject missing or primitive requirements.
    return false; // Report invalid shape to the route or job validator.
  }

  if (value.kind === "profile") { // Validate the ordinary profile-reference form.
    return isPlatformContractName(value.profile); // Require a checked-looking profile identity before complete-registry resolution.
  }

  return value.kind === "opt_out" // Accept only the explicit opt-out form.
    && isPlatformObservabilityOptOutReason(value.reason) // Require a controlled exception reason.
    && typeof value.justification === "string" // Require a human-reviewable justification.
    && value.justification.trim().length > 0 // Reject empty or whitespace-only explanations.
    && value.justification.length <= 280; // Bound the declaration so it cannot become a hidden payload channel.
}

export function isPlatformObservabilitySignalKind(value: unknown): value is PlatformObservabilitySignalKind { // Check an untyped signal-family value against the controlled vocabulary.
  return isOneOf(value, platformObservabilitySignalKinds); // Reuse the local literal-array membership helper.
}

export function isPlatformNfrClass(value: unknown): value is PlatformNfrClass { // Check an untyped NFR-class value against the central-policy references.
  return isOneOf(value, platformNfrClasses); // Reuse the local literal-array membership helper.
}

export function isPlatformLatencyMeasurement(value: unknown): value is PlatformLatencyMeasurement { // Check an untyped latency interval against the explicit measurement vocabulary.
  return isOneOf(value, platformLatencyMeasurements); // Reuse the local literal-array membership helper.
}

export function isPlatformMetricDimensionFieldName(value: unknown): value is PlatformMetricDimensionFieldName { // Check an untyped metric dimension against the low-cardinality allowlist.
  return isOneOf(value, platformMetricDimensionFieldNames); // Reuse the local literal-array membership helper.
}

export function isPlatformObservabilityOptOutReason(value: unknown): value is PlatformObservabilityOptOutReason { // Check an untyped opt-out reason against the narrow controlled vocabulary.
  return isOneOf(value, platformObservabilityOptOutReasons); // Reuse the local literal-array membership helper.
}

function validateNfrObjectives(value: unknown): value is readonly PlatformNfrObjectiveReference[] | undefined { // Validate optional NFR objective references and their class-to-measurement compatibility.
  if (value === undefined) { // Allow capabilities with useful telemetry but no latency objective.
    return true; // Accept the absent optional declaration.
  }

  if (!Array.isArray(value) || value.length === 0) { // Reject an empty array because absence expresses “none” more clearly.
    return false; // Require each present declaration to mean something.
  }

  const seenObjectives = new Set<string>(); // Track pairs so a profile cannot declare the same objective twice.
  for (const objective of value) { // Inspect every declared class and interval pair.
    if (!isRecord(objective) || !isPlatformNfrClass(objective.nfrClass) || !isPlatformLatencyMeasurement(objective.measurement)) { // Reject malformed or unreviewed pairs.
      return false; // Stop at the first invalid objective.
    }

    const compatibleMeasurements: readonly PlatformLatencyMeasurement[] = platformNfrClassMeasurements[objective.nfrClass]; // Widen one class-specific tuple to the common measurement union for safe membership checking.
    if (!compatibleMeasurements.includes(objective.measurement)) { // Reject a class paired with a nonsensical interval.
      return false; // Keep acceptance, completion, queue, and health timing distinct.
    }

    const objectiveKey = `${objective.nfrClass}:${objective.measurement}`; // Form a stable duplicate-detection key from two bounded values.
    if (seenObjectives.has(objectiveKey)) { // Reject duplicate declarations that add no semantic information.
      return false; // Keep the profile easy to review.
    }

    seenObjectives.add(objectiveKey); // Remember the accepted pair before checking the next one.
  }

  return true; // Accept the complete unique compatible objective list.
}

function validateFieldNames<TFieldName extends string>(value: unknown, isFieldName: (candidate: unknown) => candidate is TFieldName): value is readonly TFieldName[] | undefined { // Validate an optional non-empty unique allowlist against a supplied field guard.
  if (value === undefined) { // Allow a signal family to use no optional canonical fields.
    return true; // Treat absence as a valid minimal declaration.
  }

  return isNonEmptyUniqueArray(value, isFieldName); // Require a present allowlist to contain distinct reviewed fields.
}

function isNonEmptyUniqueArray<TValue extends string>(value: unknown, isValue: (candidate: unknown) => candidate is TValue): value is readonly TValue[] { // Check a literal array for non-emptiness, membership, and duplicates.
  return Array.isArray(value) // Require an actual array.
    && value.length > 0 // Reject meaningless empty declarations.
    && value.every(isValue) // Require each item to be in the caller's controlled vocabulary.
    && new Set(value).size === value.length; // Reject duplicate items that make review harder.
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> { // Narrow an unknown runtime value to a non-null object record.
  return typeof value === "object" && value !== null; // Reject primitives and null.
}

function isOneOf<TValue extends string>(value: unknown, values: readonly TValue[]): value is TValue { // Compare an unknown string with one controlled literal vocabulary.
  return typeof value === "string" && values.includes(value as TValue); // Accept only exact known values.
}

function profileFailure(reason: string): Result<void, PlatformContractError> { // Construct one stable profile-validation failure result.
  return { ok: false, error: malformedPlatformObservabilityProfile(reason) }; // Preserve the contract error rather than exposing implementation details.
}

const platformNfrClassMeasurements = { // Map each NFR class to the latency intervals that have truthful start and finish points for it.
  interactive_read: ["request_response_latency"], // Reads complete on the request path.
  interactive_command: ["request_response_latency"], // Interactive commands acknowledge their completed request-path work.
  async_acceptance: ["request_response_latency"], // Async acceptance is measured before background completion starts.
  async_completion: ["job_execution_latency", "end_to_end_completion_latency"], // Async completion may need worker-only and whole-workflow timing.
  async_queue_delay: ["queue_wait_latency"], // Queue delay measures waiting before execution.
  health_probe: ["health_check_latency"], // Health checks have their own short execution interval.
} as const satisfies Readonly<Record<PlatformNfrClass, readonly PlatformLatencyMeasurement[]>>; // Keep mapping complete whenever an NFR class changes.
