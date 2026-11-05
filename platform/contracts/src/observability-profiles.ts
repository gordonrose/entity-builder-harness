import { withPlatformContractDiagnostic, type PlatformContractDiagnosticField, type PlatformContractDiagnosticCondition, type PlatformContractObserver } from "./registration-diagnostics";
import { platformContractClassificationDiagnosticRecord } from "./registration-diagnostics";
import { inspectPlatformErrorClassDeclaration, platformOptionalErrorClassification, type PlatformErrorClassificationOptions } from "./observability";
import type { MetricLabelValue } from "@kanbien/core/monitoring"; // Reuse the Core scalar metric-label type without choosing a metrics provider.
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
  type PlatformOperationalNomenclature, // Project only typed operational facts through one profile's allowlists.
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

export interface PlatformCapabilityObservabilityProfile extends PlatformErrorClassificationOptions { // Declare the provider-neutral operational evidence permitted for one app-owned capability.
  readonly name: PlatformObservabilityProfileName; // Give the profile a stable app-namespaced registry identity.
  readonly capability: PlatformCapabilityName; // Identify the business capability rather than a transport route or provider operation.
  readonly action: PlatformCapabilityAction; // Identify the controlled business action performed by that capability.
  readonly signals: readonly PlatformObservabilitySignalKind[]; // Declare which operational signal families the capability may emit.
  readonly logFieldNames?: readonly PlatformOperationalFieldName[]; // Allowlist canonical safe facts for ordinary operational logs.
  readonly metricDimensionFieldNames?: readonly PlatformMetricDimensionFieldName[]; // Allowlist bounded dimensions for aggregate metrics.
  readonly traceAttributeNames?: readonly PlatformOperationalFieldName[]; // Allowlist canonical safe facts for diagnostic trace attributes.
  readonly nfrObjectives?: readonly PlatformNfrObjectiveReference[]; // Reference central NFR classes without embedding provider, threshold, alert, or retention policy.
}

