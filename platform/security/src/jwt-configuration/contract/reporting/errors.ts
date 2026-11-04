import { parseDiagnosticRecord, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { jwtConfigurationDiagnostic } from "./diagnostics";

export interface JwtConfigurationFailure {
  readonly code: "PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID";
  readonly diagnosticRecord: DiagnosticRecord;
}
const ownedFailures = new WeakSet<object>();
export function jwtConfigurationError(diagnosticRecord: DiagnosticRecord): TypeError & JwtConfigurationFailure {
  const checked = parseDiagnosticRecord(jwtConfigurationDiagnostic, diagnosticRecord);
  if (!checked.ok) throw new TypeError("PLATFORM_SECURITY_JWT_DIAGNOSTIC_INVALID");
  const error = Object.assign(new TypeError("PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID"), {
    code: "PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID" as const, diagnosticRecord: checked.value,
  });
  ownedFailures.add(error);
  return error;
}
export function isJwtConfigurationError(value: unknown): value is TypeError & JwtConfigurationFailure {
  return typeof value === "object" && value !== null && ownedFailures.has(value);
}
