import { numberConfigValue, type ConfigSource } from "@kanbien/core/config";
import { lambdaBudgetError } from "./diagnostics";

export interface PlatformLambdaContext {
  getRemainingTimeInMillis(): number;
}

/** Cooperative bound only: connection, query and SDK timeouts still own in-flight calls. */
export function checkedMinimumRemainingMs(minimumRemainingMs: number, field: "minimum-remaining-ms" | "minimum-delivery-remaining-ms" = "minimum-remaining-ms"): number {
  const checked = numberConfigValue({ get: () => minimumRemainingMs } as ConfigSource, field);
  if (!checked.ok) throw lambdaBudgetError(field, minimumRemainingMs === undefined ? "missing" : typeof minimumRemainingMs !== "number" ? "wrong-type" : "not-finite");
  if (!Number.isInteger(checked.value)) throw lambdaBudgetError(field, "not-integer");
  if (checked.value <= 0) throw lambdaBudgetError(field, "not-positive");
  return checked.value;
}

export function createPlatformLambdaContinuation(context: PlatformLambdaContext, minimumRemainingMs: number): () => boolean {
  const minimum = checkedMinimumRemainingMs(minimumRemainingMs);
  return () => {
    // Read the actual provider clock each time; a thrown read stays the original failure.
    const remaining = context.getRemainingTimeInMillis();
    if (typeof remaining !== "number") throw lambdaBudgetError("remaining-time", remaining === undefined ? "missing" : "wrong-type");
    if (!Number.isFinite(remaining)) throw lambdaBudgetError("remaining-time", "not-finite");
    if (remaining < 0) throw lambdaBudgetError("remaining-time", "negative");
    return remaining > minimum;
  };
}
