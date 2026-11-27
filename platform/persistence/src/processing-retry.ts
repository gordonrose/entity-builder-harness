import { createDiagnosticRecord } from "@kanbien/core/diagnostics";
import { isoDateTime, type ISODateTime, type Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError } from "./errors";
import { capturePlatformPersistenceDiagnostic, observePlatformPersistenceDiagnostic, persistenceProcessingRetryRejectedDiagnostic, persistenceProcessingRetryStoredInvalidDiagnostic, type PlatformPersistenceDiagnosticOptions } from "./diagnostics";

/** A retry deadline is optional for legacy immediate-release consumers. */
export function validatePlatformProcessingRetryAt(
  input: { readonly releasedAt: ISODateTime; readonly retryAt?: ISODateTime },
  diagnostics: PlatformPersistenceDiagnosticOptions = {},
): Result<ISODateTime | undefined, PlatformPersistenceError> {
  const submitted = input.retryAt;
  if (submitted === undefined) return { ok: true, value: undefined };
  const released = isoDateTime(input.releasedAt);
  const retry = isoDateTime(submitted);
  if (released.ok && retry.ok && Date.parse(retry.value) >= Date.parse(released.value)) return retry;
  const diagnosticRecord = capturePlatformPersistenceDiagnostic(() => {
    const checked = createDiagnosticRecord(persistenceProcessingRetryRejectedDiagnostic, {
      field: released.ok ? "retry-at" : "released-at",
      reason: released.ok && retry.ok ? "before-release" : "invalid-timestamp", effect: "not-started",
    });
    return checked.ok ? checked.value : undefined;
  });
  observePlatformPersistenceDiagnostic(diagnostics, diagnosticRecord);
  return { ok: false, error: platformPersistenceError({ code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED",
    defaultMessage: "Processing retry deadline must be valid and not precede release.", diagnosticRecord }) };
}

/** Stored retry timing must fail closed; malformed data cannot mean immediate retry. */
export function decodePlatformProcessingRetryAt(value: unknown): ISODateTime {
  const checked = typeof value === "string" ? isoDateTime(value) : undefined;
  if (checked?.ok) return checked.value;
  const diagnosticRecord = capturePlatformPersistenceDiagnostic(() => {
    const built = createDiagnosticRecord(persistenceProcessingRetryStoredInvalidDiagnostic, {
      field: "retry-at", reason: typeof value === "string" ? "invalid-timestamp" : "wrong-type", effect: "not-assessed",
    });
    return built.ok ? built.value : undefined;
  });
  throw Object.assign(new TypeError("Stored processing retry deadline is invalid."), { diagnosticRecord });
}
