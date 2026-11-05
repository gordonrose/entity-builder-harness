import { numberConfigValue, type ConfigSource } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";
import type { WorkerRetryDelayReason } from "../../contract/requirements";

export function defaultWorkerRetryDelay(attempt: number): number { return attempt * 1000; }
export function validateWorkerRetryDelay(value: unknown): Result<number, { readonly reason: WorkerRetryDelayReason }> {
  const number = numberConfigValue({ get: () => value } as ConfigSource, "retry-delay");
  if (!number.ok) return { ok: false, error: { reason: value === undefined ? "missing" : typeof value === "number" ? "not-finite" : "wrong-type" } };
  if (number.value < 0) return { ok: false, error: { reason: "negative" } };
  return { ok: true, value: number.value };
}
