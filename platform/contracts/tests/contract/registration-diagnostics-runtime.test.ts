import { deepEqual, equal, throws } from "node:assert/strict";
import { parseDiagnosticRecord } from "@kanbien/core/diagnostics";
import {
  platformContractDiagnosticCatalog, platformContractRegistrationDiagnosticDefinition,
  validatePlatformDiagnosticCatalog, validatePlatformPermissionDeclaration,
  validatePlatformRouteRegistration, validatePlatformJobRegistration,
  validatePlatformCapabilityObservabilityProfile, platformAppId,
  type PlatformContractError, type PlatformRouteRegistration, type PlatformJobRegistration,
  type PlatformCapabilityObservabilityProfile, type PlatformDiagnosticCatalog,
  type PlatformPermissionDeclaration,
  isPlatformObservabilityRequirement,
} from "../../src/index";
import { isPlatformContractName } from "../../src/identifiers";
import { platformContractClassificationDiagnosticDefinition, platformErrorClassification, platformErrorClassDeclarations,
  platformNativeErrorClasses, platformProfileLogFields, platformProfileMetricLabels, platformProfileTraceFields } from "../../src/index";

const canary = "private-canary-token@example.invalid";
equal(isPlatformContractName("BAD", () => { throw new Error(canary); }), false);
equal(isPlatformObservabilityRequirement(null, () => { throw new Error(canary); }), false);
const requirement = { kind: "opt_out", reason: "non_user_workload_path", justification: "Contract test fixture." };
const baseRoute = { name: "test.route", method: "GET", path: "/example", auth: { kind: "public" }, observability: requirement, handler: { handle() {} } };
const baseJob = { name: "test.job", messageType: "test.message", observability: requirement, handler: { handle() {} } };
const baseProfile = { name: "test.profile", capability: "test.capability", action: "read", signals: ["operational_log", "metric", "trace"] };
let classGetters = 0;
const accessorClasses = Object.defineProperty(["APP_FIXED"], "0", { get() { classGetters++; throw canary; }, enumerable: true });
const declarationCases: readonly [unknown, string, number?][] = [
  [{}, "array-required"], [Object.setPrototypeOf(["APP_FIXED"], {}), "plain-array-required"],
  [Array(1), "dense-array-required"], [accessorClasses, "data-fields-required", 0],
  [Array.from({ length: 65 }, (_, index) => "Class" + index), "too-many-members"],
  [[42], "member-invalid", 0], [["A".repeat(129)], "member-too-long", 0], [[canary], "member-invalid-format", 0],
  [[""], "member-invalid-format", 0], [["APP_FIXED", "APP_FIXED"], "duplicate-member", 1],
  [new Proxy([], { ownKeys() { throw canary; } }), "inspection-threw"],
];
for (const [errorClasses, condition, index] of declarationCases) {
  const result = validatePlatformCapabilityObservabilityProfile({ ...baseProfile, errorClasses } as unknown as PlatformCapabilityObservabilityProfile);
  equal(result.ok, false);
  if (result.ok) throw new Error("Expected classification declaration rejection.");
  const record = result.error.diagnosticRecord;
  deepEqual(record, { schema: "core/diagnostic-record/v1", code: "platform-contracts.registration-rejected", definitionVersion: 2,
    detail: { registration: "observability-profile", field: "errorClasses", condition, ...(index === undefined ? {} : { index }), phase: "validation", effect: "rejected" } });
  equal(parseDiagnosticRecord(platformContractClassificationDiagnosticDefinition, record).ok, true);
  equal(parseDiagnosticRecord(platformContractRegistrationDiagnosticDefinition, record).ok, false);
  equal(JSON.stringify(record).includes(canary), false);
}
const accessorDeclaration = Object.defineProperty({ ...baseProfile }, "errorClasses", { get() { classGetters++; throw canary; } });
const accessorRejection = validatePlatformCapabilityObservabilityProfile(accessorDeclaration as unknown as PlatformCapabilityObservabilityProfile);
equal(accessorRejection.ok, false);
if (!accessorRejection.ok) deepEqual(accessorRejection.error.diagnosticRecord?.detail,
  { registration: "observability-profile", field: "errorClasses", condition: "data-fields-required", phase: "validation", effect: "rejected" });
