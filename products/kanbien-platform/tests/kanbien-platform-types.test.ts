import type { PlatformApp } from "@kanbien/platform-contracts";
import {
  kanbienPlatformApps,
  kanbienPlatformProductManifest,
  type KanbienPlatformProductManifest,
} from "../src/index";

const manifest: KanbienPlatformProductManifest = kanbienPlatformProductManifest;
void manifest;

const apps: readonly PlatformApp[] = kanbienPlatformApps;
void apps;

const productId: "kanbien-platform" = kanbienPlatformProductManifest.productId;
void productId;
