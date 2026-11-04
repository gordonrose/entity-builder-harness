import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";
import { workerRetryConfigurationReasons, workerRetryDelayReasons, type WorkerRetryConfigurationReason, type WorkerRetryDelayReason } from "../requirements";

export interface WorkerRetryConfigurationIssue {
  readonly setting: "max-attempts" | "retry-delay-calculator";
  readonly reason: WorkerRetryConfigurationReason;
}
export const workerRetryConfigurationDiagnostic = defineDiagnostic({
  code: "platform-worker.retry-configuration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["configure-worker"] }, phase: { type: "enum", values: ["configuration"] },
    issues: { type: "array", minItems: 1, maxItems: 2, items: { type: "object", properties: {
      setting: { type: "enum", values: ["max-attempts", "retry-delay-calculator"] }, reason: { type: "enum", values: workerRetryConfigurationReasons },
    } } }, effect: { type: "enum", values: ["worker-not-created"] },
  } },
} as const);
export const workerRetryDelayDiagnostic = defineDiagnostic({
  code: "platform-worker.retry-delay-invalid", version: 1,
  classification: { failureKind: "validation", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["job-delivery"] }, phase: { type: "enum", values: ["backoff"] },
    setting: { type: "enum", values: ["retry-delay"] }, reason: { type: "enum", values: workerRetryDelayReasons },
    effect: { type: "enum", values: ["retry-not-submitted"] },
  } },
} as const);
export const workerRetryConfigurationDiagnosticCatalog = Object.freeze({ owner: "platform-worker",
  definitions: Object.freeze([workerRetryConfigurationDiagnostic, workerRetryDelayDiagnostic]) });
export function workerRetryConfigurationRecord(issues: readonly WorkerRetryConfigurationIssue[]) {
  if (issues.some(issue => (issue.setting === "retry-delay-calculator") !== (issue.reason === "not-callable"))) throw new TypeError("PLATFORM_WORKER_RETRY_DIAGNOSTIC_INVALID");
  const checked = createDiagnosticRecord(workerRetryConfigurationDiagnostic, { operation: "configure-worker", phase: "configuration", issues, effect: "worker-not-created" });
  if (!checked.ok) throw new TypeError("PLATFORM_WORKER_RETRY_DIAGNOSTIC_INVALID");
  return checked.value;
}
export function workerRetryDelayRecord(reason: WorkerRetryDelayReason) {
  const checked = createDiagnosticRecord(workerRetryDelayDiagnostic, { operation: "job-delivery", phase: "backoff", setting: "retry-delay", reason, effect: "retry-not-submitted" });
  if (!checked.ok) throw new TypeError("PLATFORM_WORKER_RETRY_DIAGNOSTIC_INVALID");
  return checked.value;
}
