import { deepEqual, equal } from "node:assert/strict";
import type { Permission } from "@kanbien/core/authz";
import type { QueueMessageType } from "@kanbien/core/queues";
import {
  definePlatformApp,
  duplicatePlatformRegistration,
  featureFlagName,
  fixedFeatureFlagReader,
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
} from "../src/index";

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
}

main()
  .then(() => {
    console.log("platform/contracts runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
