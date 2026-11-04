import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";

export const serverDiagnosticErrorCodes = [
  "PLATFORM_SERVER_MOUNT_FAILED", "PLATFORM_SERVER_CONFIG_INVALID", "PLATFORM_SERVER_START_FAILED",
  "PLATFORM_SERVER_ROUTE_NOT_FOUND", "PLATFORM_SERVER_METHOD_NOT_ALLOWED", "PLATFORM_SERVER_RATE_LIMITED",
  "PLATFORM_SERVER_UNAUTHENTICATED", "PLATFORM_SERVER_FORBIDDEN", "PLATFORM_SERVER_RESOURCE_NOT_FOUND",
  "PLATFORM_SERVER_TENANT_RESOLVER_REQUIRED", "PLATFORM_SERVER_AUTHORIZER_REQUIRED", "PLATFORM_SERVER_AUTHZ_MAPPING_INVALID",
  "PLATFORM_SERVER_TRANSPORT_CONFIG_INVALID", "PLATFORM_SERVER_INVALID_REQUEST", "PLATFORM_SERVER_PAYLOAD_TOO_LARGE",
  "PLATFORM_SERVER_UNSUPPORTED_MEDIA_TYPE", "PLATFORM_SERVER_REQUEST_TIMEOUT", "PLATFORM_SERVER_SERVICE_UNAVAILABLE", "PLATFORM_SERVER_HANDLER_FAILED",
] as const;
export const serverObservedPhases = ["configuration", "mount", "lifecycle", "listen", "authentication", "authorization", "tenant-resolution", "context", "readiness", "request-validation", "admission", "handler", "response", "shutdown"] as const;

export const platformServerDiagnostic = defineDiagnostic({ code: "platform-server.operation-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    errorCode: { type: "enum", values: serverDiagnosticErrorCodes },
    phase: { type: "enum", values: serverObservedPhases },
    reason: { type: "enum", values: ["invalid", "rejected", "unavailable", "deadline-exceeded", "unclassified"] },
    effect: { type: "enum", values: ["not-started", "rejected", "unknown"] },
  } },
} as const);
const selectionClassification = { failureKind: "configuration", failureSource: "platform", severity: "info", recovery: "not_recoverable", action: "none" } as const;
const fallbackClassification = { ...selectionClassification, severity: "warning", recovery: "manual_investigation" } as const;
const configurationPhase = { type: "enum", values: ["configuration"] } as const;
const selectedEffect = { type: "enum", values: ["selected", "default-selected"] } as const;

export const serverListenerConfigurationDiagnostic = defineDiagnostic({ code: "platform-server.listener-configuration-selected", version: 1,
  classification: selectionClassification,
  detail: { type: "object", properties: {
    phase: configurationPhase,
    setting: { type: "enum", values: ["http.host", "http.port"] },
    source: { type: "enum", values: ["environment", "process-option", "default"] },
    reason: { type: "enum", values: ["provided", "missing", "empty", "explicit-override"] },
    effect: selectedEffect,
  } },
} as const);

export const serverPortFallbackReasons = ["not-numeric", "not-finite", "not-integer", "below-minimum", "above-maximum"] as const;
export const serverPortConfigurationFallbackDiagnostic = defineDiagnostic({ code: "platform-server.port-configuration-fallback", version: 1,
  classification: fallbackClassification,
  detail: { type: "object", properties: {
    phase: configurationPhase,
    setting: { type: "enum", values: ["http.port"] },
    source: { type: "enum", values: ["default"] },
    reason: { type: "enum", values: serverPortFallbackReasons },
    effect: { type: "enum", values: ["default-selected"] },
  } },
} as const);

const healthSelectionProperties = {
  phase: configurationPhase,
  setting: { type: "enum", values: ["http.health.liveness-exposure", "http.health.readiness-exposure"] },
  source: { type: "enum", values: ["environment", "default", "authentication-default"] },
  exposure: { type: "enum", values: ["public", "authenticated"] },
} as const;
export const serverHealthExposureSelectionDiagnostic = defineDiagnostic({ code: "platform-server.health-exposure-selected", version: 1,
  classification: selectionClassification,
  detail: { type: "object", properties: { ...healthSelectionProperties,
    reason: { type: "enum", values: ["provided", "missing", "empty"] }, effect: selectedEffect,
  } },
} as const);
export const serverHealthExposureFallbackDiagnostic = defineDiagnostic({ code: "platform-server.health-exposure-fallback", version: 1,
  classification: fallbackClassification,
  detail: { type: "object", properties: { ...healthSelectionProperties,
    source: { type: "enum", values: ["default", "authentication-default"] },
    reason: { type: "enum", values: ["unsupported"] },
    effect: { type: "enum", values: ["default-selected"] },
  } },
} as const);
export const serverTransportConfigurationFields = ["maxRequestBodyBytes", "maxHeaderBytes", "maxHeadersCount", "headersTimeoutMs", "requestTimeoutMs",
  "keepAliveTimeoutMs", "handlerTimeoutMs", "shutdownDrainTimeoutMs", "maxConcurrentRequests", "maxRequestsPerSocket"] as const;
