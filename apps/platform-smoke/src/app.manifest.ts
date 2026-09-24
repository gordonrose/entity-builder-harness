import type { Permission } from "@kanbien/core/authz";

export interface PlatformSmokeAppManifest {
  readonly appId: "platform-smoke";
  readonly packageName: "@kanbien/app-platform-smoke";
  readonly displayName: "Platform Smoke";
  readonly routeBasePath: "/smoke";
  readonly permissions: readonly Permission[];
  readonly jobs: readonly string[];
  readonly healthChecks: readonly string[];
  readonly requiredConfig: readonly string[];
}

export const platformSmokeReadPermission = "platform-smoke.smoke:read" as Permission;
export const platformSmokeWorkItemCreatePermission = "platform-smoke.persistence.work-item:create" as Permission;
export const platformSmokeConfigKeys = ["PLATFORM_SMOKE_APP_NAME"] as const;

export const platformSmokeAppManifest: PlatformSmokeAppManifest = {
  appId: "platform-smoke",
  packageName: "@kanbien/app-platform-smoke",
  displayName: "Platform Smoke",
  routeBasePath: "/smoke",
  permissions: [platformSmokeReadPermission, platformSmokeWorkItemCreatePermission],
  jobs: ["platform-smoke.rebuild", "platform-smoke.work-item.accepted"],
  healthChecks: ["platform-smoke.readiness"],
  requiredConfig: platformSmokeConfigKeys,
};