export type PlatformProfileObservationFields = Readonly<{ // Describe the correctly typed canonical facts that survive one profile allowlist.
  readonly capability?: PlatformOperationalNomenclature["capability"]; // Preserve a stable checked capability name when the profile permits it.
  readonly action?: PlatformOperationalNomenclature["action"]; // Preserve a controlled business action when the profile permits it.
  readonly actor_type?: Exclude<PlatformOperationalNomenclature["actorType"], undefined>; // Preserve a bounded actor category when supplied and permitted.
  readonly interaction_source?: Exclude<PlatformOperationalNomenclature["interactionSource"], undefined>; // Preserve a bounded initiation channel when supplied and permitted.
  readonly execution_context?: PlatformOperationalNomenclature["executionContext"]; // Preserve a controlled runtime location when the profile permits it.
  readonly http_method?: Exclude<PlatformOperationalNomenclature["httpMethod"], undefined>; // Preserve a bounded HTTP method when supplied and permitted.
  readonly http_status_code?: Exclude<PlatformOperationalNomenclature["httpStatusCode"], undefined>; // Preserve a numeric HTTP result when supplied and permitted.
  readonly job_delivery_disposition?: Exclude<PlatformOperationalNomenclature["jobDeliveryDisposition"], undefined>; // Preserve a controlled delivery decision when supplied and permitted.
  readonly outcome?: PlatformOperationalNomenclature["outcome"]; // Preserve the logical result when the profile permits it.
  readonly error_class?: Exclude<PlatformOperationalNomenclature["errorClass"], undefined>; // Preserve only a bounded error classification when supplied and permitted.
}>; // Prevent payloads, objects, identifiers, and unbounded values from passing this declaration boundary.

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
  let field: PlatformContractDiagnosticField = "declaration";
  let condition: PlatformContractDiagnosticCondition = "object-required";
  const select = (location: PlatformContractDiagnosticField, fallback: PlatformContractDiagnosticCondition): void => { field = location; condition = fallback; };
  const failure = (reason: string): Result<void, PlatformContractError> => ({ ok: false, error: withPlatformContractDiagnostic(malformedPlatformObservabilityProfile(reason), "observability-profile", field, condition) });
  if (!isRecord(profile)) { // Reject absent, primitive, or malformed profile declarations.
    return failure("Observability profiles must be objects."); // Explain the first structural defect without exposing data.
  }

  if (!(select("name", "invalid-format"), isPlatformContractName(profile.name, (value) => { condition = value; }))) { // Require a checked dotted profile name at runtime as well as compile time.
    return failure("Observability profile names must use dot-separated lowercase segments."); // Keep registry keys semantically scanable.
  }

  if (!(select("capability", "invalid-format"), isPlatformContractName(profile.capability, (value) => { condition = value; }))) { // Require a stable checked capability identity rather than a free-form label.
    return failure("Observability profile capabilities must use dot-separated lowercase segments."); // Keep capability grouping stable across signals.
  }

  if (!(select("action", "unsupported"), isPlatformCapabilityAction(profile.action))) { // Reject an unreviewed verb such as an ad-hoc synonym.
    return failure("Observability profiles must use a controlled capability action."); // Preserve the shared action vocabulary.
  }

  if (!(select("signals", "declaration-rejected"), isNonEmptyUniqueArray(profile.signals, isPlatformObservabilitySignalKind, (value) => { condition = value.condition; }))) { // Require at least one distinct signal family.
    return failure("Observability profiles must declare one or more distinct signal kinds."); // Prevent a meaningless empty profile or duplicate declarations.
  }

  if (!(select("logFieldNames", "declaration-rejected"), validateFieldNames(profile.logFieldNames, isPlatformOperationalFieldName, (value) => { condition = value.condition; }))) { // Check optional log allowlists against the canonical operational field vocabulary.
    return failure("Observability profile log fields must be distinct canonical operational field names."); // Prevent arbitrary log-field declarations.
  }

  if (!(select("metricDimensionFieldNames", "declaration-rejected"), validateFieldNames(profile.metricDimensionFieldNames, isPlatformMetricDimensionFieldName, (value) => { condition = value.condition; }))) { // Check optional metric dimensions against the stricter low-cardinality allowlist.
    return failure("Observability profile metric dimensions must be distinct approved metric field names."); // Prevent tenant, user, raw path, and other unsafe dimensions.
  }

  if (!(select("traceAttributeNames", "declaration-rejected"), validateFieldNames(profile.traceAttributeNames, isPlatformOperationalFieldName, (value) => { condition = value.condition; }))) { // Check optional trace attribute allowlists against the canonical operational field vocabulary.
    return failure("Observability profile trace attributes must be distinct canonical operational field names."); // Prevent arbitrary trace payload declarations.
  }

  if (!(select("nfrObjectives", "declaration-rejected"), validateNfrObjectives(profile.nfrObjectives, (value) => { field = value.field; condition = value.condition; }))) { // Check every declared NFR class and latency interval together.
    return failure("Observability profile NFR objectives must use distinct compatible central classes and latency measurements."); // Prevent an app from declaring an incoherent target reference.
  }

  if ((profile.metricDimensionFieldNames !== undefined || profile.nfrObjectives !== undefined) && !profile.signals.includes("metric")) { // Require metric intent before declaring metric dimensions or latency objectives.
    field = "signals"; condition = "signal-required";
    return failure("Metric dimensions and NFR objectives require the metric signal kind."); // Keep declared measurement intent internally coherent.
  }

  if (profile.logFieldNames !== undefined && !profile.signals.includes("operational_log")) { // Require log intent before declaring log fields.
    field = "logFieldNames"; condition = "signal-required";
    return failure("Log fields require the operational_log signal kind."); // Keep declared log intent internally coherent.
  }

  if (profile.traceAttributeNames !== undefined && !profile.signals.includes("trace")) { // Require trace intent before declaring trace fields.
    field = "traceAttributeNames"; condition = "signal-required";
    return failure("Trace attributes require the trace signal kind."); // Keep declared trace intent internally coherent.
  }

  const classesIssue = inspectPlatformErrorClassDeclaration(profile).issue;
  if (classesIssue !== undefined) return { ok: false, error: { ...malformedPlatformObservabilityProfile("Observability profile error classes must be distinct bounded data declarations."),
    diagnosticRecord: platformContractClassificationDiagnosticRecord(classesIssue) } };
  return { ok: true, value: undefined }; // Accept the fully coherent provider-neutral declaration.
}

