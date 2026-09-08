import type { AuditActorType } from "@kanbien/core/audit"; // Reuse Core's provider-neutral accountable-actor vocabulary without selecting an audit store.
import type { Brand, Result } from "@kanbien/core/shared"; // Reuse the shared branded-name and explicit-result primitives.
import type { PlatformContractError } from "./errors"; // Return the existing platform-contract error shape when a capability name is malformed.
import { brandedPlatformContractName } from "./identifiers"; // Apply the checked dotted-name rule used by existing platform identifiers.
import type { HttpMethod } from "./routes"; // Reuse the already constrained HTTP transport-method vocabulary.

export const platformCapabilityActions = [ // Declare the controlled business-action vocabulary used by capability declarations.
  "create", // Name creation of a new resource or business object.
  "read", // Name retrieval of one known resource.
  "list", // Name retrieval of a bounded collection without implying a search query.
  "search", // Name query-driven discovery across a collection.
  "update", // Name a change to an existing resource; avoid the ambiguous synonym "edit".
  "delete", // Name a deletion request or completed deletion according to the capability lifecycle.
  "archive", // Name a reversible move out of ordinary active use.
  "restore", // Name restoration of an archived or soft-deleted resource.
  "assign", // Name assignment of a relationship, owner, or responsibility.
  "unassign", // Name removal of an assignment without implying deletion of either resource.
  "grant", // Name granting of an access, entitlement, or other controlled right.
  "revoke", // Name withdrawal of a previously granted right.
  "approve", // Name an affirmative controlled decision.
  "reject", // Name a negative controlled decision; it is a business action, not an HTTP outcome.
  "enable", // Name activation of a controlled setting or capability.
  "disable", // Name deactivation of a controlled setting or capability.
  "publish", // Name making approved material available to its intended audience.
  "unpublish", // Name withdrawing previously published material.
  "upload", // Name movement of data into the product boundary.
  "download", // Name movement of a prepared file or object out to a caller.
  "import", // Name ingestion that becomes product-owned data.
  "export", // Name creation or delivery of product data for an authorised caller.
  "submit", // Name submitting work or a decision for a later process.
  "cancel", // Name cancelling a pending operation where cancellation is meaningful.
  "execute", // Name an explicit operation that does not have a more truthful specialised verb.
  "schedule", // Name arranging work for a future time or recurrence.
  "retry", // Name an explicit retry request, distinct from an automatic delivery disposition.
  "authenticate", // Name proving an actor's identity through an approved authentication process.
  "verify", // Name verification of a fact, identity, artefact, or state.
  "reset", // Name resetting an approved controlled value or state.
  "recover", // Name a controlled recovery action after a failure or lockout.
  "rotate", // Name replacement of a versioned credential, key reference, or other rotating material.
  "generate", // Name production of a derived artefact such as a report or document.
] as const; // Preserve each literal so TypeScript can form a closed action union.

export type PlatformCapabilityAction = (typeof platformCapabilityActions)[number]; // Represent one approved business action in a provider-neutral capability declaration.

export const platformInteractionSources = [ // Declare how work began, separate from actor authority and execution location.
  "web", // A browser-based web interaction initiated the work.
  "mobile", // A mobile application interaction initiated the work.
  "desktop", // A desktop application interaction initiated the work.
  "tablet", // A tablet application interaction initiated the work.
  "chat", // A chat interaction initiated the work through an approved boundary.
  "voice", // A voice interaction initiated the work through an approved boundary.
  "cli", // A human or automation command-line interaction initiated the work.
  "api", // An API client initiated the work.
  "integration", // An external system integration initiated the work.
  "scheduled_job", // A scheduled trigger initiated the work.
  "system", // The platform or product initiated the work without an external interaction.
] as const; // Preserve each literal so TypeScript can form a closed interaction-source union.

export type PlatformInteractionSource = (typeof platformInteractionSources)[number]; // Represent the initiation channel without claiming who had authority.

export const platformExecutionContexts = [ // Declare the bounded runtime locations that can perform a capability.
  "server", // A server process handled the capability synchronously.
  "worker", // A background worker process handled the capability.
  "scheduler", // A scheduler process triggered or ran scheduled work.
  "cli", // A controlled command-line process handled the capability.
] as const; // Preserve each literal so TypeScript can form a closed execution-context union.

export type PlatformExecutionContext = (typeof platformExecutionContexts)[number]; // Represent where work ran, independently of how it was initiated.

export const platformOperationalOutcomes = [ // Declare the shared logical outcomes for operational capability evidence.
  "accepted", // The platform accepted an asynchronous request but has not claimed final completion.
  "succeeded", // The capability completed its intended work successfully.
  "denied", // A policy or authority control refused the requested action.
  "rejected", // Validation, preconditions, or request shape prevented the work from starting.
  "failed", // A technical or unexpected failure prevented successful completion.
  "cancelled", // The work ended because a permitted cancellation occurred.
  "timed_out", // The work ended because its allowed time elapsed.
] as const; // Preserve each literal so TypeScript can form a closed outcome union.

export type PlatformOperationalOutcome = (typeof platformOperationalOutcomes)[number]; // Represent what happened without using transport-specific status words.

