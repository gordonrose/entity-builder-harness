import type { ConfigSchema } from "@kanbien/core/config";
import type { QueueMessageType } from "@kanbien/core/queues";
import type { PlatformApp } from "@kanbien/platform-contracts";
import type { PlatformPersistenceDiagnosticOptions } from "@kanbien/platform-persistence";
import {
  platformSmokeApp,
  platformSmokeAppManifest,
  platformSmokeConfigSchema,
  platformSmokeJobMessageType,
  platformSmokeWorkItemAcceptedJobMessageType,
  platformSmokeReadPermission,
  acceptPlatformSmokeWorkItem,
  createPlatformSmokeApp,
  type PlatformSmokeAcceptedWorkItemFacts,
  type PlatformSmokeAcceptWorkItemDependencies,
  type PlatformSmokeAcceptWorkItemInput,
  type PlatformSmokeWorkItemPersistenceError,
  type PlatformSmokeConfig,
} from "../src/index";

const app: PlatformApp = platformSmokeApp;
void app;

const configSchema: ConfigSchema<PlatformSmokeConfig> = platformSmokeConfigSchema;
void configSchema;

const messageType: QueueMessageType = platformSmokeJobMessageType;
void messageType;

const durableMessageType: QueueMessageType = platformSmokeWorkItemAcceptedJobMessageType;
void durableMessageType;

const permission: string = platformSmokeReadPermission;
void permission;

const manifestPackageName: "@kanbien/app-platform-smoke" = platformSmokeAppManifest.packageName;
void manifestPackageName;

// Existing feature callers remain assignable; observation is an additive invocation input.
const legacyAcceptance: (input: PlatformSmokeAcceptWorkItemInput, dependencies: PlatformSmokeAcceptWorkItemDependencies) =>
  Promise<import("@kanbien/core/shared").Result<PlatformSmokeAcceptedWorkItemFacts, PlatformSmokeWorkItemPersistenceError>> = acceptPlatformSmokeWorkItem;
void legacyAcceptance;
const invocation: PlatformPersistenceDiagnosticOptions = { onDiagnostic(record) { return Promise.resolve(record.code); } };
const observedAcceptance: (input: PlatformSmokeAcceptWorkItemInput, dependencies: PlatformSmokeAcceptWorkItemDependencies,
  diagnostics?: PlatformPersistenceDiagnosticOptions) => ReturnType<typeof acceptPlatformSmokeWorkItem> = acceptPlatformSmokeWorkItem;
void observedAcceptance; void invocation;
const explicitlySelectedApp: PlatformApp = createPlatformSmokeApp({ diagnosticDefinitions: [] });
void explicitlySelectedApp;
