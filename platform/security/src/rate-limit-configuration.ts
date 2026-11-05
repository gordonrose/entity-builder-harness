import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { observeSecurityFailure, securityConfigurationPredicateRecord, securityOperationDiagnosticRecord } from "./diagnostics";

/** Numeric evidence only; source reading/conversion and failure policy stay with callers. */
export function securityRateLimitPositiveIntegerFailureRecord(
  field: "limit" | "window" | "bucket-capacity", value: unknown,
): DiagnosticRecord | undefined {
  if (field !== "limit" && field !== "window" && field !== "bucket-capacity") {
    throw new TypeError("PLATFORM_SECURITY_RATE_LIMIT_FIELD_INVALID");
  }
  const integer = Number.isInteger(value);
  if (integer && (value as number) > 0) return undefined;
  const reason = integer ? "not-positive" : typeof value !== "number" ? "wrong-type"
    : value !== value || value === Infinity || value === -Infinity ? "not-finite" : "not-integer";
  return securityConfigurationPredicateRecord(field, reason);
}

/** Preserve the direct limiter constructors' RangeError and ordered observations. */
export function assertPlatformRateLimitPositiveInteger(
  name: "limit" | "windowMs" | "maxBuckets", value: unknown,
): void {
  if (name !== "limit" && name !== "windowMs" && name !== "maxBuckets") {
    throw new TypeError("PLATFORM_SECURITY_RATE_LIMIT_SETTING_INVALID");
  }
  const field = name === "limit" ? "limit" : name === "windowMs" ? "window" : "bucket-capacity";
  const observation = securityRateLimitPositiveIntegerFailureRecord(field, value);
  if (observation !== undefined) {
    throw observeSecurityFailure(new RangeError(name + " must be a positive integer."),
      securityOperationDiagnosticRecord("rate-limit", "configuration-invalid", { reference: field }), [observation]);
  }
}