equal(classGetters, 0);
equal(Object.isFrozen(platformNativeErrorClasses), true);
for (const errorClasses of [[], ["A"], ["A".repeat(128)], Array.from({ length: 64 }, (_, index) => "Class" + index)]) {
  equal(validatePlatformCapabilityObservabilityProfile({ ...baseProfile, errorClasses } as unknown as PlatformCapabilityObservabilityProfile).ok, true);
}
let arrayGets = 0;
const deceptiveClasses = new Proxy(["APP_FIXED"], { get(_target, key) {
  arrayGets++;
  if (key === "includes") return () => true;
  if (key === Symbol.iterator) return function* () { yield "PRIVATE_VALID_TOKEN"; };
  return "PRIVATE_VALID_TOKEN";
} });
const bound = { errorClasses: deceptiveClasses };
equal(platformErrorClassification("APP_FIXED", bound), "APP_FIXED");
equal(platformErrorClassification("PRIVATE_VALID_TOKEN", bound), "unknown");
deepEqual(platformErrorClassDeclarations(bound), ["APP_FIXED"]);
equal(arrayGets, 0, "membership cannot call a caller includes/iterator/index trap");
const fullBinding = { errorClasses: Array.from({ length: 128 }, (_, index) => "Class" + index) };
equal(platformErrorClassification("Class127", fullBinding), "Class127", "owner composition may exceed the declaration-only64 limit");
equal(platformErrorClassification("Class128", { errorClasses: [...fullBinding.errorClasses, "Class128"] }), "unknown");
const classifiedProfile = { ...baseProfile, ...bound, logFieldNames: ["error_class"], metricDimensionFieldNames: ["error_class"], traceAttributeNames: ["error_class"] } as unknown as PlatformCapabilityObservabilityProfile;
const facts = { capability: "test.capability", action: "read", executionContext: "server", outcome: "failed", errorClass: "APP_FIXED" } as const;
for (const project of [platformProfileLogFields, platformProfileMetricLabels, platformProfileTraceFields]) {
  deepEqual(project(classifiedProfile, facts as never), { error_class: "APP_FIXED" });
  deepEqual(project(classifiedProfile, { ...facts, errorClass: canary } as never), { error_class: "unknown" });
  deepEqual(project({ ...classifiedProfile, logFieldNames: [], metricDimensionFieldNames: [], traceAttributeNames: [] }, facts as never), {});
}
equal(arrayGets, 0);
const profileReadOrder = ["capability", "action", "actorType", "interactionSource", "executionContext", "httpMethod", "httpStatusCode", "jobDeliveryDisposition", "outcome", "errorClass"];
for (const project of [platformProfileLogFields, platformProfileMetricLabels, platformProfileTraceFields]) {
  const reads: string[] = [];
  const observed = new Proxy({ ...facts }, { get(target, key, receiver) { reads.push(String(key)); return Reflect.get(target, key, receiver); } });
  deepEqual(project(classifiedProfile, observed as never), { error_class: "APP_FIXED" });
  deepEqual(reads, profileReadOrder, "classification preserves original property-read order/count");
}
const validClassRecord = { schema: "core/diagnostic-record/v1", code: "platform-contracts.registration-rejected", definitionVersion: 2,
  detail: { registration: "observability-profile", field: "errorClasses", condition: "member-invalid", index: 0, phase: "validation", effect: "rejected" } };
