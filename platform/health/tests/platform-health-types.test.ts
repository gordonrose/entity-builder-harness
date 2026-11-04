import { healthCheckName, healthCheckResult, monitoringComponent } from "@kanbien/core/monitoring";
import { fixedClock, isoDateTimeFromDate } from "@kanbien/core/shared";
import type { PlatformHealthRegistration } from "@kanbien/platform-contracts";
import { platformHealthName } from "@kanbien/platform-contracts";
import { platformHealthHttpStatus, platformLiveness, platformReadiness, type PlatformPublicHealthMessage, type PlatformPublicHealthMetadata } from "../src/index";

const publicMessage: PlatformPublicHealthMessage = "Health check failed.";
const publicMetadata: PlatformPublicHealthMetadata = { dependency: "ready", config: "missing", failure: "check-failed" };
void publicMessage; void publicMetadata;
// @ts-expect-error arbitrary dependency text is not public health evidence
const privateDependency: PlatformPublicHealthMetadata = { dependency: "private-value" };
// @ts-expect-error unknown public metadata fields require an explicit policy change
const privateField: PlatformPublicHealthMetadata = { detail: "private-value" };
// @ts-expect-error arbitrary messages cannot be public health summaries
const privateMessage: PlatformPublicHealthMessage = "private-value";
void privateDependency; void privateField; void privateMessage;

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
void platformReadiness({ lifecycleReady: true, healthChecks: [registration], clock, diagnostics: { report: () => ({ status: "rejected" }) } });

// @ts-expect-error unknown health states are rejected
platformHealthHttpStatus("warming");
