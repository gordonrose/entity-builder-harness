import {
  createPlatformSmokeApp,
  platformSmokeAppManifest,
  platformSmokeWorkItemDeliveryObservabilityProfile,
  type PlatformSmokeAppOptions,
} from "@kanbien/app-platform-smoke";

export interface KanbienPlatformProductApp {
  readonly appId: string;
  readonly packageName: string;
  readonly mountModule: string;
  readonly routeBasePath: string;
  readonly permissions: readonly string[];
  readonly jobs: readonly string[];
  readonly healthChecks: readonly string[];
  readonly requiredConfig: readonly string[];
}

export interface KanbienPlatformProductManifest {
  readonly productId: "kanbien-platform";
  readonly displayName: "Kanbien Platform";
  readonly purpose: "development-runtime-proof";
  readonly apps: readonly KanbienPlatformProductApp[];
}

/**
 * A deployment composition may supply app-facing dependencies without making
 * the product aware of a cloud provider, target profile, or persistence SDK.
 */
export interface KanbienPlatformProductOptions {
  readonly platformSmoke?: PlatformSmokeAppOptions;
}

/**
 * Target composition selects this app-registered profile for the harmless
 * outbox relay and durable worker transition evidence.
 */
export const kanbienPlatformSmokeWorkItemDeliveryObservabilityProfile =
  platformSmokeWorkItemDeliveryObservabilityProfile;

export const kanbienPlatformProductManifest: KanbienPlatformProductManifest = {
  productId: "kanbien-platform",
  displayName: "Kanbien Platform",
  purpose: "development-runtime-proof",
  apps: [
    {
      appId: platformSmokeAppManifest.appId,
      packageName: platformSmokeAppManifest.packageName,
      mountModule: platformSmokeAppManifest.packageName,
      routeBasePath: platformSmokeAppManifest.routeBasePath,
      permissions: platformSmokeAppManifest.permissions,
      jobs: platformSmokeAppManifest.jobs,
      healthChecks: platformSmokeAppManifest.healthChecks,
      requiredConfig: platformSmokeAppManifest.requiredConfig,
    },
  ],
};

export function createKanbienPlatformApps(options: KanbienPlatformProductOptions = {}) {
  return [createPlatformSmokeApp(options.platformSmoke)] as const;
}

export const kanbienPlatformApps = createKanbienPlatformApps();