equal(parseDiagnosticRecord(platformContractClassificationDiagnosticDefinition, validClassRecord).ok, true);
for (const detail of [{ ...validClassRecord.detail, field: "name" }, { ...validClassRecord.detail, phase: "registration" },
  { ...validClassRecord.detail, condition: canary }, { ...validClassRecord.detail, index: 64 }, { ...validClassRecord.detail, submitted: canary }]) {
  equal(parseDiagnosticRecord(platformContractClassificationDiagnosticDefinition, { ...validClassRecord, detail }).ok, false);
}
function checked(result: { readonly ok: boolean; readonly error?: PlatformContractError }, registration: string, field: string, condition: string, phase = "validation"): void {
  equal(result.ok, false);
  if (!result.error) throw new Error("Expected contract failure.");
  const record = result.error.diagnosticRecord;
  equal(record?.schema, "core/diagnostic-record/v1");
  equal(record?.code, "platform-contracts.registration-rejected");
  equal(record?.definitionVersion, 1);
  deepEqual(record?.detail, { registration, field, condition, phase, effect: "rejected" });
  equal(parseDiagnosticRecord(platformContractRegistrationDiagnosticDefinition, record).ok, true);
  equal(JSON.stringify(record).includes(canary), false);
  equal(JSON.stringify(record).includes("defaultMessage"), false);
}
const route = (value: unknown) => validatePlatformRouteRegistration(value as PlatformRouteRegistration);
const job = (value: unknown) => validatePlatformJobRegistration(value as PlatformJobRegistration);
const profile = (value: unknown) => validatePlatformCapabilityObservabilityProfile(value as PlatformCapabilityObservabilityProfile);
const catalog = (value: unknown, existing: readonly PlatformDiagnosticCatalog[] = []) => validatePlatformDiagnosticCatalog(value as PlatformDiagnosticCatalog, existing);

equal(platformContractDiagnosticCatalog.owner, "platform-contracts");
checked(validatePlatformPermissionDeclaration(null as unknown as PlatformPermissionDeclaration), "permission", "declaration", "object-required");
for (const value of [null, 9, undefined]) checked(validatePlatformPermissionDeclaration({ permission: value } as unknown as PlatformPermissionDeclaration), "permission", "permission", "string-required");
checked(validatePlatformPermissionDeclaration({ permission: canary } as unknown as PlatformPermissionDeclaration), "permission", "permission", "invalid-format");
checked(platformAppId(canary), "identifier", "name", "invalid-format");

