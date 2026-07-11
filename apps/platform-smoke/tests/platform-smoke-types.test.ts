import type { ConfigSchema } from "@kanbien/core/config";
import type { QueueMessageType } from "@kanbien/core/queues";
import type { PlatformApp } from "@kanbien/platform-contracts";
import {
  platformSmokeApp,
  platformSmokeAppManifest,
  platformSmokeConfigSchema,
  platformSmokeJobMessageType,
  platformSmokeReadPermission,
  type PlatformSmokeConfig,
} from "../src/index";

const app: PlatformApp = platformSmokeApp;
void app;

const configSchema: ConfigSchema<PlatformSmokeConfig> = platformSmokeConfigSchema;
void configSchema;

const messageType: QueueMessageType = platformSmokeJobMessageType;
void messageType;

const permission: string = platformSmokeReadPermission;
void permission;

const manifestPackageName: "@kanbien/app-platform-smoke" = platformSmokeAppManifest.packageName;
void manifestPackageName;