export const serverTransportConfigurationDiagnostic = defineDiagnostic({ code: "platform-server.transport-configuration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: serverTransportConfigurationFields },
    reason: { type: "enum", values: ["wrong-type", "not-finite", "not-integer", "not-positive"] },
    phase: configurationPhase, effect: { type: "enum", values: ["rejected"] },
  } },
} as const);
export const serverTransportRelationshipDiagnostic = defineDiagnostic({ code: "platform-server.transport-configuration-inconsistent", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    relationship: { type: "enum", values: ["headers-within-request-timeout"] },
    rule: { type: "enum", values: ["less-than-or-equal"] }, phase: configurationPhase,
    effect: { type: "enum", values: ["rejected"] },
  } },
} as const);

export const serverTransportRejectionReasons = [
  "url-invalid", "method-unsupported", "server-closing", "concurrency-capacity-reached",
  "declared-length-not-integer", "declared-length-negative", "declared-length-over-limit",
  "streamed-body-over-limit", "media-type-missing", "media-type-empty", "media-type-unsupported",
  "body-decoding-threw", "handler-deadline-observed", "handler-result-unavailable",
] as const;
export const serverTransportRejectionDiagnostic = defineDiagnostic({ code: "platform-server.transport-request-rejected", version: 1,
  classification: { failureKind: "unknown", failureSource: "platform", severity: "warning", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    reason: { type: "enum", values: serverTransportRejectionReasons },
    phase: { type: "enum", values: ["metadata", "admission", "body", "handler"] },
    effect: { type: "enum", values: ["request-rejected", "handler-still-pending", "handler-result-not-returned"] },
  } },
} as const);
export const serverTransportBoundaryPhases = [
  "metadata", "admission", "body-stream", "handler", "late-handler", "response-headers", "response-status",
  "response-serialization", "response-end", "failure-projection", "server-construction", "listen", "client-error", "server-error", "close-invocation", "close-callback",
] as const;
export const serverTransportBoundaryDiagnostic = defineDiagnostic({ code: "platform-server.transport-boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: serverTransportBoundaryPhases },
    reason: { type: "enum", values: ["threw", "error-event", "callback-error"] },
    effect: { type: "enum", values: ["request-not-returned", "handler-settled", "listener-not-returned", "close-not-confirmed", "unknown"] },
  } },
} as const);
export const serverTransportObservationDiagnostic = defineDiagnostic({ code: "platform-server.transport-state-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "platform", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: { type: "object", properties: {
    reason: { type: "enum", values: ["response-already-ended", "response-destroyed", "response-closed-before-end", "drain-deadline-observed"] },
    phase: { type: "enum", values: ["response", "shutdown"] },
    effect: { type: "enum", values: ["response-skipped", "abort-requested", "shutdown-still-pending"] },
  } },
} as const);
export const serverClientAddressTrustConfigurationDiagnostic = defineDiagnostic({ code: "platform-server.client-address-trust-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: configurationPhase, setting: { type: "enum", values: ["http.client-address-trust"] },
    reason: { type: "enum", values: ["unsupported"] }, effect: { type: "enum", values: ["rejected"] },
  } },
} as const);
export const serverClientAddressFallbackDiagnostic = defineDiagnostic({ code: "platform-server.client-address-fallback-selected", version: 1,
  classification: { failureKind: "unknown", failureSource: "platform", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["client-address-selection"] },
    reason: { type: "enum", values: ["forwarded-header-missing", "forwarded-final-address-invalid"] },
    source: { type: "enum", values: ["socket-peer", "unavailable"] },
    effect: { type: "enum", values: ["fallback-selected"] },
  } },
} as const);
export const serverConfigurationOmissionDiagnostic = defineDiagnostic({ code: "platform-server.configuration-omitted", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: { type: "object", properties: {
    phase: configurationPhase,
    setting: { type: "enum", values: ["release.source-commit", "http.cors-origin", "http.cors-allowlist"] },
    reason: { type: "enum", values: ["missing", "empty", "normalization-empty", "format-rejected"] },
    effect: { type: "enum", values: ["omitted"] },
  } },
} as const);
export const serverProcessBoundaryDiagnostic = defineDiagnostic({ code: "platform-server.process-boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["startup-log", "shutdown-log", "shutdown-close", "signal-registration"] },
    reason: { type: "enum", values: ["boundary-threw"] },
    effect: { type: "enum", values: ["process-not-returned", "shutdown-not-completed"] },
  } },
} as const);
export const serverRequestPredicateFields = ["tenant-result", "tenantId", "isolationKey", "resource-result", "resource.kind", "resource.disclosure",
  "principal", "authorizer", "request-body", "resource", "route"] as const;
