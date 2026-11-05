import { numberConfigValue, type ConfigSource } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";
import { persistenceLeaseDurationRequirement, type PersistenceLeaseDurationReason } from "../../contract/requirements";

export function validatePersistenceLeaseDuration(value: unknown): Result<number, { readonly reason: PersistenceLeaseDurationReason }> {
  const number = numberConfigValue({ get: () => value } as ConfigSource, "lease-duration");
  if (!number.ok) return { ok: false, error: { reason: value === undefined ? "missing" : typeof value === "number" ? "not-finite" : "wrong-type" } };
  if (persistenceLeaseDurationRequirement.integer && !Number.isInteger(number.value)) return { ok: false, error: { reason: "invalid-integer" } };
  if (number.value < persistenceLeaseDurationRequirement.minimum) return { ok: false, error: { reason: "not-positive" } };
  return { ok: true, value: number.value };
}
