import { deepEqual, equal } from "node:assert/strict";
import {
  definePlatformApp,
  featureFlagName,
  fixedFeatureFlagReader,
  platformAppId,
  platformRouteName,
} from "../src/index";

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

  const app = definePlatformApp({
    id: appId.value,
    name: "CRM",
    version: "0.0.0",
    mount(registry) {
      if (!routeName.ok) {
        throw new Error("Expected route name to be valid.");
      }

      registry.registerRoute({
        name: routeName.value,
        method: "GET",
        path: "/deals/:id",
        auth: { kind: "authenticated" },
        handler: { handle: () => ({ status: 200 }) },
      });
    },
  });

  const registeredRoutes: unknown[] = [];
  await app.mount(
    {
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