export const serverRequestPredicateConditions = ["object-required", "string-required", "nonempty-required", "kind-rejected", "disclosure-rejected",
  "unavailable", "validator-rejected", "not-found", "forbidden-disclosure", "method-not-registered", "path-not-registered", "tenant-unavailable"] as const;
export const serverRequestPredicatePhases = ["tenant-resolution", "resource-resolution", "authorization", "request-validation", "routing"] as const;
export const serverRequestPredicateDiagnostic = defineDiagnostic({ code: "platform-server.request-predicate-rejected", version: 1,
  classification: { failureKind: "unknown", failureSource: "platform", severity: "warning", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: serverRequestPredicateFields }, condition: { type: "enum", values: serverRequestPredicateConditions },
    phase: { type: "enum", values: serverRequestPredicatePhases }, effect: { type: "enum", values: ["handler-not-invoked"] },
  } },
} as const);
export const serverRequestBoundaryPhases = ["request-clock", "request-identity", "route-selection", "route-parameter-decoding", "tenant-resolution",
  "resource-resolution", "authorization", "request-validation", "handler", "response", "context"] as const;
export const serverRequestBoundaryEffects = ["handler-not-invoked", "handler-invocation-outcome-unknown", "handler-completed-response-not-returned"] as const;
export const serverRequestBoundaryDiagnostic = defineDiagnostic({ code: "platform-server.request-boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: serverRequestBoundaryPhases }, reason: { type: "enum", values: ["boundary-threw"] },
    effect: { type: "enum", values: serverRequestBoundaryEffects }, index: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["index"] },
} as const);

export function serverRequestPredicateRecord(field: (typeof serverRequestPredicateFields)[number], condition: (typeof serverRequestPredicateConditions)[number],
  phase: (typeof serverRequestPredicatePhases)[number]) {
  return checkedRecord(serverRequestPredicateDiagnostic, { field, condition, phase, effect: "handler-not-invoked" });
}
export function serverRequestBoundaryRecord(phase: (typeof serverRequestBoundaryPhases)[number], effect: (typeof serverRequestBoundaryEffects)[number], index?: number) {
  return checkedRecord(serverRequestBoundaryDiagnostic, { phase, reason: "boundary-threw", effect, ...(index === undefined ? {} : { index }) });
}

export function serverConfigurationOmissionRecord(setting: "release.source-commit" | "http.cors-origin" | "http.cors-allowlist",
  reason: "missing" | "empty" | "normalization-empty" | "format-rejected") {
  return checkedRecord(serverConfigurationOmissionDiagnostic, { phase: "configuration", setting, reason, effect: "omitted" });
}
export function serverProcessBoundaryRecord(phase: "startup-log" | "shutdown-log" | "shutdown-close" | "signal-registration",
  effect: "process-not-returned" | "shutdown-not-completed") {
  return checkedRecord(serverProcessBoundaryDiagnostic, { phase, reason: "boundary-threw", effect });
}

export function serverClientAddressTrustConfigurationRecord() {
  return checkedRecord(serverClientAddressTrustConfigurationDiagnostic, {
    phase: "configuration", setting: "http.client-address-trust", reason: "unsupported", effect: "rejected",
  });
}
export function serverClientAddressFallbackRecord(
  reason: "forwarded-header-missing" | "forwarded-final-address-invalid", source: "socket-peer" | "unavailable",
) {
  return checkedRecord(serverClientAddressFallbackDiagnostic, { phase: "client-address-selection", reason, source, effect: "fallback-selected" });
}

/** Optional evidence delivery cannot change transport or adapter behavior. */
export function observeServerDiagnostic(observer: ((record: import("@kanbien/core/diagnostics").DiagnosticRecord) => unknown) | undefined,
  record: import("@kanbien/core/diagnostics").DiagnosticRecord): void {
  if (observer === undefined) return;
  try {
    const pending = observer(record);
    if (pending === undefined) return;
    const ignore = (): void => {};
    try { Reflect.apply(intrinsicPromiseThen, pending, [undefined, ignore]); }
    catch { Reflect.apply(intrinsicPromiseThen, Promise.resolve(pending), [undefined, ignore]); }
  } catch { /* Optional diagnostics are not a transport control path. */ }
}
const intrinsicPromiseThen = Promise.prototype.then;