export const platformJobDeliveryDispositions = [ // Declare what the worker chose to do with a non-idle delivery attempt.
  "succeeded", // The message completed and does not require another delivery attempt.
  "retry_scheduled", // The message failed this attempt but a later retry has been scheduled.
  "dead_lettered", // The message exhausted or bypassed retry and was quarantined for separate handling.
] as const; // Preserve each literal so TypeScript can form a closed job-delivery-disposition union.

export type PlatformJobDeliveryDisposition = (typeof platformJobDeliveryDispositions)[number]; // Represent delivery handling separately from the business action's logical outcome.

export type PlatformCapabilityName = Brand<string, "PlatformCapabilityName">; // Distinguish a checked capability identity from a route name, job name, or ordinary string.

export interface PlatformOperationalNomenclature { // Describe the provider-neutral semantic facts a future observability profile may select.
  readonly capability: PlatformCapabilityName; // Identify the stable app-owned capability rather than a raw path or provider operation.
  readonly action: PlatformCapabilityAction; // Identify the controlled business verb rather than an HTTP method.
  readonly actorType?: AuditActorType; // Optionally identify a bounded accountable-actor category without emitting an actor identifier.
  readonly interactionSource?: PlatformInteractionSource; // Optionally identify how work began when that fact is safe and useful.
  readonly executionContext: PlatformExecutionContext; // Identify where the work executed.
  readonly httpMethod?: HttpMethod; // Optionally identify the HTTP transport method for server-executed work.
  readonly httpStatusCode?: number; // Optionally identify a numeric HTTP result without overloading a generic status field.
  readonly jobDeliveryDisposition?: PlatformJobDeliveryDisposition; // Optionally identify a worker delivery decision without confusing it with business outcome.
  readonly outcome: PlatformOperationalOutcome; // Identify the logical result of the capability.
  readonly errorClass?: string; // Optionally identify a bounded stable failure classification, never an error message or payload.
}

export const platformOperationalFieldNames = { // Map typed semantic properties to the canonical snake-case keys emitted by future signal profiles.
  capability: "capability", // Name the stable capability identity field.
  action: "action", // Name the controlled business-action field.
  actorType: "actor_type", // Name the bounded actor-category field.
  interactionSource: "interaction_source", // Name the initiation-channel field.
  executionContext: "execution_context", // Name the runtime-location field.
  httpMethod: "http_method", // Name the HTTP transport-method field.
  httpStatusCode: "http_status_code", // Name the numeric HTTP-status field.
  jobDeliveryDisposition: "job_delivery_disposition", // Name the worker-delivery decision field.
  outcome: "outcome", // Name the logical-result field.
  errorClass: "error_class", // Name the bounded error-class field.
} as const satisfies Readonly<Record<keyof PlatformOperationalNomenclature, string>>; // Keep the mapping complete whenever the semantic interface changes.

export type PlatformOperationalFieldName = (typeof platformOperationalFieldNames)[keyof typeof platformOperationalFieldNames]; // Represent one canonical emitted field name.

export function platformCapabilityName(value: string): Result<PlatformCapabilityName, PlatformContractError> { // Validate and brand one app-owned capability identity.
  return brandedPlatformContractName(value, "PlatformCapabilityName", "platform capability name"); // Reuse the established lowercase dotted-name policy.
}

export function isPlatformCapabilityAction(value: unknown): value is PlatformCapabilityAction { // Check untyped input against the controlled business-action vocabulary.
  return isOneOf(value, platformCapabilityActions); // Delegate the literal-array membership test to the local generic helper.
}

export function isPlatformInteractionSource(value: unknown): value is PlatformInteractionSource { // Check untyped input against the controlled interaction-source vocabulary.
  return isOneOf(value, platformInteractionSources); // Delegate the literal-array membership test to the local generic helper.
}

export function isPlatformExecutionContext(value: unknown): value is PlatformExecutionContext { // Check untyped input against the controlled execution-context vocabulary.
  return isOneOf(value, platformExecutionContexts); // Delegate the literal-array membership test to the local generic helper.
}

export function isPlatformOperationalOutcome(value: unknown): value is PlatformOperationalOutcome { // Check untyped input against the controlled logical-outcome vocabulary.
  return isOneOf(value, platformOperationalOutcomes); // Delegate the literal-array membership test to the local generic helper.
}

export function isPlatformOperationalFieldName(value: unknown): value is PlatformOperationalFieldName { // Check untyped input against the canonical emitted operational field names.
  return typeof value === "string" && Object.values(platformOperationalFieldNames).includes(value as PlatformOperationalFieldName); // Accept only one controlled snake-case emitted key.
}

export function isPlatformJobDeliveryDisposition(value: unknown): value is PlatformJobDeliveryDisposition { // Check untyped input against the controlled worker-delivery vocabulary.
  return isOneOf(value, platformJobDeliveryDispositions); // Delegate the literal-array membership test to the local generic helper.
}

function isOneOf<TValue extends string>(value: unknown, values: readonly TValue[]): value is TValue { // Compare one unknown value with a literal string vocabulary without widening its type.
  return typeof value === "string" && values.includes(value as TValue); // Accept only an exact known string from the supplied vocabulary.
}
