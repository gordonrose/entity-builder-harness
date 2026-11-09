import { deepEqual, equal, throws } from "node:assert/strict";
import { parseDiagnosticRecord, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { Permission } from "@kanbien/core/authz";
import type { QueueMessageType } from "@kanbien/core/queues";
import {
  definePlatformApp,
  duplicatePlatformRegistration,
  featureFlagName,
  fixedFeatureFlagReader,
  platformReadinessObservationEvent,
  platformReadinessStates,
  platformOperationalEventDiagnosticDefinition,
  platformOperationalBoundaryDiagnosticDefinition,
  platformOperationalEventDiagnosticRecord,
  platformOperationalBoundaryDiagnosticRecord,
  type FeatureFlagName,
  type PlatformOperationalDiagnosticOptions,
  type PlatformOperationalDiagnosticContext,
  isPlatformCapabilityAction,
  isPlatformExecutionContext,
  isPlatformInteractionSource,
  isPlatformJobDeliveryDisposition,
  isPlatformOperationalOutcome,
  platformAppId,
  platformCapabilityActions,
  platformCapabilityName,
  platformExecutionContexts,
  platformInteractionSources,
  platformJobDeliveryDispositions,
  platformOperationalFieldNames,
  platformOperationalOutcomes,
  platformJobName,
  platformObservabilityProfileName,
  platformProfileAllowsSignal,
  platformProfileLogFields,
  platformProfileMeasuresLatency,
  platformProfileMetricLabels,
  platformProfileTraceFields,
  platformRouteName,
  validatePlatformCapabilityObservabilityProfile,
  validatePlatformJobRegistration,
  validatePlatformPermissionDeclaration,
  validatePlatformRouteRegistration,
  type PlatformContractErrorCode,
} from "../../src/index";

function expectContractError(
  result: ReturnType<typeof validatePlatformRouteRegistration> | ReturnType<typeof validatePlatformJobRegistration>,
  code: PlatformContractErrorCode,
): void {
  equal(result.ok, false);
  if (result.ok) {
    throw new Error(`Expected platform contract error ${code}.`);
  }
  equal(result.error.code, code);
}

async function main(): Promise<void> {
  const appId = platformAppId("crm");
  equal(appId.ok, true);
  if (!appId.ok) {
    throw new Error("Expected platform app id to be valid.");
  }
  equal(appId.value, "crm");

  const invalidAppId = platformAppId("CRM App");
  equal(invalidAppId.ok, false);
  if (invalidAppId.ok) {
    throw new Error("Expected platform app id to be invalid.");
  }
  equal(invalidAppId.error.code, "PLATFORM_CONTRACT_INVALID_NAME");

  const routeName = platformRouteName("crm.deals.show");
  equal(routeName.ok, true);
  if (!routeName.ok) {
    throw new Error("Expected route name to be valid.");
  }

  const jobName = platformJobName("crm.deals.recalculate-score");
  equal(jobName.ok, true);
  if (!jobName.ok) {
    throw new Error("Expected job name to be valid.");
  }

  const capabilityName = platformCapabilityName("crm.deal.export"); // Validate the stable app-owned capability identity used by the observability nomenclature.
  const observabilityProfileName = platformObservabilityProfileName("crm.deal.export"); // Validate one app-owned observability-profile identity.
  equal(capabilityName.ok, true); // Prove the capability name accepts the safe dotted-name syntax used by other platform declarations.
  if (!capabilityName.ok || !observabilityProfileName.ok) { // Narrow both checked names before reading them in later declarations.
    throw new Error("Expected platform capability name to be valid."); // Fail the runtime contract test if the intended identity is rejected.
  }
  equal(capabilityName.value, "crm.deal.export"); // Prove branding preserves the declared runtime value.
  equal(platformCapabilityName("CRM Deal Export").ok, false); // Reject a malformed capability name rather than accepting a free-form label.
  const validObservabilityProfile = {
    name: observabilityProfileName.value,
    capability: capabilityName.value,
    action: "export" as const,
    signals: ["operational_log", "metric", "trace"] as const,
    logFieldNames: ["capability", "action", "outcome"] as const,
    metricDimensionFieldNames: ["capability", "action", "outcome"] as const,
    traceAttributeNames: ["capability", "action", "outcome"] as const,
    nfrObjectives: [{ nfrClass: "async_completion" as const, measurement: "job_execution_latency" as const }],
  };
  deepEqual(validatePlatformCapabilityObservabilityProfile(validObservabilityProfile), { ok: true, value: undefined });
  equal(validatePlatformCapabilityObservabilityProfile({ ...validObservabilityProfile, signals: ["trace"], nfrObjectives: validObservabilityProfile.nfrObjectives }).ok, false);
  const failingWorkerNomenclature = {
    capability: capabilityName.value,
    action: "export" as const,
    executionContext: "worker" as const,
    jobDeliveryDisposition: "retry_scheduled" as const,
    outcome: "failed" as const,
    errorClass: "PLATFORM_WORKER_HANDLER_FAILED",
  };
  equal(platformProfileAllowsSignal(validObservabilityProfile, "metric"), true);
  equal(platformProfileAllowsSignal(validObservabilityProfile, "trace"), true);
  equal(platformProfileMeasuresLatency(validObservabilityProfile, "job_execution_latency"), true);
  equal(platformProfileMeasuresLatency(validObservabilityProfile, "queue_wait_latency"), false);
  deepEqual(platformProfileLogFields(validObservabilityProfile, failingWorkerNomenclature), {
    capability: "crm.deal.export",
    action: "export",
    outcome: "failed",
  });
  deepEqual(platformProfileMetricLabels(validObservabilityProfile, failingWorkerNomenclature), {
    capability: "crm.deal.export",
    action: "export",
    outcome: "failed",
  });
  deepEqual(platformProfileTraceFields(validObservabilityProfile, failingWorkerNomenclature), {
    capability: "crm.deal.export",
    action: "export",
    outcome: "failed",
  });
  equal(platformCapabilityActions.includes("export"), true); // Prove the controlled business-action list includes a supported action.
  equal(isPlatformCapabilityAction("export"), true); // Prove the action guard accepts a controlled action.
  equal(isPlatformCapabilityAction("edit"), false); // Prove the action guard rejects an unapproved synonym.
  equal(platformInteractionSources.includes("voice"), true); // Prove a bounded voice interaction source is part of the documented vocabulary.
  equal(isPlatformInteractionSource("voice"), true); // Prove the interaction-source guard accepts a known value.
  equal(isPlatformInteractionSource("browser-extension"), false); // Prove the interaction-source guard rejects an unreviewed value.
  deepEqual(platformExecutionContexts, ["server", "worker", "scheduler", "cli"]); // Prove execution context remains separate from interaction source.
  equal(isPlatformExecutionContext("worker"), true); // Prove the execution-context guard accepts a known runtime location.
  equal(isPlatformExecutionContext("voice"), false); // Prove a source channel cannot be mistaken for a runtime location.
  deepEqual(platformOperationalOutcomes, ["accepted", "succeeded", "denied", "rejected", "failed", "cancelled", "timed_out"]); // Prove the logical-outcome vocabulary is explicit and ordered.
  equal(isPlatformOperationalOutcome("denied"), true); // Prove the outcome guard accepts a policy denial.
  equal(isPlatformOperationalOutcome("error"), false); // Prove vague transport-oriented outcome words are not accepted as canonical vocabulary.
  deepEqual(platformJobDeliveryDispositions, ["succeeded", "retry_scheduled", "dead_lettered"]); // Prove worker delivery disposition is independent of business outcome.
  equal(isPlatformJobDeliveryDisposition("retry_scheduled"), true); // Prove the delivery-disposition guard accepts a scheduled retry.
  equal(isPlatformJobDeliveryDisposition("retry"), false); // Prove the legacy shorthand is not the future canonical emitted value.
  deepEqual(platformOperationalFieldNames, { // Prove every future signal profile uses the one canonical emitted field-name map.
    capability: "capability", // Confirm the stable capability field name.
    action: "action", // Confirm the controlled business-action field name.
    actorType: "actor_type", // Confirm the bounded actor-category field name.
    interactionSource: "interaction_source", // Confirm the initiation-channel field name.
    executionContext: "execution_context", // Confirm the runtime-location field name.
    httpMethod: "http_method", // Confirm the HTTP-method field name.
    httpStatusCode: "http_status_code", // Confirm the numeric HTTP-status field name.
    jobDeliveryDisposition: "job_delivery_disposition", // Confirm the worker-delivery field name.
    outcome: "outcome", // Confirm the logical-result field name.
    errorClass: "error_class", // Confirm the bounded error-class field name.
  }); // Finish the canonical mapping assertion.

  const flagName = featureFlagName("crm.deals.bulk-import");
  equal(flagName.ok, true);
  if (!flagName.ok) {
    throw new Error("Expected feature flag name to be valid.");
  }

  const flags = fixedFeatureFlagReader({ [flagName.value]: true });
  equal(await flags.isEnabled(flagName.value), true);

  const mutableFlags = { "crm.deals.bulk-import": false };
  const snapshotFlags = fixedFeatureFlagReader(mutableFlags, true);
  mutableFlags["crm.deals.bulk-import"] = true;
  equal(await snapshotFlags.isEnabled(flagName.value), false);

  const dealReadPermission: Permission = "crm.deal:read";
  deepEqual(validatePlatformPermissionDeclaration({ permission: dealReadPermission }), { ok: true, value: undefined });
  expectContractError(
    validatePlatformPermissionDeclaration({ permission: "deal read" as never }),
    "PLATFORM_CONTRACT_MALFORMED_PERMISSION",
  );

  const validRoute = {
    name: routeName.value,
    method: "GET",
    path: "/deals/:id",
    auth: { kind: "authenticated", permissions: [dealReadPermission] },
    observability: { kind: "profile" as const, profile: observabilityProfileName.value },
    handler: { handle: () => ({ status: 200 }) },
  } as const;
  deepEqual(validatePlatformRouteRegistration(validRoute, { declaredPermissions: [dealReadPermission] }), {
    ok: true,
    value: undefined,
  });
  const tenantAndResourceRoute = {
    ...validRoute,
    tenant: "required" as const,
    resourceAuthorization: {
      permission: dealReadPermission,
      resolve: () => ({ kind: "authorize" as const, facts: { source: "contract-test" } }),
    },
  };
  deepEqual(validatePlatformRouteRegistration(tenantAndResourceRoute, { declaredPermissions: [dealReadPermission] }), {
    ok: true,
    value: undefined,
  });
  expectContractError(
    validatePlatformRouteRegistration({ ...validRoute, auth: { kind: "public" }, tenant: "required" }, { declaredPermissions: [dealReadPermission] }),
    "PLATFORM_CONTRACT_MALFORMED_ROUTE",
  );
  expectContractError(
    validatePlatformRouteRegistration({
      ...validRoute,
      resourceAuthorization: {
        permission: "record:read" as never,
        resolve: () => ({ kind: "authorize" as const }),
      },
    }, { declaredPermissions: [dealReadPermission] }),
    "PLATFORM_CONTRACT_UNKNOWN_PERMISSION",
  );
  expectContractError(
    validatePlatformRouteRegistration({ ...validRoute, path: "/readyz" }, { declaredPermissions: [dealReadPermission] }),
    "PLATFORM_CONTRACT_RESERVED_PATH",
  );
  expectContractError(
    validatePlatformRouteRegistration(validRoute, { declaredPermissions: [] }),
    "PLATFORM_CONTRACT_UNKNOWN_PERMISSION",
  );
  expectContractError(
    validatePlatformRouteRegistration({ ...validRoute, method: "TRACE" as never }, { declaredPermissions: [dealReadPermission] }),
    "PLATFORM_CONTRACT_MALFORMED_ROUTE",
  );
  expectContractError(
    validatePlatformRouteRegistration({ ...validRoute, observability: undefined as never }, { declaredPermissions: [dealReadPermission] }),
    "PLATFORM_CONTRACT_MALFORMED_ROUTE",
  );
  expectContractError(
    validatePlatformRouteRegistration({
      ...validRoute,
      observability: { kind: "opt_out", reason: "non_user_workload_path", justification: "" } as never,
    }, { declaredPermissions: [dealReadPermission] }),
    "PLATFORM_CONTRACT_MALFORMED_ROUTE",
  );

  const validJob = {
    name: jobName.value,
    messageType: "crm.deals.recalculate-score" as QueueMessageType,
    observability: { kind: "profile" as const, profile: observabilityProfileName.value },
    handler: { handle: () => undefined },
  };
  deepEqual(validatePlatformJobRegistration(validJob), { ok: true, value: undefined });
  expectContractError(
    validatePlatformJobRegistration({ ...validJob, messageType: "CRM Deals" as never }),
    "PLATFORM_CONTRACT_MALFORMED_JOB",
  );
  expectContractError(
    validatePlatformJobRegistration({ ...validJob, observability: undefined as never }),
    "PLATFORM_CONTRACT_MALFORMED_JOB",
  );

  const duplicateRoute = duplicatePlatformRegistration("route", routeName.value);
  equal(duplicateRoute.code, "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION");

  const app = definePlatformApp({
    id: appId.value,
    name: "CRM",
    version: "0.0.0",
    mount(registry) {
      if (!routeName.ok) {
        throw new Error("Expected route name to be valid.");
      }

      registry.registerPermission({ permission: dealReadPermission });
      registry.registerObservabilityProfile(validObservabilityProfile);
      registry.registerRoute({
        name: routeName.value,
        method: "GET",
        path: "/deals/:id",
        auth: { kind: "authenticated", permissions: [dealReadPermission] },
        observability: { kind: "profile", profile: observabilityProfileName.value },
        handler: { handle: () => ({ status: 200 }) },
      });
    },
  });

  const registeredRoutes: unknown[] = [];
  await app.mount(
    {
      registerPermission() {
        return { ok: true, value: undefined };
      },
      registerDiagnosticCatalog() { return { ok: true, value: undefined }; },
      registerRoute(route) {
        registeredRoutes.push(route);
        return { ok: true, value: undefined };
      },
      registerJob() {
        return { ok: true, value: undefined };
      },
      registerObservabilityProfile() {
        return { ok: true, value: undefined };
      },
      registerHealthCheck() {
        return { ok: true, value: undefined };
      },
      registerConfigSchema() {
        return { ok: true, value: undefined };
      },
    },
    {
      logger: { write: () => undefined },
      metrics: { record: () => undefined },
      config: { get: () => undefined },
      flags,
      clock: { now: () => new Date("2026-07-08T00:00:00.000Z") },
    },
  );
  deepEqual(registeredRoutes.map((route) => (route as { readonly path: string }).path), ["/deals/:id"]);
  await operationalContractsDiagnostics();
}

async function operationalContractsDiagnostics(): Promise<void> {
  const base = { type: "dependency.readiness-observed" as const, target: "fixture-target", scope: "fixture-scope", workload: "fixture-workload", dependency: "fixture-dependency", readiness: "ready" as const, observedAt: "2026-10-31T00:00:00.000Z" };
  const records: DiagnosticRecord[] = [], contexts: PlatformOperationalDiagnosticContext[] = [];
  const getRecords = (): readonly DiagnosticRecord[] => records;
  const options: PlatformOperationalDiagnosticOptions = { onDiagnostic(record, context) { equal(this, options); records.push(record); contexts.push(context); } };
  const literal = (code: string, detail: unknown): DiagnosticRecord => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
  const rejected = (field: string, condition: string, ordinal?: number): DiagnosticRecord => literal("platform-contracts.operational-event-rejected", { operation: "readiness-event", field, condition, phase: "validation", effect: "predicate-rejected", ...(ordinal === undefined ? {} : { ordinal }) });
  const boundary = (operation: string, phase: string, field: string, effect: string): DiagnosticRecord => literal("platform-contracts.operational-boundary-failed", { operation, phase, field, reason: "threw", effect });
  const validationLiteral = rejected("keys", "unknown-field", 2), boundaryLiteral = boundary("fixed-feature-flags", "snapshot", "flags", "reader-not-produced");
  deepEqual(platformOperationalEventDiagnosticRecord({ field: "keys", condition: "unknown-field", ordinal: 2 }), validationLiteral);
  deepEqual(platformOperationalBoundaryDiagnosticRecord({ operation: "fixed-feature-flags", phase: "snapshot", field: "flags", effect: "reader-not-produced" }), boundaryLiteral);
  for (const [definition, value] of [[platformOperationalEventDiagnosticDefinition, validationLiteral], [platformOperationalBoundaryDiagnosticDefinition, boundaryLiteral]] as const) {
    equal(parseDiagnosticRecord<unknown>(definition, value).ok, true);
    for (const invalid of [{ ...value, definitionVersion: 2 }, { ...value, detail: { ...(value.detail as object), private: "PRIVATE-contract-canary" } }, { ...value, detail: { ...(value.detail as object), effect: "committed" } }]) equal(parseDiagnosticRecord<unknown>(definition, invalid).ok, false);
  }
  equal(parseDiagnosticRecord(platformOperationalEventDiagnosticDefinition, rejected("keys", "unknown-field", -1)).ok, false);
  for (const [value, field, condition, ordinal] of [
    [0, "event", "object-required"], [null, "event", "null-rejected"], [[], "event", "array-rejected"],
    [{ ...base, privateValue: "PRIVATE-contract-canary" }, "keys", "unknown-field", 7], [{ ...base, type: "PRIVATE-contract-canary" }, "type", "unsupported"],
    ...(["target", "scope", "workload", "dependency"] as const).flatMap((field) => [[{ ...base, [field]: 7 }, field, "string-required"], [{ ...base, [field]: "PRIVATE-contract-canary" }, field, "invalid-format"]]),
    [{ ...base, readiness: 7 }, "readiness", "string-required"], [{ ...base, readiness: "PRIVATE-contract-canary" }, "readiness", "unsupported"],
    [{ ...base, observedAt: 7 }, "observed-at", "string-required"], [{ ...base, observedAt: "PRIVATE-contract-canary" }, "observed-at", "invalid-format"], [{ ...base, observedAt: "2026-99-99T00:00:00Z" }, "observed-at", "date-parse-rejected"],
    [{ ...base, diagnosticCode: "fixture.failure" }, "diagnostic-code", "unexpected-present"], [{ ...base, readiness: "not-ready" }, "diagnostic-code", "string-required"],
    [{ ...base, readiness: "not-ready", diagnosticCode: 7 }, "diagnostic-code", "string-required"], [{ ...base, readiness: "not-ready", diagnosticCode: "PRIVATE-contract-canary" }, "diagnostic-code", "invalid-format"],
  ] as readonly (readonly [unknown, string, string, number?])[]) {
    records.length = contexts.length = 0;
    const checked = platformReadinessObservationEvent(value, options);
    equal(checked.ok, false); if (checked.ok) throw new Error("Expected existing event rejection");
    equal(checked.error.code, "PLATFORM_OPERATIONAL_EVENT_INVALID"); equal(checked.error.defaultMessage, "Operational event does not match the closed readiness observation envelope.");
    deepEqual(checked.error.diagnosticRecord, rejected(field, condition, ordinal)); deepEqual(getRecords(), [checked.error.diagnosticRecord]);
    deepEqual(contexts, [{ operation: "readiness-event", phase: "validation", evidence: "owned" }]);
    equal(JSON.stringify(checked).includes("PRIVATE-"), false);
  }
  records.length = 0;
  deepEqual(platformReadinessObservationEvent(base, options), { ok: true, value: base });
  const inherited = Object.create(base); inherited[Symbol("PRIVATE-contract-canary")] = "PRIVATE-contract-canary";
  Object.defineProperty(inherited, "PRIVATE-contract-canary", { value: true, enumerable: false });
  deepEqual(platformReadinessObservationEvent(inherited, options), { ok: true, value: base });
  equal(platformReadinessObservationEvent({ ...base, observedAt: "2026-02-30T00:00:00Z" }, options).ok, true, "existing Date.parse rollover acceptance is not an IANA/calendar policy");
  equal(platformReadinessObservationEvent({ ...base, readiness: "not-ready", diagnosticCode: "fixture.failure" }, options).ok, true);
  deepEqual(getRecords(), []);
  const reads: string[] = [];
  const readInput = Object.fromEntries(Object.entries(base).map(([key, value]) => [key, value]));
  for (const [key, value] of Object.entries(base)) Object.defineProperty(readInput, key, { enumerable: true, get() { reads.push(key); return value; } });
  platformReadinessObservationEvent(readInput);
  deepEqual(reads, ["type", "target", "scope", "workload", "dependency", "readiness", "observedAt", "readiness", "readiness", "target", "scope", "workload", "dependency", "readiness", "observedAt"]);
  let readinessReads = 0;
  const changing = platformReadinessObservationEvent({ ...base, get readiness() { return ++readinessReads === 1 ? "ready" : readinessReads === 2 ? "not-ready" : readinessReads === 3 ? "ready" : "not-ready"; } });
  equal(changing.ok, true); equal(readinessReads, 4); if (changing.ok) equal(changing.value.readiness, "not-ready");
  const originalKeys = Object.keys;
  try {
    for (const [aggregate, visit, expected] of [[false, false, rejected("keys", "predicate-rejected")], [false, true, rejected("keys", "unknown-field", 1)], [true, true, undefined]] as const) {
      Object.keys = ((value: object) => value === base ? Object.assign([], { every(callback: (key: string, index: number) => unknown) { if (visit) { callback("type", 999); callback("PRIVATE-contract-canary", 999); } return aggregate; } }) : originalKeys(value)) as typeof Object.keys;
      records.length = 0;
      equal(platformReadinessObservationEvent(base, options).ok, aggregate);
      deepEqual(getRecords(), expected === undefined ? [] : [expected]);
    }
  } finally { Object.keys = originalKeys; }
  const source9: DiagnosticRecord[] = Array.from({ length: 9 }, (_, ordinal) => literal("core.persistence.in-memory-boundary-failed", { operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal }));
  const raw = Object.freeze(Object.assign(new Error("PRIVATE-contract-canary"), { diagnosticRecord: source9[0], relatedDiagnosticRecords: source9.slice(1) }));
  try {
    for (const getter of [false, true]) {
      const order: string[] = [];
      const selectedKeys = Object.defineProperty([], "every", { get() { order.push("selection"); if (getter) throw raw; return function(this: unknown) { equal(this, selectedKeys); order.push("invocation"); throw raw; }; } });
      Object.keys = ((value: object) => value === base ? (order.push("enumeration"), selectedKeys) : originalKeys(value)) as typeof Object.keys;
      records.length = 0;
      throws(() => platformReadinessObservationEvent(base, options), (error) => error === raw);
      deepEqual(getRecords(), [boundary("readiness-event", getter ? "key-traversal-selection" : "key-traversal", "keys", "event-not-produced"), ...source9]);
      deepEqual(order, getter ? ["enumeration", "selection"] : ["enumeration", "selection", "invocation"]);
    }
  } finally { Object.keys = originalKeys; }
  for (const [value, phase, field] of [
    [new Proxy(base, { ownKeys() { throw raw; } }), "key-enumeration", "keys"],
    [{ ...base, get target() { throw raw; } }, "field-projection", "target"],
  ] as const) {
    records.length = contexts.length = 0;
    throws(() => platformReadinessObservationEvent(value, options), (error) => error === raw);
    deepEqual(getRecords(), [boundary("readiness-event", phase, field, "event-not-produced"), ...source9]);
    equal(contexts[0]?.evidence, "owned"); equal(contexts.slice(1).every((context) => context.evidence === "source" && context.phase === phase), true);
  }
  let resultReads = 0;
  records.length = 0;
  throws(() => platformReadinessObservationEvent({ ...base, get target() { if (++resultReads === 2) throw raw; return base.target; } }, options), (error) => error === raw);
  equal(resultReads, 2); deepEqual(getRecords(), [boundary("readiness-event", "result-projection", "target", "event-not-produced"), ...source9]);
  const originalParse = Date.parse;
  try {
    let parseCalls = 0;
    Date.parse = function(value) { equal(this, Date); parseCalls++; throw raw; };
    records.length = 0;
    equal(platformReadinessObservationEvent({ ...base, observedAt: "invalid" }, options).ok, false); equal(parseCalls, 0);
    records.length = 0; throws(() => platformReadinessObservationEvent(base, options), (error) => error === raw);
    equal(parseCalls, 1); deepEqual(getRecords(), [boundary("readiness-event", "time-parsing", "observed-at", "event-not-produced"), ...source9]);
  } finally { Date.parse = originalParse; }
  const mutableStates = platformReadinessStates as unknown as { includes(value: string): boolean };
  const originalIncludes = mutableStates.includes, originalTest = RegExp.prototype.test;
  try {
    mutableStates.includes = function () { equal(this, platformReadinessStates); throw raw; };
    records.length = 0; throws(() => platformReadinessObservationEvent(base, options), (error) => error === raw);
    deepEqual(getRecords(), [boundary("readiness-event", "field-predicate", "readiness", "event-not-produced"), ...source9]);
    mutableStates.includes = originalIncludes;
    RegExp.prototype.test = function(value) { if (value === base.target) throw raw; return Reflect.apply(originalTest, this, [value]); };
    records.length = 0; throws(() => platformReadinessObservationEvent(base, options), (error) => error === raw);
    deepEqual(getRecords(), [boundary("readiness-event", "field-predicate", "target", "event-not-produced"), ...source9]);
  } finally { mutableStates.includes = originalIncludes; RegExp.prototype.test = originalTest; }
  const flag = "fixture.flag" as FeatureFlagName, symbol = Symbol("PRIVATE-contract-canary");
  let flagReads = 0;
  const flagInput = { get [flag]() { flagReads++; return false; }, [symbol]: true };
  const reader = fixedFeatureFlagReader(flagInput, true, options);
  equal(flagReads, 1); equal(reader.isEnabled(flag), false); equal(flagReads, 1); equal(reader.isEnabled(symbol as unknown as FeatureFlagName), true);
  equal(reader.isEnabled("missing" as FeatureFlagName), true);
  const legacyNullish = fixedFeatureFlagReader({ [flag]: null } as unknown as Readonly<Record<string, boolean>>, "legacy-default" as unknown as boolean);
  equal(legacyNullish.isEnabled(flag), "legacy-default");
  equal(typeof reader.isEnabled("toString" as FeatureFlagName), "function", "legacy inherited lookup is not a new boolean validation policy");
  const silentContext = new Proxy({}, { get() { throw raw; } }); equal(reader.isEnabled(flag, silentContext), false);
  for (const thrown of [raw, Object.freeze(new Error("PRIVATE-contract-canary")), "PRIVATE-contract-canary", null]) {
    records.length = 0;
    throws(() => fixedFeatureFlagReader({ get [flag](): boolean { throw thrown; } }, false, options), (error) => error === thrown);
    deepEqual(getRecords().slice(0, 1), [boundary("fixed-feature-flags", "snapshot", "flags", "reader-not-produced")]);
    equal(JSON.stringify(getRecords()).includes("PRIVATE-"), false);
    records.length = 0;
    const badName = { [Symbol.toPrimitive]() { throw thrown; } } as unknown as FeatureFlagName;
    throws(() => reader.isEnabled(badName), (error) => error === thrown);
    deepEqual(getRecords().slice(0, 1), [boundary("fixed-feature-flags", "read", "value", "value-not-produced")]);
    if (thrown === raw) deepEqual(getRecords().slice(1), source9);
  }
  let evidenceReads = 0;
  const inaccessible = Object.defineProperty({}, "diagnosticRecord", { get() { evidenceReads++; throw raw; } });
  for (const [thrown, reason] of [[inaccessible, "evidence-inaccessible"], [{ diagnosticRecord: { ...source9[0], code: "private.unselected" } }, undefined], [{ diagnosticRecord: { ...source9[0], detail: { private: "PRIVATE-contract-canary" } } }, "evidence-rejected"]] as const) {
    records.length = 0;
    throws(() => fixedFeatureFlagReader({ get [flag](): boolean { throw thrown; } }, false, options), (error) => error === thrown);
    deepEqual(getRecords(), [boundary("fixed-feature-flags", "snapshot", "flags", "reader-not-produced"), ...(reason === undefined ? [] : [literal("core.diagnostics.processing-failed", { reason })])]);
  }
  equal(evidenceReads, 0);
  const builders = require("../../src/registration-diagnostics") as {
    platformOperationalEventDiagnosticRecord: typeof platformOperationalEventDiagnosticRecord;
    platformOperationalBoundaryDiagnosticRecord: typeof platformOperationalBoundaryDiagnosticRecord;
  };
  const originalEvent = builders.platformOperationalEventDiagnosticRecord, originalBoundary = builders.platformOperationalBoundaryDiagnosticRecord;
  for (const mode of ["throws", "missing", "malformed"] as const) {
    const broken = (): DiagnosticRecord => {
      if (mode === "throws") throw new Error("PRIVATE-contract-canary");
      return mode === "missing" ? undefined as never : { ...source9[0]!, detail: { private: "PRIVATE-contract-canary" } };
    };
    builders.platformOperationalEventDiagnosticRecord = broken;
    builders.platformOperationalBoundaryDiagnosticRecord = broken;
    try {
      const processing = literal("core.diagnostics.processing-failed", { reason: mode === "throws" ? "construction-threw" : mode === "missing" ? "construction-rejected" : "definition-unselected" });
      records.length = contexts.length = 0;
      const rejected = platformReadinessObservationEvent(null, options);
      if (rejected.ok) throw new Error("Expected original rejection.");
      equal(rejected.error.code, "PLATFORM_OPERATIONAL_EVENT_INVALID");
      deepEqual(rejected.error.diagnosticRecord, processing);
      deepEqual(records, [processing]);
      deepEqual(contexts[0], { operation: "readiness-event", phase: "validation", evidence: "owned" });
      records.length = contexts.length = 0;
      throws(() => fixedFeatureFlagReader({ get [flag](): boolean { throw raw; } }, false, options), error => error === raw);
      deepEqual(records, [processing, ...source9]);
      deepEqual(contexts[0], { operation: "fixed-feature-flags", phase: "snapshot", evidence: "owned" });
    } finally {
      builders.platformOperationalEventDiagnosticRecord = originalEvent;
      builders.platformOperationalBoundaryDiagnosticRecord = originalBoundary;
    }
  }
  const unhandled: unknown[] = [], onUnhandled = (error: unknown): void => { unhandled.push(error); };
  process.on("unhandledRejection", onUnhandled);
  try {
    let thenReads = 0;
    for (const sink of [() => { throw raw; }, () => Promise.reject(raw), () => Object.defineProperty(Promise.reject(raw), "then", { get() { thenReads++; throw raw; } }), () => ({ then(_resolve: unknown, reject: (error: unknown) => void) { reject(raw); } })]) {
      const failed = platformReadinessObservationEvent(null, { onDiagnostic: sink }); equal(failed.ok, false);
      throws(() => fixedFeatureFlagReader({ get [flag](): boolean { throw raw; } }, false, { onDiagnostic: sink }), (error) => error === raw);
    }
    await new Promise<void>((resolve) => setImmediate(resolve)); equal(thenReads, 0); deepEqual(unhandled, []);
  } finally { process.off("unhandledRejection", onUnhandled); }
}

main()
  .then(() => {
    console.log("platform/contracts runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
