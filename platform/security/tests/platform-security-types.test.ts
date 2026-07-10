import type { Permission } from "@kanbien/core/authz";
import {
  authorizePlatformPermissions,
  createInMemoryPlatformRateLimiter,
  createPlatformSecurityHeaders,
  denyByDefaultAuthenticationResult,
} from "../src/index";

const permission = "smoke:read" as Permission;
const decision = authorizePlatformPermissions([permission], denyByDefaultAuthenticationResult.permissions);
if (!decision.ok) {
  void decision.error.code;
}

const headers: Readonly<Record<string, string>> = createPlatformSecurityHeaders();
void headers;

const limiter = createInMemoryPlatformRateLimiter({ limit: 1, windowMs: 1000 });
void limiter.check("client").allowed;

// @ts-expect-error permissions must use core Permission values
authorizePlatformPermissions([1], []);
