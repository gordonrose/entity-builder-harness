import { deepEqual, equal } from "node:assert/strict";
import { healthCheckName, healthCheckResult, monitoringComponent } from "@kanbien/core/monitoring";
import { fixedClock, isoDateTimeFromDate } from "@kanbien/core/shared";
import type { PlatformHealthRegistration } from "@kanbien/platform-contracts";
import { platformHealthName } from "@kanbien/platform-contracts";
import {
  platformHealthHttpStatus,
  platformLiveness,
  platformReadiness,
} from "../src/index";

async function main(): Promise<void> {
  const healthName = platformHealthName("smoke.readiness");
  if (!healthName.ok) {
    throw new Error("Expected valid health name.");
  }

  const clock = fixedClock(new Date("2026-07-10T00:00:00.000Z"));
  deepEqual(platformLiveness(clock), {
    status: "live",
    checkedAt: "2026-07-10T00:00:00.000Z",
  });

  const check: PlatformHealthRegistration = {
    name: healthName.value,
    check: {
      check: () => healthCheckResult({
        name: healthCheckName("smoke.readiness"),
        type: "readiness",
        component: monitoringComponent({ type: "runtime", name: "platform" }),
        status: "healthy",
        checkedAt: isoDateTimeFromDate(clock.now()),
        metadata: { secret: "do-not-leak", dependency: "ready" },
      }),
    },
  };

  const ready = await platformReadiness({
    lifecycleReady: true,
    healthChecks: [check],
    clock,
  });
  equal(ready.status, "ready");
  equal(platformHealthHttpStatus(ready.status), 200);
  equal(ready.checks[0]?.metadata?.["secret"], "[REDACTED]");
  equal(ready.checks[0]?.metadata?.["dependency"], "ready");

  const notReady = await platformReadiness({
    lifecycleReady: false,
    healthChecks: [check],
    clock,
  });
  equal(notReady.status, "not-ready");
  equal(platformHealthHttpStatus(notReady.status), 503);

  const failed = await platformReadiness({
    lifecycleReady: true,
    healthChecks: [{
      name: healthName.value,
      check: {
        check: () => {
          throw Object.assign(new Error("down"), { token: "secret" });
        },
      },
    }],
    clock,
  });
  equal(failed.status, "not-ready");
  equal(failed.checks[0]?.status, "unhealthy");
  deepEqual(failed.checks[0]?.metadata?.["error"], { name: "Error", message: "down" });
}

main()
  .then(() => {
    console.log("platform/health runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
