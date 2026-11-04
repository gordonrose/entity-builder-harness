import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { PlatformContractError, PlatformRegistrationKind } from "./errors";

export const platformContractDiagnosticFields = ["validator.validate", "validator.explain", "resourceAuthorization.permission", "resourceAuthorization.resolve", "handler.handle", "auth.kind", "auth.permissions", "observability.kind", "observability.profile", "observability.reason", "observability.justification", "nfrObjectives.nfrClass", "nfrObjectives.measurement", "declaration", "name", "permission", "method", "path", "auth", "observability", "tenant", "resourceAuthorization", "validator", "handler", "messageType", "capability", "action", "signals", "logFieldNames", "metricDimensionFieldNames", "traceAttributeNames", "nfrObjectives", "owner", "definitions", "identity"] as const;
export const platformContractDiagnosticConditions = ["path-not-absolute", "path-whitespace", "path-url-scheme", "object-required", "string-required", "invalid-format", "unsupported", "reserved-path", "public-controls", "public-permissions", "permissions-array-required", "function-required", "profile-name-invalid", "opt-out-reason-invalid", "justification-string-required", "justification-empty", "justification-too-long", "array-required", "array-empty", "member-invalid", "duplicate-member", "nfr-class-invalid", "measurement-invalid", "measurement-incompatible", "signal-required", "namespace-mismatch", "duplicate-name", "duplicate-route-key", "duplicate-message-type", "duplicate-permission", "duplicate-owner", "duplicate-identity", "undeclared-permission", "undeclared-profile", "plain-object-required", "exact-fields-required", "data-fields-required", "owner-too-long", "definitions-too-many", "plain-array-required", "dense-array-required", "definition-invalid", "ownership-mismatch", "inspection-threw", "declaration-rejected"] as const;
export type PlatformContractDiagnosticField = typeof platformContractDiagnosticFields[number];
export type PlatformContractDiagnosticCondition = typeof platformContractDiagnosticConditions[number];
export interface PlatformContractObservation { readonly field: PlatformContractDiagnosticField; readonly condition: PlatformContractDiagnosticCondition }
export type PlatformContractObserver = (observation: PlatformContractObservation) => void;

