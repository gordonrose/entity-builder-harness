import { definePlatformApp, platformAppId, platformHealthName } from "@kanbien/platform-contracts";
import { healthCheckName, healthCheckResult, monitoringComponent } from "@kanbien/core/monitoring";
import { isoDateTimeFromDate } from "@kanbien/core/shared";
import { testEntityDiagnosticCatalog } from "../features/test-entity/index";
import { entitySmokeAppManifest } from "./app.manifest";

export const entitySmokeApp = definePlatformApp({
  id: required(platformAppId(entitySmokeAppManifest.appId)), name: entitySmokeAppManifest.displayName,
  mount(registry, deps) {
    required(registry.registerDiagnosticCatalog(testEntityDiagnosticCatalog));
    required(registry.registerHealthCheck({ name: required(platformHealthName("entity-smoke.readiness")), check: { check: () => healthCheckResult({ name: healthCheckName("entity-smoke.readiness"), type: "readiness", component: monitoringComponent({ type: "runtime", name: "entity-smoke" }), status: "healthy", checkedAt: isoDateTimeFromDate(deps.clock.now()) }) } }));
  },
});
function required<T>(result: { readonly ok: true; readonly value: T } | { readonly ok: false; readonly error: { readonly defaultMessage: string } }): T { if (!result.ok) throw new Error(result.error.defaultMessage); return result.value; }
