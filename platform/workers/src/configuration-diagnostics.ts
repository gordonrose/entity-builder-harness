import { configurationDiagnostic, defineConfigurationDiagnostic } from "@kanbien/platform-config";

export const workerConfigurationFields = ["queue-address", "region", "receive-wait", "visibility-timeout", "durable-lease-duration"] as const;
export const workerConfigurationReasons = ["missing", "empty", "blank", "wrong-type", "not-finite", "invalid-integer", "not-positive", "out-of-range", "not-below-visibility"] as const;
export const platformWorkerConfigurationDiagnostic = defineConfigurationDiagnostic("platform-worker.configuration-invalid", workerConfigurationFields, workerConfigurationReasons);

/** Adapter facts are checked against the capability's closed definition. */
export function workerConfigurationDiagnosticRecord(setting: string, reason: string) {
  const checked = configurationDiagnostic(platformWorkerConfigurationDiagnostic, [{ setting, reason }]);
  if (!checked.ok) throw new TypeError("PLATFORM_WORKER_CONFIGURATION_DIAGNOSTIC_INVALID");
  return checked.value;
}