export function isPlatformObservabilityRequirement(value: unknown, observer?: PlatformContractObserver): value is PlatformObservabilityRequirement {
  if (!isRecord(value)) return rejected(observer, "observability", "object-required");
  if (value.kind === "profile") {
    return isPlatformContractName(value.profile) || rejected(observer, "observability.profile", "profile-name-invalid");
  }
  if (value.kind !== "opt_out") return rejected(observer, "observability.kind", "unsupported");
  if (!isPlatformObservabilityOptOutReason(value.reason)) return rejected(observer, "observability.reason", "opt-out-reason-invalid");
  if (typeof value.justification !== "string") return rejected(observer, "observability.justification", "justification-string-required");
  if (!(value.justification.trim().length > 0)) return rejected(observer, "observability.justification", "justification-empty");
  if (!(value.justification.length <= 280)) return rejected(observer, "observability.justification", "justification-too-long");
  return true;
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

export function platformProfileAllowsSignal( // Check whether a capability explicitly approved one operational signal family.
  profile: PlatformCapabilityObservabilityProfile, // Read the registered profile governing the current capability.
  signal: PlatformObservabilitySignalKind, // Ask about one closed signal-family value.
): boolean { // Return a simple decision that runtime callers can apply without duplicating profile logic.
  return profile.signals.includes(signal); // Signal declarations are already validated and deduplicated at registration time.
}

export function platformProfileMeasuresLatency( // Check whether a profile truthfully declares one timing interval as an objective.
  profile: PlatformCapabilityObservabilityProfile, // Read the registered profile governing the current capability.
  measurement: PlatformLatencyMeasurement, // Name the exact interval whose start and finish points the caller knows.
): boolean { // Return false when no NFR objective permits this measurement.
  return profile.nfrObjectives?.some((objective) => objective.measurement === measurement) ?? false; // Keep undeclared latency out of metrics even when ordinary counters are enabled.
}

export function platformProfileLogFields( // Project capability facts through the log-field allowlist.
  profile: PlatformCapabilityObservabilityProfile, // Read the registered profile governing the current capability.
  nomenclature: PlatformOperationalNomenclature, // Receive only typed provider-neutral capability facts.
): PlatformProfileObservationFields { // Return only the canonical facts this profile approved for operational logs.
  return selectProfileFields(profile.logFieldNames, nomenclature, profile); // Omit every fact not explicitly allowlisted for logs.
}

export function platformProfileMetricLabels( // Project capability facts through the stricter metric-dimension allowlist.
  profile: PlatformCapabilityObservabilityProfile, // Read the registered profile governing the current capability.
  nomenclature: PlatformOperationalNomenclature, // Receive only typed provider-neutral capability facts.
): Readonly<Record<string, MetricLabelValue>> { // Return only bounded scalar labels accepted by Core metrics.
  return Object.fromEntries(Object.entries(selectProfileFields(profile.metricDimensionFieldNames, nomenclature, profile))) as Readonly<Record<string, MetricLabelValue>>; // Widen the completed scalar projection to Core's metric-label map shape.
}

export function platformProfileTraceFields( // Project capability facts through the trace-attribute allowlist.
  profile: PlatformCapabilityObservabilityProfile, // Read the registered profile governing the current capability.
  nomenclature: PlatformOperationalNomenclature, // Receive only typed provider-neutral capability facts.
): PlatformProfileObservationFields { // Return only canonical facts this profile approved for diagnostic spans.
  return selectProfileFields(profile.traceAttributeNames, nomenclature, profile); // Keep trace attributes from becoming a logging-policy bypass.
}

function validateNfrObjectives(value: unknown, observer?: PlatformContractObserver): value is readonly PlatformNfrObjectiveReference[] | undefined { // Validate optional NFR objective references and their class-to-measurement compatibility.
  if (value === undefined) { // Allow capabilities with useful telemetry but no latency objective.
    return true; // Accept the absent optional declaration.
  }

  if (!Array.isArray(value)) return rejected(observer, "nfrObjectives", "array-required");
  if (value.length === 0) return rejected(observer, "nfrObjectives", "array-empty");

  const seenObjectives = new Set<string>(); // Track pairs so a profile cannot declare the same objective twice.
  for (const objective of value) { // Inspect every declared class and interval pair.
    if (!isRecord(objective)) return rejected(observer, "nfrObjectives", "object-required");
    if (!isPlatformNfrClass(objective.nfrClass)) return rejected(observer, "nfrObjectives.nfrClass", "nfr-class-invalid");
    if (!isPlatformLatencyMeasurement(objective.measurement)) return rejected(observer, "nfrObjectives.measurement", "measurement-invalid");

    const compatibleMeasurements: readonly PlatformLatencyMeasurement[] = platformNfrClassMeasurements[objective.nfrClass]; // Widen one class-specific tuple to the common measurement union for safe membership checking.
    if (!compatibleMeasurements.includes(objective.measurement)) { // Reject a class paired with a nonsensical interval.
      return rejected(observer, "nfrObjectives.measurement", "measurement-incompatible"); // Keep acceptance, completion, queue, and health timing distinct.
    }

    const objectiveKey = `${objective.nfrClass}:${objective.measurement}`; // Form a stable duplicate-detection key from two bounded values.
    if (seenObjectives.has(objectiveKey)) { // Reject duplicate declarations that add no semantic information.
      return rejected(observer, "nfrObjectives", "duplicate-member"); // Keep the profile easy to review.
    }

    seenObjectives.add(objectiveKey); // Remember the accepted pair before checking the next one.
  }

  return true; // Accept the complete unique compatible objective list.
}

function validateFieldNames<TFieldName extends string>(value: unknown, isFieldName: (candidate: unknown) => candidate is TFieldName, observer?: PlatformContractObserver): value is readonly TFieldName[] | undefined { // Validate an optional non-empty unique allowlist against a supplied field guard.
  if (value === undefined) { // Allow a signal family to use no optional canonical fields.
    return true; // Treat absence as a valid minimal declaration.
  }

  return isNonEmptyUniqueArray(value, isFieldName, observer); // Require a present allowlist to contain distinct reviewed fields.
}

function isNonEmptyUniqueArray<TValue extends string>(value: unknown, isValue: (candidate: unknown) => candidate is TValue, observer?: PlatformContractObserver): value is readonly TValue[] { // Check a literal array for non-emptiness, membership, and duplicates.
  if (!Array.isArray(value)) return rejected(observer, "signals", "array-required");
  if (!(value.length > 0)) return rejected(observer, "signals", "array-empty");
  if (!value.every(isValue)) return rejected(observer, "signals", "member-invalid");
  return new Set(value).size === value.length || rejected(observer, "signals", "duplicate-member"); // Reject duplicate items that make review harder.
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> { // Narrow an unknown runtime value to a non-null object record.
  return typeof value === "object" && value !== null; // Reject primitives and null.
}

function isOneOf<TValue extends string>(value: unknown, values: readonly TValue[]): value is TValue { // Compare an unknown string with one controlled literal vocabulary.
  return typeof value === "string" && values.includes(value as TValue); // Accept only exact known values.
}

function selectProfileFields( // Apply one optional profile allowlist to the complete controlled nomenclature object.
  allowedFields: readonly PlatformOperationalFieldName[] | readonly PlatformMetricDimensionFieldName[] | undefined, // Accept the profile's relevant reviewed field list.
  nomenclature: PlatformOperationalNomenclature, // Read the complete typed operational facts supplied by the platform runtime.
  profile: PlatformErrorClassificationOptions,
): PlatformProfileObservationFields { // Return a newly projected minimal set of safe canonical fields.
  if (allowedFields === undefined) { // Treat an omitted optional allowlist as approval for no optional facts.
    return {}; // A signal can still be emitted with its fixed name and no facts.
  }

  const values = { // Map canonical emitted keys to their corresponding typed nomenclature values exactly once.
    capability: nomenclature.capability, // Preserve the stable capability identity, never a raw route or resource identifier.
    action: nomenclature.action, // Preserve the controlled business action.
    actor_type: nomenclature.actorType, // Preserve a bounded actor category only when supplied.
    interaction_source: nomenclature.interactionSource, // Preserve a bounded origin channel only when supplied.
    execution_context: nomenclature.executionContext, // Preserve the server/worker/scheduler/CLI location.
    http_method: nomenclature.httpMethod, // Preserve a bounded method only for server work that supplies it.
    http_status_code: nomenclature.httpStatusCode, // Preserve a numeric response result only for server work that supplies it.
    job_delivery_disposition: nomenclature.jobDeliveryDisposition, // Preserve the controlled worker delivery decision only when supplied.
    outcome: nomenclature.outcome, // Preserve the shared logical capability outcome.
    error_class: platformOptionalErrorClassification(nomenclature.errorClass, profile), // Exact declaration membership, one original property read.
  } satisfies Readonly<Record<PlatformOperationalFieldName, string | number | undefined>>; // Prove the mapping remains complete whenever canonical field names change.
  const selected: Record<PlatformOperationalFieldName, string | number | undefined> = {} as Record<PlatformOperationalFieldName, string | number | undefined>; // Build a fresh complete map so unapproved facts cannot leak through object spreading.

  for (const fieldName of allowedFields) { // Inspect each field the reviewed profile expressly permits.
    const value = values[fieldName]; // Read the one matching typed operational fact.
    if (value !== undefined) { // Avoid emitting absent optional facts as misleading null-like dimensions.
      selected[fieldName] = value; // Copy only a present scalar fact into the returned profile projection.
    }
  }

  return selected as PlatformProfileObservationFields; // Return the narrow field projection after the checked loop excluded every absent or unapproved fact.
}

function rejected(observer: PlatformContractObserver | undefined, field: PlatformContractDiagnosticField, condition: PlatformContractDiagnosticCondition): false {
  try { observer?.({ field, condition }); } catch { /* Optional observation only. */ } return false;
}

const platformNfrClassMeasurements = { // Map each NFR class to the latency intervals that have truthful start and finish points for it.
  interactive_read: ["request_response_latency"], // Reads complete on the request path.
  interactive_command: ["request_response_latency"], // Interactive commands acknowledge their completed request-path work.
  async_acceptance: ["request_response_latency"], // Async acceptance is measured before background completion starts.
  async_completion: ["job_execution_latency", "end_to_end_completion_latency"], // Async completion may need worker-only and whole-workflow timing.
  async_queue_delay: ["queue_wait_latency"], // Queue delay measures waiting before execution.
  health_probe: ["health_check_latency"], // Health checks have their own short execution interval.
} as const satisfies Readonly<Record<PlatformNfrClass, readonly PlatformLatencyMeasurement[]>>; // Keep mapping complete whenever an NFR class changes.
