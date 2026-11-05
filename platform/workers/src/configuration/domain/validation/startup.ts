import { numberConfigValue, type ConfigSource } from "@kanbien/core/config";
import { queueAttempt } from "@kanbien/core/queues";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { Result } from "@kanbien/core/shared";
import { workerDefaultMaxAttempts, type CheckedWorkerRetryConfiguration, type WorkerRetryConfigurationInput } from "../../contract/requirements";
import { workerRetryConfigurationRecord, type WorkerRetryConfigurationIssue } from "../../contract/reporting/diagnostics";
import { defaultWorkerRetryDelay } from "./retry-delay";

export function validateWorkerRetryConfiguration(input: WorkerRetryConfigurationInput): Result<CheckedWorkerRetryConfiguration, { readonly diagnosticRecord: DiagnosticRecord }> {
  const suppliedLimit: unknown = input.maxAttempts;
  const limit = suppliedLimit === undefined ? workerDefaultMaxAttempts : suppliedLimit;
  const calculator = input.retryBackoffMs;
  const issues: WorkerRetryConfigurationIssue[] = [];
  let acceptedLimit = workerDefaultMaxAttempts;
  const number = numberConfigValue({ get: () => limit } as ConfigSource, "max-attempts");
  if (!number.ok) issues.push({ setting: "max-attempts", reason: typeof limit === "number" ? "not-finite" : "wrong-type" });
  else {
    const attempt = queueAttempt(number.value);
    if (!attempt.ok) issues.push({ setting: "max-attempts", reason: Number.isInteger(number.value) ? "not-positive" : "invalid-integer" });
    else acceptedLimit = attempt.value;
  }
  if (calculator !== undefined && typeof calculator !== "function") issues.push({ setting: "retry-delay-calculator", reason: "not-callable" });
  if (issues.length !== 0) return { ok: false, error: { diagnosticRecord: workerRetryConfigurationRecord(issues) } };
  return { ok: true, value: Object.freeze({ maxAttempts: acceptedLimit, retryBackoffMs: calculator === undefined ? defaultWorkerRetryDelay : calculator }) };
}