export const platformContractRegistrationDiagnosticDefinition = defineDiagnostic({
  code: "platform-contracts.registration-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "platform", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false, action: "none" },
  detail: { type: "object", properties: {
    registration: { type: "enum", values: ["app", "route", "permission", "job", "health", "config", "observability-profile", "diagnostic-catalog", "identifier"] },
    field: { type: "enum", values: platformContractDiagnosticFields },
    condition: { type: "enum", values: platformContractDiagnosticConditions },
    phase: { type: "enum", values: ["validation", "registration", "resolution", "structure", "definitions", "conflicts", "snapshot"] },
    effect: { type: "enum", values: ["rejected"] },
  } },
});
/** Only malformed new errorClasses declarations use v2. */
export const platformContractClassificationDiagnosticDefinition = defineDiagnostic({
  code: "platform-contracts.registration-rejected", version: 2,
  classification: platformContractRegistrationDiagnosticDefinition.classification,
  detail: { type: "object", properties: {
    registration: { type: "enum", values: ["observability-profile"] },
    field: { type: "enum", values: ["errorClasses"] },
    condition: { type: "enum", values: ["array-required", "plain-array-required", "dense-array-required", "data-fields-required", "too-many-members", "member-invalid", "member-too-long", "member-invalid-format", "duplicate-member", "inspection-threw"] },
    phase: { type: "enum", values: ["validation"] }, effect: { type: "enum", values: ["rejected"] },
    index: { type: "integer", minimum: 0, maximum: 63 },
  }, optional: ["index"] },
} as const);
export function platformContractClassificationDiagnosticRecord(issue: import("./observability").PlatformErrorClassesIssue): DiagnosticRecord {
  const record = createDiagnosticRecord(platformContractClassificationDiagnosticDefinition,
    { registration: "observability-profile", field: "errorClasses", ...issue, phase: "validation", effect: "rejected" });
  if (!record.ok) throw new TypeError("PLATFORM_CONTRACT_DIAGNOSTIC_INVALID");
  return record.value;
}
export const platformOperationalEventDiagnosticDefinition = defineDiagnostic({
  code: "platform-contracts.operational-event-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "platform", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false, action: "none" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["readiness-event"] },
    field: { type: "enum", values: ["event", "keys", "type", "target", "scope", "workload", "dependency", "readiness", "observed-at", "diagnostic-code"] },
    condition: { type: "enum", values: ["object-required", "null-rejected", "array-rejected", "unknown-field", "predicate-rejected", "string-required", "unsupported", "invalid-format", "date-parse-rejected", "unexpected-present"] },
    phase: { type: "enum", values: ["validation"] }, effect: { type: "enum", values: ["predicate-rejected"] },
    ordinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["ordinal"] },
} as const);
export const platformOperationalBoundaryDiagnosticDefinition = defineDiagnostic({
  code: "platform-contracts.operational-boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false, action: "none" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["readiness-event", "fixed-feature-flags"] },
    phase: { type: "enum", values: ["structure", "key-enumeration", "key-traversal-selection", "key-traversal", "field-projection", "field-predicate", "time-parsing", "result-projection", "snapshot", "read"] },
    field: { type: "enum", values: ["event", "keys", "type", "target", "scope", "workload", "dependency", "readiness", "observed-at", "diagnostic-code", "flags", "name", "value"] },
    reason: { type: "enum", values: ["threw"] },
    effect: { type: "enum", values: ["event-not-produced", "reader-not-produced", "value-not-produced"] },
  } },
} as const);
export type PlatformOperationalEventDiagnosticDetail = NonNullable<typeof platformOperationalEventDiagnosticDefinition.__detail>;
export type PlatformOperationalBoundaryDiagnosticDetail = NonNullable<typeof platformOperationalBoundaryDiagnosticDefinition.__detail>;
export function platformOperationalEventDiagnosticRecord(detail: Omit<PlatformOperationalEventDiagnosticDetail, "operation" | "phase" | "effect">): DiagnosticRecord {
  const record = createDiagnosticRecord(platformOperationalEventDiagnosticDefinition, { operation: "readiness-event", phase: "validation", effect: "predicate-rejected", ...detail });
  if (!record.ok) throw new TypeError("PLATFORM_CONTRACT_DIAGNOSTIC_INVALID");
  return record.value;
}
export function platformOperationalBoundaryDiagnosticRecord(detail: Omit<PlatformOperationalBoundaryDiagnosticDetail, "reason">): DiagnosticRecord {
  const record = createDiagnosticRecord(platformOperationalBoundaryDiagnosticDefinition, { ...detail, reason: "threw" });
  if (!record.ok) throw new TypeError("PLATFORM_CONTRACT_DIAGNOSTIC_INVALID");
  return record.value;
}
export const platformContractDiagnosticCatalog = Object.freeze({ owner: "platform-contracts", definitions: Object.freeze([platformContractRegistrationDiagnosticDefinition, platformContractClassificationDiagnosticDefinition, platformOperationalEventDiagnosticDefinition, platformOperationalBoundaryDiagnosticDefinition]) });

/** Only observations made by the existing predicate belong here; never caller values. */
export function platformContractDiagnosticRecord(registration: PlatformRegistrationKind | "identifier", field: PlatformContractDiagnosticField,
  condition: PlatformContractDiagnosticCondition, phase: "validation" | "registration" | "resolution" | "structure" | "definitions" | "conflicts" | "snapshot" = "validation"): DiagnosticRecord {
  const record = createDiagnosticRecord(platformContractRegistrationDiagnosticDefinition, { registration, field, condition, phase, effect: "rejected" });
  if (!record.ok) throw new TypeError("PLATFORM_CONTRACT_DIAGNOSTIC_INVALID");
  return record.value;
}
export function withPlatformContractDiagnostic(error: PlatformContractError, registration: PlatformRegistrationKind | "identifier", field: PlatformContractDiagnosticField,
  condition: PlatformContractDiagnosticCondition, phase?: "validation" | "registration" | "resolution" | "structure" | "definitions" | "conflicts" | "snapshot"): PlatformContractError {
  return { ...error, diagnosticRecord: platformContractDiagnosticRecord(registration, field, condition, phase) };
}
