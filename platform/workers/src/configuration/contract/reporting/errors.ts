import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { WorkerRetryDelayReason } from "../requirements";
import { workerRetryDelayRecord } from "./diagnostics";

export function workerRetryDelayError(reason: WorkerRetryDelayReason): TypeError & { readonly diagnosticRecord: DiagnosticRecord } {
  return Object.assign(new TypeError("Worker retry delay is invalid."), { diagnosticRecord: workerRetryDelayRecord(reason) });
}