for (const [value, field, condition] of [
  [null, "declaration", "object-required"],
  [{ ...baseRoute, name: 0 }, "name", "string-required"],
  [{ ...baseRoute, name: canary }, "name", "invalid-format"],
  [{ ...baseRoute, method: 0 }, "method", "string-required"],
  [{ ...baseRoute, method: "OPTIONS" }, "method", "unsupported"],
  [{ ...baseRoute, path: 0 }, "path", "string-required"],
  [{ ...baseRoute, path: "relative" }, "path", "path-not-absolute"],
  [{ ...baseRoute, path: "/space here" }, "path", "path-whitespace"],
  [{ ...baseRoute, path: "/https://internal" }, "path", "path-url-scheme"],
  [{ ...baseRoute, path: "/admin/child" }, "path", "reserved-path"],
  [{ ...baseRoute, auth: null }, "auth", "object-required"],
  [{ ...baseRoute, auth: { kind: "public", permissions: [] } }, "auth.permissions", "public-permissions"],
  [{ ...baseRoute, auth: { kind: "private" } }, "auth.kind", "unsupported"],
  [{ ...baseRoute, auth: { kind: "authenticated", permissions: {} } }, "auth.permissions", "permissions-array-required"],
  [{ ...baseRoute, observability: null }, "observability", "object-required"],
  [{ ...baseRoute, observability: { kind: "profile", profile: canary } }, "observability.profile", "profile-name-invalid"],
  [{ ...baseRoute, observability: { kind: "other" } }, "observability.kind", "unsupported"],
  [{ ...baseRoute, observability: { ...requirement, reason: canary } }, "observability.reason", "opt-out-reason-invalid"],
  [{ ...baseRoute, observability: { ...requirement, justification: 0 } }, "observability.justification", "justification-string-required"],
  [{ ...baseRoute, observability: { ...requirement, justification: " " } }, "observability.justification", "justification-empty"],
  [{ ...baseRoute, observability: { ...requirement, justification: "x".repeat(281) } }, "observability.justification", "justification-too-long"],
  [{ ...baseRoute, tenant: "unsupported" }, "tenant", "unsupported"],
  [{ ...baseRoute, resourceAuthorization: null }, "resourceAuthorization", "object-required"],
  [{ ...baseRoute, resourceAuthorization: { permission: 1 } }, "resourceAuthorization.permission", "string-required"],
  [{ ...baseRoute, resourceAuthorization: { permission: "test:read", resolve: 1 } }, "resourceAuthorization.resolve", "function-required"],
  [{ ...baseRoute, tenant: "required" }, "auth", "public-controls"],
  [{ ...baseRoute, auth: { kind: "authenticated", permissions: [canary] } }, "permission", "invalid-format"],
  [{ ...baseRoute, auth: { kind: "authenticated" }, resourceAuthorization: { permission: canary, resolve() {} } }, "resourceAuthorization.permission", "invalid-format"],
  [{ ...baseRoute, validator: null }, "validator", "object-required"],
  [{ ...baseRoute, validator: { validate: 1 } }, "validator.validate", "function-required"],
  [{ ...baseRoute, validator: { validate() {}, explain: 1 } }, "validator.explain", "function-required"],
  [{ ...baseRoute, handler: null }, "handler", "object-required"],
  [{ ...baseRoute, handler: { handle: 1 } }, "handler.handle", "function-required"],
] as const) checked(route(value), "route", field, condition);
checked(validatePlatformRouteRegistration({ ...baseRoute, auth: { kind: "authenticated", permissions: ["test:read"] } } as unknown as PlatformRouteRegistration, { declaredPermissions: [] }), "route", "permission", "undeclared-permission");
checked(validatePlatformRouteRegistration({ ...baseRoute, auth: { kind: "authenticated" }, resourceAuthorization: { permission: "test:read", resolve() {} } } as unknown as PlatformRouteRegistration, { declaredPermissions: [] }), "route", "resourceAuthorization.permission", "undeclared-permission");

for (const [value, field, condition] of [
  [null, "declaration", "object-required"],
  [{ ...baseJob, name: 1 }, "name", "string-required"],
  [{ ...baseJob, messageType: canary }, "messageType", "invalid-format"],
  [{ ...baseJob, messageType: 1 }, "messageType", "string-required"],
  [{ ...baseJob, observability: {} }, "observability.kind", "unsupported"],
  [{ ...baseJob, validator: {} }, "validator.validate", "function-required"],
  [{ ...baseJob, validator: { validate() {} } }, "validator.explain", "function-required"],
  [{ ...baseJob, handler: {} }, "handler.handle", "function-required"],
] as const) checked(job(value), "job", field, condition);

