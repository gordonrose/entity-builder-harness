import { equal } from "node:assert/strict";
import type { Permission } from "@kanbien/core/authz";
import { fixedClock } from "@kanbien/core/shared";
import {
  authorizePlatformPermissions,
  corsPolicyForOrigin,
  createInMemoryPlatformRateLimiter,
  createPlatformSecurityHeaders,
  denyByDefaultAuthenticationResult,
  platformRateLimitError,
} from "../src/index";

async function main(): Promise<void> {
  const defaultHeaders = createPlatformSecurityHeaders();
  equal(defaultHeaders["x-content-type-options"], "nosniff");
  equal(defaultHeaders["x-frame-options"], "DENY");
  equal(defaultHeaders["access-control-allow-origin"], undefined);

  const corsHeaders = createPlatformSecurityHeaders({
    cors: corsPolicyForOrigin("https://app.example.test"),
  });
  equal(corsHeaders["access-control-allow-origin"], "https://app.example.test");
  equal(corsHeaders["access-control-allow-headers"], "authorization, content-type, x-request-id");

  equal(denyByDefaultAuthenticationResult.authenticated, false);
  equal(denyByDefaultAuthenticationResult.permissions.length, 0);

  const permission = "smoke:read" as Permission;
  equal(authorizePlatformPermissions([permission], [permission]).ok, true);
  const forbidden = authorizePlatformPermissions([permission], []);
  equal(forbidden.ok, false);
  if (!forbidden.ok) {
    equal(forbidden.error.code, "PLATFORM_SECURITY_FORBIDDEN");
    equal(forbidden.error.details?.["permission"], permission);
  }

  const limiter = createInMemoryPlatformRateLimiter({
    limit: 2,
    windowMs: 1000,
    clock: fixedClock(new Date("2026-07-10T00:00:00.000Z")),
  });
  equal(limiter.check("client").allowed, true);
  equal(limiter.check("client").allowed, true);
  const limited = limiter.check("client");
  equal(limited.allowed, false);
  equal(limited.retryAfterMs, 1000);
  equal(platformRateLimitError(limited.retryAfterMs).code, "PLATFORM_SECURITY_RATE_LIMITED");
}

main()
  .then(() => {
    console.log("platform/security runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
