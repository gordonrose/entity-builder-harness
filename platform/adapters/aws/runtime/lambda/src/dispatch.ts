import type { PlatformScheduleDispatcher, PlatformScheduleDispatchRunResult } from "@kanbien/platform-persistence";
import { checkedMinimumRemainingMs, createPlatformLambdaContinuation, type PlatformLambdaContext } from "./deadline";
import { lambdaBudgetError, lambdaDispatchError } from "./diagnostics";

export interface PlatformLambdaDispatcherOptions {
  readonly dispatcher: PlatformScheduleDispatcher;
  /** Must exceed the longest bounded dependency call plus result settlement time. */
  readonly minimumRemainingMs: number;
  /** Earlier due-phase stop reserves invocation time for old outbox backlog. */
  readonly minimumDeliveryRemainingMs: number;
}

/** Translate one fixed tick to the existing bounded dispatcher; event contents cannot select work. */
export function createPlatformLambdaDispatcherHandler(options: PlatformLambdaDispatcherOptions) {
  const { dispatcher } = options;
  const minimumRemainingMs = checkedMinimumRemainingMs(options.minimumRemainingMs);
  const minimumDeliveryRemainingMs = checkedMinimumRemainingMs(options.minimumDeliveryRemainingMs, "minimum-delivery-remaining-ms");
  if (minimumDeliveryRemainingMs <= minimumRemainingMs) throw lambdaBudgetError("minimum-delivery-remaining-ms", "not-after-total-margin");
  return async (_event: unknown, context: PlatformLambdaContext): Promise<PlatformScheduleDispatchRunResult> => {
    const result = await dispatcher.runOnce({
      shouldContinue: createPlatformLambdaContinuation(context, minimumRemainingMs),
      shouldContinueDelivery: createPlatformLambdaContinuation(context, minimumDeliveryRemainingMs),
    });
    if (!result.ok) throw result.error;
    if (result.value.stopReason === "queue-send-failed" || result.value.stopReason === "publish-marker-failed") {
      throw lambdaDispatchError(result.value.stopReason);
    }
    // A clean bounded stop acknowledges this invocation, never completion of its jobs.
    return result.value;
  };
}
