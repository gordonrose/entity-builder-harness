import {
  createPlatformScheduleDispatcher,
  persistenceScheduleDispatchBoundaryDiagnosticRecord,
  persistenceScheduleDispatchConfigurationDiagnosticRecord,
  type PlatformOutboxRelay,
  type PlatformScheduleDelivery,
  type PlatformScheduleDispatcher,
  type PlatformScheduleDispatchOptions,
  type PlatformScheduleDispatchInvocation,
  type PlatformScheduleDispatchRunResult,
} from "../../src/index";

declare const delivery: PlatformScheduleDelivery;
declare const relay: PlatformOutboxRelay;
const options: PlatformScheduleDispatchOptions = { delivery, relay, maximumRelayAttempts: 10 };
const dispatcher: PlatformScheduleDispatcher = createPlatformScheduleDispatcher(options);
const invocation: PlatformScheduleDispatchInvocation = { shouldContinue: () => true };
const result = dispatcher.runOnce(invocation);
const stopped: PlatformScheduleDispatchRunResult = {
  delivery: null, relayAttempts: 0, published: 0, stopReason: "requested-stop",
};
// @ts-expect-error The work bound is numeric, not an unchecked environment string.
const unchecked: PlatformScheduleDispatchOptions = { delivery, relay, maximumRelayAttempts: "10" };
// @ts-expect-error The work bound must be chosen explicitly.
const unbounded: PlatformScheduleDispatchOptions = { delivery, relay };
// @ts-expect-error Stop decisions are synchronous; promises must not be treated as true.
const asynchronous: PlatformScheduleDispatchInvocation = { shouldContinue: async () => false };
// @ts-expect-error A published item is not itself a reason the entire pass stopped.
const misleading: PlatformScheduleDispatchRunResult["stopReason"] = "published";

persistenceScheduleDispatchConfigurationDiagnosticRecord("not-positive");
persistenceScheduleDispatchBoundaryDiagnosticRecord({
  boundary: "outbox-relay", reason: "returned-failure", effect: "relay-outcome-unknown",
});
// @ts-expect-error Raw submitted values are not configuration diagnostic detail.
persistenceScheduleDispatchConfigurationDiagnosticRecord("private-setting");
// @ts-expect-error Claiming an unobserved transaction rollback is not supported.
persistenceScheduleDispatchBoundaryDiagnosticRecord({ boundary: "due-delivery", reason: "threw", effect: "rolled-back" });

void result; void stopped; void unchecked; void unbounded; void asynchronous; void misleading;
