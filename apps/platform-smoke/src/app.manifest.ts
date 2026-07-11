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

export const platformSmokeReadPermission = "smoke:read" as Permission;
export const platformSmokeConfigKeys = ["PLATFORM_SMOKE_APP_NAME"] as const;

export const platformSmokeAppManifest: PlatformSmokeAppManifest = {
  appId: "platform-smoke",
  packageName: "@kanbien/app-platform-smoke",
  displayName: "Platform Smoke",
  routeBasePath: "/smoke",
  permissions: [platformSmokeReadPermission],
  jobs: ["platform-smoke.rebuild"],
  healthChecks: ["platform-smoke.readiness"],
  requiredConfig: platformSmokeConfigKeys,
};
