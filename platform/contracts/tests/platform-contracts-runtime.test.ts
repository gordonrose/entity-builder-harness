import { deepEqual, equal } from "node:assert/strict";
import type { QueueMessageType } from "@kanbien/core/queues";
import {
  definePlatformApp,
  duplicatePlatformRegistration,
  featureFlagName,
  fixedFeatureFlagReader,
  platformAppId,
  platformJobName,
  platformRouteName,
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

  const dealReadPermission = "deal:read";
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
    handler: { handle: () => ({ status: 200 }) },
  } as const;
  deepEqual(validatePlatformRouteRegistration(validRoute, { declaredPermissions: [dealReadPermission] }), {
    ok: true,
    value: undefined,
  });
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

  const validJob = {
    name: jobName.value,
    messageType: "crm.deals.recalculate-score" as QueueMessageType,
    handler: { handle: () => undefined },
  };
  deepEqual(validatePlatformJobRegistration(validJob), { ok: true, value: undefined });
  expectContractError(
    validatePlatformJobRegistration({ ...validJob, messageType: "CRM Deals" as never }),
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
      registry.registerRoute({
        name: routeName.value,
        method: "GET",
        path: "/deals/:id",
        auth: { kind: "authenticated", permissions: [dealReadPermission] },
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