for (const [value, field, condition] of [
  [null, "declaration", "object-required"],
  [{ ...baseProfile, name: canary }, "name", "invalid-format"],
  [{ ...baseProfile, name: null }, "name", "string-required"],
  [{ ...baseProfile, capability: canary }, "capability", "invalid-format"],
  [{ ...baseProfile, capability: null }, "capability", "string-required"],
  [{ ...baseProfile, action: canary }, "action", "unsupported"],
  [{ ...baseProfile, signals: {} }, "signals", "array-required"],
  [{ ...baseProfile, signals: [] }, "signals", "array-empty"],
  [{ ...baseProfile, signals: [canary] }, "signals", "member-invalid"],
  [{ ...baseProfile, signals: ["trace", "trace"] }, "signals", "duplicate-member"],
  [{ ...baseProfile, logFieldNames: {} }, "logFieldNames", "array-required"],
  [{ ...baseProfile, logFieldNames: [] }, "logFieldNames", "array-empty"],
  [{ ...baseProfile, logFieldNames: [canary] }, "logFieldNames", "member-invalid"],
  [{ ...baseProfile, logFieldNames: ["outcome", "outcome"] }, "logFieldNames", "duplicate-member"],
  [{ ...baseProfile, metricDimensionFieldNames: [canary] }, "metricDimensionFieldNames", "member-invalid"],
  [{ ...baseProfile, traceAttributeNames: [canary] }, "traceAttributeNames", "member-invalid"],
  [{ ...baseProfile, nfrObjectives: {} }, "nfrObjectives", "array-required"],
  [{ ...baseProfile, nfrObjectives: [] }, "nfrObjectives", "array-empty"],
  [{ ...baseProfile, nfrObjectives: [null] }, "nfrObjectives", "object-required"],
  [{ ...baseProfile, nfrObjectives: [{ nfrClass: canary }] }, "nfrObjectives.nfrClass", "nfr-class-invalid"],
  [{ ...baseProfile, nfrObjectives: [{ nfrClass: "health_probe", measurement: canary }] }, "nfrObjectives.measurement", "measurement-invalid"],
  [{ ...baseProfile, nfrObjectives: [{ nfrClass: "health_probe", measurement: "queue_wait_latency" }] }, "nfrObjectives.measurement", "measurement-incompatible"],
  [{ ...baseProfile, nfrObjectives: [{ nfrClass: "health_probe", measurement: "health_check_latency" }, { nfrClass: "health_probe", measurement: "health_check_latency" }] }, "nfrObjectives", "duplicate-member"],
  [{ ...baseProfile, signals: ["trace"], metricDimensionFieldNames: ["outcome"] }, "signals", "signal-required"],
  [{ ...baseProfile, signals: ["trace"], logFieldNames: ["outcome"] }, "logFieldNames", "signal-required"],
  [{ ...baseProfile, signals: ["metric"], traceAttributeNames: ["outcome"] }, "traceAttributeNames", "signal-required"],
] as const) checked(profile(value), "observability-profile", field, condition);

const definition = platformContractRegistrationDiagnosticDefinition;
for (const [value, field, condition, phase] of [
  [null, "declaration", "object-required", "structure"],
  [[], "declaration", "plain-object-required", "structure"],
  [{ owner: "test" }, "declaration", "exact-fields-required", "structure"],
  [Object.defineProperty({ definitions: [definition] }, "owner", { get() { throw new Error(canary); }, enumerable: true }), "declaration", "data-fields-required", "structure"],
  [{ owner: 0, definitions: [definition] }, "owner", "string-required", "structure"],
  [{ owner: "a".repeat(129), definitions: [definition] }, "owner", "owner-too-long", "structure"],
  [{ owner: canary, definitions: [definition] }, "owner", "invalid-format", "structure"],
  [{ owner: "platform-contracts", definitions: {} }, "definitions", "array-required", "structure"],
  [{ owner: "platform-contracts", definitions: [] }, "definitions", "array-empty", "structure"],
  [{ owner: "platform-contracts", definitions: Array(257).fill(definition) }, "definitions", "definitions-too-many", "structure"],
  [{ owner: "platform-contracts", definitions: Object.setPrototypeOf([definition], null) }, "definitions", "plain-array-required", "structure"],
  [{ owner: "platform-contracts", definitions: Object.assign([definition], { extra: true }) }, "definitions", "dense-array-required", "structure"],
  [{ owner: "platform-contracts", definitions: Array(1) }, "definitions", "dense-array-required", "structure"],
  [{ owner: "platform-contracts", definitions: [null] }, "definitions", "definition-invalid", "definitions"],
  [{ owner: "other", definitions: [definition] }, "definitions", "ownership-mismatch", "definitions"],
  [{ owner: "platform-contracts", definitions: [definition, definition] }, "identity", "duplicate-identity", "conflicts"],
] as const) checked(catalog(value), "diagnostic-catalog", field, condition, phase);
checked(catalog(platformContractDiagnosticCatalog, [platformContractDiagnosticCatalog]), "diagnostic-catalog", "owner", "duplicate-owner", "conflicts");
checked(catalog(platformContractDiagnosticCatalog, [{ owner: "other", definitions: [definition] }]), "diagnostic-catalog", "identity", "duplicate-identity", "conflicts");
checked(catalog(new Proxy({}, { getPrototypeOf() { throw new Error(canary); } })), "diagnostic-catalog", "declaration", "inspection-threw", "structure");
checked(catalog(new Proxy({ owner: "platform-contracts", definitions: [definition] }, { get(target, key, receiver) { if (key === "toJSON") throw new Error(canary); return Reflect.get(target, key, receiver); } })), "diagnostic-catalog", "declaration", "inspection-threw", "snapshot");
checked(catalog(platformContractDiagnosticCatalog, [new Proxy({ owner: "other", definitions: [] }, { get() { throw new Error(canary); } })]), "diagnostic-catalog", "declaration", "inspection-threw", "conflicts");
equal(catalog(platformContractDiagnosticCatalog).ok, true);