function checkedRecord<T>(definition: import("@kanbien/core/diagnostics").DiagnosticDefinition<T>, detail: NoInfer<T>) {
  const record = createDiagnosticRecord(definition, detail);
  if (!record.ok) throw new TypeError("PLATFORM_SERVER_DIAGNOSTIC_INVALID");
  return record.value;
}

export function serverTransportRejectionRecord(reason: (typeof serverTransportRejectionReasons)[number],
  phase: "metadata" | "admission" | "body" | "handler", effect: "request-rejected" | "handler-still-pending" | "handler-result-not-returned" = "request-rejected") {
  return checkedRecord(serverTransportRejectionDiagnostic, { reason, phase, effect });
}
export function serverTransportBoundaryRecord(phase: (typeof serverTransportBoundaryPhases)[number],
  reason: "threw" | "error-event" | "callback-error",
  effect: "request-not-returned" | "handler-settled" | "listener-not-returned" | "close-not-confirmed" | "unknown") {
  return checkedRecord(serverTransportBoundaryDiagnostic, { phase, reason, effect });
}
export function serverTransportObservationRecord(reason: "response-already-ended" | "response-destroyed" | "response-closed-before-end" | "drain-deadline-observed",
  phase: "response" | "shutdown", effect: "response-skipped" | "abort-requested" | "shutdown-still-pending") {
  return checkedRecord(serverTransportObservationDiagnostic, { reason, phase, effect });
}

export const platformServerDiagnosticCatalog = { owner: "platform-server", definitions: [platformServerDiagnostic,
  serverListenerConfigurationDiagnostic, serverPortConfigurationFallbackDiagnostic,
  serverHealthExposureSelectionDiagnostic, serverHealthExposureFallbackDiagnostic,
  serverTransportConfigurationDiagnostic, serverTransportRelationshipDiagnostic,
  serverTransportRejectionDiagnostic, serverTransportBoundaryDiagnostic, serverTransportObservationDiagnostic,
  serverClientAddressTrustConfigurationDiagnostic, serverClientAddressFallbackDiagnostic,
  serverConfigurationOmissionDiagnostic, serverProcessBoundaryDiagnostic,
  serverRequestPredicateDiagnostic, serverRequestBoundaryDiagnostic,
] } as const;

/** Interpret only the boundary's stable code, never exception text or request data. */
export function serverDiagnosticRecord(code: (typeof serverDiagnosticErrorCodes)[number], observedPhase?: (typeof serverObservedPhases)[number]) {
  const phase = observedPhase ?? (code === "PLATFORM_SERVER_MOUNT_FAILED" ? "mount"
    : ["PLATFORM_SERVER_CONFIG_INVALID", "PLATFORM_SERVER_TENANT_RESOLVER_REQUIRED", "PLATFORM_SERVER_AUTHORIZER_REQUIRED", "PLATFORM_SERVER_AUTHZ_MAPPING_INVALID", "PLATFORM_SERVER_TRANSPORT_CONFIG_INVALID"].includes(code) ? "configuration"
    : code === "PLATFORM_SERVER_START_FAILED" ? "listen"
    : code === "PLATFORM_SERVER_HANDLER_FAILED" ? "handler"
    : code === "PLATFORM_SERVER_UNAUTHENTICATED" ? "authentication" : code === "PLATFORM_SERVER_FORBIDDEN" ? "authorization"
    : ["PLATFORM_SERVER_INVALID_REQUEST", "PLATFORM_SERVER_PAYLOAD_TOO_LARGE", "PLATFORM_SERVER_UNSUPPORTED_MEDIA_TYPE", "PLATFORM_SERVER_REQUEST_TIMEOUT"].includes(code) ? "request-validation" : "admission");
  const record = createDiagnosticRecord(platformServerDiagnostic, { errorCode: code, phase,
    reason: code === "PLATFORM_SERVER_REQUEST_TIMEOUT" ? "deadline-exceeded" : code === "PLATFORM_SERVER_HANDLER_FAILED" || code === "PLATFORM_SERVER_START_FAILED" ? "unclassified" : phase === "configuration" ? "invalid" : "rejected",
    effect: phase === "configuration" || phase === "mount" ? "not-started" : code === "PLATFORM_SERVER_HANDLER_FAILED" || code === "PLATFORM_SERVER_START_FAILED" ? "unknown" : "rejected" });
  if (!record.ok) throw new TypeError("PLATFORM_SERVER_DIAGNOSTIC_INVALID");
  return record.value;
}
