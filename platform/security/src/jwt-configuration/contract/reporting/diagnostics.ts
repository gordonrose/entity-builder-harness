import { defineDiagnostic, createDiagnosticRecord, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { ConfigCheckFailure } from "@kanbien/core/config";
import { jwtConfigurationSettings, jwtConfigurationReasons, type JwtConfigurationReason } from "../requirements";

export const jwtConfigurationDiagnostic = defineDiagnostic({ code: "security.jwt-configuration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["verifier-construction"] }, effect: { type: "enum", values: ["verifier-not-created"] },
    issues: { type: "array", minItems: 1, maxItems: 32, items: { type: "object", properties: {
      setting: { type: "enum", values: jwtConfigurationSettings }, reason: { type: "enum", values: jwtConfigurationReasons },
      index: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
      attributeIndex: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
    }, optional: ["index", "attributeIndex"] } }, truncated: { type: "boolean" },
  } },
} as const);
export const jwtConfigurationDiagnosticCatalog = Object.freeze({ owner: "security", definitions: Object.freeze([jwtConfigurationDiagnostic]) });
export function jwtConfigurationDiagnosticRecord(failure: ConfigCheckFailure<JwtConfigurationReason>): DiagnosticRecord {
  for (const issue of failure.issues) {
    const nested = issue.setting.startsWith("required-claim.");
    if (nested && issue.index === undefined
      || issue.index !== undefined && !nested && issue.setting !== "required-claims"
      || issue.attributeIndex !== undefined && (issue.setting !== "required-claim.value" || issue.index === undefined)) {
      throw new TypeError("PLATFORM_SECURITY_JWT_DIAGNOSTIC_INVALID");
    }
  }
  const checked = createDiagnosticRecord<unknown>(jwtConfigurationDiagnostic, { phase: "verifier-construction", effect: "verifier-not-created",
    issues: failure.issues, truncated: failure.truncated });
  if (!checked.ok) throw new TypeError("PLATFORM_SECURITY_JWT_DIAGNOSTIC_INVALID");
  return checked.value;
}