// Original first failure and getter/callback effects remain observable.
let laterReads = 0;
const invalidEarly = { ...baseRoute, method: "UNSUPPORTED", get path() { laterReads++; throw new Error(canary); } };
checked(route(invalidEarly), "route", "method", "unsupported");
equal(laterReads, 0);
let validateReads = 0, explainReads = 0;
const validator = { get validate() { validateReads++; return 0; }, get explain() { explainReads++; throw new Error(canary); } };
checked(route({ ...baseRoute, validator }), "route", "validator.validate", "function-required");
equal(validateReads, 1); equal(explainReads, 0);
let kindReads = 0, permissionReads = 0;
checked(route({ ...baseRoute, auth: { get kind() { kindReads++; return "unsupported"; }, get permissions() { permissionReads++; throw new Error(canary); } } }), "route", "auth.kind", "unsupported");
equal(kindReads, 2); equal(permissionReads, 0);
const thrown = new Error(canary);
throws(() => route({ ...baseRoute, get method() { throw thrown; } }), (error) => error === thrown);
const minimalValidator = { validate() { return true; }, explain() { return { valid: true, issues: [] }; }, get diagnose() { throw new Error(canary); } };
equal(route({ ...baseRoute, validator: minimalValidator }).ok, true);
equal(route({ ...baseRoute, validator: Object.defineProperties([], Object.getOwnPropertyDescriptors(minimalValidator)) }).ok, true);
equal(route(Object.assign([], baseRoute)).ok, true);
equal(route({ ...baseRoute, handler: Object.assign([], { handle() {} }) }).ok, true);
equal(route({ ...baseRoute, observability: Object.assign([], requirement) }).ok, true);
equal(profile(Object.assign([], baseProfile)).ok, true);
equal(profile({ ...baseProfile, signals: Array(1) }).ok, true, "Retain the existing sparse-array every/Set policy");
let memberReads = 0;
const signals = [canary, "trace"];
Object.defineProperty(signals, "1", { enumerable: true, get() { memberReads++; throw new Error(canary); } });
checked(profile({ ...baseProfile, signals }), "observability-profile", "signals", "member-invalid");
equal(memberReads, 0, "A failed first member must not cause a later item read to diagnose duplicates");
let justificationReads = 0;
checked(route({ ...baseRoute, observability: { kind: "opt_out", reason: canary, get justification() { justificationReads++; throw new Error(canary); } } }), "route", "observability.reason", "opt-out-reason-invalid");
equal(justificationReads, 0);

const rejected = route({ ...baseRoute, method: "OPTIONS" });
if (rejected.ok) throw new Error("Expected rejected method");
const { diagnosticRecord: _record, ...legacy } = rejected.error;
deepEqual(legacy, { code: "PLATFORM_CONTRACT_MALFORMED_ROUTE", defaultMessage: "Route method must be a supported HTTP method.", details: { method: "OPTIONS" } });
for (const bad of [null, { ...definition, detail: {} }, { schema: "core/diagnostic-record/v1", code: "unknown.code", definitionVersion: 1, detail: {} }, { ...rejected.error.diagnosticRecord, detail: { arbitrary: canary } }]) equal(parseDiagnosticRecord(definition, bad).ok, false);
