import { healthCheckName, healthCheckResult, monitoringComponent } from "@kanbien/core/monitoring";
import { fixedClock, isoDateTimeFromDate } from "@kanbien/core/shared";
import type { PlatformHealthRegistration } from "@kanbien/platform-contracts";
import { platformHealthName } from "@kanbien/platform-contracts";
import { platformHealthHttpStatus, platformLiveness, platformReadiness } from "../src/index";

const healthName = platformHealthName("smoke.readiness");
if (!healthName.ok) {
  throw new Error("Expected valid health name.");
}

const clock = fixedClock(new Date("2026-07-10T00:00:00.000Z"));
const registration: PlatformHealthRegistration = {
  name: healthName.value,
  check: {
    check: () => healthCheckResult({
      name: healthCheckName("smoke.readiness"),
      type: "readiness",
      component: monitoringComponent({ type: "runtime", name: "platform" }),
      status: "healthy",
      checkedAt: isoDateTimeFromDate(clock.now()),
    }),
  },
};

void platformLiveness(clock).status;
void platformHealthHttpStatus("ready");
void platformReadiness({ lifecycleReady: true, healthChecks: [registration], clock });

// @ts-expect-error unknown health states are rejected
platformHealthHttpStatus("warming");
